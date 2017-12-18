from django.conf.urls import url,include
from django.contrib import admin
from superMarket import views as superMarket_views
from weixin import views as weixin_views
from django.views.generic import TemplateView


urlpatterns = [
	url(r'^$', superMarket_views.index),
	#url(r'^admin/', admin.site.urls),
	url(r'^register/', weixin_views.register),
	url(r'^entry/', weixin_views.entry),
	url(r'^info/', weixin_views.info),
	url(r'^order/',weixin_views.order),
	url(r'^item/',weixin_views.item),
	url(r'^resend/',weixin_views.resend),
	url(r'^goodsplus/',weixin_views.goodsplus),
	url(r'^callpay/',weixin_views.callpay),
	url(r'^notify/',weixin_views.notify),
	url(r'^getConfig/',weixin_views.getConfig),
	url(r'^callOpen/$',weixin_views.callOpen),
	url(r'^toPay/$',weixin_views.toPay),
	url(r'^toOpen/$',weixin_views.toOpen),
	url(r'^test/',weixin_views.test),
	url(r'^MP_verify_qh3ZfWI2M06zTjuR\.txt$', weixin_views.wx_verify),

]

