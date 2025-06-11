from contextlib import asynccontextmanager
from fastapi import FastAPI

from src.infrastructure.kafka.producer import KafkaProducer

kafka_producer: KafkaProducer | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    producer = KafkaProducer()
    await producer.connect()
    app.state.kafka_producer = producer
    yield
    await producer.close()
