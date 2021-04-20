---
title: "Una breve introducción a PostgreSQL"
slug: "una-breve-introduccion-a-postgresql"
date: "2019-09-09"
categories: ['Sistemas']
tags: ['introducción', 'postgresql']
---

Cuando **MongoDB** decidió cambiar la licencia por una que no cumple los criterios
básicos de *software* libre, muchos decidieron abandonar el barco, siendo las principales
distribuciones de **linux** las primeras en hacerlo. No faltaron voces que cantaran
las maravillas de **PostgreSQL**, y como soy curioso, le he dado un intento.<!--more-->

Para esta batería de pruebas, he utilizado dos servidores, ambos con **Debian**:

* **Database**: Se trata del servidor que ejecuta el demonio de la base de datos.
* **Server**: Otro servidor cualquiera, que va a ejercer como cliente remoto.

Asumiremos que ambos tienen las herramientas cliente, y que **database** ejecuta el servidor.

```bash
gerard@database:~$ sudo apt install postgresql postgresql-client
...
gerard@database:~$ 
```

```bash
gerard@server:~$ sudo apt install postgresql-client
...
gerard@server:~$ 
```

## Abriendo el acceso remoto

Por defecto, cuando se instala una base de datos en **Debian**, la política es que escuche
solamente en la interfaz de red *localhost*; esto se hace para evitar exponerlo a otros
vecinos de la red, a menos que el administrador sepa lo que hace y lo modifique.

Esto se puede hacer fácilmente con la directiva de configuración `listen_addresses`, que
podemos poner como `'*'` para que escuche en todas. Para que aplique el cambio, es necesario
que se reinicie el servicio.

```bash
gerard@database:~$ grep ^listen /etc/postgresql/11/main/postgresql.conf 
listen_addresses = '*'
gerard@database:~$ 
```

```bash
gerard@database:~$ sudo systemctl restart postgresql
gerard@database:~$ 
```

Ahora ya podemos comprobar que la base de datos escucha en todas las direcciones IP (`0.0.0.0`):

```bash
gerard@database:~$ ss -lnt
State                     Recv-Q                    Send-Q                                       Local Address:Port                                       Peer Address:Port                   
LISTEN                    0                         128                                                0.0.0.0:22                                              0.0.0.0:*                      
LISTEN                    0                         128                                                0.0.0.0:5432                                            0.0.0.0:*                      
LISTEN                    0                         128                                                   [::]:22                                                 [::]:*                      
LISTEN                    0                         128                                                   [::]:5432                                               [::]:*                      
gerard@database:~$ 
```

Si intentamos acceder de forma remota, veremos que no nos deja; esto es porque el servidor
implementa una restricción de acceso propia, que debe configurarse.

```bash
gerard@server:~$ psql -h database -U postgres
psql: FATAL:  no hay una línea en pg_hba.conf para «10.0.0.243», usuario «postgres», base de datos «postgres», SSL activo
FATAL:  no hay una línea en pg_hba.conf para «10.0.0.243», usuario «postgres», base de datos «postgres», SSL inactivo
gerard@server:~$ 
```

Estas reglas se guardan en el fichero `pg_hba.conf`, que viene comentado y es bastante
fácil de seguir. En un ejercicio de minimalismo, ya he dejado lo siguiente:

```bash
gerard@database:~$ sudo egrep -v '^[[:space:]]*(#|$)' /etc/postgresql/11/main/pg_hba.conf
local   all             all                                     trust
host    all             all             127.0.0.1/32            trust
host    all             all             ::1/128                 trust
local   replication     all                                     trust
host    replication     all             127.0.0.1/32            trust
host    replication     all             ::1/128                 trust
host    all             all             all                     md5
gerard@database:~$ 
```

Básicamente indica que se deja entrar sin contraseña a todos los usuarios desde el servidor
local (a través de IP o de *unix socket*) y requiere contraseña para todo el resto.

