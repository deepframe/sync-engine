import ssl
import json
import smtpd
import asyncore
import datetime

import pytest
import gevent

from tests.util.base import default_account
from tests.api.base import api_client, new_api_client
from tests.api_legacy.base import api_client as api_legacy_client

__all__ = ['api_client', 'api_legacy_client', 'default_account']

SELF_SIGNED_CERTFILE = 'tests/data/self_signed_cert.pem'
SELF_SIGNED_KEYFILE = 'tests/data/self_signed_cert.key'

from inbox.sendmail.smtp.postel import SMTP_OVER_SSL_TEST_PORT

SHARD_ID = 0
SMTP_SERVER_HOST = 'localhost'
SMTP_SERVER_PORT = SMTP_OVER_SSL_TEST_PORT


class BadCertSMTPServer(smtpd.DebuggingServer):
    def __init__(self, localaddr, remoteaddr):
        smtpd.DebuggingServer.__init__(self, localaddr, remoteaddr)
        self.set_socket(ssl.wrap_socket(self.socket,
                                        certfile=SELF_SIGNED_CERTFILE,
                                        keyfile=SELF_SIGNED_KEYFILE,
                                        server_side=True))


def run_bad_cert_smtp_server():
    BadCertSMTPServer((SMTP_SERVER_HOST, SMTP_SERVER_PORT), (None, None))
    asyncore.loop()


@pytest.yield_fixture(scope='function')
def bad_cert_smtp_server():
    s = gevent.spawn(run_bad_cert_smtp_server)
    yield s
    s.kill()


@pytest.fixture(scope='function')
def local_smtp_account(db):
    from inbox.auth.generic import GenericAuthHandler

    handler = GenericAuthHandler(provider_name='custom')
    acc = handler.get_account(SHARD_ID,
                              'user@gmail.com',
                              {'email': 'user@gmail.com',
                               'password': 'hunter2',
                               'imap_server_host': 'imap-test.nylas.com',
                               'imap_server_port': 143,
                               'smtp_server_host': SMTP_SERVER_HOST,
                               'smtp_server_port': SMTP_SERVER_PORT})
    db.session.add(acc)
    db.session.commit()
    return acc


@pytest.fixture
def example_draft(db, default_account):
    return {
        'subject': 'Draft test at {}'.format(datetime.datetime.utcnow()),
        'body': '<html><body><h2>Sea, birds and sand.</h2></body></html>',
        'to': [{'name': 'The red-haired mermaid',
                'email': default_account.email_address}]
    }


def test_smtp_ssl_verification_bad_cert(db, bad_cert_smtp_server,
                                        example_draft, local_smtp_account,
                                        api_legacy_client):

    error_msg = 'SMTP server SSL certificate verify failed'

    api_client = new_api_client(db, local_smtp_account.namespace)
    gevent.sleep(0.2)  # let SMTP daemon start up
    r = api_client.post_data('/send', example_draft)
    assert r.status_code == 503
    assert json.loads(r.data)['message'] == error_msg


def test_smtp_ssl_verification_bad_cert_legacy(db, bad_cert_smtp_server,
                                               example_draft,
                                               local_smtp_account,
                                               api_legacy_client):

    error_msg = 'SMTP server SSL certificate verify failed'

    ns_public_id = local_smtp_account.namespace.public_id
    r = api_legacy_client.post_data('/send', example_draft, ns_public_id)
    assert r.status_code == 503
    assert json.loads(r.data)['message'] == error_msg


if __name__ == '__main__':
    server = BadCertSMTPServer((SMTP_SERVER_HOST, SMTP_SERVER_PORT), None)
    asyncore.loop()
