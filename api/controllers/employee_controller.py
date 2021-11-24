from datetime import datetime

from flask import Blueprint, g, request, json, jsonify

from common.db_model import rbac

from api.helper.allowed_charge_points import allowed_charge_points
from api.auth import token_auth

employee_api = Blueprint('employee', __name__)


@employee_api.route('/list-allowed-charge-points', methods=['GET'])
@rbac.allow(['employee'], methods=['GET'], endpoint="employee.list_allowed_charge_points")
@token_auth.login_required
def list_allowed_charge_points():
    """Returns the list of charge points this employee has access to"""

    limit = int(request.args.get('limit', 10))
    offset = int(request.args.get('offset', 0))
    sort = request.args.get('sort', 'reference')
    order = request.args.get('order', 'asc')
    _filter = request.args.get('filter', None)

    if _filter:
        _filter = json.loads(_filter)
    else:
        _filter = {}

    _filter['user_id'] = g.current_user.id
    _filter['unexpired_at'] = datetime.utcnow().strftime('%Y-%m-%d')

    data = allowed_charge_points(limit, offset, sort, order, _filter)

    response = jsonify(data)
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.status_code = 200
    return response
