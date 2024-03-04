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
from Utility.Resource import (enforceRateLimit, getHeader, logBadResponse,
                              postEventToFrame, splitListIntoChunks)
from Utility.Web.WebRequests import performPostRequestWithRetry


@api_tool_decorator()
def createCommand(
    frame, command_args, commandType, schedule, schType, combineRequests=False
):
    """ Attempt to apply a Command given user specifications """
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
    """ Ask user to confirm the command they want to run """
    modal = None
    isGroup = False
    cmd_dict = ast.literal_eval(str(cmd).replace("\n", ""))
    sch_dict = ast.literal_eval(str(schedule).replace("\n", ""))
    cmdFormatted = json.dumps(cmd_dict, indent=2)
    schFormatted = json.dumps(sch_dict, indent=2)
    label = ""
    applyTo = ""
    commaSeperated = ", "
    if len(Globals.frame.sidePanel.selectedDevicesList) > 0:
        selections = Globals.frame.sidePanel.deviceMultiDialog.GetSelections()
        label = ""
        for device in selections:
            label += device + commaSeperated
        if label.endswith(", "):
            label = label[0 : len(label) - len(commaSeperated)]
        applyTo = "device"
    elif len(Globals.frame.sidePanel.selectedGroupsList) >= 0:
        selections = Globals.frame.sidePanel.groupMultiDialog.GetSelections()
        label = ""
        for group in selections:
            label += group + commaSeperated
        if label.endswith(", "):
            label = label[0 : len(label) - len(commaSeperated)]
        applyTo = "group"
        isGroup = True
    modal = wx.NO
    with CmdConfirmDialog(
        commandType, cmdFormatted, schType, schFormatted, applyTo, label
    ) as dialog:
        Globals.OPEN_DIALOGS.append(dialog)
        res = dialog.ShowModal()
        Globals.OPEN_DIALOGS.remove(dialog)
        if res == wx.ID_OK:
            modal = wx.YES

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
    """ Execute a Command on a Group of Devices """
    statusList = []
    groupList = frame.sidePanel.selectedGroupsList
    if groupIds and isinstance(groupIds, str):
        groupList = [groupIds]
    elif groupIds and hasattr(groupIds, "__iter__"):
        groupList = groupIds
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
            entryName = list(
                filter(lambda x: groupToUse == x[1], frame.sidePanel.devices.items())
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
            last_status = sendCommandToGroup(
                gList, command_type, command_args, schedule_type, schedule, maxAttempt
            )
            if last_status and hasattr(last_status, "state"):
                entry = {}
                entry["Groups"] = gList
                if hasattr(last_status, "id"):
                    entry["Command Id"] = last_status.id
                entry["Status State"] = last_status.state
                if hasattr(last_status, "reason"):
                    entry["Reason"] = last_status.reason
                statusList.append(entry)
            else:
                entry = {}
                entry["Groups"] = gList
                if hasattr(last_status, "state"):
                    entry["Command Id"] = last_status.id
                entry["Status"] = last_status
                statusList.append(entry)
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
    """ Execute a Command on a Device """
    statusList = []
    devicelist = frame.sidePanel.selectedDevicesList
    if deviceIds and isinstance(deviceIds, str):
        devicelist = [deviceIds]
    elif deviceIds and hasattr(deviceIds, "__iter__"):
        devicelist = deviceIds
    if not combineRequests:
        for deviceToUse in devicelist:
            last_status = sendCommandToDevice(
                [deviceToUse],
                command_type,
                command_args,
                schedule_type,
                schedule,
                maxAttempt,
            )
            deviceEntryName = list(
                filter(lambda x: deviceToUse == x[1], frame.sidePanel.devices.items())
            )
            if deviceEntryName:
                deviceEntryName = deviceEntryName[0]
            if last_status and hasattr(last_status, "state"):
                entry = {}
                if deviceEntryName and len(deviceEntryName) > 1:
                    parts = deviceEntryName[0].split(" ")
                    if len(parts) > 3:
                        entry["Esper Name"] = parts[2]
                        entry["Alias"] = parts[3]
                    elif len(parts) > 2:
                        entry["Esper Name"] = parts[2]
                    entry["Device Id"] = deviceEntryName[1]
                else:
                    entry["Device Id"] = deviceToUse
                if hasattr(last_status, "id"):
                    entry["Command Id"] = last_status.id
                entry["status"] = last_status.state
                if hasattr(last_status, "reason"):
                    entry["Reason"] = last_status.reason
                statusList.append(entry)
            else:
                entry = {}
                if deviceEntryName and len(deviceEntryName) > 1:
                    parts = deviceEntryName[0].split(" ")
                    if len(parts) > 3:
                        entry["Esper Name"] = parts[2]
                        entry["Alias"] = parts[3]
                    elif len(parts) > 2:
                        entry["Esper Name"] = parts[2]
                    entry["Device Id"] = deviceEntryName[1]
                else:
                    entry["Device Id"] = deviceToUse
                entry["Status"] = last_status
                statusList.append(entry)
    else:
        splitDeviceList = splitListIntoChunks(devicelist, maxChunkSize=500)
        for dList in splitDeviceList:
            last_status = sendCommandToDevice(
                dList, command_type, command_args, schedule_type, schedule, maxAttempt
            )
            if last_status and hasattr(last_status, "state"):
                entry = {}
                entry["Devices"] = dList
                if hasattr(last_status, "id"):
                    entry["Command Id"] = last_status.id
                entry["status"] = last_status.state
                if hasattr(last_status, "reason"):
                    entry["Reason"] = last_status.reason
                statusList.append(entry)
            else:
                entry = {}
                entry["Devices"] = dList
                entry["Status"] = last_status
                statusList.append(entry)
    if postStatus:
        postEventToFrame(eventUtil.myEVT_COMMAND, statusList)
    return statusList


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
    last_status = executeCommandAndWait(request, maxAttempt=maxAttempt)
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
    last_status = executeCommandAndWait(request, maxAttempt=maxAttempt)
    return last_status


def executeCommandAndWait(request, maxAttempt=Globals.MAX_RETRY):
    api_instance = getCommandsApiInstance()
    api_response = None
    for attempt in range(maxAttempt):
        try:
            enforceRateLimit()
            api_response = api_instance.create_command(Globals.enterprise_id, request)
            ApiToolLog().LogApiRequestOccurrence(
                "executeCommandAndWait",
                api_instance.create_command,
                Globals.PRINT_API_LOGS,
            )
            postEventToFrame(
                eventUtil.myEVT_AUDIT,
                {
                    "operation": "Command (%s)" % request.command,
                    "data": request,
                    "resp": api_response,
                },
            )
            break
        except Exception as e:
            if hasattr(e, "body") and (
                "invalid device id" in e.body or "invalid group id" in e.body
            ):
                logBadResponse("create command api", api_response, None)
                return None
            if attempt == maxAttempt - 1:
                ApiToolLog().LogError(e, postIssue=False)
                raise e
            if "429" not in str(e) and "Too Many Requests" not in str(e):
                time.sleep(Globals.RETRY_SLEEP)
            else:
                time.sleep(
                    Globals.RETRY_SLEEP * 20 * (attempt + 1)
                )  # Sleep for a minute * retry number
    ignoreQueued = False if Globals.REACH_QUEUED_ONLY else True
    last_status = waitForCommandToFinish(api_response.id, ignoreQueue=ignoreQueued)
    return last_status


@api_tool_decorator()
def waitForCommandToFinish(
    request_id,
    ignoreQueue=False,
    timeout=Globals.COMMAND_TIMEOUT,
    maxAttempt=Globals.MAX_RETRY,
):
    """ Wait until a Command is done or it times out """
    api_instance = getCommandsApiInstance()
    response = None
    for attempt in range(maxAttempt):
        try:
            enforceRateLimit()
            response = api_instance.get_command_request_status(
                Globals.enterprise_id, request_id
            )
            ApiToolLog().LogApiRequestOccurrence(
                "waitForCommandToFinish",
                api_instance.get_command_request_status,
                Globals.PRINT_API_LOGS,
            )
            break
        except Exception as e:
            if attempt == maxAttempt - 1:
                ApiToolLog().LogError(e, postIssue=False)
                raise e
            if "429" not in str(e) and "Too Many Requests" not in str(e):
                time.sleep(Globals.RETRY_SLEEP)
            else:
                time.sleep(
                    Globals.RETRY_SLEEP * 20 * (attempt + 1)
                )  # Sleep for a minute * retry number
    if response and response.results:
        status = response.results[0]
        postEventToFrame(
            eventUtil.myEVT_LOG, "---> Command state: %s" % str(status.state)
        )

        stateList = [
            "Command Success",
            "Command Failure",
            "Command TimeOut",
            "Command Cancelled",
            "Command Queued",
            "Command Scheduled",
            # "Command Initated",
        ]
        if ignoreQueue:
            stateList.remove("Command Queued")

        start = time.perf_counter()
        while status.state not in stateList:
            end = time.perf_counter()
            duration = end - start
            if duration >= timeout:
                postEventToFrame(
                    eventUtil.myEVT_LOG,
                    "---> Skipping wait for Command, last logged Command state: %s (Device may be offline)"
                    % str(status.state),
                )
                break
            for attempt in range(maxAttempt):
                try:
                    enforceRateLimit()
                    response = api_instance.get_command_request_status(
                        Globals.enterprise_id, request_id
                    )
                    ApiToolLog().LogApiRequestOccurrence(
                        "waitForCommandToFinish",
                        api_instance.get_command_request_status,
                        Globals.PRINT_API_LOGS,
                    )
                    break
                except Exception as e:
                    if attempt == maxAttempt - 1:
                        ApiToolLog().LogError(e, postIssue=False)
                        raise e
                    if "429" not in str(e) and "Too Many Requests" not in str(e):
                        time.sleep(Globals.RETRY_SLEEP)
                    else:
                        time.sleep(
                            Globals.RETRY_SLEEP * 20 * (attempt + 1)
                        )  # Sleep for a minute * retry number
            if response and response.results:
                status = response.results[0]
            postEventToFrame(
                eventUtil.myEVT_LOG, "---> Command state: %s" % str(status.state)
            )
            time.sleep(3)
        return status
    else:
        return "No status found"


@api_tool_decorator()
def getCommandsApiInstance():
    """ Returns an instace of the Commands API """
    return esperclient.CommandsV2Api(esperclient.ApiClient(Globals.configuration))


@api_tool_decorator()
def postEsperCommand(command_data, useV0=True):
    json_resp = None
    resp = None
    try:
        headers = getHeader()
        url = ""
        if useV0:
            url = "https://%s-api.esper.cloud/api/v0/enterprise/%s/command/" % (
                Globals.configuration.host.split("-api")[0].replace("https://", ""),
                Globals.enterprise_id,
            )
        else:
            url = "https://%s-api.esper.cloud/api/enterprise/%s/command/" % (
                Globals.configuration.host.split("-api")[0].replace("https://", ""),
                Globals.enterprise_id,
            )
        resp = performPostRequestWithRetry(url, headers=headers, json=command_data)
        json_resp = resp.json()
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
        ApiToolLog().LogError(e, postIssue=False)
    return resp, json_resp


@api_tool_decorator()
def sendPowerDownCommand():
    """ Send a Power Down Command to the selected Devices """
    command_args = V0CommandArgs(
        custom_settings_config={
            "dpcParams": [{"key": "powerOff", "value": "true"}]
        }
    )
    createCommand(Globals.frame, command_args, "UPDATE_DEVICE_CONFIG", None, "immediate")