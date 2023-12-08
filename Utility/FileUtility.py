import csv
import json
import tempfile
import platform
import os
import pandas as pd
import openpyxl
import Common.Globals as Globals
from Utility.Logging import ApiToolLogging


def read_from_file(filePath, mode="r") -> list:
    content = None
    with open(filePath, mode) as file:
        content = file.read()
    return content


def read_lines_from_file(filePath, mode="r") -> list:
    content = None
    with open(filePath, mode) as file:
        content = file.readlines()
    return content


def read_json_file(filePath) -> dict:
    content = None
    with open(filePath, "r") as file:
        content = json.load(file)
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


def read_data_from_csv(filePath: str) -> list:
    fileData = None
    if filePath.endswith("csv"):
        try:
            fileData = __read_data_from_csv_helper__(filePath, "utf-8-sig")
        except:
            fileData = __read_data_from_csv_helper__(filePath, "utf-8")
    return fileData


def read_data_from_csv_as_dict(filePath: str) -> list:
    fileData = None
    if filePath.endswith("csv"):
        with open(filePath, "r") as csvFile:
            csv_reader = csv.DictReader(csvFile)
            fileData = list(csv_reader)
    return fileData


def __read_data_from_csv_helper__(
    filePath, encoding, quoting=csv.QUOTE_MINIMAL, skipinitialspace=True
):
    fileData = None
    with open(filePath, "r", encoding=encoding) as csvFile:
        reader = csv.reader(csvFile, quoting=quoting, skipinitialspace=skipinitialspace)
        fileData = list(reader)
    return fileData


def write_data_to_csv(
    filePath: str, data, mode="w", encoding="utf-8", newline=""
) -> None:
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


def getToolDataPath():
    basePath = "%s/EsperApiTool/" % tempfile.gettempdir().replace(
        "Local", "Roaming"
    ).replace("Temp", "")

    if platform.system() != "Windows":
        basePath = "%s/EsperApiTool/" % os.path.expanduser("~/Desktop/")

    return basePath


def read_excel_via_openpyxl(path: str, readAnySheet=False) -> pd.DataFrame:
    workbook = openpyxl.load_workbook(path, read_only=True, data_only=True)
    df = None
    rows = []
    for sheet in workbook.sheetnames:
        if (
            "Device & Network" in sheet
            or "Device and Network" in sheet
            or "Device" in sheet
            or readAnySheet
        ):
            # Select the worksheet
            worksheet = workbook[sheet]
            # Extract the data
            for row in worksheet.iter_rows(values_only=True):
                rows.append(row)
    df = pd.DataFrame(rows[1:], columns=rows[0])
    return df


def read_csv_via_pandas(path: str) -> pd.DataFrame:
    return pd.read_csv(path, sep=",", header=0, keep_default_na=False)


def save_excel_pandas_xlxswriter(path, df_dict: dict):
    if len(df_dict) < Globals.MAX_NUMBER_OF_SHEETS_PER_FILE:
        writer = pd.ExcelWriter(
            path,
            engine="xlsxwriter",
        )
        for sheet, df in df_dict.items():
            try:
                sheetNames = []
                if len(df) > Globals.SHEET_CHUNK_SIZE:
                    for i in range(0, len(df), Globals.SHEET_CHUNK_SIZE):
                        sheetName = "{} Part {}".format(sheet, i)
                        df[i : i + Globals.SHEET_CHUNK_SIZE].to_excel(
                            writer,
                            sheet_name=sheetName,
                            index=False,
                        )
                        sheetNames.append(sheetName)
                else:
                    sheetNames.append(sheet)
                    df.to_excel(writer, sheet_name=sheet, index=False)
                for s in sheetNames:
                    worksheet = writer.sheets[s]
                    for idx, col in enumerate(df):  # loop through all columns
                        series = df[col]
                        max_len = (
                            max(
                                (
                                    series.astype(str)
                                    .map(len)
                                    .max(),  # len of largest item
                                    len(str(series.name)),  # len of column name/header
                                )
                            )
                            + 1
                        )  # adding a little extra space
                        worksheet.set_column(idx, idx, max_len)  # set column width
            except Exception as e:
                ApiToolLogging().LogError(e)
            writer.save()
    else:
        for i in range(0, len(df_dict), Globals.MAX_NUMBER_OF_SHEETS_PER_FILE):
            path = path.replace(".xlsx", "_{}.xlsx".format(i))
            save_excel_pandas_xlxswriter(path, df_dict[i : i + Globals.MAX_NUMBER_OF_SHEETS_PER_FILE])


def save_csv_pandas(path, df):
    df.to_csv(
        path, sep=",", index=False, encoding="utf-8", quoting=csv.QUOTE_NONNUMERIC
    )
