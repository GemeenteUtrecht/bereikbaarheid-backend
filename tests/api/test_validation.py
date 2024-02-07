import pytest

from src.app.api.validation import is_bus, is_company_car


class TestValidation:
    @pytest.mark.parametrize(
        "test_input, expected",
        [("Bus", True), ("bus", True), ("Bedrijfsauto", False)],
    )
    def test_is_bus(self, test_input, expected):
        assert is_bus(test_input) is expected

    @pytest.mark.parametrize(
        "test_input, expected",
        [("Bedrijfsauto", True), ("bedrijfsauto", True), ("Bus", False)],
    )
    def test_is_company_car(self, test_input, expected):
        assert is_company_car(test_input) is expected
