from datetime import date, datetime
from typing import Dict

from flask import Blueprint, g, current_app, request, json, jsonify

from common.db_model import rbac
from common.db_model.charge_point import ChargePoint
from common.db_model.whitelist import WhitelistUser, Whitelist, WhitelistChargePoint

from api.auth import token_auth

employee_api = Blueprint('employee', __name__)


@employee_api.route('/list-allowed-charge-points', methods=['GET'])
@rbac.allow(['employee'], methods=['GET'], endpoint="employee.list_allowed_charge_points")
@token_auth.login_required
def list_allowed_charge_points():
    """Returns the list of charge points this employee has access to"""

    limit = int(request.args.get('limit', 10))
    offset = int(request.args.get('offset', 0))
    sort = request.args.get('sort', 'reference')
    order = request.args.get('order', 'asc')
    _filter = request.args.get('filter', None)

    if _filter:
        _filter = json.loads(_filter)
    else:
        _filter = {}

    _filter['user_id'] = g.current_user.id
    _filter['unexpired_at'] = datetime.utcnow().strftime('%Y-%m-%d')

    total = WhitelistUser.get_total_for_list(_filter=_filter)

    m_tuples = WhitelistUser.get_all_for_list(
        limit=limit,
        offset=offset,
        sort=sort,
        order=order,
        _filter=_filter
    )

    charge_points_dict = {}

    for m_whitelist_user, m_whitelist, m_whitelist_charge_point, m_charge_point, \
        m_status, m_address, m_zip_code, m_city in m_tuples:
        m_whitelist_user: WhitelistUser
        m_whitelist: Whitelist
        m_whitelist_charge_point: WhitelistChargePoint
        m_charge_point: ChargePoint

        # if charge point is already present we have to aggregate access info
        if charge_points_dict.get(m_charge_point.reference, None):
            charge_point_dict = charge_points_dict[m_charge_point.reference]
            acces_dict = charge_point_dict["access"]
            created_at = min(acces_dict["created_at"],
                             max(m_whitelist.created_at, m_whitelist_user.created_at, m_whitelist_charge_point.created_at))
            expires_at = None
            if m_whitelist.expires_at or m_whitelist_user.expires_at:
                expires_at = min(m_whitelist.expires_at or date(year=9999, month=12, day=31),
                                 m_whitelist_user.expires_at or date(year=9999, month=12, day=31))
                if acces_dict["expires_at"]:
                    expires_at = max(expires_at, acces_dict["expires_at"])
                else:
                    expires_at = None

            charge_point_dict["access"] = {
                "created_at": created_at,
                "expires_at": expires_at,
                "paid_by_organization": acces_dict["paid_by_organization"] or
                                        (True if m_whitelist.paid_by_organization else False)
            }
            continue

        # else we create a whole cp dict with access info
        charge_point_dict = m_charge_point.to_list_dict()

        created_at = max(m_whitelist.created_at, m_whitelist_user.created_at, m_whitelist_charge_point.created_at)
        expires_at = None
        if m_whitelist.expires_at or m_whitelist_user.expires_at:
            expires_at = min(m_whitelist.expires_at or date(year=9999, month=12, day=31),
                             m_whitelist_user.expires_at or date(year=9999, month=12, day=31))

        charge_point_dict["access"] = {
            "created_at": created_at,
            "expires_at": expires_at,
            "paid_by_organization" : True if m_whitelist.paid_by_organization else False
        }
        charge_points_dict[m_charge_point.reference] = charge_point_dict

    charge_points = list(charge_points_dict.values())
    for charge_point in charge_points:
        charge_point["access"]["created_at"] = charge_point["access"]["created_at"].isoformat()
        charge_point["access"]["expires_at"] = charge_point["access"]["expires_at"].isoformat() if charge_point["access"]["expires_at"] else None

    data = {
        "total": total,
        "rows": list(charge_points)
    }

    response = jsonify(data)
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.status_code = 200
    return response
