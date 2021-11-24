from datetime import date
from typing import Dict

from common.db_model.charge_point import ChargePoint
from common.db_model.whitelist import WhitelistUser, WhitelistChargePoint, Whitelist


def allowed_charge_points(limit: int, offset: int, sort: str, order: str, _filter: str) -> Dict:

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
                             max(m_whitelist.created_at, m_whitelist_user.created_at,
                                 m_whitelist_charge_point.created_at))
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
            "paid_by_organization": True if m_whitelist.paid_by_organization else False
        }
        charge_points_dict[m_charge_point.reference] = charge_point_dict

    charge_points = list(charge_points_dict.values())
    for charge_point in charge_points:
        charge_point["access"]["created_at"] = charge_point["access"]["created_at"].isoformat()
        charge_point["access"]["expires_at"] = charge_point["access"]["expires_at"].isoformat() if \
        charge_point["access"]["expires_at"] else None

    return {
        "total": total,
        "rows": charge_points
    }