import base64
import email
import hashlib
import hmac
import http.client
import json
import ssl
from json.decoder import JSONDecodeError
from time import strptime, mktime, timezone, time, daylight

from django.conf import settings
from django.core.cache import cache


class AASDK(object):
    def __init__(self):
        self._conf = settings.AA_VISIONLINE_CONF
        self._use_ssl = self._conf.get("secure", True)
        self._host = self._conf.get("host", True)
        self._basepath = self._conf.get("path", True)
        # Store credentials in an object ready to be sent to the server.
        self._credentials = {'username': self._conf.get("user", True),
                             'password': self._conf.get("password", True)}
        self._debug_level = 0  # Get text output from HTTPConnection
        self._session = {}  # Placeholder for session ID and access key
        self._time_skew = 0  # Assume that server and client times match

    def send_request(self, method, url, body=None):
        """Send a request to the web service.
        Automatically handle session creation and time skew.
        """
        # Send the request at most 3 times: The first request may need
        # a new time skew, the second request may hit an expired session,
        # the third request is successful or has a permanent error.
        status = None
        resource = None
        for _ in range(3):
            try:
                # If we are already logged in, send the request. Otherwise,
                # create the session and then send the request in the next
                # loop iteration.
                if 'accessKey' in self._session:
                    (status, resource, server_time) = \
                        self._send_single_request(method, url, body)
                    request_was_sent = True
                else:
                    (status, resource, server_time) = \
                        self._create_session()
                    request_was_sent = False
                # Handle time skew (40101) and expired session (40103).
                # If the request was sent and everything went fine, or if any
                # other type of error occurred, we leave that to the caller.
                if status == 401 and resource['code'] == 40101:
                    _ = strptime(server_time, '%a, %d %b %Y %H:%M:%S GMT')
                    self._time_skew = mktime(
                        _) - timezone - time() + daylight * 3600
                elif status == 401 and resource['code'] == 40103:
                    if 'accessKey' in self._session:
                        cache.delete(settings.AA_CACHE_KEY)
                        del self._session['accessKey']
                elif status == 401 and resource['code'] == 40104:
                    cache.delete(settings.AA_CACHE_KEY)
                    del self._session['accessKey']
                elif request_was_sent:
                    return status, resource
            except (IOError, ValueError) as e:
                # Handle connection refused, nameserver lookup failure,
                # sslv3 alert handshake failure or server response that was
                # not in JSON format.
                # Set a temporary error code and try again.
                (status, resource) = (500, {'message': str(e, 'iso-8859-1')})
                if self._debug_level:
                    print('error: %s' % resource['message'])
                if e.args[0] == 10061:
                    break
        # If the server still returns an error after 3 attempts, nothing
        # else can be done except for returning the error to the caller.
        return status, resource

    def _create_session(self):
        """Send user credentials and record the ID and the access key."""
        session = cache.get(settings.AA_CACHE_KEY)
        if session:
            (status, resource, server_time) = session
            self._session = resource
        else:
            (status, resource, server_time) = \
                self._send_single_request('POST', '/sessions',
                                          self._credentials, False)
            if status == 201:
                self._session = resource  # Success! Store ID and key.
                cache.set(settings.AA_CACHE_KEY,
                          (status, resource, server_time), 900)
        return status, resource, server_time

    def _send_single_request(self, method, url, body, sign=True):
        """Send a properly signed request to the web service."""
        url = self._basepath + url
        headers = {}
        if body:
            # Encode request body as JSON
            body = json.dumps(body)
            headers['Content-Type'] = 'application/json;charset=utf-8'
            # Compute MD5 digest
            h = hashlib.new('md5')
            h.update(body.encode('utf-8'))
            headers['Content-MD5'] = base64.b64encode(h.digest()).decode()
        # Format the date correctly, after applying the client/server skew
        headers['Date'] = email.utils.formatdate(time() + self._time_skew)
        if sign and 'id' in self._session:
            # Canonicalize the URL
            (canonicalized_resource, q, query_string) = url.partition('?')
            canonicalized_resource += q + '&'.join(
                sorted(query_string.split('&')))
            # Build the string to be signed
            string_to_sign = method + "\n"
            if 'Content-MD5' in headers:
                string_to_sign += headers['Content-MD5']
            string_to_sign += "\n"
            if 'Content-Type' in headers:
                string_to_sign += headers['Content-Type']
            string_to_sign += "\n" + headers[
                'Date'] + "\n" + canonicalized_resource
            # Create the signature
            h = hmac.new(self._session['accessKey'].encode('utf-8'),
                         string_to_sign.encode('utf-8'), hashlib.sha1)
            headers['Authorization'] = 'AWS %s:%s' \
                                       % (self._session['id'],
                                          base64.b64encode(h.digest()).decode())
        # Communicate with server
        if self._use_ssl:
            conn = http.client.HTTPSConnection(
                self._host, timeout=240,
                context=ssl._create_unverified_context())
        else:
            conn = http.client.HTTPConnection(self._host, timeout=240)
        conn.set_debuglevel(self._debug_level)
        conn.request(method, url, body, headers)
        response_obj = conn.getresponse()
        # Interpret response
        server_time = response_obj.getheader('Date')
        response_body = response_obj.read()
        if self._debug_level:
            print("reply body: " + response_body)
        try:
            resource = json.loads(response_body.decode())
        except JSONDecodeError:
            resource = {
                'message': "JSON Decode failed. \nServer response:\n" +
                           response_body}
        except ValueError as e:
            resource = {
                'message': e.message + "\nServer response:\n" + response_body}
        return response_obj.status, resource, server_time
