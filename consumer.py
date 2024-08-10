from abc import ABC, abstractmethod
import json
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import NotFoundError
import redis
from rabbitmq import RabbitMQ
import copy

from datetime import datetime

from config import Config

# Initialize Redis and Elasticsearch
redis_client = redis.StrictRedis(host=Config.REDIS_HOST, port=Config.REDIS_PORT, db=Config.REDIS_DB)
es = Elasticsearch(
    [{'host': Config.ES_HOST, 'port': Config.ES_PORT, 'scheme': 'http'}],
    basic_auth=(Config.ES_USER, Config.ES_PASSWORD)
)


# Abstract Command class
class Command(ABC):
    def __init__(self, message):
        self.message = message

    @abstractmethod
    def execute(self):
        pass


class CreateCommand(Command):

    def execute(self):
        document = self.message['document']
        parent_id = document['objectId']
        redis_parent_id = f"plan:{parent_id}"

        # Index parent document (Plan) in Elasticsearch
        es.index(index='plans', id=parent_id, body={
            "objectId": parent_id,
            "org": document['org'],
            "creationDate": datetime.utcnow(),
            "objectType": document['objectType'],
            "planType": document['planType'],
            "join_field": {
                "name": "plan"  # Define this as the parent type
            }
        })

        # Index planCostShares as a child document in Elasticsearch
        cost_shares_id = document['planCostShares']['objectId']
        es.index(index='plans', id=cost_shares_id, routing=parent_id, body={
            "objectId": cost_shares_id,
            "deductible": document['planCostShares']['deductible'],
            "copay": document['planCostShares']['copay'],
            "org": document['planCostShares']['org'],
            "objectType": document['planCostShares']['objectType'],
            "join_field": {
                "name": "planCostShares",
                "parent": parent_id
            }
        })

        # Index linkedPlanServices as child documents in Elasticsearch
        for service in document['linkedPlanServices']:
            service_id = service['objectId']
            es.index(index='plans', id=service_id, routing=parent_id, body={
                "objectId": service_id,
                "org": service['org'],
                "objectType": service['objectType'],
                "join_field": {
                    "name": "linkedPlanServices",
                    "parent": parent_id
                }
            })

            # Handle nested children (linkedService and planserviceCostShares)
            linked_service_id = service['linkedService']['objectId']
            planservice_cost_shares_id = service['planserviceCostShares']['objectId']

            # Index linkedService (Child of linkedPlanServices)
            es.index(index='plans', id=linked_service_id, routing=service_id, body={
                "objectId": linked_service_id,
                "name": service['linkedService']['name'],
                "org": service['linkedService']['org'],
                "objectType": service['linkedService']['objectType'],
                "join_field": {
                    "name": "linkedService",
                    "parent": service_id
                }
            })

            # Index planserviceCostShares (Child of linkedPlanServices)
            es.index(index='plans', id=planservice_cost_shares_id, routing=service_id, body={
                "objectId": planservice_cost_shares_id,
                "deductible": service['planserviceCostShares']['deductible'],
                "copay": service['planserviceCostShares']['copay'],
                "org": service['planserviceCostShares']['org'],
                "objectType": service['planserviceCostShares']['objectType'],
                "join_field": {
                    "name": "planserviceCostShares",
                    "parent": service_id
                }
            })

        # Save the entire document to Redis
        redis_client.set(redis_parent_id, json.dumps(document))

        print(f"Document {parent_id} created successfully.")


