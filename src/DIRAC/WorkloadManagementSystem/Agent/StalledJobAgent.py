""" The StalledJobAgent hunts for stalled jobs in the Job database. Jobs in "running"
    state not receiving a heart beat signal for more than stalledTime
    seconds will be assigned the "Stalled" state.


.. literalinclude:: ../ConfigTemplate.cfg
  :start-after: ##BEGIN StalledJobAgent
  :end-before: ##END
  :dedent: 2
  :caption: StalledJobAgent options

"""
import concurrent.futures

from DIRAC import S_OK, S_ERROR, gConfig
from DIRAC.AccountingSystem.Client.Types.Job import Job
from DIRAC.Core.Base.AgentModule import AgentModule
from DIRAC.Core.Utilities import DErrno
from DIRAC.Core.Utilities.Time import fromString, toEpoch, dateTime, second
from DIRAC.Core.Utilities.ClassAd.ClassAdLight import ClassAd
from DIRAC.ConfigurationSystem.Client.Helpers import cfgPath
from DIRAC.ConfigurationSystem.Client.PathFinder import getSystemInstance
from DIRAC.WorkloadManagementSystem.Client.WMSClient import WMSClient
from DIRAC.WorkloadManagementSystem.Client.JobMonitoringClient import JobMonitoringClient
from DIRAC.WorkloadManagementSystem.Client.PilotManagerClient import PilotManagerClient
from DIRAC.WorkloadManagementSystem.DB.JobDB import JobDB
from DIRAC.WorkloadManagementSystem.DB.JobLoggingDB import JobLoggingDB
from DIRAC.WorkloadManagementSystem.Client import JobStatus, JobMinorStatus


