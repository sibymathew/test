from rest_framework.renderers import JSONRenderer
from rest_framework.views import APIView


class VRIoTAPIView(APIView):
    renderer_classes = (JSONRenderer,)

    def __init__(self):
        super(VRIoTAPIView, self).__init__()

    @staticmethod
    def authenticate_request(request):
        # auth_header = self.get_authenticate_header(request=request)
        raise NotImplemented
