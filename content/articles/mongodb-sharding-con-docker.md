Title: MongoDB sharding con docker
Slug: mongodb-sharding-con-docker
Date: 2018-07-02 09:00
Category: Sistemas
Tags: mongodb, docker, sharding, cluster



El otro día estaba revisando viejos artículos, y me tropecé con [uno anterior]({filename}/articles/mongodb-sharding-con-ansible.md). Este estaba montado con **ansible**, y se me pasó por la cabeza reescribirlo usando contenedores con **docker**. Así pues, vamos a montar exactamente el mismo *cluster*, pero con el cambio que la última revolución tecnológica nos aporta.

![Sharded cluster]({filename}/images/sharding_arquitectura_logica.jpg)

Aunque lo ideal sería desplegar todas las instancias en varias máquinas diferentes, voy a pasar; por comodidad, voy a desplegar todos los contenedores en una sola máquina mediante **docker-compose**. De esta forma puedo aprovechar las mismas imágenes sin una ocupación de disco elevada.

Como de costumbre, vamos a crear una carpeta para contener el proyecto y la vamos a llamar `sharding`. En ella voy a depositar los ficheros `Dockerfile` necesarios para la construcción de las imágenes, y de paso, el `docker-compose.yml` y las configuraciones que vamos a montar como volúmenes.

```bash
gerard@sirius:~/workspace/sharding$ tree
.
├── build
│   ├── mongo
│   │   └── Dockerfile
│   ├── mongod
│   │   └── Dockerfile
│   └── mongos
│       └── Dockerfile
├── docker-compose.yml
├── mongod_aquila.conf
├── mongod_config.conf
├── mongod_cygnus.conf
├── mongod_lyra.conf
└── mongos.conf

4 directories, 9 files
gerard@sirius:~/workspace/sharding$ 
```

## Construyendo las imágenes

El primer paso para levantar el entorno son las imágenes que lo sostienen. Necesitamos 3 imágenes: una para el proceso `mongod` (que sostiene los *shards* y los *config server*), una para el proceso `mongos` (punto de entrada al *cluster*) y otra para el cliente `mongo` (que nos sirve para atar el *cluster*).

```bash
gerard@sirius:~/workspace/sharding$ cat build/mongod/Dockerfile 
FROM alpine:3.7
RUN apk add --no-cache mongodb && \
    rm /usr/bin/mongo /usr/bin/mongos /usr/bin/mongoperf && \
    install -d -o mongodb -g mongodb -m 0755 /srv/mongodb
USER mongodb
CMD ["/usr/bin/mongod", "--config", "/etc/mongod.conf"]
gerard@sirius:~/workspace/sharding$ 
```

```bash
gerard@sirius:~/workspace/sharding$ cat build/mongos/Dockerfile 
FROM alpine:3.7
RUN apk add --no-cache mongodb && \
    rm /usr/bin/mongo /usr/bin/mongod /usr/bin/mongoperf
USER mongodb
CMD ["/usr/bin/mongos", "--config", "/etc/mongos.conf"]
gerard@sirius:~/workspace/sharding$ 
```

```bash
gerard@sirius:~/workspace/sharding$ cat build/mongo/Dockerfile 
FROM alpine:3.7
RUN apk add --no-cache mongodb && \
    rm /usr/bin/mongod /usr/bin/mongos /usr/bin/mongoperf
USER mongodb
gerard@sirius:~/workspace/sharding$ 
```

Solo nos queda construirlas usando los comandos habituales:

```bash
gerard@sirius:~/workspace/sharding$ docker build -t mongo-server build/mongod/
...
Successfully tagged mongo-server:latest
gerard@sirius:~/workspace/sharding$ 
```

```bash
gerard@sirius:~/workspace/sharding$ docker build -t mongo-proxy build/mongos/
...
Successfully tagged mongo-proxy:latest
gerard@sirius:~/workspace/sharding$ 
```

```bash
gerard@sirius:~/workspace/sharding$ docker build -t mongo-client build/mongo/
...
Successfully tagged mongo-client:latest
gerard@sirius:~/workspace/sharding$ 
```

## Levantando todos los procesos

La parte más tediosa de levantar un *cluster* es levantar todos los procesos implicados. En el caso del *cluster* de ejemplo, necesitamos un mínimo de 13 procesos:

* 1 `mongos` o más para poder utilizar e *cluster* de forma transparente
* 3 `mongod` en configuración de *replica set* para actuar como *config servers*
* 3 `mongod` en configuración de *replica set* para actuar como el *shard aquila*
* 3 `mongod` en configuración de *replica set* para actuar como el *shard lyra*
* 3 `mongod` en configuración de *replica set* para actuar como el *shard cygnus*

