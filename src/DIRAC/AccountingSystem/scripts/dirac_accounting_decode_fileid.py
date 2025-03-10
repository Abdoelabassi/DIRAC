#!/usr/bin/env python
########################################################################
# File :    dirac_accounting_decode_fileid
# Author :  Adria Casajus
########################################################################
"""
Decode Accounting plot URLs
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

__RCSID__ = "$Id$"

import sys
import pprint
from urllib import parse

from DIRAC import gLogger
from DIRAC.Core.Utilities.DIRACScript import DIRACScript as Script


@Script()
def main():
    from DIRAC.Core.Utilities.Plotting.FileCoding import extractRequestFromFileId

    Script.registerArgument(["URL: encoded URL of a DIRAC Accounting plot"])

    _, fileIds = Script.parseCommandLine()

    for fileId in fileIds:
        # Try to find if it's a url
        parseRes = parse.urlparse(fileId)
        if parseRes.query:
            queryRes = parse.parse_qs(parseRes.query)
            if "file" in queryRes:
                fileId = queryRes["file"][0]
        # Decode
        result = extractRequestFromFileId(fileId)
        if not result["OK"]:
            gLogger.error("Could not decode fileId", "'%s', error was %s" % (fileId, result["Message"]))
            sys.exit(1)
        gLogger.notice("Decode for '%s' is:\n%s" % (fileId, pprint.pformat(result["Value"])))

    sys.exit(0)


if __name__ == "__main__":
    main()
