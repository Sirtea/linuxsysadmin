Title: Construyendo una replica set en mongodb
Slug: construyendo-una-replica-set-en-mongodb
Date: 2015-12-08 12:30
Category: Sistemas
Tags: linux, debian, jessie, mongodb, replica set, systemd



Muchas veces nos interesa obtener alta disponibilidad en los servicios que gestionamos. No hay nada mas desagradable que una llamada a las tantas de la noche porque se ha caído un nodo de una base de datos y no damos servicio. Para eso *mongodb* nos ofrece el mecanismo de replicación.

En este artículo vamos a montar una *replica set*, de forma que si se cayera un nodo de la base de datos, otro asumiría su rol, de forma que se seguiría dando servicio.

Nuestra *replica set* va a tener 3 nodos, que vamos a alojar en 3 máquinas distintas, de forma que la caída de una máquina afecte solamente a 1 proceso de *mongodb*. La caonfiguración de 3 nodos nos da una tolerancia a fallos de 1 máquina; mientras queden 2, el clúster va a seguir operativo.

## Descripción del entorno

Disponemos de 3 máquinas que vamos a llamar **mongo1**, **mongo2** y **mongo3**. Cada una funciona con un sistema operativo *Debian jessie* con *systemd* y cuenta 1 gb de disco y con 256 mb de memoria; para esta demostración no se necesita mas.

Como pequeño detalle, las máquinas se van referir entre ellas por nombre, pero como no me interesa poner una solución completa de *DNS*, he puesto en el fichero */etc/hosts* de todas las máquinas las equivalencias.

```bash
root@mongo1:~# grep mongo /etc/hosts
10.0.0.2	mongo1
10.0.0.3	mongo2
10.0.0.4	mongo3
root@mongo1:~# 
```

## Consideraciones de seguridad

Estas máquinas se comunican entre sí por el puerto TCP en el que corran sus procesos; para seguir con el puerto "titular" vamos a ponerlos en el puerto 27017. Es importante que las 3 máquinas puedan acceder al puerto de las otras 2. Adicionalmente, la máquina que vaya a usar este clúster también debe pode acceder al puerto 27017 de las 3 máquinas.

## Preparación de las máquinas individuales

Queremos una versión de *mongodb* un poco reciente, así que no vamos a usar los paquetes oficiales de la distribución, y la empresa de *mongodb* no ofrece paquete para *Debian jessie*. Por ello vamos a montar un esqueleto de ficheros como se describe en [un artículo anterior]({filename}/articles/escribiendo-units-en-systemd.md). Vamos a describir el proceso en la máquina **mongo1**, para replicarlo a posteriori en las otras 2.

Creamos la estructura de carpetas que van a contener todo lo relativo a **mongodb**.

```bash
root@mongo1:~# mkdir -p /opt/mongodb/{bin,conf,data/replica,logs}
root@mongo1:~# 
```

Copiamos el binario **mongod** que encontraremos en el fichero *.tar.gz* de la página de descargas de la página web.

```bash
root@mongo1:~# cp mongod /opt/mongodb/bin/
root@mongo1:~# 
```

Creamos un fichero de configuración con el que vamos a levantar el proceso en esta máquina.

```bash
root@mongo1:~# cat /opt/mongodb/conf/replica.conf
systemLog:
    path: /opt/mongodb/logs/replica.log
    logAppend: true
    destination: file

net:
    port: 27017
    bindIp: 0.0.0.0

storage:
    dbPath: /opt/mongodb/data/replica
    smallFiles: true

replication:
    replSetName: replica
root@mongo1:~# 
```

Por razones de seguridad vamos a lanzar el servicio con un usuario propio de sistema.

```bash
root@mongo1:~# useradd -s /usr/sbin/nologin -r -M mongo -d /opt/mongodb/
root@mongo1:~# 
```

Y para ahorrarnos problemas de permisos, lo hacemos propietario de todo lo referente al servicio:

```bash
root@mongo1:~# chown -R mongo:mongo /opt/mongodb/
root@mongo1:~# 
```

Vamos a crearle una **unit** para que el sistema se encargue de levantar automáticamente el servicio en caso de reinicio de la máquina:

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
ExecStartPre=/bin/rm -f /opt/mongodb/data/replica/mongod.lock
ExecStart=/opt/mongodb/bin/mongod -f /opt/mongodb/conf/replica.conf

[Install]
WantedBy=multi-user.target
root@mongo1:~# 
```

Finalmente activamos la **unit** e iniciamos el servicio.

```bash
root@mongo1:~# systemctl enable mongo
Created symlink from /etc/systemd/system/multi-user.target.wants/mongo.service to /etc/systemd/system/mongo.service.
root@mongo1:~# systemctl start mongo
root@mongo1:~# 
```

Ahora toca repetir el proceso en las otras 2 máquinas, exactamente igual.

## Configuración del clúster

Accedemos a una de las máquinas del futuro clúster desde cualquier máquina que pueda hacerlo y que disponga del binario **mongo** (el mongo shell), que también viene en el archivo *.tar.gz* descargado de la página oficial; este shell no es necesario para la aplicación que use el clúster ya que el **driver** de cada lenguaje suple sus funciones, pero es muy útil tenerlo a mano para tareas de administración y consultas varias.

```bash
root@client:~# ./mongo --host 10.0.0.2
MongoDB shell version: 3.0.7
connecting to: 10.0.0.2:27017/test
Welcome to the MongoDB shell.
For interactive help, type "help".
> 
```

Hay dos formas de crear la configuración del clúster: pasando el documento de configuración en el método *initiate* o añadir los nodos a posteriori con el método *add*. Voy a usar este método por ser mas fácil.

```bash
> rs.initiate()
{
	"info2" : "no configuration explicitly specified -- making one",
	"me" : "mongo1:27017",
	"ok" : 1
}
replica:PRIMARY> rs.add("mongo2:27017")
{ "ok" : 1 }
replica:PRIMARY> rs.add("mongo3:27017")
{ "ok" : 1 }
replica:PRIMARY> 
```

Vamos a lanzar el método *status* hasta que todos los nodos sean primarios o secundarios, momento en el que la *replica* va a quedar correctamente montada.

```bash
replica:PRIMARY> rs.status()
{
	"set" : "replica",
...
	"members" : [
		{
...
			"name" : "mongo1:27017",
			"stateStr" : "PRIMARY",
			"self" : true
...
		},
		{
...
			"name" : "mongo2:27017",
			"stateStr" : "SECONDARY",
			"syncingTo" : "mongo1:27017",
...
		},
		{
...
			"name" : "mongo3:27017",
			"stateStr" : "SECONDARY",
			"syncingTo" : "mongo1:27017",
...
		}
	],
	"ok" : 1
}
replica:PRIMARY> 
```

Y con esta salida del método *status* ya lo tenemos todo funcionando correctamente.
