from kafka import KafkaProducer
from kafka.partitioner.default import DefaultPartitioner

class CustomPartitioner(DefaultPartitioner):
    def __call__(self, key, all_partitions, available_partitions):
        if key is not None:
            if int(key) % 2 == 0:
                partition = 0
            else:
                partition = 1
            #partition = int(key) % len(all_partitions)
            return partition
        return super().__call__(key, all_partitions, available_partitions)  # Por defecto

producer = KafkaProducer(
    bootstrap_servers="kafka1:19092",
    key_serializer=lambda k: str(k).encode() if k is not None else None,
    value_serializer=lambda v: str(v).encode(),
    partitioner=CustomPartitioner()
)

topic_name = "simple-topic"

for i in range(10):
    key = str(i)
    value = f"Mensaje {i}"
    producer.send(topic_name, key=key, value=value).add_callback(
        lambda metadata: print(f"Enviado a particion {metadata.partition}, offset {metadata.offset}")
    )

producer.flush()
producer.close()
