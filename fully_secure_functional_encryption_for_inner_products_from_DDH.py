# -*- coding: utf-8 -*-
from charm.toolbox.integergroup import *
from functools import reduce


class MyIntegerGroup(IntegerGroup):
    def __init__(self):
        super().__init__()

    def randomGen(self):
        while True:
            h = random(self.p)
            if h == 0:
                continue
            g = (h ** self.r) % self.p
            if not g == 1:
                break
        return g


class FullySecureFE:
    def __init__(self):
        self.msk = None
        self.mpk = None
        self.x = None

    def setup(self, λ, l):
        G = MyIntegerGroup()
        while True:
            G.paramgen(λ+1)
            if G.p > 2**λ:
                break
        # g, h <- G
        g = G.randomGen()
        h = G.randomGen()

        # msk := {(si, ti) | si, ti <- Zq, 1<=i<=l}
        self.msk = [(G.random(), G.random()) for _ in range(l)]
        # mpk := (G, g, h, {hi|1<=i<=l})
        self.mpk = [G, g, h, [(g**si)*(h**ti) for si, ti in self.msk]]

    def vectorgen(self):
        return [self.mpk[0].random() for _ in range(len(self.mpk[3]))]

    def keygen(self, x):
        self.x = x
        return reduce(lambda a, b: (a[0]+b[0], a[1]+b[1]),
                      [(xi*si, xi*ti) for xi, (si, ti) in zip(x, self.msk)])

    def encrypt(self, y):
        G, g, h, hv = self.mpk
        r = G.random()
        C = g**r
        D = h**r
        E = [(g**yi)*(hi**r) for yi, hi in zip(y, hv)]

        return [C, D] + E

    def decrypt(self, skx, Cy):
        g = self.mpk[1]
        sx, tx = skx
        C = Cy[0]
        D = Cy[1]
        E = Cy[2:]
        numer = reduce(lambda a, b: a*b, [Ei**xi for Ei, xi in zip(E, self.x)])
        denom = (C**sx) * (D**tx)
        Ex = numer / denom

        return Ex, g


def main():
    f = FullySecureFE()
    f.setup(1024, 10)
    x = f.vectorgen()
    skx = f.keygen(x)
    y = f.vectorgen()
    Cy = f.encrypt(y)
    Ex, g = f.decrypt(skx, Cy)
    g**reduce(lambda a,b:a+b, [xi*yi for xi, yi in zip(x,y)]) == Ex
