---
title: "Automatizando el setup de un mongo replica set en docker"
slug: "automatizando-el-setup-de-un-mongo-replica-set-en-docker"
date: 2018-01-29
categories: ['Sistemas']
tags: ['mongodb', 'replica set', 'docker', 'docker-compose']
---

Algunas veces queremos probar nuestras aplicaciones en local y necesitamos una base de datos **MongoDB**; en estos casos, **Docker** nos presta un gran servicio. Es posible que en estos casos necesitemos un **replica set** para probar; aunque **Docker** sigue ayudando, la inicialización del *cluster* sigue siendo un tedioso proceso manual.<!--more-->

Así que me puse a pensar... ¿Por qué no puedo atar el **replica set** directamente en el proceso de *runtime*?

* **Docker** ejecuta un solo proceso (que debe ser *mongod*)
* Necesitamos un proceso auxiliar para atar el *cluster*
* No queremos más contenedores que los que hacen falta
* No quiero imágenes específicas de un "*mongodb leader*"

Tras muchas vueltas a la cabeza, llegué a un conclusión interesante:

1. Podemos crear el comportamiento líder mediante variables de entorno
2. Este líder puede lanzar un proceso en *background* que se dedique a atar el *cluster* y luego muera

Para conseguir este doble proceso condicionado, nos vemos obligados a cambiar el comando *mongod* por un *script* que ejecute el *setup* del *cluster* (si procede) y el proceso *mongod*.

## La imagen única

Partimos de un *Dockerfile* bastante estándar; las únicas excepciones van a ser el *script* inicial y otro *script* auxiliar que configure nuestro *cluster* en una sola de las máquinas.

```bash
gerard@aldebaran:~/docker/replica/mongo$ cat Dockerfile 
FROM debian:jessie-slim
RUN apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv 0C49F3730359A14518585931BC711F9BA15703C6 && \
    echo "deb http://repo.mongodb.org/apt/debian jessie/mongodb-org/3.4 main" > /etc/apt/sources.list.d/mongodb-org-3.4.list
RUN apt-get update && \
    apt-get install -y mongodb-org-server mongodb-org-shell && \
    rm -rf /var/lib/apt/lists/*
COPY mongod.conf /etc/
COPY start.sh setup_cluster.sh /
USER mongodb
CMD ["/start.sh"]
gerard@aldebaran:~/docker/replica/mongo$ 
```

La configuración de **mongodb** es bastante estándar y solo se incluye por completitud:

```bash
gerard@aldebaran:~/docker/replica/mongo$ cat mongod.conf 
processManagement:
  fork: false

net:
  bindIp: 0.0.0.0
  port: 27017
  unixDomainSocket:
    enabled: false

storage:
  dbPath: /var/lib/mongodb
  journal:
    enabled: true

replication:
   replSetName: rs
gerard@aldebaran:~/docker/replica/mongo$ 
```

Y este es el truco: vamos a definir dos variables de entorno, llamadas **ROLE** y **REPLICAS**. La idea es que el que tenga que configurar el *cluster* va a tener en **ROLE** algún valor que le dé a entender que es el elegido, y la variable **REPLICAS** que le indica los otros miembros a añadir en el *cluster*.

De hecho, las variables no necesitan estar en las réplicas, porque **bash** va a interpretar la variable **ROLE** inexistente como vacía y no va a lanzar el proceso de configuración, haciendo de la variable **REPLICAS** algo innecesario.

El contenedor con el rol *orchestrator* va a levantar otro *script* en *background*, dejando así el flujo de ejecución para el proceso *mongod*. Este *script* tiene permisos de ejecución.

```bash
gerard@aldebaran:~/docker/replica/mongo$ cat start.sh 
#!/bin/bash

if [ "$ROLE" == "orchestrator" ]; then
	/setup_cluster.sh &
fi

exec mongod --config /etc/mongod.conf
gerard@aldebaran:~/docker/replica/mongo$ 
```

El *script setup_cluster.sh* (también ejecutable) es complejo, pero no complicado:

* Espera a que todos los procesos *mongod* respondan
* Conecta a su mismo contenedor para lanzar el `rs.initiate()` y el `rs.add(...)` de las *replicas*
* Espera que todas las *replicas* estén como secundarias, mediante `rs.status()`

y así queda esta primera versión:

```bash
gerard@aldebaran:~/docker/replica/mongo$ cat setup_cluster.sh 
#!/bin/bash

for REPLICA in ${REPLICAS}; do
	until echo "" | mongo --host ${REPLICA} >/dev/null 2>&1; do sleep 1; done
done
until echo "" | mongo >/dev/null 2>&1; do sleep 1; done

replicas=0
echo "rs.initiate()" | mongo >/dev/null 2>&1
for REPLICA in ${REPLICAS}; do
	echo "rs.add(\"${REPLICA}:27017\")" | mongo >/dev/null 2>&1
	let replicas=replicas+1
done

online=0
until [ ${online} -eq ${replicas} ]; do
	sleep 1
	online=$(echo "rs.status()" | mongo 2>/dev/null | grep -c "SECONDARY")
done
gerard@aldebaran:~/docker/replica/mongo$ 
```

## Testeando nuestro deploy

Levantar 3 contenedores es muy pesado y nada apetecible, así que haremos con **Docker Compose**. Veamos un *docker-compose.yml* de ejemplo:

```bash
gerard@aldebaran:~/docker/replica$ cat docker-compose.yml 
version: '3'
services:
  rs01:
    image: mongo
    hostname: rs01
    container_name: rs01
    environment:
        ROLE: orchestrator
        REPLICAS: "rs02 rs03"
  rs02:
    image: mongo
    hostname: rs02
    container_name: rs02
  rs03:
    image: mongo
    hostname: rs03
    container_name: rs03
gerard@aldebaran:~/docker/replica$ 
```

De esta forma, y de acuerdo a las decisiones de diseño, el contenedor *rs01* inicializaría el *cluster* consigo mismo y añadiría *rs02* y *rs03*.

```bash
gerard@aldebaran:~/docker/replica$ docker-compose up -d
Creating network "replica_default" with the default driver
Creating rs01
Creating rs02
Creating rs03
gerard@aldebaran:~/docker/replica$ docker-compose ps
Name    Command    State   Ports 
--------------------------------
rs01   /start.sh   Up            
rs02   /start.sh   Up            
rs03   /start.sh   Up            
gerard@aldebaran:~/docker/replica$ 
```

Solo nos quedaría entrar en un *mongod* cualquiera y pedirle el estado del *cluster* con `rs.status()`.

```bash
gerard@aldebaran:~/docker/replica$ docker exec -ti rs02 mongo
MongoDB shell version v3.4.4
connecting to: mongodb://127.0.0.1:27017
MongoDB server version: 3.4.4
...  
rs:SECONDARY> rs.status()
{
	"set" : "rs",
...  
	"members" : [
		{
			"_id" : 0,
			"name" : "rs01:27017",
...  
			"stateStr" : "PRIMARY",
...  
		},
		{
			"_id" : 1,
			"name" : "rs02:27017",
...  
			"stateStr" : "SECONDARY",
...  
			"self" : true
		},
		{
			"_id" : 2,
			"name" : "rs03:27017",
...  
			"stateStr" : "SECONDARY",
...  
		}
	],
	"ok" : 1
}
rs:SECONDARY> 
```

Y todo ha quedado como esperábamos, sin ninguna intervención manual por nuestra parte.
