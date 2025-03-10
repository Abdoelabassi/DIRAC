from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os
import re
import jwt
import six
import stat
import time
import json
import datetime

from DIRAC import S_OK, S_ERROR
from DIRAC.Core.Utilities import DErrno
from DIRAC.ConfigurationSystem.Client.Helpers import Registry
from DIRAC.Resources.IdProvider.IdProviderFactory import IdProviderFactory

from authlib.oauth2.rfc6749.util import scope_to_list
from authlib.oauth2.rfc6749.wrappers import OAuth2Token as _OAuth2Token

BEARER_TOKEN_ENV = "BEARER_TOKEN"
BEARER_TOKEN_FILE_ENV = "BEARER_TOKEN_FILE"


def getTokenFileLocation(fileName=None):
    """Research token file location. Use the bearer token discovery protocol
    defined by the WLCG (https://doi.org/10.5281/zenodo.3937438) to find one.

    :param str fileName: file name to dump to

    :return: str
    """
    if fileName:
        return fileName
    if os.environ.get(BEARER_TOKEN_FILE_ENV):
        return os.environ[BEARER_TOKEN_FILE_ENV]
    elif os.environ.get("XDG_RUNTIME_DIR"):
        return "%s/bt_u%s" % (os.environ["XDG_RUNTIME_DIR"], os.getuid())
    else:
        return "/tmp/bt_u%s" % os.getuid()


def getLocalTokenDict(location=None):
    """Search local token. Use the bearer token discovery protocol
    defined by the WLCG (https://doi.org/10.5281/zenodo.3937438) to find one.

    :param str location: token file path

    :return: S_OK(dict)/S_ERROR()
    """
    result = readTokenFromEnv()
    return result if result["OK"] and result["Value"] else readTokenFromFile(location)


def readTokenFromEnv():
    """Read token from an environ variable

    :return: S_OK(dict or None)
    """
    token = os.environ.get(BEARER_TOKEN_ENV, "").strip()
    return S_OK(OAuth2Token(token) if token else None)


def readTokenFromFile(fileName=None):
    """Read token from a file

    :param str fileName: filename to read

    :return: S_OK(dict or None)/S_ERROR()
    """
    location = getTokenFileLocation(fileName)
    try:
        with open(location, "rt") as f:
            token = f.read().strip()
    except IOError as e:
        return S_ERROR(DErrno.EOF, "Can't open %s token file.\n%s" % (location, repr(e)))
    return S_OK(OAuth2Token(token) if token else None)


def writeToTokenFile(tokenContents, fileName):
    """Write a token string to file

    :param str tokenContents: token as string
    :param str fileName: filename to dump to

    :return: S_OK(str)/S_ERROR()
    """
    location = getTokenFileLocation(fileName)
    try:
        with open(location, "wt") as fd:
            fd.write(tokenContents)
    except Exception as e:
        return S_ERROR(DErrno.EWF, " %s: %s" % (location, repr(e)))
    try:
        os.chmod(location, stat.S_IRUSR | stat.S_IWUSR)
    except Exception as e:
        return S_ERROR(DErrno.ESPF, "%s: %s" % (location, repr(e)))
    return S_OK(location)


def writeTokenDictToTokenFile(tokenDict, fileName=None):
    """Write a token dict to file

    :param dict tokenDict: dict object to dump to file
    :param str fileName: filename to dump to

    :return: S_OK(str)/S_ERROR()
    """
    fileName = getTokenFileLocation(fileName)
    if not isinstance(tokenDict, dict):
        return S_ERROR("Token is not a dictionary")
    return writeToTokenFile(json.dumps(tokenDict), fileName)


