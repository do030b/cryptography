# coding=utf-8
from charm.toolbox.pairinggroup import PairingGroup, ZR, G1, G2, GT, pair
from charm.toolbox.matrixops import *
from my_crypto_toolbox import *
from kiltz_and_wee_2 import generate_crs, generate_pi, check_certificate


class JutraRoy:

    def __init__(self, groupObj, r):
        self.group = groupObj
        self.r = r

    def generate_key(self, g1, g2, t):
        crs    = generate_crs(self.group, g1, g2, t)
        g1_t   = crs[0][0][1]
        x1, x2 = self.group.random(ZR, 2)
        y      = (g1**x1) * (g1_t**x2)
        return {"public_key": (g1, g1_t, y, crs), "secret_key": (x1, x2)}

    def encrypt(self, pk, m, label=[]):
        g1, g2, y, crs   = pk
        g1_r             = g1**self.r
        g2_r             = g2**self.r
        my_r             = m*(y**self.r)

        label = list(label) + [my_r]

        labeled_instance = [[label, g1_r, g2_r]]
        pi               = generate_pi(self.group, crs, labeled_instance, self.r)
        return g1_r, g2_r, my_r, pi

    def decrypt(self, sk, c):
        # c[0]=g1**r, c[1]=g2**r, c[2]=m*Y**r, sk[0]=x1, sk[1]=x2
        return c[2] / ((c[0]**sk[0]) * (c[1]**sk[1]))

    def check_NIZK(self, pk, c, label=[]):
        crs                  = pk[3]
        g1_r, g2_r, my_r, pi = c

        instance             = [[g1_r, g2_r]]
        label = list(label) + [my_r]
        return check_certificate(self.group, crs, pi, instance, label)


if __name__ == '__main__':
    groupObj = PairingGroup('MNT159')
    r  = groupObj.random(ZR)

    jr = JutraRoy(groupObj, r)
    g1 = groupObj.random(G1)
    g2 = groupObj.random(G2)
    t  = groupObj.random(ZR)
    keys = jr.generate_key(g1, g2, t)

    m1 = groupObj.random(G1)

    c  = jr.encrypt(keys["public_key"], m1)

    m2 = jr.decrypt(keys["secret_key"], c)

    if jr.check_NIZK(keys["public_key"], c):
        print("accept!")
        print("message         : ", m1)
        print("secret key      : ", keys["secret_key"])
        print("public key      : ", keys["public_key"])
        print("encrypt message : ", c)
        print("decrypt message : ", m2)
