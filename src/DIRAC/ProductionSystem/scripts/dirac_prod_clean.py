#!/usr/bin/env python
"""
Clean a given production
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

__RCSID__ = "$Id$"

import DIRAC
from DIRAC.Core.Utilities.DIRACScript import DIRACScript as Script


@Script()
def main():
    # Registering arguments will automatically add their description to the help menu
    Script.registerArgument("prodID: Production ID")
    _, args = Script.parseCommandLine()

    from DIRAC.ProductionSystem.Client.ProductionClient import ProductionClient

    # get arguments
    prodID = args[0]

    res = ProductionClient().setProductionStatus(prodID, "Cleaned")
    if not res["OK"]:
        DIRAC.gLogger.error(res["Message"])
        DIRAC.exit(1)

    DIRAC.gLogger.notice("Production %s successully cleaned" % prodID)
    DIRAC.exit(0)


if __name__ == "__main__":
    main()
