---
title: "Montando un cluster de docker con docker swarm"
slug: "montando-un-cluster-de-docker-con-docker-swarm"
date: 2017-10-30
categories: ['Sistemas']
tags: ['docker', 'swarm', 'cluster']
---

Usar **docker** en nuestro dia a dia es muy interesante y tiene un montón de aplicaciones prácticas; sin embargo no es la mejor opción confiar en un único servidor en producción. Para tener alta disponibilidad y alto renidmiento podemos montar un cluster, como por ejemplo su implementación oficial, **docker swarm**.<!--more-->

## Preparando los servidores

Vamos a seguir el tutorial mismo de la página de docker, que nos invita a crear 3 servidores, siendo uno el *manager* y el resto *nodos*. Así pues, nuestro cluster se va a componer inicialmente de 3 servidores:

* **shangrila** &rarr; nuestro manager, con IP 192.168.56.2
* **arcadia** &rarr; el nodo 1, con IP 192.168.56.3
* **eldorado** &rarr; el nodo 2, con IP 192.168.56.4

Para ello vamos a preparar tres máquinas que son las que van a componer el cluster de **Docker**. Las máquinas solo necesitan **docker** y me he guiado por [este artículo]({{< relref "/articles/2017/07/montando-un-servidor-docker-con-debian-stretch.md" >}}). Adicionalmente, he instalado el servicio **NTP** siguiendo [este otro artículo]({{< relref "/articles/2017/10/un-servicio-casi-imprescindible-ntp.md" >}}), aunque esto es opcional.

Un punto importante a tener en cuenta es que las máquinas deben tener [conectividad con el manager](https://docs.docker.com/engine/swarm/swarm-tutorial/#the-ip-address-of-the-manager-machine), y deben poder accederse entre ellas por [algunos puertos](https://docs.docker.com/engine/swarm/swarm-tutorial/#open-protocols-and-ports-between-the-hosts).

## Creando el manager

Entramos por SSH en el manager (en nuestro caso **shangrila**) y lanzamos el comando `docker swarm init`. Esto nos va a crear un cluster con solamente un *manager* y sin *nodos*.

```bash
gerard@shangrila:~$ docker swarm init --advertise-addr 192.168.56.2
Swarm initialized: current node (rtmzvsbndn4ox5mhzsgu2xi81) is now a manager.

To add a worker to this swarm, run the following command:

    docker swarm join --token SWMTKN-1-09ebvbcbqjttt3o6ssqfnkb1n4xuzf1e1jildujhkh7dpb6iaq-0i6smvy5g75h2mn82t8kv4ptd 192.168.56.2:2377

To add a manager to this swarm, run 'docker swarm join-token manager' and follow the instructions.

gerard@shangrila:~$
```

También hemos añadido el flag `--advertise-addr` para indicar la IP del *manager* que se va a usar para las comunicaciones con los diferentes nodos.

Ahora ya tenemos un cluster de *docker swarm* operativo, aunque al no tener *nodos*, no podemos usar algunos de los comandos, que son multinodo.

Podemos ver los nodos del cluster y el estado del mismo con unos pocos comandos:

```bash
gerard@shangrila:~$ docker info
...
Swarm: active
 NodeID: rtmzvsbndn4ox5mhzsgu2xi81
 Is Manager: true
 ClusterID: krknl2v0llpyczyqg1ihi250d
 Managers: 1
 Nodes: 1
 Orchestration:
  Task History Retention Limit: 5
 Raft:
  Snapshot Interval: 10000
  Number of Old Snapshots to Retain: 0
  Heartbeat Tick: 1
  Election Tick: 3
 Dispatcher:
  Heartbeat Period: 5 seconds
 CA Configuration:
  Expiry Duration: 3 months
  Force Rotate: 0
 Root Rotation In Progress: false
 Node Address: 192.168.56.2
 Manager Addresses:
  192.168.56.2:2377
...
gerard@shangrila:~$ docker node ls
ID                            HOSTNAME            STATUS              AVAILABILITY        MANAGER STATUS
rtmzvsbndn4ox5mhzsgu2xi81 *   shangrila           Ready               Active              Leader
gerard@shangrila:~$
```

## Añadiendo nodos al cluster

Para añadir un *nodo* en el cluster, solo tenemos que entrar en ese nodo y lanzar el comando que nos sugirió el `docker init`. Si no nos acordamos, siempre podemos pedir que nos lo repita:

```bash
gerard@shangrila:~$ docker swarm join-token worker
To add a worker to this swarm, run the following command:

    docker swarm join --token SWMTKN-1-09ebvbcbqjttt3o6ssqfnkb1n4xuzf1e1jildujhkh7dpb6iaq-0i6smvy5g75h2mn82t8kv4ptd 192.168.56.2:2377

gerard@shangrila:~$
```

Así tal cual, lanzamos el comando en cualquier *nodo* que deseemos preparar ahora. No es necesario poner todos los *nodos* en este momento, pudiendo añadir *nodos* en un futuro, tal como nuestro cluster lo vaya necesitando.

Lanzamos en **arcadia**:

```bash
gerard@arcadia:~$ docker swarm join --token SWMTKN-1-09ebvbcbqjttt3o6ssqfnkb1n4xuzf1e1jildujhkh7dpb6iaq-0i6smvy5g75h2mn82t8kv4ptd 192.168.56.2:2377
This node joined a swarm as a worker.
gerard@arcadia:~$
```

Y lanzamos en **eldorado**:

```bash
gerard@eldorado:~$ docker swarm join --token SWMTKN-1-09ebvbcbqjttt3o6ssqfnkb1n4xuzf1e1jildujhkh7dpb6iaq-0i6smvy5g75h2mn82t8kv4ptd 192.168.56.2:2377
This node joined a swarm as a worker.
gerard@eldorado:~$
```

Y podemos comprobar de nuevo el estado de nuestro cluster:

```bash
gerard@shangrila:~$ docker info
...
Swarm: active
 NodeID: rtmzvsbndn4ox5mhzsgu2xi81
 Is Manager: true
 ClusterID: krknl2v0llpyczyqg1ihi250d
 Managers: 1
 Nodes: 3
 Orchestration:
  Task History Retention Limit: 5
 Raft:
  Snapshot Interval: 10000
  Number of Old Snapshots to Retain: 0
  Heartbeat Tick: 1
  Election Tick: 3
 Dispatcher:
  Heartbeat Period: 5 seconds
 CA Configuration:
  Expiry Duration: 3 months
  Force Rotate: 0
 Root Rotation In Progress: false
 Node Address: 192.168.56.2
 Manager Addresses:
  192.168.56.2:2377
...
gerard@shangrila:~$ docker node ls
ID                            HOSTNAME            STATUS              AVAILABILITY        MANAGER STATUS
5p0wbl6rhvs5oo461xsmxhph4     eldorado            Ready               Active
rtmzvsbndn4ox5mhzsgu2xi81 *   shangrila           Ready               Active              Leader
su20j7s0itgssfcm8x5whz8o8     arcadia             Ready               Active
gerard@shangrila:~$
```

**AVISO:** Tened en cuenta que los comandos de estado del cluster solo se pueden lanzar en un *manager*.

Y con esto tenemos montado nuestro cluster.
