#!/usr/bin/env python

import ast
import json
import time

import esperclient
import wx
from esperclient.models.v0_command_args import V0CommandArgs

import Common.Globals as Globals
import Utility.EventUtility as eventUtil
from Common.decorator import api_tool_decorator
from GUI.Dialogs.CmdConfirmDialog import CmdConfirmDialog
from Utility.Logging.ApiToolLogging import ApiToolLog
from Utility.Resource import (
    displayMessageBox,
    getHeader,
    getTenant,
    logBadResponse,
    postEventToFrame,
    splitListIntoChunks,
)
from Utility.Web.WebRequests import (
    performGetRequestWithRetry,
    performPostRequestWithRetry,
)


@api_tool_decorator()
def createCommand(frame, command_args, commandType, schedule, schType, combineRequests=False):
    """Attempt to apply a Command given user specifications"""
    
    # Audit log command initiation
    postEventToFrame(
        eventUtil.myEVT_AUDIT,
        {
            "operation": commandType,
            "data": f"Command: {commandType} Schedule: {schType} Args: {str(command_args) if command_args else 'None'}",
        },
    )
    
    result, isGroup = confirmCommand(command_args, commandType, schedule, schType)

    if schType.lower() == "immediate":
        schType = esperclient.V0CommandScheduleEnum.IMMEDIATE
    elif schType.lower() == "window":
        schType = esperclient.V0CommandScheduleEnum.WINDOW
    elif schType.lower() == "recurring":
        schType = esperclient.V0CommandScheduleEnum.RECURRING
    t = None
    if result and isGroup:
        Globals.THREAD_POOL.enqueue(
            executeCommandOnGroup,
            frame,
            command_args,
            schedule,
            schType,
            commandType,
            combineRequests=combineRequests,
        )
    elif result and not isGroup:
        Globals.THREAD_POOL.enqueue(
            executeCommandOnDevice,
            frame,
            command_args,
            schedule,
            schType,
            commandType,
            combineRequests=combineRequests,
        )
    if t:
        frame.menubar.disableConfigMenu()
        frame.statusBar.gauge.Pulse()


@api_tool_decorator()
def confirmCommand(cmd, commandType, schedule, schType):
    """Ask user to confirm the command they want to run"""
    modal = None
    isGroup = False
    cmd_dict = ast.literal_eval(str(cmd).replace("\n", ""))
    sch_dict = ast.literal_eval(str(schedule).replace("\n", ""))
    cmdFormatted = json.dumps(cmd_dict, indent=2)
    schFormatted = json.dumps(sch_dict, indent=2)
    label = ""
    applyTo = ""
    commaSeperated = ", "
    # Safe access to frame selections
    selections = []
    
    try:
        if (Globals.frame and 
            hasattr(Globals.frame, 'sidePanel') and
            hasattr(Globals.frame.sidePanel, 'selectedDevicesList') and
            len(Globals.frame.sidePanel.selectedDevicesList) > 0):
            
            selections = Globals.frame.sidePanel.selectedDevicesList
            label = ""
            for device in selections:
                if device:  # Ensure device is not None
                    label += str(device) + commaSeperated
            if label.endswith(", "):
                label = label[0 : len(label) - len(commaSeperated)]
            applyTo = "device"
            
        elif (Globals.frame and 
              hasattr(Globals.frame, 'sidePanel') and
              hasattr(Globals.frame.sidePanel, 'selectedGroupsList') and
              len(Globals.frame.sidePanel.selectedGroupsList) >= 0):
              
            selections = Globals.frame.sidePanel.selectedGroupsList
            label = ""
            for group in selections:
                if group:
                    label += str(group) + commaSeperated
            if label.endswith(", "):
                label = label[0 : len(label) - len(commaSeperated)]
        else:
            ApiToolLog().LogError("Frame or side panel not properly initialized")
            
    except (AttributeError, TypeError) as e:
        ApiToolLog().LogError(f"Error accessing frame selections: {str(e)}")
        selections = []
        label = "Unknown"
        applyTo = "group"
        isGroup = True
    modal = wx.NO
    if label:
        with CmdConfirmDialog(commandType, cmdFormatted, schType, schFormatted, applyTo, label) as dialog:
            Globals.OPEN_DIALOGS.append(dialog)
            res = dialog.ShowModal()
            Globals.OPEN_DIALOGS.remove(dialog)
            if res == wx.ID_OK:
                modal = wx.YES
    else:
        displayMessageBox(
            (
                "ERROR: No valid inputs from device/group selection.",
                wx.ICON_ERROR,
            )
        )

    if modal == wx.YES:
        return True, isGroup
    else:
        return False, isGroup


