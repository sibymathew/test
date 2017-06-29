from rest_framework.response import Response
from rest_framework.status import *

import uuid,json,time
from ._authapi import AuthAPIView
from ..authenticators.apiAuthenticator import RefreshTokenAuthentication
from baseapp.settings import ACCESS_TOKEN_VALIDITY_SECONDS
from ..services.cache import Cache

class OauthRefreshView(AuthAPIView):

    authentication_classes = (RefreshTokenAuthentication,)

    def __init__(self):
        super().__init__()
    def get(self, request):
        account =request.user

        #create a new access token
        accessToken = str(uuid.uuid4().hex)
        # [Improvements TO DO ]cacheEntry should be created 
        # as a model kept in models folder.

        accessTokenCacheObj = {
            'account_obj':account,
            'expire_time':int(time.time())+ ACCESS_TOKEN_VALIDITY_SECONDS,
            'token_type': 'access'

        }
        Cache().add(accessToken,accessTokenCacheObj)
        return Response(json.dumps({
            'access_token':accessToken
            }), status=HTTP_200_OK)