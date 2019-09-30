---
title: "Un entorno productivo basado en Docker Swarm (III)"
slug: "un-entorno-productivo-basado-en-docker-swarm-3"
date: "2019-09-30"
categories: ['Sistemas']
tags: ['linux', 'entorno', 'docker', 'swarm', 'mongodb', 'cluster', 'autenticación']
series: "Un entorno productivo basado en Docker Swarm"
---

Continuamos la serie enfocada a construir un entorno entero basado en **docker swarm**
siguiendo desde el punto en que lo dejamos: con los servidores a punto y el *cluster*
en marcha. Ahora vamos a poner en marcha un *cluster* de base de datos en el mismo
*swarm* que, por ejemplo, va a ser un *replica set* de **mongodb**.<!--more-->

Como ya sabemos que en un entorno de bases de datos compartidas **suceden cosas malas**,
vamos a habilitar autenticación, de forma que cada aplicación va a tener acceso a su
propia base de datos, y a ninguna más. Como se trata de un *replica set*, hay un paso
extra: los nodos del *cluster* también deben tener un mecanismo de autenticación propio.

**NOTA**: Este artículo combina el contenido de dos artículos anteriores, que indican
como [montar un *replica set*][1] y como [habilitar autenticación][2], aunque también
incluye una parte adicional, que corresponde a la autenticación entre los nodos del *cluster*.

## Decisiones de diseño

Como vamos a utilizar **docker**, necesitamos pensar por un momento como nos lo vamos
a hacer para tener los datos persistentes; además tenemos el *handicap* de que el *swarm*
va a recolocar los nodos si fuera necesario.

Para no montar un sistema de ficheros distribuido, he decidido que voy a utilizar
volúmenes locales, lo que nos obliga a separar los contenedores en diferentes nodos del
*swarm*; para asegurar que no acaban en el mismo (usarían el mismo volumen) y para
evitar que *swarm* los recoloque (dejarían el volumen y los datos atrás), me he decidido
por "clavar" cada instancia del *replica set* a un nodo concreto del *swarm*.

Otra decisión de diseño será pasar los ficheros necesarios para cada servicio utilizando
[secretos y configuraciones][3], lo que nos evita hacer una distribución de los mismos
de forma manual.

Finalmente, a nivel de **docker** los contenedores del *replica set* van ser servicios
diferentes; de esta forma cualquier servicio se podrá referir a un nodo en particular
por el nombre de su servicio, que es un balanceador *ingress* directo al único contenedor.

**TRUCO**: Todos los contenedores conectados a un red *overlay* van a poder utilizar
el nombre del servicio del resto, a modo de resolución DNS. Como voy a poner un *stack*
para cada aplicación y uno para la base de datos, necesito una red global, que no
pertenezca a ningún *stack* particular. La llamaré *backend* y todos los contenedores
que estén en ella podrán utilizar el nombre de servicio de los nodos de **mongodb**.

## Implementación del *cluster*

### El fichero keyfile

Lo primero de todo es la creación de un fichero [*keyFile*][4], ya que sin él, los nodos
del *replica set* con autenticación habilitada no aceptarían operaciones de *cluster*.
Siguiendo la documentación proporcionada, bastaría con poner un fichero con un contenido
cualquiera entre 6 y 1024 bytes. Vamos a utilizar **openssl** para crear uno aleatorio:

```bash
gerard@docker01:~$ mkdir mongo
gerard@docker01:~$ cd mongo/
gerard@docker01:~/mongo$ 
```

```bash
gerard@docker01:~/mongo$ openssl rand -base64 756 > keyfile
gerard@docker01:~/mongo$ 
```

```bash
gerard@docker01:~/mongo$ cat keyfile 
8OftSgxaHKz5+RD5ehmVgTQ+KjAptZq9qSVEb61YO9F0FIE6GRlus6GmdduzmMwE
...
+0UZsNWMfkTDY53VpxY1qV+S7HzZ9Uc5RswLeKPJAnBxtunj
gerard@docker01:~/mongo$ 
```

**NOTA**: Podemos trabajar desde cualquier *manager* del *swarm*; utilizo **docker01**
por utilizar alguno. Desde aquí empujaremos los cambios al resto utilizando el mismo *swarm*.

**TRUCO**: El fichero debe pertenecer al usuario que ejecute el proceso `mongod` y tener
permisos 400 (o `-r--------`); esto lo conseguiremos en el mapeo del secreto en la declaración
del *stack*. El usuario y su *uid* se pueden sacar del fichero `/etc/passwd` del contenedor.

