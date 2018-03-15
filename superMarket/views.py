# -*- coding: utf-8 -*-
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
import json  
import MySQLdb
import time
import uuid
import datetime
import urllib
import zmq
from django.core.cache import cache

context = zmq.Context()
socket = context.socket(zmq.PUSH)
socket.connect('tcp://39.106.27.51:12300') #test
#socket.connect('tcp://47.94.92.14:12300') #operative

logFile = open('logFile.txt','a')

def http_get(url,reqJson):
	reqJson = json.dumps(reqJson)
	url += reqJson
	#print "HTTP GET: " + url
	print '\033[1;31;40m' + "HTTP GET: " + url + '\033[0m'
	response = urllib.urlopen(url)
	return response.read()

def http_post(url,reqJson):
	reqJson = json.dumps(reqJson)
	url += reqJson
	#print "HTTP POST: " + url
	print '\033[1;31;40m' + "HTTP POST: " + url + '\033[0m'
	response = urllib.urlopen(url,"")
	return response.read()

#CanCheck flag
g_dicCanCheck = {}

def check_stock(vendorId,shopId):
	print "vendorId: " + vendorId + " shopId: " + shopId + " check_stock start..."
	result = {'result':[], 'ErrMsg':''}
	#time.sleep(10)
	global g_dicCanCheck
	key = vendorId + shopId #vendorId + shopId
	reqJson = {}
	reqJson['vendorId'] = vendorId
	reqJson['storeCode'] = shopId
	reqJson['skuInfo'] = ''
	response = http_post("https://erp.1015bar.com/api/exec?m=getSkustockByVenStoreSku&token=H8DH9Snx9877SDER5667&reqJson=",reqJson)
	#print '\033[1;31;40m' + "HTTP response: " + response + '\033[0m'
	response = json.loads(response)
	print '\033[1;31;40m' + "HTTP response: " + response['returnMsg'] + '\033[0m'
	if response['returnCode'] == 10:
		conn = MySQLdb.connect(host="127.0.0.1",user="tangff",passwd="migrsoft*2017",db="1015shop",charset="utf8")
		sql = "select * from steelyard where shopId = '" + shopId + " and vendorId = '" + vendorId + "';"
		cur = conn.cursor(MySQLdb.cursors.DictCursor)
		n = cur.execute(sql)
		rows = cur.fetchall()
		dic = {} #shop stock
		for row in rows:
			#custom in, stop check_stock
			if key not in g_dicCanCheck:
				result['ErrMsg'] = 'Broken_check_stock'
				print "vendorId: " + vendorId + " shopId: " + shopId + " custom in, stop check_stock!"
				break
			skuCode = row['skuCode']
			if skuCode == "":
				continue
			#match skuCode
			sql = "select * from sku where (skuCode = '" + skuCode + "' or barcode = '" + skuCode + "') and vendorId = '" + vendorId + "';"
			#print sql
			n = cur.execute(sql)
			if n > 0:
				row0 = cur.fetchall()
				skuCode = row0[0]['skuCode']
			if skuCode in dic:
				dic[skuCode] = dic.get(skuCode) + round(float(row['skuNum'])) #shop stock sum
			else:
				dic[skuCode] = round(float(row['skuNum']))
		#for k in dic:
		#	print k,' ',dic[k]
		#match stock
		if key in g_dicCanCheck:
			print "<skuCode>  <skuNum>  <stock>  [diff]"
			for i in response['returnObject']:
				#time.sleep(5)
				#custom in, stop check_stock
				if key not in g_dicCanCheck:
					result['ErrMsg'] = 'Broken_check_stock'
					print "vendorId: " + vendorId + " shopId: " + shopId + " custom in, stop check_stock!"
					break
				stock = round(float(i['stock']))
				diff = 0.0
				if i['skuCode'] in dic:
					diff = dic[i['skuCode']] - stock
					print "<%s>\t<%d>\t<%d>\t[%d]" % (i['skuCode'], dic[i['skuCode']], stock, diff)
					#print "<" + i['skuCode'] + ">  <" + str(dic[i['skuCode']]) + ">  <" + str(stock) + ">  [" + str(diff) + "]"
					if diff != 0:
                                		res = {}
                                        	res['skuCode'] = i['skuCode']
                                        	res['skuName'] = i['skuName']
                                        	#res['skuNum'] = str(dic[i['skuCode']])
                                        	#res['stock'] = str(stock)
                                        	res['diff'] = str(diff)
                                        	result['result'].append(res)
				else:
					print "<%s>\t<none>\t<%d>\t[none]" % (i['skuCode'], stock)
					#print "<" + i['skuCode'] + ">  <none>  <" + str(stock) + ">  [none]"
		cur.close()
		conn.commit()
		conn.close()
	else:
		result['ErrMsg'] = 'Failed_query_erp'
		print "Failed to query the erp DB!!!"
		print "vendorId: " + vendorId + " shopId: " + shopId + " check_stock error!"
	if result['result'] != []:
		result['ErrMsg'] = 'Error_stock'
	#check_stock end, reset CanCheck flag
	if key in g_dicCanCheck:
		del g_dicCanCheck[key]
	print "vendorId: " + vendorId + " shopId: " + shopId + " check_stock end!"
	return result

