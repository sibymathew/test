from rest_framework.response import Response
from rest_framework.status import *
from ._authapi import AuthAPIView
from ..authenticators.apiAuthenticator import  BasicAuthentication

class OauthAuthenticateView(AuthAPIView):


    def __init__():
        super().__init__()

    def get(self, request):

        if not request.user:
            return Response("",status=HTTP_401_UNAUTHORIZED)
        return Response(request.user.to_json(),status=HTTP_200_OK)