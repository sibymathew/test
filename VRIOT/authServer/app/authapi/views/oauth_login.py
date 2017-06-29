from rest_framework.response import Response
from rest_framework.status import *
import base64
import uuid
import json
import time

from ._authapi import AuthAPIView
from ..authenticators.apiAuthenticator import  BasicAuthentication
from ..services.cache import Cache
from baseapp.settings import ACCESS_TOKEN_VALIDITY_SECONDS
from baseapp.settings import REFRESH_TOKEN_VALIDITY_SECONDS




class OauthLoginView(AuthAPIView):

    def __init__(self):
        super(OauthLoginView,self).__init__()

    def get(self, request):
        """
            This route returns a token by verifying the Base64 encoded 
            username:password in the Auth header.
            Token is passed as a part of JSON string.
        """
        try:
            # if the token was valid and has a user related. 
            # it should be set on request.user
            account = request.user
            if not account:
                raise Exception("Invalid User")

            # create a cache entry based on the user.
            # add the entry in cache based on random uuid.
            accessToken = str(uuid.uuid4().hex)
            # [Improvements TO DO ]cacheEntry should be created 
            # as a model kept in models folder.

            accessTokenCacheObj = {
                'account_obj':account,
                'expire_time':int(time.time())+ ACCESS_TOKEN_VALIDITY_SECONDS,
                'token_type': 'access'
            }
            Cache().add(accessToken,accessTokenCacheObj)

            #refresh token will be one time accesible.
            refreshToken = str(uuid.uuid4().hex)
            refreshTokenCacheObj = {
                'access_token': accessToken,
                'expire_time': int(time.time())+ REFRESH_TOKEN_VALIDITY_SECONDS,
                'token_type': 'refresh'
            }
            Cache().add(refreshToken,refreshTokenCacheObj)
        except Exception as e:
            return Response(e.args,status=HTTP_401_UNAUTHORIZED)
            
        #return token in application/json based response.
        return  Response(json.dumps({
            'access_token':accessToken,
            'refresh_token':refreshToken
            }),
            HTTP_200_OK)
        return Response("hello",status=HTTP_200_OK)