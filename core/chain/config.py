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
from pathlib import Path
from enum import Enum, auto

import chain
from chain.message import print_info, print_error
from chain.errors import *


#==============================================================================
class ConfigFile:
    '''Searching of config files in known locations.

    Searching is performed in the following order:

        - path to the file, specified in appropriate command-line parameter;

        - current working directory (usually this is a project root);

        - path to the config home directory, specified in command-line;

        - $CHAIN_CONFIG_HOME, if this environment variable is set;

        - $XDG_CONFIG_HOME/<config_subdir>, if the '$XDG_CONFIG_HOME'
          environment variable is set (see the note below, marked with a '*');

        - ~/.config/<config_subdir> (see the note below, marked with a '*');

        - default config path (the 'config' subdirectory in the path,
          where build system is installed).

    * - if the '$CHAIN_CONFIG_DIR_NAME' variable does not set, <config_subdir>
    is 'chain', otherwise it is set by value from the '$CHAIN_CONFIG_DIR_NAME'
    variable.

    Path to the found file(s) can be used from 'self.paths' list.
    '''

    #--------------------------------------------------------------------------
    def __init__(
            self, *, for_what, args, arg_name, file_name, default_path,
            find_all, message_tag = 'BUILD/INIT/CONFIG'):
        self.for_what = for_what
        self.file_name = file_name
        self.find_all = find_all
        self.message_tag = message_tag
        self.file_path = None

        cfg_dir = Path(os.environ.get('CHAIN_CONFIG_DIR_NAME', 'chain'))
        user_config_subdir = Path('.config') / cfg_dir

        if (not self.__load_from_arg(args, arg_name, is_dir=False)
                and not self.__load_from_project_root(args)
                and not self.__load_from_arg(args, 'config_home', is_dir=True)
                and not self.__load_from_env_path('CHAIN_CONFIG_HOME')
                and not self.__load_from_env_path('XDG_CONFIG_HOME', cfg_dir)
                and not self.__load_from_env_path('HOME', user_config_subdir)
                and not self.__load_from_path(default_path, 'default path')
                and self.file_path is None):
            print_error(
                f"Configuration file for {for_what} does not found",
                self.message_tag)
            raise ConfigFileNotFound(for_what)

        if self.find_all:
            print_debug(
                f"Configuration files used for {self.for_what}: "
                f"'{self.file_path}'", self.message_tag)

    #--------------------------------------------------------------------------
    def __set_config_origin(self, file_path, origin):
        if self.paths is None:
            self.paths = list()

        self.paths.append(file_path)

        if self.find_all:
            return False
        else:
            print_debug(
                f"Configuration for {self.for_what} is used from {origin}: "
                f"'{self.file_path}'", self.message_tag)

            return True

    #--------------------------------------------------------------------------
    def __load_from_arg(self, args, arg_name, is_dir=False):
        try:
            path_ = Path(args[arg_name])
        except:
            return False

        if is_dir:
            if not path_.is_dir():
                print_error(
                    f"Path is not directory "
                    f"(location of the config file for {self.for_what}): "
                    f"{path_}",
                    self.message_tag)
                raise ConfigPathError(path_, ConfigPathError.Kind.NOT_DIR)

            file_path = path_ / self.file_name
        else:
            file_path = path_

        file_path = file_path.resolve()
        msg = (f"(config file for {self.for_what}, "
               f"specified in command-line argument): {file_path}")

        if not file_path.exists():
            print_error(f"File does not found {msg}", self.message_tag)
            raise ConfigPathError(path_, ConfigPathError.Kind.NOT_EXISTS)

        if file_path.is_dir():
            print_error(f"Path is directory {msg}", self.message_tag)
            raise ConfigPathError(path_, ConfigPathError.Kind.NOT_FILE)

        return self.__set_config_origin(file_path, "command-line argument")

    #--------------------------------------------------------------------------
    def __load_from_project_root(self, args):
        try:
            file_path = Path(args['project_root']) / self.file_name
        except:
            return False

        if not file_path.exists():
            return False

        return self.__set_config_origin(file_path, 'project root')

    #--------------------------------------------------------------------------
    def __load_from_path(self, path_, loc):
        if not path_.exists():
            return False

        if not path_.is_dir():
            print_error(
                f"Finding config '{self.file_name}' in '{loc}', "
                f"but this path is to a file, not to a directory: {path_}",
                self.message_tag)
            raise ConfigPathError(path_, ConfigPathError.Kind.NOT_DIR)

        file_path = path_ / self.file_name

        if not file_path.exists():
            return False

        return self.__set_config_origin(file_path, loc)

    #--------------------------------------------------------------------------
    def __load_from_env_path(self, env_var, subdir=''):
        try:
            env_var_path = Path(os.environ[env_var])
        except:
            return False

        loc = os.path.join('$' + env_var, subdir)

        if not env_var_path.is_absolute():
            print_error(
                f"Finding config '{self.file_name}' in '{loc}'. "
                f"Path in the '${env_var}' environment variable "
                f"should be absolute, but set to '{env_var_path}'",
                self.message_tag)
            raise RelativeEnvPath(env_var, env_var_path)

        return self.__load_from_path(env_var_path / subdir, loc)
