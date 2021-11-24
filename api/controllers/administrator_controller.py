from datetime import date, datetime
from functools import wraps
from typing import Dict

from flask import Blueprint, g, current_app, request, json, jsonify
from sqlalchemy import and_
from sqlalchemy.orm import joinedload
from sqlalchemy.sql.functions import count

from api.helper.allowed_charge_points import allowed_charge_points
from common.helper import standard_json_response
from common.db_model import rbac, db
from common.db_model.charge_point import ChargePoint, ChargePointStatus
from common.db_model.user import Role, User
from common.db_model.whitelist import WhitelistUser, Whitelist, WhitelistChargePoint

from api.auth import token_auth
from api.helper.user_info import get_user_info as helper_get_user_info


administrator_api = Blueprint('administrator', __name__)


def load_user_if_allowed(f):
    """this wrapper loads user as g.inspected_user if and only if it belongs to
    authenticated administrator organization
    first argument must be _email of the requested user
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        _email = list(kwargs.values())[0]

        m_user: User = User.query.options(joinedload(User.roles)).filter_by(email=_email).first()
        if not m_user or m_user.organization_id != g.current_user.organization_id:
            return standard_json_response(http_status_code=404, message=f"Unknown user with id {_email}")
        g.inspected_user = m_user
        return f(*args, **kwargs)

    return decorated


@administrator_api.route('/list-organization-employees', methods=['GET'])
@rbac.allow(['administrator'], methods=['GET'], endpoint="administrator.list_organization_employees")
@token_auth.login_required
def list_organization_employees():
    """Returns the list of employees belonging to this administrator organization"""

    limit = int(request.args.get('limit', 10))
    offset = int(request.args.get('offset', 0))
    sort = request.args.get('sort', 'email')
    order = request.args.get('order', 'asc')
    _filter = request.args.get('filter', None)

    if _filter:
        _filter = json.loads(_filter)
    else:
        _filter = {}

    _filter['organization_id'] = g.current_user.organization.id
    _filter['role'] = Role.EMPLOYEE

    total = User.get_total_for_list(_filter=_filter)

    m_users = User.get_all_for_list(
        limit=limit,
        offset=offset,
        sort=sort,
        order=order,
        _filter=_filter
    )

    data = {
        "total": total,
        "rows": list(map(lambda x: x.to_list_dict(), m_users))
    }

    response = jsonify(data)
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.status_code = 200
    return response


@administrator_api.route('/get-employee-info/<_email>', methods=['GET'])
@rbac.allow(['administrator'], ['GET'], endpoint='administrator.get_employee_info')
@token_auth.login_required
@load_user_if_allowed
def get_employee_info(_email: str):
    """allows for an administrator to retrieve data about on organization employee"""
    user_info = helper_get_user_info(g.inspected_user)
    return standard_json_response(http_status_code=200, data=user_info)


@administrator_api.route('/list-employee-allowed-charge-points/<_email>', methods=['GET'])
@rbac.allow(['employee'], methods=['GET'], endpoint="administrator.list_employee_allowed_charge_points")
@token_auth.login_required
@load_user_if_allowed
def list_employee_allowed_charge_points(_email: str):
    """Returns the list of charge points one employee has access to"""

    limit = int(request.args.get('limit', 10))
    offset = int(request.args.get('offset', 0))
    sort = request.args.get('sort', 'reference')
    order = request.args.get('order', 'asc')
    _filter = request.args.get('filter', None)

    if _filter:
        _filter = json.loads(_filter)
    else:
        _filter = {}

    _filter['user_id'] = g.inspected_user.id
    _filter['unexpired_at'] = datetime.utcnow().strftime('%Y-%m-%d')

    data = allowed_charge_points(limit, offset, sort, order, _filter)

    response = jsonify(data)
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.status_code = 200
    return response


@administrator_api.route('/get-charge-point-statistics', methods=['GET'])
@rbac.allow(['administrator'], methods=['GET'], endpoint="administrator.get_charge_point_statistics")
@token_auth.login_required
def get_charge_point_statistics():
    """Returns statistics about charge points of the organization"""

    stats = db.session.query(ChargePointStatus.code, ChargePointStatus.label, count(ChargePoint.id)). \
        filter(and_(ChargePointStatus.id == ChargePoint.status_id,
                    ChargePoint.organization_id == g.current_user.organization_id)) \
        .group_by(ChargePointStatus.code).all()

    stats = list(map(lambda _tuple: {'status_code': _tuple[0],
                                     'status_label': _tuple[1],
                                     'cp_count': _tuple[2]}, stats))

    return standard_json_response(http_status_code=200, data=stats)


@administrator_api.route('/list-whitelists', methods=['GET'])
@rbac.allow(['administrator'], methods=['GET'], endpoint="administrator.list_whitelists")
@token_auth.login_required
def list_whitelists():
    """Returns whitelists of the organization"""

    limit = int(request.args.get('limit', 10))
    offset = int(request.args.get('offset', 0))
    sort = request.args.get('sort', 'created_at')
    order = request.args.get('order', 'desc')
    _filter = request.args.get('filter', None)

    if _filter:
        _filter = json.loads(_filter)
    else:
        _filter = {}

    _filter['organization_id'] = g.current_user.organization.id

    total = Whitelist.get_total_for_list(_filter=_filter)

    m_whitelists = Whitelist.get_all_for_list(
        limit=limit,
        offset=offset,
        sort=sort,
        order=order,
        _filter=_filter
    )

    data = {
        "total": total,
        "rows": list(map(lambda x: x.to_list_dict(), m_whitelists))
    }

    response = jsonify(data)
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.status_code = 200
    return response
