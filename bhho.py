# coding=utf-8
from charm.toolbox.pairinggroup import PairingGroup, ZR, G1, G2, pair
from charm.toolbox.matrixops import *
from my_crypto_toolbox import *
import random
from functools import reduce


class BHHO:

    def __init__(self, groupObj, k, r):
        self.group = groupObj
        self.k     = k
        self.r     = r
        self.n     = len(self.k)

    def generate_key(self, g1):
        sk = intlist_to_zrlist(self.group, [random.randint(0, 1) for _ in range(self.n)])
        pk = [g1**t for t in self.k]
        h  = reduce(lambda a, b: a * b, [g**s for g, s in zip(pk, sk)])**int_to_zr(self.group, -1)
        pk += [h]

        return {"public_key": pk, "secret_key": sk}

    def encrypt(self, pk, m):
        return [g**self.r for g in pk[0:-1]] + [m * pk[-1]**self.r]

    def decrypt(self, sk, c):
        return c[-1] * reduce(lambda a, b: a * b, [g**s for g, s in zip(c[0:-1], sk)])


if __name__ == '__main__':
    groupObj = PairingGroup('SS512')
    r = groupObj.random(ZR)

    k  = [groupObj.random(ZR) for _ in range(200)]
    bhho = BHHO(groupObj, k, r)
    g1 = groupObj.random(G1)
    keys = bhho.generate_key(g1)
    m = groupObj.random(G1)
    print(m)
    c = bhho.encrypt(keys["public_key"], m)
    print(c)
    m2 = bhho.decrypt(keys["secret_key"], c)
    z = groupObj.random(ZR)
    print(m2)
