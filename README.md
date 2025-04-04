# Práctica Guiada de Kafka

## Requisitos:

1. Docker
2. docker-compose
3. Python
4. Java JDK 11+
5. Gradle

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

```bash
docker-compose -f docker-compose-cluster-kafka.yml up
```

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

### Nota: consultar el Anexo 1 para ejecutar los ejemplos de Python y Java desde un container

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

1. Crear topic con 1 partición

```bash
docker exec -it kafka-broker-1 bash

kafka-topics --bootstrap-server kafka1:19092 --create --topic simple-topic --partitions 1
```

2. Ejecutar el productor

   **Modificar el bootstrap-server con la opción comentada "localhost" si se ejecuta fuera del contenedor**

```bash
cd python_version
python3 producer.py
```

3. Ejecutar el consumidor

   **Modificar el bootstrap-server con la opción comentada "localhost" si se ejecuta fuera del contenedor**

```bash
cd python_version
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

   . Ejecutar el productor y enviar mensajes con diferentes keys. Verificar que lleguen diferentes mensajes a los consumidores

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

## Particionador customizado

1. Creamos un topic con 2 particiones

```bash
kafka-topics --bootstrap-server kafka1:19092 --topic simple-topic --delete
kafka-topics --bootstrap-server kafka1:19092 --create --topic simple-topic --partitions 2
```

2. Ejecutamos el Productor

```bash
python3 custom_partitioner.py
```

3. Leemos de la partición 0 y vetificamos que llegan mensajes con valores pares

```bash
kafka-console-consumer --bootstrap-server kafka1:19092 --topic simple-topic --property print.key=true --from-beginning --partition 0
```

4. Leemos de la partición 1 y vetificamos que llegan mensajes con valores impares

```bash
kafka-console-consumer --bootstrap-server kafka1:19092 --topic simple-topic --property print.key=true --from-beginning --partition 1
```

## Ejercicio productor con varios topics

Completar y ejecutar el script **python_version/ejercicio_producer.py**

## Java API Producer/Consumer

### Nota: consultar el Anexo 1 para ejecutar los ejemplos de Python y Java desde un container

0. En caso de ejecución desde el contenedor

```bash
docker exec -it runner bash
```

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

0. En caso de ejecución desde el contenedor

```bash
docker exec -it runner bash
```

1. Instalar librería confluent_kafka

```bash
pip install confluent_kafka  # No es necesario desde el contenedor
```

2. Ejecutar el productor

   **Modificar el bootstrap-server con la opción comentada "localhost" si se ejecuta fuera del contenedor**

```bash
cd python_version
python3 producer_tx.py
```

3. Ejecutar el consumidor

   **Modificar el bootstrap-server con la opción comentada "localhost" si se ejecuta fuera del contenedor**

```bash
cd python_version
python3 consumer_tx.py
```

4. Validar que el consumidor sólo consume mensajes commited

- Ejecutar un console-consumer

```bash
kafka-console-consumer --bootstrap-server kafka2:19093 --topic topic-tx --from-beginning
```

- Lanzar el consumidor de Transacciones

```bash
python3 consumer_tx.py
```

- Ejecutor el productor con una transacción fallida

```bash
python3 producer_tx_error.py
```

- Verificar que el mensaje es recibido en el console-consumer pero no en el Python consumer

## Kafka Connect

Connect es una herramienta que nos permite ingestar desde y hacia sistemas de persistencia externos (incluidos topics de kafka) usando workers (máquinas tanto en modo standalone como distribuido) donde tendremos instalado el core de Connect (normalmente una instalación común de Kafka nos valdría) usando para ello una serie de plugins (connectors).

Como cualquier otra API construida "on top" of producer/consumer utiliza la propia infraestructura de Kafka para asegurarnos la persistencia, semánticas de entrega (es capaz de asegurar semántica exactly once, dependiendo del conector).

Mas info sobre como levantar Connect e instalar plugins [aquí](https://docs.confluent.io/platform/current/connect/userguide.html)

Además connect nos provee de un [API REST](https://docs.confluent.io/platform/current/connect/references/restapi.html) para poder interactuar de manera amigable.

Existe un [Hub](https://www.confluent.io/hub/) donde podremos buscar y descargar los connectors oficiales y no oficiales que necesitemos.

**Nota**: Para este apartado utilizaremos el docker compose de Confluent

```bash
docker-compose -f docker-compose-confluent.yml up

