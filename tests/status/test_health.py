from flask import url_for


class TestHealth:
    def test_health_check(self, client):
        response = client.get(url_for("status.health_check"))
        assert response.status_code == 200
