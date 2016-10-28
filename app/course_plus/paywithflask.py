# -*- coding: utf-8 -*-

import pingpp
from flask import Flask, jsonify, abort, g, make_response, request , url_for, Response
import json
import random
import string
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
    authorId = request.json.get("authorId")
    resourceId = request.json.get("resourceId")
    amount = request.json.get("amount")
    channel = request.json.get("channel")
    if not authorId and not resourceId:
        abort(400)
    if not channel or not amount:
        abort(400)
    params = {"amount":amount,"channel":channel}
    orderno = ''.join(random.sample(string.ascii_letters + string.digits, 8))
    record = TradeRecord()
    record.orderNo = orderno
    record.userId = g.user.id
    record.authorId = authorId
    record.attachmentId = resourceId
    record.cost = amount
    record.createdAt = datetime.datetime.now()
    record.updatedAt = record.createdAt
    record.orderStatus = 0
    db.session.add(record)
    db.session.commit() 
    extra = dict(
        success_url='http://www.yourdomain.com/success',
        recordId = record.id
        # cancel_url='http://www.yourdomain.com/cancel'
    )   
    if isinstance(params, dict):
        params['order_no'] = orderno
        params['app'] = dict(id='app_jnz9COjH08O4vLaD')
        params['currency'] = 'cny'
        params['client_ip'] = '127.0.0.1'
        params['subject'] = 'course+资料下载'
        params['body'] = 'Your Body'
        params['extra'] = extra
    print params
    pingpp.api_key = 'sk_test_OWrPOCPm94q5j5qXLO5e1OO4'
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
        recordId = charge['extra']['recordId']
        record = Trade.query.get(recordId)
        if record :
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
    record = Trade.query.get(id)
    if (record.orderStatus == 1):
       return make_response(jsonify(SimpleResult(1,"支付成功").json()), 200)
    else:
       return make_response(jsonify(SimpleResult(-1,"支付未成功").json()), 405)


@app.errorhandler(400)
def bad_request(error):
    return make_response(jsonify(SimpleResult(-1,"缺少参数").json()), 400)
