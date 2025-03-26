from confluent_kafka import Consumer

consumer_config = {
    'bootstrap.servers': 'localhost:9092',
    'group.id': 'my-consumer-group',
    'enable.auto.commit': True,
    'auto.offset.reset': 'earliest',
    'isolation.level': 'read_committed'  # Solo consumir transacciones completadas
}

consumer = Consumer(consumer_config)
consumer.subscribe(['topic-tx'])

try:
    while True:
        msg = consumer.poll(1.0)  # Esperar max 1 segundo por mensajes
        if msg is None:
            continue
        if msg.error():
            print(f"Error del consumidor: {msg.error()}")
            continue

        print(f"Recibido: {msg.value().decode('utf-8')}")

except KeyboardInterrupt:
    print("Deteniendo el consumidor...")
finally:
    consumer.close()
