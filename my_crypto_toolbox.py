# coding=utf-8
from charm.toolbox.pairinggroup import PairingGroup, ZR, G1, G2, pair
from functools import reduce


def int_to_zr(group, num):
    t = group.random(ZR)
    return (num * t) / t


def intlist_to_zrlist(group, num):
    t = group.random(ZR)
    return [(n * t) / t for n in num]


def generate_random_matrix(group, row, column, gtype=ZR):
    return [[group.random(gtype) for _ in range(column)] for _ in range(row)]


def base_pow_expmatrix(base, expmatrix):
    # example:
    #   [a, b]1 -> [g1**a, g1**b]
    return [[base**exp for exp in row] for row in expmatrix]


def basematrix_pow_exp(basematrix, exp):
    return [[base**exp for base in row] for row in basematrix]


def matrix_mul(matrix_a, matrix_b):
    return [reduce(lambda a, b: a + b, [ca * cb for ca, cb in zip(ra, rb)])
            for ra, rb in zip(matrix_a, matrix_b)]


def hadamard_product(matrix_a, matrix_b):
    return [[ca * cb for ca, cb in zip(ra, rb)] for ra, rb in zip(matrix_a, matrix_b)]


def pairing_matrix(lmatrix, rmatrix):
    return [reduce(lambda a, b: a*b, [pair(l,r) for l, r in zip(lrow, rrow)])
                for lrow, rrow in zip(lmatrix, rmatrix)]


