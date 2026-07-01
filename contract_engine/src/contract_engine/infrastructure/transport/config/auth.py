from typing import Literal

from pydantic import BaseModel


class NoAuth(BaseModel):
    type: Literal["none"] = "none"


class UsernamePasswordAuth(BaseModel):
    type: Literal["basic"] = "basic"

    username: str
    password: str


class AzureClientCredentialsAuth(BaseModel):
    type: Literal["azure"] = "azure"

    tenant_id: str
    client_id: str
    client_secret: str


AuthConfig = NoAuth | UsernamePasswordAuth | AzureClientCredentialsAuth
