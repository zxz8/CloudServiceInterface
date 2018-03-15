# -*- coding: utf-8 -*-

from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse,JsonResponse
from weixin.models import Custom
from weixin.models import Verify
from weixin.models import CustomOrder
from weixin.models import OrderItem
from weixin import SendSmsRequest
from weixin import wzhifuSDK
from django.db import connection
import time
import datetime
import random
import json  
import re
import MySQLdb
import time
import uuid
import hashlib
import qrcode
import urllib2
import urllib
from aliyunsdkcore.client import AcsClient
import xml.etree.ElementTree as ET

"""
短信产品-发送短信接口
Created on 2017-06-12
"""
REGION = "cn-hangzhou"# 暂时不支持多region
APP_ID = "wx27b4aeccb2628d52"
APP_SECRET = "400d1c316791b450a96cea9fd343ef8d"
ACCESS_KEY_ID = "LTAIKPGhlNRX3Vmr"
ACCESS_KEY_SECRET = "YqscfUfsO7ukq86OyQZZQjx1cs9kc3"
TEMPLATE_ID = "5W2dF1qubxRbMDJDf7-nIP9p2o5sBOrUVryr3LzQMZs"
acs_client = AcsClient(ACCESS_KEY_ID, ACCESS_KEY_SECRET, REGION)
#conn = MySQLdb.connect(host="127.0.0.1",user="tangff",passwd="migrsoft*2017",db="1015shop",charset="utf8")

def rgx(cdata):
	rgx = re.compile("\<\!\[CDATA\[(.*F：)\]\]\>")
	m = rgx.search(cdata)
	if m:
		return m.group(1)
	else:
		return cdata

def rgx_data(array):
	for key,value in array.items():
		array[key]=rgx(value)

def wx_verify(request):
	return HttpResponse('qh3ZfWI2M06zTjuR')


def getAccessToken():
	string = "https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid="+APP_ID+"&secret="+APP_SECRET
	print string
	f = urllib.urlopen(string)
	data = f.read()
	data = json.loads(data)
	if 'access_token' in data:
		print data['access_token']
		return data['access_token']
	return 'null'

def ranstr():
	str = ''
	for i in range(32):
		str +=random.choice("abcdefghijklmnopqrstuvwxyz0123456789")
	return str


def getJsapiTicket():
	string = "https://api.weixin.qq.com/cgi-bin/ticket/getticket?access_token={0}&type=jsapi".format(getAccessToken())
	f = urllib.urlopen(string)
	data = f.read()
	data = json.loads(data)
	if 'ticket' in data:
		print data['ticket']
		return data['ticket']
	return 'null'

def sendOrderMessage(customOrderId, customId,amount,count,description,status):
	try:
		custom = Custom.objects.get(customId = customId)
	except Custom.DoesNotExist:
		return ''
	openid = custom.openid
	access_token = getAccessToken()
	string = "https://api.weixin.qq.com/cgi-bin/message/template/send?access_token="+access_token
	url = "http://www.haohuoshuo.com/item?openid="+openid +"&customOrderId="+customOrderId+"&description="+description+"&amount="+amount+"&status="+status
	data = {"touser":openid,"template_id":TEMPLATE_ID,"url":url,"data":{"first":{"value":"下单成功","color":"#173177"},"orderno":{"value":customOrderId,"color":"#173177"},"refundno":{"value":count,"color":"#173177"},"refundproduct":{"value":amount,"color":"#173177"},"remark":{"value":"点击链接进行支付","color":"#173177"}}}
	data = json.dumps(data)
	f = urllib.urlopen(string,data)
	res = f.read()
	print res
	return res

@csrf_exempt
def test(request):
	res = "orderMessage test."
	#res = sendOrderMessage('123','150772918489','0.01','desc','0')
	return HttpResponse(res)

#扫码开门方式
@csrf_exempt
def toOpen(request):
	if request.method == "POST":
		res = {"success":"false",'message':''}
		customId = request.POST['customId']
		shopId = request.POST['shopId']
		try:
			isOpen = Custom.objects.get(isused = shopId)
		except Custom.DoesNotExist:
			isOpen = None
		result = Custom.objects.get(customId = customId)
		if shopId != '0' and result.isused == '0' and isOpen is None:
			Custom.objects.filter(customId = customId).update(isused = shopId)
			res = {"success":"true",'message':''}
		return JsonResponse(json.dumps(res),safe=False)

