"""baseapp URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""

from django.conf.urls import url ,include
from ..views.account import AccountView
from ..views.account_id import AccountIdView
from ..views.oauth_authenticate import OauthAuthenticateView
from ..views.oauth_login import OauthLoginView
from ..views.oauth_refresh import OauthRefreshView
from ..views.account_id_resetPassword import AccountIdResetPasswordView
from ..views.account_id_apiKey import AccountIdApiKeyView


urlpatterns = [
    url(r'^account/{0,1}$', AccountView.as_view()),
    url(r'^account/(?P<id>.+)/$', AccountIdView.as_view()),
    #need to update the url matcher regex to accept only appropriate chars.
    url(r'^account/(?P<id>.+)$', AccountIdView.as_view()),
    url(r'^account/(?P<id>.+)/api-key$', AccountIdApiKeyView.as_view()),
    url(r'^account/(?P<id>.+)/reset-password$',AccountIdResetPasswordView.as_view()),
    url(r'^oauth/login$', OauthLoginView.as_view()),
    url(r'^oauth/authenticate$', OauthAuthenticateView.as_view()),
    url(r'^oauth/refresh$', OauthRefreshView.as_view()),
]