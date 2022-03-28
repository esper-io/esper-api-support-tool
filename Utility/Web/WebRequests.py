import requests
import time
import Common.Globals as Globals
from Utility import EventUtility

from Utility.Logging.ApiToolLogging import ApiToolLog
from Utility.Resource import postEventToFrame


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
            if resp.status_code < 300 or (resp.status_code == 500 and attempt >= 2):
                break
            if resp.status_code == 429:
                if attempt == 0:
                    postEventToFrame(EventUtility.myEVT_LOG, "Rate Limit Encountered retrying in 1 minute")
                else:
                    postEventToFrame(EventUtility.myEVT_LOG, "Rate Limit Encountered retrying in %s minutes" % attempt + 1)
                time.sleep(
                    Globals.RETRY_SLEEP * 20 * attempt
                )  # Sleep for a minute * retry number
        except Exception as e:
            if attempt == maxRetry - 1:
                ApiToolLog().LogError(e)
            if "429" not in str(e) and "Too Many Requests" not in str(e):
                time.sleep(Globals.RETRY_SLEEP)
            else:
                time.sleep(
                    Globals.RETRY_SLEEP * 20 * attempt
                )  # Sleep for a minute * retry number
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
            if resp.status_code < 300 or (resp.status_code == 500 and attempt >= 2):
                break
            if resp.status_code == 429:
                if attempt == 0:
                    postEventToFrame(EventUtility.myEVT_LOG, "Rate Limit Encountered retrying in 1 minute")
                else:
                    postEventToFrame(EventUtility.myEVT_LOG, "Rate Limit Encountered retrying in %s minutes" % attempt + 1)
                time.sleep(
                    Globals.RETRY_SLEEP * 20 * attempt
                )  # Sleep for a minute * retry number
        except Exception as e:
            if attempt == maxRetry - 1:
                ApiToolLog().LogError(e)
            if "429" not in str(e) and "Too Many Requests" not in str(e):
                time.sleep(Globals.RETRY_SLEEP)
            else:
                time.sleep(
                    Globals.RETRY_SLEEP * 20 * attempt
                )  # Sleep for a minute * retry number
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
            if resp.status_code < 300 or (resp.status_code == 500 and attempt >= 2):
                break
            if resp.status_code == 429:
                if attempt == 0:
                    postEventToFrame(EventUtility.myEVT_LOG, "Rate Limit Encountered retrying in 1 minute")
                else:
                    postEventToFrame(EventUtility.myEVT_LOG, "Rate Limit Encountered retrying in %s minutes" % attempt + 1)
                time.sleep(
                    Globals.RETRY_SLEEP * 20 * attempt
                )  # Sleep for a minute * retry number
            if resp.status_code == 500 and attempt >= 2:
                break
        except Exception as e:
            if attempt == maxRetry - 1:
                ApiToolLog().LogError(e)
            if "429" not in str(e) and "Too Many Requests" not in str(e):
                time.sleep(Globals.RETRY_SLEEP)
            else:
                time.sleep(
                    Globals.RETRY_SLEEP * 20 * attempt
                )  # Sleep for a minute * retry number
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
            if resp.status_code < 300 or (resp.status_code == 500 and attempt >= 2):
                break
            if resp.status_code == 429:
                if attempt == 0:
                    postEventToFrame(EventUtility.myEVT_LOG, "Rate Limit Encountered retrying in 1 minute")
                else:
                    postEventToFrame(EventUtility.myEVT_LOG, "Rate Limit Encountered retrying in %s minutes" % attempt + 1)
                time.sleep(
                    Globals.RETRY_SLEEP * 20 * attempt
                )  # Sleep for a minute * retry number
            if resp.status_code == 500 and attempt >= 2:
                break
        except Exception as e:
            if attempt == maxRetry - 1:
                ApiToolLog().LogError(e)
            if "429" not in str(e) and "Too Many Requests" not in str(e):
                time.sleep(Globals.RETRY_SLEEP)
            else:
                time.sleep(
                    Globals.RETRY_SLEEP * 20 * attempt
                )  # Sleep for a minute * retry number
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
            if resp.status_code < 300 or (resp.status_code == 500 and attempt >= 2):
                break
            if resp.status_code == 429:
                if attempt == 0:
                    postEventToFrame(EventUtility.myEVT_LOG, "Rate Limit Encountered retrying in 1 minute")
                else:
                    postEventToFrame(EventUtility.myEVT_LOG, "Rate Limit Encountered retrying in %s minutes" % attempt + 1)
                time.sleep(
                    Globals.RETRY_SLEEP * 20 * attempt
                )  # Sleep for a minute * retry number
        except Exception as e:
            if attempt == maxRetry - 1:
                ApiToolLog().LogError(e)
            if "429" not in str(e) and "Too Many Requests" not in str(e):
                time.sleep(Globals.RETRY_SLEEP)
            else:
                time.sleep(
                    Globals.RETRY_SLEEP * 20 * attempt
                )  # Sleep for a minute * retry number
    return resp