@csrf_exempt
def callOpen(request):
	if request.method =="POST":
		shopId = request.POST['shopId']
		res = {'customId':''}
		if shopId !='0':
			try:
				canOpen = Custom.objects.get(isused = request.POST['shopId'])
			except Custom.DoesNotExist:
				canOpen = None
			if canOpen is not None:
				res['customId']=canOpen.customId
		return JsonResponse(json.dumps(res),safe=False)

	

@csrf_exempt
def notify(request):
	print request.body
	data = xmlToArray(request.body)
	print data
	if data['appid'] == APP_ID and data['result_code'] == 'SUCCESS' and data['return_code'] == 'SUCCESS':
		out_trade_no = data['out_trade_no']
		print out_trade_no
		total_fee = data['total_fee']
		total_fee = str(float(total_fee)/100)
		print total_fee
		transaction_id = data['transaction_id']
		print transaction_id
		openid = data['openid']
		CustomOrder.objects.filter(customOrderId = out_trade_no,amount = total_fee).update(orderId = transaction_id,result = '1')
		Custom.objects.filter(openid = openid).update(status = '0')
		return HttpResponse(1)
	return HttpResponse(2)

@csrf_exempt
def toPay(request):
	if request.method == "POST":
		customId = ''
		openid = ''
		if 'customId' in request.POST and 'openid' in request.POST:
			customId = request.POST['customId']
			openid = request.POST['openid']
		try:
			order = CustomOrder.objects.get(customId = customId, result='0')
		except CustomOrder.DoesNotExist:
			return JsonResponse(json.dumps({'url':''}),safe=False)
		url = 'http://www.haohuoshuo.com/item/?openid='+openid+'&customOrderId='+order.customOrderId+'&customId='+customId+'&status='+order.result+'&amount='+order.amount+'&description='+order.description
		print 'url='+url
		return JsonResponse(json.dumps({'url':url}),safe=False)
@csrf_exempt
def getConfig(request):
        if request.method == "POST":
                url = request.POST['url']
                noncestr = ranstr()
                jsapi_ticket = getJsapiTicket()
                timestamp = str(int(time.time()))
                string = "jsapi_ticket={0}&noncestr={1}&timestamp={2}&url={3}".format(jsapi_ticket,noncestr,timestamp,url)
                signature = hashlib.sha1(string).hexdigest()
                data = {'appId':APP_ID,'timestamp':timestamp,'nonceStr':noncestr,'signature':signature}
                return JsonResponse(json.dumps(data),safe=False)

		

@csrf_exempt
def callpay(request):
	if(request.method == 'POST'):
		print request.POST['openid']
		un = wzhifuSDK.UnifiedOrder_pub()
		print(request.POST['out_trade_no'] + request.POST['openid']+request.POST['body']+request.POST['total_fee']+request.POST['notify_url']+ request.POST['trade_type'])
		un.setParameter('out_trade_no',request.POST['out_trade_no'])
		un.setParameter('openid',request.POST['openid'])
		un.setParameter('body',request.POST['body'])
		un.setParameter('total_fee',request.POST['total_fee'])
		un.setParameter('notify_url',request.POST['notify_url'])
		un.setParameter('trade_type',request.POST['trade_type'])
		js = wzhifuSDK.JsApi_pub()
		js.setPrepayId(un.getPrepayId())
		return JsonResponse(json.dumps(js.getParameters()),safe=False)

@csrf_exempt
def entry(request):
	if request.method == 'GET':
		if 'customId' in request.GET:
			customId = request.GET['customId']
			username = request.GET['username']
			openid = request.GET['openid']
			return render(request, 'weixin/qr.html', {'username': username,'customId':customId,'openid':openid})
		if 'code' in request.GET :
			res = getOpenId(request.GET['code'])
			if 'errcode' in res or 'openid' not in res:
				message = json.dumps(res)
				return render(request, 'weixin/error.html',{'message': message})
			openid = res['openid']	
		else: 
				message = 'None'
				return render(request, 'weixin/error.html',{'message': message})
		try:
			result = Custom.objects.get(openid = openid)
		except Custom.DoesNotExist:
			    result = None
		if result is None :
			return render(request, 'weixin/register.html', {'openid': openid,})
		else :
			#print result.username
			return render(request, 'weixin/qr.html', {'username':result.username,'customId': result.customId,'openid':openid})


