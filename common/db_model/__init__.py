"""
    DB model package contains SQLAlchemy model definitions
    Model classes also include repository (query) functions
"""
import logging
import os
from logging.handlers import RotatingFileHandler

from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy
from flask_rbac import RBAC

# initializing flask_sqlalchemy orm manager
db = SQLAlchemy(session_options={"autoflush": False, "autocommit": False, "expire_on_commit": False})
# initializing flask_rbac (Role Based Access Control) extension
rbac = RBAC()

# logging configuration
# load .env files if any
load_dotenv()
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
logging.getLogger('sqlalchemy.engine').setLevel(logging.DEBUG)
logging.getLogger('sqlalchemy.orm').setLevel(logging.DEBUG)

# to avoid sqlalchemy back-reference problems all model scripts must be imported
from . import user, address, charge_point, whitelist


