#!/usr/bin/env python

import wx

from enum import Enum


class GeneralActions(Enum):
    SHOW_ALL_AND_GENERATE_REPORT = 1
    SET_KIOSK = 2
    SET_MULTI = 3
    CLEAR_APP_DATA = 4
    SET_APP_STATE_SHOW = 5
    SET_APP_STATE_HIDE = 6
    SET_APP_STATE_DISABLE = 7
    REMOVE_NON_WHITELIST_AP = 8


class GridActions(Enum):
    MODIFY_ALIAS_AND_TAGS = 30
    SET_APP_STATE_SHOW = 31
    SET_APP_STATE_HIDE = 32
    SET_APP_STATE_DISABLE = 33


class Color(Enum):
    white = wx.Colour(255, 255, 255)
    black = wx.Colour(0, 0, 0)
    grey = wx.Colour(192, 192, 192)
    red = wx.Colour(255, 0, 0)
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

    errorBg = wx.Colour(255, 235, 234)
    warnBg = wx.Colour(255, 241, 216)
