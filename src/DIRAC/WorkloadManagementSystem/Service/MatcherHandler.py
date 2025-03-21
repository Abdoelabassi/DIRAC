""" The Matcher service provides an interface for matching jobs to pilots

    It uses a Matcher and a Limiter object that encapsulates the matching logic.
    It connects to JobDB, TaskQueueDB, JobLoggingDB, and PilotAgentsDB.
"""
from DIRAC import S_OK, S_ERROR

from DIRAC.ConfigurationSystem.Client.Helpers.Operations import Operations
from DIRAC.Core.DISET.RequestHandler import RequestHandler
from DIRAC.Core.Utilities.DEncode import ignoreEncodeWarning
from DIRAC.Core.Utilities.ObjectLoader import ObjectLoader

from DIRAC.FrameworkSystem.Client.MonitoringClient import gMonitor

from DIRAC.WorkloadManagementSystem.Client.Matcher import Matcher, PilotVersionError
from DIRAC.WorkloadManagementSystem.Client.Limiter import Limiter


class MatcherHandlerMixin:
    @classmethod
    def initializeHandler(cls, serviceInfoDict):
        try:
            result = ObjectLoader().loadObject("WorkloadManagementSystem.DB.JobDB", "JobDB")
            if not result["OK"]:
                return result
            cls.jobDB = result["Value"]()

            result = ObjectLoader().loadObject("WorkloadManagementSystem.DB.JobLoggingDB", "JobLoggingDB")
            if not result["OK"]:
                return result
            cls.jobLoggingDB = result["Value"]()

            result = ObjectLoader().loadObject("WorkloadManagementSystem.DB.TaskQueueDB", "TaskQueueDB")
            if not result["OK"]:
                return result
            cls.taskQueueDB = result["Value"]()

            result = ObjectLoader().loadObject("WorkloadManagementSystem.DB.PilotAgentsDB", "PilotAgentsDB")
            if not result["OK"]:
                return result
            cls.pilotAgentsDB = result["Value"]()

        except RuntimeError as excp:
            return S_ERROR("Can't connect to DB: %s" % excp)

        cls.limiter = Limiter(jobDB=cls.jobDB)

        gMonitor.registerActivity("matchTime", "Job matching time", "Matching", "secs", gMonitor.OP_MEAN, 300)
        gMonitor.registerActivity("matchesDone", "Job Match Request", "Matching", "matches", gMonitor.OP_RATE, 300)
        gMonitor.registerActivity("matchesOK", "Matched jobs", "Matching", "matches", gMonitor.OP_RATE, 300)
        gMonitor.registerActivity("numTQs", "Number of Task Queues", "Matching", "tqsk queues", gMonitor.OP_MEAN, 300)

        return S_OK()

    ##############################################################################
    types_requestJob = [[str, dict]]

    def export_requestJob(self, resourceDescription):
        """Serve a job to the request of an agent which is the highest priority
        one matching the agent's site capacity
        """

        resourceDescription["Setup"] = self.serviceInfoDict["clientSetup"]
        credDict = self.getRemoteCredentials()
        pilotRef = resourceDescription.get("PilotReference", "Unknown")

        try:
            opsHelper = Operations(group=credDict["group"])
            matcher = Matcher(
                pilotAgentsDB=self.pilotAgentsDB,
                jobDB=self.jobDB,
                tqDB=self.taskQueueDB,
                jlDB=self.jobLoggingDB,
                opsHelper=opsHelper,
                pilotRef=pilotRef,
            )
            result = matcher.selectJob(resourceDescription, credDict)
        except RuntimeError as rte:
            self.log.error("Error requesting job for pilot", "[%s] %s" % (pilotRef, rte))
            return S_ERROR("Error requesting job")
        except PilotVersionError as pve:
            self.log.warn("Pilot version error for pilot", "[%s] %s" % (pilotRef, pve))
            return S_ERROR("Error requesting job")

        # result can be empty, meaning that no job matched
        if result:
            gMonitor.addMark("matchesDone")
            gMonitor.addMark("matchesOK")
            return S_OK(result)
        # FIXME: This is correctly interpreted by the JobAgent, but DErrno should be used instead
        return S_ERROR("No match found")

    ##############################################################################
    types_getActiveTaskQueues = []

    @classmethod
    @ignoreEncodeWarning
    def export_getActiveTaskQueues(cls):
        """Return all task queues"""
        return cls.taskQueueDB.retrieveTaskQueues()

    ##############################################################################
    types_getMatchingTaskQueues = [dict]

    @classmethod
    @ignoreEncodeWarning
    def export_getMatchingTaskQueues(cls, resourceDict):
        """Return all task queues that match the resourceDict"""
        if "Site" in resourceDict and isinstance(resourceDict["Site"], str):
            gridCE = resourceDict.get("GridCE")
            negativeCond = cls.limiter.getNegativeCondForSite(resourceDict["Site"], gridCE)
        else:
            negativeCond = cls.limiter.getNegativeCond()
        matcher = Matcher(pilotAgentsDB=cls.pilotAgentsDB, jobDB=cls.jobDB, tqDB=cls.taskQueueDB, jlDB=cls.jobLoggingDB)
        resourceDescriptionDict = matcher._processResourceDescription(resourceDict)
        return cls.taskQueueDB.getMatchingTaskQueues(resourceDescriptionDict, negativeCond=negativeCond)


class MatcherHandler(MatcherHandlerMixin, RequestHandler):
    pass
