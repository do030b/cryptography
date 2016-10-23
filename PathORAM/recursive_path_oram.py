# -*- coding: utf-8 -*-
import math
from enum import Enum
from Crypto.Random import random
from SSEwithORAM import file_operation as fo
import itertools as it
import json

OP = Enum('OP', 'read write')


class yi_generator:
    def __init__(self, y, L):
        self.origin_y = y
        self.origin_L = L

    def __iter__(self):
        self.y = self.origin_y
        self.L = self.origin_L
        return self

    def __next__(self):
        ret = self.y
        if self.L <= 0:
            raise StopIteration
        self.y = math.ceil(self.y/2)
        self.L -= 1
        return ret


class Store:
    def __init__(self, L, Z=4):
        self.L = L
        self.Z = Z
        self.total = self.Z*(2**(self.L+1)-1)
        self.store = [[None]*self.Z for _ in range(2**(self.L+1)-1)]

    def s(self):
        buckets = [i for i in zip(*[iter(self.store)]*self.Z)]

        return {i: bucket for i, bucket in enumerate(buckets)}

    def update(self, blocks):
        if len(blocks) != self.Z*(2**(self.L+1)-1):
            print(self.L)
            print(len(blocks))
            raise ValueError
        self.store = blocks

    def path(self, x, l):
        """
        :param x: path from leaf to root
        :param l: depth of the node
        :return: index of the node
        """
        if x > 2**self.L-1 or x < 0 or l > self.L or l < 0:
            raise ValueError
        return (2 ** l) + (x >> (self.L-l)) - 1

    def read_bucket(self, x, l):
        top = self.path(x, l) * self.Z
        bottom = top + self.Z
        return self.store[top:bottom]

    def write_bucket(self, x, depth, new_bucket):
        top = self.path(x, depth) * self.Z
        if len(new_bucket) != self.Z:
            raise ValueError
        for n, block in enumerate(new_bucket):
            self.store[top + n] = block


class Server:
    def __init__(self, N, Z=4):
        self.N = N
        self.L = math.ceil(math.log2(N)) - 1
        self.Z = Z
        self.T = [Store(L=self.L-l, Z=self.Z) for l in range(self.L)]

    def read_path(self, l, x):
        return [self.T[self.L-l].read_bucket(x, li) for li in range(l+1)]