```

### Conector de ficheros - FileStream

**FileStreamSource**: para leer el contenido de un fichero línea a línea y almacenarlo en un topic.

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
# Desde un container
curl -X GET http://connect:8083/connectors
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

Desde un container:

```bash
cd connect
docker cp file_source.json broker:/home/appuser
docker exec -it broker bash
curl -d @"file_sink.json" -H "Content-Type: application/json" -X POST http://connect:8083/connectors
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
docke exec -it connect bash

cat /tmp/output.txt
```

5. Y que los erróneos son enviados al DLQ

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

Acceso mediante contenedor

```bash
docker exec -it postgres bash
psql -h localhost -U postgres -d postgres
```

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

```bash
insert into public.orders values (1, 'Buy_Phone');
insert into public.orders values (2, 'Sell_PC');
```

6. Verificar que las filas se sincronizan en **cdc.public.table_public_orders**

```bash
psql -h localhost -U postgres -d cdc; # \c cdc; -- también hace el cambio de DB

select * from cdc.public.table_public_orders;
```

### Ejercicio Kafka Connect:

Modificar los conectores para sincronizar además la tabla **products**

1. Detener los contenedores (Control + C)
2. En el fichero **images/docker-connect-debezium.yml** modifica:

   - **table.include.list** del connector **postgres-source-connector**

   - **topics** del connector **postgres-sink-connector**

3. Construir nuevamente la imagen

```bash
docker-compose  -f docker-compose-postgres-debezium.yml build
```

4. Ejecutar los contenedores

```bash
docker-compose  -f docker-compose-postgres-debezium.yml up
```

5. Crear tabla de productos

```bash
docker exec -it postgres bash
psql -h localhost -U postgres -d postgres
```

```sql
   CREATE TABLE postgres.public.products (
   id int4 NOT NULL,
   "product_name" varchar NULL,
   CONSTRAINT products_pk PRIMARY KEY (id)
   );
```

6. Añadir filas a la tabla **postgres.public.products**

```bash
insert into public.products values (1, 'Phone');
insert into public.products values (2, 'PC');
```

7. Verificar que las filas se sincronizan en **cdc.public.table_public_products**

```bash
psql -h localhost -U postgres -d cdc

select * from cdc.public.table_public_products;
```

### Reiniciar la ingesta de una tabla desde el inicio.

Útil durante cambios de schema de las fuentes de datos o cambios en la ETL, etc

- Procedimiento:
  - Eliminar el source connector
  - Eliminar el topic al que source connector envía eventos
  - Borrar todos los datos en las tablas a re-ingestar
  - Recrear el source connector

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
- El productor envía solo los datos y el ID del esquema, reduciendo el tamaño del mensaje.
- El consumidor consulta el Schema Registry y decodifica el mensaje correctamente.

### Ejemplo de Productor/Consumidor con Schema Registry

```bash
docker-compose -f docker-compose-confluent.yml up
```

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

Para estos ejercicios utlizaremos el docker-compose **docker-compose-cluster-kafka** y ejecutaremos los ejemplos desde el **runner**

```bash
docker compose -f docker-compose-cluster-kafka.yml build
docker compose -f docker-compose-cluster-kafka.yml run
```

### Quix Streams

Kafka Streams sólo tiene API para Java/Scala. Sin embargo, existen aplicaciones que intentan replicar su funcionamiento en otros lenguajes.

Quix-Streams es una aproximación de Kafka Streams en Python y lo utilizaremos como soporte para explicar algunos conceptos de Streams desde Python

1. Instalamos la librería

```bash
pip install quixstreams
```

2. Ejecutamos el productor

```bash
cd quix-streams
python3 producer.py
```

2. Ejecutamos el consumidor

```bash
cd quix-streams
python3 consumer.py
```

### 1. Contar palabras

1. Accedemos al contenedor del broker

```bash
docker exec -it kafka1 bash
```

2. Creamos el topic de entrada

```bash
kafka-topics --create --bootstrap-server kafka1:19092 --replication-factor 1 --partitions 1 --topic streams-plaintext-input
```

3. Ejecutamos el productor

```bash
kafka-console-producer --broker-list kafka1:19092 --topic streams-plaintext-input
```

3. Ejecutamos el consumidor en el topic de salida

```bash
kafka-console-consumer --bootstrap-server kafka1:19092 \
    --topic streams-wordcount-output \
    --from-beginning \
    --property print.key=true \
    --property print.value=true \
    --property key.deserializer=org.apache.kafka.common.serialization.StringDeserializer \
    --property value.deserializer=org.apache.kafka.common.serialization.LongDeserializer
