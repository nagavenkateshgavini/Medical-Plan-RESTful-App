from flask import Blueprint, request, jsonify
from pydantic import ValidationError, BaseModel

from data_models.medical_plan import PlanSchema, PatchPlanSchema
from services import redis_service

from extensions import google_auth

api_bp = Blueprint('api', __name__)


@api_bp.route('/health_check', methods=['GET'])
def health_check():
    return "Hello"


@api_bp.before_request
def before_request_func():
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({"message": "Token is missing!"}), 401

    token = auth_header.split(" ")[1]

    decoded_token = google_auth.verify_token(token)
    if not decoded_token:
        return jsonify({"message": "Token is invalid!"}), 401


@api_bp.route('/v1/plan', methods=['POST'])
def create_plan():
    try:
        plan_schema = PlanSchema(**request.json)
        redis_service.save_plan(plan_schema)
        return jsonify(plan_schema.dict()), 201

    except ValidationError as e:
        return jsonify(e.errors()), 400
    except ValueError as e:
        return jsonify({'error': str(e)}), 409
    except (ConnectionError, TimeoutError) as e:
        return jsonify({'error': 'Service Unavailable', 'details': str(e)}), 503


@api_bp.route('/v1/plan/<object_id>', methods=['GET'])
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


@api_bp.route('/v1/plan/<object_id>', methods=['PUT'])
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
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except (ConnectionError, TimeoutError) as e:
        return jsonify({'error': 'Service Unavailable', 'details': str(e)}), 503


@api_bp.route('/v1/plan/<object_id>', methods=['DELETE'])
def delete_plan(object_id):
    try:
        result = redis_service.delete_plan(object_id)

        if result:
            return jsonify({'message': 'Plan deleted successfully'}), 200
        else:
            return jsonify({'error': 'Plan not found'}), 404
    except (ConnectionError, TimeoutError) as e:
        return jsonify({'error': 'Service Unavailable', 'details': str(e)}), 503


@api_bp.route('/v1/plans', methods=['GET'])
def get_all_plans():
    try:
        plans = redis_service.get_all_plans()
        return jsonify([plan.dict() for plan in plans]), 200
    except (ConnectionError, TimeoutError) as e:
        return jsonify({'error': 'Service Unavailable', 'details': str(e)}), 503


@api_bp.route('/v1/patch/<string:key>', methods=['PATCH'])
def patch_item(key):
    try:
        patch_data = request.json
        new_plan = PatchPlanSchema(**patch_data)

        current_plan_data, current_etag = redis_service.get_plan(key)
        if not current_plan_data:
            return jsonify({"message": "Item not found"}), 404

        if current_etag != request.headers.get('If-Match'):
            return jsonify({"message": "ETag does not match"}), 412

        new_etag = redis_service.patch_item(new_plan, current_plan_data)
        if new_etag:
            response = jsonify({"message": "Item updated"})
            response.headers['ETag'] = new_etag
            return response
        else:
            jsonify({"message": "Item not updated"})
    except ValidationError as e:
        return jsonify(e.errors()), 400

    except ValueError as e:
        return jsonify({"message": "ETag does not match"}), 412
