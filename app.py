from flask import Flask, request, jsonify
from pydantic import ValidationError

from data_models.medical_plan import PlanSchema

app = Flask(__name__)


@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"


@app.route("/v1/plan", methods=["POST"])
def create_plan():
    try:
        # Parse and validate request JSON using Pydantic
        plan_schema = PlanSchema(**request.json)
        return jsonify(plan_schema.dict()), 200
    except ValidationError as e:
        # Return validation errors
        return jsonify(e.errors()), 400


if __name__ == "__main__":
    app.run()