```

4. Ejecutar la aplicación

```bash
docker exec -it runner bash

cd kstreams/wordcount
./gradlew build
./gradlew run
```

5. Introducimos texto en el productor con algunas palabras repetidas y verificamos el resultado en el topic de salida.

### 2. Filter-Map

Aplicación que filtra (envía al topic de salida) los eventos con un identificador mayor que 1000.

1. Accedemos al contenedor del broker

```bash
docker exec -it kafka1 bash
```

2. Crear el topic de entrada

```bash
kafka-topics --create \
          --bootstrap-server kafka1:19092 \
          --replication-factor 1 \
          --partitions 1 \
          --topic basic-streams-input
```

2. Ejecutar la aplicación

```bash
docker exec -it runner bash

cd kstreams/filter_map
./gradlew build
./gradlew run
```

3. Ejecutar el productor

```bash
kafka-console-producer --broker-list kafka1:19092 --topic basic-streams-input
```

4. Ejecutar el consumidor

```bash
   kafka-console-consumer --bootstrap-server kafka1:19092 \
    --topic basic-streams-output \
    --from-beginning \
    --property print.key=true \
    --property print.value=true \
    --property key.deserializer=org.apache.kafka.common.serialization.StringDeserializer \
    --property value.deserializer=org.apache.kafka.common.serialization.StringDeserializer
```

5. Introducir en productor

```bash
> orderNumber-2000
> no_output
> orderNumber-3000
> orderNumber-1000
> orderNumber-5000
```

6. Verificar en el consumidor que sólo los valores > 1000 son producidos

### 3. Agregaciones sin ventana temporal

1. Accedemos al contenedor del broker

```bash
docker exec -it kafka1 bash
```

2. Crear topic de entrada

```bash
kafka-topics --create --bootstrap-server kafka1:19092 --replication-factor 1 --partitions 1 --topic words-input
```

3. Ejecutar la aplicación

```bash
docker exec -it runner bash

cd kstreams/rolling-aggregate
./gradlew build
./gradlew run
```

4. Producir eventos

```bash
kafka-console-producer --broker-list kafka1:19092 --topic words-input --property parse.key=true --property key.separator=:

> id1:datos1
> id2:datos2
> id1:identificador1
> id2:identificador2
```

5. Verificar con el consumidor

```bash
kafka-console-consumer --bootstrap-server kafka1:19092 --topic words-aggregated --from-beginning
```

### 4. Agregaciones con ventana temporal

Se agrupan los eventos con igual key dentro de una ventana temporal de 1 minuto

1. Accedemos al contenedor del broker

```bash
docker exec -it kafka1 bash
```

2. Crear topic de entrada

```bash
kafka-topics --create --bootstrap-server kafka1:19092 --replication-factor 1 --partitions 1 --topic words-input
```

3. Ejecutar la aplicación

```bash
docker exec -it runner bash

cd kstreams/windowed-aggregate
./gradlew build
./gradlew run
```

4. Producir eventos

```bash
   kafka-console-producer --broker-list kafka1:19092 --topic words-input --property parse.key=true --property key.separator=:

> id1:evento_1
> id1:kafka_1
> id2:event_2
> id1:apache_1
> id2:kafka_2
```

5. Verificar en el consumidor

```bash
   kafka-console-consumer --bootstrap-server kafka1:19092 --topic words-aggregated --from-beginning
```

### 5. Joins

Ejemplo de JOIN de 2 KStreams de forma similar a un join de dos tablas relacionales. La principal diferencia es que los KStreams tiene que tener la misma key para hacer efectivo el JOIN.

```sql
SELECT u.*, d.* FROM users s JOIN details d ON u.id = d.user_id
```

1. Accedemos al contenedor del broker

```bash
docker exec -it kafka1 bash
```

2. Creator topics

```bash
kafka-topics --create --bootstrap-server kafka1:19092 --replication-factor 1 --partitions 1 --topic users

