---
title: "Un clúster activo-activo de MariaDB"
slug: "un-cluster-activo-activo-de-mariadb"
date: "2022-07-30"
categories: ['Sistemas']
tags: ['debian', 'cluster', 'mariadb', 'mysql']
---

Muchas de nuestras aplicaciones diarias utilizan una base de datos, y es muy fácil
disponer de una utilizando los repositorios de la distribución utilizada. Sin embargo,
en entornos críticos hace falta algo *más profesional*, capaz de resistir en caso de
fallos en los nodos y capaz de asumir mucha más carga.<!--more-->

Para eso montamos *clústeres* que nos proporcionen esa seguridad de que no vamos a
tener que actuar con prisas ni fuera de horas para garantizar el servicio que ofrecemos.
En este artículo nos vamos a centrar en montar un *clúster* de **MariaDB**, en donde
tanto lecturas como escrituras puedan ir a cualquiera de los nodos.

Para ello disponemos de 3 servidores **Debian Bullseye**: **mariadb01**, **mariadb02**
y **mariadb03**. Sus direcciones IP son irrelevantes, puesto que disponemos de una
resolución de nombres adecuada (utilizad un servicio DNS o el fichero `/etc/hosts`,
a vuestro gusto).

## Preparando los nodos

Para poder ejercer como nodos de un *clúster* de **MariaDB**, todos los servidores
deben disponer del servicio, que en el caso de **Debian** es `mariadb-server`. Vamos
a instalarlo:

```bash
gerard@mariadb01:~$ sudo apt update
...
gerard@mariadb01:~$
```

```bash
gerard@mariadb01:~$ sudo apt install mariadb-server
...
gerard@mariadb01:~$
```

Este servicio va a levantarse con una configuración diferente, así que de momento lo paramos:

```bash
gerard@mariadb01:~$ sudo systemctl stop mariadb
gerard@mariadb01:~$
```

La configuración del *clúster* se hace modificando la configuración del servicio, y en
el caso de **Debian** disponemos de un fichero preparado para ello:

```bash
gerard@mariadb01:/etc/mysql/mariadb.conf.d$ pwd
/etc/mysql/mariadb.conf.d
gerard@mariadb01:/etc/mysql/mariadb.conf.d$ cat 60-galera.cnf
#
# * Galera-related settings
#
# See the examples of server wsrep.cnf files in /usr/share/mysql
# and read more at https://mariadb.com/kb/en/galera-cluster/

[galera]
# Mandatory settings
#wsrep_on                 = ON
#wsrep_cluster_name       = "MariaDB Galera Cluster"
#wsrep_cluster_address    = gcomm://
#binlog_format            = row
#default_storage_engine   = InnoDB
#innodb_autoinc_lock_mode = 2

# Allow server to accept connections on all interfaces.
#bind-address = 0.0.0.0

# Optional settings
#wsrep_slave_threads = 1
#innodb_flush_log_at_trx_commit = 0
gerard@mariadb01:/etc/mysql/mariadb.conf.d$
```

La lista de valores obligados la podemos encontrar en [la documentación][1], y vemos
dos claras diferencias a mencionar: el `wsrep_cluster_name` no es obligado, y falta
la directiva necesaria `wsrep_provider`.

Tras modificar el fichero, nos debería quedar así:

```bash
gerard@mariadb01:~$ cat /etc/mysql/mariadb.conf.d/60-galera.cnf
#
# * Galera-related settings
#
# See the examples of server wsrep.cnf files in /usr/share/mysql
# and read more at https://mariadb.com/kb/en/galera-cluster/

[galera]
# Mandatory settings
wsrep_on                 = ON
#wsrep_cluster_name       = "MariaDB Galera Cluster"
wsrep_cluster_address    = gcomm://mariadb01,mariadb02,mariadb03
binlog_format            = row
default_storage_engine   = InnoDB
innodb_autoinc_lock_mode = 2
wsrep_provider           = /usr/lib/galera/libgalera_smm.so

# Allow server to accept connections on all interfaces.
bind-address = 0.0.0.0

# Optional settings
#wsrep_slave_threads = 1
#innodb_flush_log_at_trx_commit = 0
gerard@mariadb01:~$
```

