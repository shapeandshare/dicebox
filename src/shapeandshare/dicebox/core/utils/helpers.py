import os
import struct
import math
import errno
import logging


def lucky(noise=0):
    """Simple function to determine whether or not a thing occurs.

    :param noise: floating point value for noise
    :return: boolean
    """
    if noise == 1:
        return True
    if noise == 0:
        return False
    if float(noise) > float(ord(struct.unpack('c', os.urandom(1))[0])) / 255:
        return True
    return False


def random_index(set_size):
    rand = float(ord(struct.unpack('c', os.urandom(1))[0])) / 255
    return int(math.ceil(rand * set_size))


def random_index_between(min_index=0, max_index=1):
    if min_index > max_index:
        raise Exception('max must be greater than or equal to the min')

    rand = float(ord(struct.unpack('c', os.urandom(1))[0])) / 255
    delta = max_index - min_index
    delta_offset = int(math.ceil(rand * delta))
    final_index = min_index + delta_offset
    return final_index


def random():
    return float(ord(struct.unpack('c', os.urandom(1))[0])) / 255


# A dropout layer can is [0, 1), we can not actually use a '1' value.
def random_strict():
    new_random_number: float = random()
    while new_random_number >= 1.0:
        new_random_number = random()
    return new_random_number


###############################################################################
# Allows for easy directory structure creation
# https://stackoverflow.com/questions/273192/how-can-i-create-a-directory-if-it-does-not-exist
###############################################################################
def make_sure_path_exists(path):
    try:
        if os.path.exists(path) is False:
            os.makedirs(path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise exception