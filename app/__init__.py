from flask import Flask
from flask_login import LoginManager
from peewee import *
from playhouse.sqlite_ext import *
from playhouse.flask_utils import FlaskDB, get_object_or_404, object_list
from micawber import bootstrap_basic
from micawber.cache import Cache as OEmbedCache
import config

app = Flask(__name__)
app.config.from_object('config')

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

flask_db = FlaskDB(app)
database = flask_db.database

oembed_providers = bootstrap_basic(OEmbedCache())

from app import views
from app import models
