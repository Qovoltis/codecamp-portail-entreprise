from typing import Dict
from datetime import datetime, timedelta
import jwt


class TokenManager:
    """class for handling JsonWebTokens generation, caching, encoding and decoding"""
    _buffered_tokens: Dict
    _token_validity_span: timedelta

    def __init__(self, token_validity_span: int = 3600):
        self._token_validity_span = timedelta(seconds=token_validity_span)
        # this Dict registers generated tokens to allow returning the same token for a given amount of time
        self._buffered_tokens = {}

    def generate_token(self, user_id: int, user_email: str) -> str:
        """returns a new token or a cached one if still valid"""
        # if a token has already been generated for this user and is non expired then returns it
        if user_id in self._buffered_tokens.keys():
            token = self._buffered_tokens[user_id]
            try:
                jwt.decode(token, 'SpaceArt', "HS256")
                return token
            except jwt.ExpiredSignatureError:
                pass
        # if no token was previously buffered or the old one expired, we generate a new one
        now = datetime.utcnow()

        payload = {
            'iat': now,
            'exp': now + self._token_validity_span,
            'sub': user_id,
            'ref': user_email
        }
        token = jwt.encode(payload, 'SpaceArt', 'HS256')
        self._buffered_tokens[user_id] = token
        return token

    def decode_token(self, token: str) -> Dict:
        """decode a token and check its validity, returned Dict contains decoded data if token is valid"""
        try:
            payload = jwt.decode(token, 'SpaceArt', "HS256")
            return {
                'user_id': payload['sub'],
                'user_email': payload['ref']
            }
        except jwt.ExpiredSignatureError:
            return {
                'error': 'Token expired, please login again.'
            }
        except jwt.InvalidTokenError:
            return {
                'error': 'Invalid token, please login again to get a valid token.'
            }
        except Exception as e:
            return {
                'error': f'Other exception while decoding token: {str(e)}'
            }

    def invalidate_user_token(self, user_id: int):
        """invalidate user cached token if any"""
        if user_id in self._buffered_tokens.keys():
            self._buffered_tokens.pop(user_id)


