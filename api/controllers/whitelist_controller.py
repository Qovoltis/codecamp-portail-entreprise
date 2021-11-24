from datetime import date, datetime
from functools import wraps
from typing import Dict, Optional

from flask import Blueprint, g, current_app, request, json, jsonify
from sqlalchemy import and_
from sqlalchemy.orm import joinedload
from sqlalchemy.sql.functions import count

from common.db_model import rbac, db
from common.db_model.charge_point import ChargePoint, ChargePointStatus
from common.db_model.user import Role, User
from common.db_model.whitelist import WhitelistUser, Whitelist, WhitelistChargePoint

from api.auth import token_auth
from common.helper import standard_json_response

whitelist_api = Blueprint('whitelist', __name__)


def load_whitelist_if_allowed(f):
    """this wrapper loads whitelist as g.current_whitelist if and only if it belongs to
    authenticated administrator organization
    first argument must be _id of the requested whitelist
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        _id = list(kwargs.values())[0]

        m_whitelist: Whitelist = Whitelist.query.filter_by(id=_id).first()
        if not m_whitelist or m_whitelist.organization_id != g.current_user.organization_id:
            return standard_json_response(http_status_code=404, message=f"Unknown whitelist with id {_id}")
        g.current_whitelist = m_whitelist
        return f(*args, **kwargs)

    return decorated


@whitelist_api.route('/get-info/<_id>', methods=['GET'])
@rbac.allow(['administrator'], methods=['GET'], endpoint="whitelist.get_info")
@token_auth.login_required
@load_whitelist_if_allowed
def get_info(_id: int):
    """Returns general information about a whitelist"""
    return standard_json_response(http_status_code=200, data=g.current_whitelist.to_list_dict())


@whitelist_api.route('/update-info/<_id>', methods=['POST'])
@rbac.allow(['administrator'], methods=['POST'], endpoint="whitelist.update_info")
@token_auth.login_required
@load_whitelist_if_allowed
def update_info(_id: int):
    """Update information of a whitelist"""

    m_whitelist: Whitelist = g.current_whitelist

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


@whitelist_api.route('/create', methods=['POST'])
@rbac.allow(['administrator'], methods=['POST'], endpoint="whitelist.create")
@token_auth.login_required
def create():
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


@whitelist_api.route('/delete/<_id>', methods=['DELETE'])
@rbac.allow(['administrator'], methods=['DELETE'], endpoint="whitelist.delete")
@token_auth.login_required
@load_whitelist_if_allowed
def delete(_id: int):
    """Delete a whitelist"""

    m_whitelist: Whitelist = g.current_whitelist

    for m_whitelist_user in m_whitelist.user_links:
        db.session.delete(m_whitelist_user)
        db.session.commit()
    for m_whitelist_charge_point in m_whitelist.charge_point_links:
        db.session.delete(m_whitelist_charge_point)
        db.session.commit()

    db.session.delete(m_whitelist)
    db.session.commit()

    return standard_json_response(http_status_code=200, message=f"Whitelist '{m_whitelist.label}' successfully deleted")


@whitelist_api.route('/list-users/<_id>/<_in>', methods=['GET'])
@rbac.allow(['administrator'], methods=['GET'], endpoint="whitelist.list_users")
@token_auth.login_required
@load_whitelist_if_allowed
def list_users(_id: int, _in: str):
    """
    :param _id: id of the whitelist
    :param _in: must be either in or out : if in users of the whitelist will be included,
    if out users of the organization outside the whitelist
    :return:
    """
    if _in not in ['in', 'out']:
        return standard_json_response(http_status_code=400, message=f"Parameter in must be either in or out.")

    m_whitelist: Whitelist = g.current_whitelist

    limit = int(request.args.get('limit', 10))
    offset = int(request.args.get('offset', 0))
    sort = request.args.get('sort', 'created_at')
    order = request.args.get('order', 'desc')
    _filter = request.args.get('filter', None)

    if _filter:
        _filter = json.loads(_filter)
    else:
        _filter = {}

    users = list()

    if _in == 'in':
        _filter['whitelist_id'] = m_whitelist.id
        total = WhitelistUser.get_total_for_list_for_whitelist(_filter=_filter)
        m_tuples = WhitelistUser.get_all_for_list_for_whitelist(
            limit=limit,
            offset=offset,
            sort=sort,
            order=order,
            _filter=_filter
        )
        for m_whitelist_user, m_user, m_whitelist in m_tuples:
            m_user: User
            m_user_dict = m_user.to_list_dict()
            m_user_dict["access"] = {
                "created_at": m_whitelist_user.created_at.isoformat(),
                "expires_at": m_whitelist_user.expires_at.isoformat() if m_whitelist_user.expires_at else None
            }
            users.append(m_user_dict)
    else:
        _filter['organization_id'] = m_whitelist.organization_id
        _filter['excluded_whitelist_id'] = m_whitelist.id

        total = WhitelistUser.get_total_for_list_not_in_whitelist(_filter=_filter)
        m_tuples = WhitelistUser.get_all_for_list_not_in_whitelist(
            limit=limit,
            offset=offset,
            sort=sort,
            order=order,
            _filter=_filter
        )
        for m_user in m_tuples:
            m_user: User
            m_user_dict = m_user.to_list_dict()
            users.append(m_user_dict)

    data = {
        "total": total,
        "rows": list(users)
    }

    response = jsonify(data)
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.status_code = 200
    return response


@whitelist_api.route('/list-charge-points/<_id>/<_in>', methods=['GET'])
@rbac.allow(['administrator'], methods=['GET'], endpoint="whitelist.list_charge_points")
@token_auth.login_required
@load_whitelist_if_allowed
def list_charge_points(_id: int, _in: str):
    """
    :param _id: id of the whitelist
    :param _in: must be either in or out : if in charge_points of the whitelist will be included,
    if out charge_points of the organization outside the whitelist
    :return:
    """
    if _in not in ['in', 'out']:
        return standard_json_response(http_status_code=400, message=f"Parameter in must be either in or out.")

    m_whitelist: Whitelist = g.current_whitelist

    limit = int(request.args.get('limit', 10))
    offset = int(request.args.get('offset', 0))
    sort = request.args.get('sort', 'reference')
    order = request.args.get('order', 'asc')
    _filter = request.args.get('filter', None)

    if _filter:
        _filter = json.loads(_filter)
    else:
        _filter = {}

    charge_points = list()

    if _in == 'in':
        _filter['whitelist_id'] = m_whitelist.id
        total = WhitelistChargePoint.get_total_for_list_for_whitelist(_filter=_filter)
        m_tuples = WhitelistChargePoint.get_all_for_list_for_whitelist(
            limit=limit,
            offset=offset,
            sort=sort,
            order=order,
            _filter=_filter
        )
        for m_charge_point, m_charge_point_status, m_whitelist_charge_point, m_address, m_zip_code, m_city in m_tuples:
            m_charge_point: ChargePoint
            cp_dict = m_charge_point.to_list_dict()
            charge_points.append(cp_dict)

    else:
        _filter['organization_id'] = m_whitelist.organization_id
        _filter['excluded_whitelist_id'] = m_whitelist.id
        total = WhitelistChargePoint.get_total_for_list_not_in_whitelist(_filter=_filter)
        m_tuples = WhitelistChargePoint.get_all_for_list_not_in_whitelist(
            limit=limit,
            offset=offset,
            sort=sort,
            order=order,
            _filter=_filter
        )
        for m_charge_point, m_charge_point_status, m_address, m_zip_code, m_city in m_tuples:
            m_charge_point: ChargePoint
            cp_dict = m_charge_point.to_list_dict()
            charge_points.append(cp_dict)

    data = {
        "total": total,
        "rows": list(charge_points)
    }

    response = jsonify(data)
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.status_code = 200
    return response


@whitelist_api.route('/update-users/<_id>/<_in>', methods=['POST'])
@rbac.allow(['administrator'], methods=['POST'], endpoint="whitelist.update_users")
@token_auth.login_required
@load_whitelist_if_allowed
def update_users(_id: int, _in: str):
    """
    :param _id: id of the whitelist
    :param _in: must be either in or out : if in users will be included
    (or if already in their expiration data will be updated),
    if out users will be unlinked from whitelist
    :return:
    """
    if _in not in ['in', 'out']:
        return standard_json_response(http_status_code=400, message=f"Parameter in must be either in or out.")

    m_whitelist: Whitelist = g.current_whitelist

    req_data: Dict = request.get_json() or request.json or {}
    req_keys = req_data.keys()

    if "user_emails" not in req_keys:
        return standard_json_response(http_status_code=400, message=f"Missing key 'user_emails', must be a list")
    user_emails = req_data["user_emails"]

    if _in == 'in':
        try:
            expires_at = req_data["expires_at"]
            expires_at = datetime.strptime(expires_at, '%Y-%m-%d') if expires_at is not None else None
        except Exception:
            return standard_json_response(http_status_code=400,
                                          message=f"Missing key or wrong value 'expires_at' (mandatory when in) : "
                                                  f"must be null or a date formatted like YYYY-MM-dd")

        m_users = User.query.options(joinedload(User.whitelist_links)). \
            filter(and_(User.email.in_(user_emails),
                        User.organization_id == m_whitelist.organization_id)).all()

        results = {}

        for m_user in m_users:
            m_user: User
            existing_link: Optional[WhitelistUser] = None
            for m_link in filter(lambda x: x.whitelist_id == m_whitelist.id, m_user.whitelist_links):
                existing_link = m_link
            if existing_link:
                existing_link.expires_at = expires_at
                results[m_user.email] = "UPDATED"
            else:
                new_link = WhitelistUser()
                new_link.created_at = datetime.utcnow().date()
                new_link.whitelist = m_whitelist
                new_link.user = m_user
                new_link.expires_at = expires_at
                db.session.add(new_link)
                results[m_user.email] = "ADDED"

        db.session.commit()
        return standard_json_response(http_status_code=200,
                                      data=results,
                                      message=f"{len(results.keys())} users successfully added/updated into the whitelist.")
    else:
        # out case
        m_users = User.query.options(joinedload(User.whitelist_links)). \
            filter(and_(User.email.in_(user_emails),
                        User.organization_id == m_whitelist.organization_id)).all()

        results = {}

        for m_user in m_users:
            for m_link in filter(lambda x: x.whitelist_id == m_whitelist.id, m_user.whitelist_links):
                db.session.delete(m_link)
                results[m_user.email] = "REMOVED"

        db.session.commit()
        return standard_json_response(http_status_code=200,
                                      data=results,
                                      message=f"{len(results.keys())} users successfully removed from the whitelist.")


@whitelist_api.route('/update-charge-points/<_id>/<_in>', methods=['POST'])
@rbac.allow(['administrator'], methods=['POST'], endpoint="whitelist.update_charge_points")
@token_auth.login_required
@load_whitelist_if_allowed
def update_charge_points(_id: int, _in: str):
    """
    :param _id: id of the whitelist
    :param _in: must be either in or out : if in charge points will be included
    (or if already ignored),
    if out charge points will be unlinked from whitelist
    :return:
    """
    if _in not in ['in', 'out']:
        return standard_json_response(http_status_code=400, message=f"Parameter in must be either in or out.")

    m_whitelist: Whitelist = g.current_whitelist

    req_data: Dict = request.get_json() or request.json or {}
    req_keys = req_data.keys()

    if "references" not in req_keys:
        return standard_json_response(http_status_code=400, message=f"Missing key 'references', must be a list")
    references = req_data["references"]

    if _in == 'in':

        m_charge_points = ChargePoint.query.options(joinedload(ChargePoint.whitelist_links)). \
            filter(and_(ChargePoint.reference.in_(references),
                        ChargePoint.organization_id == m_whitelist.organization_id)).all()

        results = {}

        for m_charge_point in m_charge_points:
            m_charge_point: ChargePoint
            existing_link: Optional[WhitelistChargePoint] = None
            for m_link in filter(lambda x: x.whitelist_id == m_whitelist.id, m_charge_point.whitelist_links):
                existing_link = m_link
            if not existing_link:
                new_link = WhitelistChargePoint()
                new_link.created_at = datetime.utcnow().date()
                new_link.whitelist = m_whitelist
                new_link.charge_point = m_charge_point
                db.session.add(new_link)
                results[m_charge_point.reference] = "ADDED"

        db.session.commit()
        return standard_json_response(http_status_code=200,
                                      data=results,
                                      message=f"{len(results.keys())} charge points successfully added into the whitelist.")
    else:
        # out case
        m_charge_points = ChargePoint.query.options(joinedload(ChargePoint.whitelist_links)). \
            filter(and_(ChargePoint.reference.in_(references),
                        ChargePoint.organization_id == m_whitelist.organization_id)).all()

        results = {}

        for m_charge_point in m_charge_points:
            for m_link in filter(lambda x: x.whitelist_id == m_whitelist.id, m_charge_point.whitelist_links):
                db.session.delete(m_link)
                results[m_charge_point.reference] = "REMOVED"

        db.session.commit()
        return standard_json_response(http_status_code=200,
                                      data=results,
                                      message=f"{len(results.keys())} charge points successfully removed from the whitelist.")