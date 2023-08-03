import csv
import json

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
        json.dump(data, outfile)

def write_content_to_file(filePath, data, mode="w", encoding="utf-8") -> None:
    with open(filePath, mode, encoding=encoding) as file:
        if type(data) is list:
            for line in data:
                file.write(line)
        else:
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

def __read_data_from_csv_helper__(filePath, encoding, quoting=csv.QUOTE_MINIMAL, skipinitialspace=True):
    fileData = None
    with open(filePath, "r", encoding=encoding) as csvFile:
        reader = csv.reader(
            csvFile, quoting=quoting, skipinitialspace=skipinitialspace
        )
        fileData = list(reader)
    return fileData

def write_data_to_csv(filePath: str, data: list, mode="w", encoding="utf-8", newline="") -> None:
    with open(filePath, mode, newline=newline, encoding=encoding) as csvfile:
        writer = csv.writer(csvfile, quoting=csv.QUOTE_NONNUMERIC)
        if type(data) is dict:
            writer.writerow(list(data.values()))
        else:
            writer.writerows(data)