kafka-topics --create --bootstrap-server kafka1:19092 --replication-factor 1 --partitions 1 --topic data
```

3. Ejecutar la aplicación

```bash
docker exec -it runner bash

cd kstreams/joins
./gradlew build
./gradlew run
```

3. Producir eventos en ambos topic.
   **Importante**: los eventos deben tener el mismo key

```bash
kafka-console-producer --broker-list kafka1:19092 --topic users --property parse.key=true --property key.separator=:
id:user1
```

```bash
kafka-console-producer --broker-list kafka1:19092 --topic data --property parse.key=true --property key.separator=:
id:data_user1
```

4. Verificar el topic de salida

```bash
kafka-console-consumer --bootstrap-server kafka1:19092 --topic join  --from-beginning
```

## KSQL

Para este apartado utilizaremos el docker-compose **docker-compose-confluent**

1. Detenemos cualquier contenedor que tengamos en ejecución

2. Ejecutamos el docker-compose

```bash
docker-compose -f docker-compose-confluent.yml build
docker-compose -f docker-compose-confluent.yml up
```

3. Accedemos a la consola de ksqlDB

```bash
docker exec -it ksqldb-cli ksql http://ksqldb-server:8088
```

4. Establecemos el offset a earliest para todos los streams

```sql
SET 'auto.offset.reset' = 'earliest';
```

### 1. Filtrado

Creamos el stream **orders**

```sql
CREATE stream orders (id INTEGER KEY, item VARCHAR, address STRUCT <
city  VARCHAR, state VARCHAR >)
WITH (KAFKA_TOPIC='orders', VALUE_FORMAT='json', partitions=1);
```

Insertamos datos en el stream

```sql
INSERT INTO orders(id, item, address)
VALUES(140, 'Mauve Widget', STRUCT(city:='Ithaca', state:='NY'));
INSERT INTO orders(id, item, address)
VALUES(141, 'Teal Widget', STRUCT(city:='Dallas', state:='TX'));
INSERT INTO orders(id, item, address)
VALUES(142, 'Violet Widget', STRUCT(city:='Pasadena', state:='CA'));
INSERT INTO orders(id, item, address)
VALUES(143, 'Purple Widget', STRUCT(city:='Yonkers', state:='NY'));
INSERT INTO orders(id, item, address)
VALUES(144, 'Tan Widget', STRUCT(city:='Amarillo', state:='TX'));
```

Creamos un stream con datos filtrados

```sql
CREATE STREAM ny_orders AS SELECT * FROM ORDERS WHERE ADDRESS->STATE='NY' EMIT CHANGES;
```

Validamos el filtrado

```sql
SELECT * FROM ny_orders EMIT CHANGES;
```

### 2. Búsquedas y JOINs

1. Crear tabla **items**

```sql
CREATE TABLE items (id VARCHAR PRIMARY KEY, make VARCHAR, model VARCHAR, unit_price DOUBLE)
WITH (KAFKA_TOPIC='items', VALUE_FORMAT='avro', PARTITIONS=1);
```

2. Insertar datos

```sql
INSERT INTO items VALUES('item_3', 'Spalding', 'TF-150', 19.99);
INSERT INTO items VALUES('item_4', 'Wilson', 'NCAA Replica', 29.99);
INSERT INTO items VALUES('item_7', 'SKLZ', 'Control Training', 49.99);
```

3. Eliminamos elementos del anterior ejercicio

```sql
DROP STREAM ny_orders;
DROP STREAM orders;
```

4. Creamos nueva stream **orders**

```sql
CREATE STREAM orders (ordertime BIGINT, orderid INTEGER, itemid VARCHAR, orderunits INTEGER)
WITH (KAFKA_TOPIC='item_orders', VALUE_FORMAT='avro', PARTITIONS=1);
```

5. Creamos streams **orders_enriched** que une la tabla **items** con la stream **orders**

```sql
CREATE STREAM orders_enriched AS
SELECT o.*, i.*,
	o.orderunits * i.unit_price AS total_order_value
