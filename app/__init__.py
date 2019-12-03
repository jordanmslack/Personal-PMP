from flask import Flask
from flask_navigation import Navigation

from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
import flask_login
from dotenv import load_dotenv
import os, logging
import mimerender

db = SQLAlchemy()
nav = Navigation()
bcrypt = Bcrypt()
login_manager = flask_login.LoginManager()

mimerender.register_mime('pdf', ('application/pdf',))
mimerender = mimerender.FlaskMimeRender(global_charset='UTF-8')


def create_app():
    dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    load_dotenv(dotenv_path)

    app = Flask(__name__, template_folder='templates')

    nav.init_app(app)

    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)

    app.config['CSRF_SESSION_KEY'] = os.environ.get('CSRF_SESSION_KEY')
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')

    gunicorn_error_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers.extend(gunicorn_error_logger.handlers)

    app.logger.setLevel(logging.DEBUG)

    from app.tasks.controllers import task as task_module
    app.register_blueprint(task_module)

    return app


from app import models
