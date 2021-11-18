from __future__ import annotations

from sqlalchemy.orm import joinedload

from . import db, BasicModel
from sqlalchemy import and_, desc
from datetime import datetime, timedelta
from typing import List, Union, Optional, Tuple

import random
import string
from common.helper import convert_to_datetime_if_necessary


# user/roles association table
from .role import Role

users_roles = db.Table(
    'users_roles',
    db.Column('user_id', db.Integer, db.ForeignKey('utilisateur.id')),
    db.Column('role_id', db.Integer, db.ForeignKey('role.id'))
)


class TypeUtilisateur(db.Model):
    """
       Determine the type of utilisateur
    """
    __tablename__ = 'typeutilisateur'
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String)


class Utilisateur(db.Model):
    """
    User model containing user data. Password field contains hashed passwords
    """
    __tablename__ = 'utilisateur'
    id: int = db.Column(db.Integer, primary_key=True)
    referenceUser: str = db.Column(db.String, nullable=False)
    email: str = db.Column(db.String, nullable=False)
    password: str = db.Column(db.String)
    active: bool = db.Column(db.Boolean, nullable=False)
    log_level: str = db.Column(db.String, nullable=False)
    compteqovoltis_id = db.Column(db.Integer, db.ForeignKey('compteqovoltis.id'), nullable=True)
    compteqovoltis: Compteqovoltis = db.relationship('Compteqovoltis')
    typeUtilisateurId = db.Column(db.Integer, db.ForeignKey('typeutilisateur.id'))
    typeutilisateur = db.relationship(TypeUtilisateur)
    nom = db.Column(db.String)
    prenom = db.Column(db.String)
    telephone = db.Column(db.String)
    adresse = db.Column(db.String)
    codepostal = db.Column(db.String)
    ville = db.Column(db.String)
    country_id = db.Column(db.Integer, db.ForeignKey('country.id'))
    country = db.relationship('Country')
    accept_commercial_notification = db.Column(db.Boolean)
    created_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime)
    transactions = db.relationship('Transaction', back_populates='user')
    vehicules = db.relationship('Vehiculeutilisateur', back_populates='user')
    roles = db.relationship('Role', secondary=users_roles, backref=db.backref('roles', lazy='dynamic'))
    id_tags = db.relationship('UserIdTag', back_populates='user')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        utc_now = datetime.utcnow()
        self.created_at = utc_now
        self.updated_at = utc_now
        self.active = True

    def __repr__(self):
        return f"id={self.id}, compteQoVoltisId={self.compteqovoltis_id}, nom={self.nom}, prenom={self.prenom}," \
               f"telephone={self.telephone}, email={self.email}, referenceUser={self.referenceUser}," \
               f"adresse={self.adresse}, codepostal={self.codepostal}," \
               f"ville={self.ville}, country={self.country}"

    @staticmethod
    def id_tag_generate():
        return ''.join(
            random.choice(string.ascii_lowercase + string.ascii_uppercase + string.digits) for _ in range(14))

    @staticmethod
    def generate_reference_user() -> str:
        return 'user:' + \
               ''.join(
                   random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(10))

    def add_role(self, role):
        self.roles.append(role)

    def add_roles(self, roles):
        for role in roles:
            self.add_role(role)

    def get_roles(self):
        # if user is registered in db therefore not anonymous,
        # but has no role associated to him return anonymous role.
        if not self.roles:
            yield Role.get_by_name('anonymous')
        else:
            # return generator over all roles
            for role in self.roles:
                yield role

    def has_role(self, role_lst: List[str]):
        """
        Verifies if user has specific any of passed rights.

        :param role_lst: list of roles to verify if user has access to.
        :return: Return True if user has any of the passed rights and False otherwise.
        """
        for role in self.roles:
            if role.name in role_lst:
                return True
        return False

    def add_id_tag(self, id_tag) -> None:
        """Add an idTag to user.

        :param id_tag: UserIdTag
        :return: None
        """
        self.id_tags.append(id_tag)

    def get_permanent_id_tag(self, service: str = AuthorizedServices.AUTHORIZE_TRANSACTION) -> Union[UserIdTag, None]:
        """Return the permanent active idTag for user. If user doesn't have an active permanent idTag returns None
        :return: UserIdTag, the active idTag for user or None
        """
        id_tags = UserIdTag.query. options(
            joinedload(UserIdTag.auth_services, innerjoin=False).
            joinedload(ServiceAuthorization.service, innerjoin=False)). \
            filter(
            and_(and_(UserIdTag.utilisateur_id == self.id, UserIdTag.active.is_(True)),
                 and_(UserIdTag.bloque.is_(False), UserIdTag.typetag_id == 1)
                 )). \
            all()

        for id_tag in id_tags:
            for auth_service in id_tag.auth_services:
                auth_service: ServiceAuthorization
                if auth_service.service.name == service:
                    return id_tag

        return None

    @staticmethod
    def get_user_by_tag(id_tag: str) -> Union[Utilisateur, None]:
        """Get the user from db who has the given idTag. If no user has been found return None

        :param id_tag: str, the idTag associated with the user
        :return: Utilisateur, The user associated with the given idTag
        """
        if not id_tag or id_tag == '':
            return None
        return Utilisateur.query.join(UserIdTag).filter(UserIdTag.tag == id_tag).one_or_none()

    @staticmethod
    def get_user_by_reference(reference: str) -> Utilisateur:
        """Get user by its reference. Reference matches column `utilisateur.referenceUser` in database.
        Returns None if no user has been found

        :param reference: str, user reference
        return: Utilisateur, user corresponding to the reference or None otherwise
        """
        return Utilisateur.query.filter_by(referenceUser=reference).one_or_none()


