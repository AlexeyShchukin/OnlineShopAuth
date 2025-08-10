from typing import Any


from src.core.config import settings
from src.infrastructure.kafka.producer import KafkaProducer


class EventPublisher:
    def __init__(self, producer: KafkaProducer):
        self._producer = producer

    async def publish_user_registered(self, user: dict[str: Any]):
        await self._producer.send(
            topic=settings.KAFKA_USER_REGISTERED_TOPIC,
            message={
                "event_type": "user_registered",
                "user_id": str(user["id"]),
                "email": user["email"],
                "first_name": user["first_name"],
                "timestamp": user["created_at"].isoformat()
            }
        )

    async def publish_profile_updated(self, user: dict[str, Any]):
        await self._producer.send(
            topic=settings.KAFKA_USER_PROFILE_UPDATED_TOPIC,
            message={
                "event_type": "profile_updated",
                "user_id": str(user["id"]),
                "email": user["email"],
                "first_name": user["first_name"],
                "timestamp": user["created_at"].isoformat()
            }
        )
