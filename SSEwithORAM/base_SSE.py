# -*- coding: utf-8 -*-
from AES_based_CSPRNG import CSPRNG
from file_operation import *
from Crypto import Random
from Crypto.Random import random
from pbkdf2 import PBKDF2


def store_phase(D, W, K):
    C = [encrypt_file(Di, K[2]) for Di in D]

    f = CSPRNG(K[0], randbits=128)
    g = CSPRNG(K[1], randbits=len(D))

    index = [int("".join(map(str, [int(has_word(Di, Wi)) for Di in D])), 2) for Wi in W]
    encrypted_index = [Ii ^ g.encrypt(Wi) for Ii, Wi in zip(index, W)]
    encrypted_word  = [f.encrypt(Wi) for Wi in W]
    I = [enc for enc in zip(encrypted_word, encrypted_index)]
    random.StrongRandom().shuffle(I)

    return C, I


if __name__ == '__main__':
    key_size = 16
    salt = Random.new().read(8)

    secret_key_1 = "this is secret key 1."
    secret_key_2 = "this is secret key 2."
    secret_key_3 = "this is secret key 3."

    K = [PBKDF2(secret_key_1, salt).read(key_size),
         PBKDF2(secret_key_2, salt).read(key_size),
         PBKDF2(secret_key_3, salt).read(key_size)]

    W = [b'word1', b'word2']

    D = {'TEST/plain_text/D1.txt',
         'TEST/plain_text/D2.txt',
         'TEST/plain_text/D3.txt',
         'TEST/plain_text/D4.txt',
         'TEST/plain_text/D5.txt'}

    C, I = store_phase(D, W, K)
    #
    # t = dict()
    # f = CSPRNG(K[0], randbits=128)
    # g = CSPRNG(K[1], randbits=len(D))
    # t[W[0]] = (f.encrypt(W[0]), g.encrypt(W[0]))


