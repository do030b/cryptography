# -*- coding: utf-8 -*-
import math
from enum import Enum
import random
from PathORAM.aes_ctr import AESCTR

OP = Enum('OP', 'read write')


class Server:
    def __init__(self, N, Z):
        self.N = N
        self.L = math.ceil(math.log2(N)) - 1
        self.Z = Z
        self.total = self.Z*(2**(self.L+1)-1)
        self.store = None

    def initialize(self, blocks):
        self.store = blocks

    def __repr__(self):
        repr_str = ''
        for i in range(2 ** (self.L + 1) - 1):
            l = math.floor(math.log2(i + 1))
            repr_str += 'node' + str([l, i-(2**l)+1]) + ':\n\t' + '\n\t'.join(map(str, self.store[i * self.Z: (i + 1) * self.Z]))
            repr_str += '\n'
        return repr_str

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
        self.position_map = dict()
        self.stash = list()
        self.dummy_block = [b"0", b"0"]
        self.initialize()

    def encrypt_block(self, block):
        return [self.cipher.encrypt(v) for v in block]

    def decrypt_block(self, block):
        return [self.cipher.decrypt(v) for v in block]

    def initialize(self):
        self.Server.initialize([self.encrypt_block(self.dummy_block)
                                for _ in range(self.Server.total)])

    def read_bucket(self, x, l):
        return [self.decrypt_block(block) for block in self.Server.read_bucket(x, l)]

    def write_bucket(self, x, l, blocks):
        new_bucket = blocks + [self.dummy_block] * (self.Z-len(blocks))
        self.Server.write_bucket(x, l, [self.encrypt_block(block) for block in new_bucket])

    def access(self, op, identifier, new_data=None):
        try:
            old_position = self.position_map[identifier]
        except KeyError:
            old_position = random.randint(0, 2**self.L - 1)
        self.position_map[identifier] = random.randint(0, 2**self.L - 1)

        for l in range(self.L+1):
            self.stash.extend([b for b in self.read_bucket(old_position, l)
                               if b[0] in self.position_map.keys()])

        if op == OP.write:
            self.stash = [b for b in self.stash if b[0] != identifier] + [[identifier, new_data]]

        data = [b[1] for b in self.stash if b[0] == identifier][0]

        for l in range(self.L, -1, -1):
            new_blocks = [b for b in self.stash
                          if self.Server.path(old_position, l) == self.Server.path(self.position_map[b[0]], l)]
            new_blocks = new_blocks[0:min(self.Z, len(new_blocks))]
            self.stash = [b for b in self.stash if b not in new_blocks]
            self.write_bucket(old_position, l, new_blocks)

        return data


if __name__ == '__main__':
    N = 8
    Z = 4
    L = math.ceil(math.log2(4)) - 1,
    s = Server(N, Z)
    p = Client(s)
    p.access(OP.write, b"hello1", new_data=b"hello_world 1")
    p.access(OP.write, b"hello2", new_data=b"hello_world 2")
    p.access(OP.write, b"hello3", new_data=b"hello_world 3")
    p.access(OP.write, b"hello4", new_data=b"hello_world 4")
    print(p.Server)
    print(p.position_map)
    print(p.access(OP.read, b"hello1"))
    print(p.access(OP.read, b"hello2"))
    print(p.access(OP.read, b"hello3"))
    print(p.access(OP.read, b"hello4"))
    print(p.access(OP.read, b"hello1"))
    print(p.access(OP.read, b"hello2"))
    print(p.access(OP.read, b"hello3"))
    print(p.access(OP.read, b"hello4"))
    p.access(OP.write, b"hello1", new_data=b"new 1")
    p.access(OP.write, b"hello4", new_data=b"new 4")
    print(p.access(OP.read, b"hello1"))
    print(p.access(OP.read, b"hello2"))
    print(p.access(OP.read, b"hello3"))
    print(p.access(OP.read, b"hello4"))
    print(p.access(OP.read, b"hello1"))
    print(p.access(OP.read, b"hello2"))
    print(p.access(OP.read, b"hello3"))
    print(p.access(OP.read, b"hello4"))
