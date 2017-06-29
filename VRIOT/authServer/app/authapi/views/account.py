from rest_framework.response import Response
from rest_framework.status import *
from ._authapi import AuthAPIView
from ..models.account import Account,AccountList
import json

# from common.api import VRIoTAPIView
# from settings.environments.development import *

class AccountView(AuthAPIView):

    def __init__(self):
        super(AccountView, self).__init__()

    def get(self, request):

        directory = request.query_params.get('directory')
        group = request.query_params.get('group')

        allAccounts = AccountList()
        for account in  Account.objects:
            allAccounts.append(account)
        return Response(allAccounts.to_json(),
            status=HTTP_200_OK)

    def post(self, request):
        """
        """
        try:    
            account=Account.parseForCreate(request.data)
            account.save()
            return Response(account.to_json(),HTTP_200_OK)
        except Exception as e:
            return Response(e.args[0],HTTP_400_BAD_REQUEST)
 