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
import fnmatch
from pathlib import Path

from rich import print
from rich.console import Console
from rich.theme import Theme

import chain.message
from chain.config import ConfigFinder, ConfigLoader
from chain.message import *
from chain.errors import *
from chain import utils


#==============================================================================
class BuildEnv:
    '''Build environment, gathered from configuration files'''

    init_console_tag = 'INIT/CONSOLE'
    init_tools_tag = 'INIT/TOOLS'
    init_flows_tag = 'INIT/FLOWS'

    #--------------------------------------------------------------------------
    def __init__(self, root_path, args):
        self.__root_path = root_path
        self.__args = vars(args)
        self.__target_flow = self.__args['flow']
        self.__tools = BuildTools()
        self.__flows = BuildFlows(self.__tools)

        message._debug = self.__args['debug']
        message._quiet = self.__args['quiet']

        self.__init_config_finder()
        self.__init_console()
        self.__load_tools_config()
        self.__init_flows()

        self.__tools.check()

        #------------------------------------------------------------
        # summary
        #

        print_debug(f'Used flows: {self.__flows}', 'ENV')
        print_debug(f'Used tools: {self.__tools}', 'ENV')

        print_info(
            f'Build flows are used: {self.__flows.flows()}',
            self.init_flows_tag)

        print_info(
            f"Build tools are used: {self.__tools.versions()}",
            self.init_flows_tag)

    #--------------------------------------------------------------------------
    def root_path(self):
        return self.__root_path

    #--------------------------------------------------------------------------
    def args(self):
        return self.__args

    #--------------------------------------------------------------------------
    def target_flow(self):
        return self.__target_flow

    #--------------------------------------------------------------------------
    def tools(self):
        return self.__tools

    #--------------------------------------------------------------------------
    def flows(self):
        return self.__flows

    #--------------------------------------------------------------------------
    def __init_config_finder(self):
        config_finder = ConfigFinder()

        xdg_config_path = os.environ.get('XDG_CONFIG_HOME')
        user_home_path = os.environ.get('HOME')
        subdir = os.environ.get('CHAIN_CONFIG_DIR_NAME', 'chain')

        config_finder.append_path(
            'project root', self.__args['project_root'], is_dir=True)
        config_finder.append_arg_opt(
            '--config-home', self.__args, is_dir=True, path_prefix=os.getcwd())
        config_finder.append_env_var('CHAIN_CONFIG_HOME', is_dir=True)

        if xdg_config_path is not None:
            config_finder.append_path(
                f"system config dir '$XDG_CONFIG_HOME'",
                Path(xdg_config_path) / subdir,
                is_dir=True, should_exist=False)

        if user_home_path is not None:
            config_finder.append_path(
                "user-specific config dir '$HOME/.config'",
                Path(user_home_path) / '.config' / subdir,
                is_dir=True, should_exist=False)

        config_finder.append_path(
            'default path', self.__root_path / 'config', is_dir=True)

        self.config_finder = config_finder

    #--------------------------------------------------------------------------
    def __init_console(self):
        self.config_finder.set_file_name('theme.toml')
        self.config_finder.stop_on_first(True)
        self.config_finder.prepend_arg_opt(
            name='--theme-config', args=self.__args, path_prefix=os.getcwd(),
            should_exist=True)

        theme = None

        #------------------------------------------------------------
        # finding and loading the config file
        #

        try:
            config_file = self.config_finder.find()
            theme = Theme(ConfigLoader(config_file).load()['styles'])

        except ConfigFinderError as e:
            self.__raise_finder_error(
                'console theme', self.init_console_tag, e)

        except ConfigLoaderError as e:
            self.__raise_loader_error(
                'console theme', self.init_console_tag, e)

        except KeyError:
            print_warning(
                f"No 'styles' section is found in the console theme "
                f"configuration file: {config_file}", self.init_console_tag)
        except:
            raise

        #------------------------------------------------------------
        # set console settings
        #

        force_args = dict()
        force_terminal = self.__args.get('force_terminal')
        force_interactive = self.__args.get('force_interactive')

        if force_terminal is None:
            force_terminal = os.environ.get('CHAIN_FORCE_TERMINAL')

        if force_interactive is None:
            force_interactive = os.environ.get('CHAIN_FORCE_INTERACTIVE')

        if force_terminal is not None:
            force_args['force_terminal'] = bool(int(force_terminal))

        if force_interactive is not None:
            force_args['force_interactive'] = bool(int(force_interactive))

        self.console = Console(theme = theme, **force_args)
        message._console = self.console

        #------------------------------------------------------------
        # print info
        #

        if theme is not None:
            print_info(
                f'Console theme is used from the config file: {config_file}',
                self.init_console_tag)
        else:
            print_info('Default style settings is used', self.init_console_tag)

    #--------------------------------------------------------------------------
    def __load_tools_config(self):
        self.config_finder.set_file_name('tools.toml')
        self.config_finder.stop_on_first(True)

        self.config_finder.delete_first_loc()
        self.config_finder.prepend_arg_opt(
            name='--tools-config', args=self.__args, path_prefix=os.getcwd(),
            should_exist=True)

        #------------------------------------------------------------
        # finding and loading the config file
        #

        try:
            config_file = self.config_finder.find()

            if config_file is None:
                print_error(
                    'Configuration file for building tools was not found',
                    self.init_tools_tag)
                raise ConfigError(ConfigError.Kind.FILE_NOT_FOUND)

            config_loader = ConfigLoader(config_file)

            self.__tools_dict = config_loader.load()['tool']
            self.__tools_config_path = config_file

        except ConfigFinderError as e:
            self.__raise_finder_error(
                'tools', self.init_tools_tag, e,
                ConfigError(ConfigError.Kind.FINDING_ERROR))

        except ConfigLoaderError as e:
            self.__raise_loader_error(
                'tools', self.init_tools_tag, e,
                ConfigError(ConfigError.Kind.LOADING_ERROR, path=config_file))

        except KeyError:
            print_error(
                f"No 'tool' section is found in the tools "
                f"configuration file: {config_file}", self.init_tools_tag)
            raise ConfigError(
                ConfigError.Kind.NO_ENTITY_DATA,
                entry='tool', path=config_file)

        #------------------------------------------------------------
        # print info
        #

        print_debug(
            f"Tools configuration is loaded from '{config_file}': "
            f"{self.__tools_dict}", 'CONFIG')
        print_info(
            f"Tools configuration is used from the file: {config_file}",
            self.init_tools_tag)

    #--------------------------------------------------------------------------
    def __init_flows(self):
        single_config = self.__args['single_flows_config']

        self.config_finder.set_file_name('flows.toml')
        self.config_finder.stop_on_first(single_config)

        self.config_finder.delete_first_loc()
        self.config_finder.prepend_arg_opt(
            name='--flows-config', args=self.__args, path_prefix=os.getcwd(),
            should_exist=True)

        #------------------------------------------------------------
        # finding the config file(s)
        #

        config_files = self.config_finder.find()

        if config_files is None:
            print_error(
                'No configuration file for building flows is found',
                self.init_flows_tag)
            raise ConfigError(ConfigError.Kind.FILE_NOT_FOUND)

        if single_config:
            config_files = [config_files]

        all_flows = dict()

        #------------------------------------------------------------
        # loading the config file(s)
        #

        try:
            for path in config_files:
                config_dict = ConfigLoader(path).load()
                file_flows = config_dict.get('flow')

                if file_flows is None:
                    continue

                self.__merge_flows_params(all_flows, file_flows, path.parent)

        except ConfigFinderError as e:
            self.__raise_finder_error(
                'flows', self.init_flows_tag, e,
                ConfigError(ConfigError.Kind.FINDING_ERROR))

        except ConfigLoaderError as e:
            self.__raise_loader_error(
                'flows', self.init_flows_tag, e,
                ConfigError(ConfigError.Kind.LOADING_ERROR, path=path))

        #------------------------------------------------------------
        # processing the target flow (and dependencies) config
        #

        if len(all_flows) == 0:
            print_error(
                'No flow is found in configuration files',
                self.init_flows_tag)
            raise ConfigError(
                ConfigError.Kind.NO_ENTITY_DATA,
                entry='flow', path=config_file)

        self.__check_flow(all_flows, self.__target_flow)

    #--------------------------------------------------------------------------
    def __merge_flows_params(self, all_flows, file_flows, current_path):
        for name in file_flows:
            if not name in all_flows:
                all_flows[name] = file_flows[name]
                params = all_flows[name]

                if 'path' in params:
                    params['path'] = utils.normalize_path(
                        current_path, params['path'])

                print_debug(
                    f"New flow '{name}' is found in the file '{current_path}' "
                    f"with parameters: {params}", 'CONFIG')
            else:
                new_params = file_flows[name]
                existing_params = all_flows[name]

                for key in new_params:
                    if key in existing_params:
                        continue

                    if key == 'path':
                        existing_params['path'] = utils.normalize_path(
                            current_path, new_params['path'])
                    else:
                        existing_params[key] = new_params[key]

                    print_debug(
                        f"Add parameter '{key} = {new_params[key]}' "
                        f"to the flow '{name}' from file: {current_path}",
                        'CONFIG')

    #--------------------------------------------------------------------------
    def __check_flow(self, all_flows, name):
        try:
            flow_params = all_flows[name]
            print_debug(f"Used flow '{name}': {flow_params}", 'ENV')
        except KeyError:
            print_error(
                f"Configuration for the flow '{name}' was not found",
                self.init_flows_tag)
            raise ConfigError(
                ConfigError.Kind.NO_ENTITY_DATA, entry=f'flow.{name}')

        #------------------------------------------------------------
        # checking the 'path' parameter
        #

        path = flow_params.get('path')

        if path is None:
            print_error(
                f"Required configuration key 'path' was not found for "
                f"the flow '{name}'", self.init_flows_tag)
            raise ConfigError(
                ConfigError.Kind.NO_CONFIG_PARAM, param='path',
                entry=f'flow.{name}')

        if not path.exists():
            print_error(
                f"Path to a SCons tools for the flow '{name}' "
                f"does not exist: {path}",
                self.init_flows_tag)
            raise PathError(path, PathError.Kind.NOT_EXIST)

        #------------------------------------------------------------
        # processing configurations of required tools and
        # flow dependencies
        #

        self.__flows.add(name, path)

        if 'tools' in flow_params:
            self.__update_tools(name, flow_params['tools'])

        if 'flows' in flow_params:
            for flow in flow_params['flows']:
                if self.__flows.exists(flow):
                    continue
                self.__check_flow(all_flows, flow)

    #--------------------------------------------------------------------------
    def __update_tools(self, flow_name, required_tools):
        print_debug(
            f"Required tools for the flow '{flow_name}': {required_tools}",
            'ENV')

        for tool_name in required_tools:
            required_versions = required_tools[tool_name]
            tool_params = self.__tools_dict.get(tool_name)

            if type(required_versions) is not list:
                required_versions = [required_versions]

            #------------------------------------------------------------
            # checking the tool's config parameters
            #

            if tool_params is None:
                print_error(
                    f"No required tool '{tool_name}' is found "
                    f"for the flow '{flow_name}'",
                    self.init_flows_tag)
                raise BuildEnvError(
                    BuildEnvError.Kind.TOOL_NOT_FOUND, tool=tool_name)

            tool_path = tool_params.get('path')
            tool_versions = tool_params.get('versions')

            if tool_path is None:
                print_error(
                    f"Required configuration key 'path' was not found for "
                    f"the tool '{tool_name}'",
                    self.init_flows_tag)
                raise ConfigError(
                    ConfigError.Kind.NO_CONFIG_PARAM, param='path',
                    entry=f'tool.{tool_name}')

            if tool_versions is None:
                print_error(
                    f"Required configuration key 'version' was not found for "
                    f"the tool '{tool_name}'",
                    self.init_flows_tag)
                raise ConfigError(
                    ConfigError.Kind.NO_CONFIG_PARAM, param='version',
                    entry=f'tool.{tool_name}')

            #------------------------------------------------------------
            # select appropriate tool's version
            #

            available_versions = list(tool_versions.keys())

            tool_ver = self.__select_tool_version(
                required_versions, available_versions)

            if tool_ver is None:
                print_error(
                    f"Requested version(s) '{required_versions}' "
                    f"for the tool '{tool_name}' was not found "
                    f"in available: {available_versions}",
                    self.init_flows_tag)
                raise BuildEnvError(
                    BuildEnvError.Kind.TOOL_VERSION,
                    tool=tool_name, version=required_versions)

            #------------------------------------------------------------
            # normalize and check the tool's path
            #

            path = utils.normalize_path(
                self.__tools_config_path.parent, tool_path)

            if not path.exists():
                print_error(
                    f"Path to a SCons tools for the build tool '{tool_name}' "
                    f"does not exist: {path}",
                    self.init_flows_tag)
                raise PathError(path, PathError.Kind.NOT_EXIST)

            print_debug(
                f"Selected version of the tool '{tool_name}' for the flow "
                f"'{flow_name}' is '{tool_ver}'", 'ENV')

            #------------------------------------------------------------
            # add tool to the environment and to the flow
            #

            self.__tools.add(tool_name, tool_params, tool_ver)
            self.__flows.add_tool(flow_name, tool_name, tool_ver)

    #--------------------------------------------------------------------------
    def __select_tool_version(self, required, available):
        for pat in required:
            for name in available:
                if fnmatch.fnmatch(name, pat) is not None:
                    return name

        return None

    #--------------------------------------------------------------------------
    def __raise_finder_error(
            self, for_what, tag, catched_exception, raise_exception=None):
        msg = (f"An error occurred while searching of the {for_what} "
               f"configuration file in the {str(catched_exception.loc)}")
        utils.wrong(msg, tag, raise_exception)

    #--------------------------------------------------------------------------
    def __raise_loader_error(
            self, for_what, tag, catched_exception, raise_exception=None):
        msg = (f"An error occurred while loading of the tools "
                f"configuration due to {str(catched_exception)}")
        utils.wrong(msg, tag, raise_exception)


