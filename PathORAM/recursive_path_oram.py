# -*- coding: utf-8 -*-
import math
from enum import Enum
from Crypto.Random import random
from SSEwithORAM import file_operation as fo
import itertools as it
import json

OP = Enum('OP', 'read write')


def split_iterable(iterable, based):
    return zip(*[iter(iterable)] * based)


def is_even(number):
    return (number & 1) == 0


class Store:
    def __init__(self, depth, bucket_size=4):
        self.L = depth
        self.Z = bucket_size
        self.total = self.Z * (2 ** (self.L + 1) - 1)
        self.store = [[None] * self.Z for _ in range(2 ** (self.L + 1) - 1)]

    def s(self):
        buckets = [i for i in zip(*[iter(self.store)] * self.Z)]

        return {i: bucket for i, bucket in enumerate(buckets)}

    def update(self, blocks):
        if len(blocks) != self.Z * (2 ** (self.L + 1) - 1):
            print(self.L)
            print(len(blocks))
            raise ValueError
        self.store = blocks

    def path(self, x, l):
        if x > 2 ** self.L - 1 or x < 0 or l > self.L or l < 0:
            raise ValueError
        return (2 ** l) + (x >> (self.L - l)) - 1

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
    def __init__(self, total_num, bucket_size=4):
        self.N = total_num
        self.L = math.ceil(math.log2(self.N)) - 1
        self.Z = bucket_size
        self.T = [Store(depth=self.L - l, bucket_size=self.Z) for l in range(self.L)]

    def read_path(self, l, x):
        return [self.T[self.L - l].read_bucket(x, li) for li in range(l + 1)]


class Client:
    def __init__(self, server, key):
        self.Server = server
        self.N = server.N
        self.Z = server.Z
        self.L = server.L
        self.k = key
        self.local_position_map = []
        self.stash = [[] for _ in range(self.L)]
        self.dummy_block = [0, 0, 0]
        self.err = None

    def merge_positions(self, pos_a, pos_b):
        return (pos_a << self.L) + pos_b

    def split_positions(self, merged_positions):
        return divmod(merged_positions, 1 << self.L)

    def convert_position_map_to_storable(self, position_map):
        return [self.merge_positions(i, j)
                for i, j in split_iterable(position_map, based=2)]

    def count_total_blocks(self, l):
        return self.Z * (2 ** (l + 1) - 1)

    def initialize(self, initial_data):
        if len(initial_data) > self.N:
            raise ValueError('data size should not be larger than store size')
        rand = random.StrongRandom()
        data = initial_data
        for l in range(self.L, 0, -1):
            # set random position map
            # position is L bits
            position_map = [i for i in range(2 ** l)] * 2
            rand.shuffle(position_map)

            # set real data form of blocks (id, data, position)
            # and sorted by position
            real_blocks = ((i, data_i, pos_i)
                           for i, (data_i, pos_i)
                           in enumerate(zip(data, position_map), 1))

            # padding by dummy blocks
            total_blocks = self.count_total_blocks(l)
            # to do: convert to Store
            tree = [self.dummy_block for _ in range(total_blocks)]

            for b in real_blocks:
                leaf_top = (2 ** l - 1 + b[2]) * self.Z
                tree[leaf_top + int(tree[leaf_top][0] != 0)] = b

            # store data in tree
            self.Server.T[self.L - l].store = [self.encrypt_block(b)
                                               for b in tree]

            # set data of position map for next tree
            # data is 2L bits
            data = self.convert_position_map_to_storable(position_map)

        self.local_position_map = data
        return self.local_position_map

    @staticmethod
    def get_id_ist_for_select(block_id, depth):
        def generate_parameters(y, l):
            yi = y
            for _ in range(l):
                yield yi
                yi = math.ceil(yi / 2)

        return list(generate_parameters(block_id, depth))[::-1]

    def select(self, merged_position, even):
        return self.split_positions(merged_position)[even]

    def select_update(self, merged_position, even, new_position):
        not_selected_position = self.select(merged_position, not even)
        head, tail = (not_selected_position, new_position) if even \
            else (new_position, not_selected_position)

        return self.merge_positions(head, tail)

    def extract_bucket(self, i, y, bucket):
        ys = self.get_id_ist_for_select(y, self.L + 1)
        try:
            block = next(b for b in bucket if b[0] == ys[i])
            if i == self.L:
                return block[1]
            else:
                return self.select(block[1], 1 - ys[i + 1] % 2)
        except StopIteration:
            return None

    @staticmethod
    def is_dummy_block(block):
        return block[0] == 0

    def access(self, op, target_id, new_data=None):
        assert 0 < target_id < self.N + 1

        rand = random.StrongRandom()
        old_positions = [None] * self.L
        new_positions = [rand.getrandbits(l + 1) for l in range(self.L)]
        id_list = self.get_id_ist_for_select(target_id, self.L + 1)

        # read buckets on the path in L rounds communication
        x = self.select(self.local_position_map[id_list[0] - 1],
                        is_even(id_list[1]))
        for l in range(self.L):
            old_positions[l] = x
            blocks = ((self.decrypt_block(encrypted_block)
                       for encrypted_block in bucket)
                      for bucket in self.Server.read_path(l + 1, x))
            self.stash[l].extend([block for block in it.chain.from_iterable(blocks)
                                  if not self.is_dummy_block(block)])
            x = self.extract_bucket(l + 1, target_id, self.stash[l])

        # update main data
        data = new_data if op == OP.write else x
        self.stash[self.L - 1] = [block if block[0] != target_id
                                  else [block[0], data, new_positions[self.L - 1]]
                                  for block in self.stash[self.L - 1]]

        # update position map data
        for l in range(self.L - 1):
            self.stash[l] = [block if block[0] != id_list[l + 1]
                             else [block[0],
                                   self.select_update(block[1],
                                                      is_even(id_list[l + 2]),
                                                      new_positions[l + 1]),
                                   new_positions[l]]
                             for block in self.stash[l]]

        self.local_position_map[id_list[0] - 1] = \
            self.select_update(self.local_position_map[id_list[0] - 1],
                               is_even(id_list[1]),
                               new_positions[0])

        # store blocks in stash
        for l in range(self.L, 0, -1):
            for depth in range(l, -1, -1):
                new_blocks = [b for b in self.stash[l - 1]
                              if self.Server.T[self.L - l].path(old_positions[l - 1], depth)
                              == self.Server.T[self.L - l].path(b[2], depth)]
                new_blocks = new_blocks[0:min(self.Z, len(new_blocks))]
                self.stash[l - 1] = [b for b in self.stash[l - 1] if b not in new_blocks]
                self.write_bucket(l, old_positions[l - 1], depth, new_blocks)

        return data

    def write_bucket(self, l, x, depth, blocks):
        new_bucket = blocks + [self.dummy_block] * (self.Z - len(blocks))
        self.Server.T[self.L - l].write_bucket(x,
                                               depth,
                                               [self.encrypt_block(block)
                                                for block in new_bucket])

    def encrypt_block(self, b):
        # return b
        text = json.dumps(b).encode()
        return fo.encrypt(fo.padding(text), self.k)

    def decrypt_block(self, encrypted_block):
        # return Eb
        text = fo.suppress(fo.decrypt(encrypted_block, self.k))
        return json.loads(text.decode())


if __name__ == '__main__':
    N = 8
    s = Server(N)
    A = [str(i + 11) for i in range(8)]
    c = Client(s, b'1234567890123456')
    a, t = c.initialize(A)

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