@csrf_exempt
def register(request):
	if request.method == 'POST':
		username = request.POST['username']
		password = request.POST['password']
		tel = request.POST['tel']
		code = request.POST['code']
		openid = request.POST['openid']
		if not username or not password or not tel or not code or not openid:
			message = 'empty error.'
			return render(request, 'weixin/error.html',{'message': message})
		try:
			verify = Verify.objects.get(tel=tel,code=code)
		except Verify.DoesNotExist:
			message = "验证码输入有误"
			return render(request, 'weixin/error.html',{'message': message})
		if verify.flag == '1':
			message = '手机号已被使用'
			return render(request, 'weixin/error.html',{'message': message})
		time_now = time.time()
		if (datetime.datetime.utcfromtimestamp(time_now) - datetime.datetime.utcfromtimestamp(float(verify.time_code))).total_seconds() > 3600:
			message = '验证码已过期'
			return render(request, 'weixin/error.html',{'message': message})
		try:
			result = Custom.objects.get(openid = openid)
		except Custom.DoesNotExist:
			result = None
		if result is None:
			customId = str(time.time()).replace('.','')
			g = Custom(customId = customId,tel = tel,username = username, password = hashlib.sha1(password).hexdigest(), openid = openid)
			g.save()
			verify.flag = '1'
			verify.save()
			data = {"vendorId":"1853","openid":openid,"mobelno":tel}
			data = {}
			data['vendorId'] = '1853'
			data['openid']= openid
			data['mobelno'] = tel
			para_data = urllib.urlencode(data)
			f = urllib.urlopen("http://shop.dianxiaohuo.net/rg/register",para_data)
			res = f.read()
			res = json.loads(res)
			print res['message']
			if res['status'] != 1:
				print("同步注册用户失败")
			url = "http://mem.dianxiaohuo.net/api/qxMem?m=getMemberForBox&token=2CB1FB6F1D2F032000A1D807E17EC4DD&timeStamp=1503387111716&reqJson={\"unionid\":\""+openid+"\"}"
			f = urllib.urlopen(url,'')
			res = f.read()
			res = json.loads(res)
			if res['returnCode'] == 10:
				mem = res['returnObject']
				Custom.objects.filter(customId = customId).update(customId = mem['memNo'])
				customId = mem['memNo']
				print "memNo = " + customId
			#qr_make(customId)
				message = '注册用户成功'
				return render(request, 'weixin/result.html', {'openid':openid,'message' : message,'username':username, 'customId': customId})
			else:
				return render(request, 'weixin/error.html',{'message':'注册失败'})
		else :
			message = '用户已经注册'
			return render(request, 'weixin/result.html', {'message' : message,'openid':openid,'username':result.username, 'customid': result.customId })
	"""else:
		if 'state' not in request.GET or request.GET['state']!= '123' :
			return HttpResponse('state error.')
		if 'code' not in request.GET :
			return HttpResponse('illegal access')
		data = {}
		data['appid'] = 'wx27b4aeccb2628d52'
		data['secret'] = '400d1c316791b450a96cea9fd343ef8d'
		data['code'] = request.GET['code']
		data['grant_type'] = 'authorization_code'
		url = 'https://api.weixin.qq.com/sns/oauth2/access_token?' + urllib.urlencode(data)
		response = urllib2.urlopen(url)
		html = response.read()
		res = json.loads(html, encoding='utf-8')
		print res
		openid = res['openid']
		print openid
		try:
			result = Custom.objects.get(openid = openid)
		except Custom.DoesNotExist:
			    result = None
		if result is None:
			return render(request, 'weixin/register.html', {'openid': openid,})
		else:
			message = '用户已经注册'
			return render(request, 'weixin/result.html', {'message' : message,})
"""
@csrf_exempt
def info(request):
	if request.method == 'GET':
		if 'code' in request.GET :
			res = getOpenId(request.GET['code'])
			if 'errcode' in res:
				message = json.dumps(res)
				return render(request, 'weixin/error.html',{'message': message})
			openid = res['openid']
		else :
			message = '非法访问'
			return render(request, 'weixin/error.html',{'message': message})
		try:
			result = Custom.objects.get(openid = openid)
		except Custom.DoesNotExist:
			result = None
		if result is None :
			message = '请用户先注册'
			return render(request, 'weixin/error.html',{'message': message})
		else :
			#path = '/static/' + result.customId + '.png'
			return render(request, 'weixin/customInfo.html', {'openid':openid,'customId': result.customId,'username':result.username, 'tel':result.tel})

