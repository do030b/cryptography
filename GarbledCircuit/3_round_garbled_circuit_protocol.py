# -*- coding: utf-8 -*-
from charm.toolbox.integergroup import IntegerGroup
from charm.toolbox.securerandom import OpenSSLRand
from garbled_circuit import *
from commitment import Commitment
from PRNG import PRNG
import sys
import operator as op
from functools import reduce


if __name__ == '__main__':
    # init game
    group = IntegerGroup()
    group.paramgen(1024)

    f = (4, 1, 3, {5: 1, 6: 3, 7: 5}, {5: 2, 6: 4, 7: 6}, [op.and_, op.xor, op.or_])

    C = Commitment(group)
    pk, sk = C.get_key()

    ssl = OpenSSLRand()

    p1 = dict()
    p2 = dict()
    p3 = dict()

    # Step 1
    p1["x1"]  = int.from_bytes(ssl.getRandomBits(1), sys.byteorder)
    p2["x2"]  = int.from_bytes(ssl.getRandomBits(1), sys.byteorder)
    p3["x3"]  = int.from_bytes(ssl.getRandomBits(1), sys.byteorder)
    p3["x4"]  = int.from_bytes(ssl.getRandomBits(1), sys.byteorder)
    p3["x3*"] = p3["x3"] ^ p3["x4"]

    p1["x3"]  = p3["x3"]
    p2["x4"]  = p3["x4"]

    # Step 2
    p1["k1"]  = ssl.getRandomBytes(16)
    p2["k2"]  = ssl.getRandomBytes(16)
    p1["k2"]  = p2["k2"]
    p2["k1"]  = p1["k1"]
    p1["k"]   = p1["k1"] ^ p1["k1"]
    p2["k"]   = p2["k1"] ^ p2["k1"]

    p1["R"]   = PRNG(p1["k"]).generate_random
    p2["R"]   = PRNG(p2["k"]).generate_random

    p1["e"], p1["F"] = garble_circuit(f, p1["R"])
    p2["e"], p2["F"] = garble_circuit(f, p2["R"])

    p1["ce"] = [( C.commitment(pk, e[0], p1["R"]),
                  C.commitment(pk, e[1], p1["R"]) ) for e in p1["e"]]
    p2["ce"] = [( C.commitment(pk, e[0], p2["R"]),
                  C.commitment(pk, e[1], p2["R"]) ) for e in p2["e"]]

    # Step 3
    p3["F1"] = p1["F"]
    p3["F2"] = p2["F"]
    p3["ce1"] = p1["ce"]
    p3["ce2"] = p2["ce"]

    if (p3["F1"] != p3["F2"]) or (p3["ce1"] != p3["ce2"]):
        print("abort!")
        print(p3["F1"])
        print(p3["F2"])
        print(p3["ce1"])
        print(p3["ce2"])
        exit(1)

    p3["de"] = [ C.decommitment(p1["ce"][0][p1["x1"]]),
                 C.decommitment(p2["ce"][1][p2["x2"]]),
                 C.decommitment(p1["ce"][2][p1["x3"]]),
                 C.decommitment(p2["ce"][3][p2["x4"]]) ]

    check_decommitments = reduce(op.and_, [((pk[0]**d["m"] * pk[1]**d["r"]) in p3["ce1"][i])
                                           for i, d in enumerate(p3["de"])])
    if check_decommitments is False:
        print("reject decommitments")
        exit(1)

    p3["X"] = [d["m"] for d in p3["de"]]

    # Check
    lhs = evaluate_circuit(f, [p1["x1"], p2["x2"], p3["x3"], p3["x4"]])
    rhs = evaluate_garbled_circuit(p3["F1"], p3["X"])

    print("result: ", rhs)
    if rhs == lhs:
        print("marvelous!!")
