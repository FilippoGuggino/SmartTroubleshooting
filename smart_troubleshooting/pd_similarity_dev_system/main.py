"""
This module provides the interface to the user.

Author: Riccardo Mancini
"""

import os

import argparse
import json
from jsonschema import RefResolver, Draft7Validator, ValidationError

from smart_troubleshooting.pd_similarity_dev_system.similarity_model \
    import SimilarityModel
from smart_troubleshooting.pd_similarity_dev_system.grid_search \
    import GridSearch
from smart_troubleshooting.pd_similarity_dev_system.data_loader \
    import DataLoader


"""Set this flag to show stack traces"""
DEBUG = False


def _load_json_validator(mode):
    """Load json schema for conf file of given operation mode """

    specific_schema_file = os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        f"json/schemas/{mode}_config_schema.json"
    )
    common_schema_file = os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        "json/schemas/common_schema.json"
    )

    with open(specific_schema_file, 'r') as f:
        specific_schema = json.load(f)

    with open(common_schema_file, 'r') as f:
        common_schema = json.load(f)

    schema_store = {
        specific_schema['$id']: specific_schema,
        common_schema['$id']: common_schema,
    }

    resolver = RefResolver.from_schema(common_schema, store=schema_store)
    validator = Draft7Validator(specific_schema, resolver=resolver)

    return validator


def manual_training(params, x_train, y_train, x_validate, y_validate):
    """Train model with given parameters and return validation score

    :param params: model parameters
    :type params: dict
    :param x_train: input data to be used for training the models
    :type x_train: ndarray of shape (n_train_samples, n_features)
    :param y_train: expected valued to be used for training the models
    :type y_train: ndarray of shape (n_train_samples,)
    :param x_validate: input data to be used for validating the models
    :type x_validate: ndarray of shape (n_validate_samples, n_features)
    :param y_validate: expected values to be used for validating the models
    :type y_validate: ndarray of shape (n_train_samples,)
    :returns: score and trained model
    :rtype: tuple(float, SimilarityModel)
    """

    model = SimilarityModel(**params)
    model.fit(x_train, y_train)
    return model.score(x_validate, y_validate), model


def automatic_training(param_ranges, x_train, y_train, x_validate,
                       y_validate):
    """Find best model within parameter ranges and return its validation score

    :param param_ranges: model parameter ranges
    :type param_ranges: dict
    :param x_train: input data to be used for training the models
    :type x_train: ndarray of shape (n_train_samples, n_features)
    :param y_train: expected valued to be used for training the models
    :type y_train: ndarray of shape (n_train_samples,)
    :param x_validate: input data to be used for validating the models
    :type x_validate: ndarray of shape (n_validate_samples, n_features)
    :param y_validate: expected values to be used for validating the models
    :type y_validate: ndarray of shape (n_train_samples,)
    :returns: score and trained model
    :rtype: tuple(float, SimilarityModel)
    """

    grid_search = GridSearch(n_jobs=os.cpu_count())
    return grid_search.search(x_train, y_train, x_validate, y_validate,
                              param_ranges)


def test(model, x_test, y_test):
    """Find best model within parameter ranges and return its validation score

    :param x_test: input data to be used for testing the models
    :type x_test: ndarray of shape (n_test_samples, n_features)
    :param y_test: expected values to be used for testing the models
    :type y_test: ndarray of shape (n_test_samples,)
    :returns: model tests score
    :rtype: float
    """

    return model.score(x_test, y_test)


def _extract_hyper_training_params(model):
    model_params = model.get_params()
    hyper_params = {k: v for k, v in model_params.items()
                    if k in SimilarityModel.HYPER_PARAMS}
    training_params = {k: v for k, v in model_params.items()
                       if k not in SimilarityModel.HYPER_PARAMS}
    return hyper_params, training_params


def _main(args):
    conf = json.load(args.config_file[0])
    validator = _load_json_validator(args.action[0])
    validator.validate(conf)

    data_loader = DataLoader(conf["pd_embeddings_path"])
    if "train" in args.action[0]:
        x_train, y_train = data_loader.load(conf["training_set_path"])
        x_valid, y_valid = data_loader.load(conf["validation_set_path"])
        model_path = conf['output_model_path']

        if args.action[0] == 'manual_train':
            score, model = manual_training(
                {**conf['hyper_params'], **conf['training_params']},
                x_train, y_train,
                x_valid, y_valid
            )

        elif args.action[0] == 'auto_train':
            score, model = automatic_training(
                {**conf['hyper_params'], **conf['training_params']},
                x_train, y_train,
                x_valid, y_valid
            )

        else:
            raise ValueError(f"Unrecognized training mode: {args.action[0]}")

        model.save(model_path)

    elif args.action[0] == 'test':
        x_test, y_test = data_loader.load(conf["test_set_path"])
        model_path = conf['model_path']
        model = SimilarityModel.load(model_path)

        score = test(model, x_test, y_test)

    else:
        raise ValueError(f"Unknown mode: {args.action[0]}")

    hyper_params, training_params = _extract_hyper_training_params(model)

    out = {
        'model_path': model_path,
        'hyper_params': hyper_params,
        'training_params': training_params,
        'score': score
    }

    print(json.dumps(out, sort_keys=True, indent=4))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="PD Similarity "
                                                 "Development System")
    parser.add_argument('action', nargs=1, type=str,
                        choices=['manual_train', 'auto_train', 'test'],
                        help="Action to perform")
    parser.add_argument('-f', '--config-file', metavar='config_file',
                        nargs=1, type=argparse.FileType('r'),
                        help='Configuration file (mandatory)')

    try:
        _main(parser.parse_args())
    except ValueError as e:
        print("There was an error running the provided configuration")
        print("Please check the configuration and retry")
        print(e)
        if DEBUG:
            raise e
    except ValidationError as e:
        print("The provided configuration file is not in the desired format:")
        print(e)
        if DEBUG:
            raise e
    except Exception as e:
        print("There was an unexpected error: ")
        print(e)
        if DEBUG:
            raise e
