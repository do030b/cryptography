# coding=utf-8
from charm.toolbox.pairinggroup import PairingGroup, ZR, G1, pair


def check_theorem13(p, q, a, b):
    return pair(p, a*q+b*q) == pair(p, a*q)*pair(p, b*q) and \
           pair(a*p+b*p, q) == pair(a*p, q)*pair(b*p, q)


if __name__ == '__main__':
    group = PairingGroup('SS512')
    gp = group.random(G1)
    gq = group.random(G1)
    ga = group.random(ZR)
    gb = group.random(ZR)
    print("correct!" if check_theorem13(gp, gq, ga, gb) else "wrong!")
