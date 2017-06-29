from rest_framework.response import Response
from rest_framework.status import *
from ._authapi import AuthAPIView

class AccountIdApiKeyView(AuthAPIView):

    def __init__(self):
        super().__init__()

    def post(self, request, id):
        return Response("id:" + str(id), 
            status=HTTP_501_NOT_IMPLEMENTED)

    def patch(self, request, id):
        return Response("id:" + str(id), 
            status=HTTP_501_NOT_IMPLEMENTED)

    def delete(self, request, id):
        return Response("id:" + str(id), 
            status=HTTP_501_NOT_IMPLEMENTED)