El contenedor para ejecutar el cliente `mongo` no es necesario; lo normal es que cada aplicación consuma directamente los procesos `mongos` utilizando el *driver*. Para operar el *cluster* vamos a levantar el cliente de forma puntual, eliminando el contenedor al acabar.

Para facilitar el levantado de procesos, vamos a utilizar **docker-compose**; aquí os dejo el fichero `docker-compose.yml`.

```bash
gerard@sirius:~/workspace/sharding$ cat docker-compose.yml 
version: '3'
services:
  mongos01:
    image: mongo-proxy
    container_name: mongos01
    hostname: mongos01
    volumes:
      - ./mongos.conf:/etc/mongos.conf:ro
    restart: always
  config01:
    image: mongo-server
    container_name: config01
    hostname: config01
    volumes:
      - ./mongod_config.conf:/etc/mongod.conf:ro
    restart: always
  config02:
    image: mongo-server
    container_name: config02
    hostname: config02
    volumes:
      - ./mongod_config.conf:/etc/mongod.conf:ro
    restart: always
  config03:
    image: mongo-server
    container_name: config03
    hostname: config03
    volumes:
      - ./mongod_config.conf:/etc/mongod.conf:ro
    restart: always
  aquila01:
    image: mongo-server
    container_name: aquila01
    hostname: aquila01
    volumes:
      - ./mongod_aquila.conf:/etc/mongod.conf:ro
    restart: always
  aquila02:
    image: mongo-server
    container_name: aquila02
    hostname: aquila02
    volumes:
      - ./mongod_aquila.conf:/etc/mongod.conf:ro
    restart: always
  aquila03:
    image: mongo-server
    container_name: aquila03
    hostname: aquila03
    volumes:
      - ./mongod_aquila.conf:/etc/mongod.conf:ro
    restart: always
  lyra01:
    image: mongo-server
    container_name: lyra01
    hostname: lyra01
    volumes:
      - ./mongod_lyra.conf:/etc/mongod.conf:ro
    restart: always
  lyra02:
    image: mongo-server
    container_name: lyra02
    hostname: lyra02
    volumes:
      - ./mongod_lyra.conf:/etc/mongod.conf:ro
    restart: always
  lyra03:
    image: mongo-server
    container_name: lyra03
    hostname: lyra03
    volumes:
      - ./mongod_lyra.conf:/etc/mongod.conf:ro
    restart: always
  cygnus01:
    image: mongo-server
    container_name: cygnus01
    hostname: cygnus01
    volumes:
      - ./mongod_cygnus.conf:/etc/mongod.conf:ro
    restart: always
  cygnus02:
    image: mongo-server
    container_name: cygnus02
    hostname: cygnus02
    volumes:
      - ./mongod_cygnus.conf:/etc/mongod.conf:ro
    restart: always
  cygnus03:
    image: mongo-server
    container_name: cygnus03
    hostname: cygnus03
    volumes:
      - ./mongod_cygnus.conf:/etc/mongod.conf:ro
    restart: always
gerard@sirius:~/workspace/sharding$ 
```

**NOTA**: Es importante que el *hostname* y el *container_name* sean el mismo; las *replicas* utilizan el *hostname* para su descubrimiento, pero el *container_name* al conectarse entre ellas.

Cada elemento dentro del *cluster* necesita un parámetro `replSetName` indicando el nombre de la *replica set* a la que pertenecen. Otro parámetro cambiante es el `clusterRole`, dependiendo si la *replica set* va a ejercer como *config server* o como *shard*. Los miembros del mismo *replica set* comparten configuración, así que solo necesitamos 4 distintas.

Empezaremos exponiendo la configuración de los *config server*:

```bash
gerard@sirius:~/workspace/sharding$ cat mongod_config.conf 
processManagement:
  fork: false

net:
  bindIp: 0.0.0.0
  port: 27019
  unixDomainSocket:
    enabled: false

storage:
  dbPath: /srv/mongodb
  engine: wiredTiger
  journal:
    enabled: true

replication:
  replSetName: config

sharding:
  clusterRole: configsvr
gerard@sirius:~/workspace/sharding$ 
```

La configuración de los *shards* es prácticamente la misma; solo hace falta cambiar el `clusterRole` el `replSetName` y el puerto usado. Empezaremos exponiendo la configuración del primer *shard*:

```bash
gerard@sirius:~/workspace/sharding$ cat mongod_aquila.conf 
processManagement:
  fork: false

net:
  bindIp: 0.0.0.0
  port: 27018
  unixDomainSocket:
    enabled: false

storage:
  dbPath: /srv/mongodb
  engine: wiredTiger
  journal:
    enabled: true

replication:
  replSetName: aquila

sharding:
  clusterRole: shardsvr
gerard@sirius:~/workspace/sharding$ 
```

