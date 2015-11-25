import requests

from webservices.models import BaseConsumer


class SyncConsumer(BaseConsumer):
    def __init__(self, base_url, public_key, private_key):
        super(SyncConsumer, self).__init__(base_url, public_key, private_key)
        self.session = requests.session()

    def send_request(self, url, data, headers):  # pragma: no cover
        response = self.session.post(url, data=data, headers=headers)
        self.raise_for_status(response.status_code, response.content)
        return response.content


class DjangoTestingConsumer(SyncConsumer):
    def __init__(self, test_client, base_url, public_key, private_key):
        self.test_client = test_client
        super(DjangoTestingConsumer, self).__init__(
            base_url, public_key, private_key)

    def build_url(self, path):
        return path

    def send_request(self, url, data, headers):
        headers = {
            'HTTP_%s' % header.upper().replace('-', '_'): value
            for header, value in headers.items()
        }
        response = self.test_client.post(
            url,
            data=data,
            content_type='application/json',
            **headers
        )
        self.raise_for_status(response.status_code, response.content)
        return response.content


class FlaskTestingConsumer(DjangoTestingConsumer):
    def send_request(self, url, data, headers):
        response = self.test_client.post(url, data=data, headers=headers)
        self.raise_for_status(response.status_code, response.data)
        return response.data


def provider_for_django(provider):
    from django.http import HttpResponse
    from django.views.decorators.csrf import csrf_exempt

    def provider_view(request):
        def get_header(key, default):
            django_key = 'HTTP_%s' % key.upper().replace('-', '_')
            return request.META.get(django_key, default)
        method = request.method
        if getattr(request, 'body', None):
            signed_data = request.body
        else:
            signed_data = request.raw_post_data
        status_code, data = provider.get_response(
            method,
            signed_data,
            get_header,
        )
        return HttpResponse(data, status=status_code)
    return csrf_exempt(provider_view)


def provider_for_flask(app, url, provider):
    from flask import request

    def provider_view():
        def get_header(key, default):
            return request.headers.get(key, default)
        method = request.method
        signed_data = request.data
        status_code, data = provider.get_response(
            method,
            signed_data,
            get_header,
        )
        return data, status_code
    return app.route(url, methods=['POST'])(provider_view)
