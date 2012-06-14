# -*- coding: utf-8 -*-
from twisted.internet import reactor
from twisted.web.server import Site
from webservices.async import provider_for_twisted
from webservices.models import Provider
    
API_KEYS = {
    'pubkey': 'privkey', # your keys here
}

class HelloProvider(Provider):
    def get_private_key(self, public_key):
        return API_KEYS.get(public_key)
    
    def provide(self, data):
        name = data.get('name', 'world')
        return {'greeting': u'hello %s' % name}

resource = provider_for_twisted(HelloProvider())

site = Site(resource)
reactor.listenTCP(8000, site)
reactor.run()
