from GarbledCircuit import *

from charm.toolbox.integergroup import IntegerGroup
from charm.toolbox.securerandom import OpenSSLRand
from commitment import Commitment
from PRNG import PRNG
import sys
import operator as op

if __name__ == '__main__':
    # init game
    group = IntegerGroup()
    group.paramgen(1024)

    f = [op.and_, op.xor, op.or_]

    C = Commitment(group)
    pk, sk = C.get_key()

    ssl = OpenSSLRand()

    p1 = {}
    p2 = {}
    p3 = {}

    # Step 1 (1)
    p1["x12"]  = int.from_bytes(ssl.getRandomBits(1), sys.byteorder)
    p1["x13"]  = int.from_bytes(ssl.getRandomBits(1), sys.byteorder)
    p1["x1"]   = p1["x12"] ^ p1["x13"]

    p2["k23"]  = ssl.getRandomBytes(16)
    p3["k32"]  = ssl.getRandomBytes(16)
    p2["k32"]  = p3["k32"]
    p3["k23"]  = p2["k23"]
    p2["k3"]   = p2["k23"] ^ p2["k32"]
    p3["k2"]   = p3["k23"] ^ p3["k32"]

    p2["R3"]   = PRNG(p2["k3"]).generate_random
    p3["R2"]   = PRNG(p3["k2"]).generate_random

    # Step 1 (2)
    p2["x21"]  = int.from_bytes(ssl.getRandomBits(1), sys.byteorder)
    p2["x23"]  = int.from_bytes(ssl.getRandomBits(1), sys.byteorder)
    p2["x2"]   = p2["x21"] ^ p2["x23"]

    p1["k13"]  = ssl.getRandomBytes(16)
    p3["k31"]  = ssl.getRandomBytes(16)
    p1["k31"]  = p3["k31"]
    p3["k13"]  = p1["k13"]
    p1["k3"]   = p1["k13"] ^ p1["k31"]
    p3["k1"]   = p3["k13"] ^ p3["k31"]

    p1["R3"]   = PRNG(p1["k3"]).generate_random
    p3["R1"]   = PRNG(p3["k1"]).generate_random

    # Step 1 (3)
    p3["x31"]  = int.from_bytes(ssl.getRandomBits(1), sys.byteorder)
    p3["x32"]  = int.from_bytes(ssl.getRandomBits(1), sys.byteorder)
    p3["x3"]   = p3["x31"] ^ p3["x32"]

    p1["k12"]  = ssl.getRandomBytes(16)
    p2["k21"]  = ssl.getRandomBytes(16)
    p1["k21"]  = p2["k21"]
    p2["k12"]  = p1["k12"]
    p1["k2"]   = p1["k12"] ^ p1["k21"]
    p2["k1"]   = p2["k12"] ^ p2["k21"]

    p1["R2"]   = PRNG(p1["k2"]).generate_random
    p2["R1"]   = PRNG(p2["k1"]).generate_random

    # Step 2 (1)
    p2["F1e"], p2["F1GC"] = garbling(f, p2["R3"])
    p3["F1e"], p3["F1GC"] = garbling(f, p3["R2"])

    p2["F1ce"] = [( C.commitment(pk, e[0], p2["R3"]),
                    C.commitment(pk, e[1], p2["R3"]) ) for e in p2["F1e"]]
    p3["F1ce"] = [( C.commitment(pk, e[0], p3["R2"]),
                    C.commitment(pk, e[1], p3["R2"]) ) for e in p3["F1e"]]


