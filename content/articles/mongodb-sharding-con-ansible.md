Title: MongoDB sharding con ansible
Slug: mongodb-sharding-con-ansible
Date: 2016-05-02
Category: Sistemas
Tags: linux, debian, jessie, mongodb, replica set, sharding, ansible, playbook, systemd



Como ya vimos en un artículo anterior, los *replica sets* nos ofrecen alta disponibilidad para nuestros despliegues de **mongodb**. Sin embargo, algunas veces, necesitamos que nuestro *cluster* ofrezca alto rendimiento, y esto se consigue mediante *sharding*. Como no queremos renunciar a la alta disponibilidad, podemos aplicar ambas; hoy explicamos como.

El mecanismo de *sharding* es bastante simple: tenemos nuestros datos repartidos entre uno o mas *shards*, que se van a repartir los datos del *cluster*. Para mantener un control de donde están los datos, también vamos a necesitar unos procesos especiales llamados *config servers*. Finalmente, habrá que poner algunos procesos *mongos* que son unos *proxies* al *cluster* y sirven para ocultar la complejidad del mismo.

## Visión del conjunto

Hay que decir que el mecanismo de *sharding* permite poner y quitar *shards* a *posteriori*, igual que con los procesos *mongos*, pero para empezar vamos a necesitar una arquitectura inicial que es lo que vamos a montar.

Para empezar se ha decidido por un *cluster* de 3 *shards*, siendo cada uno de ellos un *replica set* de dos nodos de datos y un árbitro cada uno. Usaremos la cantidad de *config servers* que se recomienda en la documentación oficial.

Así pues, y tras elegir nombres para los *shards*, podemos pintar un esquema de nuestro *cluster*.

![Arquitectura lógica]({static}/images/sharding_arquitectura_logica.jpg)

Para repartir los procesos entre las máquinas, hay dos reglas que hay que respetar a rajatabla:

* Los procesos de datos necesitan una máquina propia, para que no se disputen los recursos de disco y memoria.
* No hay que poner nunca dos o mas procesos de cada *shard*, ya que la no disponibilidad de la máquina supondría la pérdida de la mayoría de las *replica sets*.

El resto de procesos pueden compartir servidor con los de datos. Hay muchas formas de cumplir con las dos reglas, por ejemplo, la que vamos a montar:

![Arquitectura física]({static}/images/sharding_arquitectura_fisica.jpg)

## Ansible al rescate

Debido a la gran cantidad de procesos que hay que levantar, se ha decidido por automatizar su despliegue mediante **ansible**. El proceso es bastante similar a [otro de nuestros artículos]({filename}/articles/construyendo-una-replica-set-en-mongodb.md).

Se ha utilizado el mecanismo de **roles** de **ansible**, para poder desplegar todos los procesos del mismo tipo; el detalle es que se han usado los parámetros en los **roles** para los cambios menores. Si queréis intentarlo o entender como funcionan los despliegues, podéis encontrar los **playbooks** [aquí]({static}/downloads/sharding_playbooks.tar.gz).

El fichero comprimido no incluye los binarios de **mongodb** para reducir tamaño, así que hay que añadirlos en las respectivas carpetas *files*. Tras descomprimir el fichero *.tar.gz* y poner los binarios ausentes, nos debería quedar algo como esto:

```bash
root@ansible:~# tree
.
├── aquila_shard.yaml
├── clients.yaml
├── config_servers.yaml
├── cygnus_shard.yaml
├── hosts.yaml
├── lyra_shard.yaml
├── mongos_servers.yaml
└── roles
    ├── client
    │   ├── files
    │   │   └── mongo
    │   └── tasks
    │       └── main.yaml
    ├── config
    │   ├── meta
    │   │   └── main.yaml
    │   ├── tasks
    │   │   └── main.yaml
    │   └── templates
    │       ├── config.conf
    │       └── config.service
    ├── mongod
    │   ├── files
    │   │   └── mongod
    │   └── tasks
    │       └── main.yaml
    ├── mongos
    │   ├── files
    │   │   └── mongos
    │   ├── tasks
    │   │   └── main.yaml
    │   └── templates
    │       ├── mongos.conf
    │       └── mongos.service
    └── shard
        ├── meta
        │   └── main.yaml
        ├── tasks
        │   └── main.yaml
        └── templates
            ├── shard.conf
            └── shard.service

19 directories, 23 files
root@ansible:~# 
```

