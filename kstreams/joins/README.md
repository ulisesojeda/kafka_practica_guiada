1. Create topics
 ./bin/kafka-topics.sh --create --bootstrap-server localhost:9092 --replication-factor 1 --partitions 1 --topic users

  ./bin/kafka-topics.sh --create --bootstrap-server localhost:9092 --replication-factor 1 --partitions 1 --topic data

2. Start app

3. Proceduce data
./bin/kafka-console-producer.sh --broker-list localhost:9092 --topic users --property parse.key=true --property key.separator=:
id:user1

./bin/kafka-console-producer.sh --broker-list localhost:9092 --topic data --property parse.key=true --property key.separator=:
id:data_user1

4. Check output topic
 bin/kafka-console-consumer.sh --bootstrap-server localhost:9092 --topic join  --from-beginning