class OAuth2Token(_OAuth2Token):
    """Implementation of a Token object"""

    def __init__(self, params=None, **kwargs):
        """Constructor"""
        if isinstance(params, bytes):
            params = params.decode()
        if isinstance(params, six.string_types):
            # Is params a JWT?
            params = params.strip()
            if re.match(r"^[A-Za-z0-9-_=]+\.[A-Za-z0-9-_=]+\.?[A-Za-z0-9-_.+/=]*$", params):
                params = dict(access_token=params)
            else:
                params = json.loads(params)

        kwargs.update(params or {})
        kwargs["issued_at"] = kwargs.get("issued_at", kwargs.get("iat"))
        kwargs["expires_at"] = kwargs.get("expires_at", kwargs.get("exp"))
        if not kwargs.get("expires_at") and kwargs.get("access_token"):
            # Get access token expires_at claim
            kwargs["expires_at"] = self.get_claim("exp")
        super(OAuth2Token, self).__init__(kwargs)

    def check_client(self, client):
        """A method to check if this token is issued to the given client.

        :param client: client object

        :return: bool
        """
        return self.get("client_id", self.get("azp")) == client.client_id

    def get_scope(self):
        """A method to get scope of the authorization code.

        :return: str
        """
        return self.get("scope")

    def get_expires_in(self):
        """A method to get the ``expires_in`` value of the token.

        :return: int
        """
        return int(self.get("expires_in"))

    def is_expired(self):
        """A method to define if this token is expired.

        :return: bool
        """
        if self.get("expires_at"):
            return int(self.get("expires_at")) < time.time()
        elif self.get("issued_at") and self.get("expires_in"):
            return int(self.get("issued_at")) + int(self.get("expires_in")) < time.time()
        else:
            exp = self.get_payload().get("exp")
            return int(exp) < time.time() if exp else True

    @property
    def scopes(self):
        """Get tokens scopes

        :return: list
        """
        return scope_to_list(self.get("scope", ""))

    @property
    def groups(self):
        """Get tokens groups

        :return: list
        """
        return [s.split(":")[1] for s in self.scopes if s.startswith("g:") and s.split(":")[1]]

    def get_payload(self, token_type="access_token"):
        """Decode token

        :param str token_type: token type

        :return: dict
        """
        if not self.get(token_type):
            return {}
        return jwt.decode(
            self.get(token_type),
            options=dict(verify_signature=False, verify_exp=False, verify_aud=False, verify_nbf=False),
        )

    def get_claim(self, claim, token_type="access_token"):
        """Get token claim without verification

        :param str attr: attribute
        :param str token_type: token type

        :return: str
        """
        return self.get_payload(token_type).get(claim)

    def dump_to_string(self):
        """Dump token dictionary to sting

        :return: str
        """
        return json.dumps(dict(self))

    def getInfoAsString(self):
        """Return information about token as string

        :return: str
        """
        result = IdProviderFactory().getIdProviderForToken(self.get("access_token"))
        if not result["OK"]:
            return "Cannot load provider: %s" % result["Message"]
        cli = result["Value"]
        cli.token = self.copy()
        result = cli.verifyToken()
        if not result["OK"]:
            return result["Message"]
        payload = result["Value"]
        result = cli.researchGroup(payload)
        if not result["OK"]:
            return result["Message"]
        credDict = result["Value"]
        result = Registry.getUsernameForDN(credDict["DN"])
        if not result["OK"]:
            return result["Message"]
        credDict["username"] = result["Value"]
        if credDict.get("group"):
            credDict["properties"] = Registry.getPropertiesForGroup(credDict["group"])
        payload.update(credDict)
        return self.__formatTokenInfoAsString(payload)

    def __formatTokenInfoAsString(self, infoDict):
        """Convert a token infoDict into a string

        :param dict infoDict: info

        :return: str
        """
        secsLeft = int(infoDict["exp"]) - time.time()
        strTimeleft = datetime.datetime.fromtimestamp(secsLeft).strftime("%I:%M:%S")
        leftAlign = 13
        contentList = []
        contentList.append("%s: %s" % ("subject".ljust(leftAlign), infoDict["sub"]))
        contentList.append("%s: %s" % ("issuer".ljust(leftAlign), infoDict["iss"]))
        contentList.append("%s: %s" % ("timeleft".ljust(leftAlign), strTimeleft))
        contentList.append("%s: %s" % ("username".ljust(leftAlign), infoDict["username"]))
        if infoDict.get("group"):
            contentList.append("%s: %s" % ("DIRAC group".ljust(leftAlign), infoDict["group"]))
        if infoDict.get("properties"):
            contentList.append("%s: %s" % ("properties".ljust(leftAlign), ", ".join(infoDict["properties"])))
        return "\n".join(contentList)
