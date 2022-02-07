import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

import compression
import decompression
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


def decompress_fake_image():
    im = decompression.EBCOT_decompression('compressed/fake_image.txt')
    with open('decompressed/fake_image.txt', 'w') as f:
        f.write(
            '\n'.join(' '.join([str(int(x[0])) for x in line]) for line in im)
        )


def image_transform_verification(im, fig=None):  # Show the result of wavelet transform + quantization
    im = color_mapping(im)
    # Wavelet transform + Quantization
    im[:, :, 0] = wavelet(im[:, :, 0])
    im[:, :, 1] = wavelet(im[:, :, 1])
    im[:, :, 2] = wavelet(im[:, :, 2])
    im = np.rint(im).astype(int)
    im = im // 2 + 128  # Remap values between 0 and 255

    if fig is not None:
        fig.add_subplot(1, 2, 1)
        plt.imshow(im)
    else:
        plt.imshow(im)
        plt.show()


def compress_shield_image(fig):
    with Image.open('source/shield_power.png') as im:
        im = im.convert('RGB')
        im = np.asarray(im)
        image_transform_verification(im, fig=fig)
        compress(im, 'compressed/shield_power.txt')


def decompress_shield_image(fig):
    im = decompression.EBCOT_decompression('compressed/shield_power.txt')

    im2 = np.rint(im).astype(int)
    im2 = im2 // 2 + 128  # Remap values between 0 and 255
    fig.add_subplot(1, 2, 2)
    plt.imshow(im2)
    plt.show()
    # Todo : implement inverse wavelet transform
    Image.fromarray(im2.astype(np.uint8)).save('decompressed/shield_power.png')


if __name__ == '__main__':
    utils.DEBUG = False

    ## Compression with shield image

    fig = plt.figure(figsize=(7, 4))
    compress_shield_image(fig)
    decompress_shield_image(fig)
    plt.show()

    ## Compression with fake image (used for tests)

    # compress_fake_image()
    # decompress_fake_image()
