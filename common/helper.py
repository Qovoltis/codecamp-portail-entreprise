import re
from datetime import datetime
from typing import Dict, Any

from dateutil import parser
from flask import jsonify, Response


def get_error_stacktrace(limit: int = None, full_stacktrace: bool = False, verify_exception: bool = True) -> str:
    """Obtain Exception stacktrace as well as full stacktrace from current context.
    Full stacktrace will only be concatenated to result if `full_stacktrace` was present.
    If no Exception is present in the current context return an empty string.

    see:
        :func:`~traceback.format_stack` and :func:`~traceback.format_exc`

    :param limit: int, the number of entries to consider from the stacktrace starting from method invocation
    :param full_stacktrace: bool, whether or not to concatenate the full stacktrace to result
    :param verify_exception: bool, whether to verify the precence of an exception before returning stacktrace
    :return: str, error stacktrace
    """
    import traceback

    if verify_exception and traceback.format_exc() == 'NoneType: None\n':
        return ''
    stack_trace = ''.join(traceback.format_stack(limit=limit))
    exception_trace = traceback.format_exc()
    stack_trace = f"{exception_trace}\nFull Traceback:\n{stack_trace}" if full_stacktrace else exception_trace
    return stack_trace


def standard_json_response(http_status_code: int = 200,
                           message: str = None,
                           data: Dict = None) -> Response:
    """Construct a standard API response.
    Having a method that constructs standard API responses
    ensures that all services are conform to the same schema.


    :param http_status_code: int, returned HTTP status code
    :param message: str, api returned message or error stack trace
    :param data: dict, custom data returned by each service
    :return: json response obtained using :func:`~jsonify`
    """

    # obtain current datetime in utc format if not present
    timestamp = datetime.utcnow()

    # Append the context stacktrace into passed stacktrace
    m_error_stacktrace = get_error_stacktrace()
    if message is not None:
        pass
    elif m_error_stacktrace != '':
        message = '\n' + m_error_stacktrace
    else:
        message = None

    # Construct response

    response = jsonify({
        'message': message,
        'timestamp': timestamp.isoformat(),
        'data': data
    })
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.status_code = http_status_code
    return response


def parse_timestamp(timestamp: str) -> datetime:
    """ parse the standard charge point timestamp (Ex : 2020-04-23T15:01:37.012Z)
    (ISO8601 with millisecond precision with UTC timeZone described in military notation (Z instead of UTC or +00:00))
    to an UTC aware datetime
    if parsing to a datetime is not possible the timestamp argument is returned
    """
    return parser.parse(timestamp, parserinfo)


iso8601_regex_1 = re.compile('^(?P<year>\\d{4})-'
                             '(?P<month>[0-1][0-9])-'
                             '(?P<day>[0-3][0-9])T'
                             '(?P<hour>[0-2][0-9]):'
                             '(?P<minute>[0-6][0-9]):'
                             '(?P<second>[0-6][0-9]).'
                             '(?P<millisecond>\\d{3})'
                             '(?P<zone>.+)$', re.IGNORECASE)
parserinfo = parser.parserinfo(yearfirst=True)


def convert_to_datetime_if_necessary(value: Any) -> datetime:
    """ helper function used for datetime fields setters
    if value is None returns None
    if value is a datetime returns it
    if value is a string call parse_timestamp to attempt parsing it, if fails returns ValueError exception
    if value is any other type returns TypeError exception
    """
    if value is None or isinstance(value, datetime):
        return value
    elif isinstance(value, str):
        return parse_timestamp(value)
    else:
        raise TypeError(f'Variable of type ${type(value)} is not convertible to DateTime')
