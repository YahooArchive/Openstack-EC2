import webob
import webob.dec
import webob.exc

from mock import config
from mock import wsgi
from mock import log as logging

LOG = logging.getLogger('mock.api.service')

class Mock(wsgi.Application):

    def __init__(self, config):
        wsgi.Application.__init__(self, config)

    @webob.dec.wsgify(RequestClass=webob.Request)
    def __call__(self, req):
        out_resp = webob.Response()
        out_resp.status = httplib.INTERNAL_SERVER_ERROR
        out_resp.body = "WIP"
        out_resp.content_type = "text/plain"
