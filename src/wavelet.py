from math import sqrt

import numpy as np

__all__ = ['wavelet']

H = [1 / sqrt(2), 1 / sqrt(2)]
G = [1 / sqrt(2), -1 / sqrt(2)]


def circular_conv(x, h, d):
    if d == 1:
        return np.transpose(circular_conv(np.transpose(x), h, 0))
    y = np.zeros(x.shape)
    p = len(h)
    pc = int(round(float((p - 1) / 2)))
    for i in range(0, p):
        y = y + h[i] * np.roll(x, pc - i, axis=0)
    return y


def down_sampling(x, d):
    p = 2
    y = None
    if d == 0:
        y = x[::p, :]
    elif d == 1:
        y = x[:, ::p]
    return y


def coarse(image, d):
    return down_sampling(circular_conv(image, H, d), d)


def fine(image, d):
    return down_sampling(circular_conv(image, G, d), d)


def wavelet(image):
    low = coarse(image, 0)
    high = fine(image, 0)

    return np.concatenate(
        (
            np.concatenate((coarse(low, 1), coarse(high, 1)), axis=0),
            np.concatenate((fine(low, 1), fine(high, 1)), axis=0)
        ), axis=1
    )
