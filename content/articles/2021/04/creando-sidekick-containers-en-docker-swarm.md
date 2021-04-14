---
title: "Creando sidekick containers en Docker Swarm"
slug: "creando-sidekick-containers-en-docker-swarm"
date: "2021-04-14"
categories: ['Operaciones']
tags: ['docker', 'swarm', 'sidekick']
---

Ya hablamos sobre los *sidekick containers* en [otro artículo][1]. Vimos como
podemos tener contenedores que se dediquen a "ayudar" a otros contenedores,
y la idea es la misma cuando trabajamos con **Docker Swarm**. Lo que no es
tan simple es crear un contenedor que ejecute una acción y "muera", una vez
cumplido su objetivo.<!--more-->

El problema es que **Docker Swarm** está pensado para alojar servicios que se
mantienen en ejecución y, cuando estos acaban, se entiende que es por algún tipo
de problema y se recoloca un contenedor para sustituir el que acaba de caer.

Este comportamiento se debe a la directiva *restart policy* del servicio
alojado en el **swarm**; por defecto se reinicia un servicio por cualquier
condición. Pero esto es un parámetro que podemos definir cuando creamos el
servicio o cuando escribimos el fichero tipo *compose* de nuestro *stack*,
con la directiva `deploy.restart_policy.condition`:

* `condition: none` &rarr; no reinicia **nunca** el contenedor, pase lo que pase.
* `condition: on-failure` &rarr; reinicia el contenedor si este acaba en fallo (código de retorno diferente de 0).
* `condition: any` &rarr; reinicia **siempre** el contenedor; es el valor por defecto.

El valor por defecto es el más útil en general, pero hay algunas veces en los que
necesitamos ejecutar una solo vez y olvidar, posiblemente para hacer algunas
acciones de inicialización en nuestro sistema, ya sea por necesidad o por comodidad.

## Un ejemplo: inicializar una base de datos

Supongamos que nuestro sistema necesita una base de datos con cierto estado
cuando se inicia. Para ello nos interesa restaurar un backup conocido una
sola vez; para ello necesitamos un contenedor que haga la restauración y se
quede parado, sin relanzar el *backup* nunca más.

**NOTA**: Vamos a utilizar **mongodb** por la familiaridad que le tenemos,
aunque los principios aplicarían a cualquier otra tecnología.

El truco es simple; en vez de levantar la base de datos, vamos a levantar dos
servicios: la base de datos en sí misma, y otro servicio efímero que ejecutará
el correspondiente `mongorestore`. Para ello, el nuevo servicio va a:

* Declarar la directiva `deploy.restart_policy.condition: on-failure`;
  * Lo reintentará mientras la base de datos no esté disponible.
  * Evitará que lo reintente una vez lo haya conseguido por primera vez.
* Inyectar el *backup* como [secretos o configuraciones][2], para tener algo que restaurar.
* Cambiar el `command` para que ejecute un `mongorestore` en vez del servidor de base de datos.

Siguiendo el patrón de trabajo habitual, crearemos una carpeta contenedora para
contener nuestro `stack.yml` (fichero tipo *compose*), un *script* de despliegue
y el propio *backup* que queremos restaurar:

```bash
gerard@atlantis:~/projects/sidekick$ tree
.
├── deploy.sh
├── shop.archive.gz
└── stack.yml

0 directories, 3 files
gerard@atlantis:~/projects/sidekick$ 
```

Nuestro `stack.yml` puede ser tan simple o complejo como necesitemos, pero ahora
nos vale con un ejemplo simple, que solo levanta un **mongodb** solo, para su uso
por otros servicios "de aplicación". Ya de paso, incluimos el *script* de despliegue.

