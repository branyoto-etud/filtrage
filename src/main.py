import numpy as np

from compression import EBCOT_compression
from wavelet import wavelet


def color_mapping(im):
    return im - 128


def compress(im, destination, max_depth):
    im = color_mapping(im)
    im = wavelet(im)

    EBCOT_compression(im, destination, max_depth)


if __name__ == '__main__':
    with open('source/img.txt', 'r') as f:
        images = [[[int(x)] for x in l.replace('\n', '').split(' ')] for l in f.readlines()]

    compress(np.array(images), "tmp.txt", 2)
