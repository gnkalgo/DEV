import json

from app.brokers.base import BrokerAdapter
from app.brokers.dhan import DhanAdapter
from app.brokers.groww import GrowwAdapter
from app.core.security import decrypt_data
from app.models import BrokerConnection, BrokerType


def get_broker_adapter(connection: BrokerConnection) -> BrokerAdapter:
    credentials = json.loads(decrypt_data(connection.encrypted_credentials))

    if connection.broker == BrokerType.DHAN:
        return DhanAdapter(
            access_token=credentials.get("access_token", ""),
            client_id=credentials.get("client_id") or connection.client_id,
        )
    if connection.broker == BrokerType.GROWW:
        return GrowwAdapter(access_token=credentials.get("access_token", ""))

    raise ValueError(f"Unsupported broker: {connection.broker}")
