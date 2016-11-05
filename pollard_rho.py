
from Crypto.Random import random
from functools import reduce
from Crypto.Util.number import getPrime, isPrime, inverse
import math


def _power_mod_sequence(x, stop, modulo):
    buf = x
    for _ in range(stop+1):
        yield buf
        buf = buf ** 2 % modulo


def _bits(x):
    while x != 0:
        yield x & 1
        x >>= 1


def power_mod(base, a, modulo):
    return reduce(lambda x, y: x*y%modulo,
                  (p for p, b in zip(_power_mod_sequence(base, a.bit_length(), modulo), _bits(a))
                   if int(b)), 1)


def random_walk(P, Q, modulo, order, split):
    a = 1
    b = 0
    r = P

    for _ in range(split):
        yield r, (a, b)
        u = random.getrandbits(128) % order
        v = random.getrandbits(128) % order
        r = (r * power_mod(P, u, modulo)) * (power_mod(Q, v, modulo)) % modulo
        a = (a + u) % order
        b = (b + v) % order


class RhoStack:
    __slot__ = ['stack', 'size', 'pointer']

    def __init__(self, stack_size):
        self.stack = [None] * stack_size
        self.size = stack_size
        self.top = -1
        self.collision = None

    def __repr__(self):
        return str([v for v in self.stack[:self.top+1]])

    def pop(self):
        if self.top < 0:
            raise ValueError('empty')

        self.top -= 1
        return self.stack[self.top+1]

    def push(self, value):
        while True:
            try:
                v = self.pop()
            except ValueError:
                self.top += 1
                self.stack[self.top] = value
                break
            else:
                if v[0] == value[0]:
                    self.collision = (v, value)
                if v[0] <= value[0]:
                    self.top += 2
                    self.stack[self.top] = value
                    break

    def initialize(self):
        self.top = -1
        self.stack = [None]*self.size
        self.collision = None


def rho(P, Q, modulo, order, stack_size=100):
    stack = RhoStack(stack_size)
    find = None
    roop_max = int(math.sqrt(modulo))
    while stack.collision is None:
        for r, (a, b) in random_walk(P, Q, modulo, order, roop_max):
            stack.push((r, a, b))
            if stack.collision is not None:
                find = [v[1:] for v in stack.collision]
                if find[0][0] == find[1][0] or find[1][1] == find[0][1]:
                    stack.initialize()
                break
    return (find[0][0] - find[1][0]) * inverse(find[1][1] - find[0][1], order) % order


def get_param(x, order_bits):
    P = 0
    Q = 0

    modulo = 0
    order  = 0
    while P == 0:
        while not isPrime(modulo):
            order = getPrime(order_bits)
            modulo = 2*order + 1

        for i in range(int(math.sqrt(modulo)), 1, -1):
            if power_mod(i, order, modulo) == 1:
                P = i
                Q = power_mod(P, x, modulo)
                break
    return P, Q, order, modulo


if __name__ == '__main__':
    import time
    x = 3
    ord_bits = 15

    s = time.time()
    P, Q, order, modulo = get_param(x, ord_bits)
    print(time.time() - s)

    s = time.time()
    assert rho(P, Q, modulo, order) == x
    print(time.time()-s)










