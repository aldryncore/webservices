###########
Webservices
###########

Build and consume web services (aka APIs) in Python. 

********
Features
********

* Providers that work with Django, Flask and Twisted
* Everything is signed (using itsdangerous)
* Synchronous consumer (framework independant)
* Asynchronous consumer (powered by Twisted)


************
Installation
************

Django (provider/consumer)
==========================

``pip install webservices[django]``


Flask (provider/consumer)
=========================

``pip install webservices[flask]``

Twisted (provider/consumer)
===========================

``pip install webservices[twisted]``

Synchronous consumer only
=========================

``pip install webservices[consumer]``


**********
Quickstart
**********

We'll write an API that greets you with your name (or 'hello world' if not name
is provided).

Provider
========

Django
------

We assume you have a setting ``API_KEYS`` which is a dictionary of public keys
mapping to private keys. 

``myapi/urls.py``::

    from django.conf.urls import url, patterns
    from webservices.sync import provider_for_django
    from myapi.views import HelloProvider

    urlpatterns = patterns('',
        url(r'hello/$', provider_for_django(HelloProvider())),
    )

Your ``myapi/views.py``::

    from django.conf import settings
    from webservices.models import Provider
    
    class HelloProvider(Provider):
        def get_private_key(self, public_key):
            return settings.API_KEYS.get(public_key)
        
        def provide(self, data):
            name = data.get('name', 'world')
            return {'greeting': u'hello %s' % name} 


Flask
-----


``app.py``::

    from flask import Flask
    from webservices.sync import provider_for_flask
    from webservices.models import Provider
    
    app = Flask(__name__)
    
    API_KEYS = {
        'publickey': 'privatekey', # your keys here
    }
    
    class HelloProvider(Provider):
        def get_private_key(self, public_key):
            return API_KEYS.get(public_key)
        
        def provide(self, data):
            name = data.get('name', 'world')
            return {'greeting': u'hello %s' % name}
    
    provider_for_flask(app, '/hello/', HelloProvider())


Twisted
-------

``app.py``::

    from twisted.internet import reactor
    from twisted.web.server import Site
    from webservices.async import provider_for_twisted
    from webservices.models import Provider
        
    API_KEYS = {
        'publickey': 'privatekey', # your keys here
    }
    
    class HelloProvider(Provider):
        def get_private_key(self, public_key):
            return API_KEYS.get(public_key)
        
        def provide(self, data):
            name = data.get('name', 'world')
            return {'greeting': u'hello %s' % name}
    
    resource = provider_for_twisted(HelloProvider())
    
    site = Site(resource)
    reactor.listenTCP(80, site)
    reactor.run()


Noticed how the provider is basically the same for all three (other than
``get_private_key``)? Neat, right?


Handling errors
---------------

To log errors (for example using raven) you can implement the ``report_exception`` method on ``Provider`` classes.
This method is called whenever the ``provide`` method throws an exception. It takes no arguments.


Consumer
========

Synchronous
-----------

To consume that code (assuming it's hosted on 'https://api.example.org')::

    from webservices.sync import SyncConsumer
    
    consumer = SyncConsumer('https://api.example.org', 'mypublickey', 'myprivatekey')
    result = consumer.consume('/hello/', {'name': 'webservices')
    print result # prints 'hello webservices'


Asynchronous
------------

Same as above, but async::

    from webservices.async import TwistedConsumer
    from twisted.internet import reactor
    
    def callback(result):
        print result # prints 'hello webserivces'
        reactor.stop()
    
    consumer = TwistedConsumer('https://api.example.org', 'mypublickey', 'myprivatekey')
    deferred = consumer.consume('/hello/', {'name': 'webservices')
    deferred.addCallback(callback)
    
    reactor.run()


Data Source Name
----------------

You can create consumers from Data Source Names (eg ``'http://public_key:private_key@api.example.org'``) using the
``from_dsn`` classmethod on consumers.

Example:

    consumer = SyncConsumer.from_dsn('https://public_key:private_key@api.example.org')

    
*******
License
*******

This code is licensed under the 3-clause BSD license, see LICENSE.txt.
