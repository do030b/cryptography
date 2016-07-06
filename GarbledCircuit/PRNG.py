
from Crypto.Cipher import AES
import sys


class PRNG:
    def __init__(self, key, counter=0):
        if len(key) != 16:
            raise ValueError("key length must be 16")
        self.__key = key
        self.__aes = AES.new(self.__key, AES.MODE_ECB)
        self.__counter = counter

    def generate_random(self):
        if self.__counter >= 10000000000000000:
            raise ValueError("please change your secret key!")

        ciphertext = self.__aes.encrypt(str(self.__counter).zfill(16))
        self.__counter += 1

        return int.from_bytes(ciphertext, sys.byteorder)
