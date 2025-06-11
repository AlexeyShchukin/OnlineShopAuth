import asyncio
import json
from datetime import datetime, timezone
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from aiokafka import AIOKafkaProducer

from src.core.config import settings

KAFKA_BOOTSTRAP_SERVERS = "host.docker.internal:19092"
KAFKA_TOPIC = "auth.public_key_updated"


def generate_rsa_key_pair():
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key()

    # Сохраняем приватный ключ
    with open(settings.private_key_file, "wb") as f:
        f.write(
            private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )
        )

    # Сохраняем публичный ключ
    with open(settings.public_key_file, "wb") as f:
        f.write(
            public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
        )

    print("Keys generated and saved.")
    settings.clear_keys_cache()


async def send_kafka_event():
    producer = AIOKafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        acks='all',
        enable_idempotence=True
    )
    await producer.start()
    try:
        event = {
            "event": "public_key_updated",
            "key_version": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        }
        await producer.send_and_wait(
            topic=KAFKA_TOPIC,
            value=json.dumps(event).encode("utf-8")
        )
        print(f"Kafka event sent: {event}")
    finally:
        await producer.stop()


async def main():
    generate_rsa_key_pair()
    await send_kafka_event()


if __name__ == "__main__":
    asyncio.run(main())
    # asyncio.run(send_kafka_event())
