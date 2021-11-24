from __future__ import annotations
from sqlalchemy.orm import joinedload
from sqlalchemy import and_, desc, or_, not_
from datetime import datetime, timedelta, date
from typing import List, Optional, Dict
from . import db
from common.db_model.user import Organization, User
from common.db_model.address import Address, ZipCode, City
from common.db_model.charge_point import ChargePoint, ChargePointStatus


class Whitelist(db.Model):
    """Whitelists represents groups of authorization which allows sets of users from on organization to access
    charge_points from this organization"""
    __tablename__ = 'whitelist'
    id: int = db.Column(db.Integer, primary_key=True)
    label: str = db.Column(db.String, nullable=False)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'), nullable=False)
    organization: Organization = db.relationship(Organization)
    paid_by_organization: bool = db.Column(db.Boolean, nullable=False)
    created_at: date = db.Column(db.Date, nullable=False)
    expires_at: Optional[date] = db.Column(db.Date, nullable=True)

    def to_list_dict(self) -> Dict:
        """returns a dictionary of this whitelist_user adapted for tables"""

        return {
            "id": self.id,
            "label": self.label,
            "organization": self.organization.name,
            "paid_by_organization": self.paid_by_organization,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "cp_count": len(self.charge_point_links)
        }

    @staticmethod
    def _get_filter_condition(_filter: Optional[Dict] = None):
        condition = and_(True, True)
        _filter = _filter or {}

        for key, value in _filter.items():
            if key == 'organization_id':
                condition = and_(condition, Whitelist.organization_id == value)
            elif key == 'label':
                condition = and_(condition, Whitelist.label.ilike(f"%{value.strip()}%"))

        return condition

    @staticmethod
    def get_total_for_list(_filter: Optional[Dict] = None) -> int:
        """returns total number of whitelist which match given filter conditions"""
        condition = Whitelist._get_filter_condition(_filter)
        return Whitelist.query.filter(condition).count() or 0

    @staticmethod
    def get_all_for_list(limit: int = 10,
                         offset: int = 0,
                         sort: str = 'created_at',
                         order: str = 'desc',
                         _filter: Optional[Dict] = None) -> list:
        """special request adapted for table queries"""
        condition = Whitelist._get_filter_condition(_filter)

        query = Whitelist.query. \
            options(joinedload(Whitelist.charge_point_links, innerjoin=False)). \
            filter(condition)

        if sort == 'label':
            if order.lower() == 'asc':
                query = query.order_by(Whitelist.label.asc())
            else:
                query = query.order_by(Whitelist.label.desc())
        elif sort == 'expires_at':
            if order.lower() == 'asc':
                query = query.order_by(Whitelist.expires_at.asc())
            else:
                query = query.order_by(Whitelist.expires_at.desc())
        else:
            if order.lower() == 'asc':
                query = query.order_by(Whitelist.created_at.asc())
            else:
                query = query.order_by(Whitelist.created_at.desc())

        return query.limit(limit).offset(offset).all() or list()


