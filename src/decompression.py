
from utils import debug
import numpy as np
import re

class EBCOT_decompressor:
    def __init__(self, input, output, length: int = 5):
        with open(input, 'r') as f:
            self.data = [line.replace('\n', '') for line in f.readlines()]
        self.N = int(self.data[0])
        self.shape = tuple(int(x.strip()) for x in self.data[1].split(","))
        self.l_idx = 2
        self.L = length  # Todo : Ajouter dans le fichier compressé
        self.output = output
        self.channel = None
        self.offset = None
        self.size = None
        self.n = None
        self.result = np.zeros(self.shape)

    # Focus

    def next_plan(self):
        self.reset_channel()
        self.reset_bloc()
        line = self.data[self.l_idx]
        match = re.search(r'---PLAN START (\d*)---', line)
        
        if match is not None:
            debug(line)
            self.l_idx += 1
            self.n = match.group(1)
            return True
        
        return False
  
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
        debug(f' --CHANNEL {self.channel} - {r}--')
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
        debug(f'   --Bloc {self.offset} - {self.size} - {r}--')
        return r

    def next_line(self):
        line = self.data[self.l_idx]
        self.l_idx += 1
        return line


    # Setter

    def setKS(self, i, j):
        di, dj = self.offset
        self.result[di+i, dj+j, self.channel] = 2 ** self.n

    # Primitives

    def RL(self, j):
        line = self.next_line()
        if line.startswith('0'):
            return None
        else:
            idx = re.search(r'1 RL (\d*)', line).group(1)
            self.setKS(idx, j)
            return idx + 1


    def SC(self, i, j):
        pass

    def MR(self, i, j):
        pass

    def ZC(self, i, j):
        pass

    # Passes

    def propagation(self):
        pass

    def affinage(self):
        pass

    def nettoyage(self):
        self.reset_bloc()
        while self.next_bloc():
            for j in range(self.size[1]):
                idx = self.RL(j)
                if idx is None:
                    continue
                for i in range(idx, self.size[0]):
                    self.ZC(i, j)




# main part
def EBCOT_decompression(input, output):
    ebcot = EBCOT_decompressor(input, output)

    with open(output, "w"):  # Clear file
        pass
    first = True
    while ebcot.next_plan():
        while ebcot.next_channel():
            if not first:
                ebcot.propagation()
                ebcot.affinage()
            ebcot.nettoyage()
        first = False
    


