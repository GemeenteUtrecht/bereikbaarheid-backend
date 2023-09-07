from apiflask import Schema, fields, validators
from marshmallow import validates, ValidationError

# Constants used for validating API parameters
bbox = {
    "lat": {"min": 52.047, "max": 52.138},
    "lon": {"min": 5.022, "max": 5.192},
}

# The vehicle parameters should be in sync with validation requirements
# for client-side forms (defined in javascript)
vehicle = {
    "axleWeight": {"min": 0, "max": 12000},  # in kilograms
    "height": {"min": 0, "max": 4},  # in meters
    "length": {"min": 0, "max": 22},  # in meters
    "maxAllowedWeight": {"min": 0, "max": 60000},  # in kilograms
    "totalWeight": {"min": 0, "max": 60000},  # in kilograms
    # vehicle types are equal to types defined by RDW
    # see https://opendata.rdw.nl/resource/9dze-d57m.json
    "types": ("Bedrijfsauto", "Bus", "Personenauto"),
    "width": {"min": 0, "max": 3},  # in meters
}


class VehicleValidationSchema(Schema):
    """
    Validates the following vehicle properties:
    - voertuigAslast
    - voertuigBreedte
    - voertuigHeeftAanhanger
    - voertuigHoogte
    - voertuigLengte
    - voertuigToegestaanMaximaalGewicht
    - voertuigTotaalGewicht
    - voertuigType
    """

    voertuigAslast = fields.Integer(
        metadata={
            "description": "De aslast van het voertuig in kilogram",
            "example": 10000,
            "title": "Aslast van het voertuig",
        },
        required=True,
        validate=[
            validators.Range(
                min=vehicle["axleWeight"]["min"],
                max=vehicle["axleWeight"]["max"],
            )
        ],
    )

    voertuigHeeftAanhanger = fields.Boolean(
        metadata={
            "description": "Heeft het voertuig een aanhanger?",
            "example": False,
            "title": "Indicator voor een aanhanger",
        },
        required=True,
    )

    voertuigHoogte = fields.Float(
        metadata={
            "description": "De hoogte van het voertuig in meters",
            "example": 3.13,
            "title": "Hoogte van het voertuig",
        },
        required=True,
        validate=[
            validators.Range(
                min=vehicle["height"]["min"],
                max=vehicle["height"]["max"],
                min_inclusive=False,
            )
        ],
    )

    voertuigLengte = fields.Float(
        metadata={
            "description": "De lengte van het voertuig in meters",
            "example": 13.95,
            "title": "Lengte van het voertuig",
        },
        required=True,
        validate=[
            validators.Range(
                min=vehicle["length"]["min"], max=vehicle["length"]["max"]
            )
        ],
    )

    voertuigToegestaanMaximaalGewicht = fields.Integer(
        metadata={
            "description": (
                "Het maximaal toegestane gewicht "
                "van het voertuig in kilogram"
            ),
            "example": 24600,
            "title": "Maximaal toegestane gewicht van het voertuig",
        },
        required=True,
        validate=[
            validators.Range(
                min=vehicle["maxAllowedWeight"]["min"],
                max=vehicle["maxAllowedWeight"]["max"],
            )
        ],
    )

    voertuigTotaalGewicht = fields.Integer(
        metadata={
            "description": "Het totale gewicht van het voertuig in kilogram",
            "example": 22150,
            "title": "Totale gewicht van het voertuig",
        },
        required=True,
        validate=[
            validators.Range(
                min=vehicle["totalWeight"]["min"],
                max=vehicle["totalWeight"]["max"],
            )
        ],
    )

    voertuigType = fields.String(
        metadata={
            "description": (
                "Het RDW type van het voertuig: "
                "Bedrijfsauto, Bus of Personenauto"
            ),
            "example": "Bedrijfsauto",
            "title": "RDW type van het voertuig",
        },
        required=True,
    )

    @validates("voertuigType")
    def allowed_vehicle_types(self, value):
        allowed_vehicle_types(value)

    voertuigBreedte = fields.Float(
        metadata={
            "description": "De breedte van het voertuig in meters",
            "example": 2.55,
            "title": "Breedte van het voertuig",
        },
        required=True,
        validate=[
            validators.Range(
                min=vehicle["width"]["min"], max=vehicle["width"]["max"]
            )
        ],
    )


def allowed_vehicle_types(vehicle_type):
    """
    Checks allowed vehicle types.
    To be used in a marshmallow Schema
    Lowercase values are also allowed, because when preparing database
    query parameters the vehicle type is checked in the same way
    """
    if not vehicle_type.casefold() in map(str.casefold, vehicle["types"]):
        raise ValidationError("Must be one of: " + ", ".join(vehicle["types"]))
