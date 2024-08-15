#!/usr/bin/env python

import time

import requests

import Common.Globals as Globals
from Utility import EventUtility
from Utility.Logging.ApiToolLogging import ApiToolLog
from Utility.Resource import (
    checkIfCurrentThreadStopped,
    enforceRateLimit,
    getHeader,
    postEventToFrame,
)


def performRequestWithRetry(
    url,
    method,
    headers=None,
    json=None,
    data=None,
    files=None,
    maxRetry=Globals.MAX_RETRY,
):
    resp = None
    for attempt in range(maxRetry):
        try:
            enforceRateLimit()
            if files:
                resp = method(
                    url, headers=headers, json=json, data=data, files=files
                )
            else:
                resp = method(url, headers=headers, json=json, data=data)
            ApiToolLog().LogApiRequestOccurrence(
                method.__name__, url, Globals.PRINT_API_LOGS
            )
            if resp.status_code < 300 or (
                resp.status_code == 500 and attempt >= 2
            ):
                break
            if resp.status_code == 429:
                doExponentialBackoff(attempt)
        except Exception as e:
            handleRequestError(attempt, e, maxRetry)
    return resp


def handleRequestError(attempt, e, maxRetry, raiseError=False):
    if attempt == maxRetry - 1:
        ApiToolLog().LogError(e, postIssue=False)
        if raiseError:
            raise e
    if "429" not in str(e) and "Too Many Requests" not in str(e):
        time.sleep(Globals.RETRY_SLEEP)
    else:
        doExponentialBackoff(attempt)
    postEventToFrame(EventUtility.myEVT_LOG, str(e))


def doExponentialBackoff(attempt):
    # If we run into a Rate Limit error, do an exponential backoff
    if attempt == 0:
        postEventToFrame(
            EventUtility.myEVT_LOG,
            "Rate Limit Encountered retrying in 1 minute",
        )
    else:
        postEventToFrame(
            EventUtility.myEVT_LOG,
            "Rate Limit Encountered retrying in %s minutes" % (attempt + 1),
        )
    time.sleep(
        Globals.RETRY_SLEEP * 20 * (attempt + 1)
    )  # Sleep for a minute * retry number


def performGetRequestWithRetry(
    url, headers=None, json=None, data=None, maxRetry=Globals.MAX_RETRY
):
    return performRequestWithRetry(
        url, requests.get, headers, json, data, maxRetry=maxRetry
    )


def performPatchRequestWithRetry(
    url, headers=None, json=None, data=None, maxRetry=Globals.MAX_RETRY
):
    return performRequestWithRetry(
        url, requests.patch, headers, json, data, maxRetry=maxRetry
    )


def performPutRequestWithRetry(
    url, headers=None, json=None, data=None, maxRetry=Globals.MAX_RETRY
):
    return performRequestWithRetry(
        url, requests.put, headers, json, data, maxRetry=maxRetry
    )


def performDeleteRequestWithRetry(
    url, headers=None, json=None, data=None, maxRetry=Globals.MAX_RETRY
):
    return performRequestWithRetry(
        url, requests.delete, headers, json, data, maxRetry=maxRetry
    )


def performPostRequestWithRetry(
    url,
    headers=None,
    json=None,
    data=None,
    files=None,
    maxRetry=Globals.MAX_RETRY,
):
    return performRequestWithRetry(
        url, requests.post, headers, json, data, files, maxRetry=maxRetry
    )


def getAllFromOffsetsRequests(
    api_response, results=None, tolarance=0, timeout=-1, useThreadPool=True
):
    count = None
    resultList = []
    if not results:
        results = []
    if hasattr(api_response, "content"):
        api_response = api_response.content
    elif type(api_response) is dict and "content" in api_response:
        api_response = api_response["content"]
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
            if useThreadPool:
                Globals.THREAD_POOL.enqueue(
                    perform_web_requests, (url, getHeader(), "GET", None)
                )
            else:
                resp_json = perform_web_requests(
                    (url, getHeader(), "GET", None)
                )
                resultList.append(resp_json)
            respOffsetInt += int(respLimit)

    if useThreadPool:
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
