# -*- coding: utf-8 -*-

import pingpp
from flask import Flask, jsonify, abort, g, make_response, request , url_for, Response
import json
import random
import string
from sqlalchemy import ForeignKey
from app import app,db,api,getUrlOfKey,auth
from course import Resource
from course import Author
from course import TradeRecord
from user import User
from simple_result import SimpleResult
import datetime
# channel   alipay_pc_direct   alipay_wap
# amount 单位 分
# authorId 作者id
# resourceId 
@app.route('/api/user/pay', methods=['POST'])
@auth.login_required
def do_charge():
    resourceId = request.json.get("resourceId")
    topicId = request.json.get("topicId")
    amount = request.json.get("amount")
    channel = request.json.get("channel")
    if not channel or not amount or not topicId:
        abort(400)
    params = {"amount":amount,"channel":channel}
    orderno = ''.join(random.sample(string.ascii_letters + string.digits, 8))
    record = TradeRecord()
    record.orderNo = orderno
    record.userId = g.user.id
    record.attachmentId = resourceId
    record.cost = amount
    record.topicId = topicId
    record.createdAt = datetime.datetime.now()
    record.updatedAt = record.createdAt
    record.orderStatus = 0
    db.session.add(record)
    db.session.commit() 
    extra = dict(
        success_url='http://118.178.137.101:3000/public/pay.html?id='+str(record.id),
        # cancel_url='http://www.yourdomain.com/cancel'
    )   
    subject = ""
    body = record.id
    if resourceId:
        subject = "course+资料下载"
    else:
        subject = "咨询费用"
    if isinstance(params, dict):
        params['order_no'] = orderno
        params['app'] = dict(id='app_jnz9COjH08O4vLaD')
        params['currency'] = 'cny'
        params['client_ip'] = '127.0.0.1'
        params['subject'] = subject
        params['body'] = body
        params['extra'] = extra
    print params
    pingpp.api_key = 'sk_live_DiX5WTmDer5G8mz5uLDinvvH'
    # pingpp.api_key = 'sk_test_OWrPOCPm94q5j5qXLO5e1OO4'
    pingpp.private_key_path = 'pingpp_rsa_private_key.pem'
    response_charge = pingpp.Charge.create(api_key=pingpp.api_key, **params)
    print 'Response_Charge: ' + str(response_charge)
    return Response(json.dumps(response_charge),
                    mimetype='application/json,charset=UTF-8')


@app.route('/api/webhooks', methods=['POST'])
def webhooks():
    event = request.get_json()
    if event['type'] == 'charge.succeeded':
        charge = event['data']['object']
        recordId = charge['body']
        record = TradeRecord.query.get(recordId)
        if record:
            record.orderStatus = 1
        db.session.add(record)
        db.session.commit()
        return Response(status=200)
    elif event['type'] == 'refund.succeeded':
        return Response(status=200)
    return Response(status=500)

@app.route('/api/user/pay/checkOrderStatus', methods=['GET'])
@auth.login_required
def checkTradeStatus():
    id = request.args.get("id")
    if not id:
        abort(400)
    record = TradeRecord.query.get(id)
    if (record.orderStatus == 1):
       return make_response(jsonify(record.json()), 200)
    else:
       return make_response(jsonify(SimpleResult(-1,"支付未成功").json()), 405)



class FeedBack(db.Model):
    __tablename__ = 't_feedback'
    id = db.Column(db.Integer, primary_key=True)
    createdAt = db.Column(db.DateTime)
    updatedAt = db.Column(db.DateTime)
    deletedAt = db.Column(db.DateTime)
    content = db.Column(db.Text)
    tradeId = db.Column(db.Integer, ForeignKey('t_trade.id'))
    userId = db.Column(db.Integer, ForeignKey('t_user.id'))


@app.route('/api/user/feedback/publishFeedBack', methods=['POST'])
@auth.login_required
def publishFeedback():
    content = request.json.get("content")
    tradeId = request.json.get("tradeId")
    if not content or not tradeId:
        abort(400)
    feedBack = FeedBack()
    feedBack.createdAt = datetime.datetime.now()
    feedBack.updatedAt = feedBack.createdAt
    feedBack.content = content
    feedBack.tradeId = tradeId
    feedBack.userId = g.user.id
    db.session.add(feedBack)
    db.session.commit()
    return make_response(jsonify(SimpleResult(0,"发布成功").json()), 200)
 
    

@app.errorhandler(400)
def bad_request(error):
    return make_response(jsonify(SimpleResult(-1,"缺少参数").json()), 400)
