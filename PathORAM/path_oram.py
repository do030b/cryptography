# -*- coding: utf-8 -*-
import math
from enum import Enum
import random
from PathORAM.store import ListStore

OP = Enum('OP', 'read write')


class PathORAM:
    def __init__(self, total, bucket_size=4):
        self.N = total
        self.Z = bucket_size
        self.L = math.ceil(math.log2(self.N)) - 1

        self.Store = ListStore(self.L, self.Z)
        self.leaves = 2 ** self.L

        self.position_map = dict()
        self.stash = list()

    def access(self, op, identifier, new_data=None, pos=None):
        if identifier in self.position_map.keys():
            old_position = self.position_map[identifier]
            self.position_map[identifier] = random.randint(0, 2**self.L - 1) if pos is None else pos
        else:
            self.position_map[identifier] = random.randint(0, 2**self.L - 1) if pos is None else pos
            old_position = self.position_map[identifier]

        for l in range(self.L+1):
            for block in self.Store.read(old_position, l):
                if block[0] in self.position_map.keys():
                    self.stash.append(block)

        data = None
        for i, d in self.stash:
            if i == identifier:
                data = d

        if op == OP.write:
            self.stash = [[i, d] for i, d in self.stash if i != identifier]
            self.stash.append([identifier, new_data])

        for l in range(self.L, -1, -1):
            s = list()
            for i, d in self.stash:
                if self.Store.path(old_position, l) == self.Store.path(self.position_map[i], l):
                    s.append([i, d])
            if len(s) > self.Z:
                s = s[0:self.Z]
            s_names = [m for m, n in s]
            self.stash = [[p, q] for p, q in self.stash if p not in s_names]
            self.Store.write(old_position, l, s)

        return data


if __name__ == '__main__':
    p = PathORAM(4)
    p.access(OP.write, "hello1", new_data="hello_world 1")
    p.access(OP.write, "hello2", new_data="hello_world 2")
    p.access(OP.write, "hello3", new_data="hello_world 3")
    p.access(OP.write, "hello4", new_data="hello_world 4")
    print(p.Store)
    print(p.position_map)
    print(p.access(OP.read, "hello1"))
    print(p.access(OP.read, "hello2"))
    print(p.access(OP.read, "hello3"))
    print(p.access(OP.read, "hello4"))
    print(p.access(OP.read, "hello1"))
    print(p.access(OP.read, "hello2"))
    print(p.access(OP.read, "hello3"))
    print(p.access(OP.read, "hello4"))
    p.access(OP.write, "hello1", new_data="new 1")
    p.access(OP.write, "hello4", new_data="new 4")
    print(p.access(OP.read, "hello1"))
    print(p.access(OP.read, "hello2"))
    print(p.access(OP.read, "hello3"))
    print(p.access(OP.read, "hello4"))
    print(p.access(OP.read, "hello1"))
    print(p.access(OP.read, "hello2"))
    print(p.access(OP.read, "hello3"))
    print(p.access(OP.read, "hello4"))
