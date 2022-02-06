import numpy as np
from PIL import Image

import compression
import utils
from wavelet import wavelet


def color_mapping(im):
    return im.astype(int) - 128


def compress(im, destination, max_depth=None):
    # Color normalization
    im = color_mapping(im)
    # Wavelet transform + Quantization
    im[:, :, 0] = wavelet(im[:, :, 0])
    im[:, :, 1] = wavelet(im[:, :, 1])
    im[:, :, 2] = wavelet(im[:, :, 2])
    im = np.rint(im).astype(int)
    # EBCOT compression
    compression.EBCOT_compression(im, destination, max_depth)


def fake_image():
    with open('source/fake_image.txt', 'r') as f:
        fake_image = [[[int(x)] for x in line.replace('\n', '').split(' ')] for line in f.readlines()]

    compression.EBCOT_compression(np.array(fake_image), "compressed/fake_image.txt")


if __name__ == '__main__':
    utils.DEBUG = False

    with Image.open('source/shield_power.png') as im:
        im = im.convert('RGB')
        im = np.asarray(im)
        compress(im, 'compressed/shield_power.txt', 2)
