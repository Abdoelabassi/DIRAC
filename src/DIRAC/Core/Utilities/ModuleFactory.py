########################################################################
# File :    ModuleFactory.py
# Author :  Stuart Paterson
########################################################################
"""  The Module Factory instantiates a given Module based on a given input
     string and set of arguments to be passed.  This allows for VO specific
     module utilities to be used in various contexts.
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

__RCSID__ = "$Id$"

from DIRAC import S_OK, S_ERROR, gLogger


class ModuleFactory(object):

    #############################################################################
    def __init__(self):
        """Standard constructor"""
        self.log = gLogger

    #############################################################################
    def getModule(self, importString, argumentsDict):
        """This method returns the Module instance given the import string and
        arguments dictionary.
        """
        try:
            moduleName = importString.split(".")[-1]
            modulePath = importString.replace(".%s" % (moduleName), "")
            importModule = __import__("%s.%s" % (modulePath, moduleName), globals(), locals(), [moduleName])
        except Exception as x:
            msg = "ModuleFactory could not import %s.%s" % (modulePath, moduleName)
            self.log.warn(x)
            self.log.warn(msg)
            return S_ERROR(msg)

        try:
            # FIXME: should we use imp module?
            moduleStr = "importModule.%s(argumentsDict)" % (moduleName)
            moduleInstance = eval(moduleStr)
        except Exception as x:
            msg = "ModuleFactory could not instantiate %s()" % (moduleName)
            self.log.warn(x)
            self.log.warn(msg)
            return S_ERROR(msg)

        return S_OK(moduleInstance)


# EOF#EOF#EOF#EOF#EOF#EOF#EOF#EOF#EOF#EOF#EOF#EOF#EOF#EOF#EOF#EOF#EOF#EOF#EOF#
