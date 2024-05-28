#******************************************************************************
#
#  Project: Build system for FPGA/ASIC
#
#  Description: Tests for searching of tools configuration file
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
def test_no_config(run_chain, cwd, tmp_config_home):
    import chain

    link_config_file('theme.toml', cwd, tmp_config_home)

    args = ['myflow']
    err = chain.errors.ConfigError

    e = run_chain(args, None)
    assert e.kind == err.Kind.FILE_NOT_FOUND

##------------------------------------------------------------------------------
#def test_cmdarg_bad_path(run_chain):
#    args = ['--tools-config', 'mytools.toml', 'myflow']
#    err = chain.errors.ConfigPathError
#
#    e = run_chain(args, err)
#    assert e.kind == err.Kind.NOT_EXIST
#
##------------------------------------------------------------------------------
#def test_cmdarg_pass_dir(run_chain, fake_config_dir):
#    args = ['--tools-config', str(fake_config_dir), 'myflow']
#    err = chain.errors.ConfigPathError
#
#    e = run_chain(args, err)
#    assert e.kind == err.Kind.NOT_FILE
#
##------------------------------------------------------------------------------
#def test_config_home_bad_path(cwd, run_chain, tmp_config_home):
#    link_config_file('theme.toml', cwd, tmp_config_home)
#
#    args = ['--config-home', str(tmp_config_home), 'myflow']
#    err = chain.errors.ConfigPathError
#
#    e = run_chain(args, err)
#    assert e.kind == err.Kind.NOT_EXIST
#
##------------------------------------------------------------------------------
#def test_config_home_pass_file(cwd, run_chain, tmp_config_home):
#    config_file = tmp_config_home / 'mytools.toml'
#    config_file.touch()
#
#    args = ['--config-home', str(config_file), 'myflow']
#    err = chain.errors.ConfigPathError
#
#    e = run_chain(args, err)
#    assert e.kind == err.Kind.NOT_DIR
#
##------------------------------------------------------------------------------
#def test_config_env_relative_path(run_chain):
#    os.environ['CHAIN_CONFIG_HOME'] = os.path.join('relative', 'path')
#
#    args = ['myflow']
#    run_chain(args, chain.errors.RelativeEnvPath)
#
#    del os.environ['CHAIN_CONFIG_HOME']
#
##------------------------------------------------------------------------------
#def test_config_env_bad_path(run_chain, tmp_path):
#    os.environ['CHAIN_CONFIG_HOME'] = str(tmp_path / 'my_config_home')
#    args = ['myflow']
#
#    err = chain.errors.ConfigPathError
#    e = run_chain(args, err)
#    assert e.kind == err.Kind.NOT_EXIST
#
#    del os.environ['CHAIN_CONFIG_HOME']
#
##------------------------------------------------------------------------------
#def test_config_env_pass_file(run_chain, tmp_config_home):
#    config_file = tmp_config_home / 'mytools.toml'
#    config_file.touch()
#
#    os.environ['CHAIN_CONFIG_HOME'] = str(config_file)
#    args = ['myflow']
#
#    err = chain.errors.ConfigPathError
#    e = run_chain(args, err)
#    assert e.kind == err.Kind.NOT_DIR
#
#    del os.environ['CHAIN_CONFIG_HOME']
#
##------------------------------------------------------------------------------
#def test_xdg_relative_path(run_chain):
#    os.environ['XDG_CONFIG_HOME'] = os.path.join('relative', 'path')
#
#    args = ['myflow']
#    run_chain(args, chain.errors.RelativeEnvPath)
#
#    del os.environ['XDG_CONFIG_HOME']
#
##------------------------------------------------------------------------------
#def test_no_tools_config(cwd, run_chain, tmp_config_home):
#    link_config_file('theme.toml', cwd, tmp_config_home)
#    args = ['myflow']
#
#    err = chain.errors.ConfigFileNotFound
#    e = run_chain(args, err)
#
##------------------------------------------------------------------------------
#def test_prj_root_bad_path(cwd, run_chain, tmp_config_home):
#    link_config_file('theme.toml', cwd, tmp_config_home)
#
#    args = ['--project-root', '/bad/path', 'myflow']
#    err = chain.errors.ConfigPathError
#
#    e = run_chain(args, err)
#    assert e.kind == err.Kind.NOT_EXIST
#
##------------------------------------------------------------------------------
#def test_prj_root_pass_file(cwd, run_chain, tmp_config_home):
#    config_file = tmp_config_home / 'mytools.toml'
#    config_file.touch()
#
#    args = ['--project-root', str(config_file), 'myflow']
#    err = chain.errors.ConfigPathError
#
#    e = run_chain(args, None)
#    assert e.kind == err.Kind.NOT_DIR


#******************************************************************************
# Fixtures
#

#------------------------------------------------------------------------------
@pytest.fixture
def tmp_config_home(tmp_path):
    config_home = tmp_path / 'my_config_home'
    config_home.mkdir()

    return config_home


#******************************************************************************
# Functions
#

#------------------------------------------------------------------------------
def link_config_file(file_name, cwd, config_home):
    file = cwd / 'config' / file_name
    link = config_home / file_name
    link.symlink_to(file, target_is_directory=False)
