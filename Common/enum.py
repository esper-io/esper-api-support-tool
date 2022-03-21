#!/usr/bin/env python

import wx

from enum import Enum


class GeneralActions(Enum):
    # REPORTS
    SHOW_ALL_AND_GENERATE_REPORT = 1
    GENERATE_DEVICE_REPORT = 14
    GENERATE_APP_REPORT = 12
    GENERATE_INFO_REPORT = 13

    # Actions
    SET_DEVICE_MODE = 1.5
    SET_KIOSK = 2
    SET_MULTI = 3
    CLEAR_APP_DATA = 4
    SET_APP_STATE = 7
    REMOVE_NON_WHITELIST_AP = 8
    MOVE_GROUP = 9
    INSTALL_APP = 10
    UNINSTALL_APP = 11


class GridActions(Enum):
    MODIFY_ALIAS_AND_TAGS = 30
    SET_APP_STATE = 33
    MOVE_GROUP = 34
    INSTALL_APP = 35
    UNINSTALL_APP = 36
    INSTALL_LATEST_APP = 37
    UNINSTALL_LISTED_APP = 38
    FACTORY_RESET = 39
    SET_DEVICE_DISABLED = 40


class DeviceState(Enum):
    DEVICE_STATE_UNSPECIFIED = 0
    ACTIVE = 1
    DISABLED = 20
    PROVISIONING_BEGIN = 30
    GOOGLE_PLAY_CONFIGURATION = 40
    POLICY_APPLICATION_IN_PROGRESS = 50

    INACTIVE = 60  # This state is set by cloud, when device is unreachable
    WIPE_IN_PROGRESS = 70  # State set by cloud, in the 5 minute waiting period for WIPE


class Color(Enum):
    white = wx.Colour(255, 255, 255)
    black = wx.Colour(0, 0, 0)
    grey = wx.Colour(192, 192, 192)
    red = wx.Colour(255, 0, 0)
    blue = wx.Colour(0, 0, 255)
    orange = wx.Colour(255, 165, 0)
    green = wx.Colour(0, 128, 0)
    purple = wx.Colour(128, 0, 128)

    darkGrey = wx.Colour(100, 100, 100)

    lightBlue = wx.Colour(204, 255, 255)
    lightYellow = wx.Colour(255, 255, 224)
    lightGreen = wx.Colour(229, 248, 229)
    lightRed = wx.Colour(255, 235, 234)
    lightOrange = wx.Colour(255, 241, 216)
    lightPurple = wx.Colour(255, 226, 255)
    lightGrey = wx.Colour(211, 211, 211)

    errorBg = wx.Colour(255, 235, 234)
    warnBg = wx.Colour(255, 241, 216)
