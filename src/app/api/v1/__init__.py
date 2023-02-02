from apiflask import APIBlueprint

api_v1 = APIBlueprint("api_v1", __name__, tag="v1")

# imports need to be after Blueprint init, hence the noqa comments
from .road_sections import by_id  # noqa: E402
from .rvv import location  # noqa: E402
from .rvv import road_sections  # noqa: E402
from .rvv import traffic_signs  # noqa: E402
