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
def permits(query_data):
    """RVV info obv locatie en voertuigkenmerken

    Retourneert RVV informatie obv locatie en voertuigkenmerken
    in JSONAPI format.
    """
    return query_db_permits(
        query_data["voertuigType"],
        query_data["voertuigLengte"],
        query_data["voertuigBreedte"],
        query_data["voertuigHeeftAanhanger"],
        query_data["voertuigHoogte"],
        query_data["voertuigAslast"],
        query_data["voertuigTotaalGewicht"],
        query_data["voertuigToegestaanMaximaalGewicht"],
        query_data["lat"],
        query_data["lon"],
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
            'id', level_a.id,
            'attributes',json_build_object(
                'afstandTotBestemmingInMeters', (
                                SELECT st_length(st_transform(st_shortestline(st_setsrid(ST_MakePoint(%(lon)s, %(lat)s),4326),st_linemerge(a.geom4326)),28992))
                                from bereikbaarheid.nwb_wegvakken_selection_enriched_directed a
                                where bst_code_binair= true
                                order by st_length(st_transform(st_shortestline(st_setsrid(
                                                ST_MakePoint(%(lon)s, %(lat)s),4326),st_linemerge(a.geom4326)),28992)
                                ) asc
                                limit 1
                            )::int,
                'behoeftOntheffingRvv', level_a.rvv_boolean::boolean,
                'locatie', level_a.geom))
        from (
            select level_aa.id,
            case	when level_aa.bereikbaar_status_code = 111 then true
                    when level_aa.bereikbaar_status_code = 222 then true
                    when level_aa.bereikbaar_status_code = 333 then true
                    when level_aa.bereikbaar_status_code = 444 then true
                    else false end as rvv_boolean,
             ST_closestpoint(
                        st_transform(level_aa.geom, 4326),
                        st_setsrid(ST_MakePoint(%(lon)s, %(lat)s), 4326)
                    ) as geom
            from (
                select abs(level_aaa.id) as id,
                max(
                case	when level_aaa.cost is NULL then 111
                        when level_aab.agg_cost is null then 222
                        when level_aaa.c07 is true and %(bedrijfsauto)s is true
                        and %(max_massa)s > 3500
                        or level_aaa.c07a is true and %(bus)s is true
                        or level_aaa.c10 is true and %(aanhanger)s is true
                        or level_aaa.c17 < %(lengte)s
                        or level_aaa.c18 < %(breedte)s
                        or level_aaa.c19 < %(hoogte)s
                        or level_aaa.c20 < %(aslast)s
                        or level_aaa.c21 < %(gewicht)s
                        then 333
                        else 999 end ) as bereikbaar_status_code,
                level_aac.geom
                from bereikbaarheid.nwb_wegvakken_selection_enriched_directed level_aaa
                left join (
                    SELECT start_vid as source,
                    end_vid as target,
                    agg_cost
                    FROM pgr_dijkstraCost('
                        select id, source, target, cost
                        from bereikbaarheid.nwb_wegvakken_selection_enriched_directed as level_aaba
                        where level_aaba.cost > 0
                        and ((( -.01 + %(lengte)s ) < level_aaba.c17 or level_aaba.c17 is null)
                            and (( -.01 + %(breedte)s ) < level_aaba.c18 or level_aaba.c18 is null)
                            and (( -.01 +%(hoogte)s ) < level_aaba.c19 or level_aaba.c19 is null)
                            and (( -1 + %(aslast)s ) < level_aaba.c20 or level_aaba.c20 is null)
                            and (( -1 + %(gewicht)s ) < level_aaba.c21 or level_aaba.c21 is null)
                            and 	( level_aaba.c07 is false or (level_aaba.c07 is true and %(bedrijfsauto)s is false)
                                    or (level_aaba.c07 is true and %(bedrijfsauto)s is true and %(max_massa)s <= 3500))
                            and (level_aaba.c07a is false or (level_aaba.c07a is true and %(bus)s is false))
                            and (level_aaba.c10 is false or (level_aaba.c10 is true and %(aanhanger)s is false))
                            )',
                        271319101,
                        array(select level_aabx.node from bereikbaarheid.nwb_wegvakken_selection_node as level_aabx))
                ) as level_aab
                on level_aaa.source = level_aab.target
                left join bereikbaarheid.nwb_wegvakken_selection_enriched_directed level_aac
                on abs(level_aaa.id) = level_aac.id
                where abs(level_aaa.id) in (select level_aax.id from bereikbaarheid.nwb_wegvakken_selection_enriched_directed as level_aax where level_aax.id > 0)
                and level_aaa.cost > 0
                and level_aaa.gme_id = 344
                and level_aaa.wegbehsrt = 'G'
                group by abs(level_aaa.id), level_aac.geom
                order by abs(level_aaa.id)
            ) as level_aa
            where level_aa.id = (	SELECT  abs(id)
                                    from bereikbaarheid.nwb_wegvakken_selection_enriched_directed a
                                    where bst_code_binair= true
                                    order by  st_length(st_transform(st_shortestline(st_setsrid(ST_MakePoint(%(lon)s, %(lat)s),4326),st_linemerge(a.geom4326)),28992)) asc,
                                    a.cost desc
                                    limit 1)
        ) as level_a """  # noqa: E501 - ignore line-length in case of long table names

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
