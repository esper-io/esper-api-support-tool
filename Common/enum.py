#!/usr/bin/env python

from enum import Enum

import wx


class GeneralActions(Enum):
    # REPORTS
    SHOW_ALL_AND_GENERATE_REPORT = 1  # All
    GENERATE_INFO_REPORT = 2  # Device & Network
    GENERATE_DEVICE_REPORT = 3  # Device
    GENERATE_APP_REPORT = 4  # App

    # Actions
    REMOVE_NON_WHITELIST_AP = 55
    MOVE_GROUP = 56


class GridActions(Enum):
    MODIFY_ALIAS = 200
    MOVE_GROUP = 202
    MODIFY_TAGS = 209


class DeviceState(Enum):
    DEVICE_STATE_UNSPECIFIED = 0
    ACTIVE = 1
    DISABLED = 20
    PROVISIONING_BEGIN = 30
    GOOGLE_PLAY_CONFIGURATION = 40
    POLICY_APPLICATION_IN_PROGRESS = 50

    INACTIVE = 60  # This state is set by cloud, when device is unreachable
    WIPE_IN_PROGRESS = (
        70  # State set by cloud, in the 5 minute waiting period for WIPE
    )

    ONBOARDING_IN_PROGRESS = 80
    ONBOARDING_FAILED = 90
    ONBOARDED = 100

    AFW_ACCOUNT_ADDED = 110
    APPS_INSTALLED = 120
    BRANDING_PROCESSED = 130
    PERMISSION_POLICY_PROCESSED = 140
    DEVICE_POLICY_PROCESSED = 150
    DEVICE_SETTINGS_PROCESSED = 160
    SECURITY_POLICY_PROCESSED = 170
    PHONE_POLICY_PROCESSED = 180
    CUSTOM_SETTINGS_PROCESSED = 190


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
    darkMedGrey = wx.Colour(80, 80, 80)
    darkdarkGrey = wx.Colour(63, 63, 63)

    lightBlue = wx.Colour(204, 255, 255)
    lightYellow = wx.Colour(255, 255, 224)
    lightGreen = wx.Colour(229, 248, 229)
    lightRed = wx.Colour(255, 235, 234)
    lightOrange = wx.Colour(255, 241, 216)
    lightPurple = wx.Colour(255, 226, 255)
    lightGrey = wx.Colour(211, 211, 211)

    errorBg = wx.Colour(255, 235, 234)
    warnBg = wx.Colour(255, 241, 216)
