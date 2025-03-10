""" UserProfileDB class is a front-end to the User Profile Database
"""

from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

__RCSID__ = "$Id$"

import six

import cachetools

from DIRAC import S_OK, S_ERROR
from DIRAC.ConfigurationSystem.Client.Helpers import Registry
from DIRAC.Core.Base.DB import DB


class UserProfileDB(DB):
    """UserProfileDB class is a front-end to the User Profile Database"""

    tableDict = {
        "up_Users": {
            "Fields": {
                "Id": "INTEGER AUTO_INCREMENT NOT NULL",
                "UserName": "VARCHAR(32) NOT NULL",
                "LastAccess": "DATETIME",
            },
            "PrimaryKey": "Id",
            "UniqueIndexes": {"U": ["UserName"]},
            "Engine": "InnoDB",
        },
        "up_Groups": {
            "Fields": {
                "Id": "INTEGER AUTO_INCREMENT NOT NULL",
                "UserGroup": "VARCHAR(32) NOT NULL",
                "LastAccess": "DATETIME",
            },
            "PrimaryKey": "Id",
            "UniqueIndexes": {"G": ["UserGroup"]},
            "Engine": "InnoDB",
        },
        "up_VOs": {
            "Fields": {
                "Id": "INTEGER AUTO_INCREMENT NOT NULL",
                "VO": "VARCHAR(32) NOT NULL",
                "LastAccess": "DATETIME",
            },
            "PrimaryKey": "Id",
            "UniqueIndexes": {"VO": ["VO"]},
            "Engine": "InnoDB",
        },
        "up_ProfilesData": {
            "Fields": {
                "UserId": "INTEGER",
                "GroupId": "INTEGER",
                "VOId": "INTEGER",
                "Profile": "VARCHAR(255) NOT NULL",
                "VarName": "VARCHAR(255) NOT NULL",
                "Data": "BLOB",
                "ReadAccess": 'VARCHAR(10) DEFAULT "USER"',
                "PublishAccess": 'VARCHAR(10) DEFAULT "USER"',
            },
            "PrimaryKey": ["UserId", "GroupId", "Profile", "VarName"],
            "Indexes": {
                "ProfileKey": ["UserId", "GroupId", "Profile"],
                "UserKey": ["UserId"],
            },
            "Engine": "InnoDB",
        },
    }

    def __init__(self):
        """Constructor"""
        self.__permValues = ["USER", "GROUP", "VO", "ALL"]
        self.__permAttrs = ["ReadAccess", "PublishAccess"]
        self.__cache = cachetools.TTLCache(1024, 15)
        DB.__init__(self, "UserProfileDB", "Framework/UserProfileDB")
        retVal = self.__initializeDB()
        if not retVal["OK"]:
            raise Exception("Can't create tables: %s" % retVal["Message"])

    def _checkTable(self):
        """Make sure the tables are created"""
        return self.__initializeDB()

    def __initializeDB(self):
        """
        Create the tables
        """
        retVal = self._query("show tables")
        if not retVal["OK"]:
            return retVal

        tablesInDB = [t[0] for t in retVal["Value"]]
        tablesD = {}

        if "up_Users" not in tablesInDB:
            tablesD["up_Users"] = self.tableDict["up_Users"]

        if "up_Groups" not in tablesInDB:
            tablesD["up_Groups"] = self.tableDict["up_Groups"]

        if "up_VOs" not in tablesInDB:
            tablesD["up_VOs"] = self.tableDict["up_VOs"]

        if "up_ProfilesData" not in tablesInDB:
            tablesD["up_ProfilesData"] = self.tableDict["up_ProfilesData"]

        return self._createTables(tablesD)

    def __getUserId(self, userName, insertIfMissing=True):
        return self.__getObjId(userName, "UserName", "up_Users", insertIfMissing)

    def __getGroupId(self, groupName, insertIfMissing=True):
        return self.__getObjId(groupName, "UserGroup", "up_Groups", insertIfMissing)

    def __getVOId(self, voName, insertIfMissing=True):
        return self.__getObjId(voName, "VO", "up_VOs", insertIfMissing)

    def __getFieldsCached(self, tableName, outFields, condDict):
        """Call getFields with a TTL cache

        The UserProfileDB is written in such a way that repeatedly makes the same
        DB queries thousands of times. To workaround this, use a simple short-lived
        TTL cache to dramatically improve performance.
        """
        key = (tableName, tuple(outFields), tuple(sorted(condDict.items())))
        if key in self.__cache:
            return self.__cache[key]
        result = self.getFields(tableName, outFields, condDict)
        if not result["OK"]:
            return result
        data = result["Value"]
        if len(data) > 0:
            objId = data[0][0]
            self.updateFields(tableName, ["LastAccess"], ["UTC_TIMESTAMP()"], {"Id": objId})
            self.__cache[key] = result
        return result

    def __getObjId(self, objValue, varName, tableName, insertIfMissing=True):
        result = self.__getFieldsCached(tableName, ["Id"], {varName: objValue})
        if not result["OK"]:
            return result
        data = result["Value"]
        if len(data) > 0:
            objId = data[0][0]
            return S_OK(objId)
        if not insertIfMissing:
            return S_ERROR("No entry %s for %s defined in the DB" % (objValue, varName))
        result = self.insertFields(tableName, [varName, "LastAccess"], [objValue, "UTC_TIMESTAMP()"])
        if not result["OK"]:
            return result
        return S_OK(result["lastRowId"])

    def getUserGroupIds(self, userName, userGroup, insertIfMissing=True):
        result = self.__getUserId(userName, insertIfMissing)
        if not result["OK"]:
            return result
        userId = result["Value"]
        result = self.__getGroupId(userGroup, insertIfMissing)
        if not result["OK"]:
            return result
        groupId = result["Value"]
        userVO = Registry.getVOForGroup(userGroup)
        if not userVO:
            userVO = "undefined"
        result = self.__getVOId(userVO, insertIfMissing)
        if not result["OK"]:
            return result
        voId = result["Value"]
        return S_OK((userId, groupId, voId))

    def deleteUserProfile(self, userName, userGroup=False):
        """
        Delete the profiles for a user
        """
        result = self.__getUserId(userName)
        if not result["OK"]:
            return result
        userId = result["Value"]
        condDict = {"UserId": userId}
        if userGroup:
            result = self.__getGroupId(userGroup)
            if not result["OK"]:
                return result
            groupId = result["Value"]
            condDict["GroupId"] = groupId
        result = self.deleteEntries("up_ProfilesData", condDict)
        if not result["OK"] or not userGroup:
            return result
        return self.deleteEntries("up_Users", {"Id": userId})

    def __webProfileUserDataCond(self, userIds, sqlProfileName=False, sqlVarName=False):
        condSQL = [
            "`up_ProfilesData`.UserId=%s" % userIds[0],
            "`up_ProfilesData`.GroupId=%s" % userIds[1],
            "`up_ProfilesData`.VOId=%s" % userIds[2],
        ]
        if sqlProfileName:
            condSQL.append("`up_ProfilesData`.Profile=%s" % sqlProfileName)
        if sqlVarName:
            condSQL.append("`up_ProfilesData`.VarName=%s" % sqlVarName)
        return " AND ".join(condSQL)

    def __webProfileReadAccessDataCond(self, userIds, ownerIds, sqlProfileName, sqlVarName=False, match=False):
        permCondSQL = []
        sqlCond = []

        if match:
            sqlCond.append(
                "`up_ProfilesData`.UserId = %s AND `up_ProfilesData`.GroupId = %s" % (ownerIds[0], ownerIds[1])
            )
        else:
            permCondSQL.append(
                "`up_ProfilesData`.UserId = %s AND `up_ProfilesData`.GroupId = %s" % (ownerIds[0], ownerIds[1])
            )

        permCondSQL.append('`up_ProfilesData`.GroupId=%s AND `up_ProfilesData`.ReadAccess="GROUP"' % userIds[1])
        permCondSQL.append('`up_ProfilesData`.VOId=%s AND `up_ProfilesData`.ReadAccess="VO"' % userIds[2])
        permCondSQL.append('`up_ProfilesData`.ReadAccess="ALL"')

        sqlCond.append("`up_ProfilesData`.Profile = %s" % sqlProfileName)
        if sqlVarName:
            sqlCond.append("`up_ProfilesData`.VarName = %s" % (sqlVarName))
        # Perms
        sqlCond.append("( ( %s ) )" % " ) OR ( ".join(permCondSQL))
        return " AND ".join(sqlCond)

    def __parsePerms(self, perms, addMissing=True):
        normPerms = {}
        for pName in self.__permAttrs:
            if not perms or pName not in perms:
                if addMissing:
                    normPerms[pName] = self.__permValues[0]
                continue
            permVal = perms[pName].upper()
            for nV in self.__permValues:
                if nV == permVal:
                    normPerms[pName] = nV
                    break
            if pName not in normPerms and addMissing:
                normPerms[pName] = self.__permValues[0]

        return normPerms

    def retrieveVarById(self, userIds, ownerIds, profileName, varName):
        """
        Get a data entry for a profile
        """
        result = self._escapeString(profileName)
        if not result["OK"]:
            return result
        sqlProfileName = result["Value"]

        result = self._escapeString(varName)
        if not result["OK"]:
            return result
        sqlVarName = result["Value"]

        sqlCond = self.__webProfileReadAccessDataCond(userIds, ownerIds, sqlProfileName, sqlVarName, True)
        # when we retrieve the user profile we have to take into account the user.
        selectSQL = "SELECT data FROM `up_ProfilesData` WHERE %s" % sqlCond
        result = self._query(selectSQL)
        if not result["OK"]:
            return result
        data = result["Value"]
        if len(data) > 0:
            return S_OK(data[0][0])
        return S_ERROR("No data for userIds %s profileName %s varName %s" % (userIds, profileName, varName))

    def retrieveAllUserVarsById(self, userIds, profileName):
        """
        Get a data entry for a profile
        """
        result = self._escapeString(profileName)
        if not result["OK"]:
            return result
        sqlProfileName = result["Value"]

        sqlCond = self.__webProfileUserDataCond(userIds, sqlProfileName)
        selectSQL = "SELECT varName, data FROM `up_ProfilesData` WHERE %s" % sqlCond
        result = self._query(selectSQL)
        if not result["OK"]:
            return result
        data = result["Value"]
        return S_OK(dict(data))

    def retrieveUserProfilesById(self, userIds):
        """
        Get all profiles and data for a user
        """
        sqlCond = self.__webProfileUserDataCond(userIds)
        selectSQL = "SELECT Profile, varName, data FROM `up_ProfilesData` WHERE %s" % sqlCond
        result = self._query(selectSQL)
        if not result["OK"]:
            return result
        data = result["Value"]
        dataDict = {}
        for row in data:
            if row[0] not in dataDict:
                dataDict[row[0]] = {}
            dataDict[row[0]][row[1]] = row[2]
        return S_OK(dataDict)

    def retrieveVarPermsById(self, userIds, ownerIds, profileName, varName):
        """
        Get a data entry for a profile
        """
        result = self._escapeString(profileName)
        if not result["OK"]:
            return result
        sqlProfileName = result["Value"]

        result = self._escapeString(varName)
        if not result["OK"]:
            return result
        sqlVarName = result["Value"]

        sqlCond = self.__webProfileReadAccessDataCond(userIds, ownerIds, sqlProfileName, sqlVarName)
        selectSQL = "SELECT %s FROM `up_ProfilesData` WHERE %s" % (", ".join(self.__permAttrs), sqlCond)
        result = self._query(selectSQL)
        if not result["OK"]:
            return result
        data = result["Value"]
        if len(data) > 0:
            permDict = {self.__permAttrs[i]: data[0][i] for i in range(len(self.__permAttrs))}
            return S_OK(permDict)
        return S_ERROR("No data for userIds %s profileName %s varName %s" % (userIds, profileName, varName))

    def deleteVarByUserId(self, userIds, profileName, varName):
        """
        Remove a data entry for a profile
        """
        result = self._escapeString(profileName)
        if not result["OK"]:
            return result
        sqlProfileName = result["Value"]

        result = self._escapeString(varName)
        if not result["OK"]:
            return result
        sqlVarName = result["Value"]

        sqlCond = self.__webProfileUserDataCond(userIds, sqlProfileName, sqlVarName)
        selectSQL = "DELETE FROM `up_ProfilesData` WHERE %s" % sqlCond
        return self._update(selectSQL)

    def storeVarByUserId(self, userIds, profileName, varName, data, perms):
        """
        Set a data entry for a profile
        """
        sqlInsertValues = []
        sqlInsertKeys = []

        sqlInsertKeys.append(("UserId", userIds[0]))
        sqlInsertKeys.append(("GroupId", userIds[1]))
        sqlInsertKeys.append(("VOId", userIds[2]))

        result = self._escapeString(profileName)
        if not result["OK"]:
            return result
        sqlProfileName = result["Value"]
        sqlInsertKeys.append(("Profile", sqlProfileName))

        result = self._escapeString(varName)
        if not result["OK"]:
            return result
        sqlVarName = result["Value"]
        sqlInsertKeys.append(("VarName", sqlVarName))

        result = self._escapeString(data)
        if not result["OK"]:
            return result
        sqlInsertValues.append(("Data", result["Value"]))

        normPerms = self.__parsePerms(perms)
        for k in normPerms:
            sqlInsertValues.append((k, '"%s"' % normPerms[k]))

        sqlInsert = sqlInsertKeys + sqlInsertValues
        insertSQL = "INSERT INTO `up_ProfilesData` ( %s ) VALUES ( %s )" % (
            ", ".join([f[0] for f in sqlInsert]),
            ", ".join([str(f[1]) for f in sqlInsert]),
        )
        result = self._update(insertSQL)
        if result["OK"]:
            return result
        # If error and not duplicate -> real error
        if "Duplicate entry" not in result["Message"]:
            return result
        updateSQL = "UPDATE `up_ProfilesData` SET %s WHERE %s" % (
            ", ".join(["%s=%s" % f for f in sqlInsertValues]),
            self.__webProfileUserDataCond(userIds, sqlProfileName, sqlVarName),
        )
        return self._update(updateSQL)

    def setUserVarPermsById(self, userIds, profileName, varName, perms):

        result = self._escapeString(profileName)
        if not result["OK"]:
            return result
        sqlProfileName = result["Value"]

        result = self._escapeString(varName)
        if not result["OK"]:
            return result
        sqlVarName = result["Value"]

        nPerms = self.__parsePerms(perms, False)
        if not nPerms:
            return S_OK()
        sqlPerms = ",".join("%s='%s'" % (k, nPerms[k]) for k in nPerms)

        updateSql = "UPDATE `up_ProfilesData` SET %s WHERE %s" % (
            sqlPerms,
            self.__webProfileUserDataCond(userIds, sqlProfileName, sqlVarName),
        )
        return self._update(updateSql)

    def retrieveVar(self, userName, userGroup, ownerName, ownerGroup, profileName, varName):
        """
        Get a data entry for a profile
        """
        result = self.getUserGroupIds(userName, userGroup)
        if not result["OK"]:
            return result
        userIds = result["Value"]

        result = self.getUserGroupIds(ownerName, ownerGroup)
        if not result["OK"]:
            return result
        ownerIds = result["Value"]

        return self.retrieveVarById(userIds, ownerIds, profileName, varName)

    def retrieveUserProfiles(self, userName, userGroup):
        """
        Helper for getting data
        """
        result = self.getUserGroupIds(userName, userGroup)
        if not result["OK"]:
            return result
        userIds = result["Value"]
        return self.retrieveUserProfilesById(userIds)

    def retrieveAllUserVars(self, userName, userGroup, profileName):
        """
        Helper for getting data
        """
        result = self.getUserGroupIds(userName, userGroup)
        if not result["OK"]:
            return result
        userIds = result["Value"]
        return self.retrieveAllUserVarsById(userIds, profileName)

    def retrieveVarPerms(self, userName, userGroup, ownerName, ownerGroup, profileName, varName):
        result = self.getUserGroupIds(userName, userGroup)
        if not result["OK"]:
            return result
        userIds = result["Value"]

        result = self.getUserGroupIds(ownerName, ownerGroup, False)
        if not result["OK"]:
            return result
        ownerIds = result["Value"]

        return self.retrieveVarPermsById(userIds, ownerIds, profileName, varName)

    def setUserVarPerms(self, userName, userGroup, profileName, varName, perms):
        result = self.getUserGroupIds(userName, userGroup)
        if not result["OK"]:
            return result
        userIds = result["Value"]
        return self.setUserVarPermsById(userIds, profileName, varName, perms)

    def storeVar(self, userName, userGroup, profileName, varName, data, perms=None):
        """
        Helper for setting data
        """
        result = self.getUserGroupIds(userName, userGroup)
        if not result["OK"]:
            return result
        userIds = result["Value"]
        return self.storeVarByUserId(userIds, profileName, varName, data, perms=perms)

    def deleteVar(self, userName, userGroup, profileName, varName):
        """
        Helper for deleting data
        """
        result = self.getUserGroupIds(userName, userGroup)
        if not result["OK"]:
            return result
        userIds = result["Value"]
        return self.deleteVarByUserId(userIds, profileName, varName)

    def __profilesCondGenerator(self, value, varType, initialValue=False):
        if isinstance(value, six.string_types):
            value = [value]
        ids = []
        if initialValue:
            ids.append(initialValue)
        for val in value:
            if varType == "user":
                result = self.__getUserId(val, insertIfMissing=False)
            elif varType == "group":
                result = self.__getGroupId(val, insertIfMissing=False)
            else:
                result = self.__getVOId(val, insertIfMissing=False)
            if not result["OK"]:
                continue
            ids.append(result["Value"])
        if varType == "user":
            fieldName = "UserId"
        elif varType == "group":
            fieldName = "GroupId"
        else:
            fieldName = "VOId"
        return "`up_ProfilesData`.%s in ( %s )" % (fieldName, ", ".join(str(iD) for iD in ids))

    def listVarsById(self, userIds, profileName, filterDict=None):
        result = self._escapeString(profileName)
        if not result["OK"]:
            return result
        sqlProfileName = result["Value"]
        sqlCond = [
            "`up_Users`.Id = `up_ProfilesData`.UserId",
            "`up_Groups`.Id = `up_ProfilesData`.GroupId",
            "`up_VOs`.Id = `up_ProfilesData`.VOId",
            self.__webProfileReadAccessDataCond(userIds, userIds, sqlProfileName),
        ]
        if filterDict:
            filterDict = {k.lower(): filterDict[k] for k in filterDict}
            for k in ("user", "group", "vo"):
                if k in filterDict:
                    sqlCond.append(self.__profilesCondGenerator(filterDict[k], k))

        sqlVars2Get = ["`up_Users`.UserName", "`up_Groups`.UserGroup", "`up_VOs`.VO", "`up_ProfilesData`.VarName"]
        sqlQuery = "SELECT %s FROM `up_Users`, `up_Groups`, `up_VOs`, `up_ProfilesData` WHERE %s" % (
            ", ".join(sqlVars2Get),
            " AND ".join(sqlCond),
        )

        return self._query(sqlQuery)

    def listVars(self, userName, userGroup, profileName, filterDict=None):
        result = self.getUserGroupIds(userName, userGroup)
        if not result["OK"]:
            return result
        userIds = result["Value"]
        return self.listVarsById(userIds, profileName, filterDict)

    def getUserProfileNames(self, permission):
        """
        it returns the available profile names by not taking account the permission: ReadAccess and PublishAccess
        """
        permissions = self.__parsePerms(permission, False)
        if not permissions:
            return S_OK([])

        condition = ",".join("%s='%s'" % (k, permissions[k]) for k in permissions)

        query = "SELECT distinct Profile from `up_ProfilesData` where %s" % condition
        retVal = self._query(query)
        if not retVal["OK"]:
            return retVal
        return S_OK([i[0] for i in retVal["Value"]])
