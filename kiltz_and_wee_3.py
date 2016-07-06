# coding=utf-8
from charm.toolbox.pairinggroup import PairingGroup, ZR, G1, G2, pair
from charm.toolbox.matrixops import *
from my_crypto_toolbox import *


def generate_crs(group, g1, g2, matrix_m=None):
    # generate random elements
    matrix_k  = generate_random_matrix(group, 1, 3)

    if matrix_m is None:
        matrix_m  = generate_random_matrix(group, 2, 3)
        # matrix_m  = [[1, 0, group.random(ZR)],
        #              [0, 1, group.random(ZR)]]

    # calculate matrix P
    matrix_p  = MatrixTransGroups(MatrixMulGroups(matrix_m, MatrixTransGroups(matrix_k)))

    return (
        (
            base_pow_expmatrix(g1, matrix_m),
            base_pow_expmatrix(g1, matrix_p),
            base_pow_expmatrix(g2, matrix_k),
        )
    )


def generate_pi(crs, r):
    return [[(crs[1][0][0]**r[0]) * (crs[1][0][1]**r[1])]]


def generate_instance(m, r):
    return [[i**r[0] * j**r[1] for i, j in zip(m[0], m[1])]]


def check_certificate(crs, y, pi, g2):
    return pairing_matrix(pi, [[g2]]) == pairing_matrix(y, crs[2])


if __name__ == '__main__':
    # 'MNT159' represents an asymmetric curve with 159-bit base field
    group = PairingGroup('MNT159')
    g1    = group.random(G1)
    g2    = group.random(G2)

    # Third-Party-Section
    crs   = generate_crs(group, g1, g2)

    # Certification-Section
    r    = group.random(ZR, 2)
    y    = generate_instance(crs[0], r)
    pi   = generate_pi(crs, r)

    # Verification-Section
    print("accept" if check_certificate(crs, y, pi, g2) else "reject")
