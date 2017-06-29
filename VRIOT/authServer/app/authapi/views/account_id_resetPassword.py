from rest_framework.response import Response
from rest_framework.status import *
from ._authapi import AuthAPIView
from ..models.account import Account
from django.core.mail import EmailMessage
import json



class AccountIdResetPasswordView(AuthAPIView):

    authentication_classes = []

    def __init__(self):
        super().__init__()

    def get(self, request, id):
        try:
            account = Account.objects.get(username=id)
        except:
            return Response(json.dumps(),status=HTTP_)
        return Response("id:" + str(id), 
            status=HTTP_501_NOT_IMPLEMENTED)

    def patch(self, request, id):
        return Response("id:" + str(id), 
            status=HTTP_501_NOT_IMPLEMENTED)

    def delete(self, request, id):
        return Response("id:" + str(id), 
            status=HTTP_501_NOT_IMPLEMENTED)