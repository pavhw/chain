#******************************************************************************
#
#  Project: Build system for FPGA/ASIC
#
#  Description: Useful utilities
#
#  Copyright (c) 2024 Anton Polstyankin <mail@pavhw.org>
#
#******************************************************************************

import os
from pathlib import Path

from chain.errors import *
from chain.message import *


#------------------------------------------------------------------------------
def check_path(path, *, is_abs=False, is_file=True, is_dir=True):
    if is_abs and not path.is_absolute():
        raise PathError(path, ConfigPathError.Kind.NOT_ABS)

    if not is_file and not is_dir:
        return

    if not path.exists():
        raise PathError(path, ConfigPathError.Kind.NOT_EXIST)

    if is_file and is_dir:
        return

    if is_file and not path.is_file():
        raise PathError(path, ConfigPathError.Kind.NOT_FILE)

    if is_dir and not path.is_dir():
        raise PathError(path, ConfigPathError.Kind.NOT_DIR)

#--------------------------------------------------------------------------
def normalize_path(current_path, relative_path):
    assert current_path.is_absolute()

    if os.path.isabs(relative_path):
        return Path(relative_path)

    return (current_path / relative_path).resolve()

#--------------------------------------------------------------------------
def wrong(msg, tag, exception=None):
    if exception is not None:
        print_error(msg, tag)
        raise exception
    else:
        print_warning(msg, tag)