# Concrete Command class for Patch operation
class PatchCommand(Command):
    def execute(self):
        new_plan = self.message['document']
        parent_id = new_plan['objectId']
        parent_redis_key = f"plan:{parent_id}"

        try:
            # Retrieve the current plan from Redis and Elasticsearch
            try:
                current_plan = json.loads(redis_client.get(parent_redis_key))
            except (TypeError, json.JSONDecodeError):
                current_plan = {}

            try:
                es_current_plan = es.get(index='plans', id=parent_id)['_source']
            except NotFoundError:
                print(f"Plan document {parent_id} not found in Elasticsearch.")
                return

            # Merge new plan data with existing data
            merged_plan = self.merge_records(current_plan, new_plan)

            # Update Redis with merged record
            redis_client.set(parent_redis_key, json.dumps(merged_plan))

            # Update only the parent plan in Elasticsearch
            es.update(index='plans', id=parent_id, body={"doc": {
                "org": new_plan.get('org', es_current_plan['org']),
                "objectType": new_plan.get('objectType', es_current_plan['objectType']),
                "planType": new_plan.get('planType', es_current_plan['planType']),
            }})

            # Update or create child documents in Elasticsearch
            if new_plan.get('planCostShares'):
                cost_shares_id = new_plan['planCostShares']['objectId']
                es.update(index='plans', id=cost_shares_id, routing=parent_id, body={"doc": new_plan['planCostShares']})

            existing_child_ids = {item['objectId'] for item in current_plan.get('linkedPlanServices', [])}

            for service in new_plan.get('linkedPlanServices', []):
                service_id = service['objectId']

                # Update or create the linkedPlanServices in Elasticsearch
                if service_id in existing_child_ids:
                    pass
                else:
                    es.index(index='plans', id=service_id, routing=parent_id, body={
                        "objectId": service['objectId'],
                        "org": service['org'],
                        "objectType": service['objectType'],
                        "join_field": {
                            "name": "linkedPlanServices",
                            "parent": parent_id
                        }
                    })

                    # Handle the children of linkedPlanServices
                    if 'linkedService' in service:
                        linked_service = service['linkedService']
                        es.index(index='plans', id=linked_service['objectId'], routing=service_id, body={
                            **linked_service,
                            "join_field": {
                                "name": "linkedService",
                                "parent": service_id
                            }
                        })

                    if 'planserviceCostShares' in service:
                        cost_shares = service['planserviceCostShares']
                        es.index(index='plans', id=cost_shares['objectId'], routing=service_id, body={
                            **cost_shares,
                            "join_field": {
                                "name": "planserviceCostShares",
                                "parent": service_id
                            }
                        })

            print(f"Document {parent_id} patched successfully.")

        except (ConnectionError, TimeoutError) as e:
            print(f"Error occurred: {e}")
            raise e

    def merge_records(self, existing_record, new_record):
        # Deep copy of the existing record to avoid modifying it directly
        merged_record = copy.deepcopy(existing_record)

        # Merge planCostShares
        if new_record.get('planCostShares'):
            merged_record['planCostShares'] = new_record['planCostShares']

        # Merge linkedPlanServices
        if new_record.get('linkedPlanServices'):
            if 'linkedPlanServices' not in merged_record:
                merged_record['linkedPlanServices'] = []

            existing_services = {item['objectId']: item for item in merged_record['linkedPlanServices']}
            for item in new_record['linkedPlanServices']:
                if item['objectId'] in existing_services:
                    # Merge the existing service
                    existing_service = existing_services[item['objectId']]
                    existing_service.update(item)
                else:
                    # Append new service
                    merged_record['linkedPlanServices'].append(item)

        # Merge other top-level fields
        for field in ['objectType', 'planType', 'org', 'creationDate']:
            if new_record.get(field):
                merged_record[field] = new_record[field]

        return merged_record


class DeleteCommand(Command):
    def execute(self):
        doc_id = self.message['doc_id']
        redis_key = f"plan:{doc_id}"

        print("Check for childs...")
        try:
            # Delete child documents of the parent (linkedPlanServices)
            query_linked_plan_services = {
                "query": {
                    "has_parent": {
                        "parent_type": "plan",
                        "query": {
                            "term": {
                                "objectId": doc_id
                            }
                        }
                    }
                }
            }
            linked_plan_services_docs = es.search(index='plans', body=query_linked_plan_services, size=1000)

            for linked_plan_service in linked_plan_services_docs['hits']['hits']:
                linked_service_id = linked_plan_service['_id']

                # Delete children of linkedPlanServices
                query_linked_service_children = {
                    "query": {
                        "has_parent": {
                            "parent_type": "linkedPlanServices",
                            "query": {
                                "term": {
                                    "objectId": linked_service_id
                                }
                            }
                        }
                    }
                }
                linked_service_children_docs = es.search(index='plans', body=query_linked_service_children, size=1000)

                for child_doc in linked_service_children_docs['hits']['hits']:
                    child_id = child_doc['_id']
                    try:
                        if es.exists(index='plans', id=child_id):
                            es.delete(index='plans', id=child_id)
                            print(f"Nested child document {child_id} deleted from Elasticsearch.")
                    except Exception as e:
                        print(f"Failed to delete nested child document {child_id} from Elasticsearch: {e}")

                # Delete the linkedPlanServices document itself
                try:
                    if es.exists(index='plans', id=linked_service_id):
                        es.delete(index='plans', id=linked_service_id)
                        print(f"Child document {linked_service_id} deleted from Elasticsearch.")
                except Exception as e:
                    print(f"Failed to delete linkedPlanServices document {linked_service_id} from Elasticsearch: {e}")

            try:
                # Delete parent document from Elasticsearch if it exists
                if es.exists(index='plans', id=doc_id):
                    es.delete(index='plans', id=doc_id)
                    print(f"Parent document {doc_id} deleted from Elasticsearch.")
                else:
                    print(f"Parent document {doc_id} does not exist in Elasticsearch.")
            except Exception as e:
                print(f"Failed to delete parent document {doc_id} from Elasticsearch: {e}")

            # Delete parent document from Redis if it exists
            if redis_client.exists(redis_key):
                redis_client.delete(redis_key)
                print(f"Parent document {doc_id} deleted from Redis.")
            else:
                print(f"Parent document {redis_key} does not exist in Redis.")

        except Exception as e:
            print(f"Failed to query or delete child documents from Elasticsearch: {e}")


# Invoker class
class CommandInvoker:
    def __init__(self):
        self._commands = {
            "create": CreateCommand,
            "patch": PatchCommand,
            "delete": DeleteCommand
        }

    def invoke(self, message):
        action = message.get("action")
        command_class = self._commands.get(action)
        if command_class:
            command = command_class(message)
            command.execute()
        else:
            print(f"Unknown operation: {action}")


def callback(ch, method, properties, body):
    print(f"Received new message")
    message = json.loads(body)
    invoker = CommandInvoker()
    invoker.invoke(message)


rabbitmq = RabbitMQ()
rabbitmq.consume(callback=callback, queue_name='medical_plan')
