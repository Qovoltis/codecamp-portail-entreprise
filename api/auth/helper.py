import re
from typing import Tuple, Optional

from flask import Request


class RequestAuthAnalyzer:
    """helper class to analyse and return information about HTTP request authentication method
    only BASIC and BEARER TOKEN authentication methods are supported
    """
    AUTH_NONE = 'none'
    AUTH_BASIC = 'basic'
    AUTH_BEARER = 'bearer'

    _basic_auth_regex = re.compile('^Basic.*')
    _bearer_auth_regex = re.compile('^Bearer.*')

    @staticmethod
    def get_auth_info(_request: Request) -> Tuple[str, Optional[str]]:
        """
        given a request analyzes is authentication header
        returns {method of authentication}, {payload of authentication}
        """
        auth_header = _request.headers.environ.get('HTTP_AUTHORIZATION', '')

        if RequestAuthAnalyzer._bearer_auth_regex.match(auth_header):
            return RequestAuthAnalyzer.AUTH_BEARER, auth_header
        elif RequestAuthAnalyzer._basic_auth_regex.match(auth_header):
            return RequestAuthAnalyzer.AUTH_BASIC, auth_header

        return RequestAuthAnalyzer.AUTH_NONE, None
