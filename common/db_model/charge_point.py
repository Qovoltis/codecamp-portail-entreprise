from __future__ import annotations
from sqlalchemy.orm import joinedload
from sqlalchemy import and_, desc, not_
from datetime import datetime, timedelta
from typing import List, Optional, Dict
from . import db
from common.db_model.user import Organization
from common.db_model.address import Address, ZipCode, City


class ChargePointStatus(db.Model):
    STUDY = 'STUDY'
    INSTALLATION = 'INSTALLATION'
    PRODUCTION = 'PRODUCTION'
    __tablename__ = 'charge_point_status'
    id: int = db.Column(db.Integer, primary_key=True)
    code: str = db.Column(db.String, nullable=False, unique=True)
    label: str = db.Column(db.String, nullable=False)


class ChargePoint(db.Model):
    """charge points (borne) are charging devices users on which users can plug their electric vehicles"""
    __tablename__ = 'charge_point'
    id: int = db.Column(db.Integer, primary_key=True)
    reference: str = db.Column(db.String, nullable=False, unique=True)
    address_id = db.Column(db.Integer, db.ForeignKey('address.id'), nullable=False)
    address: Address = db.relationship(Address)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'), nullable=False)
    organization: Organization = db.relationship(Organization)
    status_id = db.Column(db.Integer, db.ForeignKey('charge_point_status.id'), nullable=False)
    status: ChargePointStatus = db.relationship(ChargePointStatus)

    def to_list_dict(self) -> Dict:
        """returns a dictionary of this charge_point adapted for tables"""

        return {
            "reference": self.reference,
            "organization": self.organization.name,
            "address": self.address.label,
            "zip_code": self.address.zip_code.code,
            "city": self.address.zip_code.city.name,
            "status_code": self.status.code,
            "status_label": self.status.label
        }

    @staticmethod
    def _get_filter_condition(_filter: Optional[Dict] = None):
        condition = and_(True, True)
        _filter = _filter or {}

        for key, value in _filter.items():
            if key == 'organization_id':
                condition = and_(condition, ChargePoint.organization_id == value)
            elif key == 'status':
                condition = and_(condition, ChargePoint.status == value)
            elif key == 'accessible_by_user_id':
                condition = and_(condition, f"WhitelistUser.user_id == {value}")
                now = datetime.utcnow().strftime(fmt="%y-%m-%d")
                condition = and_(condition,
                                 f"or_(WhitelistUser.expires_at.is_(None),WhitelistUser.expires_at>={now})")
                condition = and_(condition, f"or_(Whitelist.expires_at.is_(None),Whitelist.expires_at>={now})")

        return condition

    @staticmethod
    def get_total_for_list(_filter: Optional[Dict] = None) -> int:
        """returns total number of charge points which match given filter conditions"""
        condition = ChargePoint._get_filter_condition(_filter)
        return db.session.query(ChargePoint, "WhitelistChargePoint", "Whitelist", "WhitelistUser").\
                   join(ChargePoint.organization). \
                   join(ChargePoint.status). \
                   join(ChargePoint.whitelist_links, isouter=True). \
                   join("WhitelistChargePoint.whitelist", isouter=True). \
                   join("Whitelist.user_links", isouter=True). \
                   filter(condition).count() or 0

    @staticmethod
    def get_all_for_list(limit: int = 10,
                         offset: int = 0,
                         sort: str = 'reference',
                         order: str = 'asc',
                         _filter: Optional[Dict] = None) -> list:
        """special request adapted for table queries"""
        condition = ChargePoint._get_filter_condition(_filter)

        query = ChargePoint.query.\
                   options(joinedload(ChargePoint.organization)). \
                   join(ChargePoint.organization). \
                   join(ChargePoint.status). \
                   join(ChargePoint.whitelist_links, isouter=True). \
                   join("WhitelistChargePoint.whitelist", isouter=True). \
                   join("Whitelist.user_links", isouter=True). \
                   filter(condition)

        if sort == 'reference':
            if order.lower() == 'asc':
                query = query.order_by(ChargePoint.reference.asc())
            else:
                query = query.order_by(ChargePoint.reference.desc())
        else:
            if order.lower() == 'asc':
                query = query.order_by(ChargePoint.reference.asc())
            else:
                query = query.order_by(ChargePoint.reference.desc())

        return query.limit(limit).offset(offset).all() or list()