#==============================================================================
class BuildTools:
    #--------------------------------------------------------------------------
    def __init__(self):
        self.__tools = dict()

    #--------------------------------------------------------------------------
    def __str__(self):
        return f'{self.__tools}'

    #--------------------------------------------------------------------------
    def exists(self, name):
        return name in self.__tools

    #--------------------------------------------------------------------------
    def add(self, name, params, version):
        if not self.exists(name):
            self.__tools[name] = params
        else:
            version_dict = self.__tools[name]['versions']

            if not version in version_dict:
                version_dict[version] = params['versions'][version]

    #--------------------------------------------------------------------------
    def names(self):
        return list(self.__tools.keys())

    #--------------------------------------------------------------------------
    def versions(self, name=None):
        tool_versions = lambda nm: [v for v in self.__tools[nm]['versions']]

        if name is None:
            return {nm: tool_versions(nm) for nm in self.__tools}
        else:
            return tool_versions(name)

    #--------------------------------------------------------------------------
    def get_scons_tool_path(self, name):
        return self.__tools[name]['path']

    #--------------------------------------------------------------------------
    def get_location(self, name, version):
        data = self.__tools[name]['versions'][version].split(':')
        where = data[0]
        loc = data[1]

        if where == 'docker':
            loc_key = 'service'
        elif where == 'path':
            loc_key = 'path'
        else:
            # TODO: error
            pass

        return {'where': where_tuple[0], loc_key: loc}

    #--------------------------------------------------------------------------
    def get_path(self, name, version):
        loc = self.get_location(name, version)

        if loc['where'] == 'docker':
            return None
        else:
            return loc['path']

    #--------------------------------------------------------------------------
    def get_docker_service(self, name, version):
        loc = self.get_location(name, version)

        if loc['where'] == 'path':
            return None
        else:
            return loc['service']

    #--------------------------------------------------------------------------
    def check(self):
        # TODO: load and try to run all tools
        pass


#==============================================================================
class BuildFlows:
    #--------------------------------------------------------------------------
    def __init__(self, tools):
        self.__flows = dict()
        self.__tools = tools

    #--------------------------------------------------------------------------
    def __str__(self):
        return f'{self.__flows}'

    #--------------------------------------------------------------------------
    def exists(self, name):
        return name in self.__flows

    #--------------------------------------------------------------------------
    def add(self, name, path):
        if not self.exists(name):
            self.__flows[name] = {'path': path}

    #--------------------------------------------------------------------------
    def add_tool(self, flow_name, tool_name, tool_version):
        flow = self.__flows[flow_name]

        if not 'tools' in flow:
            flow['tools'] = dict()

        tools = flow['tools']

        if tool_name in tools:
            if tools[tool_name] == tool_version:
                return

            # TODO: version conflict error

        tools[tool_name] = tool_version

    #--------------------------------------------------------------------------
    def flows(self):
        return list(self.__flows.keys())

    #--------------------------------------------------------------------------
    def tools(self):
        return self.__tools

    #--------------------------------------------------------------------------
    def get_scons_tool_path(self, name):
        return self.__flows[name]['path']

    #--------------------------------------------------------------------------
    def check(self):
        # TODO
        pass