class UserAppEvent(BasicModel, db.Model):
    """table for logging events from user applications"""
    __tablename__ = 'user_app_event'
    id: int = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('utilisateur.id'), nullable=False)
    user: Utilisateur = db.relationship(Utilisateur, enable_typechecks=False)
    origin: str = db.Column(db.String, nullable=False)
    level: str = db.Column(db.String, nullable=False)
    type: str = db.Column(db.String, nullable=False)
    emission_date: datetime = db.Column(db.DateTime(3), nullable=False)
    reception_date: datetime = db.Column(db.DateTime(3), nullable=False)
    delay: int = db.Column(db.Integer, nullable=False)
    important_value: Optional[str] = db.Column(db.String, nullable=True)
    payload: Optional[str] = db.Column(db.Text, nullable=True)
    sid: str = db.Column(db.String, nullable=True)


class TypeWhiteList(db.Model):
    """
       the different types of ways to authenticate on borne (see useridtag)
    """
    __tablename__ = 'typewhitelist'
    id = db.Column(db.Integer, primary_key=True)
    libelle = db.Column(db.String)
    code = db.Column(db.String)


class TypeTag(db.Model):
    """
       the different types of ways to authenticate on borne (see useridtag)
    """
    __tablename__ = 'typetag'
    id = db.Column(db.Integer, primary_key=True)
    libelle = db.Column(db.String)
    code = db.Column(db.String)
    extern = db.Column(db.Boolean)


