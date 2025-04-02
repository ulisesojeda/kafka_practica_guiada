-- Non-Windowed aggregation

[2](2). Create input topic
 ./bin/kafka-topics.sh --create --bootstrap-server localhost:9092 --replication-factor 1 --partitions 1 --topic words-input

3. Run app

4. Produce words
 ./bin/kafka-console-producer.sh --broker-list localhost:9092 --topic words-input --property parse.key=true --property key.separator=:
 >id1:datos1
 >id1:de1
 >id2:datos2
 >id1:identificador1
 >id2:identificador2

 4. Consume
  bin/kafka-console-consumer.sh --bootstrap-server localhost:9092 --topic words-aggregated --from-beginning

