from contract_engine.infrastructure.transport.auth.auth_handler import AuthHandler
from contract_engine.infrastructure.transport.auth.azure_auth_handler import AzureAuthHandler
from contract_engine.infrastructure.transport.auth.basic_auth_handler import BasicAuthHandler
from contract_engine.infrastructure.transport.auth.no_auth_handler import NoAuthHandler
from contract_engine.infrastructure.transport.config.auth import (
    AuthConfig,
    AzureClientCredentialsAuth,
    UsernamePasswordAuth,
)


def build_auth_handler(config: AuthConfig) -> AuthHandler:
    if isinstance(config, AzureClientCredentialsAuth):
        return AzureAuthHandler(config)

    if isinstance(config, UsernamePasswordAuth):
        return BasicAuthHandler(config)

    return NoAuthHandler()