class UserIdTag(BasicModel, db.Model):
    """
        each entry in this table represent a way for the user to authenticate on bornes : either with :
        - a default (permanent tag : given from a QrCode on the phone app
        - an access badge
        - an access card
        also contains tag from gireve
    """
    __tablename__ = 'useridtag'
    id = db.Column(db.Integer, primary_key=True)
    tag = db.Column(db.String)
    identifiant_physique = db.Column(db.String)
    code_activation = db.Column(db.String)
    gireve_auth_id = db.Column(db.String)
    issuer = db.Column(db.String)
    utilisateur_id = db.Column(db.Integer, db.ForeignKey('utilisateur.id'))
    user: Utilisateur = db.relationship(Utilisateur, back_populates='id_tags', enable_typechecks=False)
    active = db.Column(db.Boolean)
    bloque = db.Column(db.Boolean)
    __datemaj = db.Column('datemaj', db.DateTime)
    __datecommande = db.Column('datecommande', db.DateTime)
    __dateenvoi = db.Column('dateenvoi', db.DateTime)
    __dateactivation = db.Column('dateactivation', db.DateTime)
    __dateblocage = db.Column('dateblocage', db.DateTime)
    __dateexpiration = db.Column('dateexpiration', db.DateTime)
    commentaire = db.Column(db.String)
    auth_services = db.relationship('ServiceAuthorization')
    cpsession = db.relationship('CpSession', back_populates='useridtag')
    typetag_id = db.Column(db.Integer, db.ForeignKey('typetag.id'))
    typetag: TypeTag = db.relationship(TypeTag)
    panier_id = db.Column(db.Integer, db.ForeignKey('panier.id'))
    panier = db.relationship('Panier')
    cdr_statutag_id = db.Column(db.Integer, db.ForeignKey('cdr_statutag.id'))
    statutag = db.relationship('StatuTag', backref='exceptionnalclosings')
    cdr_emsp_id = db.Column(db.Integer, db.ForeignKey('cdr_emsp.id'))
    emsp = db.relationship('Emsp', backref='exceptionnalclosings')
    cdr_authmethod_id = db.Column(db.Integer, db.ForeignKey('cdr_authmethod.id'))
    authmethod = db.relationship('AuthMethod')
    typewhitelist_id = db.Column(db.Integer, db.ForeignKey('typewhitelist.id'))
    typewhitelist = db.relationship('TypeWhiteList')

    @property
    def datemaj(self):
        return self.__datemaj

    @datemaj.setter
    def datemaj(self, datemaj):
        self.__datemaj = convert_to_datetime_if_necessary(datemaj)

    @property
    def datecommande(self):
        return self.__datecommande

    @datecommande.setter
    def datecommande(self, datecommande):
        self.__datecommande = convert_to_datetime_if_necessary(datecommande)

    @property
    def dateenvoi(self):
        return self.__dateenvoi

    @dateenvoi.setter
    def dateenvoi(self, dateenvoi):
        self.__dateenvoi = convert_to_datetime_if_necessary(dateenvoi)

    @property
    def dateactivation(self):
        return self.__dateactivation

    @dateactivation.setter
    def dateactivation(self, dateactivation):
        self.__dateactivation = convert_to_datetime_if_necessary(dateactivation)

    @property
    def dateblocage(self):
        return self.__dateblocage

    @dateblocage.setter
    def dateblocage(self, dateblocage):
        self.__dateblocage = convert_to_datetime_if_necessary(dateblocage)

    @property
    def dateexpiration(self):
        return self.__dateexpiration

    @dateexpiration.setter
    def dateexpiration(self, dateexpiration):
        self.__dateexpiration = convert_to_datetime_if_necessary(dateexpiration)

    def is_valid(self) -> bool:
        """Return whether or not the idTag is valid.
            TODO : change logic to take into account bloque and date expiration
        """
        return self.active

    def linked_to_service(self, service_name: str) -> bool:
        """verify whether a tag is linked to a service or not (id check only if link exists not if service
        is fully allowed right now)"""
        service_authorization = list(filter(
            lambda sa: sa.service.name == service_name,
            self.auth_services)
        )
        if len(service_authorization) < 1:
            return False
        else:
            return True

    def allowed_to_use_service(self, service_name: str) -> bool:
        """
        verify whether or not this tag is allowed to use a specific service. The only service for the moment is
        authorization for starting a transaction (or starting a transaction service).

        :param service_name: service name corresponding to service.name in database.
        :return: whether or not user has access to use a specific service, exp: starting a transaction.
        """
        if (not self.active) or self.bloque:
            return False
        service_authorization = list(filter(
            lambda sa: sa.service.name == service_name,
            self.auth_services)
        )
        # TODO for now expiration_date is disabled because handling rules about it are very unclear
        if len(service_authorization) < 1 or not service_authorization[0].authorized:
            return False
        else:
            return True

    @staticmethod
    def get_by_tag(tag: str) -> Optional[UserIdTag]:
        """returns if exists db userIdTag corresponding to this tag , preloading user and account info"""

        query = UserIdTag.query.\
            options(joinedload(UserIdTag.typetag, innerjoin=True)).\
            options(joinedload(UserIdTag.typewhitelist, innerjoin=False)).\
            options(joinedload(UserIdTag.user, innerjoin=False).joinedload(Utilisateur.compteqovoltis, innerjoin=False)). \
            filter_by(tag=tag)

        return query.one_or_none()


