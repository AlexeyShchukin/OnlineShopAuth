from fastapi import Depends, Request

from src.infrastructure.kafka.event_publisher import EventPublisher
from src.infrastructure.kafka.producer import KafkaProducer


def get_kafka_producer(request: Request) -> KafkaProducer:
    producer = request.app.state.kafka_producer
    if producer is None:
        raise RuntimeError("Kafka producer not initialized")
    return producer


def get_event_publisher(
    producer: KafkaProducer = Depends(get_kafka_producer)
) -> EventPublisher:
    return EventPublisher(producer)