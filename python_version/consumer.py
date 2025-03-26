import json
import logging

from kafka import KafkaConsumer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

consumer = KafkaConsumer(
    "simple-topic",
    group_id="py-group",
    bootstrap_servers=["127.0.0.1:9092", "127.0.0.1:9093", "127.0.0.1:9094"],
    auto_offset_reset="earliest",
)

consumer.subscribe(["simple-topic"])

for message in consumer:
    logging.info(
        f"Topic: {message.topic} - Partition: {message.partition} - Offset: {message.offset} - Key: {message.key.decode('utf-8')} - Value: {message.value.decode('utf-8')}"
    )
