"""auth module contains code for handling the api authentication process
   only BASIC and BEARER TOKEN authentication methods are supported
   Also rbac user provider is configured here
"""
from flask import g, current_app, request
from flask_httpauth import HTTPBasicAuth

from common.db_model import rbac
from common.db_model.user import User
from common.helper import standard_json_response
from .helper import RequestAuthAnalyzer
from .user_logger import UserLogger
from .custom_http_token_auth import CustomHTTPTokenAuth

# dictionary storing several http response codes and messages for authentication/rbac fails use cases
__FAIL_RESPONSES = {
    "INVALID_BASIC_AUTH": {"http_status_code": 401, "message": "Wrong login and/or password."},
    "INVALID_TOKEN_AUTH": {"http_status_code": 401, "message": "Wrong or expired bearer token. Please login again."},
    "INVALID_RIGHTS": {"http_status_code": 403, "message": "You don't have the rights to access this resource."}
}

__DEFAULT_LOGGER = UserLogger()


# basic auth method will only be used at login
basic_auth = HTTPBasicAuth()


@basic_auth.error_handler
def __basic_auth_error_handler():
    return standard_json_response(**__FAIL_RESPONSES["INVALID_BASIC_AUTH"])


@basic_auth.verify_password
def __basic_auth_verify_password(email, password) -> bool:
    """
    returns a boolean indicating if provided basic auth login/password is valid.
    If true also set g.current_user and user_logger for further use in controllers
    :param email:
    :param password:
    :return bool:
    """
    # since rbac is called before if user is already set we just return it
    if g.get('current_user', None):
        return True

    m_user = User.get_by_email(email)
    if not m_user:
        return False
    elif m_user.password != password:
        return False
    # if test is ok we update current_user and user_logger
    g.current_user = m_user
    g.user_logger = UserLogger(g.current_user.email)

    return True


# token auth method is the main authentication method
token_auth = CustomHTTPTokenAuth()


@token_auth.error_handler
def __token_auth_error_handler():
    return standard_json_response(**__FAIL_RESPONSES["INVALID_TOKEN_AUTH"])


@token_auth.verify_token
def __token_auth_verify_token(token: str) -> bool:
    """returns a boolean indicating if provided bearer token token is a valid JWT token for a valid user.
    If true also set g.current_user and user_logger for further use in controllers"""

    # since rbac is called before if user is already set we just return it
    if g.get('current_user', None):
        return True

    __FAIL_RESPONSES["INVALID_TOKEN_AUTH"] = \
        {"http_status_code": 401, "message": "Wrong or expired bearer token. Please login again."}

    data = current_app.token_manager.decode_token(token)
    if data.get('error', None):
        __FAIL_RESPONSES["INVALID_TOKEN_AUTH"] = \
            {"http_status_code": 401, "message": data["error"]}
        return False

    user_id = data['user_id']
    user_email = data['user_email']

    m_user = User.get_by_email(user_email)
    if not m_user:
        return False

    # print(m_user)
    # print(m_user.get_roles())

    # if test is ok we update current_user and user_logger
    g.current_user = m_user
    g.user_logger = UserLogger(g.current_user.email)
    return True

# rbac configuration


def __rbac_user_loader():
    """rbac also needs a function to retrieve its user and check its roles
    """

    __FAIL_RESPONSES["INVALID_RIGHTS"] = \
        {"http_status_code": 403, "message": "You don't have the rights to access this resource."}

    auth_method, auth_data = RequestAuthAnalyzer.get_auth_info(request)
    # print('rbac check', auth_method, auth_data)
    if auth_method == RequestAuthAnalyzer.AUTH_NONE:
        return User.create_anonymous()
    elif auth_method == RequestAuthAnalyzer.AUTH_BASIC:
        auth = basic_auth.get_auth()
        # print(auth)
        if not __basic_auth_verify_password(auth.username, auth.password):
            __FAIL_RESPONSES["INVALID_RIGHTS"] = __FAIL_RESPONSES["INVALID_BASIC_AUTH"]
    elif auth_method == RequestAuthAnalyzer.AUTH_BEARER:
        auth = token_auth.get_auth()
        if not __token_auth_verify_token(auth.get('token')):
            __FAIL_RESPONSES["INVALID_RIGHTS"] = __FAIL_RESPONSES["INVALID_TOKEN_AUTH"]

    return g.get('current_user', User.create_anonymous())


rbac.set_user_loader(__rbac_user_loader)


def __rbac_error_handler():
    """response sent if user has not necessary rights to access a resource"""
    return standard_json_response(**__FAIL_RESPONSES["INVALID_RIGHTS"])


rbac.set_hook(__rbac_error_handler)

