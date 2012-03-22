import os
import random
import sys

from mock import log as logging

DEF_LOGGING_FMT = '%(levelname)s: @%(name)s : %(message)s'
DEF_LOGGING_DATE_FMT = None  # Apparently it should revert to ISO8601 format


def random_ip4():
    full = ["10"]
    for i in range(3):
        full.append(str(random.randint(0, 254)))
    return ".".join(full)


def setup_logging(verbosity):
    root_logger = logging.root
    if verbosity > 2:
        root_logger.setLevel(logging.DEBUG)
    elif verbosity > 1:
        root_logger.setLevel(logging.INFO)
    else:
        root_logger.setLevel(logging.WARNING)
    formatter = logging.Formatter(DEF_LOGGING_FMT, DEF_LOGGING_DATE_FMT)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)