class Programme(BasicModel, db.Model):
    """history data table that gathers all user requirements for transactions"""
    __tablename__ = 'programme'
    id = db.Column(db.Integer, primary_key=True)
    utilisateur_id = db.Column(db.Integer, db.ForeignKey('utilisateur.id'))
    user = db.relationship(Utilisateur, enable_typechecks=False)
    borne_id = db.Column(db.Integer, db.ForeignKey('borne.id'))
    borne = db.relationship('Borne')
    __date = db.Column('date', db.DateTime)
    quantite = db.Column(db.Integer)  # watts
    duree = db.Column(db.Integer)  # number of minutes between start of the transaction and its wanted end
    modecharge_id = db.Column(db.Integer, db.ForeignKey('modecharge.id'))
    modecharge = db.relationship('ModeCharge')

    @property
    def date(self):
        return self.__date

    @date.setter
    def date(self, date):
        self.__date = convert_to_datetime_if_necessary(date)

    @staticmethod
    def get_last_by_user_and_borne(m_user: Utilisateur, m_borne) -> Union[Programme, None]:
        return Programme.query.filter(and_(Programme.utilisateur_id == m_user.id, Programme.borne_id == m_borne.id)). \
            order_by(Programme.__date.desc()).first()

    @staticmethod
    def get_default_programme() -> Programme:
        """returns the default programme, used if a user has no previous history on the charge point"""
        return Programme(
            date=datetime.utcnow(),
            quantite=50000,
            duree=240,  # minutes for 4 hours
        )


class TypeCompte(db.Model):
    """
       Determine the type of compteqovoltis
    """
    __tablename__ = 'typecompte'
    id = db.Column(db.Integer, primary_key=True)
    libelle = db.Column(db.String)
    account_prefix = db.Column(db.String)


