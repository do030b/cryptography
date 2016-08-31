# -*- coding: utf-8 -*-
import operator as op
from GarbledCircuit.garbled_circuit import GarbledCircuit
from charm.toolbox.securerandom import OpenSSLRand
import sys
from GarbledCircuit.bhho import BHHO
from charm.toolbox.integergroup import IntegerGroup


def output_first(a, b):
    return a


class GarbledCircuitWithBHHO(GarbledCircuit):

    def __init__(self, groupObj, g, k, r):
        super().__init__()
        self.bhho = BHHO(groupObj, g, k, r)
        self.g = g

    def generate_keys(self, sk=None):
        return self.bhho.generate_key(sk)

    def garble_circuit(self, f):
        n, m, q, A, B, G = f

        e = [self.generate_random_pair_for_BHHO() for _ in range(n)]
        wire  = [(self.hash(int(i)), self.hash(int(j))) for i, j in e]
        wire += [self.generate_random_pair() for _ in range(q)]
        # In the output wire (pair), lsb is (0, 1)
        for i in range(m):
            if wire[-1-i][0] & 1 == 1:
                wire[-1-i] = wire[-1-i][::-1]

        table_list = [self.encrypt_table(in1=wire[A[g]-1], in2=wire[B[g]-1], out=wire[g-1], func=G[g-(n+1)])
                      for g in range(n + 1, n + q + 1)]
        # return e, F
        return e, list(f[:-1]) + [table_list]

    def generate_random_pair_for_BHHO(self):
        while(True):
            ssl = OpenSSLRand()
            a   = int.from_bytes(ssl.getRandomBits(160), sys.byteorder)
            b   = int.from_bytes(ssl.getRandomBits(160), sys.byteorder)
            # lsb is different from one another
            k0 = self.hash(int(self.g**a))
            k1 = self.hash(int(self.g**b))
            if k0 & 1 != k1 & 1:
                break

        return g**a, g**b

    def encode(self, e, x):
        return [self.hash(int(e[i][x[i]])) for i in range(len(x))]

    def encrypt_encode(self, e, x, pk, bit_len=4):
        if len(x) > bit_len:
            exit(1)
        return [self.bhho.encrypt(pk, e[i][x[i]]) for i in range(bit_len)]

    def decrypt_encode(self, enX, sk):
        return [self.hash(int(self.bhho.decrypt(sk, c))) for c in enX]


if __name__ == '__main__':
    ID = [4, 1, 3, {5: 1, 6: 5, 7: 6}, {5: 2, 6: 3, 7: 4}, [output_first]*3]

    f0 = [4, 1, 3, {5: 1, 6: 3, 7: 5}, {5: 2, 6: 4, 7: 6}, [op.and_, op.xor, op.or_]]
    f1 = [4, 1, 3, {5: 3, 6: 2, 7: 1}, {5: 4, 6: 5, 7: 6}, [op.and_, op.xor, op.or_]]

    x0  = [1, 0, 1, 0]
    x1  = [1, 0, 0, 1]

    print("--init game--")
    ssl = OpenSSLRand()
    groupObj = IntegerGroup()
    groupObj.paramgen(1024)
    g = groupObj.randomGen()
    r = groupObj.random()
    k = [groupObj.random() for _ in range(4)]

    gc = GarbledCircuitWithBHHO(groupObj, g, k, r)

    print("--start--")
    print()
    print("E:")
    print("f0size = ", f0[0:3])
    print("f1size = ", f1[0:3])
    print("f0(x0) = ", gc.evaluate_circuit(f0, x0))
    print("f1(x1) = ", gc.evaluate_circuit(f1, x1))
    keys = gc.generate_keys()

    print()
    print("C:")
    rand = int.from_bytes(ssl.getRandomBits(1), sys.byteorder)
    print("b = ", rand)
    if rand:
        y = gc.evaluate_circuit(f1, x1)
    else:
        y = gc.evaluate_circuit(f0, x0)

    while(True):
        e, F = gc.garble_circuit(ID)
        X = gc.encode(e, [y[0], 0, 0, 0])

        lhs = gc.evaluate_garbled_circuit(f0[:-1]+[F[-1]], X)
        rhs = gc.evaluate_garbled_circuit(f1[:-1]+[F[-1]], X)

        if(lhs==rhs):
            print("y = ", y)
            print("Ev(F, X) = ", gc.evaluate_garbled_circuit(F, X))
            print("Ev(F, topo(f0), X) = ", lhs)
            print("Ev(F, topo(f1), X) = ", rhs)
            enX = gc.encrypt_encode(e, [y[0], 0, 0, 0], keys["public_key"])
            break

    print()
    print("E:")
    deX = gc.decrypt_encode(enX, keys["secret_key"])

    ans = gc.evaluate_garbled_circuit(F, deX)
    phi0 = gc.evaluate_garbled_circuit(f0[:-1]+[F[-1]], deX)
    phi1 = gc.evaluate_garbled_circuit(f1[:-1]+[F[-1]], deX)
    print("Ev(F, deX)           = ", ans)
    print("Ev(F, topo(f0), deX) = ", phi0)
    print("Ev(F, topo(f1), deX) = ", phi1)
    print("topo(F)  = ", F[0:-1])
    print("topo(ID) = ", ID[0:-1])
    print("topo(f0) = ", f0[0:-1])
    print("topo(f1) = ", f1[0:-1])

    print("--finish--")
