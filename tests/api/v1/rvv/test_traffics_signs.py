from flask import url_for
import pytest
from unittest.mock import MagicMock, patch

from tests.conftest import (
    remove_key_from_dict,
    vehicle_valid_url_parameters,
    vehicle_invalid_url_parameters_test_data,
)

QUERY_RESULT = [
    [
        {
            "geometry": {
                "coordinates": [5.112518722069883, 52.09462244348518],
                "crs": {"properties": {"name": "EPSG:4326"}, "type": "name"},
                "type": "Point",
            },
            "properties": {
                "bordWaarde": 9,
                "categorie": "verplichting",
                "id": 11782936,
                "kijkrichting": "Z",
                "ndwId": "af415b96-88d3-494d-95cb-0eb893da8bda",
                "netwerkWegvakId": 600393126,
                "onderbordTekst": None,
                "rvvCode": "C17",
                "straatNaam": "Dirck van Zuylenstraat",
                "urlNaarAfbeelding": "https://url.to/the-sign-image-3456.jpg",
            },
            "type": "Feature",
        }
    ]
]

valid_url_parameters = {
    **vehicle_valid_url_parameters,
    "categorie": ["verbod met uitzondering", "verplichting"],
}


class TestRvvTrafficSigns:
    @patch(
        "src.app.api.v1.rvv.traffic_signs.query_db_traffic_signs",
        MagicMock(return_value=QUERY_RESULT),
    )
    def test_returns_traffics_signs(self, client):
        """
        The endpoint should return the traffic signs for a vehicle
        formatted as a FeatureCollection.
        """
        response = client.get(
            url_for("api_v1.traffic_signs", **valid_url_parameters)
        )

        assert response.status_code == 200
        assert response.json["features"] == QUERY_RESULT[0]

    @pytest.mark.parametrize(
        "invalid_url_parameters, error_key",
        [
            (
                {**valid_url_parameters, "categorie": ["geen categorie"]},
                "categorie",
            ),
            (
                remove_key_from_dict(valid_url_parameters, "categorie"),
                "categorie",
            ),
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
            url_for("api_v1.traffic_signs", **invalid_url_parameters)
        )

        assert response.status_code == 422
        assert len(response.json["detail"]["query"][error_key]) == 1
        assert response.json["message"] == "Validation error"
