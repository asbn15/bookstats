from flask import Flask
import config as cfg

app = Flask(__name__)
app.secret_key = cfg.secret_key
from web import routes
