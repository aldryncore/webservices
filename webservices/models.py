# -*- coding: utf-8 -*-
try:
    # python 3
    # noinspection PyCompatibility
    from urllib.parse import urlparse, urlunparse, urljoin
except ImportError:
    # python 2
    # noinspection PyCompatibility
    from urlparse import urlparse, urlunparse, urljoin

from itsdangerous import TimedSerializer, SignatureExpired, BadSignature

from webservices.exceptions import BadRequest, WebserviceError


PUBLIC_KEY_HEADER = 'x-services-public-key'


def _split_dsn(dsn):
    parse_result = urlparse(dsn)
    host = parse_result.hostname
    if parse_result.port:
        host += ':%s' % parse_result.port
    base_url = urlunparse((
        parse_result.scheme,
        host,
        parse_result.path,
        parse_result.params,
        parse_result.query,
        parse_result.fragment,
    ))
    return base_url, parse_result.username, parse_result.password


class BaseConsumer(object):
    def __init__(self, base_url, public_key, private_key):
        self.base_url = base_url
        self.public_key = public_key
        self.signer = TimedSerializer(private_key)

    @classmethod
    def from_dsn(cls, dsn):
        base_url, public_key, private_key = _split_dsn(dsn)
        return cls(base_url, public_key, private_key)

    def consume(self, path, data, max_age=None):
        if not path.startswith('/'):
            raise ValueError("Paths must start with a slash")
        signed_data = self.signer.dumps(data)
        headers = {
            PUBLIC_KEY_HEADER: self.public_key,
            'Content-Type': 'application/json',
        }
        url = self.build_url(path)
        body = self.send_request(url, data=signed_data, headers=headers)
        return self.handle_response(body, max_age)

    def handle_response(self, body, max_age):
        return self.signer.loads(body, max_age=max_age)

    def send_request(self, url, data, headers):
        raise NotImplementedError(
            'Implement send_request on BaseConsumer subclasses')

    def raise_for_status(self, status_code, message):
        if status_code == 400:
            raise BadRequest(message)
        elif status_code >= 300:
            raise WebserviceError(message)

    def build_url(self, path):
        path = path.lstrip('/')
        return urljoin(self.base_url, path)


class Provider(object):
    max_age = None

    def provide(self, data):
        raise NotImplementedError(
            'Subclasses of services.models.Provider must implement '
            'the provide method'
        )

    def get_private_key(self, public_key):
        raise NotImplementedError(
            'Subclasses of services.models.Provider must implement '
            'the get_private_key method'
        )

    def report_exception(self):
        pass

    def get_response(self, method, signed_data, get_header):
        if method != 'POST':
            return (405, ['POST'])
        public_key = get_header(PUBLIC_KEY_HEADER, None)
        if not public_key:
            return (400, "No public key")
        private_key = self.get_private_key(public_key)
        if not private_key:
            return (400, "Invalid public key")
        signer = TimedSerializer(private_key)
        try:
            data = signer.loads(signed_data, max_age=self.max_age)
        except SignatureExpired:
            return (400, "Signature expired")
        except BadSignature:
            return (400, "Bad Signature")
        try:
            raw_response_data = self.provide(data)
        except:
            self.report_exception()
            return (400, "Failed to process the request")
        response_data = signer.dumps(raw_response_data)
        return (200, response_data)
