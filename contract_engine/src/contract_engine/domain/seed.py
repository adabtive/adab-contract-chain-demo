from pydantic import BaseModel, ConfigDict


class Seed(BaseModel):
    label: int | str
    value: int

    model_config = ConfigDict(frozen=True)
