1. Create input topic
./bin/kafka-topics.sh --create \
          --bootstrap-server localhost:9092 \
          --replication-factor 1 \
          --partitions 1 \
          --topic basic-streams-input

2. Run app
./run.sh

3. Run console producer
./bin/kafka-console-producer.sh --broker-list localhost:9092 --topic basic-streams-input


4. Run console consumer
bin/kafka-console-consumer.sh --bootstrap-server localhost:9092 \
    --topic basic-streams-output \
    --from-beginning \
    --property print.key=true \
    --property print.value=true \
    --property key.deserializer=org.apache.kafka.common.serialization.StringDeserializer \
    --property value.deserializer=org.apache.kafka.common.serialization.StringDeserializer

5. Input into producer
>orderNumber-2000
>no_output
>orderNumber-3000
>orderNumber-1000
>orderNumber-5000
