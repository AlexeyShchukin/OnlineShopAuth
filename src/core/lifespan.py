from contextlib import asynccontextmanager
from fastapi import FastAPI

from src.infrastructure.kafka.producer import KafkaProducer
from src.infrastructure.redis import create_redis

kafka_producer: KafkaProducer | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    producer = KafkaProducer()
    await producer.connect()
    app.state.kafka_producer = producer

    redis = await create_redis()
    app.state.redis = redis

    yield
    await app.state.kafka_producer.close()
    await app.state.redis.close()
