import Crypto.Cipher.AES as AES
from Crypto import Random


class AESCTR:
    def __init__(self, key=None):
        random_generator = Random.new()
        if key is None:
            self.__key = random_generator.read(32)
        else:
            pad = random_generator.read(32)
            self.__key = (key + pad)[:32]
        self.nonce = int.from_bytes(random_generator.read(16), 'big')
        self.count = 0

    def __encrypt(self, plaintext):
        encryptor = AES.new(self.__key, AES.MODE_CTR, counter=lambda: ((self.nonce ^ self.count).to_bytes(16, 'big')))
        ciphertext = encryptor.encrypt(plaintext)
        self.count += 1
        return ciphertext

    def encrypt_block(self, block):
        c = self.count
        return [c] + [self.__encrypt(d) for d in block]

    def __decrypt(self, ciphertext, count):
        decryptor = AES.new(self.__key, AES.MODE_CTR, counter=lambda: (self.nonce ^ count).to_bytes(16, 'big'))
        decoded_text = decryptor.decrypt(ciphertext)
        return decoded_text.decode()

    def decrypt_block(self, block):
        c = block[0]
        return [self.__decrypt(d, c+i) for i, d in enumerate(block[1:])]


if __name__ == '__main__':
    a = AESCTR()
    e = a.encrypt_block(["a", "b"])
    a.decrypt_block(e)