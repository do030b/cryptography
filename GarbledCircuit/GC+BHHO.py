# -*- coding: utf-8 -*-
import operator as op
from GarbledCircuit import *
from bhho import BHHO
from charm.toolbox.integergroup import IntegerGroup


if __name__ == '__main__':
    f1 = (4, 1, 3, {5: 1, 6: 3, 7: 5}, {5: 2, 6: 4, 7: 6}, [op.and_, op.xor, op.or_])
    f2 = (4, 1, 3, {5: 1, 6: 5, 7: 6}, {5: 2, 6: 3, 7: 4}, [op.and_, op.xor, op.or_])
    s = [1, 0, 1, 0]

    e, F = garble_circuit(f1)

    y = evaluate_circuit(f1, s)
    X = encode(e, [y, 0, 0, 0])

    group = IntegerGroup()
    group.paramgen(512)
    r = group.random()
    g1 = group.randomGen()

    k  = [group.random() for _ in range(200)]
    bhho = BHHO(group, k, r)

    keys = bhho.generate_key(g1)
