---
title: "Uso básico de un cluster Docker Swarm"
slug: "uso-basico-de-un-cluster-docker-swarm"
date: 2017-11-06
categories: ['Sistemas']
tags: ['docker', 'swarm', 'cluster', 'uso', 'básico']
---

Usar un *cluster* de **docker swarm** no es transparente para nuestro uso; necesitamos cambiar de mentalidad y tener en cuenta algunos conceptos. Donde antes hablábamos de contenedores, aquí se habla de **servicios**, que básicamente son un número variable de contenedores repartidos por los diferentes nodos del *cluster* de forma balanceada.<!--more-->

Para trabajar con **docker swarm** necesitamos trabajar desde un nodo *manager*, y no desde los *workers*. Por ello, el resto de comandos se van a lanzar en **shangrila**, a menos que se diga lo contrario. En este artículo vamos a utilizar el que montamos en [este otro artículo]({{< relref "/articles/2017/10/montando-un-cluster-de-docker-con-docker-swarm.md" >}}).

## Un servicio básico

Si queremos crear un servicio, podemos utilizar los subcomandos de `docker service`. Una vez creado el servicio podemos trabajar con él sin problemas. Veamos una creación de un servicio básico:

```bash
gerard@shangrila:~$ docker service create --replicas 1 --name helloworld alpine ping docker.com
rl39orkjrie1r1vv0as368s8x
Since --detach=false was not specified, tasks will be created in the background.
In a future release, --detach=false will become the default.
gerard@shangrila:~$
```

Básicamente esto nos indica que queremos crear un servicio llamado *helloworld*, ejecutando un contenedor *alpine* y lanzando el comando `ping docker.com`. El número de replicas inicial lo ponemos, por ejemplo, a 1; podemos escalarlo cuando queramos.

Podemos ver el estado de nuestro servicio con `docker service ls`:

```bash
gerard@shangrila:~$ docker service ls
ID                  NAME                MODE                REPLICAS            IMAGE               PORTS
rl39orkjrie1        helloworld          replicated          1/1                 alpine:latest
gerard@shangrila:~$
```

Si necesitamos una información más detallada, podemos hacer un `docker service inspect`:

```bash
gerard@shangrila:~$ docker service inspect --pretty helloworld

ID:             rl39orkjrie1r1vv0as368s8x
Name:           helloworld
Service Mode:   Replicated
 Replicas:      1
Placement:
UpdateConfig:
 Parallelism:   1
 On failure:    pause
 Monitoring Period: 5s
 Max failure ratio: 0
 Update order:      stop-first
RollbackConfig:
 Parallelism:   1
 On failure:    pause
 Monitoring Period: 5s
 Max failure ratio: 0
 Rollback order:    stop-first
ContainerSpec:
 Image:         alpine:latest@sha256:f006ecbb824d87947d0b51ab8488634bf69fe4094959d935c0c103f4820a417d
 Args:          ping docker.com
Resources:
Endpoint Mode:  vip
gerard@shangrila:~$
```

Con `docker service ps` podemos saber en que nodos se encuentra nuestro servicio desplegado:

```bash
gerard@shangrila:~$ docker service ps helloworld
ID                  NAME                IMAGE               NODE                DESIRED STATE       CURRENT STATE            ERROR               PORTS
q5xeb2bftqlq        helloworld.1        alpine:latest       eldorado            Running             Running 10 minutes ago
gerard@shangrila:~$
```

## Escalando el servicio

En el caso que necesitemos ajustar el número de nodos que ejecutan una copia, podemos escalar. Esto tampoco tiene ninguna complicación:

```bash
gerard@shangrila:~$ docker service scale helloworld=4
helloworld scaled to 4
gerard@shangrila:~$
```

Hemos escalado nuestro servicio por encima del número de nodos del **swarm**. En este caso, esto no es un problema; solamante veremos que hay nodos con varios contenedores.

```bash
gerard@shangrila:~$ docker service ls
ID                  NAME                MODE                REPLICAS            IMAGE               PORTS
rl39orkjrie1        helloworld          replicated          4/4                 alpine:latest
gerard@shangrila:~$ docker service ps helloworld
ID                  NAME                IMAGE               NODE                DESIRED STATE       CURRENT STATE            ERROR               PORTS
q5xeb2bftqlq        helloworld.1        alpine:latest       eldorado            Running             Running 12 minutes ago
6ruk3h9lvzom        helloworld.2        alpine:latest       shangrila           Running             Running 2 seconds ago
j2xuo9pvfoeu        helloworld.3        alpine:latest       arcadia             Running             Running 2 seconds ago
t2emtl7m6r3b        helloworld.4        alpine:latest       arcadia             Running             Running 2 seconds ago
gerard@shangrila:~$
```

