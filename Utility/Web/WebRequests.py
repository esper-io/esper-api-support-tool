#!/usr/bin/env python

import time

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

import Common.Globals as Globals
from Utility import EventUtility
from Utility.Logging.ApiToolLogging import ApiToolLog
from Utility.Resource import (checkIfCurrentThreadStopped, enforceRateLimit,
                              getHeader, postEventToFrame)

session = requests.Session()

retries = Retry(
    total=Globals.MAX_RETRY,
    backoff_factor=3,       # 3, 6, 12, 24, 48...seconds
    status_forcelist=[500, 502, 503, 504],
    allowed_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
)

adapter = HTTPAdapter(max_retries=retries)
session.mount("https://", adapter)


def performRequestWithRetry(
    url,
    method,
    headers=None,
    json=None,
    data=None,
    files=None,
    requestTimeout=(30, 60), # connect, read
    maxRetry=Globals.MAX_RETRY,
):
    resp = None
    for attempt in range(maxRetry):
        try:
            enforceRateLimit()
            if files:
                resp = method(url, headers=headers, json=json, data=data, files=files, timeout=requestTimeout)
            else:
                resp = method(url, headers=headers, json=json, data=data, timeout=requestTimeout)
            ApiToolLog().LogApiRequestOccurrence(method.__name__, url, Globals.PRINT_API_LOGS)
            code = resp.status_code if resp is not None and hasattr(resp, 'status_code') else -1
            if (code > 0 and code < 300):
                break
            elif code == 429:
                err_msg = "ERROR: %s Request Failed (Attempt %s of %s) %s %s" % (
                    url, attempt + 1, maxRetry, code, resp.text
                )
                ApiToolLog().LogError(err_msg, postStatus=False)
                doExponentialBackoff(attempt, url)
            elif "timeout" in resp.text.lower() or "timing out" in resp.text.lower() or "too many requests" in resp.text.lower():
                err_msg = "ERROR: %s Request Failed (Attempt %s of %s) %s %s" % (
                    url, attempt + 1, maxRetry, code, resp.text
                )
                ApiToolLog().LogError(err_msg, postStatus=False)
                doExponentialBackoff(attempt, url, False)
            else:
                err_msg = "ERROR: %s Request Failed (Attempt %s of %s) %s %s" % (
                    url, attempt + 1, maxRetry, code, resp.text
                )
                ApiToolLog().LogError(err_msg, postStatus=False)
                postEventToFrame(EventUtility.myEVT_LOG, err_msg)
        except Exception as e:
            handleRequestError(attempt, e, maxRetry, url)
    return resp


def handleRequestError(attempt, e, maxRetry, raiseError=False, url=""):
    if attempt == maxRetry - 1:
        ApiToolLog().LogError(e, postStatus=False)
        if raiseError:
            raise e
    if "429" in str(e) or "Too Many Requests" in str(e):
        doExponentialBackoff(attempt, url)
    else:
        time.sleep(Globals.RETRY_SLEEP)
    postEventToFrame(EventUtility.myEVT_LOG, str(e))


def doExponentialBackoff(attempt, url, isRateLimit=True):
    # If we run into a Rate Limit error, do an exponential backoff
    sleepTime = Globals.RETRY_SLEEP * 20 * (attempt + 1)
    errorType = "Rate Limit" if isRateLimit else "Error"
    if attempt == 0:
        postEventToFrame(
            EventUtility.myEVT_LOG,
            "%s Encountered (%s) retrying in 1 minute" % (errorType, url),
        )
        
    else:
        postEventToFrame(
            EventUtility.myEVT_LOG,
            "%s Encountered (%s) retrying in %s minutes" % (errorType, url, attempt + 1),
        )
    if isRateLimit:
        ApiToolLog().LogError("Response returned 429, Rate Limit, waiting %s seconds" % sleepTime, postStatus=False)
    else:
        ApiToolLog().LogError("Error encountered, waiting %s seconds" % sleepTime, postStatus=False)
    time.sleep(sleepTime)  # Sleep for a minute * retry number


def performGetRequestWithRetry(url, headers=None, json=None, data=None, maxRetry=Globals.MAX_RETRY):
    return performRequestWithRetry(url, requests.get, headers, json, data, maxRetry=maxRetry)


def performPatchRequestWithRetry(url, headers=None, json=None, data=None, maxRetry=Globals.MAX_RETRY):
    return performRequestWithRetry(url, requests.patch, headers, json, data, maxRetry=maxRetry)


def performPutRequestWithRetry(url, headers=None, json=None, data=None, maxRetry=Globals.MAX_RETRY):
    return performRequestWithRetry(url, requests.put, headers, json, data, maxRetry=maxRetry)


def performDeleteRequestWithRetry(url, headers=None, json=None, data=None, maxRetry=Globals.MAX_RETRY):
    return performRequestWithRetry(url, requests.delete, headers, json, data, maxRetry=maxRetry)


def performPostRequestWithRetry(
    url,
    headers=None,
    json=None,
    data=None,
    files=None,
    maxRetry=Globals.MAX_RETRY,
):
    return performRequestWithRetry(url, requests.post, headers, json, data, files, maxRetry=maxRetry)


def getAllFromOffsetsRequests(api_response, results=None, tolarance=0, timeout=-1, useThreadPool=True):
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
            url = apiNext.replace("offset=%s" % respOffset, "offset=%s" % str(respOffsetInt))
            if useThreadPool:
                Globals.THREAD_POOL.enqueue(perform_web_requests, (url, getHeader(), "GET", None))
            else:
                resp_json = perform_web_requests((url, getHeader(), "GET", None))
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
        else:
            raise Exception("Failed to get valid response: %s" % str(resp))
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


def fetchRequestWithOffsets(url, tolerance=0, useThreadPool=True):
    resp = performGetRequestWithRetry(url, headers=getHeader())
    if resp:
        respJson = resp.json()
        if respJson and "content" in respJson:
            respJson = respJson["content"]
        offsetResponses = getAllFromOffsetsRequests(respJson, tolarance=tolerance, useThreadPool=useThreadPool)
        if type(offsetResponses) is dict and "results" in offsetResponses:
            respJson["results"] = respJson["results"] + offsetResponses["results"]
            respJson["next"] = None
            respJson["prev"] = None
        elif type(offsetResponses) is list:
            respJson["results"] = respJson["results"] + offsetResponses
        return respJson
    return resp
