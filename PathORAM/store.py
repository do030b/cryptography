from Crypto import Random
from PathORAM.aes_ctr import AESCTR


class Store:
    def __init__(self, L, Z):
        self.L = L
        self.Z = Z
        self.store = None

    def path(self, x, l):
        pass

    def read(self, x, l):
        pass

    def wirte(self, x, l, block):
        pass


class ListStore(Store):
    def __init__(self, L, Z):
        super().__init__(L, Z)
        self.random_generator = Random.new()
        self.cipher = AESCTR()
        self.dummy_block = [0, 0]
        self.store = [self.cipher.encrypt_block(self.dummy_block)
                      for _ in range((2 ** (self.L + 1) - 1) * self.Z)]

    def __repr__(self):
        repr_str = ''
        for i in range(2**(self.L + 1) - 1):
            repr_str += 'node[' + str(i) + ']:\n' + '\n'.join(map(str, self.store[i*self.Z: (i+1)*self.Z]))
            repr_str += '\n'
        return repr_str

    def path(self, x, l):
        index = 2 ** self.L + x
        for _ in range(self.L - l):
            index >>= 1
        return index - 1

    def read(self, x, l):
        top = self.path(x, l) * self.Z
        bottom = top + self.Z
        return [self.cipher.decrypt_block(block) for block in self.store[top:bottom]]

    def write(self, x, l, blocks):
        top = self.path(x, l) * self.Z
        new_bucket = (blocks + self.dummy_block * self.Z)[:self.Z]

        for n, block in enumerate(new_bucket):
            self.store[top + n] = self.cipher.encrypt_block(block)
