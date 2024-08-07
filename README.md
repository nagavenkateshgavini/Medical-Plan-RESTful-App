# Medical Plan RESTfull application

Project to demonstrate Indexing of Structured JSON objects

## Tech Stack
- Python Flask Microservice
- Redis Server
- ElasticSearch
- Kibana
- RabbitMQ
- Google IDP for OAUTH 2.0 Authentication
- Pydantic for Schema Validations
- REST Framework

## Prerequisites:
Export Google Client ID, for JWT ID token authentication with Google IDP
  - `export GOOGLE_CLIENT_ID="rand-id.apps.googleusercontent.com"`

## API Endpoints
- POST `/v1/plan` - Creates a new plan provided in the request body.
  - If the request is successful, a valid `Etag` for the object is returned in the `ETag` HTTP Response Header.
- PUT `/v1/plan/{id}` - Replaces an existing plan provided by the id.
  - A valid Etag for the object should also be provided in the `If-Match` HTTP Request Header.
  - The validator passes if the specified `ETag` matches that of the target resource.
  - The Controller updates only if there's a change in the client view of the response.
- GET `/v1/plan/{id}` - Fetches an existing plan provided by the id.
  - An Etag for the object can be provided in the If-None-Match HTTP Request Header.
  - Returns response only if data in db doesn't matches with the `Etag` provided in headers.
- DELETE `/v1/plan/{id}` - Deletes an existing plan provided by the id.
- PATCH `/v1/plan/{id}` - Update/merge an existing plan provided by the id.
  - A valid Etag for the object should also be provided in the `If-Match` HTTP Request Header.
  - The validator passes if the specified `ETag` matches that of the target resource.
  - The Controller updates only if there's a change in the client view of the response.

## Architecture Diagram:
![architecture.jpg](./data/architecture.jpg)


## Run Details on Mac:
1. `brew install redis`
2. `brew services start redis`
3. `python3 -m venv venv`
4. `source venv/bin/activate`
5. `pip install -r requirements.txt`
6. `python app.py`