## Preparación de las máquinas

De acuerdo con la arquitectura propuesta, vamos a necesitar 6 servidores para el *cluster*, que vamos a montar como contenedores LXC y, aunque no es lo ideal, nos vale como demostración. En la séptima máquina es donde tenemos las herramientas de configuración, en este caso, **ansible** y los **playbooks**.

```bash
root@lxc:~# lxc-ls -f
NAME     STATE    IPV4        IPV6  AUTOSTART
---------------------------------------------
ansible  RUNNING  10.0.0.254  -     NO
mongo01  RUNNING  10.0.0.2    -     NO
mongo02  RUNNING  10.0.0.3    -     NO
mongo03  RUNNING  10.0.0.4    -     NO
mongo04  RUNNING  10.0.0.5    -     NO
mongo05  RUNNING  10.0.0.6    -     NO
mongo06  RUNNING  10.0.0.7    -     NO
root@lxc:~#
```

Vamos a declarar todas las máquina usadas en el fichero *hosts* de **ansible**. Ya de paso, los vamos a catalogar en grupos, para que los **playbooks** se puedan lanzar a los grupos, indistintamente de los servidores que los formen.

```bash
root@ansible:~# cat ansible/etc/hosts
[mongo_servers]
10.0.0.2
10.0.0.3
10.0.0.4
10.0.0.5
10.0.0.6
10.0.0.7

[config_servers]
10.0.0.2
10.0.0.3
10.0.0.4

[aquila_shard_data]
10.0.0.2
10.0.0.5

[aquila_shard_arbiters]
10.0.0.6

[lyra_shard_data]
10.0.0.3
10.0.0.6

[lyra_shard_arbiters]
10.0.0.7

[cygnus_shard_data]
10.0.0.4
10.0.0.7

[cygnus_shard_arbiters]
10.0.0.5

[mongos_servers]
10.0.0.2

[clients]
10.0.0.2
root@ansible:~#
```

Por comodidad, vamos a referirnos a las máquinas por su nombre, y a falta de un servidor DNS adecuado, vamos a rellenar sus ficheros */etc/hosts*; para ello vamos a usar un **playbook** que se asegure que esas líneas están en el fichero.

```bash
root@ansible:~# ansible-playbook hosts.yaml

...

PLAY RECAP *********************************************************************
10.0.0.2                   : ok=6    changed=6    unreachable=0    failed=0
10.0.0.3                   : ok=6    changed=6    unreachable=0    failed=0
10.0.0.4                   : ok=6    changed=6    unreachable=0    failed=0
10.0.0.5                   : ok=6    changed=6    unreachable=0    failed=0
10.0.0.6                   : ok=6    changed=6    unreachable=0    failed=0
10.0.0.7                   : ok=6    changed=6    unreachable=0    failed=0

root@ansible:~#
```

## Los config servers

Los *config servers* son procesos **mongod** con una configuración concreta. El **playbook** se limita a crear una estructura en */opt/mongodb/* asegurándose que hay el binario **mongod**, la configuración, la carpeta de datos y la *unit* de **systemd** activa.

```bash
root@ansible:~# ansible-playbook config_servers.yaml

...

PLAY RECAP *********************************************************************
10.0.0.2                   : ok=7    changed=7    unreachable=0    failed=0
10.0.0.3                   : ok=7    changed=7    unreachable=0    failed=0
10.0.0.4                   : ok=7    changed=7    unreachable=0    failed=0

root@ansible:~#
```

## Un acceso al cluster

Para poder configurar el *cluster* y para un uso futuro, hemos decidido poner un proceso **mongos** y el binario **mongo** para poder acceder al *mongo shell*. Se ha optado por separar los **playbooks**; así se podrá utilizar para desplegarlos por separado en futuras máquinas que los puedan usar.

De hecho, la recomendación oficial es poner un **mongos** en cada *backend*, aunque no necesitan el binario **mongo** porque disponen de los *drivers* oficiales del lenguaje que utilicen.

Empezaremos desplegando los procesos **mongos** en donde toque (de momento solo en el servidor *mongo01*). Este **playbook** se limita a poner el binario **mongos** y su respectiva *unit* para **systemd**.

```bash
root@ansible:~# ansible-playbook mongos_servers.yaml

...

PLAY RECAP *********************************************************************
10.0.0.2                   : ok=6    changed=4    unreachable=0    failed=0

root@ansible:~#
```

Para nuestra comodidad, también vamos a desplegar el *mongo shell*. Este **playbook** se limita a poner el binario **mongo** en su sitio.

```bash
root@ansible:~# ansible-playbook clients.yaml

...

PLAY RECAP *********************************************************************
10.0.0.2                   : ok=3    changed=1    unreachable=0    failed=0

root@ansible:~#
```

## Los procesos de los shards

Tenemos 9 procesos de este tipo, así que los **roles** de **ansible** tienen un protagonismo especial. Los cambios entre los procesos son mínimos, y se pasan por parámetro para que el rol cree los ficheros necesarios a partir de una plantilla. El rol se encarga solamente de poner el binario **mongod** en */opt/mongodb/bin*, crear la carpeta de datos y configurar el servicio como una *unit* de **systemd**.

