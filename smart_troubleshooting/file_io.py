"""
This module offers an API to load and dump files as json or csv
"""

import json
import csv
from jsonschema import validate, ValidationError, SchemaError


def load_json(file):
    """
    load a json file and return it as a dictionary.
    :param file: the name of the file
    :return: the dictionary of the file contents
    """
    with open(file, "r") as json_file:
        return json.load(json_file)


def dump_json(data, file):
    """
    Save a dictionary in a json file.
    :param data: the data to be saved in json
    :param file: the name of the file
    :return: None
    """
    with open(file, "w") as json_file:
        json.dump(data, json_file, indent=4)


def validate_json(instance, schema):
    """
    Validate a json to a specific schema.
    :param instance: the instance to be validated
    :param schema: the schema to be used
    :return: True if the instance respects the schema
    """
    try:
        validate(instance, schema)
    except ValidationError as val_err:
        print(val_err)
        return False
    except SchemaError as sch_err:
        print(sch_err)
        return False
    return True


def dump_csv(head_row, data_rows, file, columns=None):
    """
    Dump some rows in a file in csv format.
    :param head_row: A list of words to be used as intestation line in the file
    :param data_rows: The list of dictionaries to be dumped
    :param file: the name of the file
    :param columns: the list of strings to be used as keys for elements in data_rows.
    If missing, it will be set equal to head_row
    :return: None
    """

    if columns is None:
        columns = head_row

    with open(file, 'w', newline='') as csv_file:
        problem_writer = csv.writer(csv_file, quoting=csv.QUOTE_MINIMAL)
        problem_writer.writerow(head_row)
        for row in data_rows:
            csv_row = [row[column] for column in columns]
            problem_writer.writerow(csv_row)
