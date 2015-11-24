from webservices.models import Provider

from api.models import Key


class HelloProvider(Provider):
    def get_private_key(self, public_key):
        try:
            return Key.objects.get(public_key=public_key).private_key
        except Key.DoesNotExist:
            return None

    def provide(self, data):
        name = data.get('name', 'world')
        return {'greeting': u'hello %s' % name}
