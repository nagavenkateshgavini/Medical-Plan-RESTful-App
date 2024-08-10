import os


class Config:
    REDIS_HOST = 'localhost'
    REDIS_PORT = 6379
    REDIS_DB = 0
    REDIS_URL = f'redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}'
    GOOGLE_CERTS_URL = "https://www.googleapis.com/oauth2/v3/certs"
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
    ES_HOST = 'localhost'
    ES_PORT = 9200
    ES_USER = "elastic"
    ES_PASSWORD = os.getenv("ES_PASSWORD")
    RABBITMQ_USER = os.getenv('RABBITMQ_USER')
    RABBITMQ_PASSWORD = os.getenv('RABBITMQ_PASSWORD')
    RABBITMQ_HOST = os.getenv('RABBITMQ_HOST')
    RABBITMQ_PORT = int(os.getenv('RABBITMQ_PORT'))
