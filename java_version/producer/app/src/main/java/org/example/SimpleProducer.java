package org.example;

import org.apache.kafka.clients.producer.*;

import java.util.Properties;

public class SimpleProducer {
    public static void main(String[] args) {
        String topicName = "test-topic";

        Properties props = new Properties();
        props.put("bootstrap.servers", "localhost:9092"); 
        props.put("key.serializer", "org.apache.kafka.common.serialization.StringSerializer");
        props.put("value.serializer", "org.apache.kafka.common.serialization.StringSerializer");

        Producer<String, String> producer = new KafkaProducer<>(props);

        System.out.println("Iniciando producer...");
        for (int i = 1; i <= 5; i++) {
            ProducerRecord<String, String> record = new ProducerRecord<>(topicName, "key" + i, "message " + i);
            producer.send(record, (metadata, exception) -> {
                if (exception == null) {
                    System.out.println("Sent: " + record.value() + " to " + metadata.topic() + " at partition " + metadata.partition());
                } else {
                    exception.printStackTrace();
                }
            });
        }

        producer.close();
    }
}
