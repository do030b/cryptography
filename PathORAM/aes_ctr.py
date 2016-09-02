import Crypto.Cipher.AES as AES
from Crypto import Random


class AESCTR:
    def __init__(self, key_size=16, key=None):
        assert key_size in (16, 24, 32)
        self.key_size = key_size

        if key is None:
            self.key = Random.new().read(AES.block_size)
        self.block_cipher = AES.new(self.key, AES.MODE_ECB)

    def encrypt(self, plain_text):
        nonce   = Random.new().read(AES.block_size//2)
        cipher_text = b''
        num_of_chunk = len(plain_text) // AES.block_size + 1

        for i in range(num_of_chunk):
            chunk = int.from_bytes(plain_text[i*AES.block_size: (i+1)*AES.block_size], 'big')
            en = self.block_cipher.encrypt(nonce + i.to_bytes(AES.block_size//2, 'big'))
            c = int.from_bytes(en, 'big') ^ chunk
            cipher_text += c.to_bytes(AES.block_size, 'big')

        return nonce + cipher_text

    def decrypt(self, cipher_block):
        nonce = cipher_block[0:AES.block_size//2]
        cipher_text = cipher_block[AES.block_size//2:]
        num_of_chunk = len(cipher_text) // AES.block_size

        plain_text = b''
        for i in range(num_of_chunk):
            chunk = int.from_bytes(cipher_text[i*AES.block_size: (i+1)*AES.block_size], 'big')
            c = self.block_cipher.encrypt(nonce + i.to_bytes(AES.block_size//2, 'big'))
            m  = int.from_bytes(c, 'big') ^ chunk
            plain_text += m.to_bytes(AES.block_size, 'big')[AES.block_size-(len(bin(m))-2)//8-1:]

        return plain_text


if __name__ == '__main__':
    cipher = AESCTR(24)
    p = b"hello world!"
    c = cipher.encrypt(p)
    d = cipher.decrypt(c)

    print(p)
    print(c)
    print(d)
