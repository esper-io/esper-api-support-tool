import pandas as pd
from pandas.testing import assert_frame_equal

import Common.Globals as Globals


def constructDeviceAppRowEntry(device, deviceInfo):
    if deviceInfo["appObj"] and "results" in deviceInfo["appObj"] and deviceInfo["appObj"]["results"]:
        deviceInfo["AppsEntry"] = []
        info = {}
        for app in deviceInfo["appObj"]["results"]:
            esperName = ""
            if hasattr(device, "device_name"):
                esperName = device.device_name
            elif "device_name" in device:
                esperName = device["device_name"]
            elif "name" in device:
                esperName = device["name"]
            appInFilter = True
            if "package_name" in app:
                info = {
                    "Esper Name": esperName,
                    "Group": deviceInfo["groups"] if "groups" in deviceInfo else "",
                    "Application Name": app["app_name"],
                    "Application Type": app["app_type"],
                    "Application Version Code": app.get("version_code", ""),
                    "Application Version Name": app.get("version_name", ""),
                    "Package Name": app["package_name"],
                    "State": app.get("state", ""),
                    "Whitelisted": app.get("whitelisted", ""),
                    "Can Clear Data": app.get("is_data_clearable", ""),
                    "Can Uninstall": app.get("is_uninstallable", ""),
                }
                appInFilter = app["package_name"] in Globals.APP_COL_FILTER
            elif "bundle_id" in app:
                info = {
                    "Esper Name": esperName,
                    "Group": deviceInfo["groups"] if "groups" in deviceInfo else "",
                    "Application Name": app["app_name"],
                    "Application Type": app["app_type"],
                    "Application Version Code": app.get("apple_app_version", ""),
                    "Application Version Name": app.get("version_name", ""),
                    "Package Name": app["bundle_id"],
                    "State": app.get("state", ""),
                    "Whitelisted": app.get("whitelisted", ""),
                    "Can Clear Data": app.get("is_data_clearable", ""),
                    "Can Uninstall": app.get("is_uninstallable", ""),
                }
                appInFilter = app["bundle_id"] in Globals.APP_COL_FILTER
            if (info 
                and info not in deviceInfo["AppsEntry"]
                and  info["Package Name"] not in Globals.BLACKLIST_PACKAGE_NAME
                and ((
                        Globals.APP_COL_FILTER
                        and appInFilter
                    ) 
                    or not Globals.APP_COL_FILTER)):
                deviceInfo["AppsEntry"].append(info)


def createDataFrameFromDict(headerList, sourceData):
    newData = {}
    for header in headerList:
        newData[header] = []
    for row in sourceData:
        if type(headerList) is dict:
            for columnName, key in headerList.items():
                value = ""
                if type(key) is str and key in row:
                    value = row[key]
                elif type(key) is list:
                    for k in key:
                        if k in row:
                            value = row[k]
                            break
                newData[columnName].append(value)
        elif type(headerList) is list:
            for header in headerList:
                value = ""
                if header in row:
                    value = row[header]
                newData[header].append(value)
    return pd.DataFrame(newData)


def areDataFramesTheSame(df1, df2):
    try:
        assert_frame_equal(df1, df2)
        return True
    except:
        return False


def split_dataframe(df, chunk_size):
    chunks = []
    num_chunks = len(df) // chunk_size + 1
    for i in range(num_chunks):
        chunks.append(df[i * chunk_size : (i + 1) * chunk_size])
    return chunks
