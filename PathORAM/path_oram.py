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
        self.position_map = dict()
        self.stash = list()

    def access(self, op, identifier, new_data=None, pos=None):
        try:
            old_position = self.position_map[identifier]
            self.position_map[identifier] = random.randint(0, 2**self.L - 1) if pos is None else pos
        except KeyError:
            self.position_map[identifier] = random.randint(0, 2**self.L - 1) if pos is None else pos
            old_position = self.position_map[identifier]

        for l in range(self.L+1):
            self.stash.extend([b for b in self.Store.read(old_position, l)
                               if b[0] in self.position_map.keys()])

        if op == OP.write:
            self.stash = [b for b in self.stash if b[0] != identifier] + [[identifier, new_data]]

        data = [b for b in self.stash if b[0] == identifier][0]

        for l in range(self.L, -1, -1):
            new_blocks = [b for b in self.stash
                          if self.Store.path(old_position, l) == self.Store.path(self.position_map[b[0]], l)]
            new_blocks = new_blocks[0:min(self.Z, len(new_blocks))]
            self.stash = [b for b in self.stash if b not in new_blocks]
            self.Store.write(old_position, l, new_blocks)

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
