import Crypto.Cipher.AES as AES
from Crypto import Random
from Crypto.Util import Counter


class AESCTR:
    def __init__(self, key=None):
        random_generator = Random.new()
        self.IV  = random_generator.read(8)
        if key is None:
            self.__key = random_generator.read(32)
        else:
            pad = random_generator.read(32)
            self.__key = (key + pad)[:32]
        ctr = Counter.new(64, prefix=self.IV)()
        self.nonce = ctr[:8]
        self.count = int.from_bytes(ctr[8:], 'big')
        self.one = self.count

    def encrypt(self, plaintext):
        encryptor = AES.new(self.__key, AES.MODE_CTR, counter=lambda: (self.nonce + self.count.to_bytes(8, 'big')))
        ciphertext = encryptor.encrypt(plaintext)
        self.count += self.one
        return ciphertext

    def encrypt_block(self, block):
        c = self.count
        return [c] + [self.encrypt(d) for d in block]

    def decrypt(self, ciphertext, count):
        decryptor = AES.new(self.__key, AES.MODE_CTR, counter=lambda: self.nonce + count.to_bytes(8, 'big'))
        decoded_text = decryptor.decrypt(ciphertext)
        return decoded_text.decode()

    def decrypt_block(self, block):
        c = block[0]
        return [self.decrypt(d, c+i*self.one) for i, d in enumerate(block[1:])]

a = AESCTR()
e = a.encrypt_block(["a", "b"])
a.decrypt_block(e)