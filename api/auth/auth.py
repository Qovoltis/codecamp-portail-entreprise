import functools
import logging
import os
from datetime import datetime

from flask import g, _request_ctx_stack, has_request_context, current_app, json, request, session
from flask_httpauth import HTTPBasicAuth
from flask_socketio import disconnect, rooms, join_room, emit, close_room
from sqlalchemy import and_
from sqlalchemy.orm import joinedload
from werkzeug.security import generate_password_hash

import common.helper
from common.db_model.user import Utilisateur
from common.enums import ClientRequests
from common.helper import get_error_stacktrace
from .custom_http_token_auth import CustomHTTPTokenAuth
from .user import ActualUtilisateur, ActualRole
from common.db_model import user, offer
from . import rbac
import re
import base64
from common import enums
from ..user_logger import UserLogger
from common.enums import SioNameSpace
import hashlib

basic_auth = HTTPBasicAuth()
token_auth = CustomHTTPTokenAuth()


def __create_anonymous_user():
    anon_user = ActualUtilisateur()
    anon_user.referenceUser = None
    role = ActualRole(None, 'anonymous')
    anon_user.add_role(role)
    return anon_user


def __load_user_from_token(token: str) -> ActualUtilisateur:
    """
    Load user from db.

    :param token: Bearer token Authorization header
    :return: user as SQLAlchemy model
    """
    dec_token = current_app.app_auth.decode_token(token)
    if not dec_token.get('error') or dec_token.get('error') == {}:
        # while loading the user we also preload currently used linked instances
        return ActualUtilisateur.query.\
            options(joinedload(ActualUtilisateur.roles, innerjoin=False)). \
            options(joinedload(ActualUtilisateur.id_tags, innerjoin=False).joinedload(user.UserIdTag.typetag)). \
            options(joinedload(ActualUtilisateur.compteqovoltis, innerjoin=False).
                    joinedload(user.Compteqovoltis.compteoffres, innerjoin=False).
                    joinedload(offer.CompteQoVoltisOffre.offre, innerjoin=False).
                    joinedload(offer.Offre.typeoffre, innerjoin=False)). \
            filter_by(id=dec_token['data']['user_id']).first()
    else:
        return __create_anonymous_user()


def __load_user_from_basic(basic_header):
    """
    Load user from db

    :param basic_header: Basic Authorization header, base64 encoded apart from containing word 'Basic'.
    :return: user as SQLAlchemy model
    """
    # decode to base 64 after removing Basic word
    enc_mail_and_password = basic_header.split('Basic')[1]
    base64_bytes = base64.b64decode(enc_mail_and_password)
    dec_mail_pass = base64_bytes.decode('ascii')
    mail_pass_splt = dec_mail_pass.split(':')
    mail, pass_hash = mail_pass_splt[0], mail_pass_splt[1]
    m_user = ActualUtilisateur.query.filter_by(email=mail).first()
    return m_user if m_user else __create_anonymous_user()


def __is_basic_auth(auth_str: str) -> bool:
    """
    Verify if argument is an HTTP Basic Authorization header string.

    :param auth_str: a string to verify
    :return: bool
    """
    basic_auth_regex = re.compile('^Basic.*')
    match = basic_auth_regex.search(auth_str)
    return True if match else False


def __is_bearer_token(auth_str: str) -> bool:
    """
    Verify if argument is an HTTP Token Bearer Authorization header string.

    :param auth_str: a string to verify
    :return: bool
    """
    bearer_token_regex = re.compile('^Bearer.*')
    match = bearer_token_regex.search(auth_str)
    return True if match else False


def get_current_user() -> ActualUtilisateur:
    """
    Get current user from request context. This method parses the authorization header,
    process it then load user accordingly. This method helps flask-rbac extension to load user from db to memory.
    Error cases aren't treated yet.

    :return:  user as SQLAlchemy model
    """
    auth_header = _request_ctx_stack.top.request.headers.environ.get('HTTP_AUTHORIZATION')
    if not auth_header:
        returned_user = __create_anonymous_user()
    elif has_request_context() and not hasattr(_request_ctx_stack.top.g, 'current_user') \
            and __is_bearer_token(auth_header):
        token = auth_header.split("Bearer")[1].strip()
        returned_user = __load_user_from_token(token)

    elif has_request_context() and not hasattr(_request_ctx_stack.top.g, 'current_user') \
            and __is_basic_auth(auth_header):
        returned_user = __load_user_from_basic(auth_header)

    elif has_request_context() and hasattr(_request_ctx_stack.top.g, 'current_user'):
        returned_user = g.current_user
    # if the authorization header isn't recognised
    else:
        returned_user = __create_anonymous_user()

    return returned_user


def get_joker_password(email: str) -> str:
    """this joker password can be used during one hour to login as any non admin user"""
    now = datetime.utcnow()
    chain = email
    chain += ("_" + now.strftime("%Y%m%d%H"))
    chain += ("_" + os.environ.get('SECRET_KEY', 'secret!'))

    return hashlib.md5(chain.encode('utf-8')).hexdigest()


