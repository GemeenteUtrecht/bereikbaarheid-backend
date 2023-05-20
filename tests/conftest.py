import copy
import os
import pytest

from src.app import create_app

vehicle_valid_url_parameters = {
    "voertuigAslast": 10000,
    "voertuigHeeftAanhanger": False,
    "voertuigHoogte": 3.13,
    "voertuigLengte": 13.95,
    "voertuigTotaalGewicht": 24600,
    "voertuigType": "Bus",
    "voertuigBreedte": 2.55,
    "voertuigToegestaanMaximaalGewicht": 24600,
}


@pytest.fixture(scope="session")
def app():
    """
    Setup our flask test app, this only gets executed once.

    :return: Flask app
    """
    os.environ["APP_SECRET"] = "secret"

    _app = create_app()

    _app.config.update(
        {
            "SERVER_NAME": "localhost.dev:8000",
            "TESTING": True,
        }
    )

    # Establish an application context before running the tests.
    ctx = _app.app_context()
    ctx.push()

    yield _app

    ctx.pop()


@pytest.fixture(scope="function")
def client(app):
    """
    Setup an app client, this gets executed for each test function.

    :param app: Pytest fixture
    :return: Flask app client
    """
    yield app.test_client()


def remove_key_from_dict(dictionary, key):
    new_dictionary = copy.deepcopy(dictionary)
    new_dictionary.pop(key)
    return new_dictionary


def vehicle_invalid_url_parameters_test_data(valid_url_parameters):
    """
    (test_input,expected) tuples for usage in @pytest.mark.parametrize
    an item has shape of (dict_url_params, error_key_in_json_response)
    """
    return [
        ({**valid_url_parameters, "voertuigAslast": -1}, "voertuigAslast"),
        ({**valid_url_parameters, "voertuigAslast": 13000}, "voertuigAslast"),
        (
            remove_key_from_dict(valid_url_parameters, "voertuigAslast"),
            "voertuigAslast",
        ),
        (
            {**valid_url_parameters, "voertuigHeeftAanhanger": "notABoolean"},
            "voertuigHeeftAanhanger",
        ),
        (
            remove_key_from_dict(
                valid_url_parameters, "voertuigHeeftAanhanger"
            ),
            "voertuigHeeftAanhanger",
        ),
        ({**valid_url_parameters, "voertuigHoogte": -1}, "voertuigHoogte"),
        ({**valid_url_parameters, "voertuigHoogte": 4.1}, "voertuigHoogte"),
        (
            remove_key_from_dict(valid_url_parameters, "voertuigHoogte"),
            "voertuigHoogte",
        ),
        ({**valid_url_parameters, "voertuigLengte": -1}, "voertuigLengte"),
        ({**valid_url_parameters, "voertuigLengte": 22.1}, "voertuigLengte"),
        (
            remove_key_from_dict(valid_url_parameters, "voertuigLengte"),
            "voertuigLengte",
        ),
        (
            {**valid_url_parameters, "voertuigTotaalGewicht": -1},
            "voertuigTotaalGewicht",
        ),
        (
            {**valid_url_parameters, "voertuigTotaalGewicht": 60001},
            "voertuigTotaalGewicht",
        ),
        (
            remove_key_from_dict(
                valid_url_parameters, "voertuigTotaalGewicht"
            ),
            "voertuigTotaalGewicht",
        ),
        ({**valid_url_parameters, "voertuigType": "Oplegger"}, "voertuigType"),
        (
            remove_key_from_dict(valid_url_parameters, "voertuigType"),
            "voertuigType",
        ),
        ({**valid_url_parameters, "voertuigBreedte": -1}, "voertuigBreedte"),
        ({**valid_url_parameters, "voertuigBreedte": 3.1}, "voertuigBreedte"),
        (
            remove_key_from_dict(valid_url_parameters, "voertuigBreedte"),
            "voertuigBreedte",
        ),
        (
            {**valid_url_parameters, "voertuigToegestaanMaximaalGewicht": -1},
            "voertuigToegestaanMaximaalGewicht",
        ),
        (
            {
                **valid_url_parameters,
                "voertuigToegestaanMaximaalGewicht": 60001,
            },
            "voertuigToegestaanMaximaalGewicht",
        ),
        (
            remove_key_from_dict(
                valid_url_parameters, "voertuigToegestaanMaximaalGewicht"
            ),
            "voertuigToegestaanMaximaalGewicht",
        ),
    ]