@api_tool_decorator()
def executeCommandOnGroup(
    frame,
    command_args,
    schedule=None,
    schedule_type="IMMEDIATE",
    command_type="UPDATE_DEVICE_CONFIG",
    groupIds=None,
    maxAttempt=Globals.MAX_RETRY,
    postStatus=True,
    combineRequests=False,
):
    """Execute a Command on a Group of Devices"""
    statusList = []
    groupList = frame.sidePanel.selectedGroupsList
    if groupIds and isinstance(groupIds, str):
        groupList = [groupIds]
    elif groupIds and hasattr(groupIds, "__iter__"):
        groupList = groupIds

    if len(groupList) == 1 and "" in groupList:
        groupList = list(Globals.knownGroups.keys())
        groupList.remove("* All Devices In Tenant *")

    if not combineRequests:
        for groupToUse in groupList:
            last_status = sendCommandToGroup(
                [groupToUse],
                command_type,
                command_args,
                schedule_type,
                schedule,
                maxAttempt,
            )
            executeCommandHelper(
                sendCommandToGroup,
                [groupToUse],
                command_type,
                command_args,
                schedule_type,
                schedule,
                maxAttempt,
                statusList,
                isGroup=True,
            )
            entryName = list(
                filter(
                    lambda x: groupToUse == x[1],
                    frame.sidePanel.devices.items(),
                )
            )
            if entryName:
                entryName = entryName[0]
            if last_status and hasattr(last_status, "state"):
                entry = {}
                if entryName and len(entryName) > 1:
                    entry["Group Name"] = entryName[0]
                    entry["Group Id"] = entryName[1]
                else:
                    entry["Group Id"] = groupToUse
                if hasattr(last_status, "id"):
                    entry["Command Id"] = last_status.id
                entry["Status State"] = last_status.state
                if hasattr(last_status, "reason"):
                    entry["Reason"] = last_status.reason
                statusList.append(entry)
            else:
                entry = {}
                if entryName and len(entryName) > 1:
                    entry["Group Name"] = entryName[0]
                    entry["Group Id"] = entryName[1]
                else:
                    entry["Group Id"] = groupToUse
                if hasattr(last_status, "state"):
                    entry["Command Id"] = last_status.id
                entry["Status"] = last_status
                statusList.append(entry)
    else:
        splitGroupList = splitListIntoChunks(groupList, maxChunkSize=500)
        for gList in splitGroupList:
            executeCommandHelper(
                sendCommandToGroup,
                gList,
                command_type,
                command_args,
                schedule_type,
                schedule,
                maxAttempt,
                statusList,
                isGroup=True,
            )
    if postStatus:
        postEventToFrame(eventUtil.myEVT_COMMAND, statusList)
    return statusList


@api_tool_decorator()
def executeCommandOnDevice(
    frame,
    command_args,
    schedule=None,
    schedule_type="IMMEDIATE",
    command_type="UPDATE_DEVICE_CONFIG",
    deviceIds=None,
    maxAttempt=Globals.MAX_RETRY,
    postStatus=True,
    combineRequests=False,
):
    """Execute a Command on a Device"""
    statusList = []
    devicelist = frame.sidePanel.selectedDevicesList
    if deviceIds and isinstance(deviceIds, str):
        devicelist = [deviceIds]
    elif deviceIds and hasattr(deviceIds, "__iter__"):
        devicelist = deviceIds
    if not combineRequests:
        for deviceToUse in devicelist:
            executeCommandHelper(
                sendCommandToDevice,
                [deviceToUse],
                command_type,
                command_args,
                schedule_type,
                schedule,
                maxAttempt,
                statusList,
            )
    else:
        splitDeviceList = splitListIntoChunks(devicelist, maxChunkSize=500)
        for dList in splitDeviceList:
            executeCommandHelper(
                sendCommandToDevice,
                dList,
                command_type,
                command_args,
                schedule_type,
                schedule,
                maxAttempt,
                statusList,
            )
    if postStatus:
        postEventToFrame(eventUtil.myEVT_COMMAND, statusList)
    return statusList


