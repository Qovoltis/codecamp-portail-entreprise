import werkzeug
from flask import Flask, render_template, request, g
from flask_cors import CORS

from api.auth import UserLogger
from common.helper import standard_json_response
from common.db_model import db, rbac
from api.config import get_config
from api.auth.token_manager import TokenManager


def create_app():

    app = Flask(__name__)
    # INIT APP CONF
    config = get_config()
    print(config.to_string())
    app.config.from_object(config)

    # init extensions
    cors: CORS = CORS(app)
    cors.init_app(app)
    rbac.init_app(app)
    db.init_app(app)
    app.token_manager = TokenManager(config.USER_TOKEN_VALIDITY_SPAN)

    # register blueprints
    from api.controllers.user_controller import user_api
    app.register_blueprint(user_api, url_prefix='/api/user')
    from api.controllers.employee_controller import employee_api
    app.register_blueprint(employee_api, url_prefix='/api/employee')
    from api.controllers.administrator_controller import administrator_api
    app.register_blueprint(administrator_api, url_prefix='/api/administrator')

    @app.errorhandler(werkzeug.exceptions.InternalServerError)
    def internal_server_error_handler(e):
        return standard_json_response(http_status_code=500, message=str(e))

    @app.errorhandler(werkzeug.exceptions.NotFound)
    def not_found_error_handler(e):
        return standard_json_response(http_status_code=404, message="Unknown HTTP URL.")

    __DEFAULT_LOGGER = UserLogger()

    @app.after_request
    def after_request(response):
        print("after_request")
        g.current_user = None
        g.user_logger = __DEFAULT_LOGGER
        return response

    def _get_http_routes():
        methods, http_routes = ['PUT', 'GET', 'POST', 'DELETE'], list()
        for rule in app.url_map.iter_rules():
            url_root = request.url_root.rsplit('/', 1)
            filtered_methods = [x for x in list(rule.methods) if x != 'OPTIONS' and x != 'HEAD']
            http_routes.append({"base_url": str(rule), "methods": ','.join(filtered_methods),
                                "arguments": ','.join(rule.arguments),
                                "endpoint": rule.endpoint,
                                "url": url_root[0] + str(rule)})
            http_routes.sort(key=lambda elem: elem['base_url'])
        return http_routes

    @app.route('/', methods=['GET'])
    @app.route('/index', methods=['GET'])
    @rbac.exempt
    def index():
        http_routes = _get_http_routes()
        return render_template('index.html', config_key='development',
                               http_routes=http_routes if len(http_routes) > 0 else None)

    print("Portail Entreprise API instanciated")
    return app
