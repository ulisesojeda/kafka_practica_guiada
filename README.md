# Práctica Guiada de Kafka

## Requisitos:

1. Docker
2. JDK 11+
3. Gradle

Nota: Para la instalación del SDK se recomienda utilizar [SDKman](https://sdkman.io/)

## Arrancar el broker de Kafka

```bash
docker run -p 9092:9092 --rm --name kafka apache/kafka:3.7.0
```

### Validar la ejecución

```bash
docker exec -it kafka bash

export PATH=$PATH:/opt/kafka/bin/
kafka-configs.sh --bootstrap-server localhost:9092 --entity-type brokers --describe
```

## Admin API

Configuración de algunas de las propiedades básicas de Kafka

Listado de todas las posibles configuraciones:

[Broker](http://kafka.apache.org/10/documentation.html#brokerconfigs)

[Topic](http://kafka.apache.org/10/documentation.html#topicconfigs)

### Settings básicos

Utilizando el script **kafka-configs** verificamos y ajustaremos algunos settings del broker.

```bash
docker exec -it kafka bash

export PATH=$PATH:/opt/kafka/bin/

kafka-configs.sh --bootstrap-server localhost:9092 --entity-type brokers --describe --all
```

### Ejercicio 1 - Administración de la configuración del clúster/broker

1. Establecer la propiedad **message.max.bytes** a 512 en el broker 1

```bash
kafka-configs.sh --bootstrap-server localhost:9092 --entity-type brokers --entity-name 1 --alter --add-config message.max.bytes=512
```

2. Establecer la propiedad **message.max.bytes** a 512 en todos los brokers

```bash
kafka-configs.sh --bootstrap-server localhost:9092 --entity-type brokers --entity-default --alter --add-config message.max.bytes=512
```

3. Comprobar el efecto del anterior cambio

```bash
kafka-configs.sh --bootstrap-server localhost:9092 --entity-type brokers --describe --all
```

4. Establecer **log.retention.hours** a 1 hora

```bash
kafka-configs.sh --bootstrap-server localhost:9092 --entity-type brokers --entity-default --alter --add-config log.retention.hours=1
```

**ERROR**: Caused by: org.apache.kafka.common.errors.InvalidRequestException: Cannot update these configs dynamically: Set(log.retention.hours)

Algunas propiedades no pueden ser cambiadas dinámicamente, se deben configurar en el fichero **server.properties** antes de ejecutar el cluster. Otras de ellas son:

- num.partitions
- cleanup.policy
- logs.dir

5. Revertir **message.max.bytes** a su valor por defecto

```bash
kafka-configs.sh --bootstrap-server localhost:9092 --entity-type brokers --entity-name 1 --alter --delete-config message.max.bytes
```

6. Configurar propiedades **NO** dinámicas

Se pueden modificar mediante el fichero **server.properties**, esta opción no es posible con **docker run** o utilizando variables de entornos (se deben definir todas)

```bash
docker run --name kafka -e KAFKA_NODE_ID=1 -e KAFKA_PROCESS_ROLES=broker,controller -e KAFKA_LISTENERS=PLAINTEXT://:9092,CONTROLLER://:9093 -e KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://localhost:9092 -e KAFKA_CONTROLLER_LISTENER_NAMES=CONTROLLER -e KAFKA_LISTENER_SECURITY_PROTOCOL_MAP=CONTROLLER:PLAINTEXT,PLAINTEXT:PLAINTEXT -e KAFKA_CONTROLLER_QUORUM_VOTERS=1@localhost:9093 -e KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR=1 -e KAFKA_TRANSACTION_STATE_LOG_REPLICATION_FACTOR=1 -e KAFKA_TRANSACTION_STATE_LOG_MIN_ISR=1 -e KAFKA_GROUP_INITIAL_REBALANCE_DELAY_MS=0 -e KAFKA_NUM_PARTITIONS=3 apache/kafka:3.7.0
```

Verificar dentro del contenedor mediante:

```bash
docker exec -it kafka bash

export PATH=$PATH:/opt/kafka/bin/
kafka-configs.sh --bootstrap-server localhost:9092 --entity-type brokers --describe --all | grep 'num.partitions'
```

### Creación y administración de topics

Para este apartado utilizaremos docker-compose con un cluster de 3 brokers y Zookeeper.

- Iniciar el cluster:

```bash
cd images
docker-compose -f docker-compose-cluster-kafka.yml up
```

```bash
docker exec -it kafka-broker-1 bash
```

- Crear topic

```bash
kafka-topics --bootstrap-server kafka1:19092 --create --topic my-topic --partitions 1 --replication-factor 3 --config max.message.bytes=64000 --config flush.messages=1
```

- replication-factor = 3. Mantener copias del topic en 3 brokers
- flush.message = 1. Copiar al disco duro cada mensaje según llega

* Listar los topics

```bash
kafka-topics --bootstrap-server kafka1:19092 --list
```

- Modificar el número de particiones

```bash
kafka-topics --bootstrap-server kafka1:19092 --alter --topic my-topic --partitions 2
```

- Verificar el número de particiones

```bash
kafka-topics --bootstrap-server kafka1:19092 --topic my-topic --describe
```

### Escritura y lectura de topics con el console-producer / console-consumer

```bash
kafka-console-producer --bootstrap-server kafka1:19092 --topic my-topic --property "parse.key=true" --property "key.separator=,"
>1,Topic
>2,Kafka
>3,Pruebas

# En otra terminal
kafka-console-consumer --bootstrap-server kafka1:19092 --topic my-topic --property print.key=true --from-beginning
```

### Ejercicio 2. Administración de topics

1. Crea un topic con 3 particiones, factor de replica 3, y que sincronice tras 5 mensajes.

```bash
kafka-topics --bootstrap-server kafka1:19092 --create --topic test-topic --partitions 3 --replication-factor 3  --config flush.messages=5
```

2. Cambia la configuración de sincronización para que esta se haga tras cada mensaje.

```bash
kafka-configs --bootstrap-server kafka1:19092 --entity-type topics --entity-name test-topic --alter --add-config flush.messages=1
```

3. Experimenta deteniendo y creando brokers

```bash
# Verifica el estado del topic (Irs: In-Sync-Replicas)

kafka-topics --bootstrap-server kafka1:19092 --topic test-topic --describe

# Se deberían ver todos los broker in-sync. Isr: 1, 2, 3

# Desde otra terminal, detener uno de los brokers

docker rm -f kafka-broker-3

# Esperar unos 20 segundos y verficar el estado del topic

kafka-topics --bootstrap-server kafka1:19092 --topic test-topic --describe

# Se deberían ver solo 2 broker in-sync. Isr: 1, 2

# Desde otra terminal, restablecer todos los brokers
cd images
docker compose -f docker-compose-cluster-kafka.yml up -d

# Verificar que todos los brokers tiene asignada una copia (Isr: 1, 2, 3)

kafka-topics --bootstrap-server kafka1:19092 --topic test-topic --describe
```

4. Topic con **cleanup.policy=compact**

```bash
kafka-topics --bootstrap-server kafka1:19092 --create --topic compact-topic --config cleanup.policy=compact

# Establecer el tiempo máximo antes de compactar a 1 minuto (mantener la última entrada de cada key)
kafka-configs --bootstrap-server kafka1:19092 --entity-type topics --entity-name compact-topic --alter --add-config max.compaction.lag.ms=6000

# Producir algunos eventos
kafka-console-producer --bootstrap-server kafka1:19092 --topic compact-topic --property "parse.key=true" --property "key.separator=,"

> 1,AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
> 2,AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
> 1,BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB
> 2,BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB
> 1,CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC
> 2,CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC

```

Validar en el consumidor despues de 1 minuto. Introducir más valores con la misma key para resultados más visibles

```bash
kafka-console-consumer --bootstrap-server kafka1:19092 --topic compact-topic --property print.key=true --from-beginning
```

## Producer / Consumer API

### Console producer y consumer

Primero crear un topic **console-example** con 3 particiones y factor de réplica 3.

```bash
kafka-topics --bootstrap-server kafka1:19092 --create --topic console-example --partitions 3 --replication-factor 3
```

Produciremos varios mensajes en el topic mediante el comando kafka-console-producer y observaremos el comportamiento:

El mensaje a producir será uno simple que solo contendrá un id como body:

```bash
1,{"id": "1"}
```

```bash
kafka-console-producer --bootstrap-server kafka1:19092 --topic console-example --property "parse.key=true" --property "key.separator=,"
```

Ahora crearemos un consumidor de consola en otra terminal dentro del contenedor:

```bash
kafka-console-consumer --bootstrap-server kafka1:19092 --topic console-example --property print.key=true --from-beginning
```

¿Qué pasa cuándo este arranca?

<details>
  <summary><b>Solución</b></summary>

El consumidor consume todos los mensajes

</details>

¿Qué pasará si añadimos otro consumidor?

<details>
  <summary><b>Solución</b></summary>

Tenemos dos consumidores consumiendo exactamente los mismos mensajes.

</details>

### Ahora introduciremos dos consumidores formando un grupo de consumo:

Ejecutar el siguiente comando en 2 consolas diferentes

```bash
kafka-console-consumer --bootstrap-server kafka1:19092 --topic console-example --property print.key=true --from-beginning  --consumer-property group.id=console-group-1
```

Produce el siguiente evento:

```bash
2,{"id":"2"}
```

Observad el rebalanceo y particionado que se produce mediante la partition key elegida. ¿Qué casos de uso encontramos para esta funcionalidad?

Validamos lo observado en la descripción del consumer group:

```bash
kafka-consumer-groups --bootstrap-server kafka1:19092 --group console-group-1 --describe
```

## Python Producer/Consumer

### Notas: consultar el Anexo 1 para ejecutar los ejemplos de Python y Java desde un container

Preparación para ejecución local:

```bash
# Crear y activar Python virtual environment
# Si se ejecutan los scripts desde el contenedor, este paso no es necesario

cd python_version
pip install virtualenv
python3 -m virtualenv venv
source venv/bin/activate
pip install kafka-python
```

1. Crear topic con 3 particiones

```bash
kafka-topics --bootstrap-server kafka1:19092 --create --topic simple-topic --partitions 3
```

2. Ejecutar el productor
   **Modificar el bootstrap-server con la opción comentada "localhost" si se ejecuta fuera del contenedor**

```bash
python3 producer.py
```

3. Ejecutar el consumidor
   **Modificar el bootstrap-server con la opción comentada "localhost" si se ejecuta fuera del contenedor**

```bash
python3 consumer.py
```

4. Ejecutar el consumidor nuevamente. Qué sucede y porqué ?
   <details>
   <summary><b>Solución</b></summary>

   No se consumen más mensajes. Porque el offset del consumer group se encuentra al final del topic, pues todos los mensajes ya han sido previamente consumidos

   </details>

5. Resetear el offset del consumer group para volver a ingestar todos los mensajes.

   Este procedimiento es útil cuando se cambia la lógica del consumidor y necesitamos reproducir todos los mensajes.
   También es posible volver a consumir desde un offset específico.

   - Cerrar el consumidor en caso de estar ejecutándose, en caso contrario no podremos resetear el offset
   - Ejecutamos el siguiente comando desde un broker

   ```bash
   kafka-consumer-groups --bootstrap-server kafka1:19092  --topic simple-topic --reset-offsets --to-earliest --group py-group --execute
   ```

   - Ejecutamos el consumidor nuevamente para consumir todos los mensajes nuevamente

6. Repetir el anterior procedimiento para consumir sólo desde el 4to mensaje

```bash
kafka-consumer-groups --bootstrap-server kafka1:19092  --topic simple-topic --reset-offsets --to-offset 4 --group py-group --execute
```

7. Paralelizar el consumo de mensajes mediante varios consumidores pertenecientes al mismo consumer-group
   . Eliminar el topic simple-topic
   ```bash
   kafka-topics --bootstrap-server kafka1:19092  --topic simple-topic --delete
   ```
   . Crear el topic con 2 particiones
   ```bash
   kafka-topics --bootstrap-server kafka1:19092 --create --topic simple-topic --partitions 2
   ```
   . Ejecutar 2 consumidores en terminales distintas
   . Ejecutar el productor varias veces y verificar que lleguen diferentes mensajes alos consumidores

Para solucionar posibles errores:

```bash
# Eliminar el topic

kafka-topics --bootstrap-server kafka1:19092 --topic simple-topic --delete

# Eliminar el consumer group

kafka-consumer-groups --bootstrap-server kafka1:19092 --group py-group --delete

# Verificar los offsets

kafka-consumer-groups --bootstrap-server kafka1:19092 --group py-group --describe
```

Nota: el máximo nivel de paralelismo lo define el número de particiones del topic. El consumer-group asignará un único consumidor por partición, los restantes consumidores permanecerán en stand-by hasta que alguno de los anterior falle.

## Java API Producer/Consumer

1. Ejecutar el productor

```bash
cd java_version/producer
# Linux o MacOS
./gradlew build
./gradlew run
# Windows
gradlew.bat build
gradlew.bat run
```

2. Ejecutar el consumidor

```bash
cd java_version/consumer
# Linux o MacOS
./gradlew build
./gradlew run
# Windows
gradlew.bat build
gradlew.bat run
```

## Transacciones (Exactly Once Semantics)

1. Instalar librería confluent_kafka

```bash
pip install confluent_kafka
```

2. Ejecutar el productor
   **Modificar el bootstrap-server con la opción comentada "localhost" si se ejecuta fuera del contenedor**

```bash
python3 producer_tx.py
```

3. Ejecutar el consumidor
   **Modificar el bootstrap-server con la opción comentada "localhost" si se ejecuta fuera del contenedor**

```bash
python3 consumer_tx.py
```

## Kafka Connect

Connect es una herramienta que nos permite ingestar desde y hacia sistemas de persistencia externos (incluidos topics de kafka) usando workers (maquinas tanto en modo stand alone como distribuido) donde tendremos instalado el core de Connect (normalmente una instalación común de kafka nos valdría) usando para ello una serie de plugins (connectors).

Como cualquier otra API construida "on top" of producer/consumer utiliza la propia infraestructura de Kafka para asegurarnos la persistencia, semánticas de entrega (es capaz de asegurar semántica exactly once, dependiendo del conector).

Mas info sobre como levantar connect e instalar plugin [aquí](https://docs.confluent.io/platform/current/connect/userguide.html)

Además connect nos provee de un [API REST](https://docs.confluent.io/platform/current/connect/references/restapi.html) para poder interactuar de manera amigable.

Además existe un [Hub](https://www.confluent.io/hub/) donde podremos buscar y descargar los connectors oficiales y no oficiales que necesitemos.

Para este apartado utilizaremos el docker compose de Confluent

```bash
docker-compose -f docker-compose-confluent.yml up

```

### Conector de ficheros - FileStream

**FileStreamSource**: lee el contenido de un fichero línea a línea y lo almacena en un topic.
En este ejemplo vamos a copiar el contenido del fichero **/etc/passwd** hacia el topic **file.content**

0. Listar los conectores (plugins) disponibles

```bash
curl -X GET http://localhost:8083/connector-plugins | jq
```

Útil para debugging de error durante la creación de los conectores. Si no aparece el conector deseado, debemos asegurarnos que su **jar** asociado está en algunas de los paths listados en **plugin.path** (En el docker-compose se define mediante la variable de entorno **CONNECT_PLUGIN_PATH**)

1. Creamos el conector mediante una llamada a la API

```bash
cd connect
curl -d @"file_source.json" -H "Content-Type: application/json" -X POST http://localhost:8083/connectors
```

Si no tenemos **curl** lo podemos hacer desde uno de los containers:

```bash
cd connect
docker cp file_source.json broker:/home/appuser
docker exec -it broker bash
curl -d @"file_source.json" -H "Content-Type: application/json" -X POST http://connect:8083/connectors
```

2. Verificar que se ha creado el conector

```bash
curl -X GET http://localhost:8083/connectors
# curl -X GET http://connect:8083/connectors # Desde un container
```

3. Leer del topic

```bash
docker exec -it broker bash
kafka-topics --bootstrap-server localhost:9092 --list  # Verificar que existe el topic file.content
 kafka-console-consumer --bootstrap-server localhost:9092 --topic file.content --from-beginning
```

4. Ver el estado del conector. Útil para detección de errores

```bash
curl -X GET http://localhost:8083/connectors/local-file-source/status
```

5. Ver los topics asociados

```bash
curl -X GET http://localhost:8083/connectors/local-file-source/topics
```

6. Ver los offsets actuales

```bash
curl -X GET http://localhost:8083/connectors/local-file-source/offsets
```

7. Eliminar el conector

```bash
curl -X DELETE http://localhost:8083/connectors/local-file-source
```

### FileSinkConnector

Crearemos un conector que almacena todo los eventos (correctos) en un fichero y los inválidos en un topic (dlq-file-sink-topic)

1. Creamos el conector mediante una llamada a la API

```bash
cd connect
curl -d @"file_sink.json" -H "Content-Type: application/json" -X POST http://localhost:8083/connectors
```

2. Verificamos el estado del conector

```bash
curl -X GET http://localhost:8083/connectors/local-file-sink/status
```

3. Accedemos al contenedor de Connect y publicamos eventos en el topic **test-topic**

```bash
docker exec -it connect bash
kafka-console-producer --bootstrap-server broker:29092 --topic test-topic --property "parse.key=true" --property "key.separator=,"
>1,{"id": 1}
>2,{"name": "delta"}
>3,NO_ES_UN_JSON
Control+C
```

4. Validamos que los eventos válidos (JSON) se añaden al fichero definido en el conector

```bash
# Desde el contenedor de Connect
cat /tmp/output.txt
```

5. Y que los inválidos son enviados al DLQ

```bash
kafka-console-consumer --bootstrap-server broker:29092 --topic dlq-file-sink-topic --from-beginning
```

6. Eliminamos el conector

```bash
curl -X DELETE http://localhost:8083/connectors/local-file-sink
```

### Ejercicio de conectores:

Definir 2 conectores que sincronicen los ficheros **/tmp/source.txt** y **/tmp/destination.txt**

### Kafka standalone con Connect/Debezium

Los conectores están definidos dentro del Dockerfile **images/docker-connect-debezium.yml** por simplicidad.

1. Desplegar contenedores con Postgres y Kafka

```bash
cd images
docker-compose  -f docker-compose-postgres-debezium.yml up
```

2. Acceder a la instancia de Posgres mediante DBeaver, DataGrip, psql, etc

**Usuario**: postgres

**Contraseña**: root

3. Crear la tabla a replicar

```sql
   CREATE TABLE postgres.public.orders (
   id int4 NOT NULL,
   "name" varchar NULL,
   CONSTRAINT orders_pk PRIMARY KEY (id)
   );
```

4. Create la base de datos donde se almacenará la réplica

```sql
create database cdc;
```

5. Añadir filas a la tabla **postgres.public.orders**

6. Verificar que las filas se sincronizan en **cdc.public.table_public_orders**

### Ejercicio Kafka Connect:

Modificar los conectores para sincronizar además la tabla **products**

## Schema registry

Kafka Schema Registry es un servicio que gestiona y almacena los esquemas de datos utilizados en Kafka, asegurando la compatibilidad entre productores y consumidores.

¿Para qué sirve?

- Estandariza la estructura de los datos enviados a Kafka.
- Evita errores al cambiar la estructura del mensaje.
- Reduce el tamaño de los mensajes, ya que solo se envía el ID del esquema y no todo el esquema.
- Permite compatibilidad entre versiones de esquemas (Backward, Forward, Full).

![Schema-Registry](https://docs.confluent.io/platform/current/_images/schema-registry-ecosystem.jpg)

Ejemplo de flujo con Schema Registry:

- El productor consulta el Schema Registry y obtiene el ID del esquema.
- Kafka envía solo los datos y el ID del esquema, reduciendo el tamaño del mensaje.
- El consumidor consulta el Schema Registry y decodifica el mensaje correctamente.

### Ejemplo de Productor/Consumidor con Schema Registry

1. Ejecutar el productor

```bash
cd python_version
python3 producer_schema_registry.py
```

2. Forzar backward compatibility

```bash
 curl -X PUT http://localhost:8081/config/users-value --header "Content-Type: application/json" --data '{"compatibility": "BACKWARD"}'
 # Si se ejecuta desde el contenedor
 curl -X PUT http://schema-registry:8081/config/users-value --header "Content-Type: application/json" --data '{"compatibility": "BACKWARD"}'
```

3. Ejecutar el consumidor

```bash
cd python_version
python3 consumer_schema_registry.py
```

4. Ejecutar el productor que introduce un cambio de schema

```bash
cd python_version
python3 producer2_schema_registry.py
```

Verificar el error de backward compatibility

## Streams API

## KSQL

## Anexo 1: Ejecución de los ejemplos desde un contenedor

```bash
docker exec -it runner bash
```

## Anexo 2: Solucionar problemas con la ejecución de contenedores

```bash
docker system prune
```