def steelyard_get(req):
	reqJson = {}
	reqJson['vendorId'] = req['vendorId']
	reqJson['storeCode'] = req['shopId']
	response = http_post("https://base.1015bar.com/api/exec?m=getUsingScales&token=H8DH9Snx9877SDER5667&reqJson=",reqJson)
	#print '\033[1;31;40m' + "HTTP response: " + response + '\033[0m'
	response = json.loads(response)
	print '\033[1;31;40m' + "HTTP response: " + response['returnMsg'].encode("utf-8") + '\033[0m'
	if response['returnCode'] == 10:
		result = {'result':[]}
		for i in response['returnObject']['scalesDetailList']:
			if i['totalWeight'] > 0:
				dic = {} 
				dic['steelyardId'] = i['tiersAndScales']
				dic['skuCode'] = i['skuCode']
				dic['unitWeight'] = str(i['totalWeight'])
				dic['posX'] = i['posX']
				dic['posY'] = i['posY']
				dic['posZ'] = i['posZ']
				dic['currWeight'] = "0"
				dic['offsetWeight'] = "0"
				dic['status'] = "1"
				result['result'].append(dic)
	else:
		result = {'result':'Failure', 'ErrMsg':'Failed_query_erp'}
		print "Failed to query ERP!!!"
	return result

def Alarm(req):
	vendorId = str(req['vendorId'])
	shopId = str(req['shopId'])
	print '\033[1;31;40m' + "vendorId: " + vendorId + " shopId: " + shopId + " steelyardId: " + req['steelyardId'] + " running error!!!!!!" + '\033[0m'
	reqErrJson = {}
	reqErrJson['vendorId'] = vendorId
	reqErrJson['storeCode'] = shopId
	reqErrJson['type'] = str(int(req['type']) + 2)
	if 'cpuId' in req:
		reqErrJson['shelfCode'] = "1"
	else:
		reqErrJson['shelfCode'] = req['steelyardId'][-6:-2]
	reqErrJson['scales'] = req['steelyardId']
	reqErrJson['errorMsg'] = str(req['ErrMsg'])
	response = http_post("https://base.1015bar.com/api/exec?m=errorSendMsg&token=H8DH9Snx9877SDER5667&reqJson=",reqErrJson)
	print '\033[1;31;40m' + "HTTP response: " + response + '\033[0m'
	result = {'result': 'Success'}
	return result

def ShopHeartBeat(req):
	vendorId = str(req['vendorId'])
	shopId = str(req['shopId'])
	print "vendorId: " + vendorId + " shopId: " + shopId + " heart beat!"
	result = {'result': 'Success', 'shopIn':'', 'shopOut':''}
	reqJson = {}
	reqJson['vendorId'] = vendorId
	reqJson['storeCode'] = shopId
	response = http_post("https://base.1015bar.com/api/exec?m=storeMonitor&token=H8DH9Snx9877SDER5667&reqJson=",reqJson)
	print '\033[1;31;40m' + "HTTP response: " + response + '\033[0m'
	if req['in'] == 1:
		response = http_post("https://base.1015bar.com/api/exec?m=getInDoorStatus&token=H8DH9Snx9877SDER5667&reqJson=",reqJson)
		print '\033[1;31;40m' + "HTTP response: " + response + '\033[0m'
		response = json.loads(response)
		if response['returnCode'] == 10 and response['returnObject'] != {}:
		        result['shopIn'] = response['returnObject']['MemNo']
		else:
			print "Failed to getInDoorStatus from erp!"
	if req['out'] == 1:
		response = http_post("https://base.1015bar.com/api/exec?m=getPayMemNo&token=H8DH9Snx9877SDER5667&reqJson=",reqJson)
		print '\033[1;31;40m' + "HTTP response: " + response + '\033[0m'
		response = json.loads(response)
		if response['returnCode'] == 10 and response['returnObject'] != {}:
			result['shopOut'] = response['returnObject']['outMemNo']
		else:
			print "Failed to getPayMemNo from erp!"
	response = http_post("https://base.1015bar.com/api/exec?m=getCpuMessage&token=H8DH9Snx9877SDER5667&reqJson=",reqJson)
	#print '\033[1;31;40m' + "HTTP response: " + response + '\033[0m'
	response = json.loads(response)
	if response['returnCode'] == 10 and response['returnObject'] != {} and response['returnObject']['cmd'] != None and response['returnObject']['cmd'] != "":
		cmd = response['returnObject']['cmd']
		print "shopCmd: ", cmd
		if "upload" in cmd.lower() and ("log" in cmd.lower() or "client" in cmd.lower() or "trace" in cmd.lower()):
			result['shopCmd'] = cmd
			cmdArg = {}
			cmdArg['user'] = "administrator"
			cmdArg['pwd'] = "Gcwtled901"
			cmdArg['path'] = "ftp://47.95.242.148:21/pos_log/Debug/" #test
			#cmdArg['path'] = "ftp://47.95.242.148:21/pos_log/Release/" #operative
			result['shopCmdArg'] = cmdArg
		else:
			result['cmd'] = cmd
		reqJson['cmd'] = ""
		response = http_post("https://base.1015bar.com/api/exec?m=updateCpuByStoreCode&token=H8DH9Snx9877SDER5667&reqJson=",reqJson)
		print '\033[1;31;40m' + "HTTP response: " + response + '\033[0m'
	return result

