from apiflask import Schema, fields
import logging

from .. import api_v1
from ....db import query_db

LOGGER = logging.getLogger("gunicorn_error")


class RoadSectionsValidationSchema(Schema):
    wegvakId = fields.Integer(required=True)


@api_v1.get("/wegvakken/<wegvakId>")
@api_v1.input(RoadSectionsValidationSchema, location="path")
def road_section_by_id(wegvakId, _):
    """Wegvak kenmerken

    Retourneert een wegvak als FeatureCollection op basis van het NWB wegvak ID
    """
    result = query_db_road_sections(wegvakId)

    # https://datatracker.ietf.org/doc/html/rfc7946#section-3.3
    return {
        "type": "FeatureCollection",
        "features": [result[0]] if result else [],
    }


def query_db_road_sections(road_section_wvk_id):
    """
    Queries database for road sections based on wvk_id
    :param road_section_wvk_id: int - the wvk_id of the road section
    :return: object - road section with relationships
    """
    db_query = """
        select json_build_object(
            'geometry', ST_Transform(nwb.geom, 4326)::json,
            'properties', json_build_object(
                'wegvakId', nwb.wvk_id,
                'wegvakBegindatum', nwb.wvk_begdat,
                'junctieIdBegin', nwb.jte_id_beg,
                'junctieIdEind', nwb.jte_id_end,
                'wegbeheerdersoort', nwb.wegbehsrt,
                'wegnummer', nwb.wegnummer,
                'wegdeelletter', nwb.wegdeelltr,
                'hectoletter', nwb.hecto_lttr,
                'baansubsoortCode', case
                    when err.bst_code in ('FP','VP','BU') then err.bst_code
                    when err.bst_code = 'auto' then null
                    else nwb.bst_code
                    end,
                'relatievePositieCode', nwb.rpe_code,
                'administratieveRichting', nwb.admrichtng,
                'rijrichting', case
                    when err.rijrichtng in ('H','B','T') then err.rijrichtng
                    else nwb.rijrichtng
                    end,
                'straatNaam', nwb.stt_naam,
                'straatNaamBron', nwb.stt_bron,
                'woonplaats', nwb.wpsnaam,
                'gemeenteId', nwb.gme_id,
                'toegepasteCorrecties', jsonb_build_array(
                    (case
                        when err.bst_code in ('FP','VP','BU')
                        then json_build_object(
                            'attribuutnaam', 'baansubsoortCode',
                            'nwbWaarde', nwb.bst_code,
                            'gecorrigeerdNaar', err.bst_code
                        )
                        else '"emptyrow"'
                        end
                    ),
                    (case
                        when err.rijrichtng in ('H','B','T')
                        then json_build_object(
                            'attribuutnaam', 'rijrichting',
                            'nwbWaarde', nwb.rijrichtng,
                            'gecorrigeerdNaar', err.rijrichtng
                        )
                        else '"emptyrow"'
                        end
                    )
                ) - 'emptyrow'
            ),
            'type', 'Feature'
        )
        from bereikbaarheid.nwb_wegvakken nwb

        left join bereikbaarheid.nwb_wegvakken_selection_gm0344_erratum err
            on nwb.wvk_id = err.id

        where nwb.wvk_id = %(road_section_wvk_id)s

        group by nwb.wvk_id, err.id
    """

    query_params = {"road_section_wvk_id": road_section_wvk_id}

    try:
        return query_db(db_query, query_params, True)

    except Exception:
        LOGGER.error("Error while retrieving road section by wvk_id")
