import base64
import os
import time

import hvac

from inbox.config import config

vault_config = config.get('VAULT')


client = hvac.Client(url=vault_config['URL'])

client.auth_approle(vault_config['APP_ROLE_ID'], vault_config['APP_ROLE_SECRET_ID'])


def encrypt(plaintext, namespace_public_id):
    start = time.time()

    if not plaintext:
        return ''

    if not namespace_public_id:
        return ''

    # TODO: add proper handling of exception
    try:
        result = client.write(
            'transit/encrypt/' + namespace_public_id,
            plaintext=base64.b64encode(plaintext)
        )

        end = time.time()
        latency_millis = (end - start) * 1000
        print ''.join('[vault] encryption latency is: ', str(latency_millis), 'ms')

        return result['data']['ciphertext']
    except e:
        return ''


def decrypt(ciphertext, namespace_public_id):
    start = time.time()

    if not ciphertext:
        return ''

    if not namespace_public_id:
        return ''

    # TODO: add proper handling of exception
    try:
        result = client.write(
            'transit/decrypt/' + namespace_public_id,
            ciphertext=ciphertext
        )

        end = time.time()
        latency_millis = (end - start) * 1000
        print ''.join('[vault] decryption latency is: ', str(latency_millis), 'ms')

        return base64.b64decode(result['data']['plaintext'])
    except e:
        return ''


def encrypt_batch(plaintext, account_id):
    pass


def decrypt_batch(ciphertext, account_id):
    pass