def AdSubAppHeartBeat(req,adCmd):
	vendorId = str(req['vendorId'])
	shopId = str(req['shopId'])
	print "vendorId: " + vendorId + " shopId: " + shopId + " AdSubApp heart beat!"
	result = {'result': "Success", "timeStamp":str(int(time.time()))}
	reqJson = {}
	reqJson['cpuId'] = req['cpuId']
	if 'lastCmd' in req:
		print "version: %s  lastCmd: %s" % (req['version'], req['lastCmd'])
		if req['lastCmd'].find('_Success') > 0:
			reqJson['adCmd'] = ""
			adCmd = ""
	else:
		print "version: %s" % (req['version'])
	if 'adCmd' in reqJson:
		response = http_post("https://base.1015bar.com/api/exec?m=updateCpuByCpuId&token=H8DH9Snx9877SDER5667&reqJson=",reqJson)
		print '\033[1;31;40m' + "HTTP response: " + response + '\033[0m'
	if adCmd == "updateConfig":
		result['cmd'] = adCmd
		adCmdArg = {}
		adCmdArg['user'] = "administrator"
		adCmdArg['pwd'] = "Gcwtled901"
		adCmdArg['path'] = "ftp://47.95.242.148:21/ad_pub/" + req['cpuId'] + "/Config.json"
		result['cmdArg'] = adCmdArg
	elif adCmd == "update":
		result['cmd'] = adCmd
		adCmdArg = {}
		adCmdArg['user'] = "administrator"
		adCmdArg['pwd'] = "Gcwtled901"
		adCmdArg['path'] = "ftp://47.95.242.148:21/ad_pub/" + req['cpuId'] + "/AdSubApp.apk"
		result['cmdArg'] = adCmdArg
	else:
		if adCmd != None and adCmd != "":
			result['cmd'] = adCmd
	return result

def heartBeat(req,cmd,version):
	vendorId = str(req['vendorId'])
	shopId = str(req['shopId'])
	print "vendorId: " + vendorId + " shopId: " + shopId + " heart beat!"
	result = {'result': [], "timeStamp":str(int(time.time()))}
	reqJson = {}
	reqJson['cpuId'] = req['cpuId']
	if 'lastCmd' in req:
		print "battery: %s  version: %s  lastCmd: %s" % (req['battery'], req['version'], req['lastCmd'])
		if req['lastCmd'].find('_Success') > 0:
			reqJson['cmd'] = ""
			cmd = ""
	else:
		print "battery: %s  version: %s" % (req['battery'], req['version'])
	if version != req['version']:
		reqJson['version'] = req['version']
	if 'cmd' in reqJson or 'version' in reqJson:
		response = http_post("https://base.1015bar.com/api/exec?m=updateCpuByCpuId&token=H8DH9Snx9877SDER5667&reqJson=",reqJson)
		print '\033[1;31;40m' + "HTTP response: " + response + '\033[0m'
	del req['vendorId']
	del req['shopId']
	response = http_post("https://base.1015bar.com/api/exec?m=getDoorStatus&token=H8DH9Snx9877SDER5667&reqJson=",req)
	print '\033[1;31;40m' + "HTTP response: " + response + '\033[0m'
	response = json.loads(response)
	if response['returnCode'] == 10 and response['returnObject'] != None and response['returnObject'] != {}:
		dic = {}
		dic['userId'] = response['returnObject']['memNo']
		dic['type'] = response['returnObject']['memberType']
		dic['status'] = response['returnObject']['status']
		#dic['doorStatus'] = response['returnObject']['doorStatus']
		result['result'].append(dic)
	else:
		print "Failed to getDoorStatus from erp!"
	if cmd == "update":
		result['cmd'] = cmd
		cmdArg = {}
		cmdArg['user'] = "administrator"
		cmdArg['pwd'] = "Gcwtled901"
		cmdArg['path'] = "ftp://47.95.242.148:21/box_firmware/Debug/ScaleWeightMsg_user_scan_qrcode" #test
		#cmdArg['path'] = "ftp://47.95.242.148:21/box_firmware/Release/ScaleWeightMsg_user_scan_qrcode" #operative
		result['cmdArg'] = cmdArg
	elif cmd == "uploadLog":
		result['cmd'] = cmd
		cmdArg = {}
		cmdArg['user'] = "administrator"
		cmdArg['pwd'] = "Gcwtled901"
		cmdArg['path'] = "ftp://47.95.242.148:21/box_log/Debug/" + vendorId + "_" + shopId + ".log" + datetime.datetime.now().strftime('%Y%m%d%H%M%S') #test
		#cmdArg['path'] = "ftp://47.95.242.148:21/box_log/Release/" + vendorId + "_" + shopId + ".log" + datetime.datetime.now().strftime('%Y%m%d%H%M%S') #operative
		result['cmdArg'] = cmdArg
	else:
		if cmd != None and cmd != "":
			result['cmd'] = cmd
	return result

