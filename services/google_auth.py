from flask import request, jsonify

from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from google.auth.exceptions import InvalidValue


class GoogleAuth:
    def __init__(self, client_id):
        self.client_id = client_id

    def verify_token(self, token):
        try:
            # Verify the token and get the decoded token
            decoded_token = id_token.verify_oauth2_token(
                token,
                google_requests.Request(),
                self.client_id
            )
            return decoded_token
        except InvalidValue as e:
            return None
        except ValueError:
            # Token is invalid
            return None
