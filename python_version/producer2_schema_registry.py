from confluent_kafka import SerializingProducer
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroSerializer
import json

#KAFKA_BROKER = "localhost:9092"
KAFKA_BROKER = "broker:29092"

#SCHEMA_REGISTRY_URL = "http://localhost:8081"
SCHEMA_REGISTRY_URL = "http://schema-registry:8081"
TOPIC = "users"

# Aplicamos un cambio que no es backward compatible. Se renombra name a full_name
USER_SCHEMA_STR = """
{
  "type": "record",
  "name": "User",
  "fields": [
    {"name": "id", "type": "int"},
    {"name": "full_name", "type": "string"},
    {"name": "email", "type": ["null", "string"], "default": null}
  ]
}
"""

schema_registry_client = SchemaRegistryClient({"url": SCHEMA_REGISTRY_URL})

avro_serializer = AvroSerializer(schema_registry_client, USER_SCHEMA_STR)

producer_config = {
    "bootstrap.servers": KAFKA_BROKER,
    "value.serializer": avro_serializer,
}

producer = SerializingProducer(producer_config)


def send_message(user):
    try:
        producer.produce(
            topic=TOPIC,
            key=str(user["id"]).encode("utf-8"),
            value=user
        )
        producer.flush()
        print(f"Produced: {user}")
    except Exception as e:
        print(f"Error producing message: {e}")


users = [
    {"id": 4, "full_name": "Bobby", "email": None},
]

for user in users:
    send_message(user)