class StalledJobAgent(AgentModule):
    """Agent for setting Running jobs Stalled, and Stalled jobs Failed. And a few more."""

    def __init__(self, *args, **kwargs):
        """c'tor"""
        super().__init__(*args, **kwargs)

        self.jobDB = None
        self.logDB = None
        self.matchedTime = 7200
        self.rescheduledTime = 600
        self.submittingTime = 300
        self.stalledJobsTolerantSites = []
        self.stalledJobsToRescheduleSites = []

    #############################################################################
    def initialize(self):
        """Sets default parameters"""
        self.jobDB = JobDB()
        self.logDB = JobLoggingDB()

        # getting parameters

        if not self.am_getOption("Enable", True):
            self.log.info("Stalled Job Agent running in disabled mode")

        wms_instance = getSystemInstance("WorkloadManagement")
        if not wms_instance:
            return S_ERROR("Can not get the WorkloadManagement system instance")
        self.stalledJobsTolerantSites = self.am_getOption("StalledJobsTolerantSites", [])
        self.stalledJobsToleranceTime = self.am_getOption("StalledJobsToleranceTime", 0)

        self.stalledJobsToRescheduleSites = self.am_getOption("StalledJobsToRescheduleSites", [])

        self.submittingTime = self.am_getOption("SubmittingTime", self.submittingTime)
        self.matchedTime = self.am_getOption("MatchedTime", self.matchedTime)
        self.rescheduledTime = self.am_getOption("RescheduledTime", self.rescheduledTime)

        wrapperSection = cfgPath("Systems", "WorkloadManagement", wms_instance, "JobWrapper")

        failedTime = self.am_getOption("FailedTimeHours", 6)
        watchdogCycle = gConfig.getValue(cfgPath(wrapperSection, "CheckingTime"), 30 * 60)
        watchdogCycle = max(watchdogCycle, gConfig.getValue(cfgPath(wrapperSection, "MinCheckingTime"), 20 * 60))
        stalledTime = self.am_getOption("StalledTimeHours", 2)
        self.log.verbose("", "StalledTime = %s cycles" % (stalledTime))
        self.stalledTime = int(watchdogCycle * (stalledTime + 0.5))
        self.log.verbose("", "FailedTime = %s cycles" % (failedTime))

        # Add half cycle to avoid race conditions
        self.failedTime = int(watchdogCycle * (failedTime + 0.5))

        self.minorStalledStatuses = (
            JobMinorStatus.STALLED_PILOT_NOT_RUNNING,
            "Stalling for more than %d sec" % self.failedTime,
        )

        # setting up the threading
        maxNumberOfThreads = self.am_getOption("MaxNumberOfThreads", 15)
        self.log.verbose("Multithreaded with %d threads" % maxNumberOfThreads)
        self.threadPoolExecutor = concurrent.futures.ThreadPoolExecutor(max_workers=maxNumberOfThreads)

        return S_OK()

    #############################################################################
    def execute(self):
        """The main agent execution method"""
        # Now we are getting what's going to be checked
        futures = []

        # 1) Queueing the jobs that might be marked Stalled
        # This is the minimum time we wait for declaring a job Stalled, therefore it is safe
        checkTime = dateTime() - self.stalledTime * second
        checkedStatuses = [JobStatus.RUNNING, JobStatus.COMPLETING]
        # Only get jobs whose HeartBeat is older than the stalledTime
        result = self.jobDB.selectJobs({"Status": checkedStatuses}, older=checkTime, timeStamp="HeartBeatTime")
        if not result["OK"]:
            self.log.error("Issue selecting %s jobs" % " & ".join(checkedStatuses), result["Message"])
        if result["Value"]:
            jobs = sorted(result["Value"])
            self.log.info(
                "%s jobs will be checked for being stalled" % " & ".join(checkedStatuses),
                "(n=%d, heartbeat before %s)" % (len(jobs), str(checkTime)),
            )
            for job in jobs:
                future = self.threadPoolExecutor.submit(self._execute, "%s:_markStalledJobs" % job)
                futures.append(future)

        # 2) fail Stalled Jobs
        result = self.jobDB.selectJobs({"Status": JobStatus.STALLED})
        if not result["OK"]:
            self.log.error("Issue selecting Stalled jobs", result["Message"])
        if result["Value"]:
            jobs = sorted(result["Value"])
            self.log.info("Jobs Stalled will be checked for failure", "(n=%d)" % len(jobs))
            for job in jobs:
                future = self.threadPoolExecutor.submit(self._execute, "%s:_failStalledJobs" % job)
                futures.append(future)

        # 3) Send accounting
        for minor in self.minorStalledStatuses:
            result = self.jobDB.selectJobs({"Status": JobStatus.FAILED, "MinorStatus": minor, "AccountedFlag": "False"})
            if not result["OK"]:
                self.log.error("Issue selecting jobs for accounting", result["Message"])
            if result["Value"]:
                jobs = result["Value"]
                self.log.info("Stalled jobs will be Accounted", "(n=%d)" % (len(jobs)))
                for job in jobs:
                    future = self.threadPoolExecutor.submit(self._execute, "%s:_sendAccounting" % job)
                    futures.append(future)

        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()
            except Exception as exc:
                self.log.error("_execute generated an exception: %s" % exc)

        # From here on we don't use the threads

        # 4) Fail submitting jobs
        result = self._failSubmittingJobs()
        if not result["OK"]:
            self.log.error("Failed to process jobs being submitted", result["Message"])

        # 5) Kick stuck jobs
        result = self._kickStuckJobs()
        if not result["OK"]:
            self.log.error("Failed to kick stuck jobs", result["Message"])

        return S_OK()

    def finalize(self):
        """graceful finalization"""

        self.log.info("Wait for threads to get empty before terminating the agent")
        self.threadPoolExecutor.shutdown()
        self.log.info("Threads are empty, terminating the agent...")
        return S_OK()

    def _execute(self, job_Op):
        """
        Doing the actual job. This is run inside the threads
        """
        jobID, jobOp = job_Op.split(":")
        jobID = int(jobID)
        res = getattr(self, "%s" % jobOp)(jobID)
        if not res["OK"]:
            self.log.error("Failure executing %s" % jobOp, "on %d: %s" % (jobID, res["Message"]))

    #############################################################################
    def _markStalledJobs(self, jobID):
        """
        Identifies if JobID is stalled:
        running or completing without update longer than stalledTime.

        Run inside thread.
        """
        delayTime = self.stalledTime
        # Add a tolerance time for some sites if required
        if self.stalledJobsTolerantSites:
            result = self.jobDB.getJobAttribute(jobID, "site")
            if not result["OK"]:
                return result
            site = result["Value"]
            if site in self.stalledJobsTolerantSites:
                delayTime += self.stalledJobsToleranceTime
        # Check if the job is really stalled
        result = self._checkJobStalled(jobID, delayTime)
        if not result["OK"]:
            return result
        self.log.verbose("Updating status to Stalled", "for job %s" % (jobID))
        return self._updateJobStatus(jobID, JobStatus.STALLED)

    #############################################################################
    def _failStalledJobs(self, jobID):
        """
        Changes the Stalled status to Failed for jobs long in the Stalled status.

        Run inside thread.
        """

        setFailed = False
        # Check if the job pilot is lost
        result = self._getJobPilotStatus(jobID)
        if not result["OK"]:
            self.log.error("Failed to get pilot status", "for job %d: %s" % (jobID, result["Message"]))
            return result
        pilotStatus = result["Value"]
        if pilotStatus != "Running":
            setFailed = self.minorStalledStatuses[0]
        else:
            # Verify that there was no sign of life for long enough
            result = self._getLatestUpdateTime(jobID)
            if not result["OK"]:
                self.log.error("Failed to get job update time", "for job %d: %s" % (jobID, result["Message"]))
                return result
            elapsedTime = toEpoch() - result["Value"]
            if elapsedTime > self.failedTime:
                setFailed = self.minorStalledStatuses[1]

        # Set the jobs Failed, send them a kill signal in case they are not really dead
        # and send accounting info
        if setFailed:
            self._sendKillCommand(jobID)  # always returns None

            # For some sites we might want to reschedule rather than fail the jobs
            if self.stalledJobsToRescheduleSites:
                result = self.jobDB.getJobAttribute(jobID, "site")
                if not result["OK"]:
                    return result
                site = result["Value"]
                if site in self.stalledJobsToRescheduleSites:
                    return self._updateJobStatus(jobID, JobStatus.RESCHEDULED, minorStatus=setFailed, force=True)

            return self._updateJobStatus(jobID, JobStatus.FAILED, minorStatus=setFailed)

        return S_OK()

    def _getJobPilotStatus(self, jobID):
        """Get the job pilot status"""
        result = JobMonitoringClient().getJobParameter(jobID, "Pilot_Reference")
        if not result["OK"]:
            return result
        pilotReference = result["Value"].get("Pilot_Reference", "Unknown")
        if pilotReference == "Unknown":
            # There is no pilot reference, hence its status is unknown
            return S_OK("NoPilot")

        result = PilotManagerClient().getPilotInfo(pilotReference)
        if not result["OK"]:
            if DErrno.cmpError(result, DErrno.EWMSNOPILOT):
                self.log.warn("No pilot found", "for job %d: %s" % (jobID, result["Message"]))
                return S_OK("NoPilot")
            self.log.error("Failed to get pilot information", "for job %d: %s" % (jobID, result["Message"]))
            return result
        pilotStatus = result["Value"][pilotReference]["Status"]

        return S_OK(pilotStatus)

    #############################################################################
    def _checkJobStalled(self, job, stalledTime):
        """Compares the most recent of LastUpdateTime and HeartBeatTime against
        the stalledTime limit.
        """
        result = self._getLatestUpdateTime(job)
        if not result["OK"]:
            return result

        elapsedTime = toEpoch() - result["Value"]
        self.log.debug("(CurrentTime-LastUpdate) = %s secs" % (elapsedTime))
        if elapsedTime > stalledTime:
            self.log.info(
                "Job is identified as stalled", ": jobID %d with last update > %s secs ago" % (job, elapsedTime)
            )
            return S_OK()

        return S_ERROR("Job %s is running and will be ignored" % job)

    #############################################################################
    def _getLatestUpdateTime(self, job):
        """Returns the most recent of HeartBeatTime and LastUpdateTime"""
        result = self.jobDB.getJobAttributes(job, ["HeartBeatTime", "LastUpdateTime"])
        if not result["OK"] or not result["Value"]:
            self.log.error(
                "Failed to get job attributes",
                "for job %d: %s" % (job, result["Message"] if "Message" in result else "empty"),
            )
            return S_ERROR("Could not get attributes for job")

        latestUpdate = 0
        if not result["Value"]["HeartBeatTime"] or result["Value"]["HeartBeatTime"] == "None":
            self.log.verbose("HeartBeatTime is null", "for job %s" % job)
        else:
            latestUpdate = toEpoch(fromString(result["Value"]["HeartBeatTime"]))

        if not result["Value"]["LastUpdateTime"] or result["Value"]["LastUpdateTime"] == "None":
            self.log.verbose("LastUpdateTime is null", "for job %s" % job)
        else:
            latestUpdate = max(latestUpdate, toEpoch(fromString(result["Value"]["LastUpdateTime"])))

        if not latestUpdate:
            return S_ERROR("LastUpdate and HeartBeat times are null for job %s" % job)
        else:
            self.log.verbose("", "Latest update time from epoch for job %s is %s" % (job, latestUpdate))
            return S_OK(latestUpdate)

    #############################################################################
    def _updateJobStatus(self, job, status, minorStatus=None, force=False):
        """This method updates the job status in the JobDB"""

        if not self.am_getOption("Enable", True):
            return S_OK("Disabled")

        toRet = S_OK()

        self.log.debug("self.jobDB.setJobAttribute(%s,'Status','%s',update=True)" % (job, status))
        result = self.jobDB.setJobAttribute(job, "Status", status, update=True, force=force)
        if not result["OK"]:
            self.log.error("Failed setting Status", "%s for job %d: %s" % (status, job, result["Message"]))
            toRet = result
        if minorStatus:
            self.log.debug("self.jobDB.setJobAttribute(%s,'MinorStatus','%s',update=True)" % (job, minorStatus))
            result = self.jobDB.setJobAttribute(job, "MinorStatus", minorStatus, update=True)
            if not result["OK"]:
                self.log.error(
                    "Failed setting MinorStatus", "%s for job %d: %s" % (minorStatus, job, result["Message"])
                )
                toRet = result

        if not minorStatus:  # Retain last minor status for stalled jobs
            result = self.jobDB.getJobAttributes(job, ["MinorStatus"])
            if result["OK"]:
                minorStatus = result["Value"]["MinorStatus"]
            else:
                self.log.error("Failed getting MinorStatus", "for job %d: %s" % (job, result["Message"]))
                minorStatus = "idem"
                toRet = result

        result = self.logDB.addLoggingRecord(job, status=status, minorStatus=minorStatus, source="StalledJobAgent")
        if not result["OK"]:
            self.log.warn("Failed adding logging record", result["Message"])
            toRet = result

        return toRet

    def _getProcessingType(self, jobID):
        """Get the Processing Type from the JDL, until it is promoted to a real Attribute"""
        processingType = "unknown"
        result = self.jobDB.getJobJDL(jobID, original=True)
        if not result["OK"]:
            return processingType
        classAdJob = ClassAd(result["Value"])
        if classAdJob.lookupAttribute("ProcessingType"):
            processingType = classAdJob.getAttributeString("ProcessingType")
        return processingType

    def _sendAccounting(self, jobID):
        """
        Send WMS accounting data for the given job.

        Run inside thread.
        """
        try:
            accountingReport = Job()
            endTime = "Unknown"
            lastHeartBeatTime = "Unknown"

            result = self.jobDB.getJobAttributes(jobID)
            if not result["OK"]:
                return result
            jobDict = result["Value"]

            startTime, endTime = self._checkLoggingInfo(jobID, jobDict)
            lastCPUTime, lastWallTime, lastHeartBeatTime = self._checkHeartBeat(jobID, jobDict)
            lastHeartBeatTime = fromString(lastHeartBeatTime)
            if lastHeartBeatTime is not None and lastHeartBeatTime > endTime:
                endTime = lastHeartBeatTime

            result = JobMonitoringClient().getJobParameter(jobID, "CPUNormalizationFactor")
            if not result["OK"] or not result["Value"]:
                self.log.error(
                    "Error getting Job Parameter CPUNormalizationFactor, setting 0",
                    result.get("Message", "No such value"),
                )
                cpuNormalization = 0.0
            else:
                cpuNormalization = float(result["Value"].get("CPUNormalizationFactor"))

        except Exception as e:
            self.log.exception(
                "Exception in _sendAccounting",
                "for job=%s: endTime=%s, lastHBTime=%s" % (str(jobID), str(endTime), str(lastHeartBeatTime)),
                lException=e,
            )
            return S_ERROR("Exception")
        processingType = self._getProcessingType(jobID)

        accountingReport.setStartTime(startTime)
        accountingReport.setEndTime(endTime)
        # execTime = toEpoch( endTime ) - toEpoch( startTime )
        # Fill the accounting data
        acData = {
            "Site": jobDict["Site"],
            "User": jobDict["Owner"],
            "UserGroup": jobDict["OwnerGroup"],
            "JobGroup": jobDict["JobGroup"],
            "JobType": jobDict["JobType"],
            "JobClass": jobDict["JobSplitType"],
            "ProcessingType": processingType,
            "FinalMajorStatus": JobStatus.FAILED,
            "FinalMinorStatus": JobMinorStatus.STALLED_PILOT_NOT_RUNNING,
            "CPUTime": lastCPUTime,
            "NormCPUTime": lastCPUTime * cpuNormalization,
            "ExecTime": lastWallTime,
            "InputDataSize": 0.0,
            "OutputDataSize": 0.0,
            "InputDataFiles": 0,
            "OutputDataFiles": 0,
            "DiskSpace": 0.0,
            "InputSandBoxSize": 0.0,
            "OutputSandBoxSize": 0.0,
            "ProcessedEvents": 0,
        }

        # For accidentally stopped jobs ExecTime can be not set
        if not acData["ExecTime"]:
            acData["ExecTime"] = acData["CPUTime"]
        elif acData["ExecTime"] < acData["CPUTime"]:
            acData["ExecTime"] = acData["CPUTime"]

        self.log.verbose("Accounting Report is:")
        self.log.verbose(acData)
        accountingReport.setValuesFromDict(acData)

        result = accountingReport.commit()
        if result["OK"]:
            self.jobDB.setJobAttribute(jobID, "AccountedFlag", "True")
        else:
            self.log.error("Failed to send accounting report", "Job: %d, Error: %s" % (int(jobID), result["Message"]))
        return result

    def _checkHeartBeat(self, jobID, jobDict):
        """Get info from HeartBeat"""
        result = self.jobDB.getHeartBeatData(jobID)
        lastCPUTime = 0
        lastWallTime = 0
        lastHeartBeatTime = jobDict["StartExecTime"]
        if lastHeartBeatTime == "None":
            lastHeartBeatTime = 0

        if result["OK"]:
            for name, value, heartBeatTime in result["Value"]:
                if name == "CPUConsumed":
                    try:
                        value = int(float(value))
                        if value > lastCPUTime:
                            lastCPUTime = value
                    except ValueError:
                        pass
                if name == "WallClockTime":
                    try:
                        value = int(float(value))
                        if value > lastWallTime:
                            lastWallTime = value
                    except ValueError:
                        pass
                if heartBeatTime > lastHeartBeatTime:
                    lastHeartBeatTime = heartBeatTime

        return lastCPUTime, lastWallTime, lastHeartBeatTime

    def _checkLoggingInfo(self, jobID, jobDict):
        """Get info from JobLogging"""
        logList = []
        result = self.logDB.getJobLoggingInfo(jobID)
        if result["OK"]:
            logList = result["Value"]

        startTime = jobDict["StartExecTime"]
        if not startTime or startTime == "None":
            # status, minor, app, stime, source
            for items in logList:
                if items[0] == "Running":
                    startTime = items[3]
                    break
            if not startTime or startTime == "None":
                startTime = jobDict["SubmissionTime"]

        if isinstance(startTime, str):
            startTime = fromString(startTime)
            if startTime is None:
                self.log.error("Wrong timestamp in DB", items[3])
                startTime = dateTime()

        endTime = dateTime()
        # status, minor, app, stime, source
        for items in logList:
            if items[0] == "Stalled":
                endTime = fromString(items[3])
        if endTime is None:
            self.log.error("Wrong timestamp in DB", items[3])
            endTime = dateTime()

        return startTime, endTime

    def _kickStuckJobs(self):
        """Reschedule jobs stuck in initialization status Rescheduled, Matched"""

        message = ""

        checkTime = dateTime() - self.matchedTime * second
        result = self.jobDB.selectJobs({"Status": JobStatus.MATCHED}, older=checkTime)
        if not result["OK"]:
            self.log.error("Failed to select jobs", result["Message"])
            return result

        jobIDs = result["Value"]
        if jobIDs:
            self.log.info("Rescheduling %d jobs stuck in Matched status" % len(jobIDs))
            result = self.jobDB.rescheduleJobs(jobIDs)
            if "FailedJobs" in result:
                message = "Failed to reschedule %d jobs stuck in Matched status" % len(result["FailedJobs"])

        checkTime = dateTime() - self.rescheduledTime * second
        result = self.jobDB.selectJobs({"Status": JobStatus.RESCHEDULED}, older=checkTime)
        if not result["OK"]:
            self.log.error("Failed to select jobs", result["Message"])
            return result

        jobIDs = result["Value"]
        if jobIDs:
            self.log.info("Rescheduling %d jobs stuck in Rescheduled status" % len(jobIDs))
            result = self.jobDB.rescheduleJobs(jobIDs)
            if "FailedJobs" in result:
                if message:
                    message += "\n"
                message += "Failed to reschedule %d jobs stuck in Rescheduled status" % len(result["FailedJobs"])

        if message:
            return S_ERROR(message)
        return S_OK()

    def _failSubmittingJobs(self):
        """Failed Jobs stuck in Submitting Status for a long time.
        They are due to a failed bulk submission transaction.
        """

        # Get old Submitting Jobs
        checkTime = dateTime() - self.submittingTime * second
        result = self.jobDB.selectJobs({"Status": JobStatus.SUBMITTING}, older=checkTime)
        if not result["OK"]:
            self.log.error("Failed to select jobs", result["Message"])
            return result

        for jobID in result["Value"]:
            result = self._updateJobStatus(jobID, JobStatus.FAILED)
            if not result["OK"]:
                self.log.error("Failed to update job status", result["Message"])
                continue

        return S_OK()

    def _sendKillCommand(self, job):
        """Send a kill signal to the job such that it cannot continue running.

        :param int job: ID of job to send kill command
        """
        ownerDN = self.jobDB.getJobAttribute(job, "OwnerDN")
        ownerGroup = self.jobDB.getJobAttribute(job, "OwnerGroup")
        if ownerDN["OK"] and ownerGroup["OK"]:
            wmsClient = WMSClient(
                useCertificates=True, delegatedDN=ownerDN["Value"], delegatedGroup=ownerGroup["Value"]
            )
            resKill = wmsClient.killJob(job)
            if not resKill["OK"]:
                self.log.error("Failed to send kill command to job", "%s: %s" % (job, resKill["Message"]))
        else:
            self.log.error(
                "Failed to get ownerDN or Group for job:",
                "%s: %s, %s" % (job, ownerDN.get("Message", ""), ownerGroup.get("Message", "")),
            )
