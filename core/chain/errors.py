#******************************************************************************
#
#  Project: Build system for FPGA/ASIC
#
#  Description: Exception classes
#
#  Copyright (c) 2024 Anton Polstyankin <mail@pavhw.org>
#
#******************************************************************************

#******************************************************************************
# Common
#

#==============================================================================
class RelativeEnvPath(Exception):
    '''Relative path is in environment variable, but absolute is expected'''

    def __init__(self, env_name, path_):
        self.env_name = env_name
        self.path_ = path_

    def __str__(self):
        return f"path in '${self.env_name}' is relative: {self.path_}"


#******************************************************************************
# Environment configuration
#

#==============================================================================
class ConfigFileNotFound(Exception):
    '''Configuration file does not found during searching in known locations'''

    def __init__(self, for_what):
        self.for_what = for_what

    def __str__(self):
        return f"for {self.for_what}"


#==============================================================================
class ConfigPathError(Exception):
    '''Path to the config file or to the searching location is incorrect'''

    class Kind(Enum):
        NOT_DIR = auto()
        NOT_FILE = auto()
        NOT_EXISTS = auto()

    def __init__(self, path_, kind):
        self.path_ = path_
        self.kind = kind

    def __str__(self):
        if self.kind == self.Kind.NOT_DIR:
            return f"not a directory: '{self.path_}'"
        elif self.kind == self.Kind.NOT_FILE:
            return f"not a file: '{self.path_}'"
        elif self.kind == self.Kind.NOT_EXISTS:
            return f"does not exist: '{self.path_}'"


#==============================================================================
class ConfigLoadingError(Exception):
    '''Reading error of the config file or incorrect format of it'''

    def __init__(self, for_what, path_):
        self.for_what = for_what
        self.path_ = path_

    def __str__(self):
        return f"for {self.for_what} from file: {self.path_}"


#==============================================================================
class ConfigDataNotFound(Exception):
    '''Required data is not found in the config file'''

    def __init__(self, for_what, name):
        self.for_what = for_what
        self.name = name

    def __str__(self):
        return f"for {self.for_what} '{self.name}'"


#==============================================================================
class ConfigKeyNotFound(Exception):
    '''Required key does not found in configuration data'''

    def __init__(self, key, for_what, name):
        self.key = key
        self.for_what = for_what
        self.name = name

    def __str__(self):
        return f"'{self.key}' for {self.for_what} '{name}'"


#==============================================================================
class EmptyConfigData(Exception):
    '''No data for specified entity kind'''

    def __init__(self, for_what):
        self.for_what = for_what

    def __str__(self):
        return f"for {self.for_what}"


#==============================================================================
class ToolPathNotExist(Exception):
    '''Path to the SCons tool (for build tools or for flows) is incorrect'''

    def __init__(self, for_what, name, path_):
        self.for_what = for_what
        self.name = name
        self.path_ = path_

    def __str__(self):
        return f"for {self.for_what} '{self.name}': {self.path_}"
