#!/usr/bin/env python

import time

import requests

import Common.Globals as Globals
from Utility import EventUtility
from Utility.Logging.ApiToolLogging import ApiToolLog
from Utility.Resource import (checkIfCurrentThreadStopped, enforceRateLimit,
                              getHeader, postEventToFrame)


def performGetRequestWithRetry(
    url, headers=None, json=None, data=None, maxRetry=Globals.MAX_RETRY
):
    resp = None
    for attempt in range(maxRetry):
        try:
            enforceRateLimit()
            resp = requests.get(url, headers=headers, json=json, data=data)
            ApiToolLog().LogApiRequestOccurrence(
                performGetRequestWithRetry.__name__, url, Globals.PRINT_API_LOGS
            )
            if resp.status_code < 300 or (resp.status_code == 500 and attempt >= 2):
                break
            if resp.status_code == 429:
                if attempt == 0:
                    postEventToFrame(
                        EventUtility.myEVT_LOG,
                        "Rate Limit Encountered retrying in 1 minute",
                    )
                else:
                    postEventToFrame(
                        EventUtility.myEVT_LOG,
                        "Rate Limit Encountered retrying in %s minutes" % attempt + 1,
                    )
                time.sleep(
                    Globals.RETRY_SLEEP * 20 * (attempt + 1)
                )  # Sleep for a minute * retry number
        except Exception as e:
            if attempt == maxRetry - 1:
                ApiToolLog().LogError(e, postIssue=False)
            if "429" not in str(e) and "Too Many Requests" not in str(e):
                time.sleep(Globals.RETRY_SLEEP)
            else:
                if attempt == 0:
                    postEventToFrame(
                        EventUtility.myEVT_LOG,
                        "Rate Limit Encountered retrying in 1 minute",
                    )
                else:
                    postEventToFrame(
                        EventUtility.myEVT_LOG,
                        "Rate Limit Encountered retrying in %s minutes" % attempt + 1,
                    )
                time.sleep(
                    Globals.RETRY_SLEEP * 20 * (attempt + 1)
                )  # Sleep for a minute * retry number
            postEventToFrame(EventUtility.myEVT_LOG, str(e))
    return resp


def performPatchRequestWithRetry(
    url, headers=None, json=None, data=None, maxRetry=Globals.MAX_RETRY
):
    resp = None
    for attempt in range(maxRetry):
        try:
            enforceRateLimit()
            resp = requests.patch(url, headers=headers, data=data, json=json)
            ApiToolLog().LogApiRequestOccurrence(
                performPatchRequestWithRetry.__name__, url, Globals.PRINT_API_LOGS
            )
            if resp.status_code < 300 or (resp.status_code == 500 and attempt >= 2):
                break
            if resp.status_code == 429:
                if attempt == 0:
                    postEventToFrame(
                        EventUtility.myEVT_LOG,
                        "Rate Limit Encountered retrying in 1 minute",
                    )
                else:
                    postEventToFrame(
                        EventUtility.myEVT_LOG,
                        "Rate Limit Encountered retrying in %s minutes" % attempt + 1,
                    )
                time.sleep(
                    Globals.RETRY_SLEEP * 20 * (attempt + 1)
                )  # Sleep for a minute * retry number
        except Exception as e:
            if attempt == maxRetry - 1:
                ApiToolLog().LogError(e, postIssue=False)
            if "429" not in str(e) and "Too Many Requests" not in str(e):
                time.sleep(Globals.RETRY_SLEEP)
            else:
                if attempt == 0:
                    postEventToFrame(
                        EventUtility.myEVT_LOG,
                        "Rate Limit Encountered retrying in 1 minute",
                    )
                else:
                    postEventToFrame(
                        EventUtility.myEVT_LOG,
                        "Rate Limit Encountered retrying in %s minutes" % attempt + 1,
                    )
                time.sleep(
                    Globals.RETRY_SLEEP * 20 * (attempt + 1)
                )  # Sleep for a minute * retry number
            postEventToFrame(EventUtility.myEVT_LOG, str(e))
    return resp


