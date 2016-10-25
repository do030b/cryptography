# -*- coding: utf-8 -*-
from PathORAM import recursive_path_oram as oram


class Server:
    def __init__(self, num_of_data, num_of_index):
        self.data_oram = oram.Server(num_of_data)
        self.index_oram = oram.Server(num_of_index)


class Client:
    def __init__(self, server):
        self.server = server
        self.data_oram = oram.Client(self.server.data_oram)
        self.index_oram = oram.Client(self.server.index_oram)

    def initialize(self, index_list, data_list):
        self.data_oram.initialize(data_list)
        self.index_oram.initialize(index_list)

    def search(self, word_id):
        index = self.index_oram.access(oram.OP.read, word_id)
        id_list = [i for i, b in enumerate(bin(index)[2:].zfill(index_bit), 1) if int(b) == 1]
        return [self.data_oram.access(oram.OP.read, w) for w in id_list]


if __name__ == '__main__':

    D = ["word1 is here.",
         "i have word2",
         "this is word1",
         "do you have word2 ?",
         "im word1"]

    W = ["word1",
         "word2"]

    Index = [int(''.join([str(int(w in d)) for d in D]), 2) for w in W]
    index_bit = len(D)
    Nd = Ni = 8

    s = Server(Nd, Ni)
    c = Client(s)
    c.initialize(Index, D)

    for w in W:
        print(w, ':', c.search(W.index(w) + 1))
