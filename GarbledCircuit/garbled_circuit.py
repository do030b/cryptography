# -*- coding: utf-8 -*-
from charm.toolbox.securerandom import OpenSSLRand
import sys
import hashlib
import operator as op


def lsb(num):
    return num & 1


def generate_random_pair(random_func=None):
    if random_func is None:
        ssl = OpenSSLRand()
        a   = int.from_bytes(ssl.getRandomBits(160), sys.byteorder)
        b   = int.from_bytes(ssl.getRandomBits(160), sys.byteorder)
    else:
        a = random_func()
        b = random_func()
    # lsb is different from one another
    if lsb(a) == lsb(b):
        b += 1

    return a, b


def sha1(objects):
    return hashlib.sha1(repr(objects).encode('utf-8')).hexdigest()


def garble_circuit(f, random_func=None):
    n, m, q, A, B, G = f
    wire = [generate_random_pair(random_func) for _ in range(n + q)]
    # In the output wire (pair), lsb is (0, 1)
    for i in range(m):
        if lsb(wire[-1-i][0]) == 1:
            wire[-1-i] = wire[-1-i][::-1]

    table_list = [encrypt_table(in1=wire[A[g]-1], in2=wire[B[g]-1], out=wire[g-1], func=G[g-(n+1)])
                  for g in range(n + 1, n + q + 1)]
    # return e, F
    return wire[0:n], tuple(list(f[:-1]) + [table_list])


def encrypt_table(in1, in2, out, func):
    table = [[int(sha1((r, c)), 16) ^ out[func(i, j)] for j, c in enumerate(in2)] for i, r in enumerate(in1)]
    if lsb(in1[0]) == 1:
        table[0], table[1] = table[1], table[0]
    if lsb(in2[0]) == 1:
        table[0][0], table[0][1] = table[0][1], table[0][0]
        table[1][0], table[1][1] = table[1][1], table[1][0]
    return table


def evaluate_circuit(f, x):
    n, m, q, A, B, G = f
    x_ = list(x[:])
    for g in range(n + 1, n + q + 1):
        a, b = A[g], B[g]
        x_.append(G[g - (n + 1)](x_[a - 1], x_[b - 1]))
    return lsb(x_[-1])


def evaluate_garbled_circuit(F, X):
    n, m, q, A, B, G = F
    X_ = list(X[:])
    for g in range(n + 1, n + q + 1):
        a, b = A[g], B[g]
        X_.append(G[g - (n + 1)][lsb(X_[a - 1])][lsb(X_[b - 1])] ^ int(sha1((X_[a - 1], X_[b - 1])), 16))
    return lsb(X_[-1])


def encode(e, x, bit_len=4):
    if len(x) > bit_len:
        exit(1)
    return [e[i][x[i]] for i in range(bit_len)]


def check(f, x):
    e, F = garble_circuit(f)
    X = encode(e, x)
    lhs = evaluate_circuit(f, x)
    rhs = evaluate_garbled_circuit(F, X)
    return lhs == rhs


if __name__ == '__main__':
    from itertools import product
    from functools import reduce
    f = (4, 1, 3, {5: 1, 6: 3, 7: 5}, {5: 2, 6: 4, 7: 6}, [op.and_, op.xor, op.or_])

    print(reduce(op.and_, [reduce(op.and_, [check(f, i) for i in product((0, 1), repeat=4)])
                           for _ in range(100)]))
