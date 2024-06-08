from hashlib import md5

from extensions import redis_client
from data_models.medical_plan import PlanSchema


def save_plan(plan: PlanSchema):
    try:
        plan_data = plan.json()
        record_key = f"plan:{plan.objectId}"

        # Check if the key already exists
        if redis_client.exists(record_key):
            raise ValueError(f"Plan '{plan.objectId}' already exists in Redis")

        # Set the plan data in Redis
        redis_client.set(record_key, plan_data)

        # Calculate and return the ETag
        etag = md5(plan_data.encode()).hexdigest()
        return etag
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
            return PlanSchema.parse_raw(plan_data), etag
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


def get_all_plans():
    try:
        keys = redis_client.keys("plan:*")
        plans = []
        for key in keys:
            plan_data = redis_client.get(key)
            if plan_data:
                plans.append(PlanSchema.parse_raw(plan_data))
        return plans
    except (ConnectionError, TimeoutError) as e:
        # Handle the exception (logging, retrying, etc.)
        raise e