Se ha decidido separar los *shards* en diferentes **playbooks** para simplificar la creación de futuros nuevos *shards*; así pues, lanzamos el **playbook** para el primer *shard*:

```bash
root@ansible:~# ansible-playbook aquila_shard.yaml

...

PLAY RECAP *********************************************************************
10.0.0.2                   : ok=7    changed=4    unreachable=0    failed=0
10.0.0.5                   : ok=7    changed=7    unreachable=0    failed=0
10.0.0.6                   : ok=7    changed=7    unreachable=0    failed=0

root@ansible:~#
```

Acto seguido, lanzamos el **playbook** responsable de montar los procesos del segundo *shard*:

```bash
root@ansible:~# ansible-playbook lyra_shard.yaml

...

PLAY RECAP *********************************************************************
10.0.0.3                   : ok=7    changed=4    unreachable=0    failed=0
10.0.0.6                   : ok=7    changed=4    unreachable=0    failed=0
10.0.0.7                   : ok=7    changed=7    unreachable=0    failed=0

root@ansible:~#
```

Y finalmente, lanzamos el tercer **playbook** para desplegar los procesos del último *shard*:

```bash
root@ansible:~# ansible-playbook cygnus_shard.yaml

...

PLAY RECAP *********************************************************************
10.0.0.4                   : ok=7    changed=4    unreachable=0    failed=0
10.0.0.5                   : ok=7    changed=4    unreachable=0    failed=0
10.0.0.7                   : ok=7    changed=4    unreachable=0    failed=0

root@ansible:~#
```

## Atando los replica sets

El paso anterior nos ha dejado todos los procesos en funcionamiento, pero no hemos iniciado los *replica sets*. Para que funcionen como tal, tenemos que configurarlos uno por uno como ya sabemos hacer, usando *rs.status()* para verificar que ha quedado todo como debe.

Empezaremos con una máquina cualquiera del primer *shard*; la configuración se propagará al resto sin nuestra intervención.

```bash
root@mongo01:~# /opt/mongodb/bin/mongo --host 10.0.0.5 --port 27018
MongoDB shell version: 3.2.5
connecting to: 10.0.0.5:27018/test
...
> config = {
...     _id : "aquila",
...      members : [
...          {_id : 0, host : "mongo01:27018"},
...          {_id : 1, host : "mongo04:27018"},
...          {_id : 2, host : "mongo05:27020", arbiterOnly: true},
...      ]
... }
...
> rs.initiate(config)
{ "ok" : 1 }
aquila:OTHER> rs.status()
...
aquila:PRIMARY> exit
bye
root@mongo01:~#
```

Seguimos con el segundo *shard*, entrando en una de sus máquinas y lanzando el comando de configuración.

```bash
root@mongo01:~# /opt/mongodb/bin/mongo --host 10.0.0.6 --port 27018
MongoDB shell version: 3.2.5
connecting to: 10.0.0.6:27018/test
...
> config = {
...     _id : "lyra",
...      members : [
...          {_id : 0, host : "mongo02:27018"},
...          {_id : 1, host : "mongo05:27018"},
...          {_id : 2, host : "mongo06:27020", arbiterOnly: true},
...      ]
... }
...
> rs.initiate(config)
{ "ok" : 1 }
lyra:OTHER> rs.status()
...
lyra:PRIMARY> exit
bye
root@mongo01:~#
```

