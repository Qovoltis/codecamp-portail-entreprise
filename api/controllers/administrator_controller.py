from datetime import date, datetime
from typing import Dict

from flask import Blueprint, g, current_app, request, json, jsonify
from sqlalchemy import and_
from sqlalchemy.sql.functions import count

from common.db_model import rbac, db
from common.db_model.charge_point import ChargePoint, ChargePointStatus
from common.db_model.user import Role, User
from common.db_model.whitelist import WhitelistUser, Whitelist, WhitelistChargePoint

from api.auth import token_auth
from common.helper import standard_json_response

administrator_api = Blueprint('administrator', __name__)


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


@administrator_api.route('/get-whitelist-info/<_id>', methods=['GET'])
@rbac.allow(['administrator'], methods=['GET'], endpoint="administrator.get_whitelist_info")
@token_auth.login_required
def get_whitelist_info(_id: int):
    """Returns general information about a whitelist"""
    m_whitelist: Whitelist = Whitelist.query.filter_by(id=_id).first()
    if not m_whitelist or m_whitelist.organization_id != g.current_user.organization_id:
        return standard_json_response(http_status_code=404, message=f"Unknown whitelist with id {_id}")

    return standard_json_response(http_status_code=200, data=m_whitelist.to_list_dict())


@administrator_api.route('/update-whitelist-info/<_id>', methods=['POST'])
@rbac.allow(['administrator'], methods=['POST'], endpoint="administrator.update_whitelist_info")
@token_auth.login_required
def update_whitelist_info(_id: int):
    """Update information of a whitelist"""

    m_whitelist: Whitelist = Whitelist.query.filter_by(id=_id).first()
    if not m_whitelist or m_whitelist.organization_id != g.current_user.organization_id:
        return standard_json_response(http_status_code=404, message=f"Unknown whitelist with id {_id}")

    req_data: Dict = request.get_json() or request.json or {}
    req_keys = req_data.keys()
    if "label" not in req_keys or not req_data["label"]:
        return standard_json_response(http_status_code=400, message=f"Missing key or wrong value 'label'")
    if "paid_by_organization" not in req_keys or req_data["paid_by_organization"] is None:
        return standard_json_response(http_status_code=400, message=f"Missing key or wrong value 'paid_by_organization'")
    if "expires_at" not in req_keys:
        return standard_json_response(http_status_code=400, message=f"Missing key 'expires_at'")

    m_existing_whitelist = Whitelist.query.filter_by(organization_id=g.current_user.organization_id,
                                                     label=req_data["label"]).first()
    if m_existing_whitelist and m_existing_whitelist.id != m_whitelist.id:
        return standard_json_response(http_status_code=409, message=f"This organization already has another"
                                                                    f" whitelist named "
                                                                    f"'{req_data['label']}'")

    m_whitelist.label = req_data.get("label", None) or m_whitelist.label
    m_whitelist.paid_by_organization = bool(req_data.get("paid_by_organization", None)
                                            or m_whitelist.paid_by_organization)
    if req_data.get("expires_at", -1) != -1:
        m_whitelist.expires_at = datetime.strptime(req_data.get("expires_at"), "%Y-%m-%d").date() \
            if req_data.get("expires_at") else None

    db.session.commit()

    return standard_json_response(http_status_code=200, data=m_whitelist.to_list_dict())


@administrator_api.route('/create-whitelist', methods=['POST'])
@rbac.allow(['administrator'], methods=['POST'], endpoint="administrator.create_whitelist")
@token_auth.login_required
def create_whitelist():
    """Create a new whitelist"""

    req_data: Dict = request.get_json() or request.json or {}
    req_keys = req_data.keys()
    if "label" not in req_keys or not req_data["label"]:
        return standard_json_response(http_status_code=400, message=f"Missing key or wrong value 'label'")
    if "paid_by_organization" not in req_keys or req_data["paid_by_organization"] is None:
        return standard_json_response(http_status_code=400, message=f"Missing key or wrong value 'paid_by_organization'")
    if "expires_at" not in req_keys:
        return standard_json_response(http_status_code=400, message=f"Missing key 'expires_at'")

    m_existing_whitelist = Whitelist.query.filter_by(organization_id=g.current_user.organization_id,
                                                     label=req_data["label"]).first()
    if m_existing_whitelist:
        return standard_json_response(http_status_code=409, message=f"This organization already has another"
                                                                    f" whitelist named "
                                                                    f"'{req_data['label']}'")

    m_whitelist = Whitelist()
    m_whitelist.organization = g.current_user.organization
    m_whitelist.created_at = datetime.utcnow().date()

    m_whitelist.label = req_data["label"]
    m_whitelist.paid_by_organization = bool(req_data["paid_by_organization"])
    m_whitelist.expires_at = datetime.strptime(req_data["expires_at"], "%Y-%m-%d").date() \
        if req_data["expires_at"] else None

    db.session.add(m_whitelist)
    db.session.commit()

    return standard_json_response(http_status_code=200, data=m_whitelist.to_list_dict())


@administrator_api.route('/delete-whitelist/<_id>', methods=['DELETE'])
@rbac.allow(['administrator'], methods=['DELETE'], endpoint="administrator.delete_whitelist")
@token_auth.login_required
def delete_whitelist(_id: int):
    """Delete a whitelist"""

    m_whitelist: Whitelist = Whitelist.query.filter_by(id=_id).first()
    if not m_whitelist or m_whitelist.organization_id != g.current_user.organization_id:
        return standard_json_response(http_status_code=404, message=f"Unknown whitelist with id {_id}")

    for m_whitelist_user in m_whitelist.user_links:
        db.session.delete(m_whitelist_user)
    for m_whitelist_charge_point in m_whitelist.charge_point_links:
        db.session.delete(m_whitelist_charge_point)

    db.session.commit()
    db.session.delete(m_whitelist)
    db.session.commit()

    return standard_json_response(http_status_code=200, message=f"Whitelist '{m_whitelist.label}' successfully deleted")