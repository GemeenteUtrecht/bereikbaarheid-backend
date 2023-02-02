from apiflask import fields, validators
import logging

from .. import api_v1
from ...validation import bbox, VehicleValidationSchema
from ... import vehicleTypes
from ....db import query_db

LOGGER = logging.getLogger("gunicorn_error")


class RvvLocationValidationSchema(VehicleValidationSchema):
    lat = fields.Float(
        required=True,
        validate=[
            validators.Range(min=bbox["lat"]["min"], max=bbox["lat"]["max"])
        ],
    )

    lon = fields.Float(
        required=True,
        validate=[
            validators.Range(min=bbox["lon"]["min"], max=bbox["lon"]["max"])
        ],
    )


@api_v1.get("/rvv/locatie")
@api_v1.input(RvvLocationValidationSchema, location="query")
def permits(query):
    """RVV info obv locatie en voertuigkenmerken

    Retourneert RVV informatie obv locatie en voertuigkenmerken
    in JSONAPI format.
    """
    return query_db_permits(
        query["voertuigType"],
        query["voertuigLengte"],
        query["voertuigBreedte"],
        query["voertuigHeeftAanhanger"],
        query["voertuigHoogte"],
        query["voertuigAslast"],
        query["voertuigTotaalGewicht"],
        query["voertuigToegestaanMaximaalGewicht"],
        query["lat"],
        query["lon"],
    )


def query_db_permits(
    vehicle_type,
    vehicle_length,
    vehicle_width,
    vehicle_has_trailer,
    vehicle_height,
    vehicle_axle_weight,
    vehicle_total_weight,
    vehicle_max_allowed_weight,
    lat,
    lon,
):
    """
    Queries database for permits based on location and vehicle properties
    :param vehicle_type: string - one of the RDW vehicle types
    :param vehicle_length: float - length of the vehicle
    :param vehicle_width: float - width of the vehicle
    :param vehicle_has_trailer: 'true' or 'false' - if vehicle has a trailer
    :param vehicle_height: float - height of the vehicle
    :param vehicle_axle_weight: int - axle weight of the vehicle
    :param vehicle_total_weight: int - total weight of the vehicle
    :param vehicle_max_allowed_weight: int - max allowed weight of the vehicle
    :param lat: float - the latitude of the location
    :param lon: float - the longitude of the location
    :return: object - permits based on location and vehicle properties
    """

    # default response
    # https://jsonapi.org/format/
    response = {"data": None, "errors": [], "meta": {}}

    db_query = """
        select json_build_object(
            'id', id,
            'attributes',json_build_object(
                'afstandTotBestemmingInMeters', afstand_in_m::int,
                'behoeftOntheffingRvv', rvv_boolean::boolean,
                'locatie', geom
            )
        )
        from (
            select v.id,
            case
                when v.bereikbaar_status_code = 888 then 'true'
                when v.bereikbaar_status_code = 777 then 'true'
                when v.bereikbaar_status_code = 666 then 'true'
                when v.bereikbaar_status_code = 444 then 'true'
                else 'false'
            end as rvv_boolean,

            ST_closestpoint(
                st_transform(v.geom, 4326),
                st_setsrid(ST_MakePoint(%(lon)s, %(lat)s), 4326)
            ) as geom,

            st_length(
                st_transform(
                    st_shortestline(
                        st_transform(v.geom,4326),
                        st_setsrid(ST_MakePoint(%(lon)s, %(lat)s), 4326)
                    ),
                    28992
                )
            ) as afstand_in_m

            from (
                select
                    abs(n.id) as id,
                    max(
                        case
                            when n.cost is NULL then 888
                            when routing.agg_cost is null then 777
                            when (n.c07 is true and %(bedrijfsauto)s is true and %(max_massa)s > 3500)
                                or n.c07a is true and %(bus)s is true
                                or n.c10 is true and %(aanhanger)s is true
                                or n.c17 < %(lengte)s
                                or n.c18 < %(breedte)s
                                or n.c19 < %(hoogte)s
                                or n.c20 < %(aslast)s
                                or n.c21 < %(gewicht)s
                                then 666
                            else 444
                        end
                    ) as bereikbaar_status_code,
                    g.geom as geom
                from bereikbaarheid.nwb_wegvakken_selection_enriched_directed n
                left join (
                    SELECT start_vid as source,
                    end_vid as target,
                    agg_cost FROM pgr_dijkstraCost('
                        select id, source, target, cost
                        from bereikbaarheid.nwb_wegvakken_selection_enriched_directed
                        where (%(lengte)s < c17 or c17 is null)
                        and (%(breedte)s < c18 or c18 is null)
                        and (%(hoogte)s < c19 or c19 is null)
                        and (%(aslast)s < c20 or c20 is null)
                        and (%(gewicht)s < c21 or c21 is null)
                        and (
                                c07 is false
                                or (c07 is true and %(bedrijfsauto)s is false)
                                or (
                                    c07 is true
                                    and %(bedrijfsauto)s is true
                                    and %(max_massa)s <= 3500
                                )
                            )
                            and (
                                c07a is false
                                or (c07a is true and %(bus)s is false)
                            )
                            and (
                                c10 is false
                                or (c10 is true and %(aanhanger)s is false)

                        )
                        ',
                        271319101,
                        array(
                            select node
                            from bereikbaarheid.bereikbaarheid.nwb_wegvakken_selection_node
                        )
                    )
                ) as routing on n.source=routing.target

                left join bereikbaarheid.nwb_wegvakken_selection_enriched_directed g
                    on abs(n.id) = g.id
                    where abs(n.id) in (
                        select id
                        from bereikbaarheid.nwb_wegvakken_selection_enriched_directed
                        where id > 0
                    )
                    and n.cost > 0

                group by abs(n.id), g.geom
                order by abs(n.id)) v

                left join bereikbaarheid.nwb_wegvakken_selection_enriched_directed as tiles
                    on v.id=tiles.id
                    where v.id = (
                        SELECT id
                        from bereikbaarheid.nwb_wegvakken_selection_enriched_directed a
                        where a.id > 0
                        order by st_length(
                            st_transform(
                                st_shortestline(
                                    st_setsrid(
                                        ST_MakePoint(%(lon)s, %(lat)s),
                                        4326
                                    ),
                                    st_linemerge(a.geom4326)
                                ),
                                4326
                            )
                        ) asc
                        limit 1
                    )
        ) m """  # noqa: E501 - ignore line-length in case of long table names

    query_params = {
        "bedrijfsauto": vehicleTypes.vehicle_is_company_car(vehicle_type),
        "bus": vehicleTypes.vehicle_is_bus(vehicle_type),
        "aanhanger": vehicle_has_trailer,
        "lengte": vehicle_length,
        "breedte": vehicle_width,
        "hoogte": vehicle_height,
        "aslast": vehicle_axle_weight,
        "gewicht": vehicle_total_weight,
        "max_massa": vehicle_max_allowed_weight,
        "permit_zone_milieu": True,
        "permit_zone_7_5": True,
        "lat": lat,
        "lon": lon,
    }

    try:
        result = query_db(db_query, query_params, True)

        if result:
            response["data"] = result[0]

    except Exception:
        LOGGER.error("Error while retrieving rvv location info")

        response["errors"].append(
            {
                "status": 500,
                "title": "Error",
                "detail": "Something went wrong.",
            }
        )

    return response
