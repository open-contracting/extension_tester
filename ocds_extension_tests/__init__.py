#!/usr/bin/env python
from __future__ import print_function
import unittest
import os
import json
import requests
import json_merge_patch
import copy
from jsonschema.validators import Draft4Validator as validator
from jsonschema import FormatChecker

TEST_CORE = os.environ.get('TEST_CORE')

current_dir = os.path.dirname(os.path.realpath(__file__))
all_json_path = {}
all_json_data = {}
all_schema_data = {}

metaschema = requests.get('http://json-schema.org/schema').json()

with open(os.path.join(current_dir, 'fixtures', "fullfakedata.json")) as fakedata_file:
    fakedata = json.load(fakedata_file)


def gather_data():

    schema_dir = os.getcwd()

    schema_list_page = requests.get('http://standard.open-contracting.org/schema').text

    parts = schema_list_page.split('href="')
    all_versions = []
    for part in parts:
        start = part[:part.find('"')].strip("/")
        version_parts = tuple(start.split("__"))
        if len(version_parts) != 3 or version_parts[-1] == "RC":
            continue
        all_versions.append(version_parts)
    all_versions.sort()
    latest_version = "__".join(all_versions[-1])

    all_json = ["release-package-schema.json", "release-schema.json",
                "record-package-schema.json", "versioned-release-validation-schema.json",
                "extension.json"]

    for file_name in all_json:
        if file_name == "extension.json":
            continue
        all_schema_data[file_name] = requests.get(
            'http://standard.open-contracting.org/schema/' + latest_version + '/' + file_name).json()

    for file_name in all_json:
        file_path = os.path.join(schema_dir, file_name)
        try:
            with open(file_path) as json_file:
                all_json_path[file_name] = file_path
                try:
                    all_json_data[file_name] = json.load(json_file)
                except ValueError:
                    pass  # failure will be raised in test_valid_json
        except IOError:
            if file_name == "extension.json" and not TEST_CORE:
                raise Exception("extension.json not found. This directroy is not an extension or the extension.json "
                                "file is missing")


gather_data()


class TestExtensions(unittest.TestCase):

    def test_valid_json(self):
        for file_name, file_path in all_json_path.items():
            with open(file_path) as json_file:
                try:
                    json.load(json_file)
                except ValueError:
                    raise Exception("File {} can does not appear to be valid JSON".format(file_name))

    def test_patches_apply(self):
        for key, schema in all_schema_data.items():
            if key in all_json_data:
                new_schema = copy.deepcopy(schema)
                new_schema = json_merge_patch.merge(new_schema, all_json_data[key])
                assert new_schema != schema, "{} hasn't been patched".format(key)

    def test_metaschema(self):
        for key, schema in all_schema_data.items():
            if key in all_json_data:
                new_schema = copy.deepcopy(schema)
                new_schema = json_merge_patch.merge(new_schema, all_json_data[key])
                if not validator(metaschema, format_checker=FormatChecker()).is_valid(new_schema):
                    raise Exception("File {}, once patched, does not appear valid json schema".format(key))

    def test_fakedata(self):
        errors = 0

        for error in validator(all_schema_data["release-package-schema.json"],
                               format_checker=FormatChecker()).iter_errors(fakedata):
            errors += 1
            print(json.dumps(error.instance, indent=2, separators=(',', ': ')))
            print('{} ({})\n'.format(error.message, '/'.join(error.absolute_schema_path)))

        assert errors == 0

def run_tests():
    unittest.main()


if __name__ == '__main__':
    run_tests()
