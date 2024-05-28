#******************************************************************************
#
#  Project: Build system for FPGA/ASIC
#
#  Description: Exception classes
#
#  Copyright (c) 2024 Anton Polstyankin <mail@pavhw.org>
#
#******************************************************************************

from enum import Enum, auto


#==============================================================================
class ChainException(Exception):
    pass


#******************************************************************************
# Common
#

#==============================================================================
class PathError(ChainException):
    class Kind(Enum):
        NOT_ABS = auto()
        NOT_DIR = auto()
        NOT_FILE = auto()
        NOT_EXIST = auto()

    def __init__(self, path, kind):
        self.path = path
        self.kind = kind

    def __str__(self):
        if self.kind == self.Kind.NOT_ABS:
            msg = 'is not absolute'
        elif self.kind == self.Kind.NOT_DIR:
            msg = 'is not a directory'
        elif self.kind == self.Kind.NOT_FILE:
            msg = 'is not a file'
        elif self.kind == self.Kind.NOT_EXIST:
            msg = 'does not exist'
        else:
            msg = 'unknown kind of the error'

        return f"{msg}: {self.path}"


#==============================================================================
class ConfigError(ChainException):
    class Kind(Enum):
        FINDING_ERROR = auto()
        FILE_NOT_FOUND = auto()
        LOADING_ERROR = auto()
        NO_ENTITY_DATA = auto()
        PARAMS_NOT_FOUND = auto()
        NO_CONFIG_PARAM = auto()

    def __init__(self, kind, **kw):
        self.kind = kind
        self.kw = kw

    def __str__(self):
        if 'path' in self.kw:
            file_path_msg = " (in file: {self.kw['path']})"
        else:
            file_path_msg = ''

        match self.kind:
            case self.Kind.FINDING_ERROR:
                return "config file finding is failed"

            case self.Kind.FILE_NOT_FOUND:
                return "config file does not found"

            case self.Kind.LOADING_ERROR:
                return f"loading error of the config file: {self.kw['path']}"

            case self.Kind.NO_ENTITY_DATA:
                return (f"entry key '{self.kw['entry']}' does not found "
                        f"or empty{file_path_msg}")

            case self.Kind.PARAMS_NOT_FOUND:
                return (f"no parameters is found in the entry"
                        f"'{self.kw['entry']}'{file_path_msg}")

            case self.Kind.NO_CONFIG_PARAM:
                return (f"required parameter '{self.kw['param']}' "
                        f"does not found in the entry '{self.kw['entry']}'"
                        f"{file_path_msg}")

        return 'unknown kind of the error'


#==============================================================================
class ConfigLoaderError(ChainException):
    class Kind(Enum):
        OPEN = auto()
        LOAD = auto()
        FORMAT = auto()

    def __init__(self, kind, **kw):
        self.kind = kind
        self.kw = kw

    def __str__(self):
        match self.kind:
            case self.Kind.OPEN:
                return f"opening error of the file '{self.kw['path']}'"
            case self.Kind.LOAD:
                return f"incorrect format of the file '{self.kw['path']}'"
            case self.Kind.FORMAT:
                return f"unsupported config format '{self.kw['format']}'"

        return 'unknown kind of the error'


#==============================================================================
class ConfigFinderError(ChainException):
    def __init__(self, loc):
        self.loc = loc

    def __str__(self):
        return 'searching in the ' + str(self.loc)


#==============================================================================
class BuildEnvError(ChainException):
    class Kind(Enum):
        TOOL_NOT_FOUND = auto()
        TOOL_VERSION = auto()

    def __init__(self, kind, **kw):
        self.kind = kind
        self.kw = kw

    def __str__(self):
        if self.kind == self.Kind.TOOL_NOT_FOUND:
            msg = f"required build tool '{kw['tool']}' was not found"
        elif self.kind == self.Kind.TOOL_VERSION:
            msg = (f"requested version(s) of the tool '{kw['tool']}' "
                   f"was not found: {kw['version']}")
        else:
            msg = 'unknown kind of the error'

        return f"{msg}: {self.path}"
