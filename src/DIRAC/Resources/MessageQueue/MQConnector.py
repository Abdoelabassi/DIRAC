"""
Class for management of MQ communication
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from DIRAC import gLogger, S_OK, S_ERROR
from DIRAC.Core.Utilities.ObjectLoader import ObjectLoader
from DIRAC.Core.Utilities.DErrno import EMQUKN

__RCSID__ = "$Id$"


def createMQConnector(parameters=None):
    """Function creates and returns the MQConnector object based.

    Args:
      parameters(dict): set of parameters for the MQConnector constructor,
        it should also contain pair 'MQType':mqType, where
        mqType is a string used as a prefix for the specialized MQConnector
        class.
    Returns:
      S_OK or S_ERROR: with loaded specialized class of MQConnector.
    """
    mqType = parameters.get("MQType", None)
    result = getMQConnectorClass(mqType=mqType)
    if not result["OK"]:
        gLogger.error("Failed to getMQConnectorClass:", "%s" % (result["Message"]))
        return result
    ceClass = result["Value"]
    try:
        mqConnector = ceClass(parameters)
        if not result["OK"]:
            return result
    except Exception as exc:  # pylint: disable=broad-except
        gLogger.exception("Could not instantiate MQConnector object", lExcInfo=exc)
        return S_ERROR(EMQUKN, "")
    return S_OK(mqConnector)


def getMQConnectorClass(mqType):
    """Function loads the specialized MQConnector class based on mqType.
        It is assumed that MQConnector has a name in the format mqTypeMQConnector
        e.g. if StompMQConnector.

    Args:
      mqType(str): prefix of specialized class name e.g. Stomp.
    Returns:
      S_OK or S_ERROR: with loaded specialized class of MQConnector.
    """
    subClassName = mqType + "MQConnector"
    result = ObjectLoader().loadObject("Resources.MessageQueue.%s" % subClassName)
    if not result["OK"]:
        gLogger.error("Failed to load object", "%s: %s" % (subClassName, result["Message"]))
    return result


class MQConnectionError(Exception):
    """specialized exception"""

    pass


class MQConnector(object):
    """
    Class for management of message queue connections
    """

    def __init__(self, parameters=None):
        """Standard constructor"""
        if not parameters:
            parameters = {}
        self.parameters = parameters

    def setupConnection(self, parameters=None):
        """
        :param dict parameters: dictionary with additional MQ parameters if any
        :return: S_OK/S_ERROR
        """
        raise NotImplementedError("This method should be implemented by child class")

    def put(self, message, parameters=None):
        """Send message to a MQ server

        :param message: any json encodable structure
        :return: S_OK/S_ERROR
        """
        raise NotImplementedError("This method should be implemented by child class")

    def connect(self, parameters=None):
        """
        :param dict parameters: dictionary with additional parameters if any
        :return: S_OK/S_ERROR
        """
        raise NotImplementedError("This method should be implemented by child class")

    def disconnect(self, parameters=None):
        """
        Disconnects from the message queue server

        :param dict parameters: dictionary with additional parameters if any
        :return: S_OK/S_ERROR
        """
        raise NotImplementedError("This method should be implemented by child class")

    def subscribe(self, parameters=None):
        """
        Subscribes to the message queue server

        :param dict parameters: dictionary with additional parameters if any
        :return: S_OK/S_ERROR
        """

        raise NotImplementedError("This method should be implemented by child class")

    def unsubscribe(self, parameters=None):
        """
        Subscribes to the message queue server

        :param dict parameters: dictionary with additional parameters if any
        :return: S_OK/S_ERROR
        """
        raise NotImplementedError("This method should be implemented by child class")
