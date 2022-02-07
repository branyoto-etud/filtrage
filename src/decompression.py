import re

import numpy as np

from utils import debug, sign


class EBCOT_decompressor:
    def __init__(self, input_file):
        with open(input_file, 'r') as f:
            self.data = [line.replace('\n', '') for line in f.readlines()]
        first_line = self.data[0].split(' ')
        self.N = int(first_line[0])
        self.L = int(first_line[1])
        self.shape = tuple(int(x.strip()) for x in self.data[1].split(","))
        self.l_idx = 2
        self.channel = None
        self.offset = None
        self.size = None
        self.n = None
        self.processed = np.zeros(self.shape)
        self.result = np.zeros(self.shape)
        self.sign = np.zeros(self.shape)

    # Focus

    def next_plan(self):
        self.reset_channel()
        self.reset_bloc()
        self.processed = np.zeros(self.shape)

        if self.l_idx >= len(self.data):
            return False

        line = self.data[self.l_idx]
        match = re.search(r'---PLAN START (\d*)---', line)

        if match is not None:
            self.l_idx += 1
            self.n = int(match.group(1))
            return True

        return False

    def end_plan(self):
        if not self.next_line().startswith('---PLAN END---'):
            raise Exception('Expected end plan token')

    def reset_channel(self):
        self.channel = None

    def next_channel(self):
        def aux():
            if self.channel is None:
                self.channel = 0
                return True
            if self.channel + 1 >= self.shape[2]:
                return False
            self.channel += 1
            return True

        r = aux()
        return r

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
        return r

    def next_line(self):
        line = self.data[self.l_idx]
        self.l_idx += 1
        return line

    def prev_line(self):
        self.l_idx -= 1

    def get_image(self):
        return self.result * self.sign

    # Getter

    def get_processed(self, i, j):
        di, dj = self.offset
        return self.processed[di + i, dj + j, self.channel]

    def isKs(self, i, j):
        di, dj = self.offset
        if dj + j < 0 or dj + j >= self.shape[1]:  # Out of the image x-axis
            return None
        if di + i < 0 or di + i >= self.shape[0]:  # Out of the image y-axis
            return None
        return self.result[di + i, dj + j, self.channel] != 0

    def getKs(self, i, j):
        if not self.isKs(i, j):
            return None
        di, dj = self.offset
        return self.result[di + i, dj + j, self.channel]

    def getKsSign(self, i, j):
        if not self.isKs(i, j):
            return 0
        di, dj = self.offset
        return self.sign[di + i, dj + j, self.channel]

    def haveNeighbourKS(self, i, j):
        return \
            self.isKs(i - 1, j - 1) or \
            self.isKs(i - 1, j) or \
            self.isKs(i - 1, j + 1) or \
            self.isKs(i, j - 1) or \
            self.isKs(i, j) or \
            self.isKs(i, j + 1) or \
            self.isKs(i + 1, j - 1) or \
            self.isKs(i + 1, j) or \
            self.isKs(i + 1, j + 1)

    # Setter

    def set_processed(self, i, j):
        di, dj = self.offset
        self.processed[di + i, dj + j, self.channel] = True

    def setKs(self, i, j):
        di, dj = self.offset
        if self.result[di + i, dj + j, self.channel] != 0:
            raise Exception(f"ERROR : previous value should be zero ({di + i}, {dj + j})")
        self.result[di + i, dj + j, self.channel] = 2 ** self.n

    def setKsSign(self, i, j, sign):
        di, dj = self.offset
        self.sign[di + i, dj + j, self.channel] = sign

    def addKS(self, i, j):
        di, dj = self.offset
        if self.result[di + i, dj + j, self.channel] == 0:
            raise Exception(f"ERROR : zero found instead of a value ({di + i}, {dj + j})")
        self.result[di + i, dj + j, self.channel] += 2 ** self.n

    # Primitives

    def RL(self, j):
        line = self.next_line()

        if line.startswith('0'):
            return None

        if line.startswith('1'):
            idx = int(re.search(r'1 RL (\d*)', line).group(1), 2)
            self.setKs(idx, j)
            self.SC(idx, j)
            return idx + 1

        # Todo : replace by verification of column's KS
        #  -> Remove debug in compression.py
        self.prev_line()
        return None

    def SC(self, i, j):
        def get_pred(ctx):
            if ctx == 0:
                return 1
            if ctx == 1:
                dv = sign(self.getKsSign(i - 1, j) + self.getKsSign(i + 1, j))
                return dv
            dh = sign(self.getKsSign(i, j - 1) + self.getKsSign(i, j + 1))
            return dh

        line = self.next_line()
        if (match := re.search(r'(\d) SC (\d)', line)) is not None:
            invalid, ctx = int(match.group(1)), int(match.group(2))
            pred = get_pred(ctx) * -(invalid * 2 - 1)
            self.setKsSign(i, j, pred)

    def MR(self, i, j):
        line = self.next_line()
        if line.startswith('1'):
            self.addKS(i, j)

    def ZC(self, i, j):
        line = self.next_line()
        if line.startswith('1'):
            self.setKs(i, j)
            self.SC(i, j)
            return True
        return False

    # Passes

    def propagation(self):
        debug('  --PROPAGATION--')
        self.reset_bloc()
        while self.next_bloc():
            for i in range(self.size[0]):
                for j in range(self.size[1]):
                    if self.isKs(i, j) == 0 and self.haveNeighbourKS(i, j):
                        self.set_processed(i, j)

            for j in range(self.size[1]):
                for i in range(self.size[0]):
                    if self.get_processed(i, j):
                        self.ZC(i, j)

    def affinage(self):
        debug('  --AFFINAGE--')
        self.reset_bloc()
        while self.next_bloc():
            for j in range(self.size[1]):
                for i in range(self.size[0]):
                    if self.isKs(i, j) and not self.get_processed(i, j):
                        self.MR(i, j)
                        self.set_processed(i, j)

    def nettoyage(self):
        debug('  --NETTOYAGE--')
        self.reset_bloc()
        rl = True
        while self.next_bloc():
            for j in range(self.size[1]):
                self.next_line()
                idx = 0
                if rl:
                    idx = self.RL(j)
                    if idx is None:
                        continue
                    rl = False
                else:
                    rl = True
                for i in range(idx, self.size[0]):
                    if not self.get_processed(i, j):
                        rl &= not self.ZC(i, j)
            rl = True

    def __str__(self) -> str:
        return f'(' \
               f'N = {self.N}' \
               f', L = {self.L}' \
               f', l_idx = {self.l_idx}' \
               f', channel = {self.channel}' \
               f', offset = {self.offset}' \
               f', size = {self.size}' \
               f', n = {self.n}' \
               f', shape = {self.shape}' \
               f')'


# main part
def EBCOT_decompression(input_file, ):
    ebcot = EBCOT_decompressor(input_file)

    first = True
    while ebcot.next_plan():
        while ebcot.next_channel():
            if not first:
                ebcot.propagation()
                ebcot.affinage()
            ebcot.nettoyage()
        first = False
        ebcot.end_plan()
    return ebcot.get_image()