class Compteqovoltis(db.Model):
    """
       Determine the type of compteqovoltis
    """
    __tablename__ = 'compteqovoltis'
    id = db.Column(db.Integer, primary_key=True)
    buyer_id = db.Column(db.String)
    reference = db.Column(db.String)
    email = db.Column(db.String)
    typecompte_id = db.Column(db.Integer, db.ForeignKey('typecompte.id'))
    typecompte: TypeCompte = db.relationship(TypeCompte)
    civilite = db.Column(db.String)
    nom = db.Column(db.String)
    prenom = db.Column(db.String)
    telephone = db.Column(db.String)
    adresse = db.Column(db.String)
    codepostal = db.Column(db.String)
    ville = db.Column(db.String)
    country_id = db.Column(db.Integer, db.ForeignKey('country.id'))
    country = db.relationship('Country')
    commentaire = db.Column(db.TEXT)
    __dateacceptationdescgv = db.Column('dateacceptationcgv', db.DateTime)
    __dateajoutmoyenpaiement = db.Column('dateajoutmoyendepaiement', db.DateTime)
    __datecreation = db.Column('datecreation', db.DateTime)
    code_comptable = db.Column(db.String)

    # backref -> utilisateurs to retrieve the various utilisateurs of this compte

    @property
    def dateacceptationdescgv(self):
        return self.__dateacceptationdescgv

    @dateacceptationdescgv.setter
    def dateacceptationdescgv(self, dateacceptationdescgv):
        self.__dateacceptationdescgv = convert_to_datetime_if_necessary(dateacceptationdescgv)

    @property
    def dateajoutmoyenpaiement(self):
        return self.__dateajoutmoyenpaiement

    @dateajoutmoyenpaiement.setter
    def dateajoutmoyenpaiement(self, dateajoutmoyenpaiement):
        self.__dateajoutmoyenpaiement = convert_to_datetime_if_necessary(dateajoutmoyenpaiement)

    @property
    def datecreation(self):
        return self.__datecreation

    @datecreation.setter
    def datecreation(self, datecreation):
        self.__datecreation = convert_to_datetime_if_necessary(datecreation)

    def get_default_creditcard(self):
        """return default creditcard for this account or None if there isn't"""
        for card in filter(lambda card: card.active and card.defaut, self.creditcards):
            return card
        return None

    def __repr__(self):
        return f"id={self.id}, typecompte_id={self.typecompte_id}, nom={self.nom}, " \
               f"prenom={self.prenom}, adresse={self.adresse}, codepostal={self.codepostal}, " \
               f"adresse={self.adresse}, codepostal={self.codepostal}, ville={self.ville}, " \
               f"telephone={self.telephone}, email={self.email}, commentaire={self.commentaire}" \
               f"country={self.country,}dateacceptationdescgv={self.dateacceptationdescgv}" \
               f"dateajoutmoyenpaiement={self.dateajoutmoyenpaiement}"

    def update_infos_from_user(self, user: Utilisateur):
        """utility method to update account informations from user informations"""
        self.nom = user.nom
        self.prenom = user.prenom
        self.email = user.email
        self.telephone = user.telephone
        self.adresse = user.adresse
        self.codepostal = user.codepostal
        self.ville = user.ville
        self.country = user.country

    @staticmethod
    def get_last_reference_increment_by_prefix(prefix: str) -> int:
        """returns last reference increment by prefix,
        0 if no reference beginning by this prefix exists
        raise ValueError if reference exists but end can't be cast to integer
        """
        query = Compteqovoltis.query.\
            filter(Compteqovoltis.reference.like(f"{prefix}%")).\
            order_by(Compteqovoltis.reference.desc()).\
            limit(1)

        last_account: Optional[Compteqovoltis] = query.one_or_none()
        if not last_account:
            return 0
        try:
            return int(last_account.reference.replace(prefix, ''))
        except Exception:
            raise ValueError(f"last reference for prefix {prefix} is {last_account.reference} "
                             f"whose end can't be cast to a valid integer")

    @staticmethod
    def get_next_reference_by_type_account(type: TypeCompte) -> str:
        """returns next available reference for a new compte, according to its type"""
        beginning = f"{type.account_prefix}{datetime.utcnow().strftime('%Y%m')}"
        last_increment = Compteqovoltis.get_last_reference_increment_by_prefix(beginning)
        return f"{beginning}{'%05d' % (last_increment + 1)}"


class EtatMessage(db.Model):
    """
       state of user notifications (new, already read, deleted)
    """
    __tablename__ = 'etatmessage'
    id = db.Column(db.Integer, primary_key=True)
    etat = db.Column(db.String)


from common.enums import UserMessageState, AuthorizedServices