def performPutRequestWithRetry(
    url, headers=None, json=None, data=None, maxRetry=Globals.MAX_RETRY
):
    resp = None
    for attempt in range(maxRetry):
        try:
            enforceRateLimit()
            resp = requests.put(url, headers=headers, data=data, json=json)
            ApiToolLog().LogApiRequestOccurrence(
                performPutRequestWithRetry.__name__, url, Globals.PRINT_API_LOGS
            )
            if resp.status_code < 300 or (resp.status_code == 500 and attempt >= 2):
                break
            if resp.status_code == 429:
                if attempt == 0:
                    postEventToFrame(
                        EventUtility.myEVT_LOG,
                        "Rate Limit Encountered retrying in 1 minute",
                    )
                else:
                    postEventToFrame(
                        EventUtility.myEVT_LOG,
                        "Rate Limit Encountered retrying in %s minutes" % attempt + 1,
                    )
                time.sleep(
                    Globals.RETRY_SLEEP * 20 * (attempt + 1)
                )  # Sleep for a minute * retry number
            if resp.status_code == 500 and attempt >= 2:
                break
        except Exception as e:
            if attempt == maxRetry - 1:
                ApiToolLog().LogError(e, postIssue=False)
            if "429" not in str(e) and "Too Many Requests" not in str(e):
                time.sleep(Globals.RETRY_SLEEP)
            else:
                if attempt == 0:
                    postEventToFrame(
                        EventUtility.myEVT_LOG,
                        "Rate Limit Encountered retrying in 1 minute",
                    )
                else:
                    postEventToFrame(
                        EventUtility.myEVT_LOG,
                        "Rate Limit Encountered retrying in %s minutes" % attempt + 1,
                    )
                time.sleep(
                    Globals.RETRY_SLEEP * 20 * (attempt + 1)
                )  # Sleep for a minute * retry number
            postEventToFrame(EventUtility.myEVT_LOG, str(e))
    return resp


def performDeleteRequestWithRetry(
    url, headers=None, json=None, data=None, maxRetry=Globals.MAX_RETRY
):
    resp = None
    for attempt in range(maxRetry):
        try:
            enforceRateLimit()
            resp = requests.delete(url, headers=headers, data=data, json=json)
            ApiToolLog().LogApiRequestOccurrence(
                performDeleteRequestWithRetry.__name__, url, Globals.PRINT_API_LOGS
            )
            if resp.status_code < 300 or (resp.status_code == 500 and attempt >= 2):
                break
            if resp.status_code == 429:
                if attempt == 0:
                    postEventToFrame(
                        EventUtility.myEVT_LOG,
                        "Rate Limit Encountered retrying in 1 minute",
                    )
                else:
                    postEventToFrame(
                        EventUtility.myEVT_LOG,
                        "Rate Limit Encountered retrying in %s minutes" % attempt + 1,
                    )
                time.sleep(
                    Globals.RETRY_SLEEP * 20 * (attempt + 1)
                )  # Sleep for a minute * retry number
            if resp.status_code == 500 and attempt >= 2:
                break
        except Exception as e:
            if attempt == maxRetry - 1:
                ApiToolLog().LogError(e, postIssue=False)
            if "429" not in str(e) and "Too Many Requests" not in str(e):
                time.sleep(Globals.RETRY_SLEEP)
            else:
                if attempt == 0:
                    postEventToFrame(
                        EventUtility.myEVT_LOG,
                        "Rate Limit Encountered retrying in 1 minute",
                    )
                else:
                    postEventToFrame(
                        EventUtility.myEVT_LOG,
                        "Rate Limit Encountered retrying in %s minutes" % attempt + 1,
                    )
                time.sleep(
                    Globals.RETRY_SLEEP * 20 * (attempt + 1)
                )  # Sleep for a minute * retry number
            postEventToFrame(EventUtility.myEVT_LOG, str(e))
    return resp


