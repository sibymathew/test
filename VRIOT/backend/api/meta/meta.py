from django.conf import settings
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK

from common.api import VRIoTAPIView


class MetaView(VRIoTAPIView):
    @staticmethod
    def get(request):
        import platform
        import time

        e = {
            'platform': platform.python_version(),
            'timestamp': int(time.time())
        }

        # add visionline server settings to the response if present.
        try:
            e['visionline'] = settings.AA_VISIONLINE_CONF
        except:
            e['visionline'] = 'No Visionline'

        return Response(e, status=HTTP_200_OK)