def heart_beat(req):
	result = {'result': []}
	return result

def shopEntry_in(req):
	vendorId = str(req['vendorId'])
	shopId = str(req['shopId'])
	print "vendorId: " + vendorId + " shopId: " + shopId + " custom in, stop check_stock!"
	#notify algorithm
	cmd = "INOUT$" + req['customId']+ "$" + str(1) + "$" + req['timeStamp'] + "$" + vendorId + "$" + shopId
	print cmd
	socket.send(cmd.encode('ascii'))
	logFile.write(cmd + '\n')
	logFile.flush()
	#reset CanCheck flag
	global g_dicCanCheck
	key = vendorId + shopId #vendorId + shopId
	if key in g_dicCanCheck:
		del g_dicCanCheck[key]
	else:
		print "vendorId: " + vendorId + " shopId: " + shopId + " not in check_stock!"
	result = {'result':'Success'}
	return result

def shopEntry_empty(req):
	vendorId = str(req['vendorId'])
	shopId = str(req['shopId'])
	print "vendorId: " + vendorId + " shopId: " + shopId + " empty! can check_stock!"
	global g_dicCanCheck
	key = vendorId + shopId #vendorId + shopId
	if key not in g_dicCanCheck:
		#g_dicCanCheck[key] = 1
		#result = check_stock(vendorId,shopId)
		result = {'result':[], 'ErrMsg':''}
	else:
		result = {'result':[], 'ErrMsg':'Checking_stock'}
		print "vendorId: " + vendorId + " shopId: " + shopId + " in check_stock!"
	return result

def shopEntryHistory_insert(req):
	#notify algorithm
	cmd = "INOUT$" + req['customId']+ "$" + str(0) + "$" + req['timeStamp'] + "$" + req['vendorId'] + "$" + req['shopId']
	print cmd
	socket.send(cmd.encode('ascii'))
	logFile.write(cmd + '\n')
	logFile.flush()
	conn = MySQLdb.connect(host="127.0.0.1",user="tangff",passwd="migrsoft*2017",db="1015shop",charset="utf8")
	cur = conn.cursor(MySQLdb.cursors.DictCursor)
	sql = "insert into shopentryhistory values('" + req['entryTime'] + "','" + req['exitTime'] + "','" + req['customId'] + "','" + req['vendorId'] + "','" + req['shopId'] + "');"
	print sql
	n = cur.execute(sql)
	cur.close()
	conn.commit()
	conn.close()
	if n > 0:
		result = {'result':'Success'}
	else:
		result = {'result':'Failure', 'ErrMsg':'Failed_insert_shopEntryHistory'}
		print "Failed to insert shopentryhistory!!!"
	return result

def customManager_get(req):
	reqJson = {}
	reqJson['vendorId'] = req['vendorId']
	reqJson['memNo'] = req['customId']
	response = http_post("https://mem.1015bar.com/api/qxMem?m=getMemberForBox&token=2CB1FB6F1D2F032000A1D807E17EC4DD&timeStamp=1503387111716&reqJson=",reqJson)
	#print "HTTP response: " + response
	print '\033[1;31;40m' + "HTTP response: " + response + '\033[0m'
	response = json.loads(response)
	if response['returnCode'] == 10:
		if response['returnObject'] != None and response['returnObject']['memNo'] != "":
			result = {'result':[]}
			dic = {}
			dic['userId'] = response['returnObject']['memNo']
			dic['type'] = response['returnObject']['memberType']
			dic['status'] = response['returnObject']['status']
			result['result'].append(dic)
		else:
			result = {'result':'Failure', 'ErrMsg':'Unknown_customId'}
			print "The erp DB does not have this customId!!!"
	elif response['returnCode'] == 20:
		result = {'result':'Failure', 'ErrMsg':'Unknown_customId'}
		print "The erp DB does not have this customId!!!"
	else:
		result = {'result':'Failure', 'ErrMsg':'"Failed_query_erp'}
		print "Failed to query the erp DB!!!"
	return result

