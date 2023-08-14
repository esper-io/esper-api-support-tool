import Common.Globals as Globals
from Utility.API.CommandUtility import executeCommandOnDevice, executeCommandOnGroup

from Utility.API.DeviceUtility import getProperDeviceId
from Utility.API.GroupUtility import getProperGroupId


def setWidget(enable, widgetName=None, devices=[], groups=[]):
    if (not devices and not groups) or (enable and not widgetName):
        return
    command_arg = {"enable": enable, "widget_class_name": widgetName}
    if devices:
        properDeviceList = getProperDeviceId(devices)
        executeCommandOnDevice(
            Globals.frame,
            command_arg,
            command_type="SET_WIDGET",
            deviceIds=properDeviceList,
            postStatus=True,
            combineRequests=True,
        )
    if groups:
        properGroupList = getProperGroupId(groups)
        executeCommandOnGroup(
            Globals.frame,
            command_arg,
            command_type="SET_WIDGET",
            postStatus=True,
            combineRequests=True,
            groupIds=properGroupList,
        )