def performPostRequestWithRetry(
    url, headers=None, json=None, data=None, files=None, maxRetry=Globals.MAX_RETRY
):
    resp = None
    for attempt in range(maxRetry):
        try:
            enforceRateLimit()
            resp = requests.post(
                url, headers=headers, data=data, json=json, files=files
            )
            ApiToolLog().LogApiRequestOccurrence(
                performPostRequestWithRetry.__name__, url, Globals.PRINT_API_LOGS
            )
            if resp.status_code < 300 or (resp.status_code == 500 and attempt >= 2):
                break
            if resp.status_code == 429:
                if attempt == 0:
                    postEventToFrame(
                        EventUtility.myEVT_LOG,
                        "Rate Limit Encountered retrying in 1 minute",
                    )
                else:
                    postEventToFrame(
                        EventUtility.myEVT_LOG,
                        "Rate Limit Encountered retrying in %s minutes" % attempt + 1,
                    )
                time.sleep(
                    Globals.RETRY_SLEEP * 20 * (attempt + 1)
                )  # Sleep for a minute * retry number
        except Exception as e:
            if attempt == maxRetry - 1:
                ApiToolLog().LogError(e, postIssue=False)
            if "429" not in str(e) and "Too Many Requests" not in str(e):
                time.sleep(Globals.RETRY_SLEEP)
            else:
                if attempt == 0:
                    postEventToFrame(
                        EventUtility.myEVT_LOG,
                        "Rate Limit Encountered retrying in 1 minute",
                    )
                else:
                    postEventToFrame(
                        EventUtility.myEVT_LOG,
                        "Rate Limit Encountered retrying in %s minutes" % attempt + 1,
                    )
                time.sleep(
                    Globals.RETRY_SLEEP * 20 * (attempt + 1)
                )  # Sleep for a minute * retry number
            postEventToFrame(EventUtility.myEVT_LOG, str(e))
    return resp


def getAllFromOffsetsRequests(api_response, results=None, tolarance=0, timeout=-1):
    count = None
    if not results:
        results = []
    if hasattr(api_response, "count"):
        count = api_response.count
    elif type(api_response) is dict and "count" in api_response:
        count = api_response["count"]
    apiNext = None
    if hasattr(api_response, "next"):
        apiNext = api_response.next
    elif type(api_response) is dict and "next" in api_response:
        apiNext = api_response["next"]
    if apiNext:
        respOffset = apiNext.split("offset=")[-1].split("&")[0]
        respOffsetInt = int(respOffset)
        respLimit = apiNext.split("limit=")[-1].split("&")[0]
        while int(respOffsetInt) < count and int(respLimit) < count:
            if checkIfCurrentThreadStopped():
                return
            url = apiNext.replace(
                "offset=%s" % respOffset, "offset=%s" % str(respOffsetInt)
            )
            Globals.THREAD_POOL.enqueue(
                perform_web_requests, (url, getHeader(), "GET", None)
            )
            respOffsetInt += int(respLimit)

    Globals.THREAD_POOL.join(tolarance, timeout)
    resultList = Globals.THREAD_POOL.results()
    for resp in resultList:
        if "content" in resp:
            resp = resp["content"]
        if resp and hasattr(resp, "results") and resp.results:
            results += resp.results
        elif type(resp) is dict and "results" in resp and resp["results"]:
            results += resp["results"]
    return results


def perform_web_requests(content):
    url = content[0].strip()
    header = content[1]
    method = content[2]
    json = content[3] if len(content) > 2 else None
    resp = None

    if method == "GET":
        resp = performGetRequestWithRetry(url, header, json)
    elif method == "POST":
        resp = performPostRequestWithRetry(url, header, json)
    elif method == "DELETE":
        resp = performDeleteRequestWithRetry(url, header, json)
    elif method == "PATCH":
        resp = performPatchRequestWithRetry(url, header, json)
    elif method == "PUT":
        resp = performPutRequestWithRetry(url, header, json)

    if resp:
        resp = resp.json()
    return resp
