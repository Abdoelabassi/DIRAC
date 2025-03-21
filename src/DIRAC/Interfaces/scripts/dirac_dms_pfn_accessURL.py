#!/usr/bin/env python
########################################################################
# File :    dirac-dms-pfn-accessURL
# Author  : Stuart Paterson
########################################################################
"""
Retrieve an access URL for a PFN given a valid DIRAC SE
"""
import DIRAC
from DIRAC.Core.Utilities.DIRACScript import DIRACScript as Script


@Script()
def main():
    # Registering arguments will automatically add their description to the help menu
    Script.registerArgument("PFN:      Physical File Name or file containing PFNs")
    Script.registerArgument("SE:       Valid DIRAC SE")
    _, args = Script.parseCommandLine(ignoreErrors=True)

    if len(args) > 2:
        print("Only one PFN SE pair will be considered")

    from DIRAC.Interfaces.API.Dirac import Dirac

    dirac = Dirac()
    exitCode = 0

    pfn = args[0]
    seName = args[1]
    try:
        with open(pfn, "r") as f:
            pfns = f.read().splitlines()
    except Exception:
        pfns = [pfn]

    for pfn in pfns:
        result = dirac.getPhysicalFileAccessURL(pfn, seName, printOutput=True)
        if not result["OK"]:
            print("ERROR: ", result["Message"])
            exitCode = 2

    DIRAC.exit(exitCode)


if __name__ == "__main__":
    main()
