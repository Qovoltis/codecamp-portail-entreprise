import logging
import os
from logging.handlers import RotatingFileHandler
from typing import Dict, Union
import enum
from flask_sqlalchemy import SQLAlchemy, Model

db = SQLAlchemy(session_options={"autoflush": False, "autocommit": False, "expire_on_commit": False})

log_filepath = f"{os.environ.get('LOG_FILEPATH','./logs')}/sqlalchemy.log"
log_handler = RotatingFileHandler(
    log_filepath,
    mode='a',
    maxBytes=200000,
    backupCount=5
)
log_formatter = logging.Formatter('%(asctime)s %(name)s %(module)s  %(lineno)d %(levelname)s %(message)s')
log_handler.setFormatter(log_formatter)

logging.getLogger('sqlalchemy.engine').addHandler(log_handler)
logging.getLogger('sqlalchemy.orm').addHandler(log_handler)

log_handler.setLevel(logging.INFO)
logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
logging.getLogger('sqlalchemy.orm').setLevel(logging.WARNING)


# helper class to overload model declaration for entities and benefit from its helper methods
class BasicModel:
    """
    This is a basic SQLAlchemy model.
    The Basic model can be inherited to add common features.
    Such as returning a string representation of any SQLAlchemy model or dictionary containing model attribute.
    It should be the first class in order of inheritance.
    """
    def __get_non_relational_attributes(self):
        """
        Get a list of non attribute excluding relationship-based attribute
        """
        data_mem = [k for k in self.__dict__.keys() if not k.startswith(('__', '_'))]
        # remove from keys keys that come from a relationship
        data_mem_no_rel = []
        for k in data_mem:
            relation_attr = False
            try:
                relation_attr = issubclass(type(self.__getattribute__(k)), Model)
                self.__getattribute__(k)[0]
                relation_attr = issubclass(type(self.__getattribute__(k)[0]), Model)

            except:
                pass
            finally:
                if not relation_attr:
                    data_mem_no_rel.append(k)
        return data_mem_no_rel

    def __repr__(self):
        """
        Return a String representation of instance. The string returned doesn't include relationship attributes.
        since relationships are defined on both classes (models) this can often incur recursive calls on relationship.
        Resulting either in an exception or a very very long string representation.
        """
        data_mem = self.__get_non_relational_attributes()
        ret_str = f''
        for idx, member in enumerate(data_mem):
            value = self.__getattribute__(member)
            if idx == len(data_mem) - 1:
                ret_str += f"{member} = '{value}'"
            else:
                ret_str += f"{member} = '{value}', "
        return ret_str

    def to_dict(self) -> Dict[str, Union[str, int, float]]:
        """
        Return dictionary containing object attributes. This method doesn't return relationship attributes.
        It's meant to be used with methods like jsonify to return SQLAlchemy models as a json response.
        """
        m_dct = {}
        # remove from keys keys that come from a relationship
        data_mem_no_rel = self.__get_non_relational_attributes()

        for member in data_mem_no_rel:
            value = self.__getattribute__(member)
            if isinstance(value, enum.Enum):
                value = value.value
            m_dct[member] = value
        return m_dct


# to avoid sqlalchemy backreference problem all model scripts must be imported
# from . import parameter, error_code, role, user, adresse, \
#     company, technician, \
#     vehicule, compteur, site, borne, firmware, intervention, \
#     meter_values, offer, transaction, order, \
#     billing, cdr, dbfile


