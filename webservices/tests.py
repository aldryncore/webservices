# -*- coding: utf-8 -*-
# must be first:
from django.conf import settings; settings.configure(ROOT_URLCONF='webservices.tests', DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}})
# real import
from django.test.testcases import TestCase as DjangoTestCase
from twisted.internet import reactor
from twisted.trial.unittest import TestCase as TwistedTestCase
from twisted.web.server import Site
from unittest import TestCase
from webservices.async import provider_for_twisted, TwistedConsumer
from webservices.exceptions import BadRequest, WebserviceError
from webservices.models import Provider, BaseConsumer
from webservices.sync import (provider_for_flask, FlaskTestingConsumer, 
    provider_for_django, DjangoTestingConsumer)


urlpatterns = []

class GreetingProvider(Provider):
    keys = {
        'pubkey': 'privatekey'
    }
    
    def get_private_key(self, key):
        return self.keys.get(key)
    
    def provide(self, data):
        name = data.get('name', 'World')
        return {'greeting': u'Hello %s!' % name}

class GetFlaskTestingConsumer(FlaskTestingConsumer):
    def send_request(self, url, data, headers): # pragma: no cover
        response = self.test_client.get(url, data=data, headers=headers)
        self.raise_for_status(response.status_code, response.data)
        return response.data


class BaseTests(TestCase):
    def test_consume_base_consumer(self):
        consumer = BaseConsumer('http://localhost', 'pubkey', 'privatekey')
        self.assertRaises(NotImplementedError, consumer.consume, '/', {'name': 'Test'})


class FlaskTests(TestCase):
    def setUp(self):
        from flask import Flask
        app = Flask(__name__)
        app.config['TESTING'] = True
        provider_for_flask(app, '/', GreetingProvider())
        self.client = app.test_client()
    
    def test_greeting_provider(self):
        consumer = FlaskTestingConsumer(self.client, 'http://localhost', 'pubkey', 'privatekey')
        output = consumer.consume('/', {'name': 'Test'})
        self.assertEqual(output['greeting'], 'Hello Test!')
    
    def test_greeting_provider_wrong_key(self):
        consumer = FlaskTestingConsumer(self.client, 'http://localhost', 'pubkey', 'wrongkey')
        self.assertRaises(BadRequest, consumer.consume, '/', {'name': 'Test'})
    
    def test_starts_with_slash(self):
        consumer = FlaskTestingConsumer(self.client, 'http://localhost', 'pubkey', 'wrongkey')
        self.assertRaises(ValueError, consumer.consume, 'wrong', {'name': 'Test'})
        
    def test_method_not_allowed(self):
        consumer = GetFlaskTestingConsumer(self.client, 'http://localhost', 'pubkey', 'wrongkey')
        self.assertRaises(WebserviceError, consumer.consume, '/', {'name': 'Test'})


class DjangoTests(DjangoTestCase):
    def setUp(self):
        from django.test.client import Client
        self.client = Client()
        
    @property
    def urls(self):
        from django.conf.urls import url, patterns
        return patterns('',
            url(r'^$', provider_for_django(GreetingProvider()))
        )
    
    def test_greeting_provider(self):
        consumer = DjangoTestingConsumer(self.client, 'http://localhost', 'pubkey', 'privatekey')
        output = consumer.consume('/', {'name': 'Test'})
        self.assertEqual(output['greeting'], 'Hello Test!')
    
    def test_greeting_provider_wrong_key(self):
        consumer = DjangoTestingConsumer(self.client, 'http://localhost', 'pubkey', 'wrongkey')
        self.assertRaises(BadRequest, consumer.consume, '/', {'name': 'Test'})


class TwistedTests(TwistedTestCase):

    def setUp(self):
        resource = provider_for_twisted(GreetingProvider())
        factory = Site(resource)
        self.port = reactor.listenTCP(0, factory, interface="127.0.0.1")
        self.client = None

    def tearDown(self):
        if self.client is not None:
            self.client.transport.loseConnection()
        return self.port.stopListening()

    def _test(self, public_key, private_key, path, data):
        base_url = 'http://127.0.0.1:%s/' % self.port.getHost().port
        consumer = TwistedConsumer(base_url, public_key, private_key)
        return consumer.consume(path, data)
    
    def test_greeting_provider(self):
        def cb(result):
            self.assertEqual(result['greeting'], 'Hello Test!')
        return self._test('pubkey', 'privatekey', '/', {'name': 'Test'}).addCallback(cb)
    
    def test_greeting_provider_wrong_key(self):
        def cb(result):
            self.assertRaises(BadRequest, result.raiseException)
        return self._test('pubkey', 'wrongkey', '/', {'name': 'Test'}).addErrback(cb)
