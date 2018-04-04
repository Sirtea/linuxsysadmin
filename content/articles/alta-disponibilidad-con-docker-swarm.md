Title: Alta disponibilidad con Docker Swarm
Slug: alta-disponibilidad-con-docker-swarm
Date: 2018-04-09 10:00
Category: Sistemas
Tags: docker, swarm, cluster, alta disponibilidad



He visto muchos artículos por internet que hacen maravillas para tener un *cluster* de **Docker Swarm** funcional. Puede que en versiones anteriores fuera así, pero cada vez se ha simplificado más el *setup* para alinearse con la filosofía de la simplicidad, frente a otras soluciones más completas, pero más complejas.

Hoy vamos a mostrar como conseguir alta disponibilidad en un *cluster* de **docker swarm**, de forma que si se cae un *manager*, otro asume su lugar y reestructura los servicios para continuar cumpliendo las especificaciones indicadas.

Para hacerlo, vamos a disponer de 5 máquinas, todas con **Docker** instalado, siendo irrelevante el sistema operativo, incluso mezclado:

* **swarm1** &rarr; 10.0.0.2 (será un *manager*)
* **swarm2** &rarr; 10.0.0.3 (será un *manager*)
* **swarm3** &rarr; 10.0.0.4 (será un *manager*)
* **swarm4** &rarr; 10.0.0.5 (será un *worker*)
* **swarm5** &rarr; 10.0.0.6 (será un *worker*)

Es importante recalcar que el *cluster* se rige por un protocolo de *gossip* tipo **Raft**, lo que significa que necesita que más de la mitad de los *managers* estén funcionales, con lo que un número impar de ellos es lo ideal; pondremos 3 para este ejemplo.

## Creación del cluster

Como todo *cluster* de **Docker Swarm**, empezamos inicializando un solo nodo, que va a ser el *manager* y de paso, el *leader* (el *manager* que manda).

```bash
gerard@swarm1:~$ docker swarm init
Swarm initialized: current node (t2x1d9ep99ff5o7ggf0f7dgzh) is now a manager.

To add a worker to this swarm, run the following command:

    docker swarm join --token SWMTKN-1-221kzb5ajbg3p9cu7cnxj0zp8fper4dbnzn9ntjkjxrs0mamoz-avftdi8c5t7l4y59zcjq4k6r4 10.0.0.2:2377

To add a manager to this swarm, run 'docker swarm join-token manager' and follow the instructions.

gerard@swarm1:~$
```

Podemos comprobar que ya tenemos un *cluster* con un solo nodo, que es *manager* y *leader*.

```bash
gerard@swarm1:~$ docker node ls
ID                            HOSTNAME            STATUS              AVAILABILITY        MANAGER STATUS
t2x1d9ep99ff5o7ggf0f7dgzh *   swarm1              Ready               Active              Leader
gerard@swarm1:~$
```

Para añadir nodos, solo hace falta hacer un `docker swarm join`, y su rol va a depender del *token* con el que nos unamos. El comando `docker swarm init` ya nos indicó el *token* para un *worker* y como sacar el *token* para un *manager*. Saquemos los dos de nuevo:

```bash
gerard@swarm1:~$ docker swarm join-token manager
To add a manager to this swarm, run the following command:

    docker swarm join --token SWMTKN-1-221kzb5ajbg3p9cu7cnxj0zp8fper4dbnzn9ntjkjxrs0mamoz-agq9fp4a86ahs8ll7oa2z56j7 10.0.0.2:2377

gerard@swarm1:~$ docker swarm join-token worker
To add a worker to this swarm, run the following command:

    docker swarm join --token SWMTKN-1-221kzb5ajbg3p9cu7cnxj0zp8fper4dbnzn9ntjkjxrs0mamoz-avftdi8c5t7l4y59zcjq4k6r4 10.0.0.2:2377

gerard@swarm1:~$
```

Solo necesitamos entrar en cada uno de los nodos y lanzar el comando suministrado. En este caso vamos a lanzar el comando para crear un *manager* en **swarm2** y **swarm3**, mientras que haremos *workers* de **swarm4** y **swarm5**.

```bash
gerard@swarm2:~$ docker swarm join --token SWMTKN-1-221kzb5ajbg3p9cu7cnxj0zp8fper4dbnzn9ntjkjxrs0mamoz-agq9fp4a86ahs8ll7oa2z56j7 10.0.0.2:2377
This node joined a swarm as a manager.
gerard@swarm2:~$
```

```bash
gerard@swarm3:~$ docker swarm join --token SWMTKN-1-221kzb5ajbg3p9cu7cnxj0zp8fper4dbnzn9ntjkjxrs0mamoz-agq9fp4a86ahs8ll7oa2z56j7 10.0.0.2:2377
This node joined a swarm as a manager.
gerard@swarm3:~$
```

