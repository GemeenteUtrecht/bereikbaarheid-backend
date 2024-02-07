from apiflask import fields, validators
import logging

from .. import api_v1
from ...validation import is_bus, is_company_car, VehicleValidationSchema
from ....db import query_db

LOGGER = logging.getLogger("gunicorn_error")


class RvvTrafficSignsValidationSchema(VehicleValidationSchema):
    categorie = fields.List(
        fields.String(
            required=True,
            validate=validators.OneOf(
                [
                    "verbod met uitzondering",
                    "verplichting",
                    "vooraankondiging",
                ]
            ),
        ),
        metadata={
            "description": "Eén of meerdere verkeersbordcategorieën",
            "example": ["verbod met uitzondering", "verplichting"],
            "title": "Verkeersbordcategorie",
        },
        required=True,
        validate=validators.Length(min=1),
    )


@api_v1.get("/rvv/verkeersborden")
@api_v1.input(RvvTrafficSignsValidationSchema, location="query")
def traffic_signs(query_data):
    """Verkeersborden obv voertuig kenmerken

    Retourneert verkeersborden obv voertuig kenmerken
    in FeatureCollection format.
    """
    result = query_db_traffic_signs(
        query_data["categorie"],
        query_data["voertuigAslast"],
        query_data["voertuigHeeftAanhanger"],
        query_data["voertuigHoogte"],
        query_data["voertuigLengte"],
        query_data["voertuigToegestaanMaximaalGewicht"],
        query_data["voertuigTotaalGewicht"],
        query_data["voertuigType"],
        query_data["voertuigBreedte"],
    )

    # https://datatracker.ietf.org/doc/html/rfc7946#section-3.3
    return {
        "type": "FeatureCollection",
        "features": [i[0] for i in result] if result else [],
    }


def query_db_traffic_signs(
    traffic_sign_categories,
    vehicle_axle_weight,
    vehicle_has_trailer,
    vehicle_height,
    vehicle_length,
    vehicle_max_allowed_weight,
    vehicle_total_weight,
    vehicle_type,
    vehicle_width,
):
    """
    Fetches traffic signs from database
    :param traffic_sign_categories: one or more of the following categories:
        'prohibition', 'prohibition with exception', 'prohibition ahead',
    :param vehicle_type: string - one of the RDW vehicle types
    :param vehicle_length: float - length of the vehicle
    :param vehicle_width: float - width of the vehicle
    :param vehicle_has_trailer: 'true' or 'false' - if vehicle has a trailer
    :param vehicle_height: float - height of the vehicle
    :param vehicle_axle_weight: int - axle weight of the vehicle
    :param vehicle_total_weight: int - total weight of the vehicle
    :param vehicle_max_allowed_weight: int - max allowed weight of the vehicle
    :return: object - traffic signs based on vehicle properties and expert mode
    """

    db_query = """
        select json_build_object(
            'type','Feature',
            'properties', json_build_object(
                'categorie', type_bord,
                'bordWaarde', bord_waarde,
                'id', id,
                'ndwId', ndwid,
                'netwerkWegvakId', wvk_id_validated,
                'kijkrichting', side,
                'onderbordTekst', coalesce(nullif(onderbord, 'NULL'), null),
                'rvvCode', rvvcode,
                'straatNaam', "name",
                'urlNaarAfbeelding', image
            ),
            'geometry', ST_Transform(geom, 4326)::json
        )
        from (
            select
                m.id,
                m.ndwid,
                m.rvvcode,
                m.name,
                m.image,
                m.controle_status,
                m.type_bord,
                m.wvk_id_validated,
                m.bord_waarde,
                m.onderbord,
                m.side,
                m.geom
            from bereikbaarheid.traffic_signs_enriched m
            where m.wvk_id_validated <> 0
            and controle_status = 'gecontroleerd'
            and m.type_bord in %(traffic_sign_categories)s
            and ((
                    (m.rvvcode = 'C7' or m.rvvcode = 'C7(Zone)')
                    and (%(bedrijfsauto)s is true and %(max_massa)s > 3500)
                    or (m.rvvcode = 'C7A' and %(bus)s is true)
                    or (m.rvvcode = 'C10' and %(aanhanger)s is true)
                    or (m.rvvcode = 'C7B'
                        and (
                            (%(bedrijfsauto)s is true
                            and (%(max_massa)s > 3500)
                            or %(bus)s is true)
                        )
                        or (m.rvvcode = 'C17' and %(lengte)s > m.bord_waarde)
                        or (m.rvvcode = 'C18' and %(breedte)s > m.bord_waarde)
                        or (m.rvvcode = 'C19' and %(hoogte)s > m.bord_waarde)
                        or (m.rvvcode = 'C20' and %(aslast)s > m.bord_waarde)
                        or (
                            (m.rvvcode = 'C21' or m.rvvcode = 'C21_ZB')
                            and %(gewicht)s > m.bord_waarde
                        )
                    )
                )
            )
        ) v
    """

    query_params = {
        "bus": is_bus(vehicle_type),
        "bedrijfsauto": is_company_car(vehicle_type),
        "aanhanger": vehicle_has_trailer,
        "lengte": vehicle_length,
        "breedte": vehicle_width,
        "hoogte": vehicle_height,
        "aslast": vehicle_axle_weight,
        "gewicht": vehicle_total_weight,
        "max_massa": vehicle_max_allowed_weight,
        "traffic_sign_categories": tuple(traffic_sign_categories),
    }

    try:
        return query_db(db_query, query_params)

    except Exception:
        LOGGER.error("Error while retrieving RVV traffic signs")
