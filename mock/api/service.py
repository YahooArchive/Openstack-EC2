import webob
import webob.dec
import webob.exc

from mock import ec2
from mock import log as logging
from mock import wsgi

LOG = logging.getLogger('mock.api.service')

class Mock(wsgi.Application):

    def __init__(self, config):
        wsgi.Application.__init__(self, config)
        self.ec2_mock = ec2.Ec2Mock(config)

    @webob.dec.wsgify(RequestClass=webob.Request)
    def __call__(self, req):
        raise webob.exc.HTTPBadRequest(comment="Not implemented yet")