def addskuStart(req):
	conn = MySQLdb.connect(host="127.0.0.1",user="tangff",passwd="migrsoft*2017",db="1015shop",charset="utf8")
	cur = conn.cursor(MySQLdb.cursors.DictCursor)
	sql = "insert into addsku(startTime,userId,skuMsgStart,vendorId,shopId) values('" + req['startTime'] + "','" + req['userId'] + "','" + str(req['skuMsg']) + "','" + req['vendorId'] + "','" + req['shopId'] + "');"
	print sql
	n = cur.execute(sql)
	cur.close()
	conn.commit()
	conn.close()
	if n > 0:
		result = {'result':'Success'}
	else:
		result = {'result':'Failure', 'ErrMsg':'Failed_start_addsku'}
		print "Failed to start addsku!!!"
	return result

def AddskuStart(req):
	strSkuMsg = json.dumps(req['skuMsg']).replace('\r','').replace('\n','').replace('  ','')
	conn = MySQLdb.connect(host="127.0.0.1",user="tangff",passwd="migrsoft*2017",db="1015shop",charset="utf8")
	cur = conn.cursor(MySQLdb.cursors.DictCursor)
	sql = "insert into addsku(startTime,userId,skuMsgStart,vendorId,shopId) values('" + req['startTime'] + "','" + req['userId'] + "','" + strSkuMsg + "','" + req['vendorId'] + "','" + req['shopId'] + "');"
	print sql
	n = cur.execute(sql)
	cur.close()
	conn.commit()
	conn.close()
	if n > 0:
		result = {'result':'Success'}
	else:
		result = {'result':'Failure', 'ErrMsg':'Failed_start_addsku'}
		print "Failed to start addsku!!!"
	return result

def addskuEnd(req):
	conn = MySQLdb.connect(host="127.0.0.1",user="tangff",passwd="migrsoft*2017",db="1015shop",charset="utf8")
	cur = conn.cursor(MySQLdb.cursors.DictCursor)
	sql = "update addsku set endTime = '" + req['endTime'] + "', skuMsgEnd = '" + req['skuMsg'] + "', status = '1' where userId = '" + req['userId'] + "' and shopId = '" + req['shopId'] + "' and status = '0' and vendorId = '" + req['vendorId'] + "';"
	print sql
	n = cur.execute(sql)
	cur.close()
	conn.commit()
	conn.close()
	n = 1
	if n > 0:
		result = {'result':'Success'}
	else:
		result = {'result':'Failure', 'ErrMsg':'Failed_end_addsku'}
		print "Failed to end addsku!!!"
	return result

def AddskuEnd(req):
	strSkuMsg = json.dumps(req['skuMsg']).replace('\r','').replace('\n','').replace('  ','')
	conn = MySQLdb.connect(host="127.0.0.1",user="tangff",passwd="migrsoft*2017",db="1015shop",charset="utf8")
	cur = conn.cursor(MySQLdb.cursors.DictCursor)
	sql = "update addsku set endTime = '" + req['endTime'] + "', skuMsgEnd = '" + strSkuMsg + "', status = '1' where userId = '" + req['userId'] + "' and shopId = '" + req['shopId'] + "' and status = '0' and vendorId = '" + req['vendorId'] + "';"
	n = cur.execute(sql)
	cur.close()
	conn.commit()
	conn.close()
	n = 1
	if n > 0:
		result = {'result':'Success'}
	else:
		result = {'result':'Failure', 'ErrMsg':'Failed_end_addsku'}
		print "Failed to end addsku!!!"
	return result

