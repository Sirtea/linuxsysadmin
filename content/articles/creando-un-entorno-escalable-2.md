Title: Creando un entorno escalable (II)
Slug: creando-un-entorno-escalable-2
Date: 2016-03-07 08:00
Category: Sistemas
Tags: linux, debian, jessie, mongodb, replica set, systemd, firehol
Series: Creando un entorno escalable



Seguimos con la serie de montar un entorno escalable. Tras explicar en el primer artículo lo que vamos a montar, seguimos con ello. En este artículo vamos a montar un *cluster* de bases de datos; será **mongodb** porque la aplicación lo requiere y usará la topología de un **replica set**.

Este artículo se basa enormemente en [otro artículo]({filename}/articles/construyendo-una-replica-set-en-mongodb.md) que ya publicamos, al que vamos a añadir algunas mejoras reflejadas en otros.

Como ya vimos en el artículo referido, solo necesitamos levantar un proceso *mongod* en cada una de las máquinas, para posteriormente casarlos entre sí.

## Levantando los procesos de mongodb

Este punto se repite en las máquinas que van a formar la **replica set**, que son *mongo1*, *mongo2* y *backoffice*. Vamos a seguir solamente una de ellas; el resto son análogas.

Crearemos una estructura en */opt/* para alojar los binarios, las configuraciones, los datos y los logs.

```bash
root@mongo1:~# mkdir -p /opt/mongodb/{bin,conf,data,logs}
root@mongo1:~#
```

En la carpeta de binarios vamos a poner el único que se necesita: el *mongod*. Lo podemos sacar descomprimiendo el 
fichero comprimido *.tar.gz* de la página de descargas de **mongodb**. En nuestro caso concreto, lo he sacado de [https://fastdl.mongodb.org/linux/mongodb-linux-i686-3.2.3.tgz](https://fastdl.mongodb.org/linux/mongodb-linux-i686-3.2.3.tgz).

```bash
root@mongo1:~# cp mongodb-linux-i686-3.2.3/bin/mongod /opt/mongodb/bin/
root@mongo1:~#
```

Ponemos un fichero de configuración para la instancia que queremos correr. Esta configuración puede variar mucho, pero un ejemplo básico para salir del paso con una máquina de 32 bits (que no soportan *WiredTiger*) podría ser:

```bash
root@mongo1:~# cat /opt/mongodb/conf/mongo.conf
systemLog:
    path: /opt/mongodb/logs/mongo.log
    logAppend: true
    destination: file

net:
    port: 27017
    bindIp: 0.0.0.0

storage:
    dbPath: /opt/mongodb/data/
    engine: mmapv1
    mmapv1:
        smallFiles: true

replication:
    replSetName: rs
root@mongo1:~#
```

**Truco**: Es un buen momento para montar un sistema de ficheros alternativo para almacenar los datos, sea poner [LVM]({filename}/articles/lvm-logical-volume-manager.md) (para tener crecimiento dinámico o [snapshots]({filename}/articles/haciendo-snapshots-con-lvm.md), sea un [RAID]({filename}/articles/construyendo-un-raid-10-en-linux.md) (por ejemplo para tener alto rendimiento y/o replicación de datos), o incluso ambos.

Cumpliendo con una política de seguridad básica, vamos a crear un usuario de sistema para correr el proceso.

```bash
root@mongo1:~# useradd -s /usr/sbin/nologin -r -M mongo -d /opt/mongodb/
root@mongo1:~#
```

Le damos la propiedad de toda la estructura de **mongodb**, para ahorrarnos problemas de permisos.

```bash
root@mongo1:~# chown -R mongo:mongo /opt/mongodb/
root@mongo1:~#
```

Y ya como resumen, ponemos una salida para ver como nos queda la estructura:

```bash
root@mongo1:~# tree /opt/mongodb/
/opt/mongodb/
├── bin
│   └── mongod
├── conf
│   └── mongo.conf
├── data
└── logs

4 directories, 2 files
root@mongo1:~#
```

El último paso consiste en crear una *unit* en **systemd** (o un *init script*, dependiendo de la distribución usada; de hecho, cada máquina puede ir con una distribución distinta).

```bash
root@mongo1:~# cat /etc/systemd/system/mongo.service
[Unit]
Description=MongoDB

[Service]
User=mongo
LimitFSIZE=infinity
LimitCPU=infinity
LimitAS=infinity
LimitNOFILE=64000
LimitNPROC=64000
ExecStartPre=/bin/rm -f /opt/mongodb/data/mongod.lock
ExecStart=/opt/mongodb/bin/mongod -f /opt/mongodb/conf/mongo.conf

[Install]
WantedBy=multi-user.target
root@mongo1:~#
```

Lo activamos para que se levante solo en los siguientes arranques, y lo levantamos para la sesión actual.

```bash
root@mongo1:~# systemctl enable mongo
Created symlink from /etc/systemd/system/multi-user.target.wants/mongo.service to /etc/systemd/system/mongo.service.
root@mongo1:~# systemctl start mongo
root@mongo1:~#
```

Repetid este paso en las otras máquinas de **mongodb**.

## Consideraciones de seguridad

Para que una **replica set** funcione como debe, todos los procesos deben comunicarse entre sí. Como los hemos puesto en el mismo puerto, podemos agruparlo todo en una sola regla.

Como en nuestro caso estamos virtualizando con **LXC**, vamos a controlar el tráfico con el **firehol** de la máquina anfitriona.

```bash
...
root@lxc:~# cat /etc/firehol/firehol.conf
mongo_servers="10.0.0.5 10.0.0.6 10.0.0.7"
...  
router internal inface lxc0 outface lxc0
    route custom mongodb tcp/27017 default accept src "$mongo_servers" dst "$mongo_servers"
...
root@lxc:~#
```

Acordaos de reiniciar **firehol**.

## Atando la replica set

Este paso se ejecuta en una sola máquina, que va a reproducir los cambios a las demás, por efecto de la **replica set**. Por ejemplo, lo hago en *mongo1*, por hacer alguna.

Entramos en el *mongo shell*, desde donde lanzaremos el resto de comandos.

```bash
root@mongo1:~# ./mongodb-linux-i686-3.2.3/bin/mongo
MongoDB shell version: 3.2.3
connecting to: test
Welcome to the MongoDB shell.
For interactive help, type "help".
...
> 
```

Siguiendo los pasos estándares, creamos una configuración vacía en la máquina elegida, y añadimos las otras dos. Tened en cuenta que la máquina *backoffice* se declara como un árbitro, por decisión de diseño.

```bash
> rs.initiate()
{
        "info2" : "no configuration specified. Using a default configuration for the set",
        "me" : "mongo1:27017",
        "ok" : 1
}
rs:SECONDARY> rs.add("mongo2:27017")
{ "ok" : 1 }
rs:PRIMARY> rs.addArb("backoffice:27017")
{ "ok" : 1 }
rs:PRIMARY>
```

Podemos verificar que todo está bien mediante el comando *rs.status()*, como sigue:

```bash
rs:PRIMARY> rs.status()
{
        "set" : "rs",
...  
        "members" : [
                {
...  
                        "name" : "mongo1:27017",
                        "stateStr" : "PRIMARY",
...  
                },
                {
...  
                        "name" : "mongo2:27017",
                        "stateStr" : "SECONDARY",
...  
                },
                {
...  
                        "name" : "backoffice:27017",
                        "stateStr" : "ARBITER",
...  
                }
        ],
        "ok" : 1
}
rs:PRIMARY>
```

Y salimos del *mongo shell*, que ya no necesitamos; las aplicaciones de *backend* y de *backoffice* ya incluyen una librería para conectarse por sí mismos.

```bash
rs:PRIMARY> exit
bye
root@mongo1:~#
```

Todo lo que queda en */root/* es innecesario y se puede borrar. De todas formas podemos dejar el resto de binarios en */opt/mongodb/* en alguna de las máquinas por si acaso.

***El siguiente paso va a ser montar los servidores de aplicaciones en los backends y en el backoffice***
