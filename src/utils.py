
def sign(x):
    if x is None:
        return 0
    if x == 0:
        return 0
    if x > 0:
        return 1
    return -1


def sign2(x):
    if x is None:
        return 0
    if x >= 0:
        return 1
    return -1