Para aplicar los cambios, basta con enviar un `SIGHUP` al proceso principal de **postgresql**.
Para ello, listaremos los procesos; el proceso principal es aquél cuyo padre es el PID 1,
siendo este el padre del resto. Acto seguido, le mandamos el *signal*.

```bash
gerard@database:~$ ps -eo ppid,pid,args | grep postgres
    1  2166 /usr/lib/postgresql/11/bin/postgres -D /var/lib/postgresql/11/main -c config_file=/etc/postgresql/11/main/postgresql.conf
 2166  2168 postgres: 11/main: checkpointer   
 2166  2169 postgres: 11/main: background writer   
 2166  2170 postgres: 11/main: walwriter   
 2166  2171 postgres: 11/main: autovacuum launcher   
 2166  2172 postgres: 11/main: stats collector   
 2166  2173 postgres: 11/main: logical replication launcher   
  389  2248 grep postgres
gerard@database:~$ 
```

```bash
gerard@database:~$ sudo kill -HUP 2166
gerard@database:~$ 
```

Y con esto podemos comprobar que se puede acceder desde local sin *password*, y que
se puede acceder desde un servidor remoto con la contraseña que toque.

```bash
gerard@database:~$ psql -U postgres
psql (11.5 (Debian 11.5-1+deb10u1))
Digite «help» para obtener ayuda.

postgres=# exit
gerard@database:~$ 
```

```bash
gerard@server:~$ psql -h database -U postgres
Contraseña para usuario postgres: 
psql: FATAL:  la autentificación password falló para el usuario «postgres»
FATAL:  la autentificación password falló para el usuario «postgres»
gerard@server:~$ 
```

**TRUCO**: El usuario administrativo no tiene una contraseña, precisamente para
evitar una intrusión remota. Si se necesita acceder remotamente con este usuario,
hay que darle una contraseña adecuada, como sigue:

```bash
gerard@database:~$ psql -U postgres
psql (11.5 (Debian 11.5-1+deb10u1))
Digite «help» para obtener ayuda.

postgres=# alter user postgres with encrypted password 's3cr3t';
ALTER ROLE
postgres=# exit
gerard@database:~$ 
```

Ahora ya deberíamos poder acceder remotamente con la contraseña indicada.

## Usando el servidor de bases de datos

### Creación de usuarios y bases de datos

Vamos a crear un usuario y una base de datos para hacer las pruebas relevantes.
Una propiedad nada deseable de **postgresql** es que cualquier usuario tiene permisos
para hacer lo que quiera en el *schema public*, lo que no es lo recomendable.

Como ya sabéis, soy un firme defensor de la separación forzada de aplicaciones y
usuarios, con lo que voy a revocar todos estos permisos, y se los voy a conceder
al usuario responsable de cada aplicación.

```bash
gerard@database:~$ psql -U postgres
psql (11.5 (Debian 11.5-1+deb10u1))
Digite «help» para obtener ayuda.

postgres=# create database kittendb;
CREATE DATABASE
postgres=# revoke all on database kittendb from public;
REVOKE
postgres=# create user kittenuser with encrypted password 'kittenpass';
CREATE ROLE
postgres=# grant all privileges on database kittendb to kittenuser;
GRANT
postgres=# exit
gerard@database:~$ 
```

Ahora ya deberíamos poder usar el nuevo usuario para acceder a la base de datos,
ya sea de forma remota (con contraseña) o local (sin ella), tal como indicamos
en la configuración del control de acceso.

```bash
gerard@server:~$ psql -h database -U kittenuser -d kittendb
Contraseña para usuario kittenuser: 
psql (11.5 (Debian 11.5-1+deb10u1))
conexión SSL (protocolo: TLSv1.3, cifrado: TLS_AES_256_GCM_SHA384, bits: 256, compresión: desactivado)
Digite «help» para obtener ayuda.

kittendb=> exit
gerard@server:~$ 
```

```bash
gerard@database:~$ psql -U kittenuser -d kittendb
psql (11.5 (Debian 11.5-1+deb10u1))
Digite «help» para obtener ayuda.

kittendb=> 
```

