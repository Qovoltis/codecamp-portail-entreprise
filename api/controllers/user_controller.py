from logging import Logger
from typing import Dict

from flask import Blueprint, g, current_app

from api.auth import basic_auth, token_auth
from common.db_model import rbac
from common.helper import standard_json_response
from api.helper.user_info import get_user_info as helper_get_user_info

user_api = Blueprint('user', __name__)


@user_api.route('/login', methods=['POST'])
@basic_auth.login_required
@rbac.allow(['anonymous'], methods=['POST'], endpoint='user.login')
def login():
    """Returns if basic authentication is successful the current Bearer token for authenticating the user"""
    g.user_logger.file_logger.debug("call on user.login")
    token = current_app.token_manager.generate_token(g.current_user.id, g.current_user.email)
    return standard_json_response(http_status_code=200, data={'token': token})


@user_api.route('/info', methods=['GET'])
@user_api.route('/info/<groups>', methods=['GET'])
@rbac.allow(['employee', 'administrator'], methods=['GET'], endpoint='user.get_user_info')
@token_auth.login_required
def get_user_info(groups: [str, None] = None):
    """
    :param groups a string of values & separated that can be specified to return only what you need,
    Ex : Ex : minimal&subscriptions
    :returns user info dictionary
    see helper/user_info for more details
    """
    if groups is not None:
        groups = groups.split('&')
    user_info = helper_get_user_info(g.current_user, groups)
    return standard_json_response(http_status_code=200, data=user_info)

#
# @user_api.route('/logout', methods=['POST'])
# @with_db_session
# @token_auth.login_required
# def logout():
#     """logout the user"""
#     curr_user = g.current_user
#     current_app.app_auth.invalidate_user_token(curr_user.id)
#     # print(token)
#     return standard_json_response(http_status_code=200, message="Goodbye !")
#
#
# @user_api.route('/get-info', methods=['GET'])
# @user_api.route('/get-info/<groups>', methods=['GET'])
# @with_db_session
# @token_auth.login_required
# @rbac.allow(['customer', 'admin'], methods=['GET'])
# def get_user_info(groups: [str, None] = None) -> Response:
#     """
#     get the user infos
#     :param groups a string of values & separated that can be specified to return only what you need,
#     Ex : Ex : minimal&subscriptions
#     see helper/user_info for more details
#     """
#     if groups is not None:
#         groups = groups.split('&')
#     m_user = g.current_user
#     user_info = helper_get_user_info(m_user, groups)
#     return standard_json_response(http_status_code=200, data=user_info)
#
#
# @user_api.route('/update-info', methods=['POST'])
# @with_db_session
# @token_auth.login_required
# @rbac.allow(['customer', 'admin'], methods=['POST'])
# def update_user_info() -> Response:
#     """
#     update user infos
#     """
#     m_user = g.current_user
#     req_data: Dict = request.get_json() or request.json
#
#     m_user.firstname = req_data.get("firstname", None) or m_user.firstname
#     m_user.lastname = req_data.get("lastname", None) or m_user.lastname
#     m_user.address = req_data.get("address", None) or m_user.address
#     m_user.address_code = req_data.get("address_code", None) or m_user.address_code
#     m_user.country = req_data.get("country", None) or m_user.country
#     m_user.phone = req_data.get("phone", None) or m_user.phone
#
#     g.db_session.commit()
#
#     user_info = helper_get_user_info(m_user, [INFOS])
#     return standard_json_response(http_status_code=200, data=user_info)