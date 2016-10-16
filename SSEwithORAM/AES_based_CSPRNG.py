# -*- coding: utf-8 -*-
from Crypto.Cipher import AES
from Crypto.Util import Counter
import sys


class CSPRNG:
    def __init__(self, key, randbits=128, start=0):
        self.aes_ctr = AES.new(key, AES.MODE_CTR, counter=Counter.new(AES.block_size*8))
        self.nbits = randbits
        self.end = start + 2**(AES.block_size*4) - 1
        self.ctr = start

    def padding(self, s):
        # pkcs7
        padding_size = AES.block_size - len(s) % AES.block_size
        return s + bytes([padding_size]) * padding_size

    def getrand(self):
        if self.ctr > self.end:
            # 2^(L/2)程度の乱数を出力すると1/2の確率で真の乱数と区別できるため
            raise ValueError("please change your secret key!")
        ciphertext = self.aes_ctr.encrypt(self.padding(bytes([self.ctr])))
        self.ctr += 1
        return int.from_bytes(ciphertext, sys.byteorder) & int('1'*self.nbits, 2)

    def encrypt(self, message):
        ciphertext = self.aes_ctr.encrypt(self.padding(message))
        return int.from_bytes(ciphertext, sys.byteorder) & int('1'*self.nbits, 2)

