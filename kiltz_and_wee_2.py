# coding=utf-8
from charm.toolbox.pairinggroup import PairingGroup, ZR, G1, G2, pair
from charm.toolbox.matrixops import *
from my_crypto_toolbox import *

def generate_crs(group, g1, g2, t):
    # generate pairing elements
    # g1 = group.random(G1)

    # generate random elements
    matrix_1t = [[1, t]]
    matrix_1a = [[1, group.random(ZR)]]
    matrix_k1 = generate_random_matrix(group, 2, 2)
    matrix_k2 = generate_random_matrix(group, 2, 2)

    # calculate matrix P, C
    matrix_p1 = MatrixMulGroups(matrix_1t, matrix_k1)
    matrix_p2 = MatrixMulGroups(matrix_1t, matrix_k2)
    matrix_c1 = MatrixTransGroups(MatrixMulGroups(matrix_k1, MatrixTransGroups(matrix_1a)))
    matrix_c2 = MatrixTransGroups(MatrixMulGroups(matrix_k2, MatrixTransGroups(matrix_1a)))

    return (  # CRS=([(1,t)]1, [P1]1, [P2]1, [C1]2, [C2]2, [(1,a)]2)
        base_pow_expmatrix(g1, matrix_1t),
        base_pow_expmatrix(g1, matrix_p1),
        base_pow_expmatrix(g1, matrix_p2),
        base_pow_expmatrix(g2, matrix_c1),
        base_pow_expmatrix(g2, matrix_c2),
        base_pow_expmatrix(g2, matrix_1a)
    )

def generate_pi(group, crs, instance, r):
    return hadamard_product(
        basematrix_pow_exp(crs[1], r),
        basematrix_pow_exp(crs[2], r * group.hash(instance[0], ZR))
    )

def generate_instance(crs, r):
    # [Y]1 = [r(1, t)]1
    # crs[0] = [(1, t)]1
    return basematrix_pow_exp(crs[0], r)

def check_certificate(group, crs, pi, instance, label=None):
    # crs[3]=[C1]2, crs[4]=[C2]2
    # [C]2 = [(C1+a*C2)]2 = (g2**C1) * (g2**C2)**a
    if label is None:
        hashed_instance =  group.hash(instance[0], ZR)
    else:
        labeled_instance = [label] + instance[0]
        hashed_instance  =  group.hash(labeled_instance, ZR)

    c = hadamard_product(crs[3], basematrix_pow_exp(crs[4], hashed_instance))
    # pi=[PI]1, crs[5]=[(1,a)]2, y=[Y]1, c=[C]2
    # print(pairing_matrix(pi, crs[5]))
    # print(pairing_matrix(instance, c))
    return pairing_matrix(pi, crs[5]) == pairing_matrix(instance, c)


if __name__ == '__main__':
    # 'MNT159' represents an asymmetric curve with 159-bit base field
    group = PairingGroup('MNT159')
    g1 = group.random(G1)
    g2 = group.random(G2)
    t  = group.random(ZR)

    # Third-Party-Section
    crs   = generate_crs(group, g1, g2, t)

    # Certification-Section
    r     = group.random(ZR)
    y     = generate_instance(crs, r)
    alpha = group.hash(y[0], ZR)
    pi    = generate_pi(group, crs, y, r)

    # Verification-Section
    print("accept" if check_certificate(group, crs, pi, y) else "reject")