class WhitelistUser(db.Model):
    __tablename__ = 'whitelist_user'
    whitelist_id = db.Column(db.Integer, db.ForeignKey('whitelist.id'), nullable=False, primary_key=True)
    whitelist: Whitelist = db.relationship(Whitelist, backref='user_links')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, primary_key=True)
    user: User = db.relationship(User, backref='whitelist_links')
    created_at: date = db.Column(db.Date, nullable=False)
    expires_at: Optional[date] = db.Column(db.Date, nullable=True)

    def to_list_dict(self) -> Dict:
        """returns a dictionary of this whitelist_user adapted for tables"""

        return {
            "user_id": self.user_id,
            "whitelist_id": self.whitelist_id,
        }

    @staticmethod
    def _get_filter_condition(_filter: Optional[Dict] = None):
        """queries intended for getting one user info accross multiple whitelists"""
        condition = and_(True, True)
        _filter = _filter or {}

        condition = and_(condition, WhitelistChargePoint.whitelist_id == Whitelist.id)
        condition = and_(condition, WhitelistChargePoint.charge_point_id == ChargePoint.id)
        condition = and_(condition, WhitelistUser.whitelist_id == Whitelist.id)
        condition = and_(condition, ChargePoint.status_id == ChargePointStatus.id)
        condition = and_(condition, ChargePoint.address_id == Address.id)
        condition = and_(condition, Address.zip_code_id == ZipCode.id)
        condition = and_(condition, ZipCode.city_id == City.id)

        for key, value in _filter.items():
            if key == 'user_id':
                condition = and_(condition, WhitelistUser.user_id == value)
            elif key == 'whitelist_id':
                condition = and_(condition, Whitelist.id == value)
            elif key == 'unexpired_at':
                condition = and_(condition, or_(WhitelistUser.expires_at.is_(None), WhitelistUser.expires_at >= value))
                condition = and_(condition, or_(Whitelist.expires_at.is_(None), Whitelist.expires_at >= value))
            elif key == 'paid_by_organization':
                condition = and_(condition, Whitelist.paid_by_organization == bool(value))
            elif key == 'address':
                condition = and_(condition, Address.label.ilike(f"%{value.strip()}%"))
            elif key == 'zip_code':
                condition = and_(condition, ZipCode.code.ilike(f"%{value.strip()}%"))
            elif key == 'city':
                condition = and_(condition, City.name.ilike(f"%{value.strip()}%"))
            elif key == 'status_code':
                condition = and_(condition, ChargePointStatus.code.ilike(f"%{value.strip()}%"))

        return condition

    @staticmethod
    def get_total_for_list(_filter: Optional[Dict] = None) -> int:
        """queries intended for getting one user info accross multiple whitelists"""
        condition = WhitelistUser._get_filter_condition(_filter)
        return db.session.query(WhitelistUser, Whitelist, WhitelistChargePoint, ChargePoint,
                                ChargePointStatus, Address, ZipCode, City). \
                   filter(condition). \
                   group_by(ChargePoint.id). \
                   count() or 0

    @staticmethod
    def get_all_for_list(limit: int = 10,
                         offset: int = 0,
                         sort: str = 'reference',
                         order: str = 'asc',
                         _filter: Optional[Dict] = None) -> list:
        """queries intended for getting one user info accross multiple whitelists"""
        condition = WhitelistUser._get_filter_condition(_filter)

        query = db.session.query(WhitelistUser, Whitelist, WhitelistChargePoint, ChargePoint,
                                 ChargePointStatus, Address, ZipCode, City). \
            options(joinedload(ChargePoint.organization)). \
            options(joinedload(ChargePoint.status)). \
            options(joinedload(ChargePoint.address).joinedload(Address.zip_code).joinedload(ZipCode.city)). \
            filter(condition)

        if sort == 'reference':
            if order.lower() == 'asc':
                query = query.order_by(ChargePoint.reference.asc())
            else:
                query = query.order_by(ChargePoint.reference.desc())
        elif sort == 'address':
            if order.lower() == 'asc':
                query = query.order_by(Address.label.asc())
            else:
                query = query.order_by(Address.label.desc())
        elif sort == 'zip_code':
            if order.lower() == 'asc':
                query = query.order_by(ZipCode.code.asc())
            else:
                query = query.order_by(ZipCode.code.desc())
        elif sort == 'city':
            if order.lower() == 'asc':
                query = query.order_by(City.name.asc())
            else:
                query = query.order_by(City.name.desc())
        else:
            if order.lower() == 'asc':
                query = query.order_by(ChargePoint.reference.asc())
            else:
                query = query.order_by(ChargePoint.reference.desc())

        return query.limit(limit).offset(offset).all() or list()

    @staticmethod
    def _get_filter_condition_for_whitelist(_filter: Optional[Dict] = None):
        """queries intended for getting users of one whitelist only"""
        condition = and_(True, True)
        _filter = _filter or {}

        condition = and_(condition, WhitelistUser.user_id == User.id)
        condition = and_(condition, WhitelistUser.whitelist_id == Whitelist.id)

        for key, value in _filter.items():
            if key == 'email':
                condition = and_(condition, User.email.ilike(f"%{value.strip()}%"))
            if key == 'firstname':
                condition = and_(condition, User.firstname.ilike(f"%{value.strip()}%"))
            if key == 'lastname':
                condition = and_(condition, User.lastname.ilike(f"%{value.strip()}%"))
            elif key == 'whitelist_id':
                condition = and_(condition, Whitelist.id == value)
            elif key == 'unexpired_at':
                condition = and_(condition, or_(WhitelistUser.expires_at.is_(None), WhitelistUser.expires_at >= value))
                condition = and_(condition, or_(Whitelist.expires_at.is_(None), Whitelist.expires_at >= value))

        return condition

    @staticmethod
    def get_total_for_list_for_whitelist(_filter: Optional[Dict] = None) -> int:
        """queries intended for getting users of one whitelist only"""
        condition = WhitelistUser._get_filter_condition_for_whitelist(_filter)
        return db.session.query(WhitelistUser, User, Whitelist). \
                   filter(condition).count() or 0

    @staticmethod
    def get_all_for_list_for_whitelist(limit: int = 10,
                                       offset: int = 0,
                                       sort: str = 'reference',
                                       order: str = 'asc',
                                       _filter: Optional[Dict] = None) -> list:
        """queries intended for getting users of one whitelist only"""
        condition = WhitelistUser._get_filter_condition_for_whitelist(_filter)

        query = db.session.query(WhitelistUser, User, Whitelist).filter(condition)

        if sort == 'email':
            if order.lower() == 'asc':
                query = query.order_by(User.email.asc())
            else:
                query = query.order_by(User.email.desc())
        elif sort == 'firstname':
            if order.lower() == 'asc':
                query = query.order_by(User.firstname.asc())
            else:
                query = query.order_by(User.firstname.desc())
        elif sort == 'lastname':
            if order.lower() == 'asc':
                query = query.order_by(User.lastname.asc())
            else:
                query = query.order_by(User.lastname.desc())
        elif sort == 'created_at':
            if order.lower() == 'asc':
                query = query.order_by(WhitelistUser.created_at.asc())
            else:
                query = query.order_by(WhitelistUser.created_at.desc())
        elif sort == 'expires_at':
            if order.lower() == 'asc':
                query = query.order_by(WhitelistUser.expires_at.asc())
            else:
                query = query.order_by(WhitelistUser.expires_at.desc())
        else:
            if order.lower() == 'asc':
                query = query.order_by(WhitelistUser.created_at.asc())
            else:
                query = query.order_by(WhitelistUser.created_at.desc())

        return query.limit(limit).offset(offset).all() or list()

    @staticmethod
    def _get_filter_condition_not_in_whitelist(_filter: Optional[Dict] = None):
        """queries intended for getting users not in one whitelist only"""
        condition = and_(True, True)
        _filter = _filter or {}

        for key, value in _filter.items():
            if key == 'email':
                condition = and_(condition, User.email.ilike(f"%{value.strip()}%"))
            if key == 'firstname':
                condition = and_(condition, User.firstname.ilike(f"%{value.strip()}%"))
            if key == 'lastname':
                condition = and_(condition, User.lastname.ilike(f"%{value.strip()}%"))
            elif key == 'excluded_whitelist_id':
                # this method is surely not the most optimized but efficient with not too much data
                user_ids_in_whitelist = db.session.query(WhitelistUser.user_id). \
                    filter(WhitelistUser.whitelist_id == value).all()
                user_ids_in_whitelist = list(map(lambda x: x[0], user_ids_in_whitelist))
                condition = and_(condition, not_(User.id.in_(user_ids_in_whitelist)))
            elif key == 'organization_id':
                condition = and_(condition, User.organization_id == value)

        return condition

    @staticmethod
    def get_total_for_list_not_in_whitelist(_filter: Optional[Dict] = None) -> int:
        """queries intended for getting users not in one whitelist only"""
        condition = WhitelistUser._get_filter_condition_not_in_whitelist(_filter)
        return db.session.query(User). \
                   filter(condition).count() or 0

    @staticmethod
    def get_all_for_list_not_in_whitelist(limit: int = 10,
                                          offset: int = 0,
                                          sort: str = 'reference',
                                          order: str = 'asc',
                                          _filter: Optional[Dict] = None) -> list:
        """queries intended for getting users not in one whitelist only"""
        condition = WhitelistUser._get_filter_condition_not_in_whitelist(_filter)

        query = db.session.query(User).filter(condition)

        if sort == 'email':
            if order.lower() == 'asc':
                query = query.order_by(User.email.asc())
            else:
                query = query.order_by(User.email.desc())
        elif sort == 'firstname':
            if order.lower() == 'asc':
                query = query.order_by(User.firstname.asc())
            else:
                query = query.order_by(User.firstname.desc())
        elif sort == 'lastname':
            if order.lower() == 'asc':
                query = query.order_by(User.lastname.asc())
            else:
                query = query.order_by(User.lastname.desc())

        return query.limit(limit).offset(offset).all() or list()


