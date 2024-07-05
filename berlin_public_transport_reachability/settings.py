import tomllib
from pathlib import Path

import pydantic

from berlin_public_transport_reachability.enums import TimeValue


class DestinationSettings(pydantic.BaseModel):
    destinations: list[str]
    time: TimeValue
    max_transfers: int


class GeneralSettings(pydantic.BaseModel):
    max_duration: int
    circle_radius: int


class Settings(pydantic.BaseModel):
    destination: DestinationSettings
    general: GeneralSettings


def parse_settings() -> Settings:
    config_toml_path = Path(__file__).resolve().parent.parent.joinpath("settings.toml")
    with config_toml_path.open("rb") as file:
        return Settings.parse_obj(tomllib.load(file))


settings = parse_settings()
