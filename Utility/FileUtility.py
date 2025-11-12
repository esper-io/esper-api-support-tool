import csv
import json
import os
import platform
import tempfile
import threading
from itertools import islice

import openpyxl
import pandas as pd

import Common.Globals as Globals


def checkIfCurrentThreadStopped():
    """Check if the current thread has been asked to stop/abort.
    This function is defined here to avoid circular dependency with Utility.Resource"""
    isAbortSet = False
    if hasattr(threading.current_thread(), "abort"):
        isAbortSet = threading.current_thread().abort.is_set()
    elif hasattr(threading.current_thread(), "isStopped"):
        isAbortSet = threading.current_thread().isStopped()
    elif hasattr(threading.current_thread(), "stopCurrentTask"):
        isAbortSet = threading.current_thread().stopCurrentTask.is_set()
    return isAbortSet


def read_from_file(filePath, mode="r") -> list:
    content = None
    with open(filePath, mode) as file:
        content = file.read()
    return content


def read_json_file(filePath) -> dict:
    content = {}
    try:
        with open(filePath, "r") as file:
            content = json.load(file)
            if content is None:
                content = {}
    except (FileNotFoundError, json.JSONDecodeError, Exception):
        content = {}
    return content


def write_json_file(filePath, data: dict):
    with open(filePath, "w") as outfile:
        if data:
            json.dump(data, outfile)


def write_content_to_file(filePath, data, mode="w", encoding="utf-8") -> None:
    if "b" in mode:
        encoding = None
    with open(filePath, mode, encoding=encoding) as file:
        if type(data) is list:
            for line in data:
                file.write(line)
        elif data:
            file.write(data)


def read_data_from_csv_as_dict(filePath: str) -> list:
    fileData = None
    if filePath.endswith("csv"):
        with open(filePath, "r") as csvFile:
            csv_reader = csv.DictReader(csvFile)
            fileData = list(csv_reader)
    return fileData


def write_data_to_csv(filePath: str, data, mode="w", encoding="utf-8", newline="") -> None:
    try:
        with open(filePath, mode, newline=newline, encoding=encoding) as csvfile:
            writer = csv.writer(csvfile, quoting=csv.QUOTE_NONNUMERIC)
            if type(data) is dict:
                writer.writerow(list(data.values()))
            elif any(isinstance(el, list) for el in data):
                writer.writerows(data)
            elif type(data) is list:
                writer.writerow(data)
            else:
                if data:
                    writer.writerows(data)
    except Exception as e:
        print(e)
        raise e


def getToolDataPath():
    basePath = "%s/EsperApiTool/" % tempfile.gettempdir().replace("Local", "Roaming").replace("Temp", "")

    if platform.system() != "Windows":
        basePath = "%s/EsperApiTool/" % os.path.expanduser("~/Desktop/")

    return basePath


def read_excel_via_openpyxl(path: str, readAnySheet=False) -> pd.DataFrame:
    workbook = openpyxl.load_workbook(path, read_only=True, data_only=True)
    df = None
    rows = []
    headers = None
    for sheet in workbook.sheetnames:
        if "Device & Network" in sheet or "Device and Network" in sheet or "Device" in sheet or readAnySheet:
            # Select the worksheet
            worksheet = workbook[sheet]
            # Extract the data
            for row in worksheet.iter_rows(values_only=True):
                if not headers:
                    headers = row
                # Try to avoid shape mismatch
                if len(row) == len(headers):
                    rows.append(row)
    df = pd.DataFrame(rows[1:], columns=rows[0])
    return df


def read_csv_via_pandas(path: str) -> pd.DataFrame:
    data = None
    try:
        data = pd.read_csv(path, sep=",", header=0, keep_default_na=False, chunksize=1000)
    except:
        try:
            # Try to decode ANSI encoded CSV files
            data = pd.read_csv(
                path,
                sep=",",
                header=0,
                keep_default_na=False,
                chunksize=1000,
                encoding="mbcs",
            )
        except Exception as e:
            print(e)
            raise e
    return pd.concat(data, ignore_index=True)


def save_excel_pandas_xlxswriter(path, df_dict: dict):
    # Check abort before starting
    if checkIfCurrentThreadStopped():
        return
    
    if len(df_dict) <= Globals.MAX_NUMBER_OF_SHEETS_PER_FILE:
        writer = pd.ExcelWriter(
            path,
            engine="xlsxwriter",
        )

        sheetNames = []
        try:
            for sheet, df in df_dict.items():
                # Check abort before processing each sheet
                if checkIfCurrentThreadStopped():
                    # Close writer if abort is detected
                    if hasattr(writer, "close"):
                        writer.close()
                    return
                
                sheetNames.append(sheet)
                df.to_excel(writer, sheet_name=sheet, index=False)

            # Auto adjust column width
            for s in sheetNames:
                # Check abort before adjusting each sheet's column width
                if checkIfCurrentThreadStopped():
                    break
                    
                worksheet = writer.sheets[s]
                if hasattr(worksheet, "autofit"):
                    worksheet.autofit()
                else:
                    for idx, col in enumerate(df):  # loop through all columns
                        # Check abort during column width adjustment
                        if checkIfCurrentThreadStopped():
                            break
                        series = df[col]
                        max_len = (
                            max(
                                (
                                    series.astype(str).map(len).max(),  # len of largest item
                                    len(str(series.name)),  # len of column name/header
                                )
                            )
                            + 1
                        )  # adding a little extra space
                        worksheet.set_column(idx, idx, max_len)  # set column width
        except Exception as e:
            pass
        finally:
            if hasattr(writer, "save"):
                writer.save()
            if hasattr(writer, "close"):
                writer.close()
    else:
        split_dict_list = list(__split_dict_into_chunks__(df_dict, Globals.MAX_NUMBER_OF_SHEETS_PER_FILE))
        for i in range(0, len(split_dict_list)):
            # Check abort before processing each split file
            if checkIfCurrentThreadStopped():
                return
                
            if i == 0:
                path = path[:-5] + "_{}.xlsx".format(i)
            else:
                path = path[:-7] + "_{}.xlsx".format(i)
            save_excel_pandas_xlxswriter(path, split_dict_list[i])


def __split_dict_into_chunks__(data, size):
    it = iter(data)
    for _ in range(0, len(data), size):
        yield {k: data[k] for k in islice(it, size)}


def save_csv_pandas(path, df):
    # Check abort before starting the save operation
    # Note: pandas to_csv is a blocking operation that can't be interrupted mid-write,
    # but checking here allows the thread to exit before starting a long write operation
    if checkIfCurrentThreadStopped():
        return
    
    df.to_csv(
        path,
        sep=",",
        index=False,
        encoding="utf-8",
        quoting=csv.QUOTE_NONNUMERIC,
    )