@csrf_exempt
def resend(request):
	if request.method == 'POST':
		if 'action' not in request.POST or 'tel' not in request.POST:
			message = '数据错误'
			return render(request, 'weixin/error.html',{'message': message})
		action = request.POST['action']
		tel = request.POST['tel']
		print tel
		code = random.randint(1000,9999)
		print code
		__business_id = uuid.uuid1()
		print __business_id
		params = {'code': str(code)}
		try:
			result = Verify.objects.get(tel = tel)
		except Verify.DoesNotExist:
			result = None
		if result is None:
			ver = Verify(tel = tel, code = str(code), time_code = str(time.time()))
			ver.save()
		else:
			if result.flag == '1':
				return 'false'
			result.code = str(code)
			result.time_code = str(time.time())
			result.save()
		print send_sms(__business_id, tel, '拿了就走', 'SMS_91025042', json.dumps(params))
		return HttpResponse('true')

@csrf_exempt
def order(request):
	if request.method == 'GET':
		if 'code' in request.GET :
			res = getOpenId(request.GET['code'])
			if 'errcode' in res or 'openid' not in res:
				message = json.dumps(res)
				return render(request, 'weixin/error.html',{'message': message})
			openid = res['openid']	
		
		elif 'openid' in request.GET : 
			openid = request.GET['openid']
		else:
			message = 'None'
			return render(request, 'weixin/error.html',{'message': message})
		try:
			result = Custom.objects.get(openid = openid)
		except Custom.DoesNotExist:
			result = None
		if result is None :
			return render(request, 'weixin/register.html', {'openid': openid,})
		customId = result.customId
		customOrderList = CustomOrder.objects.filter(customId = customId).order_by('-createTime')
		if len(customOrderList) == 0:
			return render(request, 'weixin/none.html',{'message': '无历史订单记录'})
		return render(request, 'weixin/order.html',{'customOrderList': customOrderList.values(),'openid':openid})

@csrf_exempt
def item(request):
	if request.method =="GET":
		if not request.GET['customOrderId']:
			message='param error'
			return render(request, 'weixin/error.html',{'message',message})
		if request.GET['openid']:
			openid = request.GET['openid']
			try:
				result = Custom.objects.get(openid = openid)
			except Custom.DoesNotExist:
				    result = None
			if result is None :
				return render(request, 'weixin/register.html', {'openid': openid,})
			customId = result.customId
		else:
			message='param error'
			return render(request, 'weixin/error.html',{'message':message})
		customOrderId = request.GET['customOrderId']
		print customOrderId
		try:
			order = CustomOrder.objects.get(customOrderId = customOrderId)
		except CustomOrder.DoesNotExist:
			order = None
		if order is None :
			return render(request, 'weixin/error.html', {'openid': openid,})
		status = order.result
		amount = request.GET['amount']
		amount = int(float(amount)*100)
		description = request.GET['description']
		print description
		orderItemList = OrderItem.objects.filter(customOrderId = customOrderId,customId =customId).values()
		print orderItemList
		conn = MySQLdb.connect(host="127.0.0.1",user="tangff",passwd="migrsoft*2017",db="1015shop",charset="utf8")
		cur = conn.cursor(MySQLdb.cursors.DictCursor)
		for orderItem in orderItemList:
			for key,value in orderItem.items():
				if key == 'skuCode':
					sql = "select * from 1015shop.sku where skuCode ='" + value + "'"
					cur.execute(sql)
					rows = cur.fetchall()
					for row in rows :
						orderItem['skuName']=row['skuName']
		cur.close()
		conn.close()
		return render(request,'weixin/item.html',{'orderItemList':orderItemList,'status':status,'customOrderId':customOrderId,'openid':openid,'amount':amount,'description':description})