def ShoppingChart(req):
	result = {'result':'Success'}
	reqJson = {'payFlag':'0','saleDetailList':[]}
	reqJson['vendorId'] = int(req['vendorId'])
	reqJson['orderStore'] = req['shopId']
	reqJson['memberCode'] = req['userId']
	try:
		#req['createTime'] = req['createTime'].replace("2018/02/29", "2018/03/01")
		reqJson['timeStamp'] = str(int(time.mktime(time.strptime(req['createTime'], "%Y/%m/%d %H:%M:%S"))))
	except Exception, e:
		print "ShoppingChart Exception: ", e.message
		year = int(req['createTime'][0:4])
		month = int(req['createTime'][5:7])
		day = int(req['createTime'][8:10])
		oldTime = "%04d/%02d/%02d" % (year, month, day)
		print "oldTime ", oldTime
		if month != 12:
			month += 1
		else:
			year += 1
			month = 1
		newTime = "%04d/%02d/01" % (year, month)
		print "newTime ", newTime
		req['createTime'] = req['createTime'].replace(oldTime, newTime)
		reqJson['timeStamp'] = str(int(time.mktime(time.strptime(req['createTime'], "%Y/%m/%d %H:%M:%S"))))
	for i in req['skuMsg']:
		saleDetailList = {}
		saleDetailList['skuCode'] = i['skuCode'].replace(" ", "")
		saleDetailList['skuNum'] = int(i['skuCount'])
		saleDetailList['steelyardId'] = i['steelyardId']
		reqJson['saleDetailList'].append(saleDetailList)
	if reqJson['saleDetailList'] != []:
		#update custom status
		reqJson0 = {'status':'-1'}
		reqJson0['vendorId'] = int(req['vendorId'])
		reqJson0['memNo'] = req['userId']
		response = http_post("https://mem.1015bar.com/api/qxMem?m=updateMemStatus&token=2CB1FB6F1D2F032000A1D807E17EC4DD&timeStamp=1503387111716&reqJson=",reqJson0)
		print '\033[1;31;40m' + "HTTP response: " + response + '\033[0m'
	response = http_post("https://order.1015bar.com/api/exect?m=receiveOrderWithOutPay&token=H8DH9Snx9877SDER5667&reqJson=",reqJson)
	print '\033[1;31;40m' + "HTTP response: " + response + '\033[0m'
	return result

def skuGet(req):
	reqJson = {}
	reqJson['vendorId'] = req['vendorId']
	reqJson['storeCode'] = req['shopId']
	response = http_post("https://base.1015bar.com/api/exec?m=getUsingScales&token=H8DH9Snx9877SDER5667&reqJson=",reqJson)
	#print '\033[1;31;40m' + "HTTP response: " + response + '\033[0m'
	response = json.loads(response)
	print '\033[1;31;40m' + "HTTP response: " + response['returnMsg'].encode("utf-8") + '\033[0m'
	if response['returnCode'] == 10:
		result = {'result':[]}
		for i in response['returnObject']['scalesDetailList']:
			if i['totalWeight'] > 0:
				dic = {} 
				#dic['steelyardId'] = i['tiersAndScales']
				dic['steelyardId'] = "%02d%02d" % (int(i['tiersCode']), int(i['scalesCode']))
				dic['tiersCode'] = i['tiersCode']
				dic['scalesCode'] = i['scalesCode']
				dic['skuCode'] = i['skuCode']
				dic['unitWeight'] = str(i['totalWeight'])
				#dic['currWeight'] = ""
				result['result'].append(dic)
	else:
		result = {'result':'Failure', 'ErrMsg':'Failed_query_erp'}
		print "Failed to query ERP!!!"
	return result

def ShoppingCartEnd(req):
	result = {'result':'Success'}
	vendorId = str(req['vendorId'])
	shopId = str(req['shopId'])
	customId = str(req['customId'])
	cache_key = vendorId + "_" + shopId + "_" + customId
	cache.delete(cache_key)
	logFile.write("Succeed to delete " + cache_key + " ShoppingCart" + '\n')
	print "Succeed to delete " + cache_key + " ShoppingCart"
	logFile.flush()
	return result

def ShoppingCartGet(req):
	result = {'result':[]}
	vendorId = str(req['vendorId'])
	shopId = str(req['shopId'])
	customId = str(req['customId'])
	cache_key = vendorId + "_" + shopId + "_" + customId
	cache_None = "cache_None"
	cache_value = cache.get(cache_key,cache_None)
	if cache_value != cache_None:
		result['result'] = eval(cache_value)['saleList']
	strSkuMsg = json.dumps(result['result']).replace('\r','').replace('\n','').replace(' ','')
	logFile.write("Ready to send " + cache_key + " ShoppingCart " + strSkuMsg + '\n')
	print "Ready to send " + cache_key + " ShoppingCart " + strSkuMsg
	logFile.flush()
	return result

def ShoppingCartAdd(req):
	result = {'result':'Success'}
	vendorId = str(req['vendorId'])
	shopId = str(req['shopId'])
	customId = str(req['customId'])
	skuCode = str(req['skuCode'])
	skuCount = str(req['skuCount'])
	confidence = float(req['confidence'])
	#timeStamp = str(req['timeStamp'])
	if confidence >= 1:
		#use Memcached in Django
		cache_key = vendorId + "_" + shopId + "_" + customId
		cache_None = "cache_None"
		cache_value = cache.get(cache_key,cache_None)
		if cache_value != cache_None:
			nIsSkuCodeIn = 0
			dicValue = eval(cache_value)
			for i in dicValue['saleList']:
				if skuCode == i['skuCode']:
					i['skuCount'] += float(skuCount)
					cache.set(cache_key,str(dicValue))
					nIsSkuCodeIn = 1
					print "skuCode in"
					break
			if nIsSkuCodeIn == 0:
				saleList = {}
				saleList['skuCode'] = skuCode
				saleList['skuCount'] = float(skuCount)
				dicValue['saleList'].append(saleList)
				cache.set(cache_key,str(dicValue))
				print "skuCode not in"
		else:
			saleList = {}
			saleList['skuCode'] = skuCode
			saleList['skuCount'] = float(skuCount)
			dic = {'saleList':[]}
			dic['saleList'].append(saleList)
			cache.set(cache_key,str(dic))
			print "customId not in"
		logFile.write("Succeed to insert " + cache_key + " ShoppingCart " + cache.get(cache_key,cache_None) + '\n')
		print "Succeed to insert " + cache_key + " ShoppingCart " + cache.get(cache_key,cache_None)
		logFile.flush()
	return result

