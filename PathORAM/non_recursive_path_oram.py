# -*- coding: utf-8 -*-
import math
from enum import Enum
import random
from PathORAM.aes_ctr import AESCTR
from collections.abc import Sequence

OP = Enum('OP', 'read write')


def split_iterable(iterable, based):
    return zip(*[iter(iterable)] * based)


class Server:
    def __init__(self, N, Z):
        self.N = N
        self.L = math.ceil(math.log2(N)) - 1
        self.Z = Z
        self.T = Store(self.N, self.Z)


class Bucket(Sequence):
    __slots__ = ['bucket']

    def __init__(self, bucket_size, default=None):
        self.bucket = [default for _ in range(bucket_size)]

    def __getitem__(self, index):
        return self.bucket[index]

    def __setitem__(self, key, value):
        self.bucket[key] = value

    def __len__(self):
        return len(self.bucket)

    def __repr__(self):
        return str(self.bucket)


class Node:
    __slots__ = ['value', 'parent', 'left', 'right']

    def __init__(self, value, parent=None, left=None, right=None):
        self.value  = value
        self.parent = parent
        self.left   = left
        self.right  = right

    def connect_left(self, left_child):
        self.left = left_child
        left_child.parent = self

    def connect_right(self, right_child):
        self.right = right_child
        right_child.parent = self


class Tree(Sequence):

    def __init__(self, N, Z):
        self.tree = [Bucket(Z) for _ in range((2**(L+1)-1))]
        self.N = N
        self.Z = Z
        self.L = math.ceil(math.log2(N)) - 1

    def __getitem__(self, index):
        return self.tree[index]

    def __setitem__(self, index, bucket):
        assert len(bucket) == self.Z
        for i, block in enumerate(bucket):
            self.tree[index][i] = block

    def __len__(self):
        return len(self.tree)

    def initialize(self, blocks):
        assert len(blocks) & 3  == 0
        for i, bucket in enumerate(split_iterable(blocks, based=self.Z)):
            self.tree[i] = bucket


class Store:
    def __init__(self, N, Z, blocks=None):
        self.N = N
        self.L = math.ceil(math.log2(N)) - 1
        self.Z = Z
        self.total = self.Z*(2**(self.L+1)-1)
        self.store = [[None]*self.Z]*(2**(self.L+1)-1) if blocks is None else blocks

    def __getitem__(self, index):
        return self.store[index]

    def initialize(self, blocks):
        self.store = blocks

    def path(self, x, l):
        index = 2 ** self.L + x
        for _ in range(self.L - l):
            index >>= 1
        return index - 1

    def read_bucket(self, x, l):
        top = self.path(x, l) * self.Z
        bottom = top + self.Z
        return self.store[top:bottom]

    def write_bucket(self, x, l, new_bucket):
        top = self.path(x, l) * self.Z
        for n, block in enumerate(new_bucket):
            self.store[top + n] = block


class Client:
    def __init__(self, server):
        self.Server = server
        self.N = server.N
        self.Z = server.Z
        self.L = server.L
        self.cipher = AESCTR()
        self.position_map = [random.randint(0, 2**self.L - 1) for _ in range(2**(self.L+1))]
        self.stash = list()
        self.dummy_block = [0, 0]
        self.initialize()

    def encrypt_block(self, block):
        return [self.cipher.encrypt(bin(v)[2:].encode().zfill(self.L+1)) for v in block ]

    def decrypt_block(self, block):
        return [int(self.cipher.decrypt(v), 2) for v in block ]

    def initialize(self):
        self.Server.T.initialize([self.encrypt_block(self.dummy_block)
                                  for _ in range(self.Server.T.total)])

    def read_bucket(self, x, l):
        return [self.decrypt_block(block) for block in self.Server.T.read_bucket(x, l)]

    def write_bucket(self, x, l, blocks):
        new_bucket = blocks + [self.dummy_block] * (self.Z-len(blocks))
        self.Server.T.write_bucket(x, l, [self.encrypt_block(block) for block in new_bucket])

    def access(self, op, data_id, new_data=None):
        old_position = self.position_map[data_id]
        self.position_map[data_id] = random.randint(0, 2**self.L - 1)

        for l in range(self.L+1):
            self.stash.extend([b for b in self.read_bucket(old_position, l)
                               if b[0] in range(1, 2**self.L+1)])

        if op == OP.write:
            self.stash = [b for b in self.stash if b[0] != data_id] + [[data_id, int.from_bytes(new_data, 'big')]]

        data = [b[1] for b in self.stash if b[0] == data_id][0] if op == OP.read else int.from_bytes(new_data, 'big')

        for l in range(self.L, -1, -1):
            new_blocks = [b for b in self.stash
                          if self.Server.T.path(old_position, l) == self.Server.T.path(self.position_map[b[0]], l)]
            new_blocks = new_blocks[0:min(self.Z, len(new_blocks))]
            self.stash = [b for b in self.stash if b not in new_blocks]
            self.write_bucket(old_position, l, new_blocks)

        return data.to_bytes(math.ceil((len(bin(data))-2)/8), 'big')


if __name__ == '__main__':
    N = 9
    Z = 4
    L = math.ceil(math.log2(N)) - 1
    s = Server(N, Z)
    p = Client(s)
    print(p.access(OP.write, 1, new_data=b"hello_world 1"))
    print(p.access(OP.write, 2, new_data=b"hello_world 2"))
    print(p.access(OP.write, 3, new_data=b"hello_world 3"))
    print(p.access(OP.write, 4, new_data=b"hello_world 4"))
    print(p.position_map)
    print(p.access(OP.read, 1))
    print(p.access(OP.read, 2))
    print(p.access(OP.read, 3))
    print(p.access(OP.read, 4))
    print(p.access(OP.read, 1))
    print(p.access(OP.read, 2))
    print(p.access(OP.read, 3))
    print(p.access(OP.read, 4))
    p.access(OP.write, 1, new_data=b"new 1")
    p.access(OP.write, 4, new_data=b"new 4")
    print(p.access(OP.read, 1))
    print(p.access(OP.read, 2))
    print(p.access(OP.read, 3))
    print(p.access(OP.read, 4))
    print(p.access(OP.read, 1))
    print(p.access(OP.read, 2))
    print(p.access(OP.read, 3))
    print(p.access(OP.read, 4))
