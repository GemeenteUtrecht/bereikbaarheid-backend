from flask import url_for
from unittest.mock import MagicMock, patch

QUERY_RESULT = [
    {
        "geometry": {
            "coordinates": [[[5.140321319514293, 52.07098409959794]]],
            "type": "MultiLineString",
        },
        "properties": {
            "administratieveRichting": None,
            "baansubsoortCode": None,
            "gemeenteId": 344,
            "hectoletter": "#",
            "junctieIdBegin": 276307001,
            "junctieIdEind": 600226815,
            "relatievePositieCode": "#",
            "rijrichting": "B",
            "straatNaam": "Rijndijk",
            "straatNaamBron": "BAG schrijfwijze",
            "toegepasteCorrecties": [],
            "wegbeheerdersoort": "G",
            "wegdeelletter": "#",
            "wegnummer": None,
            "wegvakBegindatum": "2022-03-01",
            "wegvakId": 1,
            "woonplaats": "Utrecht",
        },
        "type": "Feature",
    }
]


class TestRoadSectionById:
    @patch(
        "src.app.api.v1.road_sections.by_id.query_db_road_sections",
        MagicMock(return_value=QUERY_RESULT),
    )
    def test_returns_details_when_found(self, client):
        """
        If the road section is found, the endpoint should return the details
        as a FeatureCollection.
        """
        response = client.get(url_for("api_v1.road_section_by_id", wegvakId=1))

        assert response.status_code == 200
        assert response.json["type"] == "FeatureCollection"
        assert len(response.json["features"]) == 1
        assert response.json["features"][0]["properties"]["wegvakId"] == 1

    @patch(
        "src.app.api.v1.road_sections.by_id.query_db_road_sections",
        MagicMock(return_value=[]),
    )
    def test_returns_empty_collection_when_not_found(self, client):
        """
        If the road section is not found, the endpoint should an empty
        FeatureCollection.
        """
        response = client.get(url_for("api_v1.road_section_by_id", wegvakId=1))

        assert response.status_code == 200
        assert response.json["type"] == "FeatureCollection"
        assert len(response.json["features"]) == 0

    def test_requested_road_section_id_should_be_an_integer(self, client):
        """
        If the requested road section id is not an integer, the endpoint
        should return a validation error.
        """
        response = client.get(
            url_for("api_v1.road_section_by_id", wegvakId="hello")
        )

        assert response.status_code == 422
        assert b"Not a valid integer" in response.data
