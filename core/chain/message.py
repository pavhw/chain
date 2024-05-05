#******************************************************************************
#
#  Project: Build system for FPGA/ASIC
#
#  Description: Messaging utilities
#
#  Copyright (c) 2024 Anton Polstyankin <mail@pavhw.org>
#
#******************************************************************************

import os


#******************************************************************************
# Globals
#

_console = None
_debug = False
_quiet = False


#******************************************************************************
# Functions
#

#------------------------------------------------------------------------------
def print_info(msg, tag):
    if not _quiet:
        _print_message('info', msg, tag)

#------------------------------------------------------------------------------
def print_warning(msg, tag):
    _print_message('warning', msg, tag)

#------------------------------------------------------------------------------
def print_error(msg, tag):
    _print_message('error', msg, tag)

#------------------------------------------------------------------------------
def print_debug(msg, tag):
    if _debug:
        _print_message('debug', msg, tag)


#******************************************************************************
# Internal
#

#------------------------------------------------------------------------------
def _get_msg_tag(tag):
    if (tag is None) or (len(tag.strip()) == 0):
        return ''
    else:
        return '[' + tag + '] '

#------------------------------------------------------------------------------
def _print_message(severity, msg, tag):
    msg = f'{severity.upper()}: ' + _get_msg_tag(tag) + msg

    if _console is not None:
        _console.print(f'[{severity}]{msg}[/{severity}]')
    else:
        print(msg)