FROM orders o LEFT OUTER JOIN items i
on o.itemid = i.id;
```

6. Insertamos datos en **orders**

```sql
INSERT INTO orders VALUES (1620501334477, 65, 'item_7', 5);
INSERT INTO orders VALUES (1620502553626, 67, 'item_3', 2);
INSERT INTO orders VALUES (1620503110659, 68, 'item_7', 7);
INSERT INTO orders VALUES (1620504934723, 70, 'item_4', 1);
INSERT INTO orders VALUES (1620505321941, 74, 'item_7', 3);
INSERT INTO orders VALUES (1620506437125, 72, 'item_7', 9);
INSERT INTO orders VALUES (1620508354284, 73, 'item_3', 4);
```

7. Validamos el resultado del JOIN

```sql
SELECT * FROM orders_enriched EMIT CHANGES;
```

### 3. Unir streams

1. Crear stream **orders_uk** e insertar eventos

```sql
CREATE STREAM orders_uk (ordertime BIGINT, orderid INTEGER, itemid VARCHAR, orderunits INTEGER,
    address STRUCT< street VARCHAR, city VARCHAR, state VARCHAR>)
WITH (KAFKA_TOPIC='orders_uk', VALUE_FORMAT='json', PARTITIONS=1);

INSERT INTO orders_uk VALUES (1620501334477, 65, 'item_7', 5,
  STRUCT(street:='234 Thorpe Street', city:='York', state:='England'));
INSERT INTO orders_uk VALUES (1620502553626, 67, 'item_3', 2,
  STRUCT(street:='2923 Alexandra Road', city:='Birmingham', state:='England'));
INSERT INTO orders_uk VALUES (1620503110659, 68, 'item_7', 7,
  STRUCT(street:='536 Chancery Lane', city:='London', state:='England'));

```

2. Crear stream **orders_us** e insertar eventos

```sql
CREATE STREAM orders_us (ordertime BIGINT, orderid INTEGER, itemid VARCHAR, orderunits INTEGER,
    address STRUCT< street VARCHAR, city VARCHAR, state VARCHAR>)
WITH (KAFKA_TOPIC='orders_us', VALUE_FORMAT='json', PARTITIONS=1);

INSERT INTO orders_us VALUES (1620501334477, 65, 'item_7', 5,
  STRUCT(street:='6743 Lake Street', city:='Los Angeles', state:='California'));
INSERT INTO orders_us VALUES (1620502553626, 67, 'item_3', 2,
  STRUCT(street:='2923 Maple Ave', city:='Mountain View', state:='California'));
INSERT INTO orders_us VALUES (1620503110659, 68, 'item_7', 7,
  STRUCT(street:='1492 Wandering Way', city:='Berkley', state:='California'));
```

3. Crear la unión de los streams mediante estas 2 queries

```sql
CREATE STREAM orders_combined AS
SELECT 'US' AS source, ordertime, orderid, itemid, orderunits, address
FROM orders_us;

INSERT INTO orders_combined
SELECT 'UK' AS source, ordertime, orderid, itemid, orderunits, address
FROM orders_uk;
```

4. Verificar el resultado

```sql
SELECT * FROM orders_combined emit changes;
```

### 4. Agregaciones con estado (vistas materializadas/materialized views)

1. Crear stream **movements**

```sql
CREATE STREAM MOVEMENTS(PERSON VARCHAR KEY, LOCATION VARCHAR)
WITH (VALUE_FORMAT='JSON', PARTITIONS=1, KAFKA_TOPIC='movements');
```

2. Insertar datos

```sql
INSERT INTO MOVEMENTS VALUES ('Robin', 'York');
INSERT INTO MOVEMENTS VALUES ('Robin', 'Leeds');
INSERT INTO MOVEMENTS VALUES ('Allison', 'Denver');
INSERT INTO MOVEMENTS VALUES ('Robin', 'Ilkley');
INSERT INTO MOVEMENTS VALUES ('Allison', 'Boulder');
```

3. Ver número de movimientos por persona

```sql
SELECT PERSON, COUNT (*)
FROM MOVEMENTS GROUP BY PERSON EMIT CHANGES;
```

4. Cantidad de posiciones únicas que cada persona ha visitado

```sql
SELECT PERSON, COUNT_DISTINCT(LOCATION)
FROM MOVEMENTS GROUP BY PERSON EMIT CHANGES;
```

5. Crear vista materializada

```sql
CREATE TABLE PERSON_STATS AS
SELECT PERSON,
		LATEST_BY_OFFSET(LOCATION) AS LATEST_LOCATION,
		COUNT(*) AS LOCATION_CHANGES,
		COUNT_DISTINCT(LOCATION) AS UNIQUE_LOCATIONS
	FROM MOVEMENTS
