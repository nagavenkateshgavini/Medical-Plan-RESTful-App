import pika
from flask_redis import FlaskRedis
from services.google_auth import GoogleAuth

import config

config = config.Config()
redis_client = FlaskRedis()

# Instantiate the GoogleAuth class
google_auth = GoogleAuth(config.GOOGLE_CLIENT_ID)

# RabbitMQ setup
connection = pika.BlockingConnection(pika.ConnectionParameters(host=config.RABBITMQ_HOST, port=config.RABBITMQ_PORT))
channel = connection.channel()
channel.queue_declare(queue='medical_plan')