def CheckWeight(req):
	vendorId = str(req['vendorId'])
	shopId = str(req['shopId'])
	steelyardId = str(req['steelyardId'])
	skuCode = str(req['skuCode'])
	skuCount = str(req['skuCount'])
	operation = str(req['operation'])
	timestamp = str(req['timeStamp'])
	print "vendorId: " + vendorId + " steelyardId: " + steelyardId + " sku: " + skuCode + " operation: " + operation
	result = {'result':'Success'}
	if (operation == '0' or operation == '1') and skuCode != '' and skuCount != '0':
		result = {'result':'Failure', 'ErrMsg':'Unknown_steelyardId'}
		reqJson = {}
		reqJson['vendorId'] = vendorId
		reqJson['storeCode'] = shopId
		response = http_post("https://base.1015bar.com/api/exec?m=getUsingScales&token=H8DH9Snx9877SDER5667&reqJson=",reqJson)
		#print '\033[1;31;40m' + "HTTP response: " + response + '\033[0m'
		response = json.loads(response)
		print '\033[1;31;40m' + "HTTP response: " + response['returnMsg'].encode("utf-8") + '\033[0m'
		if response['returnCode'] == 10:
			for i in response['returnObject']['scalesDetailList']:
				if steelyardId == i['tiersAndScales']:
					x = i['posX']
					y = i['posY']
					z = i['posZ']
					#notify algorithm
					cmd = "SCALE$" + skuCode + "$" + skuCount + "$" + operation + "$" + timestamp + "$" + x + "," + y + "," + z + "$" + vendorId + "$" + shopId
					print cmd
					socket.send(cmd.encode('ascii'))
					result = {'result':'Success'}
					logFile.write(cmd + '\n')
					logFile.flush()
					break
		else:
			result = {'result':'Failure', 'ErrMsg':'Failed_query_erp'}
			print "Failed to query ERP!!!"
	return result

def steelyard_update(req):
	result = {'result':'Success'}
	return result

def steelyard_update_status(req):
	result = {'result':'Success'}
	return result

def steelyard_update_isError(req):
	result = {'result':'Success'}
	return result

def InsertTable(req):
	result = {'result':[], 'ErrMsg':''}
	primary_key = ""
	conn = MySQLdb.connect(host="127.0.0.1",user="tangff",passwd="migrsoft*2017",db="1015shop",charset="utf8")
	cur = conn.cursor(MySQLdb.cursors.DictCursor)
	sql = "show columns from " + req['TableName'] + ";"
	print sql
	n = cur.execute(sql)
	rows = cur.fetchall()
	for row in rows:
		if row['Key'] == "PRI":
			primary_key = row['Field']
	if primary_key == "":
		result['ErrMsg'] = "no_primary_key"
		print "no_primary_key"
	else:
		mFieldList = req['FieldName']
		n = mFieldList.index(primary_key)
		if n < 0:
			result['ErrMsg'] = "no_match_primary_key"
			print "no_match_primary_key"
		else:
			mDataList = req['Data']
			for i in mDataList:
				sql = "select * from " + req['TableName'] + " where " + primary_key + " = '" + i[primary_key] + "';"
				print sql
				n = cur.execute(sql)
				if n > 0:
					dic = {}
					for x in mFieldList:
						dic[x] = i[x]
					result['result'].append(dic)
					result['ErrMsg'] = "Already_exists"
					print "Already_exists"
				else:
					fields = ""
					values = ""
					for j in mFieldList:
						fields += j + ","
						values += "\"" + i[j] + "\"" + ","
					fields = fields[:-1]
					values = values[:-1]
			 		sql = "insert into "+ req['TableName'] + "(" + fields + ") values(" + values + ");"
					print sql
					n = cur.execute(sql)
					if n < 0:
						dic = {}
						for x in mFieldList:
							dic[x] = i[x]
						result['result'].append(dic)
						result['ErrMsg'] = "Failed_to_insert"
						print "Failed_to_insert"
	cur.close()
	conn.commit()
	conn.close()
	return result

