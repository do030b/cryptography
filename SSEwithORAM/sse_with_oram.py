# -*- coding: utf-8 -*-
from PathORAM import recursive_path_oram as oram
import time


class Server:
    def __init__(self, num_of_data, num_of_index):
        self.data_oram = oram.Server(num_of_data)
        self.index_oram = oram.Server(num_of_index)


class Client:
    def __init__(self, server, key):
        self.server = server
        self.data_oram = oram.Client(self.server.data_oram, key)
        self.index_oram = oram.Client(self.server.index_oram, key)
        self.num_of_data = None

    def initialize(self, word_list, data_list):
        self.num_of_data = len(data_list)
        index_list = [int(''.join([str(int(w in d)) for d in data_list]), 2) for w in word_list]
        s = time.time()
        self.data_oram.initialize(data_list)
        print(time.time() - s)
        s = time.time()
        self.index_oram.initialize(index_list)
        print(time.time() - s)

    def search(self, word_id):
        index = self.index_oram.access(oram.OP.read, word_id)
        id_list = [i for i, b in enumerate(bin(index)[2:].zfill(self.num_of_data).ljust(self.data_oram.N, '0'), 1)
                   if int(b) == 1]
        return [self.data_oram.access(oram.OP.read, w) for w in id_list]


if __name__ == '__main__':
    import time

    D = ["word1 is here.",
         "i have word2",
         "this is word1",
         "do you have word2 ?",
         "im word1"]

    W = ["word1",
         "word2"]

    Nd = 2**10
    Ni = 2**12

    s = Server(Nd, Ni)
    c = Client(s, b'1234567890123456')
    start_setup = time.time()
    c.initialize(W, D)
    end_setup = time.time()

    print(end_setup - start_setup)
    for _ in range(10):
        for w in W:
            # start_search = time.time()
            print(w, ':', c.search(W.index(w) + 1))
            # end_search = time.time()
            # print(end_search - start_search)
