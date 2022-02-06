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


def compress_fake_image():
    with open('source/fake_image.txt', 'r') as f:
        fake_image = [[[int(x)] for x in line.replace('\n', '').split(' ')] for line in f.readlines()]

    compression.EBCOT_compression(np.array(fake_image), "compressed/fake_image.txt")


def image_transform_verification(im):  # Show the result of wavelet transform + quantization
    im = color_mapping(im)
    # Wavelet transform + Quantization
    im[:, :, 0] = wavelet(im[:, :, 0])
    im[:, :, 1] = wavelet(im[:, :, 1])
    im[:, :, 2] = wavelet(im[:, :, 2])
    im = np.rint(im).astype(int)

    import matplotlib.pyplot as plt
    plt.imshow(im // 2 + 128)  # Remap values between 0 and 255
    plt.show()


def compress_shield_image():
    with Image.open('source/shield_power.png') as im:
        im = im.convert('RGB')
        im = np.asarray(im)
        image_transform_verification(im)
        compress(im, 'compressed/shield_power.txt', 2)


if __name__ == '__main__':
    utils.DEBUG = False
    compress_shield_image()