def executeCommandHelper(
    cmdFunc,
    targetList,
    command_type,
    command_args,
    schedule_type,
    schedule,
    maxAttempt,
    statusList,
    isGroup=False,
):
    last_status = cmdFunc(
        targetList,
        command_type,
        command_args,
        schedule_type,
        schedule,
        maxAttempt,
    )
    entry = {}
    if not isGroup:
        entry["Devices"] = targetList
    else:
        entry["Groups"] = targetList
    firstEntry = targetList[0]
    if len(targetList) == 1 and not isGroup:
        deviceEntryName = list(
            filter(
                lambda x: firstEntry == x[1],
                Globals.frame.sidePanel.devices.items(),
            )
        )
        deviceEntryName = deviceEntryName[0] if deviceEntryName else None
        entry["Device Id"] = firstEntry
        if deviceEntryName and len(deviceEntryName) > 1:
            parts = deviceEntryName[0].split(" ~ ")
            if len(parts) > 3:
                entry["Esper Name"] = parts[2]
                entry["Alias"] = parts[3]
            elif len(parts) > 2:
                entry["Esper Name"] = parts[2]
    elif len(targetList) == 1 and isGroup:
        entry["Group Id"] = firstEntry
        groupEntryName = Globals.knownGroups.get(firstEntry, None)
        if groupEntryName and groupEntryName.get("name", False):
            entry["Group Name"] = groupEntryName.get("name")

    if last_status and hasattr(last_status, "state"):
        entry["Status"] = last_status.state
        if hasattr(last_status, "id"):
            entry["Command Id"] = last_status.id
        if hasattr(last_status, "reason"):
            entry["Reason"] = last_status.reason
    elif type(last_status) is dict and "state" in last_status:
        entry["Status"] = last_status["state"]
        if "id" in last_status:
            entry["Command Id"] = last_status["id"]
        if "reason" in last_status:
            entry["Reason"] = last_status["reason"]
    else:
        entry["Status"] = last_status
    statusList.append(entry)


def sendCommandToDevice(
    deviceList,
    command_type,
    command_args,
    schedule_type,
    schedule,
    maxAttempt=Globals.MAX_RETRY,
):
    request = esperclient.V0CommandRequest(
        enterprise=Globals.enterprise_id,
        command_type="DEVICE",
        device_type=Globals.CMD_DEVICE_TYPE,
        devices=deviceList,
        command=command_type,
        command_args=command_args,
        schedule=schedule_type,
        schedule_args=schedule,
    )
    body = request.to_dict()
    removeKeyList = ["id", "enterprise", "issued_by", "created_on", "status"]
    for key in removeKeyList:
        body.pop(key, None)
    ignoreQueued = False if Globals.REACH_QUEUED_ONLY else True
    _, last_status = postEsperCommand(body, maxAttempt=maxAttempt)
    if last_status:
        last_status = waitForCommandToFinish(last_status["id"], ignoreQueue=ignoreQueued)
    return last_status


def sendCommandToGroup(
    groupList,
    command_type,
    command_args,
    schedule_type,
    schedule,
    maxAttempt=Globals.MAX_RETRY,
):
    request = esperclient.V0CommandRequest(
        enterprise=Globals.enterprise_id,
        command_type="GROUP",
        device_type=Globals.CMD_DEVICE_TYPE,
        groups=groupList,
        command=command_type,
        command_args=command_args,
        schedule=schedule_type,
        schedule_args=schedule,
    )
    body = request.to_dict()
    removeKeyList = ["id", "enterprise", "issued_by", "created_on", "status"]
    for key in removeKeyList:
        body.pop(key, None)
    ignoreQueued = False if Globals.REACH_QUEUED_ONLY else True
    _, last_status = postEsperCommand(body, maxAttempt=maxAttempt)
    if last_status:
        last_status = waitForCommandToFinish(last_status["id"], ignoreQueue=ignoreQueued)
    return last_status


