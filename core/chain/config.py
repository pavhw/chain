#******************************************************************************
#
#  Project: Build system for FPGA/ASIC
#
#  Description: Working with configuration files
#
#  Copyright (c) 2024 Anton Polstyankin <mail@pavhw.org>
#
#******************************************************************************

import os
import sys
import tomllib
from pathlib import Path

import chain
from chain.message import *
from chain.errors import *


#==============================================================================
class ConfigFinder:
    #--------------------------------------------------------------------------
    def __init__(self, file_name=None, stop_on_first=True):
        self.locations = list()
        self.file_name = file_name
        self.__stop_on_first = stop_on_first

    #--------------------------------------------------------------------------
    def set_file_name(self, file_name):
        self.file_name = file_name

        for loc in self.locations:
            loc.file_name = file_name

    #--------------------------------------------------------------------------
    def stop_on_first(self, value=True):
        self.__stop_on_first = value

    #--------------------------------------------------------------------------
    def insert_arg_opt(
            self, pos, name, args,
            is_dir=False, path_prefix=None, should_exist=True):

        value = args.get(name[2:].replace('-', '_'))

        loc = ConfigLoc(
            ConfigLoc.ARG_OPT, name, value, is_dir, path_prefix, should_exist,
            self.file_name)

        self.locations.insert(pos, loc)

    #--------------------------------------------------------------------------
    def insert_env_var(
            self, pos, name,
            is_dir=False, path_prefix=None, should_exist=True):

        value = os.environ.get(name)

        loc = ConfigLoc(
            ConfigLoc.ENV_VAR, name, value, is_dir, path_prefix, should_exist,
            self.file_name)

        self.locations.insert(pos, loc)

    #--------------------------------------------------------------------------
    def insert_path(
            self, pos, name, path,
            is_dir=False, path_prefix=None, should_exist=True):

        loc = ConfigLoc(
            ConfigLoc.PATH, name, path, is_dir, path_prefix, should_exist,
            self.file_name)

        self.locations.insert(pos, loc)

    #--------------------------------------------------------------------------
    def append_arg_opt(
            self, name, args,
            is_dir=False, path_prefix=None, should_exist=True):

        self.insert_arg_opt(
            len(self.locations), 
            name, args, is_dir, path_prefix, should_exist)

    #--------------------------------------------------------------------------
    def append_env_var(
            self, name, is_dir=False, path_prefix=None, should_exist=True):

        self.insert_env_var(
            len(self.locations), name, is_dir, path_prefix, should_exist)

    #--------------------------------------------------------------------------
    def append_path(
            self, name, path,
            is_dir=False, path_prefix=None, should_exist=True):

        self.insert_path(
            len(self.locations), 
            name, path, is_dir, path_prefix, should_exist)

    #--------------------------------------------------------------------------
    def prepend_arg_opt(
            self, name, args,
            is_dir=False, path_prefix=None, should_exist=True):
        self.insert_arg_opt(0, name, args, is_dir, path_prefix, should_exist)

    #--------------------------------------------------------------------------
    def prepend_env_var(
            self, name, is_dir=False, path_prefix=None, should_exist=True):
        self.insert_env_var(0, name, is_dir, path_prefix, should_exist)

    #--------------------------------------------------------------------------
    def prepend_path(
            self, name, path,
            is_dir=False, path_prefix=None, should_exist=True):
        self.insert_path(0, name, path, is_dir, path_prefix, should_exist)

    #--------------------------------------------------------------------------
    def delete_loc(self, n):
        try:
            del self.locations[n]
        except:
            pass

    #--------------------------------------------------------------------------
    def delete_first_loc(self):
        self.delete_loc(0)

    #--------------------------------------------------------------------------
    def delete_last_loc(self):
        self.delete_loc(len(self.locations)-1)

    #--------------------------------------------------------------------------
    def find(self):
        paths = list()

        for loc in self.locations:
            try:
                result = loc.find()
            except PathError as e:
                raise ConfigFinderError(loc) from e

            debug_msg = f'Searching in the {loc}: '
            msg_tag = 'CONFIG'

            if result is None:
                print_debug(debug_msg + 'not found', msg_tag)
                continue

            print_debug(debug_msg + 'ok', msg_tag)
            paths.append(result)

            if self.__stop_on_first:
                break

        if len(paths) == 0:
            return None
        elif self.__stop_on_first:
            return paths[0]
        else:
            return paths


#==============================================================================
class ConfigLoc:
    ARG_OPT = 0
    ENV_VAR = 1
    PATH = 2

    #--------------------------------------------------------------------------
    def __init__(
            self, kind, name, value,
            is_dir, path_prefix, should_exist, file_name):
        self.kind = kind
        self.name = name
        self.value = value
        self.is_dir = is_dir
        self.path_prefix = path_prefix
        self.should_exist = should_exist
        self.file_name = file_name

    #--------------------------------------------------------------------------
    def find(self):
        if self.value is None:
            return None

        path = Path(self.value)

        if self.path_prefix is None and not path.is_absolute():
            raise PathError(path, PathError.Kind.NOT_ABS)
        elif not path.is_absolute():
            path = Path(self.path_prefix) / path

        if self.should_exist and not path.exists():
            raise PathError(path, PathError.Kind.NOT_EXIST)

        if self.is_dir:
            if self.should_exist and not path.is_dir():
                raise PathError(path, PathError.Kind.NOT_DIR)

            file_path = path / self.file_name
        else:
            file_path = path

        file_path = file_path.resolve()

        if file_path.is_dir():
            raise PathError(file_path, PathError.Kind.NOT_FILE)

        if file_path.exists():
            return file_path
        else:
            return None

    #--------------------------------------------------------------------------
    def __str__(self):
        match self.kind:
            case self.ARG_OPT:
                return f"path from command-line option '{self.name}'"
            case self.ENV_VAR:
                return f"path from environment variable '${self.name}'"
            case self.PATH:
                return f"{self.name}: {self.value}"


#==============================================================================
class ConfigLoader:
    #--------------------------------------------------------------------------
    def __init__(self, file_path, format='toml'):
        self.file_path = file_path
        self.format = format
        self.dict = dict()

    #--------------------------------------------------------------------------
    def load(self):
        try:
            f = open(self.file_path, 'rb')
        except Exception as e:
            raise ConfigLoaderError(
                ConfigLoaderError.Kind.OPEN, path=file_path) from e

        if self.format == 'toml':
            return self.load_toml(f)
        else:
            raise ConfigLoaderError(
                ConfigLoaderError.Kind.FORMAT, format=format)

    #--------------------------------------------------------------------------
    def load_toml(self, f):
        try:
            return tomllib.load(f)
        except Exception as e:
            raise ConfigLoaderError(
                ConfigLoaderError.Kind.LOAD, path=f.name) from e