**NOTA**: El *cluster* original ponía el árbitro en otro puerto para poder ir a la misma máquina. Esto ya no es necesario con **docker** y nos ahorra poner una configuración nueva.

Los otros *shards* son prácticamente iguales, cambiando solamente el nombre de la *replica set*:

```bash
gerard@sirius:~/workspace/sharding$ diff mongod_aquila.conf mongod_lyra.conf 
17c17
<   replSetName: aquila
---
>   replSetName: lyra
gerard@sirius:~/workspace/sharding$ diff mongod_aquila.conf mongod_cygnus.conf 
17c17
<   replSetName: aquila
---
>   replSetName: cygnus
gerard@sirius:~/workspace/sharding$ 
```

Y con esto tenemos todo lo necesario para levantar los procesos, así que no lo demoramos más.

```bash
gerard@sirius:~/workspace/sharding$ docker-compose up -d
Creating network "sharding_default" with the default driver
Creating cygnus03
Creating config03
Creating mongos01
Creating aquila02
Creating lyra03
Creating cygnus02
Creating cygnus01
Creating config01
Creating lyra01
Creating aquila03
Creating lyra02
Creating config02
Creating aquila01
gerard@sirius:~/workspace/sharding$ 
```

## Atando el cluster

Para atar completamente el *cluster* se necesita hacer dos cosas:

* Atar los *replica sets* que conformarán los *shards* y los *config server*
* Añadir los *shards* ya atados a través de un *mongos*

Estas tareas administrativas requieren de un cliente `mongo` que no queremos tener de forma permanente, así que tendremos un contenedor de "usar y tirar". De esta forma, cuando acabemos lo destruiremos y no tendremos partes innecesarias.

Levantar un contenedor con la imagen que contiene el cliente `mongo` no tiene misterio. El único detalle es que lo vamos a añadir a la misma red que creó el *docker-compose.yml*; eso nos garantiza que podamos usar los *container_name* en vez de ir buscando las direcciones IP de cada contenedor.

```bash
gerard@sirius:~/workspace/sharding$ docker run -ti --rm --net sharding_default mongo-client
/ $ 
```

**TRUCO**: A partir de aquí todos los comandos se hacen en el *shell* de *alpine linux*. Desde esta sesión interactiva, vamos a ir abriendo sesiones de *mongo shell* contra los procesos `mongod` o `mongos` que nos haga falta.

Atar los *replica sets* es siempre igual: entramos en uno de los miembros y le damos una configuración; otra opción es iniciar uno solo de los miembros y añadir los otros.

Empezaremos con los *config servers*, que a partir de la versión 3.2 de **mongodb** pueden ser *replica sets*, y que deben serlo a partir de la versión 3.4 (la que usamos). Entraremos en *config01* y lo inicializamos, para añadir los otros dos en el mismo *mongo shell*.

```bash
/ $ mongo --host config01 --port 27019
...
> rs.initiate()
{
	"info2" : "no configuration specified. Using a default configuration for the set",
	"me" : "config01:27019",
	"ok" : 1
}
config:PRIMARY> rs.add("config02:27019")
{ "ok" : 1 }
config:PRIMARY> rs.add("config03:27019")
{ "ok" : 1 }
config:PRIMARY> exit
bye
/ $ 
```

**NOTA**: Los *replica sets* destinados a ser *config servers* no pueden contener árbitros; si lo intentáis, obtendréis un bonito mensaje de error, pero no habrá consecuencias.

Repetiremos la fórmula para cada uno de los otros *shards*; entramos en el primer contenedor de cada *shard*, donde lo inicializamos y añadimos los otros dos. Para ser fieles al artículo original, el tercer contenedor de cada *shard* será un árbitro.

```bash
/ $ mongo --host aquila01 --port 27018
...
> rs.initiate()
{
	"info2" : "no configuration specified. Using a default configuration for the set",
	"me" : "aquila01:27018",
	"ok" : 1
}
aquila:PRIMARY> rs.add("aquila02:27018")
{ "ok" : 1 }
aquila:PRIMARY> rs.addArb("aquila03:27018")
{ "ok" : 1 }
aquila:PRIMARY> exit
bye
/ $ 
```

```bash
/ $ mongo --host lyra01 --port 27018
...
> rs.initiate()
{
	"info2" : "no configuration specified. Using a default configuration for the set",
	"me" : "lyra01:27018",
	"ok" : 1
}
lyra:PRIMARY> rs.add("lyra02:27018")
{ "ok" : 1 }
lyra:PRIMARY> rs.addArb("lyra03:27018")
{ "ok" : 1 }
lyra:PRIMARY> exit
bye
/ $ 
```