Si se cayera un nodo, el mismo **swarm** se encarga de levantar otro contenedor en un nodo vivo para sustituir los fallos posibles de este *downtime*:

```bash
erard@shangrila:~$ docker node ls
ID                            HOSTNAME            STATUS              AVAILABILITY        MANAGER STATUS
5p0wbl6rhvs5oo461xsmxhph4     eldorado            Down                Active
rtmzvsbndn4ox5mhzsgu2xi81 *   shangrila           Ready               Active              Leader
su20j7s0itgssfcm8x5whz8o8     arcadia             Ready               Active
gerard@shangrila:~$ docker service ls
ID                  NAME                MODE                REPLICAS            IMAGE               PORTS
rl39orkjrie1        helloworld          replicated          4/4                 alpine:latest
gerard@shangrila:~$ docker service ps helloworld
ID                  NAME                IMAGE               NODE                DESIRED STATE       CURRENT STATE            ERROR               PORTS
j26p1q1hgvtt        helloworld.1        alpine:latest       shangrila           Running             Running 5 seconds ago
q5xeb2bftqlq         \_ helloworld.1    alpine:latest       eldorado            Shutdown            Running 24 seconds ago
6ruk3h9lvzom        helloworld.2        alpine:latest       shangrila           Running             Running 3 minutes ago
j2xuo9pvfoeu        helloworld.3        alpine:latest       arcadia             Running             Running 3 minutes ago
t2emtl7m6r3b        helloworld.4        alpine:latest       arcadia             Running             Running 3 minutes ago
gerard@shangrila:~$
```

El contenedor *helloworld.1* debería estar en **eldorado**, pero como lo hemos apagado, se ha creado otro en su sustitución en **shangrila**.

Levantamos de nuevo **eldorado**, y se vuelve al estado original, parando la instáncia de emergencia en **shangrila**:

```bash
gerard@shangrila:~$ docker node ls
ID                            HOSTNAME            STATUS              AVAILABILITY        MANAGER STATUS
5p0wbl6rhvs5oo461xsmxhph4     eldorado            Ready               Active
rtmzvsbndn4ox5mhzsgu2xi81 *   shangrila           Ready               Active              Leader
su20j7s0itgssfcm8x5whz8o8     arcadia             Ready               Active
gerard@shangrila:~$ docker service ls
ID                  NAME                MODE                REPLICAS            IMAGE               PORTS
rl39orkjrie1        helloworld          replicated          4/4                 alpine:latest
gerard@shangrila:~$ docker service ps helloworld
ID                  NAME                IMAGE               NODE                DESIRED STATE       CURRENT STATE             ERROR               PORTS
j26p1q1hgvtt        helloworld.1        alpine:latest       shangrila           Running             Running 3 minutes ago
q5xeb2bftqlq         \_ helloworld.1    alpine:latest       eldorado            Shutdown            Shutdown 24 seconds ago
6ruk3h9lvzom        helloworld.2        alpine:latest       shangrila           Running             Running 7 minutes ago
j2xuo9pvfoeu        helloworld.3        alpine:latest       arcadia             Running             Running 7 minutes ago
t2emtl7m6r3b        helloworld.4        alpine:latest       arcadia             Running             Running 7 minutes ago
gerard@shangrila:~$
```

Ahora, ya podemos eliminar este servicio de test, puesto que no lo vamos a necesitar más.

```bash
gerard@shangrila:~$ docker service rm helloworld
helloworld
gerard@shangrila:~$ docker service ls
ID                  NAME                MODE                REPLICAS            IMAGE               PORTS
gerard@shangrila:~$ docker service ps helloworld
no such services: helloworld
gerard@shangrila:~$
```

## Publicando servicios

Si deseamos exponer nuestro servicio, necesitamos indicarlo con el *flag* `--publish`, exactamente igual que el *flag* `-p` en **docker-engine**.

Veamos un ejemplo. Tenemos una imagen *sirrtea/myhostname* que responde por HTTP en el puerto 8080, indicando el nombre del *host* (el contenedor) en el que se ejecuta.

Creamos el servicio con 2 replicas, y publicando el puerto 8080 del contenedor en el 8888 de los *hosts* del *cluster*:

