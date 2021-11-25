from typing import Dict, Optional

from flask import Blueprint, g, current_app, request


from common.db_model import rbac, db
from common.db_model.user import User
from common.helper import standard_json_response

from api.auth import basic_auth, token_auth
from api.helper.user_info import get_user_info as helper_get_user_info

user_api = Blueprint('user', __name__)


@user_api.route('/login', methods=['POST'])
@rbac.allow(['employee', 'administrator'], ['POST'], endpoint='user.login')
@basic_auth.login_required
def login():
    """Returns if basic authentication is successful the current Bearer token for authenticating the user"""
    g.user_logger.file_logger.debug("call on user.login")
    token = current_app.token_manager.generate_token(g.current_user.id, g.current_user.email)
    return standard_json_response(http_status_code=200, data={'token': token})


@user_api.route('/logout', methods=['POST'])
@rbac.allow(['employee', 'administrator'], ['POST'], endpoint='user.logout')
@token_auth.login_required
def logout():
    """logout the user, all front using its token will need to login again"""
    current_app.token_manager.invalidate_user_token(g.current_user.id)
    return standard_json_response(http_status_code=200, message="You have been successfully logged out.")


@user_api.route('/get-info', methods=['GET'])
@user_api.route('/get-info/<groups>', methods=['GET'])
@rbac.allow(['employee', 'administrator'], ['GET'], endpoint='user.get_info')
@token_auth.login_required
def get_info(groups: Optional[str] = None):
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


@user_api.route('/update-info', methods=['POST'])
@rbac.allow(['employee', 'administrator'], ['POST'], endpoint='user.update_info')
@token_auth.login_required
def update_info():
    """update user infos"""
    m_user: User = g.current_user
    req_data: Dict = request.get_json() or request.json or {}

    m_user.firstname = req_data.get("firstname", None) or m_user.firstname
    m_user.lastname = req_data.get("lastname", None) or m_user.lastname
    m_user.phone = req_data.get("phone", None) or m_user.phone

    db.session.commit()

    user_info = helper_get_user_info(m_user, ['info'])
    return standard_json_response(http_status_code=200, data=user_info)


@user_api.route('/update-password', methods=['POST'])
@rbac.allow(['employee', 'administrator'], ['POST'], endpoint='user.update_password')
@token_auth.login_required
def update_password():
    """update user password, a check is done on current password too"""
    m_user: User = g.current_user
    req_data: Dict = request.get_json() or request.json or {}
    req_keys = req_data.keys()

    if "old_password" not in req_keys or not req_data["old_password"]:
        return standard_json_response(http_status_code=400, message=f"Missing key or wrong value 'old_password'")
    if "new_password" not in req_keys or not req_data["new_password"]:
        return standard_json_response(http_status_code=400, message=f"Missing key or wrong value 'new_password'")
    if req_data["old_password"] != m_user.password:
        return standard_json_response(http_status_code=400, message=f"Entered current password is wrong.")
    if len(req_data["new_password"]) < 6:
        return standard_json_response(http_status_code=400, message=f"New password must have at least 6 characters.")

    m_user.password = req_data["new_password"]
    db.session.commit()

    return standard_json_response(http_status_code=200, message="Password succesfully updated.")