class Client:
    def __init__(self, server):
        self.Server = server
        self.N = server.N
        self.Z = server.Z
        self.L = server.L
        self.k = b'1234567890123456'
        self.local_position_map = []
        self.stash = [[] for _ in range(self.L)]
        self.dummy_block = [0, 0, 0]
        self.err = None

    def initialize(self, A):
        rand = random.StrongRandom()
        trees = [None] * self.L
        data = A
        for l in range(self.L, 0, -1):
            # set random position map
            # position is L bits
            position_map = [i for i in range(2**l)] * 2
            rand.shuffle(position_map)

            # set real data form of blocks (id, data, position) and sorted by position
            real_blocks = [[i, data_i, pos_i]
                           for i, (data_i, pos_i) in enumerate(zip(data, position_map), 1)]

            # padding by dummy blocks
            total_blocks = self.Z*(2**(l+1)-1)
            tree = [self.dummy_block for _ in range(total_blocks)]

            for b in real_blocks:
                leaf_top = (2**l - 1 + b[2])*self.Z
                tree[leaf_top + int(tree[leaf_top][0] != 0)] = b

            # store data in tree
            trees[self.L-l] = tree
            self.Server.T[self.L-l].store = [self.encrypt_block(b) for b in tree]

            # set data of position map for next tree
            # data is 2L bits
            data = [(i << self.L) + j for i, j in zip(*[iter(position_map)]*2)]
        self.local_position_map = data
        return self.local_position_map, trees

    def select(self, A, is_even):
        return divmod(A, 1 << self.L)[is_even]

    def update_select(self, A, is_even, pos):
        return (divmod(A, 1 << self.L)[(not is_even)] << is_even*self.L) + (pos << (not is_even)*self.L)

    def extract_bucket(self, i, y, bucket):
        ys = [yi for yi in yi_generator(y, self.L+1)][::-1]
        try:
            block = next(b for b in bucket if b[0] == ys[i])
            if i == self.L:
                return block[1]
            else:
                return self.select(block[1], 1 - ys[i+1] % 2)
        except StopIteration:
            return None

    def access(self, op, y, new_data=None):
        assert 0 < y < self.N + 1

        rand = random.StrongRandom()
        old_positions = [None] * self.L
        new_positions = [rand.getrandbits(l+1) for l in range(self.L)]
        ys = [yi for yi in yi_generator(y, self.L+1)][::-1]

        # read buckets on the path in L rounds communication
        x = self.select(self.local_position_map[ys[0]-1], 1-ys[1]%2)
        for l in range(self.L):
            old_positions[l] = x
            B = [[self.decrypt_block(Eb) for Eb in bucket] for bucket in self.Server.read_path(l+1, x)]
            self.stash[l].extend([block for block in it.chain.from_iterable(B) if block[0] != 0])
            x = self.extract_bucket(l+1, y, self.stash[l])

        # update main data
        data = new_data if op == OP.write else x
        self.stash[self.L-1] = [block if block[0] != y else [block[0], data, new_positions[self.L-1]]
                                for block in self.stash[self.L-1]]

        # update position map data
        for l in range(self.L-1):
            self.stash[l] = [block if block[0] != ys[l+1]
                             else [block[0],
                                   self.update_select(block[1], 1-ys[l+2]%2, new_positions[l+1]),
                                   new_positions[l]]
                             for block in self.stash[l]]

        self.local_position_map[ys[0]-1] = self.update_select(self.local_position_map[ys[0]-1],
                                                              1-ys[1]%2,
                                                              new_positions[0])

        # store blocks in stash
        for l in range(self.L, 0, -1):
            for depth in range(l, -1, -1):
                new_blocks = [b for b in self.stash[l-1]
                              if self.Server.T[self.L-l].path(old_positions[l-1], depth)
                              == self.Server.T[self.L-l].path(b[2], depth)]
                new_blocks = new_blocks[0:min(self.Z, len(new_blocks))]
                self.stash[l-1] = [b for b in self.stash[l-1] if b not in new_blocks]
                self.write_bucket(l, old_positions[l-1], depth, new_blocks)

        # return y == int(x[-1])
        return data

    def write_bucket(self, l, x, depth, blocks):
        new_bucket = blocks + [self.dummy_block] * (self.Z-len(blocks))
        self.Server.T[self.L-l].write_bucket(x, depth, [self.encrypt_block(block) for block in new_bucket])

    def encrypt_block(self, b):
        # return b
        text = json.dumps(b).encode()
        return fo.encrypt(fo.padding(text), self.k)

    def decrypt_block(self, Eb):
        # return Eb
        text = fo.suppress(fo.decrypt(Eb, self.k))
        return json.loads(text.decode())


if __name__ == '__main__':
    N = 8
    s = Server(N)
    A = [str(i+11) for i in range(8)]
    c = Client(s)
    a, t = c.initialize(A)
    ys = [i for i in yi_generator(6, 2+1)][::-1]

    print(c.access(OP.read, 1))
    print(c.access(OP.read, 7))
    print(c.access(OP.read, 3))
    print(c.access(OP.read, 5))
    print(c.access(OP.read, 2))
    print(c.access(OP.read, 6))
    print(c.access(OP.read, 4))
    print(c.access(OP.read, 8))
    print(c.access(OP.write, 3, '3'))
    print(c.access(OP.write, 4, '4'))
    print(c.access(OP.write, 2, '2'))
    print(c.access(OP.write, 8, '8'))
    print(c.access(OP.write, 5, '5'))
    print(c.access(OP.write, 7, '7'))
    print(c.access(OP.write, 1, '1'))
    print(c.access(OP.write, 6, '6'))

    print('r', c.access(OP.read, 3))
    print('r', c.access(OP.read, 5))
    print('r', c.access(OP.read, 2))
    print('r', c.access(OP.read, 8))
    print('r', c.access(OP.read, 1))
    print('r', c.access(OP.read, 4))
    print('r', c.access(OP.read, 7))
    print('r', c.access(OP.read, 6))

    # from functools import reduce
    # from operator import and_
    # print(reduce(and_, [reduce(and_, [c.access(OP.read, i+1) for i in range(N)]) for _ in range(100)]))


