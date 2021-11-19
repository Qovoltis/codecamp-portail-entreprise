# standard libraries imports
import os
# third-party libraries imports
import eventlet
import click
from dotenv import load_dotenv
# project imports
from api.launcher import create_app


@click.command()
@click.option('--host', default='127.0.0.1', help='Host ip address')
@click.option('--port', default=8000, help='Access port')
def start_server(host, port):
    """configure and create the test api server"""
    # load .env files if any
    load_dotenv()

    log_filepath = os.environ.get('LOG_FILEPATH', './logs')
    if not os.path.exists(log_filepath):
        os.mkdir(log_filepath)
    data_filepath = os.environ.get('DATA_FILEPATH', './files')
    if not os.path.exists(data_filepath):
        os.mkdir(data_filepath)

    eventlet.monkey_patch(socket=False)
    # create flask app object
    application = create_app()
    # run the server
    application.run(host=host, port=port)


if __name__ == '__main__':
    start_server()
