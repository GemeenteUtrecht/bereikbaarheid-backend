from apiflask import APIBlueprint

status = APIBlueprint("status", __name__)

from . import health  # noqa: E402  # imports needs to be after Blueprint init
