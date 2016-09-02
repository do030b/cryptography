import Crypto.Cipher.AES as AES
from Crypto import Random


class AESCTR:
    def __init__(self, block_size=16, key=None):
        assert block_size in (16, 24, 32)
        self.BLOCK_SIZE = block_size

        if key is None:
            self.key = Random.new().read(self.BLOCK_SIZE)
        self.block_cipher = AES.new(self.key, AES.MODE_ECB)

    def encrypt(self, plain_text):
        nonce   = Random.new().read(self.BLOCK_SIZE//2)
        cipher_text = b''
        num_of_chunk = len(plain_text) // self.BLOCK_SIZE + 1

        for i in range(num_of_chunk):
            chunk = int.from_bytes(plain_text[i*self.BLOCK_SIZE: (i+1)*self.BLOCK_SIZE], 'big')
            en = self.block_cipher.encrypt(nonce + i.to_bytes(self.BLOCK_SIZE//2, 'big'))
            c = int.from_bytes(en, 'big') ^ chunk
            cipher_text += c.to_bytes(self.BLOCK_SIZE, 'big')

        return nonce + cipher_text

    def decrypt(self, cipher_block):
        nonce = cipher_block[0:self.BLOCK_SIZE//2]
        cipher_text = cipher_block[self.BLOCK_SIZE//2:]
        num_of_chunk = len(cipher_text) // self.BLOCK_SIZE

        plain_text = b''
        for i in range(num_of_chunk):
            chunk = int.from_bytes(cipher_text[i*self.BLOCK_SIZE: (i+1)*self.BLOCK_SIZE], 'big')
            c = self.block_cipher.encrypt(nonce + i.to_bytes(self.BLOCK_SIZE//2, 'big'))
            m  = int.from_bytes(c, 'big') ^ chunk
            plain_text += m.to_bytes(self.BLOCK_SIZE, 'big')[self.BLOCK_SIZE-(len(bin(m))-2)//8-1:]

        return plain_text


if __name__ == '__main__':
    pass