@csrf_exempt
def goodsplus(request):
	if request.method in ['POST','GET']:
		if request.method == 'POST':
			print request.POST
			if not request.POST['para']:
				res = {'status':'0','message':'参数格式错误','dataValue':''}
				return JsonResponse(json.dumps(res),safe=False)
			para = request.POST['para']
		elif request.method == 'GET':
			if not request.GET['para']:
				res = {'status':'0','message':'参数格式错误','dataValue':''}
				return JsonResponse(json.dumps(res),safe=False)
			para = request.GET['para']
		if not para:
			res = {'status':'0','message':'参数错误','dataValue':''}
			return JsonResponse(json.dumps(res),safe=False)
		qrcode = para
		url = "http://base.1015shop.com/api/exec?m=getCpuMessage&token=H8DH9Snx9877SDER5667&timeStamp=1503387111716&reqJson={\"QRCode\":\"" +qrcode + "\"}"
		f = urllib.urlopen(url,'')
		res = f.read()
		res = json.loads(res)
		"""
		vpos = para.find("vendorId")
		spos = para.find("storeCode")
		if vpos != -1 and spos != -1:
			if vpos < spos:
				print 1
				para = para[vpos+9:]
				apos = para.find('&')
				if apos > 0 and para:
					vendorId = para[:apos]
					spos = para.find("storeCode")
					para = para[spos+10:]
					print para
					apos = para.find('&')
					print apos
					if apos >=0 and para:
						storeCode = para[:apos]
					else:
						storeCode = para
			else:
				print 2
				para = para[spos+10:]
				apos = para.find('&')
				if apos >0 and para:
					storeCode = para[:apos]
					vpos = para.find("vendorId")
					para = para[vpos+9:]
					apos = para.find('&')
					if vpos >= 0 and para:
						vendorId = para[:apos]
					else:
						vendorId = para
		"""
		if res["returnCode"] == 10:
			data = res["returnObject"]
			vendorId = data["vendorId"]
			storeCode = data["storeCode"]
			if not vendorId or not storeCode :
				res = {'status':'0','message':'error','dataValue':''}
				return JsonResponse(json.dumps(res),safe=False)
			print("vendorId = "+vendorId)
			print("storeCode = "+ storeCode)
			conn = MySQLdb.connect(host="localhost",user="tangff",passwd="migrsoft*2017",db="1015shop",charset="utf8")
			#cur = conn.cursor(MySQLdb.cursors.DictCursor)
			cur = conn.cursor()

			sql = "select a.steelyardId,a.skuCode,b.skuName,a.skuNum from 1015shop.steelyard a, 1015shop.sku b where a.vendorId = b.vendorId and a.skuCode = b.skuCode and a.vendorId='"+vendorId + "' and locate('"+ storeCode + "',a.steelyardId) > 0 order by a.steelyardId asc"
			print sql
			n = cur.execute(sql)
			print n
			skulist = []
			if n >0 :
				for row in cur.fetchall():
					steelyardId = row[0]
					skuCode = row[1]
					skuName = row[2]
					skuNum = row[3]
					skulist.append({"steelyardId":steelyardId,"skuCode":skuCode,"skuName":skuName,"skuNum":'0'})
			print skulist
			cur.close()
			conn.close()
			res = {'status':'1','message':vendorId+'&'+storeCode,'dataValue':skulist}
			return JsonResponse(json.dumps(res),safe=False)
		res = {'status':'0','message':'error','dataValue':''}
		return JsonResponse(json.dumps(res),safe=False)

@csrf_exempt
def wx_verify(request):
	return HttpResponse('qh3ZfWI2M06zTjuR')

def arrayToXml(arr):
	xml = ["<xml>"]
        for k, v in arr.iteritems():
            	if v.isdigit():
                	xml.append("<{0}>{1}</{0}>".format(k, v))
           	else:
                	xml.append("<{0}><![CDATA[{1}]]></{0}>".format(k, v))
        xml.append("</xml>")
        return "".join(xml)

def xmlToArray(xml):
        array_data = {}
        root = ET.fromstring(xml)
        for child in root:
            	value = child.text
            	array_data[child.tag] = value
        return array_data

def send_sms(business_id, phone_number, sign_name, template_code, template_param=None):
	smsRequest = SendSmsRequest.SendSmsRequest()
	smsRequest.set_TemplateCode(template_code)
    	if template_param is not None:
		smsRequest.set_TemplateParam(template_param)
	smsRequest.set_OutId(business_id)
	smsRequest.set_SignName(sign_name);
	smsRequest.set_PhoneNumbers(phone_number)
	smsResponse = acs_client.do_action_with_exception(smsRequest)
	return smsResponse


def qr_make(s):
	img = qrcode.make(s)
	path = '/static/' + s + '.png'
	img.save('/SuperMarketTest/testProject/weixin' + path)
	return path

def getOpenId(code):
	data = {}
	data['appid'] = 'wx27b4aeccb2628d52'
	data['secret'] = '400d1c316791b450a96cea9fd343ef8d'
	data['code'] = code
	data['grant_type'] = 'authorization_code'
	url = 'https://api.weixin.qq.com/sns/oauth2/access_token?' + urllib.urlencode(data)
	response = urllib2.urlopen(url)
	html = response.read()
	res = json.loads(html, encoding='utf-8')
	return res

