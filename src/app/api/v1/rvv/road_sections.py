import logging

from .. import api_v1
from ...validation import VehicleValidationSchema
from ... import vehicleTypes
from ....db import query_db

LOGGER = logging.getLogger("gunicorn_error")


@api_v1.get("/rvv/wegvakken")
@api_v1.input(VehicleValidationSchema, location="query")
def roads_sections_rvv(query):
    """Wegvakken waarvoor een RVV ontheffing nodig is obv voertuig kenmerken

    Retourneert wegvakken waarvoor een RVV ontheffing nodig is obv
    voertuig kenmerken in FeatureCollection format.
    """
    return query_db_road_sections_rvv(
        query["voertuigType"],
        query["voertuigLengte"],
        query["voertuigBreedte"],
        query["voertuigHeeftAanhanger"],
        query["voertuigHoogte"],
        query["voertuigAslast"],
        query["voertuigTotaalGewicht"],
        query["voertuigToegestaanMaximaalGewicht"],
    )


def query_db_road_sections_rvv(
    vehicle_type,
    vehicle_length,
    vehicle_width,
    vehicle_has_trailer,
    vehicle_height,
    vehicle_axle_weight,
    vehicle_total_weight,
    vehicle_max_allowed_weight,
):
    """
    Fetches prohibitory roads from database
    :param vehicle_type: string - one of the RDW vehicle types
    :param vehicle_length: float - length of the vehicle
    :param vehicle_width: float - width of the vehicle
    :param vehicle_has_trailer: 'true' or 'false' - if vehicle has a trailer
    :param vehicle_height: float - height of the vehicle
    :param vehicle_axle_weight: int - axle weight of the vehicle
    :param vehicle_total_weight: int - total weight of the vehicle
    :param vehicle_max_allowed_weight: int - max allowed weight of the vehicle
    :return: object - prohibitory roads based on vehicle properties
    """

    # default response
    # https://datatracker.ietf.org/doc/html/rfc7946#section-3.3
    response = {"type": "FeatureCollection", "features": []}

    db_query = """
        select json_build_object(
            'type','Feature',
            'properties',json_build_object(
                'bereikbaarheidStatusCode', bereikbaar_status_code,
                'id', id
            ),
            'geometry', geom::json
        )
        from (
            select v.id,
            case
                when v.bereikbaar_status_code = 111 then 11001
                when v.bereikbaar_status_code = 222 then 11001
                when v.bereikbaar_status_code = 333 then 11001
                when v.bereikbaar_status_code = 444 then 11100
                else 999
            end as bereikbaar_status_code,
            st_transform(v.geom,4326) as geom
            from (
                select
                    abs(n.id) as id,
                    max(
                        case
                            when n.cost is NULL then 111
                            when routing.agg_cost is null then 222
                            when n.c07 is true and %(bedrijfsauto)s is true
                                and %(max_massa)s > 3500
                                 or n.c07a is true and %(bus)s is true
                                 or n.c10 is true and %(aanhanger)s is true
                                or n.c17 < %(lengte)s
                                or n.c18 < %(breedte)s
                                or n.c19 < %(hoogte)s
                                or n.c20 < %(aslast)s
                                or n.c21 < %(gewicht)s
                                then 333
                            else 999
                        end
                    ) as bereikbaar_status_code,
                    g.geom
                from bereikbaarheid.nwb_wegvakken_selection_enriched_directed n
                left join (
                    SELECT start_vid as source,
                    end_vid as target,
                    agg_cost FROM pgr_dijkstraCost('
                        select id, source, target, cost
                        from bereikbaarheid.nwb_wegvakken_selection_enriched_directed
                        where cost > 0
                        and (
                            (( -.01 + %(lengte)s ) < c17 or c17 is null)
                            and (( -.01 + %(breedte)s ) < c18 or c18 is null)
                            and (( -.01 +%(hoogte)s ) < c19 or c19 is null)
                            and (( -1 + %(aslast)s ) < c20 or c20 is null)
                            and (( -1 + %(gewicht)s ) < c21 or c21 is null)
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
                        )',
                        271319101,
                        array(
                            select node
                            from bereikbaarheid.nwb_wegvakken_selection_node
                        )
                    )
                ) as routing on n.source = routing.target
                left join bereikbaarheid.nwb_wegvakken_selection_enriched_directed g
                    on abs(n.id) = g.id
                    where abs(n.id) in (
                        select id
                        from bereikbaarheid.nwb_wegvakken_selection_enriched_directed
                        where id > 0
                    )
                    and n.cost > 0
                    and n.gme_id = 344
                    and n.wegbehsrt = 'G'
                group by abs(n.id), g.geom
                order by abs(n.id)
            ) v
            where v.bereikbaar_status_code <> 999
        ) m """  # noqa: E501 - ignore line-length in case of long table names

    query_params = {
        "bus": vehicleTypes.vehicle_is_bus(vehicle_type),
        "bedrijfsauto": vehicleTypes.vehicle_is_company_car(vehicle_type),
        "aanhanger": vehicle_has_trailer,
        "lengte": vehicle_length,
        "breedte": vehicle_width,
        "hoogte": vehicle_height,
        "aslast": vehicle_axle_weight,
        "gewicht": vehicle_total_weight,
        "max_massa": vehicle_max_allowed_weight,
    }

    try:
        result = query_db(db_query, query_params)

        if result:
            response["features"] = [i[0] for i in result]

    except Exception:
        LOGGER.error("Error while retrieving rvv road sections")

    return response
