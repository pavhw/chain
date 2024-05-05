#******************************************************************************
#
#  Project: Build system for FPGA/ASIC
#
#  Description: Initialization of the build environment
#
#  Copyright (c) 2024 Anton Polstyankin <mail@pavhw.org>
#
#******************************************************************************

import os
import tomllib
from pathlib import Path

from rich import print
from rich.console import Console
from rich.theme import Theme

import chain.message
from chain.config import ConfigFile
from chain.message import print_info, print_error
from chain.errors import *


#==============================================================================
class _BuildEnv:
    '''Build environment, gathered from configuration files

    Attributes:
      - root_path: path to the installation directory of Chain Build System;
      - args: command-line arguments;
      - console: the Console object of the Rich package;
      - target_flow: name of the flow to run;
      - flows: dictionary of the target flow and its dependent flows;
      - tools: TODO
    '''
    #--------------------------------------------------------------------------
    def __init__(self, root_path, args):
        self.root_path = root_path
        self.args = vars(args)
        self.target_flow = args['flow']
        self.flows = dict()
        self.tools = dict()

        self.__init_console()
        message._console = self.console
        message._debug = self.args['debug']
        message._quiet = self.args['quiet']

        self.__load_tools_config()
        self.__init_flows()

    #--------------------------------------------------------------------------
    def __init_console(self):
        theme_config = ConfigFile(
            for_what='console theme', args=self.args,
            arg_name='theme_config',
            file_name='theme.toml',
            default_path=(self.root_path / 'config'),
            find_all=False)

        try:
            config_dict = tomllib.load(open(theme_config.paths[0], 'rb'))
            theme = Theme(config_dict.get('styles'))
        except:
            theme = None

        force_args = dict()
        force_terminal = self.args.get('force_terminal')
        force_interactive = self.args.get('force_interactive')

        if force_terminal is None:
            force_terminal = os.environ.get('CHAIN_FORCE_TERMINAL')

        if force_interactive is None:
            force_interactive = os.environ.get('CHAIN_FORCE_INTERACTIVE')

        if force_terminal is not None:
            force_args['force_terminal'] = bool(int(force_terminal))

        if force_interactive is not None:
            force_args['force_interactive'] = bool(int(force_interactive))

        self.console = Console(theme = theme, **force_args)

    #--------------------------------------------------------------------------
    def __init_flows(self):
        flows_config = ConfigFile(
            for_what='build flow', args=self.args,
            arg_name='flows_config',
            file_name='flows.toml',
            default_path=(self.root_path / 'config'),
            find_all=True)

        all_flows = dict()

        for path_ in flow_config.paths:
            try:
                config_dict = tomllib.load(open(path_, 'rb'))
                file_flows = config_dict.get('flow')

                if file_flows is None:
                    continue

                self.__prepare_flows_config(all_flows, file_flows, path_)
            except Exception as e:
                print_error(
                    f'Loading of flow(s) configuration is failed: {path_}',
                    'BUILD/INIT/FLOWS')
                raise ConfigLoadingError('build flow', path_) from e

        if len(all_flows) == 0:
            print_error(
                'No flows were found in configuration files',
                'BUILD/INIT/FLOWS')
            raise EmptyConfigData('build flow')

        self.__check_flow(all_flows, self.target_flow)
        # TODO: self.__import_flows()

        print_debug(f'Loaded flows: {self.flows.keys()}', 'BUILD/INIT/FLOWS')

    #--------------------------------------------------------------------------
    def __prepare_flows_config(self, all_flows, file_flows, current_path):
        for name in file_flows:
            if not name in all_flows:
                all_flows[name] = file_flows[name]
            else:
                new_params = file_flows[name]
                existing_params = all_flows[name]

                for key in new_params:
                    if key in existing_params:
                        continue

                    existing_params[key] = new_params[key]

            flow = all_flows[name]
            flow['path'] = self.__normalize_path(current_path, flow['path'])

    #--------------------------------------------------------------------------
    def __normalize_path(self, current_path, relative_path):
        assert current_path.is_absolute()

        if os.path.isabs(relative_path):
            return Path(relative_path)

        return (current_path / relative_path).resolve()

    #--------------------------------------------------------------------------
    def __check_flow(self, all_flows, name):
        if not name in all_flows:
            print_error(
                f"Configuration for flow '{name}' does not found",
                'BUILD/INIT/FLOWS')
            raise ConfigDataNotFound('build flow', name)

        params = all_flows[name]
        path_ = params.get('path')

        if path_ is None:
            print_error(
                f"Required configuration key 'path' does not found for "
                f"the flow '{name}'", 'BUILD/INIT/FLOWS')
            raise ConfigKeyNotFound('path', 'build flow', name)

        if not path_.exists():
            print_error(
                f"Path to a SCons tool for the '{name}' flow "
                f"does not exist: {path_}", 'BUILD/INIT/FLOWS')
            raise ToolPathNotExist('build flow', name, path_)

        if 'tools' in params:
            self.__update_tools(name, params['tools'])

        if not name in self.flows:
            self.flows[name] = params

        if 'flows' in params:
            for flow in params['flows']:
                if flow in self.flows:
                    continue
                self.__check_flow(all_flows, flow)

    #--------------------------------------------------------------------------
    def __load_tools_config(self):
        tools_config = ConfigFile(
            for_what='build tools', args=self.args,
            arg_name='tools_config',
            file_name='tools.toml',
            default_path=(self.root_path / 'config'),
            find_all=False)

        try:
            path_ = tools_config.paths[0]
            config_dict = tomllib.load(open(path_, 'rb'))
        except Exception as e:
            print_error(
                f'Loading of tool(s) configuration is failed: {path_}',
                'BUILD/INIT/TOOLS')
            raise ConfigLoadingError('build tools', path_) from e

        tools = config_dict.get('tool')

        if tools is None:
            print_error(
                f'No tools were found in the configuration file: {path_}',
                'BUILD/INIT/FLOWS')
            raise EmptyConfigData('build tools')

        assert path_.is_absolute()

        self.__tools_config_path = path_
        self.__tools_dict = tools

    #--------------------------------------------------------------------------
    def __update_tools(self, flow_name, required_tools):
        for tool_name in required_tools:
            ver_regexp = required_tools[tool_name]
            params = self.__tools_dict.get(tool_name)

            if params is None:
                # TODO: raise: no required tool is found

            tool_path = params.get('path')
            tool_versions = params.get('versions')

            if tool_path is None:
                # TODO: no required key

            if tool_versions is None:
                # TODO: no required key

            ver, loc = self.__find_suitable_tool(ver_regexp, tool_versions)

            if ver is None:
                # TODO: suitable tool version is not found

            path_ = self.__normalize_path(self.__tools_config_path, tool_path)

            if not path_.exists():
                # TODO: error

            self.flows[flow_name][tool_name] = ver

            if not tool_name in self.tools:
                self.tools[tool_name] = params