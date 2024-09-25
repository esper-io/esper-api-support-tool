import sys

import numpy as np
import pandas as pd
from pandas.testing import assert_frame_equal

import Common.Globals as Globals


def constructDeviceAppRowEntry(device, deviceInfo):
    if (
        deviceInfo["appObj"]
        and "results" in deviceInfo["appObj"]
        and deviceInfo["appObj"]["results"]
    ):
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
                    "Group": (
                        deviceInfo["groups"] if "groups" in deviceInfo else ""
                    ),
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
                    "Group": (
                        deviceInfo["groups"] if "groups" in deviceInfo else ""
                    ),
                    "Application Name": app["app_name"],
                    "Application Type": app["app_type"],
                    "Application Version Code": "",
                    "Application Version Name": app.get(
                        "apple_app_version", ""
                    ),
                    "Package Name": app["bundle_id"],
                    "State": app.get("state", ""),
                    "Whitelisted": app.get("whitelisted", ""),
                    "Can Clear Data": app.get("is_data_clearable", ""),
                    "Can Uninstall": app.get("is_uninstallable", ""),
                }
                appInFilter = app["bundle_id"] in Globals.APP_COL_FILTER
            if (
                info
                and info not in deviceInfo["AppsEntry"]
                and info["Package Name"] not in Globals.BLACKLIST_PACKAGE_NAME
                and (
                    (Globals.APP_COL_FILTER and appInFilter)
                    or not Globals.APP_COL_FILTER
                )
            ):
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
            gridColType = Globals.GRID_COL_TYPES.get(col, "string").lower()
            col_type = data[col].dtype
            for _ in range(Globals.MAX_RETRY):
                if gridColType == "date":
                    data[col] = pd.to_datetime(
                        data[col], exact=False, errors="coerce"
                    )
                    data[col] = data[col].dt.strftime(Globals.DATE_COL[col])
                    data[col] = data[col].fillna("No Data Available")
                elif gridColType == "bool":
                    data[col] = data[col].astype("bool")
                elif gridColType == "number":
                    data.loc[data[col] == "None", col] = None
                    data.loc[data[col] == "", col] = None
                    with pd.option_context(
                        "future.no_silent_downcasting", True
                    ):
                        data[col] = (
                            data[col].fillna(0).infer_objects(copy=False)
                        )

                    try:
                        c_min = float(data[col].astype("float64").min())
                        c_max = float(data[col].astype("float64").max())

                        isDigit = False
                        if str(col_type)[:3] != "int":
                            try:
                                isDigit = data[col].str.isdigit().any()
                            except:
                                isDigit = (
                                    data[col]
                                    .astype(pd.StringDtype())
                                    .str.isdigit()
                                    .any()
                                )

                        if str(col_type)[:3] == "int" or isDigit:
                            if (
                                c_min > np.iinfo(np.int8).min
                                and c_max < np.iinfo(np.int8).max
                            ):
                                data[col] = data[col].astype(np.int8)
                            elif (
                                c_min > np.iinfo(np.uint8).min
                                and c_max < np.iinfo(np.uint8).max
                            ):
                                data[col] = data[col].astype(np.uint8)
                            elif (
                                c_min > np.iinfo(np.int16).min
                                and c_max < np.iinfo(np.int16).max
                            ):
                                data[col] = data[col].astype(np.int16)
                            elif (
                                c_min > np.iinfo(np.uint16).min
                                and c_max < np.iinfo(np.uint16).max
                            ):
                                data[col] = data[col].astype(np.uint16)
                            elif (
                                c_min > np.iinfo(np.int32).min
                                and c_max < np.iinfo(np.int32).max
                            ):
                                data[col] = data[col].astype(np.int32)
                            elif (
                                c_min > np.iinfo(np.uint32).min
                                and c_max < np.iinfo(np.uint32).max
                            ):
                                data[col] = data[col].astype(np.uint32)
                            elif (
                                c_min > np.iinfo(np.int64).min
                                and c_max < np.iinfo(np.int64).max
                            ):
                                data[col] = data[col].astype(np.int64)
                            elif (
                                c_min > np.iinfo(np.uint64).min
                                and c_max < np.iinfo(np.uint64).max
                            ):
                                data[col] = data[col].astype(np.uint64)
                        else:
                            if (
                                c_min > np.finfo(np.float16).min
                                and c_max < np.finfo(np.float16).max
                            ):
                                data[col] = data[col].astype(np.float16)
                            elif (
                                c_min > np.finfo(np.float32).min
                                and c_max < np.finfo(np.float32).max
                            ):
                                data[col] = data[col].astype(np.float32)
                            else:
                                data[col] = data[col].astype(np.float64)
                    except Exception as e:
                        print(e)
                elif gridColType == "category":
                    data[col] = data[col].astype("category")
                else:
                    data[col] = data[col].astype(pd.StringDtype())

                if col_type != data[col].dtype:
                    break
            if col_type == data[col].dtype:
                data[col] = data[col].astype(pd.StringDtype())
    return data
