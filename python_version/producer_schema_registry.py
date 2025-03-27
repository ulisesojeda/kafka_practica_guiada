from confluent_kafka import SerializingProducer
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroSerializer
import json

# Kafka & Schema Registry Configuration
#KAFKA_BROKER = "localhost:9092"
KAFKA_BROKER = "broker:29092"

#SCHEMA_REGISTRY_URL = "http://localhost:8081"
SCHEMA_REGISTRY_URL = "http://schema-registry:8081"
TOPIC = "users"

# Define Avro Schema
USER_SCHEMA_STR = """
{
  "type": "record",
  "name": "User",
  "fields": [
    {"name": "id", "type": "int"},
    {"name": "name", "type": "string"},
    {"name": "email", "type": ["null", "string"], "default": null}
  ]
}
"""

# Initialize Schema Registry Client
schema_registry_client = SchemaRegistryClient({"url": SCHEMA_REGISTRY_URL})

# Avro Serializer
avro_serializer = AvroSerializer(schema_registry_client, USER_SCHEMA_STR)

# Kafka Producer Configuration
producer_config = {
    "bootstrap.servers": KAFKA_BROKER,
    "value.serializer": avro_serializer,  # Use Avro Serializer
}

producer = SerializingProducer(producer_config)


# Function to send a message
def send_message(user):
    try:
        producer.produce(
            topic=TOPIC,
            key=str(user["id"]).encode("utf-8"),
            value=user
        )
        producer.flush()  # Ensure the message is sent
        print(f"Produced: {user}")
    except Exception as e:
        print(f"Error producing message: {e}")


# Sample User Data
users = [
    {"id": 1, "name": "Alice", "email": "alice@example.com"},
    {"id": 2, "name": "Bob", "email": None},
    {"id": 3, "name": "Bobby", "email": None},
]

for user in users:
    send_message(user)
