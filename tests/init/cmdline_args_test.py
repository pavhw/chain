#******************************************************************************
#
#  Project: Build system for FPGA/ASIC
#
#  Description: Tests for checking command-line arguments
#
#  Copyright (c) 2024 Anton Polstyankin <mail@pavhw.org>
#
#******************************************************************************

import os
import sys
import argparse
import importlib

import pytest


#******************************************************************************
# Tests
#

#------------------------------------------------------------------------------
def test_no_flow_specified(main):
    args = []

    with pytest.raises(SystemExit) as einfo:
        parser = main.get_command_line_parser()
        parsed_args = parser.parse_args(args)

    assert einfo.value.code != 0

