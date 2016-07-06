from charm.toolbox.pairinggroup import PairingGroup, ZR, G1, G2, pair
from jutla_roy import JutraRoy
from elliptic_curve_elgamal import EllipticCurveElGamal
import kiltz_and_wee_3 as kw3
from my_crypto_toolbox import *
from bhho import *


class CCS2:

    def __init__(self, groupObj, kdm_name):
        self.group    = groupObj
        self.g1       = self.group.random(G1)
        self.g2       = self.group.random(G2)
        self.r        = self.group.random(ZR, 2)
        self.t        = self.group.random(ZR)
        self.kdm_name = kdm_name

        self.cca      = JutraRoy(self.group, self.r[1])

        if self.kdm_name == "ElGamal":
            self.kdm      = EllipticCurveElGamal(self.group, self.r[0])
            self.__keys   = self.__generate_key()
            kdm_x         = self.__keys["kdm"]["secret_key"]
            cca_x         = self.__keys["cca"]["secret_key"]
            x             = cca_x[0] + self.t * cca_x[1]
            self.matrix_m = [[int_to_zr(self.group, 1), int_to_zr(self.group, 0), kdm_x],
                             [int_to_zr(self.group, 0), int_to_zr(self.group, 1), -x]]

        elif self.kdm_name == "BHHO":
            self.k        = [self.group.random(ZR) for _ in range(200)]
            self.kdm      = BHHO(self.group, self.k, self.r[0])
            self.__keys   = self.__generate_key()
            kdm_x         = reduce(lambda a, b: a + b,
                                   [t*s for t, s in zip(self.k, self.__keys["kdm"]["secret_key"])])
            cca_x         = self.__keys["cca"]["secret_key"]
            x             = cca_x[0] + self.t * cca_x[1]
            self.matrix_m = [[reduce(lambda a, b: a+b, self.k), int_to_zr(self.group, 0), -kdm_x],
                             [int_to_zr(self.group, 0),         int_to_zr(self.group, 1), -x]]

        self.nizk_crs = kw3.generate_crs(self.group, self.g1, self.g2, self.matrix_m)

    def __generate_key(self):
        key_kdm = self.kdm.generate_key(self.g1)
        key_cca = self.cca.generate_key(self.g1, self.g2, self.t)
        return {
            "kdm": key_kdm,
            "cca": key_cca
        }

    def get_keys(self):
        return {
            "kdm": self.__keys["kdm"],
            "cca": {"public_key": self.__keys["cca"]["public_key"]}
        }

    def encrypt(self, pk_kdm, pk_cca, m):
        c_kdm = self.kdm.encrypt(pk_kdm, m)
        c_cca = self.cca.encrypt(pk_cca, m, label=c_kdm)
        c_pi  = kw3.generate_pi(self.nizk_crs, self.r)

        return {
            "kdm": c_kdm,
            "cca": c_cca,
            "pi" : c_pi
        }

    def decrypt(self, sk_kdm, c_kdm):
        return self.kdm.decrypt(sk_kdm, c_kdm)

    def check_NIZK(self, c_kdm, c_cca, c_pi):
        if self.kdm_name == "ElGamal":
            a, b        = c_kdm
        elif self.kdm_name == "BHHO":
            a           = reduce(lambda a, b: a*b, c_kdm[0:-1])
            b           = c_kdm[-1]
        u, v, e, pi = c_cca
        instance    = [[a, u, b/e]]

        return kw3.check_certificate(self.nizk_crs, instance, c_pi, self.g2) and \
               self.cca.check_NIZK(self.__keys["cca"]["public_key"], c_cca, c_kdm)


if __name__ == '__main__':
    group = PairingGroup('MNT159')

    # ccs2 = CCS2(group, "ElGamal")
    ccs2 = CCS2(group, "BHHO")

    keys = ccs2.get_keys()
    m = group.random(G1)
    print("message: ", m)

    c = ccs2.encrypt(keys["kdm"]["public_key"], keys["cca"]["public_key"], m)
    print("encrypt: ", c)

    if ccs2.check_NIZK(c["kdm"], c["cca"], c["pi"]):
        print("accept!")
        print("decrypt: ", ccs2.decrypt(keys["kdm"]["secret_key"], c["kdm"]))
