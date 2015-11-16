Title: Escribiendo units en systemd
Slug: escribiendo-units-en-systemd
Date: 2015-11-09 22:30
Category: Operaciones
Tags: linux, debian, jessie, systemd, mongodb



Cuando se anunció *systemd* me llamó la atención que además de las funciones
estándares de otros sistemas de *init* (por ejemplo *sysvinit*), también se
ofrecían otras funcionalidades normalmente delegadas a otros procesos, como por
ejemplo, la posibilidad de reiniciar procesos automáticamente o de lanzar
procesos temporales al estilo de *cron*.

En este artículo se explica como escribir estos ficheros que rigen las tareas
propias del sistema *init* para iniciar procesos que no disponen de tales
facilidades. Adicionalmente, vamos a ver como beneficiarnos del sistema de
plantillas de estos mismos ficheros para evitarnos tener que repetirnos, de
acuerdo con el principio [DRY (don't repeat yourself)](https://en.wikipedia.org/wiki/Don%27t_repeat_yourself).

Como ejemplo, vamos a utilizar un sistema básico de *Linux* con *systemd*; que
podría ser *RedHat 7*, *ArchLinux* o *Debian 8*. En este caso, se va a utilizar
un sistema *Debian Jessie* con una instalación básica *netinstall* con *SSH* y
nada mas.

Vamos a suponer que queremos montar un servidor con 2 instancias de *MongoDB*,
escuchando en los puertos 27001 y 27002. Empecemos con montar una estructura
en */opt/* para contener todo lo relacionado con este despliegue. La idea es
que vamos a levantar el binario *mongod* con dos configuraciones distintas.
Por eso, de momento basta con poner el binario *mongod*, las dos configuraciones
y las dos carpetas de datos.

```bash
root@server:~# tree /opt/
/opt/
└── mongodb
    ├── bin
    │   └── mongod
    ├── conf
    │   ├── mongo1.conf
    │   └── mongo2.conf
    ├── data
    │   ├── mongo1
    │   └── mongo2
    └── logs

7 directories, 3 files
root@server:~# 
```

La configuración de ambos procesos va a ser la mínima necesaria para que los
procesos no entren en conflicto entre ellos.

```bash
root@server:~# cat /opt/mongodb/conf/mongo1.conf 
systemLog:
    path: /opt/mongodb/logs/mongo1.log
    logAppend: true
    destination: file

net:
    port: 27001

storage:
    dbPath: /opt/mongodb/data/mongo1
    smallFiles: true
root@server:~# cat /opt/mongodb/conf/mongo2.conf 
systemLog:
    path: /opt/mongodb/logs/mongo2.log
    logAppend: true
    destination: file

net:
    port: 27002

storage:
    dbPath: /opt/mongodb/data/mongo2
    smallFiles: true
root@server:~# 
```

Como apunte importante, no se ha definido un archivo para guardar el *PID* del
proceso; *systemd* no lo necesita y conoce el *PID* de los procesos que levanta.

Siguiendo las directivas de seguridad mínimas, los dos procesos *mongod* van a
levantarse con un usuario estándar que no sea *root*. En este caso, toda la
carpeta */opt/mongodb/* pertenece al usuario *mongo*, aunque bastaría con la
carpeta de datos y la de logs.

Ponemos la definición de nuestras **units** en la carpeta designada según el
estándar, que es */etc/systemd/system/*.

```bash
root@server:~# cat /etc/systemd/system/mongo1.service 
[Unit]
Description=MongoDB

[Service]
User=mongo
LimitFSIZE=infinity
LimitCPU=infinity
LimitAS=infinity
LimitNOFILE=64000
LimitNPROC=64000
ExecStartPre=/bin/rm -f /opt/mongodb/data/mongo1/mongod.lock
ExecStart=/opt/mongodb/bin/mongod -f /opt/mongodb/conf/mongo1.conf

[Install]
WantedBy=multi-user.target
root@server:~# cat /etc/systemd/system/mongo2.service 
[Unit]
Description=MongoDB

[Service]
User=mongo
LimitFSIZE=infinity
LimitCPU=infinity
LimitAS=infinity
LimitNOFILE=64000
LimitNPROC=64000
ExecStartPre=/bin/rm -f /opt/mongodb/data/mongo2/mongod.lock
ExecStart=/opt/mongodb/bin/mongod -f /opt/mongodb/conf/mongo2.conf

[Install]
WantedBy=multi-user.target
root@server:~# 
```

Es especialmente interesante ver que el lenguaje de la **units** de *systemd*
es declarativo, y que no son *init scripts*; *systemd* se encarga de todo por
nosotros. Basta con declarar el comando con el que levantar el servicio y el
usuario con el que hacerlo.

La directiva **WantedBy** indica que se tiene que levantar con el **target**
*multi-user*, que es el que usa *Debian* por defecto. Un **target** viene
a ser el equivalente a un *runlevel* de *sysvinit*.

Hay una directiva **ExecStartPre** que se encarga de eliminar el *lock file*
de *MongoDB* por si el proceso hubiera acabado de forma inesperada. El
binario *mongod* no levanta si este fichero existe, ya que cree que ya hay
una instancia de *mongod* usando la carpeta de datos.

El resto de directivas se limitan a modificar los límites de los procesos a
levantar, de acuerdo a la documentación de *MongoDB*.

A partir de ahora, son **units** normales del sistema y se pueden activar
e iniciar. Si ya estuvieran cargados, habría que recargar la configuración
de *systemd*.

```bash
root@server:~# systemctl enable mongo1
root@server:~# systemctl enable mongo2
root@server:~# systemctl start mongo1
root@server:~# systemctl start mongo2
root@server:~# systemctl daemon-reload
root@server:~# 
```

## Uso de plantillas para evitar repetirnos

Toda **unit** cuyo nombre acabe en **arroba** seguido por *.service* o
cualquier otro tipo de **unit**, es por convención, una **plantilla**.

La idea es que vamos a crear un *link* a la **plantilla**, que ponga un texto
detrás de la **arroba**. Este texto va a estar disponible en la plantilla
como **%i**. De esta forma podemos "pasar un parámetro" a la plantilla, usando
ese parámetro como diferenciador de los dos procesos.

**Veamos un ejemplo:**

Creamos dos *links* a la **plantilla** *mongodb@.service*, con los nombres
*mongodb@mongo1.service* y *mongodb@mongo2.service*, que son nuestras
instancias. Estas instancias se rigen con las directivas de la **plantilla**,
con la variable **%i** conteniendo los valores *mongo1* y *mongo2*
respectivamente.

```bash
root@server:~# ls -l /etc/systemd/system/mongodb\@*
lrwxrwxrwx 1 root root  16 nov  3 12:46 /etc/systemd/system/mongodb@mongo1.service -> mongodb@.service
lrwxrwxrwx 1 root root  16 nov  3 12:46 /etc/systemd/system/mongodb@mongo2.service -> mongodb@.service
-rw-r--r-- 1 root root 207 nov  3 12:45 /etc/systemd/system/mongodb@.service
```

Ahora redactamos la plantilla, teniendo en cuenta los valores que se van a
cambiarse por la variable **%i**, que vamos a usar para identificar el fichero
de configuración de cada instancia. También es posible poner otras variables
en la **plantilla**, como por ejemplo, el nombre de la máquina o la versión
del *kernel* de la máquina.

```bash
root@server:~# cat /etc/systemd/system/mongodb\@.service 
[Unit]
Description=MongoDB

[Service]
User=mongo
LimitFSIZE=infinity
LimitCPU=infinity
LimitAS=infinity
LimitNOFILE=64000
LimitNPROC=64000
ExecStartPre=/bin/rm -f /opt/mongodb/data/%i/mongod.lock
ExecStart=/opt/mongodb/bin/mongod -f /opt/mongodb/conf/%i.conf

[Install]
WantedBy=multi-user.target
root@server:~# 
```

Ahora solo falta activar las instancias e iniciarlas, con los comandos
habituales del demonio *systemd*.

```bash
root@server:~# systemctl enable mongodb@mongo1
Created symlink from /etc/systemd/system/multi-user.target.wants/mongodb@mongo1.service to /etc/systemd/system/mongodb@.service.
root@server:~# systemctl enable mongodb@mongo2
Created symlink from /etc/systemd/system/multi-user.target.wants/mongodb@mongo2.service to /etc/systemd/system/mongodb@.service.
root@server:~# systemctl start mongodb@mongo1
root@server:~# systemctl start mongodb@mongo2
root@server:~# 
```

Y con esto lo hemos conseguido.
