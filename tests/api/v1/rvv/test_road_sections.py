from flask import url_for
import pytest
from unittest.mock import MagicMock, patch

from tests.conftest import (
    vehicle_valid_url_parameters,
    vehicle_invalid_url_parameters_test_data,
)

QUERY_RESULT = {
    "features": [
        {
            "geometry": {
                "coordinates": [[[5.005628640683829, 52.135753997129704]]],
                "crs": {"properties": {"name": "EPSG:4326"}, "type": "name"},
                "type": "MultiLineString",
            },
            "properties": {
                "bereikbaarheidStatusCode": 11001,
                "id": 257321001,
            },
            "type": "Feature",
        }
    ],
    "type": "FeatureCollection",
}


class TestRvvRoadSections:
    @patch(
        "src.app.api.v1.rvv.road_sections.query_db_road_sections_rvv",
        MagicMock(return_value=QUERY_RESULT),
    )
    def test_returns_rvv_road_sections(self, client):
        """
        The endpoint should return the road sections for a vehicle
        formatted as a FeatureCollection.
        """
        response = client.get(
            url_for(
                "api_v1.roads_sections_rvv", **vehicle_valid_url_parameters
            )
        )

        assert response.status_code == 200
        assert response.json == QUERY_RESULT

    @patch(
        "src.app.api.v1.rvv.road_sections.query_db_road_sections_rvv",
        MagicMock(return_value={"type": "FeatureCollection", "features": []}),
    )
    def test_returns_empty_collection_when_no_sections_are_found(self, client):
        """
        If no road sections are found, the endpoint should return
        an empty FeatureCollection.
        """
        response = client.get(
            url_for(
                "api_v1.roads_sections_rvv", **vehicle_valid_url_parameters
            )
        )

        assert response.status_code == 200
        assert response.json["type"] == "FeatureCollection"
        assert len(response.json["features"]) == 0

    @pytest.mark.parametrize(
        "invalid_url_parameters, error_key",
        vehicle_invalid_url_parameters_test_data(vehicle_valid_url_parameters),
    )
    def test_returns_error_message_when_query_parameter_is_incorrect(
        self, client, invalid_url_parameters, error_key
    ):
        """
        If one of the query params is incorrect or missing,
        the endpoint should return a validation error.
        """
        response = client.get(
            url_for("api_v1.roads_sections_rvv", **invalid_url_parameters)
        )

        assert response.status_code == 422
        assert len(response.json["detail"]["query"][error_key]) == 1
        assert response.json["message"] == "Validation error"
