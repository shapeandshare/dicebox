import logging
import os
import struct
import math

def lucky(noise=0):
    """Simple function to determine whether or not a thing occurs.

    :param noise: floating point value for noise
    :return: boolean
    """
    if float(noise) > float(ord(struct.unpack('c', os.urandom(1))[0])) / 255:
        logging.debug('luck bestowed')
        return True
    return False


def random_index(set_size):
    rand = float(ord(struct.unpack('c', os.urandom(1))[0])) / 255
    return int(math.ceil(rand * set_size))

