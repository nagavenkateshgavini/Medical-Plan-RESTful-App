# Medical Plan RESTfull application

Project to demonstrate Indexing of Structured JSON objects

## Tech Stack
- Python Flask Microservice
- Redis Server
- ElasticSearch
- Kibana
- RabbitMQ

## API Endpoints
- POST `/plan` - Creates a new plan provided in the request body.
  - If the request is successful, a valid `Etag` for the object is returned in the `ETag` HTTP Response Header.
- PUT `/plan/{id}` - Replaces an existing plan provided by the id.
  - A valid Etag for the object should also be provided in the `If-Match` HTTP Request Header.
  - The validator passes if the specified `ETag` matches that of the target resource.
  - The Controller updates only if there's a change in the client view of the response.
- GET `/plan/{id}` - Fetches an existing plan provided by the id.
  - An Etag for the object can be provided in the If-None-Match HTTP Request Header.
  - Returns response only if data in db doesn't matches with the `Etag` provided in headers.
- DELETE `/plan/{id}` - Deletes an existing plan provided by the id.

## Architecture Diagram:

## Run Details on Mac:
1. `python3 -m venv venv`
2. `source venv/bin/activate`
3. `pip install -r requirements.txt`
4. `python app.py`
5. `brew install redis`
6. `brew services start redis`