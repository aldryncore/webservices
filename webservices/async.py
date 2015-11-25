from twisted.internet import threads
from twisted.web import server
from twisted.web.client import getPage
from twisted.web.resource import Resource

from webservices.exceptions import BadRequest, WebserviceError
from webservices.models import BaseConsumer


class TwistedConsumer(BaseConsumer):
    def send_request(self, url, data, headers):
        return getPage(url, method='POST', postdata=data, headers=headers)

    def handle_response(self, response, max_age):
        def callback(body):
            return self.signer.loads(body, max_age=max_age)

        def errback(fail):
            message = fail.value.message
            status_code = fail.value.status
            self.raise_for_status(int(status_code), message)
        response.addCallback(callback)
        response.addErrback(errback)
        return response

    def raise_for_status(self, status_code, message):
        if status_code == 400:
            raise BadRequest(message)
        elif status_code >= 300:
            raise WebserviceError(message)


class ProviderResource(Resource):
    isLeaf = True

    def __init__(self, provider):
        self.provider = provider
        Resource.__init__(self)

    def render_POST(self, request):
        def get_header(key, default):
            return request.getHeader(key) or default

        def callback(info):
            status_code, data = info
            request.setResponseCode(status_code)
            request.write(data)
            request.finish()

        # XXX: This is not the correct way to pass the data to the processing
        #      function. The content is read from disk and could be too large
        #      to fit into memory. The correct way to go is to pass an open
        #      file handler as argument instead of a single string, but this
        #      would require each provider to be adapted.
        request.content.seek(0)
        signed_data = request.content.read()

        deferred = threads.deferToThread(
            self.provider.get_response,
            'POST',
            signed_data,
            get_header,
        )
        deferred.addCallback(callback)
        return server.NOT_DONE_YET


def provider_for_twisted(provider):
    return ProviderResource(provider)
