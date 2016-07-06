# coding=utf-8
from charm.toolbox.pairinggroup import PairingGroup, ZR, G1, G2, pair
from charm.toolbox.matrixops import *


class EllipticCurveElGamal:

    def __init__(self, groupObj, r):
        self.group = groupObj
        self.r     = r

    def generate_key(self, g1):
        x  = self.group.random(ZR)
        return {"public_key": (g1, x * g1), "secret_key": x}

    def encrypt(self, pk, m):
        g1, g1_x = pk
        return g1**self.r, m * (g1_x**self.r)

    def decrypt(self, sk, c):
        return c[1] - sk * c[0]


if __name__ == '__main__':
    groupObj = PairingGroup('SS512')
    r  = groupObj.random()

    el = EllipticCurveElGamal(groupObj, r)
    g1 = groupObj.random(G1)
    keys = el.generate_key(g1)
    m = groupObj.random(G1)
    print(m)
    c = el.encrypt(keys["public_key"], m)
    print(c)
    m2 = el.decrypt(keys["secret_key"], c)
    print(m2)