```bash
gerard@swarm4:~$ docker swarm join --token SWMTKN-1-221kzb5ajbg3p9cu7cnxj0zp8fper4dbnzn9ntjkjxrs0mamoz-avftdi8c5t7l4y59zcjq4k6r4 10.0.0.2:2377
This node joined a swarm as a worker.
gerard@swarm4:~$
```

```bash
gerard@swarm5:~$ docker swarm join --token SWMTKN-1-221kzb5ajbg3p9cu7cnxj0zp8fper4dbnzn9ntjkjxrs0mamoz-avftdi8c5t7l4y59zcjq4k6r4 10.0.0.2:2377
This node joined a swarm as a worker.
gerard@swarm5:~$
```

Y con esto tenemos el *cluster* completo:

```bash
gerard@swarm1:~$ docker node ls
ID                            HOSTNAME            STATUS              AVAILABILITY        MANAGER STATUS
t2x1d9ep99ff5o7ggf0f7dgzh *   swarm1              Ready               Active              Leader
p8td0udza1chfy3ehb01wkm7p     swarm2              Ready               Active              Reachable
st9wv2k1fdmocam3dpmnas20c     swarm3              Ready               Active              Reachable
0t7m80of6t0nwo8zwn7vupwix     swarm4              Ready               Active
8sl99fhp1hnc3bt620fxdnn6y     swarm5              Ready               Active
gerard@swarm1:~$
```

Es importante recalcar que, aunque hay 3 *managers*, solo uno es *leader*, y es el que lleva la voz cantante del *cluster*.

## Pruebas de alta disponibilidad

Ya vimos en [otro artículo]({filename}/articles/uso-basico-de-un-cluster-docker-swarm.md) que en caso de caída de un *worker*, el *manager* se encarga de recolocar los contenedores para seguir ofreciendo el servicio. Así que nos vamos a limitar a tirar *managers*, que es lo que era vulnerable en el *cluster* anterior.

Empezaremos tirando **swarm1** que es un *manager* y un *leader*; esto es lo que queda:

```bash
gerard@swarm2:~$ docker node ls
ID                            HOSTNAME            STATUS              AVAILABILITY        MANAGER STATUS
t2x1d9ep99ff5o7ggf0f7dgzh     swarm1              Unknown             Active              Unreachable
p8td0udza1chfy3ehb01wkm7p *   swarm2              Ready               Active              Reachable
st9wv2k1fdmocam3dpmnas20c     swarm3              Ready               Active              Leader
0t7m80of6t0nwo8zwn7vupwix     swarm4              Ready               Active
8sl99fhp1hnc3bt620fxdnn6y     swarm5              Ready               Active
gerard@swarm2:~$
```

Sin sorpresas, **swarm1** es dado por *unreachable* y no pasa nada, más allá de elegir otro *leader* para que siga manteniendo el estado del *cluster*.

Intentemos ahora quitar otro de los *managers*, lo que haría que solo quedara uno:

```bash
gerard@swarm3:~$ docker swarm leave
Error response from daemon: You are attempting to leave the swarm on a node that is participating as a manager. Removing this node leaves 1 managers out of 3. Without a Raft quorum your swarm will be inaccessible. The only way to restore a swarm that has lost consensus is to reinitialize it with `--force-new-cluster`. Use `--force` to suppress this message.
gerard@swarm3:~$
```

Eso no nos lo deja hacer, ya que entonces no tendríamos *quorum* y meteríamos la pata a lo grande. Eso es lo mismo que va a pasar si apagamos el servidor.

Para tener *quorum* con 3 *managers*, necesitamos que **más de la mitad** estén funcionales; esto nos obliga a mantener más de 1.5 funcionales, dos en este caso. Si hay previsiones de que se caigan o se paren más, habría que tener más *managers*, para que la tolerancia a nodos caídos fuera superior.

* **1 manager** &rarr; quorum > 0.5, necesitamos = 1, tolerancia = 0
* **2 managers** &rarr; quorum > 1, necesitamos = 2, tolerancia = 0
* **3 managers** &rarr; quorum > 1.5, necesitamos = 2, tolerancia = 1
* **5 managers** &rarr; quorum > 2.5, necesitamos = 3, tolerancia = 2

Solo nos queda ver que en caso de recuperación del nodo **swarm1**, el *cluster* lo reconoce y todo vuelve a la normalidad, excepto que no se desbanca al nuevo *leader*.

```bash
gerard@swarm2:~$ docker node ls
ID                            HOSTNAME            STATUS              AVAILABILITY        MANAGER STATUS
t2x1d9ep99ff5o7ggf0f7dgzh     swarm1              Ready               Active              Reachable
p8td0udza1chfy3ehb01wkm7p *   swarm2              Ready               Active              Reachable
st9wv2k1fdmocam3dpmnas20c     swarm3              Ready               Active              Leader
0t7m80of6t0nwo8zwn7vupwix     swarm4              Ready               Active
8sl99fhp1hnc3bt620fxdnn6y     swarm5              Ready               Active
gerard@swarm2:~$
```
