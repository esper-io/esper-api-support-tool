#!/usr/bin/env python

from Utility.ApiToolLogging import ApiToolLog
from Utility.Resource import (
    getHeader,
    logBadResponse,
    performPostRequestWithRetry,
    postEventToFrame,
)
import ast
import time
import esperclient
import json
import wx

import Common.Globals as Globals
import Utility.wxThread as wxThread
import Utility.EventUtility as eventUtil

from Common.decorator import api_tool_decorator
from GUI.Dialogs.CmdConfirmDialog import CmdConfirmDialog

from esperclient.models.v0_command_args import V0CommandArgs


@api_tool_decorator()
def createCommand(frame, command_args, commandType, schedule, schType):
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
        t = wxThread.GUIThread(
            frame,
            executeCommandOnGroup,
            args=(frame, command_args, schedule, schType, commandType),
            eventType=eventUtil.myEVT_COMMAND,
            name="executeCommandOnGroup",
        )
    elif result and not isGroup:
        t = wxThread.GUIThread(
            frame,
            executeCommandOnDevice,
            args=(frame, command_args, schedule, schType, commandType),
            eventType=eventUtil.myEVT_COMMAND,
            name="executeCommandOnDevice",
        )
    if t:
        frame.menubar.disableConfigMenu()
        frame.gauge.Pulse()
        t.start()


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
        res = dialog.ShowModal()
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
):
    """ Execute a Command on a Group of Devices """
    statusList = []
    groupList = frame.sidePanel.selectedGroupsList
    if groupIds and isinstance(groupIds, str):
        groupList = [groupIds]
    elif groupIds and hasattr(groupIds, "__iter__"):
        groupList = groupIds
    for groupToUse in groupList:
        request = esperclient.V0CommandRequest(
            enterprise=Globals.enterprise_id,
            command_type="GROUP",
            device_type=Globals.CMD_DEVICE_TYPE,
            groups=[groupToUse],
            command=command_type,
            command_args=command_args,
            schedule=schedule_type,
            schedule_args=schedule,
        )
        last_status = executeCommandAndWait(request, maxAttempt=maxAttempt)
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
):
    """ Execute a Command on a Device """
    statusList = []
    devicelist = frame.sidePanel.selectedDevicesList
    if deviceIds and isinstance(deviceIds, str):
        devicelist = [deviceIds]
    elif deviceIds and hasattr(deviceIds, "__iter__"):
        devicelist = deviceIds
    for deviceToUse in devicelist:
        request = esperclient.V0CommandRequest(
            enterprise=Globals.enterprise_id,
            command_type="DEVICE",
            device_type=Globals.CMD_DEVICE_TYPE,
            devices=[deviceToUse],
            command=command_type,
            command_args=command_args,
            schedule=schedule_type,
            schedule_args=schedule,
        )
        last_status = executeCommandAndWait(request, maxAttempt=maxAttempt)
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
    return statusList


def executeCommandAndWait(request, maxAttempt=Globals.MAX_RETRY):
    api_instance = getCommandsApiInstance()
    api_response = None
    for attempt in range(maxAttempt):
        try:
            api_response = api_instance.create_command(Globals.enterprise_id, request)
            ApiToolLog().LogApiRequestOccurrence(
                "executeCommandAndWait",
                api_instance.create_command,
                Globals.PRINT_API_LOGS,
            )
            break
        except Exception as e:
            if hasattr(e, "body") and (
                "invalid device id" in e.body or "invalid group id" in e.body
            ):
                logBadResponse("create command api", api_response, None)
                return None
            if attempt == maxAttempt - 1:
                ApiToolLog().LogError(e)
                raise e
            time.sleep(Globals.RETRY_SLEEP)
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
                ApiToolLog().LogError(e)
                raise e
            time.sleep(Globals.RETRY_SLEEP)
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
                        ApiToolLog().LogError(e)
                        raise e
                    time.sleep(Globals.RETRY_SLEEP)
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
        logBadResponse(url, resp, json_resp)
    except Exception as e:
        ApiToolLog().LogError(e)
    return resp, json_resp
