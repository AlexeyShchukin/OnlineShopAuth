from aiokafka import AIOKafkaProducer
import json

from src.core.config import settings


class KafkaProducer:
    def __init__(self, bootstrap_servers: str = settings.KAFKA_BOOTSTRAP_SERVERS):
        self.bootstrap_servers = bootstrap_servers
        self._producer = AIOKafkaProducer(
            bootstrap_servers=self.bootstrap_servers,
            value_serializer=lambda m: json.dumps(m).encode("utf-8")
        )

    async def connect(self):
        await self._producer.start()

    async def close(self):
        await self._producer.stop()

    async def send(self, topic: str, message: dict):
        await self._producer.send_and_wait(topic, message)