Solo hemos descomentado las líneas obligadas (menos el nombre del *clúster*) y hemos
añadido el *provider*. Se habilita también el acceso remoto del servidor con la directiva
`bind-address`. Esta configuración es la misma para los tres nodos.

En este momento, tenemos el servicio instalado, configurado y parado.

**NOTA**: Esto se repite en los nodos **mariadb02** y **mariadb03**.

## Levantando el clúster

En circunstancias normales, la configuración especificada es suficiente; un nodo se
levanta, lee la directiva `wsrep_cluster_address` y busca uno de los nodos especificados
para unirse al *clúster*. El problema viene cuando no hay nodos levantados; el primer nodo
es incapaz de encontrar otro nodo levantado y, por lo tanto, no se puede unir al *clúster*.

En este momento hay que indicar que queremos crear un nuevo *clúster*, y eso se consigue
especificando la directiva `wsrep_cluster_address` vacía, indicando como valor `gcomm://`.
Para hacerlo disponemos de dos opciones:

* Modificar la configuración **temporalmente** para poder levantar el primer nodo, restableciéndola después.
* Utilizando el *script* `galera_new_cluster`, que levanta el servicio especificando la directiva vacía por parámetro.

Vamos a utilizar la segunda opción por ser la opción más fácil. Para ello decidimos
empezar con **mariadb01** como el primer nodo, y ejecutamos:

```bash
gerard@mariadb01:~$ sudo galera_new_cluster
gerard@mariadb01:~$
```

En este momento tenemos un *clúster* de un solo nodo, que es **mariadb01**. Esto se
puede verificar fácilmente (directiva `wsrep_cluster_size`):

```bash
gerard@mariadb01:~$ echo 'show status like "wsrep_cluster%"' | sudo mysql
Variable_name   Value
wsrep_cluster_weight    1
wsrep_cluster_capabilities
wsrep_cluster_conf_id   1
wsrep_cluster_size      1
wsrep_cluster_state_uuid        0c50e58b-0e68-11ed-9292-da9b77c8b3ef
wsrep_cluster_status    Primary
gerard@mariadb01:~$
```

El resto de nodos ya pueden unirse al *clúster*, haciendo caso a su configuración.

```bash
gerard@mariadb02:~$ sudo systemctl restart mariadb
gerard@mariadb02:~$
```

```bash
gerard@mariadb03:~$ sudo systemctl restart mariadb
gerard@mariadb03:~$
```

Podemos verificar que el *clúster* está bien montado repitiendo la consulta anterior:

```bash
gerard@mariadb03:~$ echo 'show status like "wsrep_cluster%"' | sudo mysql
Variable_name   Value
wsrep_cluster_weight    3
wsrep_cluster_capabilities
wsrep_cluster_conf_id   3
wsrep_cluster_size      3
wsrep_cluster_state_uuid        0c50e58b-0e68-11ed-9292-da9b77c8b3ef
wsrep_cluster_status    Primary
gerard@mariadb03:~$
```

**NOTA**: Solo necesitamos ejecutar `galera_new_cluster` cuando no hay nodos levantados;
de ahora en adelante podemos parar y levantar de forma normal el nodo **mariadb01**,
utilizando `systemctl`.

Y con esto el *clúster* queda funcionando.

## Probando la replicación (opcional)

Para hacer las pruebas del *clúster* nos limitaremos a ejecutar consultas y modificaciones
en todos los nodos, verificando que se reproducen en el resto. Empezamos creando una base
de datos, con una tabla y contenido; por ejemplo, en **mariadb01**:

```bash
gerard@mariadb01:~$ sudo mysql
...
MariaDB [(none)]> create database testdb;
Query OK, 1 row affected (0.031 sec)

MariaDB [(none)]> use testdb;
Database changed
MariaDB [testdb]> create table kittens (id int auto_increment, name varchar(100), primary key (id));
Query OK, 0 rows affected (0.033 sec)

MariaDB [testdb]> insert into kittens (name) values ("Garfield");
Query OK, 1 row affected (0.013 sec)

MariaDB [testdb]> insert into kittens (name) values ("Azrael");
Query OK, 1 row affected (0.015 sec)

MariaDB [testdb]> insert into kittens (name) values ("Snowball");
Query OK, 1 row affected (0.022 sec)

MariaDB [testdb]> select * from kittens;
+----+----------+
| id | name     |
+----+----------+
|  1 | Garfield |
|  4 | Azrael   |
|  7 | Snowball |
+----+----------+
3 rows in set (0.000 sec)

MariaDB [testdb]>
```

Podemos verificar que la base de datos ha aparecido en **mariadb02**:

```bash
gerard@mariadb02:~$ sudo mysql
...
MariaDB [(none)]> show databases;
+--------------------+
| Database           |
+--------------------+
| information_schema |
| mysql              |
| performance_schema |
| testdb             |
+--------------------+
4 rows in set (0.001 sec)

MariaDB [(none)]>
```

Verificamos que la tabla y su contenido existen también en **mariadb03** y, ya que
estamos, modificamos su contenido:

```bash
gerard@mariadb03:~$ sudo mysql testdb
...
MariaDB [testdb]> select * from kittens;
+----+----------+
| id | name     |
+----+----------+
|  1 | Garfield |
|  4 | Azrael   |
|  7 | Snowball |
+----+----------+
3 rows in set (0.000 sec)

MariaDB [testdb]> delete from kittens where id = 4;
Query OK, 1 row affected (0.041 sec)

MariaDB [testdb]>
```

Solo haría falta ir a cualquier otro nodo y verificar que las operaciones ejecutadas
en **mariadb03** también se replican al resto de nodos:

```bash
gerard@mariadb01:~$ sudo mysql testdb
...
MariaDB [testdb]> select * from kittens;
+----+----------+
| id | name     |
+----+----------+
|  1 | Garfield |
|  7 | Snowball |
+----+----------+
2 rows in set (0.000 sec)

MariaDB [testdb]>
```

De esta forma, nos da igual cuál es el nodo que ejecuta las consultas; todos van a ver
esos datos replicados. Esto nos garantiza que el *clúster* va a seguir operando si
se cae algún nodo y nos permite lanzar más consultas concurrentes, ganando rendimiento.

## ¿Dónde conectamos nuestras aplicaciones?

Tenemos 3 nodos y podemos leer y escribir en cualquiera de ellos. Sin embargo, los
*drivers* de conexión a **MySQL** o **MariaDB** suelen pedir una dirección IP y un
puerto para conectarse a la base de datos.

Por supuesto podemos añadir complejidad a nuestra aplicación manteniendo 3 conexiones
y reintentando las que fallen en algún otro nodo, pero no es lo ideal. Lo que necesitamos
es una dirección IP "de servicio" que sea consciente del nodo a utilizar.

Esto nos deja varias opciones, por ejemplo:

* Una dirección IP compartida con **keepalived**, que se vaya moviendo a un nodo saludable.
* Un elemento de red que pueda dirigir las peticiones a los nodos saludables, por ejemplo un balanceador **haproxy**.

La primera opción es algo más sencilla (en cuando a número de servidores), pero las
consultas solo irían a uno de los nodos. La segunda nos da más versatilidad, porque
utiliza mejor el factor numérico y nos permite distribuir las peticiones de forma
inteligente; incluso podríamos crear varios *endpoints*, por ejemplo:

* Un *endpoint* (*roundrobin* o *leastconn*) hacia **mariadb01** y **mariadb02** para uso habitual.
* Un *endpoint* hacia **mariadb03** para descargar consultas pesadas (informes o cargas, por ejemplo), sin afectar a la operativa habitual.

**TRUCO**: Es importante que haya un *check* para decidir los nodos saludables, o
nuestras consultas irán a parar en saco roto si el nodo elegido está caído.

[1]: https://mariadb.com/kb/en/configuring-mariadb-galera-cluster/