```bash
gerard@atlantis:~/projects/sidekick$ cat stack.yml 
version: '3.5'
services:
  mongo:
    image: mongo:4.4
    volumes:
      - data:/data/db
  mongoloader:
    image: mongo:4.4
    configs:
      - shop.archive.gz
    deploy:
      restart_policy:
        condition: on-failure
    command: mongorestore --uri=mongodb://mongo/ --archive=/shop.archive.gz --gzip --drop
volumes:
  data:
configs:
  shop.archive.gz:
    file: shop.archive.gz
gerard@atlantis:~/projects/sidekick$ 
```

```bash
gerard@atlantis:~/projects/sidekick$ cat deploy.sh 
#!/bin/bash

docker stack deploy -c stack.yml database
gerard@atlantis:~/projects/sidekick$ 
```

Ejecutamos el *script* de despliegue y esperamos que haya acabado:

```bas
gerard@atlantis:~/projects/sidekick$ ./deploy.sh 
Creating network database_default
Creating config database_shop.archive.gz
Creating service database_mongo
Creating service database_mongoloader
gerard@atlantis:~/projects/sidekick$ 
```

```bash
gerard@atlantis:~/projects/sidekick$ docker stack ps database
ID             NAME                     IMAGE       NODE       DESIRED STATE   CURRENT STATE             ERROR     PORTS
it8ijyw82pn5   database_mongo.1         mongo:4.4   atlantis   Running         Running 18 seconds ago              
1v52ujetbmwc   database_mongoloader.1   mongo:4.4   atlantis   Shutdown        Complete 15 seconds ago             
gerard@atlantis:~/projects/sidekick$ 
```

**TRUCO**: Vemos que el estado del servicio *mongoloader* es *complete* y que
el estado deseado es *shutdown*. Eso significa que todo ha ido bien.

Solo nos falta comprobar que el *backup* se ha restaurado. Para ello necesitaremos
sacar el identificador o el nombre del contenedor creado (es un *swarm* de un solo
nodo y, por lo tanto, el contenedor está en esta misma máquina) y entrar en el
mismo para ejecutar alguna consulta que evidencie que los datos han sido cargados.

```bash
gerard@atlantis:~/projects/sidekick$ docker ps
CONTAINER ID   IMAGE       COMMAND                  CREATED              STATUS              PORTS       NAMES
78635edd4bc7   mongo:4.4   "docker-entrypoint.s…"   About a minute ago   Up About a minute   27017/tcp   database_mongo.1.it8ijyw82pn5krtcr7e8uzte2
gerard@atlantis:~/projects/sidekick$ 
```

```bash
gerard@atlantis:~/projects/sidekick$ docker exec -ti 78635edd4bc7 mongo shop
MongoDB shell version v4.4.5
connecting to: mongodb://127.0.0.1:27017/shop?compressors=disabled&gssapiServiceName=mongodb
Implicit session: session { "id" : UUID("04caa3e7-3ac9-4d8e-966c-6ec6c5cbc437") }
MongoDB server version: 4.4.5
...
> db.fruits.find()
{ "_id" : ObjectId("6051bfe947e2bb9faf18f993"), "name" : "Apple", "price" : 1 }
{ "_id" : ObjectId("6051bff347e2bb9faf18f994"), "name" : "Orange", "price" : 0.8 }
{ "_id" : ObjectId("6051bffa47e2bb9faf18f995"), "name" : "Pear", "price" : 1.2 }
> 
```

Y con esto ya tenemos nuestro *sidekick container*, que ha ejecutado una sola acción
y ya nos ha dejado el sistema inicializado. Cabe indicar que solo va a ejecutar de
nuevo el `mongorestore` si el contenedor es recreado, por ejemplo, porque algo cambie
en la definición del servicio *mongoloader* en el `stack.yml`.

**TRUCO**: Si no se necesita más, es un buen momento para quitar el servicio del *stack*
o declarar que queremos 0 réplicas de ahora en adelante, de cara al siguiente *deploy*.

[1]: {{< relref "/articles/2018/03/los-sidekick-containers-en-docker.md" >}}
[2]: {{< relref "/articles/2019/06/distribuyendo-contenido-en-docker-swarm-configuraciones-y-secretos.md" >}}
