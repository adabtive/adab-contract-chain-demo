from typing import Literal

from pydantic import BaseModel, ConfigDict

SerializationType = Literal[
    "json",
    "raw_packet",
    "mqtt_json",
]


class SerializationProfile(BaseModel):
    type: SerializationType

    model_config = ConfigDict(extra="forbid")
