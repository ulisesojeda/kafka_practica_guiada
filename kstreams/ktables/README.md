1. Create topic ktable-input

 ./bin/kafka-topics.sh --create --bootstrap-server localhost:9092 --replication-factor 1 --partitions 1 --topic ktable-input


2. Run app ./run.sh

3. Produce events
 ./bin/kafka-console-producer.sh --broker-list localhost:9092 --topic ktable-input --property parse.key=true --property key.separator=:

>delta:orderNumber-111111
>id1:orderNumber-2000
