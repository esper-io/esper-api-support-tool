#!/usr/bin/env python

import threading
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
    sleepMin=0,
    sleepMax=0,
):
    resp = None
    for attempt in range(maxRetry):
        try:
            enforceRateLimit(sleepMin, sleepMax)
            if files:
                resp = method(url, headers=headers, json=json, data=data, files=files, timeout=requestTimeout)
            else:
                resp = method(url, headers=headers, json=json, data=data, timeout=requestTimeout)
            if Globals.IS_DEBUG:
                timeElapsed = resp.elapsed.total_seconds() if resp is not None and hasattr(resp, 'elapsed') else 'N/A'
                respCode = resp.status_code if resp is not None and hasattr(resp, 'status_code') else 'N/A'
                ApiToolLog().Log("%s\tThread:%s\tMethod: %s\tRequest Url: %s\tResponse Code: %s\tResponse Time: %s" % (
                    time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), threading.current_thread().name, method.__name__, url, respCode, timeElapsed
                ))
            ApiToolLog().LogApiRequestOccurrence(method.__name__, url, Globals.PRINT_API_LOGS)

            code = resp.status_code if resp is not None and hasattr(resp, 'status_code') else -1
            if (code > 0 and code < 300):
                break
            else:
                _handle_non_success_response(resp, attempt, maxRetry, url)
        except Exception as e:
            handleRequestError(attempt, e, maxRetry, url)
    return resp


def _handle_non_success_response(resp, attempt, maxRetry, url):
    """Handle non-2XX HTTP status codes with appropriate retry logic."""
    code = resp.status_code
    response_text = getattr(resp, 'text', '')
    
    err_msg = "ERROR: %s Request Failed (Attempt %s of %s) %s %s" % (
        url, attempt + 1, maxRetry, code, response_text
    )
    ApiToolLog().LogError(err_msg, postStatus=False)
    
    # Rate limiting (429) - use exponential backoff
    if code == 429:
        doExponentialBackoff(attempt, url)
    # Timeout-related responses - use exponential backoff without rate limit logging
    elif _is_timeout_related_response(response_text):
        doExponentialBackoff(attempt, url, False)

    if code == 429 or attempt == maxRetry - 1:
        postEventToFrame(EventUtility.myEVT_LOG, err_msg)


def _is_timeout_related_response(response_text):
    """Check if the response indicates a timeout or rate limiting issue."""
    timeout_indicators = ["timeout", "timing out", "too many requests"]
    return any(indicator in response_text.lower() for indicator in timeout_indicators)


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
    sleepTime = (Globals.RETRY_SLEEP * 20) * (2 ** (attempt))
    errorType = "Rate Limit" if isRateLimit else "Error"
    if isRateLimit:
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


def performGetRequestWithRetry(url, headers=None, json=None, data=None, maxRetry=Globals.MAX_RETRY, sleepMin=0, sleepMax=0):
    return performRequestWithRetry(url, requests.get, headers, json, data, maxRetry=maxRetry, sleepMin=sleepMin, sleepMax=sleepMax)


def performPatchRequestWithRetry(url, headers=None, json=None, data=None, maxRetry=Globals.MAX_RETRY, sleepMin=0, sleepMax=0):
    return performRequestWithRetry(url, requests.patch, headers, json, data, maxRetry=maxRetry, sleepMin=sleepMin, sleepMax=sleepMax)


def performPutRequestWithRetry(url, headers=None, json=None, data=None, maxRetry=Globals.MAX_RETRY, sleepMin=0, sleepMax=0):
    return performRequestWithRetry(url, requests.put, headers, json, data, maxRetry=maxRetry, sleepMin=sleepMin, sleepMax=sleepMax)

def performDeleteRequestWithRetry(url, headers=None, json=None, data=None, maxRetry=Globals.MAX_RETRY, sleepMin=0, sleepMax=0):
    return performRequestWithRetry(url, requests.delete, headers, json, data, maxRetry=maxRetry, sleepMin=sleepMin, sleepMax=sleepMax)

def performPostRequestWithRetry(
    url,
    headers=None,
    json=None,
    data=None,
    files=None,
    maxRetry=Globals.MAX_RETRY,
    sleepMin=0,
    sleepMax=0,
):
    return performRequestWithRetry(url, requests.post, headers, json, data, files, maxRetry=maxRetry, sleepMin=sleepMin, sleepMax=sleepMax)