Y montamos el tercer *shard* desde una cualquiera de sus *replicas*.

```bash
root@mongo01:~# /opt/mongodb/bin/mongo --host 10.0.0.7 --port 27018
MongoDB shell version: 3.2.5
connecting to: 10.0.0.7:27018/test
...
> config = {
...     _id : "cygnus",
...      members : [
...          {_id : 0, host : "mongo03:27018"},
...          {_id : 1, host : "mongo06:27018"},
...          {_id : 2, host : "mongo04:27020", arbiterOnly: true},
...      ]
... }
...
> rs.initiate(config)
{ "ok" : 1 }
cygnus:OTHER> rs.status()
...
cygnus:PRIMARY> exit
bye
root@mongo01:~#
```

## Añadiendo los shards al cluster

Ahora tenemos un grupo de *config servers*, que forman un *cluster* de 0 *shards* (válido pero inútil, ya que no tenemos donde guardar los datos). También disponemos de 3 *replica sets* independientes, que se convertirán en los futuros *shards*. Solo falta asociar los *shards* al resto del *cluster*, mediante el comando *sh.addShard()*.

Para ello entramos en un **mongos** desde donde lanzaremos los comandos. De hecho, solo tenemos uno, en *mongo01*. Puesto que está en la misma máquina que el cliente **mongo** y corre en el puerto estándar 27017, no hace falta especificar ni el *host* ni el puerto.

```bash
root@mongo01:~# /opt/mongodb/bin/mongo
MongoDB shell version: 3.2.5
connecting to: test
...
mongos>
```

Veamos como está el cluster antes de añadir los *shards*:

```bash
mongos> printShardingStatus()
--- Sharding Status ---
  sharding version: {
        "_id" : 1,
        "minCompatibleVersion" : 5,
        "currentVersion" : 6,
        "clusterId" : ObjectId("571dd47adbda7a5a80047a5d")
}
  shards:
  active mongoses:
        "3.2.5" : 1
  balancer:
        Currently enabled:  yes
        Currently running:  no
        Failed balancer rounds in last 5 attempts:  0
        Migration Results for the last 24 hours:
                No recent migrations
  databases:

mongos>
```

Procedemos a lanzar el comando para añadir cada *shard*. Es interesante saber que el proceso **mongos** puede reconocer la forma de cada *replica set* a partir de cualquiera de sus procesos. Podemos dar la URL con una sola máquina, o con varias de ellas. Lo importante es que alguna de ellas esté levantada, para que el proceso **mongos** pueda descubrir el resto a partir de su configuración.

```bash
mongos> sh.addShard('aquila/mongo01:27018')
{ "shardAdded" : "aquila", "ok" : 1 }
mongos> sh.addShard('lyra/mongo02:27018,mongo05:27018,mongo06:27020')
{ "shardAdded" : "lyra", "ok" : 1 }
mongos> sh.addShard('cygnus/mongo06:27018')
{ "shardAdded" : "cygnus", "ok" : 1 }
mongos>
```

Después de añadir los *shards*, podemos ver como queda el *cluster* con una sola consulta.

```bash
mongos> printShardingStatus()
--- Sharding Status ---
  sharding version: {
        "_id" : 1,
        "minCompatibleVersion" : 5,
        "currentVersion" : 6,
        "clusterId" : ObjectId("571dd47adbda7a5a80047a5d")
}
  shards:
        {  "_id" : "aquila",  "host" : "aquila/mongo01:27018,mongo04:27018" }
        {  "_id" : "cygnus",  "host" : "cygnus/mongo03:27018,mongo06:27018" }
        {  "_id" : "lyra",  "host" : "lyra/mongo02:27018,mongo05:27018" }
  active mongoses:
        "3.2.5" : 1
  balancer:
        Currently enabled:  yes
        Currently running:  no
        Failed balancer rounds in last 5 attempts:  0
        Migration Results for the last 24 hours:
                No recent migrations
  databases:

mongos>
```

Y como todo funciona como debe, salimos del *mongo shell* para evitar meter la pata.

```bash
mongos> exit
bye
root@mongo01:~#
```

Y con esto, tenemos nuestro *cluster* listo y preparado para su uso.
