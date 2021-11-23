from __future__ import annotations

from decimal import Decimal

from sqlalchemy.orm import joinedload
from sqlalchemy import and_, desc
from flask_rbac import RoleMixin, UserMixin
from datetime import datetime, timedelta
from typing import List, Optional
from . import db


class City(db.Model):
    __tablename__ = 'city'
    id: int = db.Column(db.Integer, primary_key=True)
    name: str = db.Column(db.String, nullable=False)


class ZipCode(db.Model):
    __tablename__ = 'zip_code'
    id: int = db.Column(db.Integer, primary_key=True)
    code: str = db.Column(db.String, nullable=False, unique=True)
    city_id: int = db.Column(db.Integer, db.ForeignKey('city.id'), nullable=False)
    city: City = db.relationship(City)


class Address(db.Model):
    __tablename__ = 'address'
    id: int = db.Column(db.Integer, primary_key=True)
    label: str = db.Column(db.String, nullable=False)
    zip_code_id: int = db.Column(db.Integer, db.ForeignKey('zip_code.id'), nullable=False)
    zip_code: ZipCode = db.relationship(ZipCode)
    latitude: Decimal = db.Column(db.Numeric, nullable=False)
    longitude: Decimal = db.Column(db.Numeric, nullable=False)

