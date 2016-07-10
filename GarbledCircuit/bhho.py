# coding=utf-8
from charm.toolbox.matrixops import *
from my_crypto_toolbox import *
import random
from functools import reduce


class BHHO:

    def __init__(self, groupObj, g, k, r):
        self.group = groupObj
        self.g     = g
        self.k     = k
        self.r     = r
        self.n     = len(self.k)

    def generate_key(self, sk=None):
        if sk is None:
            sk = [random.randint(0, 1) for _ in range(self.n)]
        pk = [self.g**t for t in self.k]
        h  = reduce(lambda a, b: a * b, [g**s for g, s in zip(pk, sk)])**(-1)
        pk += [h]

        return {"public_key": pk, "secret_key": sk}

    def encrypt(self, pk, m):
        return [g**self.r for g in pk[0:-1]] + [m * pk[-1]**self.r]

    def decrypt(self, sk, c):
        return c[-1] * reduce(lambda a, b: a * b, [g**s for g, s in zip(c[0:-1], sk)])


if __name__ == '__main__':
    from charm.toolbox.integergroup import IntegerGroup
    groupObj = IntegerGroup()
    groupObj.paramgen(1024)
    r = groupObj.random()

    k  = [groupObj.random() for _ in range(4)]
    g1 = groupObj.randomGen()

    bhho = BHHO(groupObj, g1, k, r)
    keys = bhho.generate_key()
    m1 = groupObj.random()
    c = bhho.encrypt(keys["public_key"], m1)
    m2 = bhho.decrypt(keys["secret_key"], c)
    print(m1==m2)
