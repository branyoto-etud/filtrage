from math import log, floor

import numpy as np

from utils import sign, sign2, debug


class EBCOT_Compressor:

    def __init__(self, im: np.array, length: int = 5):
        self.L = length
        self.shape = im.shape
        self.buffer = ""
        self.im = im
        self.N = int(floor(log(abs(im.max()), 2)) + 1)
        self.KS = np.zeros_like(im)
        self.KSP = None
        self.channel = None
        self.offset = None
        self.size = None
        self.n = None
        self.processed = np.zeros_like(im)

    def resolve_data(self, data):
        if data is not None:
            return data
        return self.KS

    def write(self, destination, mode="w"):
        with open(destination, mode) as out:
            out.write(f"---PLAN START {self.n}---\n")
            out.write(self.buffer)
            out.write("---PLAN END---\n")
        self.buffer = ""

    # Focus

    def reset_bloc(self):
        self.offset = None
        self.size = None

    def next_bloc(self):
        def aux():
            if self.offset is None:
                self.offset = (0, 0)
                return True
            di, dj = self.offset
            if di + self.size[0] >= self.shape[0]:
                if dj + self.size[1] >= self.shape[1]:
                    return False
                self.offset = (0, dj + self.size[1])
            else:
                self.offset = (di + self.size[0], dj)
            return True

        r = aux()
        if r:
            self.size = (min(4, self.shape[0] - self.offset[0]), min(self.L, self.shape[1] - self.offset[1]))
        debug(f'   --Bloc {self.offset} - {self.size} - {r}--')
        return r

    def reset_channel(self):
        self.channel = None

    def next_channel(self):
        def aux():
            if self.channel is None:
                self.channel = 0
                return True
            if len(self.shape) < 3 or self.channel + 1 >= self.shape[2]:
                return False
            self.channel += 1
            return True

        r = aux()
        debug(f' --CHANNEL {self.channel} - {r}--')
        return r

    def next_plan(self):
        self.n = self.n - 1 if self.n is not None else self.N - 1
        self.processed = np.zeros_like(self.im)
        self.reset_channel()
        self.reset_bloc()
        self.KSP = np.copy(self.KS)
        debug(f'--PLAN {self.n} - {2 ** self.n}--')

    # Getters

    def getK(self, i, j):
        if j < -1 or j > self.size[1]:  # Out of block x-axis
            return None
        if i < -1 or i > self.size[0]:  # Out of the block y-axis
            return None
        di, dj = self.offset
        if dj + j < 0 or dj + j >= self.shape[1]:  # Out of the image x-axis
            return None
        if di + i < 0 or di + i >= self.shape[0]:  # Out of the image y-axis
            return None
        return self.im[di + i, dj + j, self.channel]

    def isKs(self, i, j, data=None):
        data = self.resolve_data(data)
        k = self.getK(i, j)
        if k is None:
            return False
        di, dj = self.offset
        return data[di + i, dj + j, self.channel]

    def getKS(self, i, j):
        if not self.isKs(i, j):
            return None
        di, dj = self.offset
        return self.im[di + i, dj + j, self.channel]

    def getStripIndex(self, i, j):
        strip = ""
        di, dj = self.offset
        strip += "H" if dj + j >= self.shape[1] // 2 else "L"
        strip += "H" if di + i >= self.shape[0] // 2 else "L"
        return strip

    def get_processed(self, i, j):
        di, dj = self.offset
        return self.processed[di + i, dj + j, self.channel]

    # Setters

    def setKS(self, i, j):
        if self.getK(i, j) is None:
            raise Exception("ARG")
        di, dj = self.offset
        self.KS[di + i, dj + j, self.channel] = 1

    def buff(self, *args):
        txt = ' '.join(map(str, args))
        self.buffer += txt + '\n'
        debug('     ' + txt)

    def set_processed(self, i, j):
        di, dj = self.offset
        self.processed[di + i, dj + j, self.channel] = True

    # Neighbourhood
    def KH(self, i, j, data=None):
        data = self.resolve_data(data)
        return self.isKs(i, j - 1, data) + self.isKs(i, j + 1, data)

    def KV(self, i, j, data=None):
        data = self.resolve_data(data)
        return self.isKs(i - 1, j, data) + self.isKs(i + 1, j, data)

    def KD(self, i, j, data=None):
        data = self.resolve_data(data)
        return \
            self.isKs(i + 1, j + 1, data) + \
            self.isKs(i + 1, j - 1, data) + \
            self.isKs(i - 1, j + 1, data) + \
            self.isKs(i - 1, j - 1, data)

    def haveNeighbourKS(self, i, j):
        if self.KV(i, j, self.KSP) > 0:
            return True
        if self.KH(i, j, self.KSP) > 0:
            return True
        if self.KD(i, j, self.KSP) > 0:
            return True
        if self.KV(i, j, self.KS) > 0:
            return True
        if self.KH(i, j, self.KS) > 0:
            return True
        if self.KD(i, j, self.KS) > 0:
            return True
        return False

    # Primitives
    def SC(self, i, j):
        self.setKS(i, j)
        dv = sign(sign(self.getKS(i - 1, j)) + sign(self.getKS(i + 1, j)))
        dh = sign(sign(self.getKS(i, j - 1)) + sign(self.getKS(i, j + 1)))
        p = dh if dh != 0 else (dv if dv != 0 else 1)
        ctx = abs(dh * 3 + dv)
        self.buff(int(p != sign2(self.getKS(i, j))), 'SC', ctx)

    def RL(self, j):
        at_least_one = False
        for i in range(self.size[0]):
            if not self.get_processed(i, j):
                at_least_one = True
                if abs(self.getK(i, j)) >= 2 ** self.n:
                    self.buff('1', 'RL', f'{(i & 2) >> 1}{i & 1}')
                    self.SC(i, j)
                    return i + 1

        if at_least_one:
            self.buff('0', 'RL')

        return None

    def MR(self, i, j):
        ks = abs(self.getKS(i, j))
        refining = int((ks & (2 ** self.n)) != 0)
        sigma = ks < 2 ** (self.n + 1)
        if sigma != 0:
            self.buff(refining, 'MR2')
        else:
            self.buff(refining, 'MR', int((self.KH(i, j) + self.KV(i, j)) != 0))

    def ZC(self, i, j):
        def ZC_ctx():
            kh, kv, kd = self.KH(i, j), self.KV(i, j), self.KD(i, j)
            strip = self.getStripIndex(i, j)
            if strip == "HH":
                return min(8, 3 * (kh + kv) + min(2, kd))
            if strip == "HL":
                kh, kv = kv, kh
            if kh == kv == 0:
                return min(kd, 2)
            if kh == 0:
                return 2 + kv
            if kv == 0:
                return 5 + (kd != 0)
            return 6 + kh

        is_ks = abs(self.getK(i, j)) >= 2 ** self.n
        self.buff(int(is_ks), 'ZC', ZC_ctx())
        if is_ks:
            self.SC(i, j)
        return is_ks

    # Passes

    def propagation(self):
        self.reset_bloc()
        debug('  --PROPAGATION--')
        while self.next_bloc():
            for i in range(self.size[0]):
                for j in range(self.size[1]):
                    if self.isKs(i, j, self.KSP) == 0 and self.haveNeighbourKS(i, j):
                        self.set_processed(i, j)

            for j in range(self.size[1]):
                debug(f'    ---{j}---')
                for i in range(self.size[0]):
                    if self.get_processed(i, j):
                        self.ZC(i, j)

    def affinage(self):
        debug('  --AFFINAGE--')
        self.reset_bloc()
        while self.next_bloc():
            for j in range(self.size[1]):
                for i in range(self.size[0]):
                    if self.isKs(i, j, self.KSP):
                        self.MR(i, j)
                        self.set_processed(i, j)

    def nettoyage(self):
        debug('  --NETTOYAGE--')
        self.reset_bloc()
        rl = True
        while self.next_bloc():
            for j in range(self.size[1]):
                debug(f'    ---{j}---')
                rl_i = 0
                if rl:
                    rl_i = self.RL(j)
                    if rl_i is None:
                        continue
                    rl = False
                else:
                    rl = True
                for i in range(rl_i, self.size[0]):
                    if not self.get_processed(i, j):
                        rl &= not self.ZC(i, j)
            rl = True


# main part
def EBCOT_compression(im, destination, max_depth=None):
    first = True
    ebcot = EBCOT_Compressor(im)
    low = 0 if max_depth is None else max(0, ebcot.N - max_depth)

    with open(destination, "w") as out:  # Clear file
        out.write(f'{ebcot.N}\n{im.shape[0]}, {im.shape[1]}, {im.shape[2]}\n')

    debug(f"--NB PLAN - {ebcot.N}--")
    for n in range(ebcot.N - 1, low - 1, -1):
        ebcot.next_plan()
        while ebcot.next_channel():
            if not first:
                ebcot.propagation()
                ebcot.affinage()
            ebcot.nettoyage()
        first = False
        ebcot.write(destination, "a")
