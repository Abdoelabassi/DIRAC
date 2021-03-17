#!/usr/bin/env python

"""
Script that emulates the behaviour of a shell to edit the CS config.
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

__RCSID__ = "$Id$"

import sys

from DIRAC.Core.Utilities.DIRACScript import DIRACScript

# Invariants:
# * root does not end with "/" or root is "/"
# * root starts with "/"


@DIRACScript()
def main(self):
  self.parseCommandLine()
  from DIRAC.ConfigurationSystem.Client.CSShellCLI import CSShellCLI
  shell = CSShellCLI()
  shell.cmdloop()


if __name__ == "__main__":
  main()  # pylint: disable=no-value-for-parameter