class Message(db.Model):
    """
       in this table are stored user notifications (ex beginning or end of transaction, payment, etc...)
    """
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.TEXT)
    etatmessage_id = db.Column(db.Integer, db.ForeignKey('etatmessage.id'))
    etatmessage: EtatMessage = db.relationship(EtatMessage)
    utilisateur_id = db.Column(db.Integer, db.ForeignKey('utilisateur.id'))
    utilisateur: Utilisateur = db.relationship(Utilisateur, enable_typechecks=False)
    __created_at = db.Column('created_at', db.DateTime)

    def __init__(self, utilisateur: Utilisateur, message: str):
        new_state = EtatMessage.query.filter_by(etat=UserMessageState.NEW).first()
        self.utilisateur = utilisateur
        self.message = message
        self.created_at = datetime.utcnow()
        self.etatmessage = new_state

    def update(self, data):
        for key, item in data.items():
            if item is not None:
                setattr(self, key, item)
        db.session.commit()

    @property
    def created_at(self):
        return self.__created_at

    @created_at.setter
    def created_at(self, created_at):
        self.__created_at = convert_to_datetime_if_necessary(created_at)

    def to_dict(self):
        """returns a dictionnary of the message to send to user"""
        created_at = utc_tz.localize(self.created_at).astimezone(tx_tz)
        return {
            'id': self.id,
            'text': self.message,
            'etat': self.etatmessage.etat,
            'year': created_at.year,
            'month': created_at.month,
            'day': created_at.day,
            'hour': created_at.hour,
            'minute': created_at.minute,
            'all': created_at.strftime("%d/%m/%Y, %H:%M")
        }

    @staticmethod
    def __get_all_by_user_query(user: Utilisateur, state: str = None):
        query = Message.query.join(EtatMessage)
        if state is not None:
            condition = and_(
                Message.utilisateur_id == user.id,
                EtatMessage.etat == state
            )
        else:
            condition = and_(
                Message.utilisateur_id == user.id
            )
        return query.filter(condition)

    @staticmethod
    def get_all_by_user(user: Utilisateur, state: str = None):
        """get all messages for a given user with optional message state"""
        return Message.__get_all_by_user_query(user, state).order_by(desc(Message.id)).all()

    @staticmethod
    def count_all_by_user(user: Utilisateur, state: str = None):
        """count all messages for a given user with optional message state"""
        return Message.__get_all_by_user_query(user, state).count()


class PendingAction(db.Model):
    """
       Status of user's actions
    """
    __tablename__ = 'user_pending_action'
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String)
    email = db.Column(db.String)
    data = db.Column(db.TEXT)
    token = db.Column(db.String)
    created_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime)
    done_at = db.Column(db.DateTime)
    expiration_delay = db.Column(db.Integer)

    def __repr__(self):
        return f"id={self.id}, type={self.type}, " \
               f"email={self.email}, data={self.data}, token={self.token}, " \
               f"created_at={self.created_at}, updated_at={self.updated_at}, done_at={self.done_at}, " \
               f"expiration_delay={self.expiration_delay}"

    def update(self, data):
        for key, item in data.items():
            if item is not None:
                setattr(self, key, item)
        db.session.commit()

    @staticmethod
    def get_all_by_mail(mail: str, types: Optional[List[str]] = None) -> List[PendingAction]:
        """returns all pending actions corresponding to a given mail in chronologically descending order
        if types if specified only those of wanted types are returned"""
        query = PendingAction.query

        condition = (PendingAction.email == mail)

        if types is not None:
            condition = and_(
                condition,
                PendingAction.type.in_(types)
            )

        query = query.filter(condition).order_by(desc(PendingAction.created_at))
        return query.all()


class Service(db.Model):
    """
    Table containing list of services provided by the api.
    This is not to be mixed with web services and micro services. It's more related to business services such as
    the ability to start a transaction.
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    description = db.Column(db.String)

    # users = db.relationship('Utilisateur', secondary='service_authorization')
    # useridtags = db.relationship('ServiceAuthorization', back_populates='service')

    def __repr__(self):
        return f"id={self.id}, name={self.name}, description={self.description}"


class ServiceAuthorization(db.Model):
    """
    Association table for service and utilisateur tables.
    Each entry represent which user have access to which service.
    """
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'), primary_key=True)
    service: Service = db.relationship('Service')
    useridtag_id = db.Column(db.Integer, db.ForeignKey('useridtag.id'), primary_key=True)
    useridtag: UserIdTag = db.relationship('UserIdTag', back_populates='auth_services')
    authorized = db.Column(db.Integer)
    __expiration_date = db.Column('expiration_date', db.DateTime)

    def __repr__(self):
        return f"user_id={self.utilisateur_id}, service_id={self.service_id}," \
               f" authorized={self.authorized}, expiration_date={self.expiration_date.isoformat()}"

    @property
    def expiration_date(self):
        return self.__expiration_date

    @expiration_date.setter
    def expiration_date(self, expiration_date):
        self.__expiration_date = convert_to_datetime_if_necessary(expiration_date)
