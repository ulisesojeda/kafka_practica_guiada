from confluent_kafka import DeserializingConsumer
from confluent_kafka.schema_registry.avro import AvroDeserializer
from confluent_kafka.schema_registry import SchemaRegistryClient

KAFKA_BROKER = "localhost:9092"
SCHEMA_REGISTRY_URL = "http://localhost:8081"
TOPIC = "users"

schema_registry_client = SchemaRegistryClient({"url": SCHEMA_REGISTRY_URL})

avro_deserializer = AvroDeserializer(schema_registry_client)

consumer_config = {
    "bootstrap.servers": KAFKA_BROKER,
    "group.id": "user-consumer-group",
    "auto.offset.reset": "earliest",
    "value.deserializer": avro_deserializer
}

consumer = DeserializingConsumer(consumer_config)
consumer.subscribe([TOPIC])

print("Esperando mensajes...")
while True:
    msg = consumer.poll(1.0)
    if msg is None:
        continue
    if msg.error():
        print(f"Consumer error: {msg.error()}")
        continue
    print(f"Consumed message: {msg.value()}")
