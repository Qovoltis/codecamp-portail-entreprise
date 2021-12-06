import os
from dotenv import load_dotenv

# load .env files if any
load_dotenv()


class ApiConfig(object):
    FLASK_ENV = os.environ.get('FLASK_ENV', 'development')
    DEBUG = bool(os.environ.get('DEBUG', True))
    TESTING = bool(os.environ.get('TESTING', True))
    ALLOW_ORIGIN = os.environ.get('ALLOW_ORIGIN', '*')
    CORS_SUPPORTS_CREDENTIALS = True
    RBAC_USE_WHITE = True
    USER_TOKEN_VALIDITY_SPAN = int(os.environ.get('USER_TOKEN_VALIDITY_SPAN', 3600))
    LOG_FILEPATH = os.environ.get('LOG_FILEPATH', './logs/')
    DATA_FILEPATH = os.environ.get('DATA_FILEPATH', './files/')
    DB_CURSORCLASS = 'DictCursor'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {'encoding': 'utf8'}
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{DATA_FILEPATH}/db.sqlite"

    @classmethod
    def to_string(cls) -> str:
        _dict = {**cls.__dict__}
        items = _dict.items()
        public_items = list(filter(lambda item: not item[0].startswith('__'), items))
        return f"Configuration: \n" + ", \n".join([f'{key} => {value}' for key, value in public_items])


def get_config():
    return ApiConfig
