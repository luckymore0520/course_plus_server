#coding=utf-8
import sys
reload(sys)
sys.setdefaultencoding('utf8')
from flask import Flask, jsonify, abort, g, make_response, request , url_for
from flask.ext.restful import Api, Resource
from sqlalchemy.orm import relationship, backref
from passlib.apps import custom_app_context as pwd_context
from itsdangerous import (TimedJSONWebSignatureSerializer
                          as Serializer, BadSignature, SignatureExpired)
from app import app,db,api,auth,getUrlOfKey,getTokenOfKey
import json
import datetime
import requests
from simple_result import SimpleResult


class User(db.Model):
    __tablename__ = 't_user'
    id = db.Column(db.Integer, primary_key=True)
    phone = db.Column(db.String(16), unique=True)
    password = db.Column(db.String(128))
    nickname = db.Column(db.String(32))
    icon = db.Column(db.String(32))
    email = db.Column(db.String(32))
    qq = db.Column(db.String(32))
    wechat = db.Column(db.String(32))
    introduction = db.Column(db.Text)
    enable = db.Column(db.Integer)
    gender = db.Column(db.Integer)
    createdAt = db.Column(db.DateTime)
    updatedAt = db.Column(db.DateTime)
    comments = relationship("Comment", backref = "User")
    token = ""

    def hash_password(self, raw_password):
        self.password = pwd_context.encrypt(raw_password)

    def verify_password(self, raw_password):
        return pwd_context.verify(raw_password, self.password)

    def generate_auth_token(self, expiration=36000):
        s = Serializer(app.config['SECRET_KEY'], expires_in=expiration)
        self.token = s.dumps({'id': self.id})
        return self.token

    @staticmethod
    def verify_auth_token(token):
        s = Serializer(app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except SignatureExpired:
            return None    # valid token, but expired
        except BadSignature:
            return None    # invalid token
        user = User.query.get(data['id'])
        return user

    def json(self):
        return {"id":self.id, "nickname":self.nickname, "icon":getUrlOfKey(self.icon),"gender":self.gender,"introduction":self.introduction ,"token":self.token}

# 校验密码
@auth.verify_password
def verify_password(username_or_token, password):
    # first try to authenticate by token
    user = User.verify_auth_token(username_or_token)
    if not user:
        # try to authenticate with username/password
        user = User.query.filter_by(phone=username_or_token).first()
        if not user or not user.verify_password(password):
            return False
    g.user = user
    return True


@app.route('/api/web/user/sendAuthCode', methods=['POST'])
def send_auth_code():
    phone = request.json.get("phone")
    if phone is None:
        abort(400)
    params = {'phonenumber': phone, 'coursePlus': 1}
    r = requests.post("http://www.mebox.top/index.php/Home/SMS/sendCode", data=params).json()
    if r["result"] == 1:
        return (jsonify(SimpleResult(1,"发送成功").json()),200)
    else:
        message = r["errorMessage"]["message"]
        return (jsonify(SimpleResult(-1,message).json()),400)

    # 发送验证码，这里需要第三方服务器

@app.route('/api/web/user/register', methods=['POST'])
def register():
    phone = request.json.get("phone")
    password = request.json.get("password")
    verifyCode = request.json.get("verifyCode")
    if phone is None or password is None or verifyCode is None:
        abort(400)
    params = {'phonenumber': phone, 'verifyCode': verifyCode}
    r = requests.post("http://www.mebox.top/index.php/Home/SMS/verifyCode", data=params).json()
    if r["result"] == 0:
        return (jsonify(SimpleResult(-1,"验证失败").json()),400)
    # 验证验证码
    user = User.query.filter_by(phone=phone).first()
    if user:
        abort(401)       
    user = User()
    user.phone = phone;
    user.hash_password(password)
    user.createdAt = datetime.datetime.now()
    user.updatedAt = user.createdAt
    user.gender = 3
    user.nickname = "用户" + phone
    user.enable = 1
    db.session.add(user)
    db.session.commit()
    token = user.generate_auth_token(6000)
    g.user = user
    return (jsonify(user.json()),200)

@app.route('/api/web/user/resetPassword', methods=['POST'])
def resetPassword():
    phone = request.json.get("phone")
    password = request.json.get("password")
    verifyCode = request.json.get("verifyCode")
    if phone is None or password is None or verifyCode is None:
        abort(400)
    # 验证验证码
    user = User.query.filter_by(phone=phone).first()
    if not user:
        return (jsonify(SimpleResult(-1,"手机号未注册").json()),400)
    else:
        user.hash_password(password)
        user.updatedAt = datetime.datetime.now()
        db.session.add(user)
        db.session.commit()
    return (jsonify(SimpleResult(0,"重置成功").json()),200)


@app.route('/api/web/file/getFileToken', methods=['GET'])
def getFileToken():
    key = request.args.get("key")
    if not key:
        abort(400)
    token = getTokenOfKey(key)
    return (jsonify(SimpleResult(0,token).json()),200)



@app.route('/api/web/user/checkUserIsValid', methods=['GET'])
def checkUserIsExist():
    phone = request.args.get("phone")
    if phone is None:
        abort(400)  
    user = User.query.filter_by(phone=phone).first()
    if not user:
        return (jsonify(SimpleResult(0,"手机号可用").json()),200)
    else:
        return (jsonify(SimpleResult(-1,"手机号已占用").json()),409)


@app.route('/api/web/user/login', methods=['POST'])
def login():
    phone = request.json.get("phone")
    password = request.json.get("password")
    if phone is None or password is None:
        abort(400)
    user = User.query.filter_by(phone=phone).first()
    if not user or not user.verify_password(password):
        return (jsonify(SimpleResult(-1,"账户名或密码错误").json()),400)
    else:
        token = user.generate_auth_token(600)
        g.user = user
        return (jsonify(user.json()),200)


@app.route('/api/user/user/changePassword', methods=['POST'])
@auth.login_required
def changePassword():
    oldPassword = request.json.get("oldPassword")
    newPassword = request.json.get("newPassword")
    if not oldPassword or not newPassword:
        abort(400)
    user = g.user
    if user.verify_password(oldPassword):
        user.hash_password(newPassword)
        db.session.add(user)
        db.session.commit()
        return (jsonify(SimpleResult(0,"修改成功").json()),200)
    else:
        return (jsonify(SimpleResult(-1,"原密码错误").json()),400)

@app.route('/api/user/user/getUserInfo', methods=['GET'])
@auth.login_required
def getUserInfo():
    user = g.user
    return (jsonify(user.json()),200)

def getCurrentUser(request):
    auth = request.authorization
    if not auth:
        return None
    token = auth.username
    return User.verify_auth_token(token)
    
@app.route('/api/user/user/updateUserInfo', methods=['POST'])
@auth.login_required
def updateUserInfo():
    nickname = request.json.get("nickname")
    gender = request.json.get("gender")
    avatar = request.json.get("avatar")
    user = g.user
    if nickname:
        user.nickname = nickname
    if gender:
        user.gender = gender
    if avatar:
        user.icon = avatar
    db.session.add(user)
    db.session.commit() 
    return (jsonify(user.json()),200)
   
@app.route('/api/resource')
@auth.login_required
def get_resource():
    return jsonify({'data': 'Hello, %s!' % g.user.phone})


@app.errorhandler(400)
def bad_request(error):
    return make_response(jsonify(SimpleResult(-1,"缺少参数").json()), 400)



@app.errorhandler(409)
def bad_request(error):
    return make_response(jsonify(SimpleResult(-1,"用户重复").json()), 409)


