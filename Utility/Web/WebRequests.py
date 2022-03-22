import requests
import time
import Common.Globals as Globals
from Utility.Logging.ApiToolLogging import ApiToolLog


def performGetRequestWithRetry(
    url, headers=None, json=None, data=None, maxRetry=Globals.MAX_RETRY
):
    resp = None
    for attempt in range(maxRetry):
        try:
            resp = requests.get(url, headers=headers, json=json, data=data)
            ApiToolLog().LogApiRequestOccurrence(
                performGetRequestWithRetry.__name__, url, Globals.PRINT_API_LOGS
            )
            if resp.status_code < 300:
                break
        except Exception as e:
            if attempt == maxRetry - 1:
                ApiToolLog().LogError(e)
            time.sleep(Globals.RETRY_SLEEP)
    return resp


def performPatchRequestWithRetry(
    url, headers=None, json=None, data=None, maxRetry=Globals.MAX_RETRY
):
    resp = None
    for attempt in range(maxRetry):
        try:
            resp = requests.patch(url, headers=headers, data=data, json=json)
            ApiToolLog().LogApiRequestOccurrence(
                performPatchRequestWithRetry.__name__, url, Globals.PRINT_API_LOGS
            )
            if resp.status_code < 300:
                break
        except Exception as e:
            if attempt == maxRetry - 1:
                ApiToolLog().LogError(e)
            time.sleep(Globals.RETRY_SLEEP)
    return resp


def performPutRequestWithRetry(
    url, headers=None, json=None, data=None, maxRetry=Globals.MAX_RETRY
):
    resp = None
    for attempt in range(maxRetry):
        try:
            resp = requests.put(url, headers=headers, data=data, json=json)
            ApiToolLog().LogApiRequestOccurrence(
                performPutRequestWithRetry.__name__, url, Globals.PRINT_API_LOGS
            )
            if resp.status_code < 300:
                break
        except Exception as e:
            if attempt == maxRetry - 1:
                ApiToolLog().LogError(e)
            time.sleep(Globals.RETRY_SLEEP)
    return resp


def performDeleteRequestWithRetry(
    url, headers=None, json=None, data=None, maxRetry=Globals.MAX_RETRY
):
    resp = None
    for attempt in range(maxRetry):
        try:
            resp = requests.delete(url, headers=headers, data=data, json=json)
            ApiToolLog().LogApiRequestOccurrence(
                performDeleteRequestWithRetry.__name__, url, Globals.PRINT_API_LOGS
            )
            if resp.status_code < 300:
                break
        except Exception as e:
            if attempt == maxRetry - 1:
                ApiToolLog().LogError(e)
            time.sleep(Globals.RETRY_SLEEP)
    return resp


def performPostRequestWithRetry(
    url, headers=None, json=None, data=None, files=None, maxRetry=Globals.MAX_RETRY
):
    resp = None
    for attempt in range(maxRetry):
        try:
            resp = requests.post(
                url, headers=headers, data=data, json=json, files=files
            )
            ApiToolLog().LogApiRequestOccurrence(
                performPostRequestWithRetry.__name__, url, Globals.PRINT_API_LOGS
            )
            if resp.status_code < 300:
                break
        except Exception as e:
            if attempt == maxRetry - 1:
                ApiToolLog().LogError(e)
            time.sleep(Globals.RETRY_SLEEP)
    return resp
