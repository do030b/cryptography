# -*- coding: utf-8 -*-
import zipfile
import sys
import io
from Crypto.Cipher import AES
from Crypto import Random


def padding(s):
    # pkcs7
    padding_size = AES.block_size - len(s) % AES.block_size
    return s + bytes([padding_size]) * padding_size


def encrypt(plain_text, secret_key):
    padded_text  = padding(plain_text)
    iv = Random.new().read(AES.block_size)

    aes_cbc = AES.new(secret_key, AES.MODE_CBC, iv)
    cipher_text = aes_cbc.encrypt(padded_text)

    # one time pad for iv
    iv_otp = (int.from_bytes(iv, sys.byteorder) ^ int.from_bytes(secret_key, sys.byteorder))\
        .to_bytes(AES.block_size, sys.byteorder)
    return iv_otp + cipher_text


def decrypt(cipher_text, secret_key):
    iv_otp      = cipher_text[:AES.block_size]
    iv = (int.from_bytes(iv_otp, sys.byteorder) ^ int.from_bytes(secret_key, sys.byteorder))\
        .to_bytes(AES.block_size, sys.byteorder)

    cipher_text = cipher_text[AES.block_size:]

    aes_cbc = AES.new(secret_key, AES.MODE_CBC, iv)
    padded_text = aes_cbc.decrypt(cipher_text)

    padding_size = padded_text[-1]
    plain_text = padded_text[:-padding_size]

    return plain_text


def encrypt_file(input_file_name, secret_key):
    with io.BytesIO() as zip_file:
        with zipfile.ZipFile(zip_file, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.write(input_file_name)
        cipher_text = encrypt(zip_file.getvalue(), secret_key)
    return cipher_text


def decrypt_file(cipher_text, secret_key, output_dir='./'):
    plain_text = decrypt(cipher_text, secret_key)
    with io.BytesIO(plain_text) as zip_file:
        with zipfile.ZipFile(zip_file) as zf:
            zf.extractall(output_dir)
            output_file_name_list = zf.namelist()
    return output_file_name_list


def has_word(file_name, word):
    with open(file_name, 'rb') as fo:
        text = fo.read()
    return word in text
