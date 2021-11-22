from __future__ import annotations
from sqlalchemy.orm import joinedload
from sqlalchemy import and_, desc
from flask_rbac import RoleMixin, UserMixin
from datetime import datetime, timedelta
from typing import List, Optional
from . import db, rbac


@rbac.as_role_model
class Role(db.Model, RoleMixin):
    """User roles"""
    ANONYMOUS = 'anonymous'
    ADMINISTRATOR = 'administrator'
    EMPLOYEE = 'employee'
    __tablename__ = 'role'
    id: int = db.Column(db.Integer, primary_key=True)
    name: str = db.Column(db.String, nullable=False, unique=True)

    @staticmethod
    def get_by_name(name: str) -> Optional[Role]:
        if name == Role.ANONYMOUS:
            anonymous_role = Role()
            anonymous_role.name = Role.ANONYMOUS
            return anonymous_role

        return Role.query.filter_by(name=name).one_or_none()

    @staticmethod
    def create_anonymous() -> Role:
        """return an anonymous role"""
        anonymous_role = Role()
        anonymous_role.name = Role.ANONYMOUS
        return anonymous_role

    def add_parent(self, parent):
        # You don't need to add this role to parent's children set,
        # relationship between roles would do this work automatically
        pass

    def add_parents(self, *parents):
        for parent in parents:
            self.add_parent(parent)

    def get_children(self):
        return []


class Organization(db.Model):
    """Represents the organization (company, school ...) a user is attached with"""
    __tablename__ = 'organization'
    id: int = db.Column(db.Integer, primary_key=True)
    name: str = db.Column(db.String, nullable=False, unique=True)

    @staticmethod
    def find_one_by_name(name: str) -> Optional[Organization]:
        return Organization.query.filter_by(name=name).one_or_none()


user_role = db.Table(
    'user_role',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('role_id', db.Integer, db.ForeignKey('role.id'))
)


@rbac.as_user_model
class User(db.Model, UserMixin):
    """
    User model.
    email is also the login of the user
    Password field contains clear password (acceptable since this API is intended for local tests only)
    """
    __tablename__ = 'user'
    id: int = db.Column(db.Integer, primary_key=True)
    email: str = db.Column(db.String, nullable=False, unique=True)
    password: str = db.Column(db.String, nullable=False)
    firstname: str = db.Column(db.String, nullable=False)
    lastname: str = db.Column(db.String, nullable=False)
    phone: str = db.Column(db.String, nullable=False)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'), nullable=False)
    organization: Organization = db.relationship(Organization)
    roles = db.relationship(Role, secondary=user_role)

    def get_roles(self) -> List:
        # if user is registered in db therefore not anonymous,
        # but has no role associated to him return anonymous role.
        if not self.roles:
            return [Role.create_anonymous()]
        else:
            return self.roles

    def has_role(self, name: str) -> bool:
        if name in map(lambda x: x.name, self.get_roles()):
            return True
        else:
            return False

    @staticmethod
    def get_by_email(email: str) -> Optional[User]:
        return User.query.\
            options(joinedload(User.organization, innerjoin=False)). \
            options(joinedload(User.roles, innerjoin=False)). \
            filter_by(email=email).one_or_none()

    @staticmethod
    def create_anonymous() -> User:
        """return an anonymous user"""
        anonymous_user = User()
        anonymous_user.email = "anonymous"
        anonymous_user.firstname = "NA"
        anonymous_user.lastname = "NA"
        anonymous_user.phone = "NA"
        anonymous_user.roles = [Role.create_anonymous()]
        return anonymous_user

