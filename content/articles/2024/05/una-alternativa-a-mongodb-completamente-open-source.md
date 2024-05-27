---
title: "Una alternativa a MongoDB, completamente Open Source"
slug: "una-alternativa-a-mongodb-completamente-open-source"
date: "2024-05-27"
categories: ['Sistemas']
tags: ['linux', 'debian', 'mongodb', 'ferretdb', 'proxy']
---

Hace tiempo me enamoré de **MongoDB**; era la base de datos por defecto para todos mis proyectos.
El *status quo* cambió cuando decidieron cambiar la licencia (perdiendo el soporte de las principales
distribuciones Linux), y cuando decidieron requerir extensiones AVX en el procesador,
limitando los entornos virtuales en los que ejecutarlo.<!--more-->

En medio de este descontento apareció un proyecto que pretendía reemplazar **MongoDB** por una
solución mayormente compatible, apoyada por software libre. El resultado fue **FerretDB**, que
intenta traducir el protocolo de **MongoDB** para guardar los datos en otra base de datos, que
de momento puede ser **PostgreSQL** o **SQLite**.

La idea es simple: se trata de un servidor tipo **proxy** al que el cliente (sea un **mongo shell**
o una aplicación con un *driver* compatible) le hace las peticiones. El **proxy** traduce las peticiones
a otro protocolo para que otra base de datos se encargue de la parte de persistencia.

![FerretDB como proxy MongoDB](/images/ferretdb-como-proxy-mongodb.png)

## Un ejemplo rápido utilizando SQLite

Primero necesitamos descargarnos el binario en [la página de descargas][1]. Este se ofrece en varios
formatos, para que podáis elegir el que más os convenga: en formato **Docker**, **RPM**, **DEB** o
incluso como binario solo. En el caso de los paquetes, solo contienen el binario, que se va a poner
en `/usr/bin/ferretdb`, sin ningún fichero adicional.

La ejecución es tan simple como ejecutar el binario, configurándolo mediante *flags* o variables
de entorno, según [su documentación][2]. Para el caso de **SQLite**, los más importantes son
`--handler` y `--sqlite-url` para indicar donde guardar los ficheros de bases de datos. Por ejemplo:

```bash
ferretdb --state-dir=data/ --handler=sqlite --sqlite-url=file:data/
```

## Creando un servicio SystemD

Si queremos crear un servicio con **SystemD**, solo necesitamos un fichero que contenga la *unit*
en `/etc/systemd/system/`. Otro punto interesante es que el servicio ejecute con un usuario de
sistema dedicado, que deberemos crear con este fin.

Vamos a empezar instalando el paquete `.deb`, porque lo que tenemos entre manos en este momento
es una distribución **Debian 12**.

```bash
gerard@database:~$ wget https://github.com/FerretDB/FerretDB/releases/download/v1.21.0/ferretdb-linux-amd64.deb
...
gerard@database:~$
```

```bash
gerard@database:~$ sudo dpkg -i ferretdb-linux-amd64.deb
Seleccionando el paquete ferretdb previamente no seleccionado.
(Leyendo la base de datos ... 22279 ficheros o directorios instalados actualmente.)
Preparando para desempaquetar ferretdb-linux-amd64.deb ...
Desempaquetando ferretdb (1.21.0) ...
Configurando ferretdb (1.21.0) ...
gerard@database:~$
```

Crear un usuario de sistema no tiene mucha dificultad; basta con usar el comando **useradd**
con algunos parámetros, que ya de paso nos va a crear la carpeta de datos en `/var/lib/ferretdb`.

```bash
gerard@database:~$ sudo useradd -d /var/lib/ferretdb -m -r ferretdb -s /usr/sbin/nologin -k /dev/null
gerard@database:~$
```

La *unit* de **SystemD** tampoco entraña ninguna dificultad. Se trata simplemente de un servicio
simple, ejecutado por el usuario que acabamos de crear y que lanza el comando necesario.

```bash
gerard@database:~$ cat /etc/systemd/system/ferretdb.service
[Service]
Type=simple
Restart=always
User=ferretdb
Group=ferretdb
ExecStart=ferretdb --telemetry=disabled --debug-addr=- --state-dir=/var/lib/ferretdb/ --handler=sqlite --sqlite-url=file:/var/lib/ferretdb/

[Install]
WantedBy=multi-user.target
gerard@database:~$
```

Alternativamente, podemos ejecutar el comando `ferretdb` sin argumentos, suministrándolos mediante
variables de entorno, en una especie de fichero de configuración, lo que nos dejaría la *unit*
y su configuración de esta forma:

```bash
gerard@database:~$ cat /etc/ferretdb.conf
FERRETDB_DEBUG_ADDR=-
FERRETDB_TELEMETRY=disabled
FERRETDB_STATE_DIR=/var/lib/ferretdb/
FERRETDB_HANDLER=sqlite
FERRETDB_SQLITE_URL=file:/var/lib/ferretdb/
gerard@database:~$
```

```bash
gerard@database:~$ cat /etc/systemd/system/ferretdb.service
[Service]
Type=simple
Restart=always
User=ferretdb
Group=ferretdb
EnvironmentFile=/etc/ferretdb.conf
ExecStart=ferretdb

[Install]
WantedBy=multi-user.target
gerard@database:~$
```

Solo nos faltará recargar la configuración de **SystemD**, activar y levantar el nuevo servicio:

```bash
gerard@database:~$ sudo systemctl daemon-reload
gerard@database:~$
```

```bash
gerard@database:~$ sudo systemctl enable ferretdb --now
Created symlink /etc/systemd/system/multi-user.target.wants/ferretdb.service → /etc/systemd/system/ferretdb.service.
gerard@database:~$
```

Y con esto tenemos un servidor **MongoDB** impostor que podemos utilizar con las herramientas habituales:

```bash
gerard@database:~$ mongosh mongodb://localhost/kittens
...
kittens> db.kittens.insertOne({name: "Garfield"})
...
kittens> db.kittens.insertOne({name: "Azrael"})
...
kittens> db.kittens.insertOne({name: "Snowball"})
...
kittens> db.kittens.find()
[
  { _id: ObjectId('6654debea478bf8021a26a13'), name: 'Garfield' },
  { _id: ObjectId('6654decea478bf8021a26a14'), name: 'Azrael' },
  { _id: ObjectId('6654ded2a478bf8021a26a15'), name: 'Snowball' }
]
kittens>
```

Podemos encontrar los ficheros variables en `/var/lib/ferretdb/`, como indicamos en la configuración.
Ninguna otra carpeta tiene contenido cambiante del que necesitemos copias de respaldo.

```bash
gerard@database:~$ tree /var/lib/ferretdb/
/var/lib/ferretdb/
├── kittens.sqlite
├── kittens.sqlite-shm
├── kittens.sqlite-wal
└── state.json

1 directory, 4 files
gerard@database:~$
```

## Una última advertencia

En el momento de escribir este artículo, **FerretDB** tiene algunos puntos cojos:

* No soporta autenticación en **SQLite**, y su soporte es limitado en **PostgreSQL**.
* No permite hacer clústeres, ni mediante *replica sets* ni mediante *sharding*.
* Algunas operaciones del *aggregation framework* no están todavía implementadas.

Aun así, es una magnífica herramienta para dotar a **SQLite** de una capa de acceso remota.
Con el tiempo espero una evolución que seguiré con mucho cariño.

[1]: https://github.com/FerretDB/FerretDB/releases
[2]: https://docs.ferretdb.io/configuration/flags/
