from flask_redis import FlaskRedis
from services.google_auth import GoogleAuth

import config

config = config.Config()
redis_client = FlaskRedis()

# Instantiate the GoogleAuth class
google_auth = GoogleAuth(config.GOOGLE_CLIENT_ID)
