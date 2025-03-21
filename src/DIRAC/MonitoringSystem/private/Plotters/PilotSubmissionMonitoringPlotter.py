"""
This class is used to define the plot using the plot attributes.
"""

from DIRAC import S_OK

from DIRAC.MonitoringSystem.Client.Types.PilotSubmissionMonitoring import PilotSubmissionMonitoring
from DIRAC.MonitoringSystem.private.Plotters.BasePlotter import BasePlotter


class PilotSubmissionPlotter(BasePlotter):

    """
    .. class:: PilotSubMonitoringPlotter

    It is used to crate the plots.

    param: str _typeName monitoring type
    param: list _typeKeyFields list of keys what we monitor (list of attributes)
    """

    _typeName = "PilotSubmissionMonitoring"
    _typeKeyFields = PilotSubmissionMonitoring().keyFields

    def reportNumberOfSubmissions(self, reportRequest):
        """It is used to retrieve the data from the database.

        :param dict reportRequest: contains attributes used to create the plot.
        :return: S_OK or S_ERROR {'data':value1, 'granularity':value2} value1 is a dictionary, value2 is the bucket length
        """
        retVal = self._getTimedData(
            startTime=reportRequest["startTime"],
            endTime=reportRequest["endTime"],
            selectField="NumTotal",
            preCondDict=reportRequest["condDict"],
            metadataDict=None,
        )
        if not retVal["OK"]:
            return retVal
        dataDict, granularity = retVal["Value"]
        return S_OK({"data": dataDict, "granularity": granularity})

    def _plotNumberOfSubmissions(self, reportRequest, plotInfo, filename):
        """It creates the plot.

        :param dict reportRequest: plot attributes
        :param dict plotInfo: contains all the data which are used to create the plot
        :param str filename:
        :return: S_OK or S_ERROR { 'plot' : value1, 'thumbnail' : value2 } value1 and value2 are TRUE/FALSE
        """
        metadata = {
            "title": "Pilot Submissions by %s" % reportRequest["grouping"],
            "starttime": reportRequest["startTime"],
            "endtime": reportRequest["endTime"],
            "span": plotInfo["granularity"],
            "skipEdgeColor": True,
            "ylabel": "Submissions",
        }

        plotInfo["data"] = self._fillWithZero(
            granularity=plotInfo["granularity"],
            startEpoch=reportRequest["startTime"],
            endEpoch=reportRequest["endTime"],
            dataDict=plotInfo["data"],
        )

        return self._generateStackedLinePlot(filename=filename, dataDict=plotInfo["data"], metadata=metadata)

    def reportNumSucceeded(self, reportRequest):
        """It is used to retrieve the data from the database.

        :param dict reportRequest: contains attributes used to create the plot.
        :return: S_OK or S_ERROR {'data':value1, 'granularity':value2} value1 is a dictionary, value2 is the bucket length
        """
        retVal = self._getTimedData(
            startTime=reportRequest["startTime"],
            endTime=reportRequest["endTime"],
            selectField="NumSucceeded",
            preCondDict=reportRequest["condDict"],
            metadataDict=None,
        )
        if not retVal["OK"]:
            return retVal
        dataDict, granularity = retVal["Value"]
        return S_OK({"data": dataDict, "granularity": granularity})

    def _plotNumSucceeded(self, reportRequest, plotInfo, filename):
        """It creates the plot.

        :param dict reportRequest: plot attributes
        :param dict plotInfo: contains all the data which are used to create the plot
        :param str filename:
        :return: S_OK or S_ERROR { 'plot' : value1, 'thumbnail' : value2 } value1 and value2 are TRUE/FALSE
        """
        metadata = {
            "title": "SuSubmissions by %s" % reportRequest["grouping"],
            "starttime": reportRequest["startTime"],
            "endtime": reportRequest["endTime"],
            "span": plotInfo["granularity"],
            "skipEdgeColor": True,
            "ylabel": "submissions",
        }

        plotInfo["data"] = self._fillWithZero(
            granularity=plotInfo["granularity"],
            startEpoch=reportRequest["startTime"],
            endEpoch=reportRequest["endTime"],
            dataDict=plotInfo["data"],
        )

        return self._generateStackedLinePlot(filename=filename, dataDict=plotInfo["data"], metadata=metadata)
