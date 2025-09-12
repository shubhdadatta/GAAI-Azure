
"""

Required env vars
─────────────────
KV_NAME              e.g. 'BDCvault'
AZURE_CLIENT_ID
AZURE_CLIENT_SECRET
AZURE_TENANT_ID
AZURE_DEPLOYMENT
"""

from functools import lru_cache
import logging
from azure.identity import ClientSecretCredential
from azure.keyvault.secrets import SecretClient
import os
from dotenv import load_dotenv
load_dotenv()

_LOGGER = logging.getLogger(__name__)

@lru_cache
def _kv_client() -> SecretClient:
    vault_name = os.environ["KV_NAME"]
    if not vault_name:
        raise EnvironmentError("KV_NAME env var not set")

    credential = ClientSecretCredential(
        tenant_id=os.getenv("AZURE_TENANT_ID"),
        client_id=os.getenv("AZURE_CLIENT_ID"),
        client_secret=os.getenv("AZURE_CLIENT_SECRET"),
    )
    return SecretClient(vault_url=f"https://{vault_name}.vault.azure.net", credential=credential)


@lru_cache
def get_secret(name: str) -> str:
    """Fetch once per process via lru_cache."""
    _LOGGER.debug("Fetching secret %s from Key Vault", name)
    return _kv_client().get_secret(name).value