def getAllFromOffsetsRequests(api_response, results=None, tolarance=0, timeout=-1, useThreadPool=True):
    count = None
    if results is None:
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
        if "v2/devices/" in apiNext:
            minSleep = 25
            maxSleep = 45
        else:
            minSleep = 0
            maxSleep = 0
        
        if useThreadPool:
            # Queue all requests first
            total_requests = 0
            while int(respOffsetInt) < count and int(respLimit) < count:
                if checkIfCurrentThreadStopped():
                    return
                url = apiNext.replace("offset=%s" % respOffset, "offset=%s" % str(respOffsetInt))
                url = validateUrl(url)
                Globals.THREAD_POOL.enqueue(perform_web_requests, (url, getHeader(), "GET", None, Globals.MAX_RETRY, minSleep, maxSleep))
                respOffsetInt += int(respLimit)
                total_requests += 1
            
            # Process results as they become available with fail-fast
            _process_threaded_responses_with_fail_fast(total_requests, results, tolarance, timeout)
        else:
            # Sequential processing with immediate fail-fast
            while int(respOffsetInt) < count and int(respLimit) < count:
                if checkIfCurrentThreadStopped():
                    return
                url = apiNext.replace("offset=%s" % respOffset, "offset=%s" % str(respOffsetInt))
                url = validateUrl(url)
                resp_json = perform_web_requests((url, getHeader(), "GET", None, Globals.MAX_RETRY, minSleep, maxSleep))
                
                # Fail fast on invalid response
                _validate_and_process_single_response(resp_json, results)
                respOffsetInt += int(respLimit)
    
    return results

def validateUrl(url):
    # check to ensure URL is https not http
    if url.startswith("http://"):
        url = url.replace("http://", "https://", 1)
    if ".esper.cloud" in url:
        # check to see if URL has the correct API endpoint
        host = Globals.configuration.host.replace("https://", "").replace("http://", "")
        if host not in url:
            properHost = host.split(".esper.cloud")[0]
            invalidHost = url.split("//")[1].split(".esper.cloud")[0]
            url = url.replace(invalidHost, properHost)
    return url


def _process_threaded_responses_with_fail_fast(total_requests, results, tolerance=0, timeout=-1):
    """Process threaded responses as they become available with true fail-fast behavior."""
    import time
    processed_count = 0
    start_time = time.time()
    
    while processed_count < total_requests:
        if checkIfCurrentThreadStopped():
            return
            
        # Check for timeout
        if timeout > 0 and (time.time() - start_time) > timeout:
            raise Exception("Timeout waiting for threaded responses")
        
        # Get available results without waiting
        available_results = Globals.THREAD_POOL.results(wait=0)
        
        if available_results:
            # Process each available result immediately
            for resp in available_results:
                _validate_and_process_single_response(resp, results)
                processed_count += 1
        else:
            # No results available yet, wait a short time before checking again
            time.sleep(0.1)
    
    # Final join to ensure thread pool is clean
    Globals.THREAD_POOL.join(tolerance)


def _validate_and_process_single_response(resp, results):
    """Validate a single response and add its results to the results list, failing fast on invalid responses."""
    if "content" in resp:
        resp = resp["content"]

    if resp and hasattr(resp, "results") and resp.results:
        results += resp.results
    elif type(resp) is dict and "results" in resp and resp["results"]:
        results += resp["results"]
    else:
        raise Exception("Failed to get valid response: %s" % str(resp))


def perform_web_requests(content):
    url = content[0].strip()
    header = content[1]
    method = content[2]
    json = content[3] if len(content) > 3 else None
    retry = content[4] if len(content) > 4 and content[4] is not None else Globals.MAX_RETRY
    min = content[5] if len(content) > 5 and content[5] is not None else 0
    max = content[6] if len(content) > 6 and content[6] is not None else 0
    resp = None

    if method == "GET":
        resp = performGetRequestWithRetry(url, header, json, maxRetry=retry, sleepMin=min, sleepMax=max)
    elif method == "POST":
        resp = performPostRequestWithRetry(url, header, json, maxRetry=retry, sleepMin=min, sleepMax=max)
    elif method == "DELETE":
        resp = performDeleteRequestWithRetry(url, header, json, maxRetry=retry, sleepMin=min, sleepMax=max)
    elif method == "PATCH":
        resp = performPatchRequestWithRetry(url, header, json, maxRetry=retry, sleepMin=min, sleepMax=max)
    elif method == "PUT":
        resp = performPutRequestWithRetry(url, header, json, maxRetry=retry, sleepMin=min, sleepMax=max)

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