```bash
gerard@shangrila:~$ docker service create --replicas 2 --name myhostname --publish 8888:8080 sirrtea/myhostname
c0pvrkvf233odc1z9piitf1wa
Since --detach=false was not specified, tasks will be created in the background.
In a future release, --detach=false will become the default.
gerard@shangrila:~$ docker service ls
ID                  NAME                MODE                REPLICAS            IMAGE                       PORTS
c0pvrkvf233o        myhostname          replicated          2/2                 sirrtea/myhostname:latest   *:8888->8080/tcp
gerard@shangrila:~$ docker service ps myhostname
ID                  NAME                IMAGE                       NODE                DESIRED STATE       CURRENT STATE           ERROR               PORTS
xnljno3f285w        myhostname.1        sirrtea/myhostname:latest   shangrila           Running             Running 3 seconds ago
rivqb4uqqiwl        myhostname.2        sirrtea/myhostname:latest   eldorado            Running             Running 3 seconds ago
gerard@shangrila:~$
```

De ahora en adelante, podemos acceder a **cualquier nodo** en el puerto 8888 y obtendremos un balanceo de peticiones entre todos los contenedores que conforman el servicio.

Es importante recalcar que, aunque el servicio solo tiene contenedores en **shangrila** y en **eldorado**, también vamos a obtener respuesta del balanceador en **arcadia**.

En el caso de mi *cluster*, no tengo resolución DNS, así que os resumo las IPs de mi *cluster*:

* **shangrila** &rarr; 192.168.56.2
* **arcadia** &rarr; 192.168.56.3
* **eldorado** &rarr; 192.168.56.4

Ahora nos podemos hacer una idea de donde estoy lanzando las siguientes conexiones...

```bash
gerard@shangrila:~$ curl http://192.168.56.2:8888/
Hello world from <em>9294907313e7</em>
gerard@shangrila:~$ curl http://192.168.56.2:8888/
Hello world from <em>5295009a7737</em>
gerard@shangrila:~$ curl http://192.168.56.3:8888/
Hello world from <em>9294907313e7</em>
gerard@shangrila:~$ curl http://192.168.56.3:8888/
Hello world from <em>5295009a7737</em>
gerard@shangrila:~$ curl http://192.168.56.4:8888/
Hello world from <em>9294907313e7</em>
gerard@shangrila:~$ curl http://192.168.56.4:8888/
Hello world from <em>5295009a7737</em>
gerard@shangrila:~$
```

En este caso concreto, el *hostname* 9294907313e7 es el de la instancia de **shangrila** y el *hostname* 5295009a7737 corresponde a la intancia de **eldorado**. Esto se puede comprobar fácilmente mirando en los nodos que albergan los contenedores.

```bash
gerard@shangrila:~$ docker ps
CONTAINER ID        IMAGE                       COMMAND                  CREATED             STATUS              PORTS               NAMES
9294907313e7        sirrtea/myhostname:latest   "/usr/bin/gunicorn..."   25 minutes ago      Up 25 minutes                           myhostname.1.xnljno3f285wkfl0xyfmb0xek
gerard@shangrila:~$ docker inspect myhostname.1.xnljno3f285wkfl0xyfmb0xek | grep Hostname
        "HostnamePath": "/var/lib/docker/containers/9294907313e78d46193dabb36eee2b6eb422208675812c77fdef96139cb0e62b/hostname",
            "Hostname": "9294907313e7",
gerard@shangrila:~$

gerard@eldorado:~$ docker ps
CONTAINER ID        IMAGE                       COMMAND                  CREATED             STATUS              PORTS               NAMES
5295009a7737        sirrtea/myhostname:latest   "/usr/bin/gunicorn..."   25 minutes ago      Up 25 minutes                           myhostname.2.rivqb4uqqiwlbla8716foavzy
gerard@eldorado:~$ docker inspect myhostname.2.rivqb4uqqiwlbla8716foavzy | grep Hostname
        "HostnamePath": "/var/lib/docker/containers/5295009a7737ef709260ea984b9c7720d6bd752a40d8305e86c2649c0ab2af10/hostname",
            "Hostname": "5295009a7737",
gerard@eldorado:~$
```

La recomendación oficial para tener tener una única IP consiste en poner delante de todos los nodos un balanceador, especialmente uno que pueda descartar nodos parados como puede ser **HAProxy**.

Con eso ganamos balanceo entre todos los nodos del *cluster* que queden vivos y, en caso de alcanzar alguno, un balanceo entre todas las instancias de un servicio dado.
