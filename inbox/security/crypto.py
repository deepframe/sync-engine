import base64
import zlib
from Crypto.Cipher import AES
from Crypto import Random
from inbox.config import config

BS = 16
pad = lambda s: s + (BS - len(s) % BS) * chr(BS - len(s) % BS)
unpad = lambda s : s[:-ord(s[len(s)-1:])]

class CryptoCipher:
    def __init__(self):
        self.key = config.get_required('CRYPTO_ENCRYPTION_KEY').decode('hex')

    def encrypt(self, text):
        compressed = zlib.compress(text.encode('utf-8'))
        paded = pad(compressed)
        iv = Random.new().read(AES.block_size)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return 'crypto:' + base64.b64encode(iv + cipher.encrypt(paded))

    def decrypt(self, encrypted_text):
        if not encrypted_text.startswith('crypto'):
            return encrypted_text
        decoded = base64.b64decode(encrypted_text[6:])
        iv = decoded[:16]
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return zlib.decompress(unpad(cipher.decrypt(decoded[16:]))).decode('utf-8')
