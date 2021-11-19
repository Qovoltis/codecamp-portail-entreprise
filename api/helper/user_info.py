"""helper file to generate user info dictionary"""
from typing import Union, List, Dict

from sqlalchemy import and_, desc
from sqlalchemy.orm import joinedload

from common import enums
from common.db_model.user import User, Role

"""groups of generation-serialization of the userInfo dictionary"""
MINIMAL = 'minimal'
INFO = 'info'

"""list of available groups"""
__GROUPS = [MINIMAL, INFO]


def get_user_info(user: User, groups: Union[List, None] = None) -> Dict:
    """returns the userInfo dictionary for the provided user and the given groups
    if no groups are provided the user_info is generated for all available groups
    if a non-existent group is provided raises an exception"""

    if groups is not None and not all(item in __GROUPS for item in groups):
        raise ValueError(f"some groups provided in input are invalid : accepted groups are ${','.join(__GROUPS)}")
    if groups is None:
        groups = __GROUPS
    user_info = {}
    if MINIMAL in groups:
        __update_user_info_for_minimal(user_info, user)
    if INFO in groups:
        __update_user_info_for_info(user_info, user)

    return user_info


def __update_user_info_for_minimal(user_info: Dict, user: User):
    """add the minimal group to userInfo dict :
    example {"email":"prenom.nom@dummy.com", "roles": ["employee", "administrator"]}"""
    user_info['email'] = user.email
    user_info['roles'] = list(map(lambda role: role.name, user.roles))


def __update_user_info_for_info(user_info: Dict, user: User):
    """add the info group to userInfo dict :
    example {"firstname": "Simon", "lastname": "THUILLIER", "organization": "Qovoltis"}"""
    user_info['info'] = {
        "firstname": user.firstname,
        "lastname": user.lastname,
        "organization": user.organization.name
    }
