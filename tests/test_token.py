import pytest

from solid_client import token

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.backends import default_backend
from authlib.jose import JsonWebKey


@pytest.fixture()
def dummy_key_pair():

    key = ec.generate_private_key(ec.SECP256R1(), backend=default_backend())

    private_key = key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption())
    public_key = key.public_key().public_bytes(
        serialization.Encoding.OpenSSH,
        serialization.PublicFormat.OpenSSH
    )

    PRIVATE_KEY = JsonWebKey.import_key(private_key, {'kty': 'EC'})
    PUBLIC_KEY = JsonWebKey.import_key(public_key, {'kty': 'EC'})

    keys = {'PUBLIC_KEY': PUBLIC_KEY,
            'PRIVATE_KEY': PRIVATE_KEY}

    return keys


def test_gen_access_request_dpop_token_type(dummy_key_pair):

    res = token.gen_access_request_dpop_token(dummy_key_pair['PUBLIC_KEY'],
                                              dummy_key_pair['PRIVATE_KEY'],
                                              'test')
    assert type(res) is bytes
