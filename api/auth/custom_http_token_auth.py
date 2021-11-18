import json
from functools import wraps

from flask import request, g
from flask_httpauth import HTTPTokenAuth

from common.helper import get_error_stacktrace


class CustomHTTPTokenAuth(HTTPTokenAuth):
    """this class is a simple wrapper of HTTPTokenAuth which redefines only login_required decorator
    in order to log user activities"""

    def login_required(self, f):
        @wraps(f)
        def decorated(*args, **kwargs):
            auth = self.get_auth()

            # Flask normally handles OPTIONS requests on its own, but in the
            # case it is configured to forward those to the application, we
            # need to ignore authentication headers and let the request through
            # to avoid unwanted interactions with CORS.
            if request.method != 'OPTIONS':  # pragma: no cover
                password = self.get_auth_password(auth)
                if not self.authenticate(auth, password):
                    # Clear TCP receive buffer of any pending data
                    # request.data
                    return self.auth_error_callback()

            g.user_logger.file_logger.info(f"Call on {f.__module__}.{f.__name__} ")
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
                    f"Exception while executing {f.__module__}.{f.__name__} "
                    f"with args {serialized_args} and kwargs {serialized_kwargs} : {get_error_stacktrace(full_stacktrace = False)}")
                raise err

        return decorated
