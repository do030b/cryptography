# coding=utf-8
from charm.toolbox.pairinggroup import PairingGroup, ZR, G1, G2, pair
from charm.toolbox.matrixops import *
from my_crypto_toolbox import *


"""
Kiltz_and_Wee_1
----------------------------------------------------
CRS:           ([(1,t)]1, [P]1, [C]2, [(1,a)]2)
                   | P=(1,t)*K, C=K*(1,a)t
Instance:      [Y]1 = [r*(1,t)]1
NIZK_proof:    [PI]1 = [r*P]1
verification:  e([PI]1, [(1,a)]2) == e([Y]1, [C]2)
----------------------------------------------------
public data:   CRS, Instance
secret data:   r
random data:   r, t, a, K, P, C, CRS
"""


def generate_crs(group):
    # generate pairing elements
    g1 = group.random(G1)
    g2 = group.random(G2)

    # generate random elements
    matrix_1t = [[1, group.random(ZR)]]
    matrix_1a = [[1, group.random(ZR)]]
    matrix_k  = generate_random_matrix(group, 2, 2)

    # calculate matrix P, C
    matrix_p = MatrixMulGroups(matrix_1t, matrix_k)
    matrix_c = MatrixTransGroups(MatrixMulGroups(matrix_k, MatrixTransGroups(matrix_1a)))

    return (  # CRS=([(1,t)]1, [P]1, [C]2, [(1,a)]2)
        base_pow_expmatrix(g1, matrix_1t),
        base_pow_expmatrix(g1, matrix_p),
        base_pow_expmatrix(g2, matrix_c),
        base_pow_expmatrix(g2, matrix_1a)
    ), matrix_k, g1, matrix_1t[0][1]


def generate_pi(crs, r):
    # [P]1 = [(p0, p1)]1 -> [(rp0, rp1)]1 = [(pi0, pi1)]1 = [PI]1
    return basematrix_pow_exp(crs[1], r)


def generate_instance(crs, r):
    # [(1, t)]1 -> [(r, rt)]1 = [Y]1
    return basematrix_pow_exp(crs[0], r)

def check_certificate(crs, y, pi):
    # e([PI]1, [(1,a)]2) == e([Y]1, [C]2)
    # pi=[PI]1, crs[3]=[(1,a)]2, y=[Y]1, crs[2]=[C]2
    return pairing_matrix(pi, crs[3]) == pairing_matrix(y, crs[2])


if __name__ == '__main__':
    # 'MNT159' represents an asymmetric curve with 159-bit base field
    group = PairingGroup('MNT159')

    # Third-Party-Section
    crs, k, g1, t = generate_crs(group)

    # Certification-Section
    r  = group.random(ZR)
    y  = generate_instance(crs, r)

    pi = generate_pi(crs, r)

    print("[r*P]1: ", pi)
    print("[Y*K]1: ", base_pow_expmatrix(g1, MatrixMulGroups([[r, r*t]], k)))

    # Verification-Section
    print("accept" if check_certificate(crs, y, pi) else "reject")
