#!/usr/bin/env python
"""
Stop DIRAC component using runsvctrl utility
"""
from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

from DIRAC.Core.Utilities.DIRACScript import DIRACScript as Script


@Script()
def main():
    Script.disableCS()
    # Registering arguments will automatically add their description to the help menu
    Script.registerArgument(
        " System:  Name of the system for the component (default *: all)", mandatory=False, default="*"
    )
    Script.registerArgument(
        (
            "Service: Name of the particular component (default *: all)",
            "Agent:   Name of the particular component (default *: all)",
        ),
        mandatory=False,
        default="*",
    )
    _, args = Script.parseCommandLine()
    system, component = Script.getPositionalArgs(group=True)

    from DIRAC.FrameworkSystem.Client.ComponentInstaller import gComponentInstaller

    __RCSID__ = "$Id$"

    if len(args) > 2:
        Script.showHelp(exitCode=1)

    if system != "*":
        if len(args) > 1:
            component = args[1]

    gComponentInstaller.exitOnError = True

    result = gComponentInstaller.runsvctrlComponent(system, component, "d")
    if not result["OK"]:
        print("ERROR:", result["Message"])
        exit(-1)

    gComponentInstaller.printStartupStatus(result["Value"])


if __name__ == "__main__":
    main()
