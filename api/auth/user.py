"""here we extend db.Model classes user, role and role_parents from common.db_model
in order to define them as RoleMixin and UserMixin"""
import common.db_model.role as role
import common.db_model.user as user
from . import rbac

from flask_rbac import RoleMixin, UserMixin
from werkzeug.security import check_password_hash, generate_password_hash


@rbac.as_user_model
class ActualUtilisateur(user.Utilisateur, UserMixin):
    __tablename__ = 'utilisateur'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # give user anonymous rights by default
        # there might be a bug regarding initializing users with 'anonymous' rights
        # self.roles.append(Role.get_by_name('anonymous'))

    def check_password(self, password):
        hsh_pass = self.password
        return check_password_hash(hsh_pass, password)

    @staticmethod
    def hash_password(password):
        return generate_password_hash(password)

    def get_roles(self):
        # if user is registered in db therefore not anonymous,
        # but has no role associated to him return anonymous role.
        if not self.roles:
            yield ActualRole.get_by_name('anonymous')
        else:
            # return generator over all roles
            for role in self.roles:
                yield role

    def has_role(self, srole: str) -> bool:
        if srole in map(lambda x: x.name, self.get_roles()):
            return True
        else:
            return False


@rbac.as_role_model
class ActualRole(role.Role, RoleMixin):

    def __init__(self, id, name):
        RoleMixin.__init__(self, name)
        self.id = id
        self.name = name
        # self.roles[name] = self

    def add_parent(self, parent):
        # You don't need to add this role to parent's children set,
        # relationship between roles would do this work automatically
        self.parents.append(parent)

    def add_parents(self, *parents):
        for parent in parents:
            self.add_parent(parent)


