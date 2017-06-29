from django.conf.urls import url

from api.device.device import DeviceAPI, DeviceScanAPI
from api.gateway.gateway import GatewayAPI
from api.meta.meta import MetaView

urlpatterns = [
    url(r'^ping/$', MetaView.as_view()),
    url(r'^device/$', DeviceAPI.as_view()),
    url(r'^device/(?P<resource_id>[a-f0-9]{24}?)$', DeviceAPI.as_view()),
    url(r'^device/window$', DeviceScanAPI.as_view()), 
    ## IOTC-182, Url above be changed to only post part of DeviceScanAPI.
    ## And, create a new url something like scanlist or unauthlist, 
    ## for the existing DeviceScanAPI.
    url(r'^gateway/$', GatewayAPI.as_view()),
    url(r'^gateway/(?P<resource_id>[a-f0-9]{24}?)$', GatewayAPI.as_view()),
]
