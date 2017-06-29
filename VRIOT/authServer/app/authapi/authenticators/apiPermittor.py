"""
Provides a set of pluggable permission policies.
"""
from __future__ import unicode_literals

from django.http import Http404

from rest_framework.compat import is_authenticated


SAFE_METHODS = ('GET', 'HEAD', 'OPTIONS')


class BasePermission(object):
    """
    A base class from which all permission classes should inherit.
    """

    def has_permission(self, request, view):
        """
        Return `True` if permission is granted, `False` otherwise.
        """
        return True

    def has_object_permission(self, request, view, obj):
        """
        Return `True` if permission is granted, `False` otherwise.
        """
        return True

class AllowAny(BasePermission):
    """
    Allow any access.
    This isn't strictly required, since you could use an empty
    permission_classes list, but it's useful because it makes the intention
    more explicit.
    """

    def has_permission(self, request, view):
        return True

class IsAuthenticated(BasePermission):
    """
    Allows access only to authenticated users.
    """

    def has_permission(self, request, view):
        print (request.user)
        if request.user:
            return True 
        return False # ALert here!!!