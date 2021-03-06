"""
Contains HipChat client.
"""

import json, urllib, urllib2, base64, os
from urllib2 import HTTPError

TOO_MANY_REQUESTS = 429


class Hip(object):
    """
    HipChat REST API wrapper.
    """

    def __init__(
        self, api_key='', api_root=None):

        self.api_root = "https://hipchat.com/v2/"
        self.api_root = api_root and api_root or self.api_root
        self.auth_keys = api_key

    def post_notification_to_room(self, room_id_or_name, message, color='green', notify=False, message_format='text'):
        "Send a notification to a HipChat room."

        data = {
            'message': message,
            'color': color,
            'notify': notify,
            'message_format': message_format
        }
        self._make_call(
            'room', room_id_or_name,
            'notification',
            method='POST',
            data=data)

    def _make_call(self, *args, **kwargs):
        request_args = {}

        if kwargs.get('data'):
            request_args['data'] = json.dumps(kwargs['data'])
        
        request_args['url'] = self.api_root + '/'.join(args)
        
        req = urllib2.Request(**request_args) 
        if kwargs.get('method'):
            req.get_method = lambda: kwargs['method']
        else:
            req.get_method = lambda: 'GET'
        req.add_header('Content-Type', 'application/json')
        req.add_header('Authorization', 'Bearer ' + self.auth_keys[0])

        try:
            f = urllib2.urlopen(req)
            response = f.read()
            f.close()
            return response
        except HTTPError, e:
            # cycle to next API key
            self.auth_keys = self.auth_keys[1:] + self.auth_keys[:1]
            print "Cycled to next API key"

            if not self.auth_keys or e.code != TOO_MANY_REQUESTS:
                self._error_handler(e)
            
            self._make_call(*args, **kwargs)

    def _error_handler(self, e):
        """
        Handles HipChat response codes.
        """
        raise HipChatError({
            'error_code': str(e.code),
            'response'  : json.loads(e.read())
        })

class HipChatError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

