import json
import logging
import random

from kafka import KafkaProducer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# Creamos nuestro Kafka Producer pasandole TODOS los Broker
# Utilizaremos la libreria JSON para serializar nuestros mensajes
producer = KafkaProducer(
    bootstrap_servers=["kafka1:19092", "kafka2:19093", "kafka3:19094"],
    #bootstrap_servers=["127.0.0.1:9092", "127.0.0.1:9093", "127.0.0.1:9094"],
    value_serializer=lambda m: json.dumps(m).encode("utf-8"),
)


def on_send_success(meta):
    logging.info(
        f"Topic: {meta.topic}. Partition: {meta.partition}. Offset: {meta.offset}"
    )


def on_send_error(ex):
    logging.error("Error", exc_info=ex)


# producimos 10 mensajes
for i in range(10):
    key = str(i)
    if .....:  # Si la key convertida a entero es par seleccionamos topic "pares", sino topic "impares"
        ....
    else:
        ....

    producer.send(
        topic,
        key=key.encode("utf-8"),
        value={"msg": str(i)}
    ).add_callback(on_send_success).add_errback(on_send_error)

producer.flush()
