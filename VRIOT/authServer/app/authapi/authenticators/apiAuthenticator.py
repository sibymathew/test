"""
Provides various authentication policies.
"""


import base64
import binascii
# import uuid
import time

# from django.contrib.auth import authenticate, get_user_model
# from django.middleware.csrf import CsrfViewMiddleware
from django.utils.six import text_type
from django.utils.translation import ugettext_lazy as _

from rest_framework import HTTP_HEADER_ENCODING, exceptions


from ..services.cache import Cache
from ..models.account import Account

def authenticate(**kwargs):
    """
        helper function that authenticates the user based on username
        and password.
    """
    try:
        accObj= Account.objects.get(username=kwargs['username'])
        # check if the password matches.

        if not accObj.password == kwargs['password']:
            raise Exception ('Password Mismatch.')
        return accObj
    except:
        return None

def get_authorization_header(request):
    """
    Return request's 'Authorization:' header, as a bytestring.
    """
    return request.META.get('HTTP_AUTHORIZATION', b'')
    return auth

"""
class CSRFCheck(CsrfViewMiddleware):
    def _reject(self, request, reason):
        # Return the failure reason instead of an HttpResponse
        return reason
"""

class BaseAuthentication(object):
    """
    All authentication classes should extend BaseAuthentication.
    """

    def authenticate(self, request):
        """
        Authenticate the request and return a two-tuple of (user, token).
        """
        raise NotImplementedError(".authenticate() must be overridden.")

    def authenticate_header(self, request):
        """
        Return a string to be used as the value of the `WWW-Authenticate`
        header in a `401 Unauthenticated` response, or `None` if the
        authentication scheme should return `403 Permission Denied` responses.
        """
        pass


class BasicAuthentication(BaseAuthentication):
    """
    HTTP Basic authentication against username/password.
    """
    www_authenticate_realm = 'api'

    def authenticate(self, request):
        """
        Returns a `User` if a correct username and password have been supplied
        using HTTP Basic authentication.  Otherwise returns `None`.
        """
        auth = get_authorization_header(request).split()

        if not auth or auth[0].lower() != 'basic':
            return None

        if len(auth) == 1:
            msg = _('Invalid basic header. No credentials provided.')
            raise exceptions.AuthenticationFailed(msg)
        elif len(auth) > 2:
            msg = _('Invalid basic header. Credentials string should not contain spaces.')
            raise exceptions.AuthenticationFailed(msg)

        try:
            auth_parts = base64.b64decode(auth[1]).decode(HTTP_HEADER_ENCODING).partition(':')

        except (TypeError, UnicodeDecodeError, binascii.Error):
            msg = _('Invalid basic header. Credentials not correctly base64 encoded.')
            raise exceptions.AuthenticationFailed(msg)

        userid, password = auth_parts[0], auth_parts[2]
        return self.authenticate_credentials(userid, password)

    def authenticate_credentials(self, userid, password):
        """
        Authenticate the userid and password against username and password.
        """
        credentials = {
            'username' : userid,
            'password': password
        }

        account = authenticate(**credentials)

        if account is None:
            raise exceptions.AuthenticationFailed(_('Invalid username/password.'))

        if not account.is_enabled:
            raise exceptions.AuthenticationFailed(_('User inactive or deleted.'))

        return (account, None)

    def authenticate_header(self, request):
        return 'Basic realm="%s"' % self.www_authenticate_realm

class SessionAuthentication(BaseAuthentication):
    """
    Use Django's session framework for authentication.
    """

    def authenticate(self, request):
        """
        Returns a `User` if the request session currently has a logged in user.
        Otherwise returns `None`.
        """

        # Get the session-based user from the underlying HttpRequest object
        user = getattr(request._request, 'user', None)

        # Unauthenticated, CSRF validation not required
        if not user or not user.is_active:
            return None

        self.enforce_csrf(request)

        # CSRF passed with authenticated user
        return (user, None)

    def enforce_csrf(self, request):
        """
        Enforce CSRF validation for session based authentication.
        """
        reason = CSRFCheck().process_view(request, None, (), {})
        if reason:
            # CSRF failed, bail with explicit error message
            raise exceptions.PermissionDenied('CSRF Failed: %s' % reason)


class TokenAuthentication(BaseAuthentication):

    """
    Simple token based authentication.

    Clients should authenticate by passing the token key in the "Authorization"
    HTTP header, prepended with the string "Token ".  For example:
        Authorization: Token 401f7ac837da42b97f613d789819ff93537bee6a
    """

    keyword = 'token'

    def authenticate(self, request):

        auth = get_authorization_header(request).split()

        if not auth or auth[0].lower() != self.keyword:
            return None

        if len(auth) == 1:
            msg = _('Invalid token header. No credentials provided.')
            raise exceptions.AuthenticationFailed(msg)
        elif len(auth) > 2:
            msg = _('Invalid token header. Token string should not contain spaces.')
            raise exceptions.AuthenticationFailed(msg)

        try :
            token = auth[1]
        except UnicodeError :
            msg = _('Invalid token header. Token string should not contain invalid characters.')
            raise exceptions.AuthenticationFailed(msg)
        except Exception as e:
            msg = _('Unable to decode Token')
            raise exceptions.AuthenticationFailed(msg)

        return self.authenticate_credentials(token)

    def authenticate_credentials(self, key):
        # model = self.get_model()
        # try:
        #     token = model.objects.select_related('user').get(key=key)
        # except model.DoesNotExist:
        #     raise exceptions.AuthenticationFailed(_('Invalid token.'))

        tokenValue = Cache().get(key) # cache consists of token to account object mapping.
        # [Improvements TO DO ]tokenValue should be created as a model kept in models folder.

        if not tokenValue:
            raise exceptions.AuthenticationFailed(_("Invalid Token."))
        tokenType = tokenValue.get('token_type')
        if not tokenType == 'access':
            raise exceptions.AuthenticationFailed(_(
                'A refresh token is provided. Please provide Access Token.'))
        if tokenValue['expire_time']<int(time.time()):
            #if access token is expired raise an error.
            raise exceptions.AuthenticationFailed(_(
                'Access Token Expired. Please refresh Access token.'))

        return (tokenValue['account_obj'],key)

    def authenticate_header(self, request):
        return self.keyword

class RefreshTokenAuthentication(TokenAuthentication):
    """
        Specific authentication for refresh tokens.
    """

    def authenticate_credentials(self, key):

        tokenValue = Cache().get(key) # cache consists of token to account object mapping.
        # [Improvements TO DO ]cacheEntry should be created as a model kept in models folder.

        if not tokenValue:
            raise exceptions.AuthenticationFailed(_("Invalid Token."))
        tokenType = tokenValue.get('token_type')

        if not tokenType == 'refresh':
            raise exceptions.AuthenticationFailed(_(
                'Please provide a refresh token to access this route.'))
        if tokenValue['expire_time']<int(time.time()):
            raise exceptions.AuthenticationFailed(_(
                'Refresh Token Expired. Login again.'))

        accountObj = Cache().get(tokenValue['access_token'])['account_obj']

        #clean up the access token entries.
        # Cache().remove(tokenValue['access_token'])

        return (accountObj, key)
