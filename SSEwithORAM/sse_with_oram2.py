# -*- coding: utf-8 -*-
from PathORAM import recursive_path_oram as oram
from SSEwithORAM.AES_based_CSPRNG import CSPRNG
from SSEwithORAM import file_operation as fo


class Server:
    def __init__(self, num_of_index):
        self.store = None
        self.index_oram = oram.Server(num_of_index)


class Client:
    def __init__(self, server, oram_key, hash_key, data_key, padding_size):
        self.server = server
        self.oram_key = oram_key
        self.hash_key = hash_key
        self.data_key = data_key
        self.index_oram = oram.Client(self.server.index_oram, self.oram_key)
        self.num_of_data = None
        self.hash = lambda x: CSPRNG(self.hash_key, randbits=128).encrypt(x)
        self.padding_size = padding_size

    def initialize(self, word_list, data_list):
        self.num_of_data = len(data_list)

        indexes = {w: [d for d in data_list if w in d] for w in word_list}
        counts = [len(data) for data in indexes.values()]

        self.server.store = [[self.encrypt(d) for d in (data+['0']*self.padding_size)[:self.padding_size]]
                             for data in indexes.values()]

        self.index_oram.initialize(counts)

    def search(self, word_id):
        count = self.index_oram.access(oram.OP.read, word_id)
        return [self.decrypt(c) for c in self.server.store[word_id-1][:count]]

    def encrypt(self, plaintext):
        return fo.encrypt(fo.padding(plaintext.encode()), self.data_key)

    def decrypt(self, ciphertext):
        return fo.suppress(fo.decrypt(ciphertext, self.data_key)).decode()

if __name__ == '__main__':
    import time

    D = ["word1 is here.",
         "i have word2",
         "this is word1",
         "do you have word2 ?",
         "im word1"]

    W = ["word1",
         "word2"]

    Ni = 2**12

    s = Server(Ni)
    c = Client(s, b'1234567890123456', b'1234567890123456', b'1234567890123456', 10)
    start_setup = time.time()
    c.initialize(W, D)
    end_setup = time.time()
    print(end_setup - start_setup)
    for _ in range(10):
        for w in W:
            start_search = time.time()
            print(w, ':', c.search(W.index(w) + 1))
            end_search = time.time()
            print(end_search - start_search)
