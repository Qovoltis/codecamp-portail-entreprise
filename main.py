# standard libraries imports
import os
# third-party libraries imports
import eventlet
import click
from dotenv import load_dotenv
# project imports
from api.launcher import create_app

eventlet.monkey_patch(socket=False)
# load .env files if any
load_dotenv()
# create flask app object
application = create_app()


@click.command()
@click.option('--host', default='127.0.0.1', help='Host ip address')
@click.option('--port', default=8000, help='Access port')
def start_server(host, port):
    """Start a Flask development server on given host and port"""
    application.run(host=host, port=port)


if __name__ == '__main__':
    start_server()
