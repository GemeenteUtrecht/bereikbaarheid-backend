from flask import url_for
import pytest
from unittest.mock import MagicMock, patch

from tests.conftest import (
    remove_key_from_dict,
    vehicle_valid_url_parameters,
    vehicle_invalid_url_parameters_test_data,
)

QUERY_RESULT = [
    {
        "data": {
            "attributes": {
                "afstandTotBestemmingInMeters": 6,
                "behoeftOntheffingRvv": False,
                "locatie": {
                    "coordinates": [5.099953390917054, 52.10904332286939],
                    "crs": {
                        "properties": {"name": "EPSG:4326"},
                        "type": "name",
                    },
                    "type": "Point",
                },
            },
            "id": 270315072,
        },
        "errors": [],
        "meta": {},
    }
]

valid_url_parameters = {
    **vehicle_valid_url_parameters,
    "lat": 52.109,
    "lon": 5.1,
}


class TestRvvLocation:
    @patch(
        "src.app.api.v1.rvv.location.query_db_permits",
        MagicMock(return_value=QUERY_RESULT),
    )
    def test_returns_details_for_a_location(self, client):
        """
        The endpoint should return the details for a location
        as a JSONAPI formatted response.
        """
        response = client.get(
            url_for("api_v1.permits", **valid_url_parameters)
        )

        assert response.status_code == 200
        assert response.json == QUERY_RESULT

    @pytest.mark.parametrize(
        "invalid_url_parameters, error_key",
        [
            ({**valid_url_parameters, "lat": 51.1}, "lat"),
            ({**valid_url_parameters, "lat": 52.2}, "lat"),
            (remove_key_from_dict(valid_url_parameters, "lat"), "lat"),
            ({**valid_url_parameters, "lon": 4.8}, "lon"),
            ({**valid_url_parameters, "lon": 5.2}, "lon"),
            (remove_key_from_dict(valid_url_parameters, "lon"), "lon"),
        ]
        + vehicle_invalid_url_parameters_test_data(valid_url_parameters),
    )
    def test_returns_error_message_when_query_parameter_is_incorrect(
        self, client, invalid_url_parameters, error_key
    ):
        """
        If one of the query params is incorrect or missing,
        the endpoint should return a validation error.
        """
        response = client.get(
            url_for("api_v1.permits", **invalid_url_parameters)
        )

        assert response.status_code == 422
        assert len(response.json["detail"]["query"][error_key]) == 1
        assert response.json["message"] == "Validation error"
