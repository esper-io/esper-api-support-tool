import Common.Globals as Globals

def constructDeviceAppRowEntry(device, deviceInfo):
    if deviceInfo["appObj"] and "results" in deviceInfo["appObj"]:
        deviceInfo["AppsEntry"] = []
        info = {}
        for app in deviceInfo["appObj"]["results"]:
            if app["package_name"] not in Globals.BLACKLIST_PACKAGE_NAME:
                esperName = ""
                if hasattr(device, "device_name"):
                    esperName = device.device_name
                elif "device_name" in device:
                    esperName = device["device_name"]
                elif "name" in device:
                    esperName = device["name"]
                info = {
                    "Esper Name": esperName,
                    "Group": deviceInfo["groups"] if "groups" in deviceInfo else "",
                    "Application Name": app["app_name"],
                    "Application Type": app["app_type"],
                    "Application Version Code": app["version_code"],
                    "Application Version Name": app["version_name"],
                    "Package Name": app["package_name"],
                    "State": app["state"],
                    "Whitelisted": app["whitelisted"],
                    "Can Clear Data": app["is_data_clearable"],
                    "Can Uninstall": app["is_uninstallable"],
                }
            if info and info not in deviceInfo["AppsEntry"]:
                deviceInfo["AppsEntry"].append(info)