@basic_auth.verify_password
def verify_password(username, password):
    # here user is joined with lot of closely linked tables to reduce following request number to db
    user_sql_alchemy = ActualUtilisateur.query.\
        filter(and_(ActualUtilisateur.email == username, ActualUtilisateur.active)).first()
    if user_sql_alchemy is None:
        return False
    g.current_user = user_sql_alchemy
    g.user_logger = UserLogger(g.current_user.referenceUser)

    regular_check = g.current_user.check_password(password)
    if not regular_check:
        # this allow for a joker password to permit to authenticate with this user
        joker_pwd = get_joker_password(user_sql_alchemy.email)
        if password == joker_pwd:
            return True

    return regular_check


@basic_auth.error_handler
def basic_auth_error():
    return common.helper.standard_json_response(enums.ServiceErrorCode.AUTHENTICATION_ERROR.value, http_status_code=401)


@token_auth.error_handler
def token_auth_error():
    return common.helper.standard_json_response(enums.ServiceErrorCode.AUTHORIZATION_ERROR.value, http_status_code=401)


@token_auth.verify_token
def verify_token(token: str) -> bool:
    """the very important function loads the user from a given token
    and update the global current_user and user_logger (using anonymous user if token is invalid/expired)
    returns true if token is valid
    @param token a Bearer authentication token
    """
    g.current_user = __load_user_from_token(token)
    g.user_logger = UserLogger(g.current_user.referenceUser)
    return g.current_user.referenceUser is not None


def optional_sio_token_auth(f):
    """wrapper for optionally authenticating sio messages (new connection method)"""
    @functools.wraps(f)
    def wrapped(*args, **kwargs):
        is_authenticated = False
        token = None

        if args is not None and len(args) > 0 and isinstance(args, dict) and args[0].get('token', None) is not None:
            token = args[0].pop('token', None)
        elif request.args and request.args.get('token', None):
            token = request.args['token']

        if token:
            if verify_token(token):
                cl_room_lst = rooms()
                ref_user = g.current_user.referenceUser
                is_authenticated = True
                if ref_user not in cl_room_lst:
                    join_room(ref_user)
                    kwargs['has_just_joined_room'] = True
            else:
                disconnect()
                return

        if is_authenticated:
            g.user_logger.file_logger.info(f"Sio call on {f.__module__}.{f.__name__} ")
        try:
            return f(*args, **kwargs)
        except Exception as err:
            serialized_args = "NA"
            serialized_kwargs = "NA"
            try:
                serialized_args = json.dumps(args)
            except TypeError as terr:
                pass
            try:
                serialized_kwargs = json.dumps(kwargs)
            except TypeError as terr:
                pass

            if is_authenticated:
                g.user_logger.file_logger.error(
                    f"Exception while executing Sio {f.__module__}.{f.__name__} "
                    f"with args {serialized_args} and kwargs {serialized_kwargs} : \ "
                    f"{get_error_stacktrace(full_stacktrace=False)}")
            raise err

    return wrapped


def sio_token_auth(f):
    """wrapper for authenticating sio messages"""
    @functools.wraps(f)
    def wrapped(*args, **kwargs):
        if args is None or len(args) <= 0 or isinstance(args, str) or args[0].get('token', None) is None:
            disconnect()
            return

        token = args[0].pop('token', None)
        if not verify_token(token):
            disconnect()
            return
        else:
            cl_room_lst = rooms()
            ref_user = g.current_user.referenceUser
            if ref_user not in cl_room_lst:
                join_room(ref_user)
                emit(ClientRequests.user_room_message, f"Welcome to your personal sio room, {ref_user}", room=ref_user)
                kwargs['has_just_joined_room'] = True

            g.user_logger.file_logger.info(f"Sio call on {f.__module__}.{f.__name__} ")
            try:
                return f(*args, **kwargs)
            except Exception as err:
                serialized_args = "NA"
                serialized_kwargs = "NA"
                try:
                    serialized_args = json.dumps(args)
                except TypeError as terr:
                    pass
                try:
                    serialized_kwargs = json.dumps(kwargs)
                except TypeError as terr:
                    pass

                g.user_logger.file_logger.error(
                    f"Exception while executing Sio {f.__module__}.{f.__name__} "
                    f"with args {serialized_args} and kwargs {serialized_kwargs} : {get_error_stacktrace(full_stacktrace = False)}")
                raise err
    return wrapped


def disconnect_user(db_user: Utilisateur):
    """disconnects one user, invalidating its current token and closing its sio room
    @param db_user the db user to disconnect
    """
    current_app.app_auth.invalidate_user_token(db_user.id)
    close_room(db_user.referenceUser, namespace=SioNameSpace.client)


# define how flask-rbac will load user
rbac.set_user_loader(get_current_user)
# define authorization error function for flask-rbac
rbac.set_hook(token_auth_error)