```bash
/ $ mongo --host cygnus01 --port 27018
...
> rs.initiate()
{
	"info2" : "no configuration specified. Using a default configuration for the set",
	"me" : "cygnus01:27018",
	"ok" : 1
}
cygnus:PRIMARY> rs.add("cygnus02:27018")
{ "ok" : 1 }
cygnus:PRIMARY> rs.addArb("cygnus03:27018")
{ "ok" : 1 }
cygnus:PRIMARY> exit
bye
/ $ 
```

Ahora tenemos 4 *replica sets*, uno configurado como *config server* y apuntado por el proceso `mongos`, y otros 3 que serán los *shards*. Vamos a iniciar un *mongo shell* contra el proceso `mongos`, desde donde vamos a acabar las configuraciones.

```bash
/ $ mongo --host mongos01 --port 27017
...
mongos> 
```

De hecho, en este punto ya tenemos un *cluster* funcional, pero como no tiene *shards*, no hay donde guardar datos.

```bash
mongos> sh.status()
--- Sharding Status --- 
  sharding version: {
  	"_id" : 1,
  	"minCompatibleVersion" : 5,
  	"currentVersion" : 6,
  	"clusterId" : ObjectId("5b182ae62446c4f43cbab312")
  }
  shards:
  active mongoses:
        "3.4.10" : 1
  autosplit:
        Currently enabled: yes
  balancer:
        Currently enabled:  yes
        Currently running:  no
NaN
        Failed balancer rounds in last 5 attempts:  0
        Migration Results for the last 24 hours: 
                No recent migrations
  databases:

mongos> 
```

Para añadir *shards* solamente tenemos que utilizar el método `sh.addShard()` para especificar la *replica set* que va a actuar como *shard*; hay que añadir la *replica set* siguiendo la fórmula `rsName/server1:port,...,serverN:port`, aunque si especificamos uno solo nombre, basta.

```bash
mongos> sh.addShard("aquila/aquila01:27018")
{ "shardAdded" : "aquila", "ok" : 1 }
mongos> 
```

**TRUCO**: A pesar de haber dado solamente el nombre *aquila01*, el resto de servidores ha sido descubierto por el *cluster* de forma automática; aún así, los árbitros no aparecen en el listado.

```bash
mongos> sh.status()
--- Sharding Status --- 
  sharding version: {
  	"_id" : 1,
  	"minCompatibleVersion" : 5,
  	"currentVersion" : 6,
  	"clusterId" : ObjectId("5b182ae62446c4f43cbab312")
  }
  shards:
        {  "_id" : "aquila",  "host" : "aquila/aquila01:27018,aquila02:27018",  "state" : 1 }
  active mongoses:
        "3.4.10" : 1
  autosplit:
        Currently enabled: yes
  balancer:
        Currently enabled:  yes
        Currently running:  no
NaN
        Failed balancer rounds in last 5 attempts:  0
        Migration Results for the last 24 hours: 
                No recent migrations
  databases:

mongos> 
```

Vamos a repetir la fórmula para añadir los otros *shards*, que es básicamente la misma:

```bash
mongos> sh.addShard("lyra/lyra01:27018")
{ "shardAdded" : "lyra", "ok" : 1 }
mongos> sh.addShard("cygnus/cygnus01:27018")
{ "shardAdded" : "cygnus", "ok" : 1 }
mongos> 
```

Y de esta forma, ya podemos ver el *cluster* acabado, con sus 3 *shards* añadidos sin problemas.

```bash
mongos> sh.status()
--- Sharding Status --- 
  sharding version: {
  	"_id" : 1,
  	"minCompatibleVersion" : 5,
  	"currentVersion" : 6,
  	"clusterId" : ObjectId("5b182ae62446c4f43cbab312")
  }
  shards:
        {  "_id" : "aquila",  "host" : "aquila/aquila01:27018,aquila02:27018",  "state" : 1 }
        {  "_id" : "cygnus",  "host" : "cygnus/cygnus01:27018,cygnus02:27018",  "state" : 1 }
        {  "_id" : "lyra",  "host" : "lyra/lyra01:27018,lyra02:27018",  "state" : 1 }
  active mongoses:
        "3.4.10" : 1
  autosplit:
        Currently enabled: yes
  balancer:
        Currently enabled:  yes
        Currently running:  no
NaN
        Failed balancer rounds in last 5 attempts:  0
        Migration Results for the last 24 hours: 
                No recent migrations
  databases:

mongos> 
```

Como no necesitamos más el contenedor del *mongo shell*, salimos de él para que el sistema lo pueda reciclar.

```bash
mongos> exit
bye
/ $ exit
gerard@sirius:~/workspace/sharding$ 
```

Y con esto estamos listos para introducir nuestros datos, aunque añadir más procesos `mongos` nos dará alta disponibilidad para el acceso de nuestras aplicaciones, aunque los *shards* y los *config servers* ya disfrutan de ella.
