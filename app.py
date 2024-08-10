import os

from flask import Flask
from elasticsearch import Elasticsearch, exceptions

import config
from config import Config
from data_models.es_mappings import INDEX_MAPPING, INDEX_NAME

from extensions import redis_client

es = Elasticsearch(
    [{'host': 'localhost', 'port': 9200, 'scheme': 'http'}],
    basic_auth=(config.Config.ES_USER, config.Config.ES_PASSWORD)
)


def create_index_if_not_exists():
    try:
        if not es.indices.exists(index=INDEX_NAME):
            es.indices.create(index=INDEX_NAME, body=INDEX_MAPPING)
            print(f"Index '{INDEX_NAME}' created with mappings.")
        else:
            print(f"Index '{INDEX_NAME}' already exists.")
    except exceptions.ConnectionError as e:
        print(f"Error connecting to Elasticsearch: {e}")
    except exceptions.ElasticsearchException as e:
        print(f"Error creating index: {e}")


def create_app():
    app = Flask(__name__)
    app.config_class(Config)

    redis_client.init_app(app)
    create_index_if_not_exists()

    from medical_plan_bp import api_bp
    app.register_blueprint(api_bp)

    return app


app = create_app()


if __name__ == '__main__':
    app.run(debug=True)