@csrf_exempt
def index(request):
	if request.method == 'POST':
		result = {'result':'Failure', 'ErrMsg':'Unknown_reason'}
		if request.body.find('steelyard_update') < 0:
			print "\n[" + datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S') + "]"
			strTemp = request.body.replace('\r','').replace('\n','').replace('  ','')
			print '\033[1;31;40m' + strTemp + '\033[0m'
		#request.body.encode('utf-8').strip()
		req = json.loads(request.body,encoding="utf-8")
		if request.body.find('CheckWeight') > 0:
			if int(req['skuCount']) > 0:
				logFile.write(request.body)
				logFile.flush()
		if request.body.find('ShoppingCartAdd') > 0:
			logFile.write('\n' + request.body + '\n')
			logFile.flush()
		if 'cpuId' in req:
			#cpuId >>> vendorId shopId
			reqJson = {}
			reqJson['cpuId'] = req['cpuId']
			response = http_post("https://base.1015bar.com/api/exec?m=getCpuMessage&token=H8DH9Snx9877SDER5667&reqJson=",reqJson)
			#print '\033[1;31;40m' + "HTTP response: " + response + '\033[0m'
			response = json.loads(response)
			if response['returnCode'] == 10 and response['returnObject'] != {}:
                        	req['vendorId'] = response['returnObject']['vendorId']
                        	req['shopId'] = response['returnObject']['storeCode']
				print req['cpuId'], " >>> ", req['vendorId'], " ", req['shopId']
				cmd = response['returnObject']['cmd']
				adCmd = response['returnObject']['adCmd']
				version = response['returnObject']['version']
				if cmd != "":
					print "cmd: ", cmd
				if adCmd != "":
					print "adCmd: ", adCmd
			else:
				result = {'result':'Failure', 'ErrMsg':'Unknown_cpuId'}
				print "Failed to translate cpuId! ", req['cpuId']
				#return HttpResponse(json.dumps(result,ensure_ascii=False))
				return HttpResponse(json.dumps(result,ensure_ascii=False,separators=(',',':')))
		if (req['action'] == 'steelyard_get'):
			result = steelyard_get(req)
		
		elif (req['action'] == 'Alarm'):
			result = Alarm(req)

		elif (req['action'] == 'ShopHeartBeat'):
			result = ShopHeartBeat(req)

		elif (req['action'] == 'AdSubAppHeartBeat'):
			result = AdSubAppHeartBeat(req,adCmd)

		elif (req['action'] == 'heartBeat'):
			result = heartBeat(req,cmd,version)

		elif (req['action'] == 'heart_beat'):
			result = heart_beat(req)

		elif (req['action'] == 'shopEntry_in'):
			result = shopEntry_in(req)

		elif (req['action'] == 'shopEntry_empty'):
			result = shopEntry_empty(req)

                elif (req['action'] == 'shopEntryHistory_insert'):
			result = shopEntryHistory_insert(req)

                elif (req['action'] == 'customManager_get'):
			result = customManager_get(req)

		elif (req['action'] == 'addskuStart'):
			result = addskuStart(req)

		elif (req['action'] == 'AddskuStart'):
			result = AddskuStart(req)

		elif (req['action'] == 'addskuEnd'):
			result = addskuEnd(req)

		elif (req['action'] == 'AddskuEnd'):
			result = AddskuEnd(req)

		elif (req['action'] == 'ShoppingChart'):
			result = ShoppingChart(req)

		elif (req['action'] == 'shoppingChart'):
			result = ShoppingChart(req)

		elif (req['action'] == 'shopping_chart'):
			result = ShoppingChart(req)

		elif (req['action'] == 'skuGet'):
			result = skuGet(req)

		elif (req['action'] == 'sku_get'):
			result = skuGet(req)

		elif (req['action'] == 'ShoppingCartEnd'):
			result = ShoppingCartEnd(req)

		elif (req['action'] == 'ShoppingCartGet'):
			result = ShoppingCartGet(req)

		elif (req['action'] == 'ShoppingCartAdd'):
			result = ShoppingCartAdd(req)

		elif (req['action'] == 'CheckWeight'):
			result = CheckWeight(req)

		elif (req['action'] == 'steelyard_update'):
			result = steelyard_update(req)

		elif (req['action'] == 'steelyard_update_status'):
			result = steelyard_update_status(req)

		elif (req['action'] == 'steelyard_update_isError'):
			result = steelyard_update_isError(req)

		elif (req['action'] == 'InsertTable'):
			result = InsertTable(req)
		else:
			result = {'result':'Failure', 'ErrMsg':'Unknown_action'}
			print '\033[1;31;40m' + "Error: Unknown action" + '\033[0m'
		#print result
		#return HttpResponse(json.dumps(result,ensure_ascii=False))
		return HttpResponse(json.dumps(result,ensure_ascii=False,separators=(',',':')))

	elif request.method == 'GET':
		return HttpResponse("[" + datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S') + "] " + "Hello World")
		#return render(request,'weixin/home.html')
	else:
		return HttpResponse("[" + datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S') + "]")

