from flask import Blueprint, request, jsonify
from pydantic import ValidationError

from data_models.medical_plan import PlanSchema
from services import redis_service

bp = Blueprint('api', __name__)


@bp.route('/v1/plan', methods=['POST'])
def create_plan():
    try:
        plan_schema = PlanSchema(**request.json)

        # Save the plan to Redis and get the ETag
        etag = redis_service.save_plan(plan_schema)

        # Return the plan with ETag in the response headers
        return jsonify(plan_schema.dict()), 201, {'ETag': etag}

    except ValidationError as e:
        return jsonify(e.errors()), 400
    except ValueError as e:
        return jsonify({'error': str(e)}), 409
    except (ConnectionError, TimeoutError) as e:
        return jsonify({'error': 'Service Unavailable', 'details': str(e)}), 503


@bp.route('/v1/plan/<object_id>', methods=['GET'])
def get_plan(object_id):
    try:
        plan, etag = redis_service.get_plan(object_id)

        # Get the provided If-None-Match header from the request
        if_none_match = request.headers.get('If-None-Match')

        if plan:
            # Compare the If-None-Match header with the plan's ETag
            if if_none_match == etag:
                # If the ETags match, return 304 Not Modified
                return '', 304
            else:
                # If the ETags don't match, return the plan with updated ETag
                return jsonify(plan.dict()), 200, {'ETag': etag}
        else:
            return jsonify({'error': 'Plan not found'}), 404
    except (ConnectionError, TimeoutError) as e:
        return jsonify({'error': 'Service Unavailable', 'details': str(e)}), 503


@bp.route('/v1/plan/<object_id>', methods=['PATCH'])
def update_plan(object_id):
    try:
        # Parse the request JSON into a PlanSchema object
        plan_data = request.json
        plan_schema = PlanSchema(**plan_data)

        # Get the provided ETag from the request headers
        etag = request.headers.get('If-Match')

        # Update the plan if the ETag matches
        if etag:
            new_etag = redis_service.update_plan(plan_schema, etag)
            if new_etag:
                if new_etag != etag:
                    # Plan updated successfully
                    return jsonify({'message': 'Plan updated successfully'}), 200, {'ETag': new_etag}
                else:
                    # Plan was not changed, return Not Modified
                    return jsonify({'message': 'Plan not modified'}), 304, {'ETag': new_etag}
            else:
                # Precondition failed, ETag mismatch
                return jsonify({'error': 'Precondition Failed'}), 412
        else:
            return jsonify({'error': 'If-Match header is missing'}), 400
    except ValidationError as e:
        return jsonify(e.errors()), 400
    except (ConnectionError, TimeoutError) as e:
        return jsonify({'error': 'Service Unavailable', 'details': str(e)}), 503


@bp.route('/v1/plan/<object_id>', methods=['DELETE'])
def delete_plan(object_id):
    try:
        result = redis_service.delete_plan(object_id)

        if result:
            return jsonify({'message': 'Plan deleted successfully'}), 200
        else:
            return jsonify({'error': 'Plan not found'}), 404
    except (ConnectionError, TimeoutError) as e:
        return jsonify({'error': 'Service Unavailable', 'details': str(e)}), 503