```bash
gerard@atlantis:~/personal/mongo$ docker run -ti --rm sirrtea/mongo:debian cat /etc/passwd
...
mongodb:x:101:65534::/home/mongodb:/bin/false
gerard@atlantis:~/personal/mongo$ 
```

### La configuración de mongo

Todos los nodos del *replica set* utilizan la misma, lo que nos simplifica el *setup*.
Sin embargo, no nos vale la que viene en la imagen; no lleva ninguna configuración relativa
al *replica set* ni a la autenticación. Simplemente copiamos la configuración de la imagen
y le añadimos las claves `replication` y `security`.

```bash
gerard@docker01:~/mongo$ cat mongod.conf 
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

security:
  keyFile: /run/secrets/keyfile
  authorization: enabled
gerard@docker01:~/mongo$ 
```

**NOTA**: En este momento, vamos a hacer acto de fe, y nos vamos a creer que el *keyfile*
estará en `/run/secrets/`, que es donde *swarm* deja todos los secretos.

### Los servicios del *stack*

Nos limitamos a describir los servicios-contenedores que van a formar el *replica set*, sin
olvidarnos del *keyfile* (y el *uid* 101 equivalente al usuario `mongodb`), ni de la
configuración de **mongo**, ni de las restricciones de desplegar en nodos concretos (usando
el *tag* `mongo`), ni del volumen local, ni de la red *backend*.

```bash
gerard@docker01:~/mongo$ cat mongo.yml 
version: "3.3"
services:
  mongo01:
    image: sirrtea/mongo:debian
    secrets:
      - source: keyfile
        uid: '101'
        mode: 0400
    configs:
      - source: mongod.conf
        target: /etc/mongod.conf
    deploy:
      placement:
        constraints:
        - node.labels.mongo == 01
    volumes:
      - data:/var/lib/mongodb
    networks:
      - backend
  mongo02:
    image: sirrtea/mongo:debian
    secrets:
      - source: keyfile
        uid: '101'
        mode: 0400
    configs:
      - source: mongod.conf
        target: /etc/mongod.conf
    deploy:
      placement:
        constraints:
        - node.labels.mongo == 02
    volumes:
      - data:/var/lib/mongodb
    networks:
      - backend
  mongo03:
    image: sirrtea/mongo:debian
    secrets:
      - source: keyfile
        uid: '101'
        mode: 0400
    configs:
      - source: mongod.conf
        target: /etc/mongod.conf
    deploy:
      placement:
        constraints:
        - node.labels.mongo == 03
    volumes:
      - data:/var/lib/mongodb
    networks:
      - backend
secrets:
  keyfile:
    file: keyfile
configs:
  mongod.conf:
    file: mongod.conf
volumes:
  data:
networks:
  backend:
    external: true
gerard@docker01:~/mongo$ 
```

### Levantando el *stack*

**WARNING**: En este punto no existe ni la red *backend* ni los *tags* `mongo`
para los nodos del *swarm*; es un buen momento para ponerlos. Vamos a desplegar
los contenedores en **docker04**, **docker05** y **docker06** respectivamente
para descargar de trabajo a los *managers*.

```bash
gerard@docker01:~/mongo$ docker network create -d overlay backend
07xs5ra32um3tb16coktynl2i
gerard@docker01:~/mongo$ 
```

```bash
gerard@docker01:~/mongo$ docker node update --label-add mongo=01 docker04
docker04
gerard@docker01:~/mongo$ 
```

```bash
gerard@docker01:~/mongo$ docker node update --label-add mongo=02 docker05
docker05
gerard@docker01:~/mongo$ 
```

```bash
gerard@docker01:~/mongo$ docker node update --label-add mongo=03 docker06
docker06
gerard@docker01:~/mongo$ 
```

Y solo nos falta desplegar el *stack*:

```bash
gerard@docker01:~/mongo$ docker stack deploy -c mongo.yml mongo
Creating secret mongo_keyfile
Creating config mongo_mongod.conf
Creating service mongo_mongo03
Creating service mongo_mongo01
Creating service mongo_mongo02
gerard@docker01:~/mongo$ 
```

Si todo ha ido bien, tenemos el *stack* y sus servicios levantados:

```bash
gerard@docker01:~/mongo$ docker stack ls
NAME                SERVICES            ORCHESTRATOR
mongo               3                   Swarm
gerard@docker01:~/mongo$ docker stack ps mongo
ID                  NAME                IMAGE                  NODE                DESIRED STATE       CURRENT STATE                ERROR               PORTS
utzhwaxskcmb        mongo_mongo02.1     sirrtea/mongo:debian   docker05            Running             Running 2 minutes ago                            
4xn6emptjk6d        mongo_mongo01.1     sirrtea/mongo:debian   docker04            Running             Running about a minute ago                       
ulfd25fqqbdd        mongo_mongo03.1     sirrtea/mongo:debian   docker06            Running             Running about a minute ago                       
gerard@docker01:~/mongo$ 
```

### Inicializando el *replica set* y el usuario inicial

**NOTA**: Este paso se hace una sola vez; esto queda guardado con los datos del
**mongo** y no hace falta repetirlo nunca más.

Para configurar el *replica set* necesitamos entrar en uno de ellos a ejecutar algunos pasos;
por ejemplo entramos en **mongo01** que está "clavado" en **docker04**:

```bash
gerard@docker04:~$ docker ps
CONTAINER ID        IMAGE                  COMMAND                  CREATED             STATUS              PORTS               NAMES
4891c8b577e7        sirrtea/mongo:debian   "/usr/bin/mongod --c…"   8 minutes ago       Up 8 minutes                            mongo_mongo01.1.4xn6emptjk6duqse0tj9ey3hc
gerard@docker04:~$ docker exec -ti 4891c8b577e7 mongo
MongoDB shell version v4.0.11
...
> 
```

Primero hay que atar la *replica set*; lo hago en un solo comando para aligerar, pero nada
impediría hacer un `rs.initiate()` y varios `rs.add()`.

```bash
> rs.initiate(
...    {
...       _id: "rs",
...       version: 1,
...       members: [
...          { _id: 0, host : "mongo01:27017" },
...          { _id: 1, host : "mongo02:27017" },
...          { _id: 2, host : "mongo03:27017" }
...       ]
...    }
... )
{ "ok" : 1 }
rs:SECONDARY> 
```

Para que la autenticación de usuarios se haga efectiva, debemos poner uno, con permisos
suficientes para gestionar todo el resto. Voy a crear un usuario **admin** y luego ya
pensaremos en hacer usuarios "de uso habitual" de la base de datos, más limitados a sus funciones.

```bash
rs:PRIMARY> use admin
switched to db admin
rs:PRIMARY> db.createUser({user: "admin", pwd: "s3cr3t", roles: [{role: "root", db: "admin"}]})
Successfully added user: {
	"user" : "admin",
	"roles" : [
		{
			"role" : "root",
			"db" : "admin"
		}
	]
}
rs:PRIMARY> 
```

Si lo hemos hecho bien, salimos del *mongo shell* y al entrar, nos obligará a autenticarnos
para poder sacar un `rs.status()`, que de paso, confirmará que el *replica set* esta bien.

```bash
gerard@docker04:~$ docker exec -ti 4891c8b577e7 mongo
...
rs:PRIMARY> rs.status()
...
	"ok" : 0,
	"errmsg" : "command replSetGetStatus requires authentication",
	"code" : 13,
	"codeName" : "Unauthorized",
...
rs:PRIMARY> 
```

Nos autenticamos como **admin** y repetimos:

```bash
rs:PRIMARY> use admin
switched to db admin
rs:PRIMARY> db.auth("admin", "s3cr3t")
1
rs:PRIMARY> rs.status()
{
	"set" : "rs",
...
	"members" : [
		{
...
			"name" : "mongo01:27017",
...
			"stateStr" : "PRIMARY",
		},
		{
...
			"name" : "mongo02:27017",
...
			"stateStr" : "SECONDARY",
		},
		{
...
			"name" : "mongo03:27017",
...
			"stateStr" : "SECONDARY",
...
		}
	],
	"ok" : 1,
...
}
rs:PRIMARY> 
```

Y de momento lo dejamos; habrá que crear usuarios para que las aplicaciones accedan a
su propia base de datos, pero como de momento no servimos ninguna aplicación, ya lo
revisaremos en futuros artículos de la serie.

[1]: {{< relref "/articles/2015/12/construyendo-una-replica-set-en-mongodb.md" >}}
[2]: {{< relref "/articles/2018/03/usando-autenticacion-en-mongodb.md" >}}
[3]: {{< relref "/articles/2019/06/distribuyendo-contenido-en-docker-swarm-configuraciones-y-secretos.md" >}}
[4]: https://docs.mongodb.com/manual/tutorial/enforce-keyfile-access-control-in-existing-replica-set/