### Trabajando con la base de datos

Normalmente vamos a dar unas credenciales específicas a los desarrolladores de las
aplicaciones, y es responsabilidad de estos lanzar las operaciones que crean oportunas.
Vamos a lanzar algunas operaciones solo para ver que todo funciona como debe.

Vamos a aprovechar que tenemos un usuario nominal y vamos a utilizarlo, por ejemplo,
en remoto. Como el usuario se creó para esta base de datos concreta, vamos a utilizarlo.
Abriremos un *shell* de **postgresql** desde donde haremos el resto de operaciones.

```bash
gerard@server:~$ psql -h database -U kittenuser -d kittendb
Contraseña para usuario kittenuser: 
psql (11.5 (Debian 11.5-1+deb10u1))
conexión SSL (protocolo: TLSv1.3, cifrado: TLS_AES_256_GCM_SHA384, bits: 256, compresión: desactivado)
Digite «help» para obtener ayuda.

kittendb=> 
```

Vamos a crear dos tablas, que nos van a ayudar a visualizar el ejemplo: se trata
de un sistema en el que tenemos usuarios y gatitos, indicando cada gatito su propietario.
No es gran cosa, pero expresa varias tablas y una relacion entre ellas vía una *foreign key*.

```bash
kittendb=> CREATE TABLE owners (id SERIAL PRIMARY KEY, name TEXT);
CREATE TABLE
kittendb=> CREATE TABLE kittens (id SERIAL PRIMARY KEY, name TEXT, owner_id INTEGER REFERENCES owners (id));
CREATE TABLE
kittendb=> 
```

Vamos a declarar algunos propietarios de gatitos, por poner algún dato en la base de datos:

```bash
kittendb=> INSERT INTO owners (name) VALUES ('Bob');
INSERT 0 1
kittendb=> INSERT INTO owners (name) VALUES ('Alice');
INSERT 0 1
kittendb=> SELECT * FROM owners;
 id | name  
----+-------
  1 | Bob
  2 | Alice
(2 filas)

kittendb=> 
```

De la misma forma, vamos a poner gatitos, dos para Bob y uno para Alice:

```bash
kittendb=> INSERT INTO kittens (name, owner_id) VALUES ('Smirnov', 1);
INSERT 0 1
kittendb=> INSERT INTO kittens (name, owner_id) VALUES ('Eristoff', 1);
INSERT 0 1
kittendb=> INSERT INTO kittens (name, owner_id) VALUES ('Stolichnaya', 2);
INSERT 0 1
kittendb=> SELECT * FROM kittens;
 id |    name     | owner_id 
----+-------------+----------
  1 | Smirnov     |        1
  2 | Eristoff    |        1
  3 | Stolichnaya |        2
(3 filas)

kittendb=> 
```

Ahora toca hacer alguna consulta. Ya que estamos en un sistema relacional, voy a
utilizar una operación de `JOIN`, que nos muestre un agregado de gatitos y propietarios.

```bash
kittendb=> SELECT * FROM owners INNER JOIN kittens ON owners.id = kittens.owner_id;
 id | name  | id |    name     | owner_id 
----+-------+----+-------------+----------
  1 | Bob   |  1 | Smirnov     |        1
  1 | Bob   |  2 | Eristoff    |        1
  2 | Alice |  3 | Stolichnaya |        2
(3 filas)

kittendb=> 
```

Funciona, así que ya podemos crear un usuario y su base de datos para un proyecto
un poco más interesante, pero como indico, esto queda como responsabilidad para el
desarrollador, que seguramente utilizará alguna librería tipo ORM para ello.

## Backups y restores

### Backups

Siguiendo el estilo de **mysql**, el *backup* se hace con una herramienta de *dump*
propia, que volcará un fichero SQL con los comandos necesarios para recrear la base
de datos entera. Solo hay que indicar el fichero de salida, o recoger la salida estándar.