class WhitelistChargePoint(db.Model):
    __tablename__ = 'whitelist_charge_point'
    whitelist_id = db.Column(db.Integer, db.ForeignKey('whitelist.id'), nullable=False, primary_key=True)
    whitelist: Whitelist = db.relationship(Whitelist, backref='charge_point_links')
    charge_point_id = db.Column(db.Integer, db.ForeignKey('charge_point.id'), nullable=False, primary_key=True)
    charge_point: ChargePoint = db.relationship(ChargePoint, backref='whitelist_links')
    created_at: date = db.Column(db.Date, nullable=False)

    @staticmethod
    def _get_filter_condition_for_whitelist(_filter: Optional[Dict] = None):
        """queries intended for getting charge points of one whitelist only"""
        condition = and_(True, True)
        _filter = _filter or {}

        condition = and_(condition, or_(WhitelistChargePoint.charge_point_id == ChargePoint.id,
                                        WhitelistChargePoint.charge_point_id.is_(None)))
        condition = and_(condition, ChargePoint.status_id == ChargePointStatus.id)
        condition = and_(condition, ChargePoint.address_id == Address.id)
        condition = and_(condition, Address.zip_code_id == ZipCode.id)
        condition = and_(condition, ZipCode.city_id == City.id)

        for key, value in _filter.items():
            if key == 'whitelist_id':
                condition = and_(condition, WhitelistChargePoint.whitelist_id == value)
            elif key == 'excluded_whitelist_id':
                # this method is surely not the most optimized but efficient with not too much data
                cp_ids_in_whitelist = db.session.query(WhitelistChargePoint.charge_point_id). \
                    filter(WhitelistChargePoint.whitelist_id == value).all()
                cp_ids_in_whitelist = list(map(lambda x: x[0], cp_ids_in_whitelist))
                condition = and_(condition, not_(ChargePoint.id.in_(cp_ids_in_whitelist)))
            elif key == 'organization_id':
                condition = and_(condition, ChargePoint.organization_id == value)
            elif key == 'reference':
                condition = and_(condition, ChargePoint.reference.ilike(f"%{value.strip()}%"))
            elif key == 'address':
                condition = and_(condition, Address.label.ilike(f"%{value.strip()}%"))
            elif key == 'zip_code':
                condition = and_(condition, ZipCode.code.ilike(f"%{value.strip()}%"))
            elif key == 'city':
                condition = and_(condition, City.name.ilike(f"%{value.strip()}%"))
            elif key == 'status_code':
                condition = and_(condition, ChargePointStatus.code.ilike(f"%{value.strip()}%"))

        return condition

    @staticmethod
    def get_total_for_list_for_whitelist(_filter: Optional[Dict] = None) -> int:
        """queries intended for getting charge points of one whitelist only"""
        condition = WhitelistChargePoint._get_filter_condition_for_whitelist(_filter)
        return db.session.query(ChargePoint, ChargePointStatus, WhitelistChargePoint, Address, ZipCode, City). \
                   filter(condition).count() or 0

    @staticmethod
    def get_all_for_list_for_whitelist(limit: int = 10,
                                       offset: int = 0,
                                       sort: str = 'reference',
                                       order: str = 'asc',
                                       _filter: Optional[Dict] = None) -> list:
        """queries intended for getting charge points of one whitelist only"""
        condition = WhitelistChargePoint._get_filter_condition_for_whitelist(_filter)

        query = db.session.query(ChargePoint, ChargePointStatus, WhitelistChargePoint,
                                 Address, ZipCode, City).filter(condition)

        if sort == 'reference':
            if order.lower() == 'asc':
                query = query.order_by(ChargePoint.reference.asc())
            else:
                query = query.order_by(ChargePoint.reference.desc())
        elif sort == 'status_code':
            if order.lower() == 'asc':
                query = query.order_by(ChargePointStatus.code.asc())
            else:
                query = query.order_by(ChargePointStatus.code.desc())
        elif sort == 'address':
            if order.lower() == 'asc':
                query = query.order_by(Address.label.asc())
            else:
                query = query.order_by(Address.label.desc())
        elif sort == 'zip_code':
            if order.lower() == 'asc':
                query = query.order_by(ZipCode.code.asc())
            else:
                query = query.order_by(ZipCode.code.desc())
        elif sort == 'city':
            if order.lower() == 'asc':
                query = query.order_by(City.name.asc())
            else:
                query = query.order_by(City.name.desc())
        else:
            if order.lower() == 'asc':
                query = query.order_by(ChargePoint.reference.asc())
            else:
                query = query.order_by(ChargePoint.reference.desc())

        return query.limit(limit).offset(offset).all() or list()

    @staticmethod
    def _get_filter_condition_not_in_whitelist(_filter: Optional[Dict] = None):
        """queries intended for getting charge points not in one whitelist only"""
        condition = and_(True, True)
        _filter = _filter or {}

        condition = and_(condition, ChargePoint.status_id == ChargePointStatus.id)
        condition = and_(condition, ChargePoint.address_id == Address.id)
        condition = and_(condition, Address.zip_code_id == ZipCode.id)
        condition = and_(condition, ZipCode.city_id == City.id)

        for key, value in _filter.items():
            if key == 'excluded_whitelist_id':
                # this method is surely not the most optimized but efficient with not too much data
                cp_ids_in_whitelist = db.session.query(WhitelistChargePoint.charge_point_id). \
                    filter(WhitelistChargePoint.whitelist_id == value).all()
                cp_ids_in_whitelist = list(map(lambda x: x[0], cp_ids_in_whitelist))
                condition = and_(condition, not_(ChargePoint.id.in_(cp_ids_in_whitelist)))
            elif key == 'organization_id':
                condition = and_(condition, ChargePoint.organization_id == value)
            elif key == 'reference':
                condition = and_(condition, ChargePoint.reference.ilike(f"%{value.strip()}%"))
            elif key == 'address':
                condition = and_(condition, Address.label.ilike(f"%{value.strip()}%"))
            elif key == 'zip_code':
                condition = and_(condition, ZipCode.code.ilike(f"%{value.strip()}%"))
            elif key == 'city':
                condition = and_(condition, City.name.ilike(f"%{value.strip()}%"))
            elif key == 'status_code':
                condition = and_(condition, ChargePointStatus.code.ilike(f"%{value.strip()}%"))

        return condition

    @staticmethod
    def get_total_for_list_not_in_whitelist(_filter: Optional[Dict] = None) -> int:
        """queries intended for getting charge points of one whitelist only"""
        condition = WhitelistChargePoint._get_filter_condition_not_in_whitelist(_filter)
        return db.session.query(ChargePoint, ChargePointStatus, Address, ZipCode, City). \
                   filter(condition).count() or 0

    @staticmethod
    def get_all_for_list_not_in_whitelist(limit: int = 10,
                                          offset: int = 0,
                                          sort: str = 'reference',
                                          order: str = 'asc',
                                          _filter: Optional[Dict] = None) -> list:
        """queries intended for getting charge points not in one whitelist only"""
        condition = WhitelistChargePoint._get_filter_condition_not_in_whitelist(_filter)

        query = db.session.query(ChargePoint, ChargePointStatus,
                                 Address, ZipCode, City).filter(condition)

        if sort == 'reference':
            if order.lower() == 'asc':
                query = query.order_by(ChargePoint.reference.asc())
            else:
                query = query.order_by(ChargePoint.reference.desc())
        elif sort == 'status_code':
            if order.lower() == 'asc':
                query = query.order_by(ChargePointStatus.code.asc())
            else:
                query = query.order_by(ChargePointStatus.code.desc())
        elif sort == 'address':
            if order.lower() == 'asc':
                query = query.order_by(Address.label.asc())
            else:
                query = query.order_by(Address.label.desc())
        elif sort == 'zip_code':
            if order.lower() == 'asc':
                query = query.order_by(ZipCode.code.asc())
            else:
                query = query.order_by(ZipCode.code.desc())
        elif sort == 'city':
            if order.lower() == 'asc':
                query = query.order_by(City.name.asc())
            else:
                query = query.order_by(City.name.desc())
        else:
            if order.lower() == 'asc':
                query = query.order_by(ChargePoint.reference.asc())
            else:
                query = query.order_by(ChargePoint.reference.desc())

        return query.limit(limit).offset(offset).all() or list()


