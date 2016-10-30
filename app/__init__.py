#coding=utf-8
from flask import Flask, jsonify, abort, make_response, request , url_for
from flask.ext.restful import Api, Resource, reqparse , fields, marshal
from flask.ext.httpauth import HTTPBasicAuth
from flask.ext.sqlalchemy import SQLAlchemy
from app import config
from qiniu import Auth
from qiniu import BucketManager

app = Flask(__name__)
api = Api(app)
app.config['SQLALCHEMY_DATABASE_URI'] =  config.DB_URL
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SECRET_KEY'] = 'gao yang zui chou le'
db = SQLAlchemy(app)
auth = HTTPBasicAuth()
access_key = 'hdZdapjcdEK2vbVKTo--ETEciepTc9Eqs12BKS7T'
secret_key = 'QpWXhhBKo9tayM45xb-2oLaMyOqB4k8cyA4dfOCX'
#初始化Auth状态
q = Auth(access_key, secret_key)
#初始化BucketManager
bucket = BucketManager(q)
#你要测试的空间， 并且这个key在你空间中存在
bucket_name = 'course-plus'
bucket_domain = 'ofjhruj62.bkt.clouddn.com'

def getUrlOfKey(key):
    #有两种方式构造base_url的形式
    if not key:
        return ""
    base_url = 'http://%s/%s' % (bucket_domain, key)
    #可以设置token过期时间
    private_url = q.private_download_url(base_url, expires=3600)
    print(private_url)
    return private_url

def getTokenOfKey(key):
    if not key:
        return ""
    token = q.upload_token(bucket_name, key, 3600)
    return token

from app import views
import course_plus.user
import course_plus.course
import course_plus.comment
import course_plus.paywithflask
import config

@auth.error_handler
def auth_error():
    return make_response(jsonify({"code":-1,"message":"未登录或token过期"}), 403)