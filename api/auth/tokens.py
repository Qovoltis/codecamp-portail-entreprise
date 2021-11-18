import os
import time
from functools import wraps
from typing import Dict, Optional

from flask import json, Response
import datetime
import jwt
from .user import ActualUtilisateur


class Token:
    _buffered_tokens: Dict
    _TOKEN_VALIDITY_PERIOD: datetime.timedelta

    def __init__(self, token_validity_period=datetime.timedelta(
        days=int(os.environ.get("USER_TOKEN_VALIDITY_SPAN_DAYS", 1))
    )):
        # this Dict registers generated tokens to allow returning the same token for a given amount of time
        self._buffered_tokens = {}
        # TODO see what time is the best security/usability compromise
        self._TOKEN_VALIDITY_PERIOD = token_validity_period

    def generate_token(self, user_id: int, referenceUser: str) -> str:
        """returns a new token or a cached one if still valid"""
        # if a token has already been generated for this user and is non expired then returns it
        if user_id in self._buffered_tokens.keys():
            token = self._buffered_tokens[user_id]
            try:
                jwt.decode(token, 'SpaceArt')
                return token
            except jwt.ExpiredSignatureError:
                pass
        # if no token buffered generate a new one
        try:
            payload = {'exp': datetime.datetime.utcnow() + self._TOKEN_VALIDITY_PERIOD,
                       'iat': datetime.datetime.utcnow(),
                       'sub': user_id,
                       'ref': referenceUser
                       }
            token = jwt.encode(payload, 'SpaceArt', 'HS256').decode('utf-8')
            self._buffered_tokens[user_id] = token
            return token
        except Exception as e:
            try:
                return Response(mimetype='application/json',
                                response=json.dumps({'error': 'error in generating user token'}),
                                status=400)
            finally:
                e = None
                del e

    def invalidate_user_token(self, user_id: int):
        """invalidate user cached token if any"""
        if user_id in self._buffered_tokens.keys():
            self._buffered_tokens.pop(user_id)

    def decode_token(self, token: str) -> Dict:
        """decode a token and check its validity, returned Dict contains decoded data if token is valid"""
        re = {'data': {}, 'error': {}}
        try:
            payload = jwt.decode(token, 'SpaceArt')
            re['data'] = {'user_id': payload['sub'], 'referenceUser': payload['ref']}
        except jwt.ExpiredSignatureError as e1:
            try:
                re['error'] = {'message': 'token expired, please login again.'}
                return re
            finally:
                e1 = None
                del e1
        except jwt.InvalidTokenError:
            re['error'] = {'message': 'Invalid token, please try again with a new token.'}
            return re

        # the only valid token is the buffered one : this production rule allow to easily disconnect users
        if os.environ.get("FLASK_APP_MODE", "development") == "docker" and token not in self._buffered_tokens.values():
            re['error'] = {'message': 'token expired, please login again.'}
            re['data'] = {}

        return re

    def is_token_valid(self, token: str) -> bool:
        """returns whether a token is valid or not using decode_token method"""
        user_ref = self.decode_token(token).get('data', {}).get('referenceUser', None)
        return user_ref is not None

    def get_user_from_token(self, token: str) -> Optional[ActualUtilisateur]:
        """returns the db user from a valid token, else None"""
        user_ref = self.decode_token(token).get('data', {}).get('referenceUser', None)
        return ActualUtilisateur.query.filter_by(referenceUser=user_ref).one_or_none() if user_ref else None


