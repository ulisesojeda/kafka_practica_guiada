from confluent_kafka import Producer

producer_config = {
    #'bootstrap.servers': 'localhost:9092',
    'bootstrap.servers': 'kafka1:19092',
    'transactional.id': 'my-transactional-producer',
    'enable.idempotence': True,  # exactly-once semantics. Equivalente a ENABLE_IDEMPOTENCE_CONFIG = True en Java
    'acks': 'all',  # ACKS_CONFIG = ALL
}


producer = Producer(producer_config)

producer.init_transactions()

try:
    producer.begin_transaction()

    producer.produce('topic-tx', key='key1', value='Mensaje con error de transaccion')
    producer.produce('topic-tx2', key='key2', value='Message 2') # Podemos enviar mensajes a diferentes topic dentro de la misma transacción
    producer.flush()

    raise Exception("Error simulado en la transacción")

    producer.commit_transaction()
    print("Transaction committed successfully!")

except Exception as e:
    print(f"Transaction failed: {e}")
    producer.abort_transaction()
    print("Transaction aborted.")
