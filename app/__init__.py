from flask import Flask, jsonify, abort, make_response, request , url_for
from flask.ext.restful import Api, Resource, reqparse , fields, marshal
from flask.ext.httpauth import HTTPBasicAuth
from flask.ext.sqlalchemy import SQLAlchemy
from app import config

app = Flask(__name__)
api = Api(app)
app.config['SQLALCHEMY_DATABASE_URI'] =  config.DB_URL
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SECRET_KEY'] = 'gao yang zui chou le'
db = SQLAlchemy(app)
auth = HTTPBasicAuth()
from app import views
import course_plus.user
import course_plus.course
import course_plus.comment
import config



