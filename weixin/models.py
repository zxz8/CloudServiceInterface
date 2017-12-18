from django.db import models

# Create your models here.

class Custom(models.Model):
	customId = models.CharField(max_length=64,primary_key=True)
	openid = models.CharField(max_length=64, null=True)
	username = models.CharField(max_length=64, null=True)
	password = models.CharField(max_length=64, null=True)
	tel = models.CharField(max_length=32, null=True)
	remark = models.TextField(null=True)
	types = models.CharField(max_length=16, default='0')
	isused = models.CharField(max_length=16, default='0')
	status = models.CharField(max_length=16, default='0')
	class Meta:
		db_table = "customManager"

class Verify(models.Model):
	tel = models.CharField(max_length = 20, null=True)
	code = models.CharField(max_length = 4, null=True)
	time_code = models.CharField(max_length = 64, null=True)
	flag = models.CharField(max_length = 1,default = '0', null=True)


class CustomOrder(models.Model):
	customOrderId = models.CharField(max_length = 64,primary_key=True)
	orderId = models.CharField(max_length=64, null=True)
	customId = models.CharField(max_length=64, null=True)
	amount = models.CharField(max_length=64, null=True)
	payment = models.CharField(max_length=64, null=True)
	description = models.CharField(max_length=64, null=True)
	createTime = models.CharField(max_length=64, null=True)
	shopId = models.CharField(max_length=64, null=True)
	result = models.CharField(max_length=64, null=True)
	class Meta:
		db_table = "customOrder"
	def __str__():
		return customOrderId

class OrderItem(models.Model):
	customOrderId = models.CharField(max_length=64, null=True)
	skuCode = models.CharField(max_length=64, null=True)
	customId = models.CharField(max_length=64, null=True)
	skuCount =  models.CharField(max_length=20, null=True)
	class Meta:
		db_table = "orderItem"
