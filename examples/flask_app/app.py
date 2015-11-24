from flask import Flask
from webservices.models import Provider
from webservices.sync import provider_for_flask
import os

app = Flask(__name__)


with open(os.path.join(os.path.dirname(__file__), 'keys.txt')) as fobj:
    data = fobj.read()
    app.keys = dict([
        line.split(':')
        for line in data.split('\n')
        if line.strip()
    ])


class HelloProvider(Provider):
    def get_private_key(self, public_key):
        private_key = app.keys.get(public_key)
        return private_key

    def provide(self, data):
        name = data.get('name', 'world')
        return {'greeting': u'hello %s' % name}


provider_for_flask(app, '/', HelloProvider())

if __name__ == '__main__':
    app.run(port=8000, debug=True)