GROUP BY PERSON
EMIT CHANGES;
```

6. Insertar más datos

```sql
INSERT INTO MOVEMENTS VALUES('Robin', 'Manchester');
INSERT INTO MOVEMENTS VALUES('Allison', 'Loveland');
INSERT INTO MOVEMENTS VALUES('Robin', 'London');
INSERT INTO MOVEMENTS VALUES('Allison', 'Aspen');
INSERT INTO MOVEMENTS VALUES('Robin', 'Ilkley');
INSERT INTO MOVEMENTS VALUES('Allison', 'Vail');
INSERT INTO MOVEMENTS VALUES('Robin', 'York');
```

7. Verificar resultados para una persona

```sql
SELECT * FROM PERSON_STATS WHERE PERSON = 'Allison';
```

### 5. Pull y Push queries

**Push query**: se identifica por la clausula **EMIT CHANGES**. El cliente recibe un mensage por cada cambio que ocurre en la stream. Se mantiene la conexión abierta a la espera de nuevos cambios hasta que el cliente cierra la misma.

**Pull query**: Devuelve el estado actual al cliente y termina la conexión. Son similares a las query **SELECT** de las base de datos relacionales (MySQL, Postgres, etc)

1. Pull query

```sql
SELECT LATEST_LOCATION, LOCATION_CHANGES, UNIQUE_LOCATIONS
FROM PERSON_STATS WHERE PERSON = 'Allison';
```

2. Push query

```sql
SELECT LATEST_LOCATION, LOCATION_CHANGES, UNIQUE_LOCATIONS
FROM PERSON_STATS WHERE PERSON = 'Allison' EMIT CHANGES;
```

3. En otra sesión de KSQL

```bash
docker exec -it ksqldb-cli ksql http://ksqldb-server:8088
```

```sql
INSERT INTO MOVEMENTS VALUES ('Robin', 'York');
INSERT INTO MOVEMENTS VALUES ('Robin', 'Leeds');
INSERT INTO MOVEMENTS VALUES ('Allison', 'Denver');
INSERT INTO MOVEMENTS VALUES ('Robin', 'Ilkley');
INSERT INTO MOVEMENTS VALUES ('Allison', 'Boulder');
```

4. Verificar los nuevos mensajes en la sesión de la push query

## Anexo 1: Ejecución de los ejemplos desde un contenedor

```bash
docker exec -it runner bash
```

## Anexo 2: Solucionar problemas con la ejecución de contenedores

```bash
docker system prune
```

# Anexo 3: Repaso de conceptos básicos

- Clúster Kafka
  ![cluster](https://www.ionos.es/digitalguide/fileadmin/_processed_/5/6/csm_apache-kafka-ES-1_2552f353b6.webp)

- Estructura de un mensaje
  ![Mensaje](https://images.ctfassets.net/gt6dp23g0g38/7kjwh5nb53QL29LuUYAREZ/b8300cddd1e2034086878fdfd077413c/header.jpg)

- Estructura de un tópico
  ![Topic](https://miro.medium.com/v2/resize:fit:416/1*9Qm9qjZbvfV0X1pAlUUxcw.png)

- Offset
  ![offset](https://cdn.educba.com/academy/wp-content/uploads/2021/01/Kafka-offset.jpg)

- Grupo de consumidores
  ![consumer-group](https://docs.datastax.com/en/kafka/doc/kafka/images/partitionsKafka.png)

## Ejercicios

1. Crear topic "equipos" con 1 partición
2. Producir eventos en el topic "equipos"
3. Leer los eventos del topic
4. Resetear el offset del topic para volver a consumir desde el 2do mensaje
