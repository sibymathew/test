from rest_framework.response import Response
from rest_framework.status import *
from ._authapi import AuthAPIView
from ..models.account import Account


class AccountIdView(AuthAPIView):

    def __init__(self):
        super().__init__()

    def get(self, request, id):
        try:
            account = Account.objects.get(username=id)
            return Response(account.to_json(), 
                status=HTTP_200_OK)
        except Account.DoesNotExist:
            return Response('',HTTP_400_BAD_REQUEST)


    def patch(self, request, id):
        try:
            account = Account.objects.get(username=id)
            updatedAccount =  account.updateAccount(request.data)
            updatedAccount.save()
            return Response("id:" + str(id), 
                status=HTTP_200_OK)
        except Account.DoesNotExist as e:

            print (e.args)
            return Response('',HTTP_400_BAD_REQUEST)

    def delete(self, request, id):
        try:
            account = Account.objects.get(username=id)
            account.delete()
            return Response("", status=HTTP_200_OK)
        except Account.DoesNotExist:
            return Response('',HTTP_400_BAD_REQUEST)

