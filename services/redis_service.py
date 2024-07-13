import json
from hashlib import md5

from extensions import redis_client
from data_models.medical_plan import PlanSchema, PatchPlanSchema


def save_plan(plan: PlanSchema):
    try:
        plan_data = plan.json()
        record_key = f"plan:{plan.objectId}"

        # Check if the key already exists
        if redis_client.exists(record_key):
            raise ValueError(f"Plan '{plan.objectId}' already exists in Redis")

        # Set the plan data in Redis
        redis_client.set(record_key, plan_data)
    except (ConnectionError, TimeoutError) as e:
        # Handle the exception (logging, retrying, etc.)
        raise e


def get_plan(object_id: str):
    try:
        record_key = f"plan:{object_id}"
        plan_data = redis_client.get(record_key)
        if plan_data:
            # Calculate ETag
            etag = md5(plan_data).hexdigest()
            return PatchPlanSchema.parse_raw(plan_data), etag
        return None, None
    except (ConnectionError, TimeoutError) as e:
        # Handle the exception (logging, retrying, etc.)
        raise e


def delete_plan(object_id: str):
    try:
        record_key = f"plan:{object_id}"
        result = redis_client.delete(record_key)
        return result == 1
    except (ConnectionError, TimeoutError) as e:
        # Handle the exception (logging, retrying, etc.)
        raise e


def update_plan(plan: PlanSchema, etag: str):
    try:
        plan_data = plan.json()
        record_key = f"plan:{plan.objectId}"

        # Get the current plan data from Redis
        current_plan_data = redis_client.get(record_key)

        # Check if the plan exists and if the provided ETag matches the current data
        if current_plan_data and md5(current_plan_data).hexdigest() == etag:
            # Check if the new data differs from the current data
            if current_plan_data != plan_data:
                # Update the plan data in Redis
                redis_client.set(record_key, plan_data)
                # Calculate and return the new ETag
                new_etag = md5(plan_data.encode()).hexdigest()
                return new_etag
            else:
                # No change in data, return the existing ETag
                return etag
        else:
            raise ValueError("ETag mismatch")
    except (ConnectionError, TimeoutError) as e:
        # Handle the exception (logging, retrying, etc.)
        raise e


def merge_records(existing_record, new_record):
    # Create a deep copy of the existing record to avoid modifying it directly
    merged_record = existing_record.copy()

    # Merge planCostShares from new_record to existing_record
    if new_record.get('planCostShares'):
        for key, value in new_record['planCostShares'].items():
            if value is not None:  # Ignore None values
                merged_record['planCostShares'][key] = value

    # Merge linkedPlanServices from new_record to existing_record
    if new_record.get('linkedPlanServices'):
        if 'linkedPlanServices' not in merged_record:
            merged_record['linkedPlanServices'] = []

        existing_services = {item['objectId']: item for item in merged_record['linkedPlanServices']}
        for item in new_record['linkedPlanServices']:
            if item.get('objectId') in existing_services:
                # Merge the existing service
                existing_service = existing_services[item['objectId']]
                for key, value in item.items():
                    if key == 'linkedService' or key == 'planserviceCostShares':
                        if value:
                            existing_service[key].update(value)
                    elif value is not None:
                        existing_service[key] = value
            else:
                # Append new service
                merged_record['linkedPlanServices'].append(item)

    # Merge objectId and objectType from new_record to existing_record
    if new_record.get('objectType'):
        merged_record['objectType'] = new_record['objectType']

    # Merge planType from new_record to existing_record
    if new_record.get('planType'):
        merged_record['planType'] = new_record['planType']

    return merged_record


def patch_item(new_plan: PatchPlanSchema, current_plan: PlanSchema):
    try:
        record_key = f"plan:{new_plan.objectId}"
        current_plan = current_plan.dict()

        merged_record = json.dumps(merge_records(current_plan, new_plan.dict()))
        redis_client.set(record_key, merged_record)

        updated_etag = md5(merged_record.encode('utf-8')).hexdigest()
        return updated_etag
    except (ConnectionError, TimeoutError) as e:
        # Handle the exception (logging, retrying, etc.)
        raise e


def get_all_plans():
    try:
        keys = redis_client.keys("plan:*")
        plans = []
        for key in keys:
            plan_data = redis_client.get(key)
            if plan_data:
                plans.append(PatchPlanSchema.parse_raw(plan_data))
        return plans
    except (ConnectionError, TimeoutError) as e:
        # Handle the exception (logging, retrying, etc.)
        raise e
