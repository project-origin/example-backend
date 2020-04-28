import sys
import logging

from flask import Flask
from flask_cors import CORS

from .urls import urls
from .settings import DEBUG, SECRET, CORS_ORIGINS

# Import models here for SQLAlchemy to detech them
from .models import VERSIONED_DB_MODELS


# -- Flask setup -------------------------------------------------------------

app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET
app.config['PROPAGATE_EXCEPTIONS'] = True

cors = CORS(app, resources={r'*': {'origins': CORS_ORIGINS}})


# -- URLs/routes setup -------------------------------------------------------

for url, controller in urls:
    app.add_url_rule(url, url, controller, methods=[controller.METHOD])


# -- Logging -----------------------------------------------------------------

if DEBUG:
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
    app.logger.setLevel(logging.DEBUG)
