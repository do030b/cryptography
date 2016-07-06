
from charm.toolbox.integergroup import IntegerGroup
import hashlib


class Commitment:
    """
        example:
            >>> group = IntegerGroup()
            >>> group.paramgen(1024)
            >>> Commitment(group)
    """
    def __init__(self, paramgened_integer_group):
        self.group = paramgened_integer_group
        self.pk, self.sk = self.__generate_key()
        self.__commitments = {}

    def __generate_key(self):
        g = self.group.randomGen()
        x = self.group.random()
        return (g, g**x), x

    def get_key(self):
        return self.pk, self.sk

    def commitment(self, pk, m, random_func=None):
        if random_func is None:
            r = self.group.random()
        else:
            r = random_func()

        c = (pk[0]**m) * (pk[1]**r)
        hashc = hashlib.sha1(repr(c).encode('utf-8')).hexdigest()
        if (hashc in self.__commitments.keys()) and (self.__commitments[hashc] != {"m": m, "r": r}):
            print("collision!")
            exit(1)

        self.__commitments[hashc] = {"m": m, "r": r}
        return c

    def decommitment(self, c):
        try:
            return self.__commitments[hashlib.sha1(repr(c).encode('utf-8')).hexdigest()]
        except:
            print("reject")
            exit(1)

