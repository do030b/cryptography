# -*- coding: utf-8 -*-
from SSEwithORAM.AES_based_CSPRNG import CSPRNG
from SSEwithORAM.file_operation import *
from Crypto import Random
from Crypto.Random import random
from pbkdf2 import PBKDF2


def store_phase(D, W, K):
    C = [encrypt_file(Di, K[2]) for Di in D]

    f = lambda x: CSPRNG(K[0], randbits=128).encrypt(x)
    g = lambda x: CSPRNG(K[1], randbits=len(D)).encrypt(x)

    index = [int("".join([str(int(has_word(Di, Wi))) for Di in D]), 2) for Wi in W]
    encrypted_index = [Ii ^ g(Wi) for Ii, Wi in zip(index, W)]
    encrypted_word  = [f(Wi) for Wi in W]
    I = [enc for enc in zip(encrypted_word, encrypted_index)]
    random.StrongRandom().shuffle(I)

    return C, I


if __name__ == '__main__':
    output_dir = 'SSEwithORAM/TEST/plain_text/output/'

    key_size = 16
    salt = Random.new().read(8)

    secret_key_1 = "this is secret key 1."
    secret_key_2 = "this is secret key 2."
    secret_key_3 = "this is secret key 3."

    K = [PBKDF2(secret_key_1, salt).read(key_size),
         PBKDF2(secret_key_2, salt).read(key_size),
         PBKDF2(secret_key_3, salt).read(key_size)]

    W = [b'word1', b'word2']

    D = ['SSEwithORAM/TEST/plain_text/D1.txt',
         'SSEwithORAM/TEST/plain_text/D2.txt',
         'SSEwithORAM/TEST/plain_text/D3.txt',
         'SSEwithORAM/TEST/plain_text/D4.txt',
         'SSEwithORAM/TEST/plain_text/D5.txt']

    D_width = len(D)

    C, I = store_phase(D, W, K)

    f = lambda x: CSPRNG(K[0], randbits=128).encrypt(x)
    g = lambda x: CSPRNG(K[1], randbits=D_width).encrypt(x)
    t = {Wi: (f(Wi), g(Wi)) for Wi in W}

    fk1_w1, gk2_w1 = t[W[0]]
    fk1_w2, gk2_w2 = t[W[1]]

    mask1 = [int(i) for i in bin(next(gk2_w1 ^ x[1] for x in I if x[0] == fk1_w1))[2:].zfill(D_width)]
    mask2 = [int(i) for i in bin(next(gk2_w2 ^ x[1] for x in I if x[0] == fk1_w2))[2:].zfill(D_width)]

    ans = [c for c, m in zip(C, mask1) if m]

    decrypted_file = [decrypt_file(i, K[2], output_dir) for i in ans]
