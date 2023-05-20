from flask import url_for


class TestOpenApiDocs:
    def test_openapi_docs_page(self, client):
        """
        The docs page should display interactive OpenAPI documentation.
        """
        response = client.get(url_for("openapi.docs"))
        assert response.status_code == 200
        assert b"API Nationaal wegenbestand" in response.data

    def test_openapi_specification(self, client):
        """
        Should return the OpenAPI specification in JSON format.
        """
        response = client.get(url_for("openapi.spec"))
        assert response.status_code == 200
        assert response.json["info"]["title"] == "API Nationaal wegenbestand"
