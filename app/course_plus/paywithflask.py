# -*- coding: utf-8 -*-

import pingpp
from flask import Flask, request, Response
import json
import random
import string
from app import app,db,api,getUrlOfKey,auth

# channel   alipay_pc_direct   alipay_wap
# amount 单位 分
@app.route('/api/user/pay', methods=['POST'])
@auth.login_required
def do_charge():
    print request.url
    params = request.get_json()
    orderno = ''.join(random.sample(string.ascii_letters + string.digits, 8))
    extra = dict(
        success_url='http://www.yourdomain.com/success',
        cancel_url='http://www.yourdomain.com/cancel'
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