@api_tool_decorator()
def waitForCommandToFinish(
    request_id,
    ignoreQueue=False,
    timeout=Globals.COMMAND_TIMEOUT,
    maxAttempt=Globals.MAX_RETRY,
):
    """Wait until a Command is done or it times out"""
    response = getCommandRequestStats(request_id, maxAttempt=maxAttempt)
    if response and "status" in response and response["status"]:
        cmdQueued = "Command Queued"
        stateList = [
            "Command Success",
            "Command Failure",
            "Command TimeOut",
            "Command Cancelled",
            cmdQueued,
            "Command Scheduled",
            # "Command Initated",
        ]
        if ignoreQueue:
            stateList.remove(cmdQueued)
        if type(response["status"]) is list:
            status = response["status"]
            postEventToFrame(eventUtil.myEVT_LOG, "---> Command state: %s" % str(status))
            start = time.perf_counter()
            queuedStatus = list(filter(lambda x: x["state"] == cmdQueued, status))
            if queuedStatus:
                queuedStatus = queuedStatus[0]
            else:
                return status
            while queuedStatus["total"] > 0:
                end = time.perf_counter()
                duration = end - start
                if duration >= timeout:
                    postEventToFrame(
                        eventUtil.myEVT_LOG,
                        "---> Skipping wait for Command, last logged Command state: %s (Device may be offline)" % str(status),
                    )
                    break
                status = getCommandRequestStats(request_id, maxAttempt=maxAttempt)
                if status and "status" in status and status["status"]:
                    queuedStatus = list(filter(lambda x: x["state"] == cmdQueued, status["status"]))
                    if queuedStatus:
                        queuedStatus = queuedStatus[0]
                    else:
                        break
            return status
        else:
            # Safe access to status array
            status_list = response.get("status", [])
            if status_list:
                status = status_list[0]
                state = status.get("state", "UNKNOWN") if isinstance(status, dict) else "INVALID"
                postEventToFrame(
                    eventUtil.myEVT_LOG,
                    "---> Command state: %s" % str(state),
                )
            else:
                ApiToolLog().LogError("No status found in command response")
                status = None

            start = time.perf_counter()
            while status and isinstance(status, dict) and status.get("state") not in stateList:
                end = time.perf_counter()
                duration = end - start
                if duration >= timeout:
                    statusState = status.get("state", "UNKNOWN") if isinstance(status, dict) else "UNKNOWN"
                    statusState = statusState if not hasattr(status, "state") else status.state
                    postEventToFrame(
                        eventUtil.myEVT_LOG,
                        "---> Skipping wait for Command, last logged Command state: %s (Device may be offline)"
                        % str(statusState),
                    )
                    break
                status = getCommandRequestStats(request_id, maxAttempt=maxAttempt)
                if status and isinstance(status, dict):
                    statusState = status.get("state", "UNKNOWN") if isinstance(status, dict) else "UNKNOWN"
                    statusState = statusState if not hasattr(status, "state") else status.state
                    postEventToFrame(
                        eventUtil.myEVT_LOG,
                        "---> Command state: %s" % str(statusState),
                    )
                time.sleep(3)
        return status
    else:
        return "No status found"


@api_tool_decorator()
def postEsperCommand(command_data, maxAttempt=Globals.MAX_RETRY):
    json_resp = None
    resp = None
    try:
        headers = getHeader()
        url = "https://%s-api.esper.cloud/api/commands/v0/commands/" % getTenant()
        resp = performPostRequestWithRetry(url, headers=headers, json=command_data, maxRetry=maxAttempt)
        json_resp = None
        
        # Safe JSON parsing with proper error handling
        if resp:
            try:
                json_resp = resp.json()
                if json_resp and isinstance(json_resp, dict) and "content" in json_resp:
                    json_resp = json_resp["content"]
            except (ValueError, TypeError, AttributeError) as e:
                ApiToolLog().LogError(f"Failed to parse command response JSON: {str(e)}")
                json_resp = None
        postEventToFrame(
            eventUtil.myEVT_AUDIT,
            {
                "operation": "Command(%s)" % command_data["command"],
                "data": command_data,
                "resp": resp,
            },
        )
        logBadResponse(url, resp, json_resp)
    except Exception as e:
        ApiToolLog().LogError(e, postStatus=False)
    return resp, json_resp


def getCommandRequestStats(command_id, maxAttempt=Globals.MAX_RETRY):
    url = "https://%s-api.esper.cloud/api/commands/v0/commands/%s/stats/" % (
        getTenant(),
        command_id,
    )
    json_resp = None
    resp = None
    try:
        headers = getHeader()
        resp = performGetRequestWithRetry(url, headers=headers, maxRetry=maxAttempt)
        json_resp = None
        
        # Safe JSON parsing with proper error handling
        if resp:
            try:
                json_resp = resp.json()
                if json_resp and isinstance(json_resp, dict) and "content" in json_resp:
                    json_resp = json_resp["content"]
            except (ValueError, TypeError, AttributeError) as e:
                ApiToolLog().LogError(f"Failed to parse command stats response JSON: {str(e)}")
                json_resp = None
        logBadResponse(url, resp, json_resp)
    except Exception as e:
        ApiToolLog().LogError(e, postStatus=False)
    return json_resp


@api_tool_decorator()
def sendPowerDownCommand():
    """Send a Power Down Command to the selected Devices"""
    command_args = V0CommandArgs(custom_settings_config={"dpcParams": [{"key": "powerOff", "value": "true"}]})
    createCommand(Globals.frame, command_args, "UPDATE_DEVICE_CONFIG", None, "immediate")
