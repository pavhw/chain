#******************************************************************************
#
#  Project: Build system for FPGA/ASIC
#
#  Description: Shared test objects
#
#  Copyright (c) 2024 Anton Polstyankin <mail@pavhw.org>
#
#******************************************************************************

import os
import sys
import importlib
from pathlib import Path

import pytest


#==============================================================================
class RunWithArgs:
    '''Runs in the fake root of build system installation

    Object of this class is returned by fixture 'run_chain'.
    This object is callable and receives the command-line arguments for
    building and an exception which should be raised (optionally).

    The calling returns the exception object for checking in test
    (if the exception is passed in method argument) or None.
    '''

    def __init__(self, main, fake_chain_root):
        self.main = main
        self.root_path = fake_chain_root

    def __call__(self, args, exception=None):
        parser = self.main.get_command_line_parser()
        parsed_args = parser.parse_args(args)

        if exception is None:
            self.main.main(self.root_path, parsed_args)
            return None

        with pytest.raises(exception) as einfo:
            self.main.main(self.root_path, parsed_args)

        return einfo.value


#------------------------------------------------------------------------------
@pytest.fixture(scope="session")
def main():
    '''Load the run script as module'''

    script_path = str(Path.cwd() / 'bin' / 'chain')

    spec = importlib.util.spec_from_loader(
        'chain', importlib.machinery.SourceFileLoader('chain', script_path))

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    return module

#------------------------------------------------------------------------------
@pytest.fixture
def run_chain(main, fake_chain_root):
    return RunWithArgs(main, fake_chain_root)

#------------------------------------------------------------------------------
@pytest.fixture(scope="session")
def cwd():
    return Path.cwd()


#******************************************************************************
# Autouse fixtures
#

#------------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def fake_chain_root(tmp_path, cwd):
    root = tmp_path / 'chain_root'
    root.mkdir()

    core_path = root / 'core'
    core_path.symlink_to(cwd / 'core', target_is_directory=True)

    return root.resolve()

#------------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def fake_config_dir(fake_chain_root):
    cfg_dir = fake_chain_root / 'config'
    cfg_dir.mkdir()

    return cfg_dir

#------------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def theme_config_link(cwd, fake_config_dir):
    file = cwd / 'config' / 'theme.toml'
    link = fake_config_dir / 'theme.toml'

    link.symlink_to(file, target_is_directory=False)

#------------------------------------------------------------------------------
@pytest.fixture(autouse=True, scope="session")
def add_core_dir_to_sys_path():
    sys.path.append(os.path.join(os.getcwd(), 'core'))