# -*- coding: utf-8 -*-
from charm.toolbox.securerandom import OpenSSLRand
import sys
import hashlib
import operator as op


class GarbledCircuit:
    def __init__(self):
        pass

    def lsb(self, num):
        return num & 1

    def generate_random_pair(self, random_func=None):
        if random_func is None:
            ssl = OpenSSLRand()
            a   = int.from_bytes(ssl.getRandomBits(160), sys.byteorder)
            b   = int.from_bytes(ssl.getRandomBits(160), sys.byteorder)
        else:
            a = random_func()
            b = random_func()
        # lsb must be different in a and b
        if a & 1 == b & 1:
            b ^= 1

        return a, b

    def garble_circuit(self, f, random_func=None):
        """
        :param f: f = (n: number of inputs,
                       m: number of outputs,
                       q: number of gates,
                       A: first input,
                       B: second input,
                       G: gate symbols)
        :param random_func:
        :return: e, F
        """
        n, m, q, A, B, G = f
        wire = [self.generate_random_pair(random_func) for _ in range(n + q)]
        # In the output wire, lsb(wire[n]) is n
        for i in range(n+q-m, n+q):
            if wire[i][0] & 1:
                wire[i] = wire[i][::-1]

        table_list = [self.encrypt_table(in1  = wire[A[g]-1],
                                         in2  = wire[B[g]-1],
                                         out  = wire[g-1],
                                         func = G[g-(n+1)])
                      for g in range(n + 1, n + q + 1)]

        return wire[0:n], tuple(list(f[:-1]) + [table_list])

    def hash(self, obj):
        """
        :param obj: target object
        :return: int
        """
        return int(hashlib.sha1(repr(obj).encode('utf-8')).hexdigest(), 16)

    def garble_circuit(self, f):
        """
        :param f: f = (n: number of inputs,
                       m: number of outputs,
                       q: number of gates,
                       A: first input,
                       B: second input,
                       G: gate symbols)
        :return: e, F
        """
        n, m, q, A, B, G = f
        wire = [self.generate_random_pair() for _ in range(n + q)]
        # In the output wire, lsb(wire[n]) is n
        for i in range(n+q-m, n+q):
            if wire[i][0] & 1:
                wire[i] = wire[i][::-1]

        table_list = [self.encrypt_table(in1  = wire[A[g]-1],
                                         in2  = wire[B[g]-1],
                                         out  = wire[g-1],
                                         func = G[g-(n+1)])
                      for g in range(n + 1, n + q + 1)]

        return wire[0:n], tuple(list(f[:-1]) + [table_list])

    def encrypt_table(self, in1, in2, out, func):
        """
        :param in1:  input_wire_1
        :param in2:  input_wire_2
        :param out:  output_wire
        :param func: gate_function
        :return: garbled table
        """
        table = [[self.hash((r, c)) ^ out[func(i, j)]
                  for j, c in enumerate(in2)]
                 for i, r in enumerate(in1)]
        if in1[0] & 1:
            table[0], table[1] = table[1], table[0]
        if in2[0] & 1:
            table[0][0], table[0][1] = table[0][1], table[0][0]
            table[1][0], table[1][1] = table[1][1], table[1][0]
        return table

    def evaluate_circuit(self, f, x):
        """
        :param f: f = (n: number of inputs,
                       m: number of outputs,
                       q: number of gates,
                       A: first input,
                       B: second input,
                       G: gate symbols)
        :param x: inputs of the circuit
        :return: outputs of the circuit
        """
        n, m, q, A, B, G = f
        # input_wires  = (x_[i] | 1<=i<=n),
        # inner_wires  = (x_[i] | n+1<=i<=n+q-m),
        # output_wires = (x_[i] | n+q-m+1<=i<=n+q)
        x_ = [-1] + list(x[:]) + [-1]*q
        for g in range(n+1, n+q+1):
            a, b = A[g], B[g]
            x_[g] = G[g-(n+1)](x_[a], x_[b])
        return [x_[i] & 1 for i in range(n+q-m+1, n+q+1)]

    def evaluate_garbled_circuit(self, F, X):
        """
        :param F: F = (n: number of inputs,
                       m: number of outputs,
                       q: number of gates,
                       A: first input,
                       B: second input,
                       G: gate symbols)
        :param X: garbled inputs of the circuit
        :return: outputs of the circuit
        """
        n, m, q, A, B, G = F
        # input_wires  = (X_[i] | 1<=i<=n),
        # inner_wires  = (X_[i] | n+1<=i<=n+q-m),
        # output_wires = (X_[i] | n+q-m+1<=i<=n+q)
        X_ = [-1] + list(X[:]) + [-1]*q
        for g in range(n+1, n+q+1):
            a, b = A[g], B[g]
            X_[g] = G[g-(n+1)][X_[a] & 1][X_[b] & 1] ^ self.hash((X_[a], X_[b]))
        return [X_[i] & 1 for i in range(n+q-m+1, n+q+1)]

    def encode(self, e, x):
        return [e[i][x[i]] for i in range(len(x))]


if __name__ == '__main__':
    from itertools import product
    from functools import reduce

    def check(gc, f, x):
        e, F = gc.garble_circuit(f)
        X = gc.encode(e, x)
        lhs = gc.evaluate_circuit(f, x)
        rhs = gc.evaluate_garbled_circuit(F, X)
        return lhs == rhs

    f = (4, 1, 3, {5: 1, 6: 3, 7: 5}, {5: 2, 6: 4, 7: 6}, [op.and_, op.xor, op.or_])
    gc = GarbledCircuit()
    print(reduce(op.and_, [check(gc, f, i) for i in product((0, 1), repeat=4)]))

