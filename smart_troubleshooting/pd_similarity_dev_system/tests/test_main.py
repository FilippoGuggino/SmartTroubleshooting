"""
Testing for main module.

Author: Riccardo Mancini
"""

import json

from smart_troubleshooting.pd_similarity_dev_system.main \
    import _main

from smart_troubleshooting.pd_similarity_dev_system.tests.test_utils \
    import path_of, capture_stdout


class MockArgs:
    def __init__(self, action, config_file_path):
        self.action = [action]
        self.config_file = [open(config_file_path, 'r')]


def test_manual_train():
    args = MockArgs("manual_train",
                    path_of("dummy_manual_train_config.json"))
    output = capture_stdout(_main, args=[args])
    json_out = json.loads(output)
    json_in = json.load(open(path_of("dummy_manual_train_config.json")))

    for k, v in json_in["hyper_params"].items():
        assert json_out["hyper_params"].get(k) == v
    for k, v in json_in["training_params"].items():
        assert json_out["training_params"].get(k) == v


def test_auto_train():
    args = MockArgs("auto_train",
                    path_of("dummy_auto_train_config.json"))
    _main(args)


def test_test():
    args = MockArgs("test",
                    path_of("dummy_test_config.json"))
    _main(args)
