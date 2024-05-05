#******************************************************************************
#
#  Project: Build system for FPGA/ASIC
#
#  Description: Tests of loading the 'tools.toml' config file
#
#  Copyright (c) 2024 Anton Polstyankin <mail@pavhw.org>
#
#******************************************************************************

import os
import sys
import argparse
import importlib

import pytest


#------------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def theme_config(run_test_root, fake_chain_root):
    cfg_dir = fake_chain_root / 'config'
    cfg_dir.mkdir()

    theme_config_file = run_test_root / 'config' / 'theme.toml'
    theme_config_link = cfg_dir / 'theme.toml'

    theme_config_link.symlink_to(theme_config_file, target_is_directory=False)

#------------------------------------------------------------------------------
def test_not_file_from_cmdarg(run_chain, tmp_path):
    import chain.config

    cfg_dir = tmp_path / 'config'
    cfg_dir.mkdir()

    args = ['--flows-config', str(cfg_dir), 'test_flow']

    e = run_chain(args, chain.config.ConfigPathError)
    assert e.kind == chain.config.ConfigPathError.Kind.NOT_FILE

#------------------------------------------------------------------------------
def test_not_exists_from_cmdarg(run_chain, tmp_path):
    import chain.config

    cfg_dir = tmp_path / 'config' / 'local_tools.toml'
    args = ['--flows-config', str(cfg_dir), 'test_flow']

    e = run_chain(args, chain.config.ConfigPathError)
    assert e.kind == chain.config.ConfigPathError.Kind.NOT_EXISTS

#------------------------------------------------------------------------------
def test_empty_config_from_cmdarg(run_chain, tmp_path):
    cfg_dir = tmp_path / 'config'
    cfg_dir.mkdir()

    cfg_file = cfg_dir / 'local_tools.toml'
    cfg_file.touch()

    sconstruct = tmp_path / 'SConstruct'
    sconstruct.touch()

    args = [
        '--flows-config', str(cfg_file),
        '-p', str(tmp_path),
        'test_flow',
    ]

    e = run_chain(args, SystemExit)
    assert e.code == 0

#------------------------------------------------------------------------------
def test_empty_config_from_project_root(run_chain, tmp_path):
    import chain.config

    prj_dir = tmp_path / 'project'
    prj_dir.mkdir()

    cfg_file = prj_dir / 'flows.toml'
    cfg_file.touch()
#   cfg_file.write_text('')

    sconstruct = prj_dir / 'SConstruct'
    sconstruct.touch()

    args = [
        '-p', str(prj_dir),
        'test_flow',
    ]

    # TODO: load file and check

    e = run_chain(args, SystemExit)
    assert e.code == 0
