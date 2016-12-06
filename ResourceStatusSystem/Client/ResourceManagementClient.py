""" ResourceManagementClient

  Client to interact with the ResourceManagementDB.

"""

from DIRAC                      import gLogger, S_ERROR
from DIRAC.Core.DISET.RPCClient import RPCClient

__RCSID__ = '$Id:  $'

class ResourceManagementClient( object ):
  """
  The :class:`ResourceManagementClient` class exposes the :mod:`DIRAC.ResourceManagement`
  API. All functions you need are on this client.

  It has the 'direct-db-access' functions, the ones of the type:
   - insert
   - update
   - select
   - delete

  that return parts of the RSSConfiguration stored on the CS, and used everywhere
  on the RSS module. Finally, and probably more interesting, it exposes a set
  of functions, badly called 'boosters'. They are 'home made' functions using the
  basic database functions that are interesting enough to be exposed.

  The client will ALWAYS try to connect to the DB, and in case of failure, to the
  XML-RPC server ( namely :class:`ResourceManagementDB` and
  :class:`ResourceManagementHancler` ).

  You can use this client on this way

   >>> from DIRAC.ResourceManagementSystem.Client.ResourceManagementClient import ResourceManagementClient
   >>> rsClient = ResourceManagementClient()

  All functions calling methods exposed on the database or on the booster are
  making use of some syntactic sugar, in this case a decorator that simplifies
  the client considerably.
  """

  def __init__( self , serviceIn = None ):
    '''
    The client tries to connect to :class:ResourceManagementDB by default. If it
    fails, then tries to connect to the Service :class:ResourceManagementHandler.
    '''

    if not serviceIn:
      self.rmsDB = RPCClient( "ResourceStatus/ResourceManagement" )
    else:
      self.rmsDB = serviceIn

  def _prepare(self, sendDict):
    # remove unnecessary key generated by locals()
    del sendDict['self']
    return sendDict

  # AccountingCache Methods ....................................................

  def selectAccountingCache( self, Name = None, PlotType = None, PlotName = None,
                                  Result = None, DateEffective = None, LastCheckTime = None ):
    '''
    Gets from PolicyResult all rows that match the parameters given.

    :Parameters:
      **name** - `[, string, list]`
        name of an individual of the grid topology
      **plotType** - `[, string, list]`
        the plotType name (e.g. 'Pilot')
      **plotName** - `[, string, list]`
        the plot name
      **result** - `[, string, list]`
        command result
      **dateEffective** - `[, datetime, list]`
        time-stamp from which the result is effective
      **lastCheckTime** - `[, datetime, list]`
        time-stamp setting last time the result was checked

    :return: S_OK() || S_ERROR()
    '''

    return self.rmsDB.select( 'AccountingCache', self._prepare(locals()) )


  def addOrModifyAccountingCache( self, Name = None, PlotType = None, PlotName = None,
                                  Result = None, DateEffective = None, LastCheckTime = None ):
    '''
    Adds or updates-if-duplicated to AccountingCache. Using `name`, `plotType`
    and `plotName` to query the database, decides whether to insert or update the
    table.

    :Parameters:
      **name** - `string`
        name of an individual of the grid topology
      **plotType** - `string`
        the plotType name (e.g. 'Pilot')
      **plotName** - `string`
        the plot name
      **result** - `string`
        command result
      **dateEffective** - `datetime`
        time-stamp from which the result is effective
      **lastCheckTime** - `datetime`
        time-stamp setting last time the result was checked

    :return: S_OK() || S_ERROR()
    '''

    return self.rmsDB.addOrModify( 'AccountingCache', self._prepare(locals()) )



  def deleteAccountingCache( self, Name = None, PlotType = None, PlotName = None,
                                  Result = None, DateEffective = None, LastCheckTime = None ):
    '''
    Deletes from AccountingCache all rows that match the parameters given.

    :Parameters:
      **name** - `string`
        name of an individual of the grid topology
      **plotType** - `string`
        the plotType name (e.g. 'Pilot')
      **plotName** - `string`
        the plot name
      **result** - `string`
        command result
      **dateEffective** - `datetime`
        time-stamp from which the result is effective
      **lastCheckTime** - `datetime`
        time-stamp setting last time the result was checked

    :return: S_OK() || S_ERROR()
    '''

    return self.rmsDB.delete( 'AccountingCache', self._prepare(locals()) )


  # GGUSTicketsCache Methods ...................................................

  def selectGGUSTicketsCache( self, GocSite = None, Link = None, OpenTickets = None,
                              Tickets = None, LastCheckTime = None ):

    return self.rmsDB.select( 'GGUSTicketsCache', self._prepare(locals()) )


  def deleteGGUSTicketsCache( self, GocSite = None, Link = None, OpenTickets = None,
                              Tickets = None, LastCheckTime = None ):

    return self.rmsDB.delete( 'GGUSTicketsCache', self._prepare(locals()) )


  def addOrModifyGGUSTicketsCache( self, GocSite = None, Link = None, OpenTickets = None,
                                  Tickets = None, LastCheckTime = None ):

    return self.rmsDB.addOrModify( 'GGUSTicketsCache', self._prepare(locals()) )


  # DowntimeCache Methods ......................................................

  def selectDowntimeCache( self, DowntimeID = None, Element = None, Name = None,
                           StartDate = None, EndDate = None, Severity = None,
                           Description = None, Link = None, DateEffective = None,
                           LastCheckTime = None, GocdbServiceType = None ):
    '''
    Gets from DowntimeCache all rows that match the parameters given.

    :Parameters:
      **downtimeID** - [, `string`, `list`]
        unique id for the downtime
      **element** - [, `string`, `list`]
        valid element in the topology ( Site, Resource, Node )
      **name** - [, `string`, `list`]
        name of the element where the downtime applies
      **startDate** - [, `datetime`, `list`]
        starting time for the downtime
      **endDate** - [, `datetime`, `list`]
        ending time for the downtime
      **severity** - [, `string`, `list`]
        severity assigned by the gocdb
      **description** - [, `string`, `list`]
        brief description of the downtime
      **link** - [, `string`, `list`]
        url to the details
      **dateEffective** - [, `datetime`, `list`]
        time when the entry was created in this database
      **lastCheckTime** - [, `datetime`, `list`]
        time-stamp setting last time the result was checked
      **gocdbServiceType** - `string`
        service type assigned by gocdb

    :return: S_OK() || S_ERROR()
    '''

    return self.rmsDB.select( 'DowntimeCache', self._prepare(locals()) )


  def deleteDowntimeCache( self, DowntimeID = None, Element = None, Name = None,
                           StartDate = None, EndDate = None, Severity = None,
                           Description = None, Link = None, DateEffective = None,
                           LastCheckTime = None, GocdbServiceType = None ):
    '''
    Deletes from DowntimeCache all rows that match the parameters given.

    :Parameters:
      **downtimeID** - [, `string`, `list`]
        unique id for the downtime
      **element** - [, `string`, `list`]
        valid element in the topology ( Site, Resource, Node )
      **name** - [, `string`, `list`]
        name of the element where the downtime applies
      **startDate** - [, `datetime`, `list`]
        starting time for the downtime
      **endDate** - [, `datetime`, `list`]
        ending time for the downtime
      **severity** - [, `string`, `list`]
        severity assigned by the gocdb
      **description** - [, `string`, `list`]
        brief description of the downtime
      **link** - [, `string`, `list`]
        url to the details
      **dateEffective** - [, `datetime`, `list`]
        time when the entry was created in this database
      **lastCheckTime** - [, `datetime`, `list`]
        time-stamp setting last time the result was checked
      **gocdbServiceType** - `string`
        service type assigned by gocdb

    :return: S_OK() || S_ERROR()
    '''

    return self.rmsDB.delete( 'DowntimeCache', self._prepare(locals()) )


  def addOrModifyDowntimeCache( self, DowntimeID = None, Element = None, Name = None,
                           StartDate = None, EndDate = None, Severity = None,
                           Description = None, Link = None, DateEffective = None,
                           LastCheckTime = None, GocdbServiceType = None ):
    '''
    Adds or updates-if-duplicated to DowntimeCache. Using `downtimeID` to query
    the database, decides whether to insert or update the table.

    :Parameters:
      **downtimeID** - `string`
        unique id for the downtime
      **element** - `string`
        valid element in the topology ( Site, Resource, Node )
      **name** - `string`
        name of the element where the downtime applies
      **startDate** - `datetime`
        starting time for the downtime
      **endDate** - `datetime`
        ending time for the downtime
      **severity** - `string`
        severity assigned by the gocdb
      **description** - `string`
        brief description of the downtime
      **link** - `string`
        url to the details
      **dateEffective** - `datetime`
        time when the entry was created in this database
      **lastCheckTime** - `datetime`
        time-stamp setting last time the result was checked
      **gocdbServiceType** - `string`
        service type assigned by gocdb

    :return: S_OK() || S_ERROR()
    '''

    return self.rmsDB.addOrModify( 'DowntimeCache', self._prepare(locals()) )


  # JobCache Methods ...........................................................

  def selectJobCache( self, Site = None, MaskStatus = None, Efficiency = None,
                      Status = None, LastCheckTime = None ):
    '''
    Gets from JobCache all rows that match the parameters given.

    :Parameters:
      **site** - `[, string, list ]`
        name of the site element
      **maskStatus** - `[, string, list ]`
        maskStatus for the site
      **efficiency** - `[, float, list ]`
        job efficiency ( successful / total )
      **status** - `[, string, list ]`
        status for the site computed
      **lastCheckTime** - `[, datetime, list ]`
        time-stamp setting last time the result was checked

    :return: S_OK() || S_ERROR()
    '''

    return self.rmsDB.select( 'JobCache', self._prepare(locals()) )


  def deleteJobCache( self, Site = None, MaskStatus = None, Efficiency = None,
                      Status = None, LastCheckTime = None ):
    '''
    Deletes from JobCache all rows that match the parameters given.

    :Parameters:
      **site** - `[, string, list ]`
        name of the site element
      **maskStatus** - `[, string, list ]`
        maskStatus for the site
      **efficiency** - `[, float, list ]`
        job efficiency ( successful / total )
      **status** - `[, string, list ]`
        status for the site computed
      **lastCheckTime** - `[, datetime, list ]`
        time-stamp setting last time the result was checked

    :return: S_OK() || S_ERROR()
    '''

    return self.rmsDB.delete( 'JobCache', self._prepare(locals()) )


  def addOrModifyJobCache( self, Site = None, MaskStatus = None, Efficiency = None,
                      Status = None, LastCheckTime = None ):
    '''
    Adds or updates-if-duplicated to JobCache. Using `site` to query
    the database, decides whether to insert or update the table.

    :Parameters:
      **site** - `[, string, list ]`
        name of the site element
      **maskStatus** - `[, string, list ]`
        maskStatus for the site
      **efficiency** - `[, float, list ]`
        job efficiency ( successful / total )
      **status** - `[, string, list ]`
        status for the site computed
      **lastCheckTime** - `[, datetime, list ]`
        time-stamp setting last time the result was checked

    :return: S_OK() || S_ERROR()
    '''

    return self.rmsDB.addOrModify( 'JobCache', self._prepare(locals()) )


  # TransferCache Methods ......................................................

  def selectTransferCache( self, SourceName = None, DestinationName = None, Metric = None,
                           Value = None, LastCheckTime = None ):
    '''
#    Gets from TransferCache all rows that match the parameters given.
#
#    :Parameters:
#      **elementName** - `[, string, list ]`
#        name of the element
#      **direction** - `[, string, list ]`
#        the element taken as Source or Destination of the transfer
#      **metric** - `[, string, list ]`
#        measured quality of failed transfers
#      **value** - `[, float, list ]`
#        percentage
#      **lastCheckTime** - `[, float, list ]`
#        time-stamp setting last time the result was checked
#      **meta** - `[, dict]`
#        meta-data for the MySQL query. It will be filled automatically with the\
#       `table` key and the proper table name.
#
#    :return: S_OK() || S_ERROR()
    '''

    return self.rmsDB.select( 'TransferCache', self._prepare(locals()) )


  def deleteTransferCache( self, SourceName = None, DestinationName = None, Metric = None,
                           Value = None, LastCheckTime = None ):
    '''
#    Deletes from TransferCache all rows that match the parameters given.
#
#    :Parameters:
#      **elementName** - `[, string, list ]`
#        name of the element
#      **direction** - `[, string, list ]`
#        the element taken as Source or Destination of the transfer
#      **metric** - `[, string, list ]`
#        measured quality of failed transfers
#      **value** - `[, float, list ]`
#        percentage
#      **lastCheckTime** - `[, float, list ]`
#        time-stamp setting last time the result was checked
#      **meta** - `[, dict]`
#        meta-data for the MySQL query. It will be filled automatically with the\
#       `table` key and the proper table name.
#
#    :return: S_OK() || S_ERROR()
    '''

    return self.rmsDB.delete( 'TransferCache', self._prepare(locals()) )


  def addOrModifyTransferCache( self, SourceName = None, DestinationName = None, Metric = None,
                           Value = None, LastCheckTime = None ):
    '''
#    Adds or updates-if-duplicated to TransferCache. Using `elementName`, `direction`
#    and `metric` to query the database, decides whether to insert or update the table.
#
#    :Parameters:
#      **elementName** - `string`
#        name of the element
#      **direction** - `string`
#        the element taken as Source or Destination of the transfer
#      **metric** - `string`
#        measured quality of failed transfers
#      **value** - `float`
#        percentage
#      **lastCheckTime** - `datetime`
#        time-stamp setting last time the result was checked
#      **meta** - `[, dict]`
#        meta-data for the MySQL query. It will be filled automatically with the\
#       `table` key and the proper table name.
#
#    :return: S_OK() || S_ERROR()
    '''

    return self.rmsDB.addOrModify( 'TransferCache', self._prepare(locals()) )


  # PilotCache Methods .........................................................

  def selectPilotCache( self, Site = None, CE = None, PilotsPerJob = None,
                        PilotJobEff = None, Status = None, LastCheckTime = None ):
    '''
    Gets from TransferCache all rows that match the parameters given.

    :Parameters:
      **site** - `[, string, list ]`
        name of the site
      **cE** - `[, string, list ]`
        name of the CE of 'Multiple' if all site CEs are considered
      **pilotsPerJob** - `[, float, list ]`
        measure calculated
      **pilotJobEff** - `[, float, list ]`
        percentage
      **status** - `[, float, list ]`
        status of the CE / Site
      **lastCheckTime** - `[, datetime, list ]`
        measure calculated

    :return: S_OK() || S_ERROR()
    '''

    return self.rmsDB.select( 'PilotCache', self._prepare(locals()) )


  def deletePilotCache( self, Site = None, CE = None, PilotsPerJob = None,
                        PilotJobEff = None, Status = None, LastCheckTime = None ):
    '''
    Deletes from TransferCache all rows that match the parameters given.

    :Parameters:
      **site** - `[, string, list ]`
        name of the site
      **cE** - `[, string, list ]`
        name of the CE of 'Multiple' if all site CEs are considered
      **pilotsPerJob** - `[, float, list ]`
        measure calculated
      **pilotJobEff** - `[, float, list ]`
        percentage
      **status** - `[, float, list ]`
        status of the CE / Site
      **lastCheckTime** - `[, datetime, list ]`
        measure calculated

    :return: S_OK() || S_ERROR()    '''

    return self.rmsDB.delete( 'PilotCache', self._prepare(locals()) )


  def addOrModifyPilotCache( self, Site = None, CE = None, PilotsPerJob = None,
                        PilotJobEff = None, Status = None, LastCheckTime = None ):
    '''
    Adds or updates-if-duplicated to PilotCache. Using `site` and `cE`
    to query the database, decides whether to insert or update the table.

    :Parameters:
      **site** - `string`
        name of the site
      **cE** - `string`
        name of the CE of 'Multiple' if all site CEs are considered
      **pilotsPerJob** - `float`
        measure calculated
      **pilotJobEff** - `float`
        percentage
      **status** - `string`
        status of the CE / Site
      **lastCheckTime** - `datetime`
        measure calculated

    :return: S_OK() || S_ERROR()
    '''

    return self.rmsDB.addOrModify( 'PilotCache', self._prepare(locals()) )


  # PolicyResult Methods .......................................................

  def selectPolicyResult( self, Element = None, Name = None, PolicyName = None,
                          StatusType = None, Status = None, Reason = None,
                          LastCheckTime = None ):
    '''
    Gets from PolicyResult all rows that match the parameters given.

    :Parameters:
      **granularity** - `[, string, list]`
        it has to be a valid element ( ValidElement ), any of the defaults: `Site` \
        | `Service` | `Resource` | `StorageElement`
      **name** - `[, string, list]`
        name of the element
      **policyName** - `[, string, list]`
        name of the policy
      **statusType** - `[, string, list]`
        it has to be a valid status type for the given granularity
      **status** - `[, string, list]`
        it has to be a valid status, any of the defaults: `Active` | `Degraded` | \
        `Probing` | `Banned`
      **reason** - `[, string, list]`
        decision that triggered the assigned status
      **lastCheckTime** - `[, datetime, list]`
        time-stamp setting last time the policy result was checked

    :return: S_OK() || S_ERROR()
    '''

    return self.rmsDB.select( 'PolicyResult', self._prepare(locals()) )


  def deletePolicyResult( self, Element = None, Name = None, PolicyName = None,
                          StatusType = None, Status = None, Reason = None,
                          LastCheckTime = None ):
    '''
    Deletes from PolicyResult all rows that match the parameters given.

    :Parameters:
      **granularity** - `[, string, list]`
        it has to be a valid element ( ValidElement ), any of the defaults: `Site` \
        | `Service` | `Resource` | `StorageElement`
      **name** - `[, string, list]`
        name of the element
      **policyName** - `[, string, list]`
        name of the policy
      **statusType** - `[, string, list]`
        it has to be a valid status type for the given granularity
      **status** - `[, string, list]`
        it has to be a valid status, any of the defaults: `Active` | `Degraded` | \
        `Probing` | `Banned`
      **reason** - `[, string, list]`
        decision that triggered the assigned status
      **lastCheckTime** - `[, datetime, list]`
        time-stamp setting last time the policy result was checked

    :return: S_OK() || S_ERROR()
    '''

    return self.rmsDB.delete( 'PolicyResult', self._prepare(locals()) )


  def addOrModifyPolicyResult( self, Element = None, Name = None, PolicyName = None,
                          StatusType = None, Status = None, Reason = None,
                          LastCheckTime = None ):
    '''
    Adds or updates-if-duplicated to PolicyResult. Using `name`, `policyName` and
    `statusType` to query the database, decides whether to insert or update the table.

    :Parameters:
      **element** - `string`
        it has to be a valid element ( ValidElement ), any of the defaults: `Site` \
        | `Service` | `Resource` | `StorageElement`
      **name** - `string`
        name of the element
      **policyName** - `string`
        name of the policy
      **statusType** - `string`
        it has to be a valid status type for the given element
      **status** - `string`
        it has to be a valid status, any of the defaults: `Active` | `Degraded` | \
        `Probing` | `Banned`
      **reason** - `string`
        decision that triggered the assigned status
      **dateEffective** - `datetime`
        time-stamp from which the policy result is effective
      **lastCheckTime** - `datetime`
        time-stamp setting last time the policy result was checked

    :return: S_OK() || S_ERROR()
    '''

    return self.rmsDB.addOrModify( 'PolicyResult', self._prepare(locals()) )


  # PolicyResultLog Methods ....................................................

  def selectPolicyResultLog( self, Element = None, Name = None,
                             PolicyName = None, StatusType = None, Status = None,
                             Reason = None, LastCheckTime = None ):
    '''
    Gets from PolicyResultLog all rows that match the parameters given.

    :Parameters:
      **element** - `[, string, list]`
        it has to be a valid element ( ValidRes ), any of the defaults: `Site` \
        | `Service` | `Resource` | `StorageElement`
      **name** - `[, string, list]`
        name of the element
      **policyName** - `[, string, list]`
        name of the policy
      **statusType** - `[, string, list]`
        it has to be a valid status type for the given element
      **status** - `[, string, list]`
        it has to be a valid status, any of the defaults: `Active` | `Degraded` | \
        `Probing` | `Banned`
      **reason** - `[, string, list]`
        decision that triggered the assigned status
      **lastCheckTime** - `[, datetime, list]`
        time-stamp setting last time the policy result was checked

    :return: S_OK() || S_ERROR()
    '''

    return self.rmsDB.select( 'PolicyResultLog', self._prepare(locals()) )


  def deletePolicyResultLog( self, Element = None, Name = None,
                             PolicyName = None, StatusType = None, Status = None,
                             Reason = None, LastCheckTime = None ):
    '''
    Deletes from PolicyResult all rows that match the parameters given.

    :Parameters:
      **element** - `[, string, list]`
        it has to be a valid element ( ValidRes ), any of the defaults: `Site` \
        | `Service` | `Resource` | `StorageElement`
      **name** - `[, string, list]`
        name of the element
      **policyName** - `[, string, list]`
        name of the policy
      **statusType** - `[, string, list]`
        it has to be a valid status type for the given element
      **status** - `[, string, list]`
        it has to be a valid status, any of the defaults: `Active` | `Degraded` | \
        `Probing` | `Banned`
      **reason** - `[, string, list]`
        decision that triggered the assigned status
      **lastCheckTime** - `[, datetime, list]`
        time-stamp setting last time the policy result was checked

    :return: S_OK() || S_ERROR()
    '''

    return self.rmsDB.delete( 'PolicyResultLog', self._prepare(locals()) )


  def addOrModifyPolicyResultLog( self, Element = None, Name = None,
                             PolicyName = None, StatusType = None, Status = None,
                             Reason = None, LastCheckTime = None ):
    '''
    Adds or updates-if-duplicated to PolicyResultLog. Using `name`, `policyName`,
    'statusType` to query the database, decides whether to insert or update the table.

    :Parameters:
      **element** - `string`
        it has to be a valid element ( ValidRes ), any of the defaults: `Site` \
        | `Service` | `Resource` | `StorageElement`
      **name** - `string`
        name of the element
      **policyName** - `string`
        name of the policy
      **statusType** - `string`
        it has to be a valid status type for the given element
      **status** - `string`
        it has to be a valid status, any of the defaults: `Active` | `Degraded` | \
        `Probing` | `Banned`
      **reason** - `string`
        decision that triggered the assigned status
      **lastCheckTime** - `datetime`
        time-stamp setting last time the policy result was checked

    :return: S_OK() || S_ERROR()
    '''

    return self.rmsDB.addOrModify( 'PolicyResultLog', self._prepare(locals()) )


  # SpaceTokenOccupancyCache Methods ...........................................

  def selectSpaceTokenOccupancyCache( self, Endpoint = None, Token = None,
                                      Total = None, Guaranteed = None, Free = None,
                                      LastCheckTime = None ):
    '''
    Gets from SpaceTokenOccupancyCache all rows that match the parameters given.

    :Parameters:
      **endpoint** - `[, string, list]`
        srm endpoint
      **token** - `[, string, list]`
        name of the token
      **total** - `[, integer, list]`
        total terabytes
      **guaranteed** - `[, integer, list]`
        guaranteed terabytes
      **free** - `[, integer, list]`
        free terabytes
      **lastCheckTime** - `[, datetime, list]`
        time-stamp from which the result is effective

    :return: S_OK() || S_ERROR()
    '''

    return self.rmsDB.select( 'SpaceTokenOccupancyCache', self._prepare(locals()) )


  def deleteSpaceTokenOccupancyCache( self, Endpoint = None, Token = None,
                                      Total = None, Guaranteed = None, Free = None,
                                      LastCheckTime = None ):
    '''
    Deletes from SpaceTokenOccupancyCache all rows that match the parameters given.

    :Parameters:
      **endpoint** - `[, string, list]`
        srm endpoint
      **token** - `[, string, list]`
        name of the token
      **total** - `[, integer, list]`
        total terabytes
      **guaranteed** - `[, integer, list]`
        guaranteed terabytes
      **free** - `[, integer, list]`
        free terabytes
      **lastCheckTime** - `[, datetime, list]`
        time-stamp from which the result is effective

    :return: S_OK() || S_ERROR()
    '''

    return self.rmsDB.delete( 'SpaceTokenOccupancyCache', self._prepare(locals()) )


  def addOrModifySpaceTokenOccupancyCache( self, Endpoint = None, Token = None,
                                      Total = None, Guaranteed = None, Free = None,
                                      LastCheckTime = None ):
    '''
    Adds or updates-if-duplicated to SpaceTokenOccupancyCache. Using `site` and `token`
    to query the database, decides whether to insert or update the table.

    :Parameters:
      **endpoint** - `[, string, list]`
        srm endpoint
      **token** - `string`
        name of the token
      **total** - `integer`
        total terabytes
      **guaranteed** - `integer`
        guaranteed terabytes
      **free** - `integer`
        free terabytes
      **lastCheckTime** - `datetime`
        time-stamp from which the result is effective

    :return: S_OK() || S_ERROR()
    '''

    return self.rmsDB.addOrModify( 'SpaceTokenOccupancyCache', self._prepare(locals()) )


  # UserRegistryCache Methods ..................................................

  def selectUserRegistryCache( self, Login = None, Name = None, Email = None,
                               LastCheckTime = None ):
    '''
    Gets from UserRegistryCache all rows that match the parameters given.

    :Parameters:
      **login** - `[, string, list]`
        user's login ID
      **name** - `[, string, list]`
        user's name
      **email** - `[, string, list]`
        user's email
      **lastCheckTime** - `[, datetime, list]`
        time-stamp from which the result is effective

    :return: S_OK() || S_ERROR()
    '''

    return self.rmsDB.select( 'UserRegistryCache', self._prepare(locals()) )


  def deleteUserRegistryCache( self, Login = None, Name = None, Email = None,
                               LastCheckTime = None ):
    '''
    Deletes from UserRegistryCache all rows that match the parameters given.

    :Parameters:
      **login** - `[, string, list]`
        user's login ID
      **name** - `[, string, list]`
        user's name
      **email** - `[, string, list]`
        user's email
      **lastCheckTime** - `[, datetime, list]`
        time-stamp from which the result is effective

    :return: S_OK() || S_ERROR()
    '''

    return self.rmsDB.delete( 'UserRegistryCache', self._prepare(locals()) )


  def addOrModifyUserRegistryCache( self, Login = None, Name = None, Email = None,
                               LastCheckTime = None ):
    '''
    Adds or updates-if-duplicated to UserRegistryCache. Using `login` to query
    the database, decides whether to insert or update the table.

    :Parameters:
      **login** - `string`
        user's login ID
      **name** - `string`
        user's name
      **email** - `string`
        user's email
      **lastCheckTime** - `datetime`
        time-stamp from which the result is effective

    :return: S_OK() || S_ERROR()
    '''

    return self.rmsDB.addOrModify( 'UserRegistryCache', self._prepare(locals()) )


  # ErrorReportBuffer Methods ..................................................

  def insertErrorReportBuffer( self, Name = None, ElementType = None, Reporter = None,
                               ErrorMessage = None, Operation = None, Arguments = None,
                               DateEffective = None ):

    return self.rmsDB.insert( 'ErrorReportBuffer', self._prepare(locals()) )


  def selectErrorReportBuffer( self, Name = None, ElementType = None, Reporter = None,
                               ErrorMessage = None, Operation = None, Arguments = None,
                               DateEffective = None ):

    return self.rmsDB.select( 'ErrorReportBuffer', self._prepare(locals()) )


  def deleteErrorReportBuffer( self, Name = None, ElementType = None, Reporter = None,
                               ErrorMessage = None, Operation = None, Arguments = None,
                               DateEffective = None ):

    return self.rmsDB.delete( 'ErrorReportBuffer', self._prepare(locals()) )

#...............................................................................
#EOF#EOF#EOF#EOF#EOF#EOF#EOF#EOF#EOF#EOF#EOF#EOF#EOF#EOF#EOF#EOF#EOF#EOF#EOF#EOF