```bash
gerard@server:~$ pg_dump -h database -U kittenuser -d kittendb > kittendb.sql
Contraseña: 
gerard@server:~$ 
```

Este fichero de texto está lleno de espacios y comentarios, con lo que se comprime bien;
podemos dejar el trabajo a la misma utilidad, o comprimirlo *a posteriori* con **gzip**,
**bzip2** o similares (es lo que hace el *flag* `--compress`).

```bash
gerard@server:~$ pg_dump -h database -U kittenuser -d kittendb --compress 9 > kittendb.sql.gz
Contraseña: 
gerard@server:~$ 
```

```bash
gerard@server:~$ pg_dump -h database -U kittenuser -d kittendb | gzip -9c > kittendb.sql.gz
Contraseña: 
gerard@server:~$ 
```

**TRUCO**: Es recomendable poner la fecha del *backup* en el nombre del fichero, y
archivarlo en algún lugar seguro, para posibles futuros usos. Herramientas tipo **cron**
nos pueden ayudar a lanzar *scripts* de *backup* automatizados.

Alternativamente, podemos utilizar la herramienta `pg_dumpall` que necesita ejecutarse
con el usuario administrador, pero permite sacar un *backup* de todas las bases
de datos del servidor, incluídos metadatos de usuarios.

### Restores

Tras hacer el *backup* obtuvimos un fichero SQL, que debe ser interpretado como cualquier
otro *script*, con el binario `psql`. Solo hay que tener en cuenta dos cosas:

* El *backup* no comprueba si una fila existe, lo que da lugar a duplicidades y problemas de claves duplicadas.
* El *backup* incluye *grants* al usuario original, que debe existir para no dar un error.

Por ello, vamos a destruir la base de datos original, con los permisos y usuarios necesarios.
Una vez la tengamos vacía, basta con ejecutar el comando `psql` con la entrada estándar
conectada al fichero de *backup*, o con una *pipe* al comando que lo descomprime.

Empezaremos eliminando la base de datos que no deseamos conservar; para ello necesitamos acceder
con el usuario administrador de la base de datos, sea de forma local o remota:

```bash
postgres=# drop database kittendb;
DROP DATABASE
postgres=# 
```

Creamos la base de datos de nuevo, dejándola vacía y sin acceso a nadie:

```bash
postgres=# create database kittendb;
CREATE DATABASE
postgres=# revoke all on database kittendb from public;
REVOKE
postgres=# 
```

**TRUCO**: Si estuviéramos en otro servidor de **postgresql** o hubiéramos borrado el
usuario **kittenuser**, también tendríamos que crearlo en este paso; es necesario
para restablecer el *backup* y para entrar luego para utilizar la base de datos.

Ahora que tenemos un usuario adecuado para trabajar con esta nueva base de datos,
vamos a darle permisos para hacer con ella lo que quiera; ya de paso, haremos la
restauración con este mismo usuario, que puede escribir las tablas y filas sin problemas.

```bash
postgres=# grant all privileges on database kittendb to kittenuser;
GRANT
postgres=# 
```

Solo nos queda ejecutar el *script* de *backup* a través del *shell* de **postgresql**:

```bash
gerard@server:~$ zcat kittendb.sql.gz | psql -h database -U kittenuser -d kittendb
Contraseña para usuario kittenuser: 
...
gerard@server:~$ 
```

Y con esto ya tenemos nuestros datos restablecidos.

## Conclusión

**PostgreSQL** nos ofrece un motor de base de datos completo y relativamente poco complejo.
Sin embargo, se trata de un modelo de bases de datos relacionales, que nada tiene que ver
con **MongoDB**; más que hablar de sustituirlo, lo correcto sería hablar de complementarlo.

Sigue teniendo su encanto y sirve en la mayoría de casos de uso necesarios; por lo que
he podido leer, hay administradores que le sacan un rendimiento más que aceptable, sin
renunciar el modelo relacional con el que todo el mundo está cómodo y acostumbrado.
