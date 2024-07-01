import sys

import pandas as pd
from pandas.api.types import is_bool_dtype, is_string_dtype
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
                    "Whitelisted": str(app.get("whitelisted", "")),
                    "Can Clear Data": str(app.get("is_data_clearable", "")),
                    "Can Uninstall": str(app.get("is_uninstallable", "")),
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


def createDataFrameFromDict(headerList, sourceData, convertTypes=False):
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
                        if k in row and row[k]:
                            value = row[k]
                            break
                newData[columnName].append(value)
        elif type(headerList) is list:
            for header in headerList:
                value = ""
                if header in row:
                    value = row[header]
                newData[header].append(value)
    df = pd.DataFrame(newData)
    if convertTypes:
        df = convertColumnTypes(df, headerList)
    return df


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

def convertColumnTypes(data, headers):
    for col in headers:
        if len(data[col]) > 0:
            if col in Globals.DATE_COL:
                data[col] = pd.to_datetime(data[col], exact=False, errors="coerce")
                data[col] = data[col].dt.strftime(Globals.DATE_COL[col])
                data[col].fillna("No Data Available", inplace=True)
            elif is_bool_dtype(data[col]):
                data[col] = data[col].astype("bool")
            elif is_string_dtype(data[col]) and all(data[col].str.isnumeric()):
                if float(data[col]) < sys.maxsize:
                    data[col] = data[col].astype("int64")
                else:
                    data[col] = data[col].astype("float64")

                    if "." not in data[col]:
                        data[col] = data[col].apply(lambda x: "{:.0f}".format(x))
                    else:
                        data[col] = data[col].apply(lambda x: "{:.2f}".format(x))
            else:
                data[col] = data[col].astype("str")
    return data
