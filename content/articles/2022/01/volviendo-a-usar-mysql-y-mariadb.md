---
title: "Volviendo a usar MySQL y MariaDB"
slug: "volviendo-a-usar-mysql-y-mariadb"
date: "2022-01-25"
categories: ['Sistemas']
tags: ['debian', 'mysql', 'mariadb', 'phpmyadmin', 'docker']
---

Hace mucho tiempo que he creído en **MongoDB**. Sin embargo, con el cambio de
licencia el soporte del mismo ha caído en los repositorios oficiales de las
diferentes distribuciones. Para añadir más sal a la herida, la empresa responsable
no soporta las últimas distribuciones estables de **Debian** en sus repositorios.<!--more-->

Eso me ha llevado a plantearme el abandono de **MongoDB** en favor de otros
sistemas de bases de datos, y como no podía ser de otra manera, miré hacia atrás
a los tiempos en que **MySQL** era el estándar *de facto*. Por supuesto, los
tiempos han cambiado y tenemos otras opciones compatibles con **MySQL**, como
por ejemplo **MariaDB** y **Percona**.

En este artículo nos centraremos en **MariaDB**, simplemente porque es la
opción que se encuentra en los repositorios de la distribución que vamos a
usar: **Debian Bullseye**.

## Un servidor dedicado

La idea es que vamos a dedicar este servidor al servicio de **MariaDB** en
exclusiva, aunque nada os impide poner más servicios en él. Pero es más fácil,
claro y conciso si nos centramos solamente en la parte de bases de datos.

### El servidor MariaDB

Esta parte es posiblemente la más fácil; usando **APT** podemos instalar
todo con el paquete **mariadb-server**. Las dependencias hacen el resto.

```bash
gerard@database:~$ sudo apt install mariadb-server
...
gerard@database:~$
```

En este momento tenemos un servidor de bases de datos **MariaDB** funcional,
con un usuario **root** con una *password* inválida, lo que hace que solo
podamos acceder desde local, sin *password* y usando el usuario **root** del
sistema operativo:

```bash
gerard@database:~$ sudo mysql
Welcome to the MariaDB monitor.  Commands end with ; or \g.
Your MariaDB connection id is 46
Server version: 10.5.12-MariaDB-0+deb11u1 Debian 11

Copyright (c) 2000, 2018, Oracle, MariaDB Corporation Ab and others.

Type 'help;' or '\h' for help. Type '\c' to clear the current input statement.

MariaDB [(none)]>
```

Esto nos puede valer para la mayoría de casos, pero a veces vamos a necesitar
poder entrar con **root** desde una aplicación web o de forma remota. Entonces
solo necesitamos darle una *password* a dicho usuario:

```bash
MariaDB [(none)]> ALTER USER 'root'@'localhost' IDENTIFIED BY 's3cr3t';
Query OK, 0 rows affected (0.013 sec)

MariaDB [(none)]> exit
Bye
gerard@database:~$
```

Ahora deberíamos poder entrar desde cualquier cliente con el usuario **root**
y la *password* elegida.

```bash
gerard@database:~$ mysql -u root -p
Enter password:
...
MariaDB [(none)]>
```

En el caso concreto del cliente de terminal `mysql` podemos evitar indicar
la contraseña declarando un fichero `~/.my.cnf` con los valores por defecto.

```bash
gerard@database:~$ cat .my.cnf
[client]
user=root
password=s3cr3t
database=mysql
gerard@database:~$
```

```bash
gerard@database:~$ mysql
...
MariaDB [mysql]>
```

A partir de este punto, solo necesitaríamos crear las bases de datos
necesarias para cada aplicación con un usuario dedicado, para limitar
los desastres que se puedan hacer desde un solo sitio.

```bash
MariaDB [mysql]> CREATE DATABASE myblog;
Query OK, 1 row affected (0.000 sec)

MariaDB [mysql]> CREATE USER 'mybloguser'@'%' IDENTIFIED BY 'myblogpassword';
Query OK, 0 rows affected (0.005 sec)

MariaDB [mysql]> GRANT ALL PRIVILEGES ON myblog.* TO 'mybloguser'@'%';
Query OK, 0 rows affected (0.040 sec)

MariaDB [mysql]>
```

### Instalando phpmyadmin (opcional)

Esta es una herramienta muy cómoda en un servidor de bases de datos **MySQL**,
que nos permite gestionar fácilmente todos los aspectos de las bases de datos
gestionadas; desde la creación de bases de datos y tablas y sus datos, hasta
la gestión de usuarios y *backups*.

**WARNING**: Esta herramienta es tipo web, y abre el servidor a accesos remotos.
Usadla con cabeza y en entornos aislados o de test.

Para obtener esta herramienta, solo necesitamos instalar dos paquetes:
**phpmyadmin** y **php** (por algún motivo, las dependencias de **phpmyadmin**
no incluyen el intérprete de **PHP**, pero sí el **apache** para servirlo).

```bash
gerard@database:~$ sudo apt install php phpmyadmin
...
gerard@database:~$
```

**TRUCO**: Podemos indicarle que queremos configurar **apache2** y **phpmyadmin**
automáticamente para ahorrarnos trabajo posterior. Es importante en este caso no
haber cambiado la contraseña de **root**.

En este punto ya tenemos el **PHPMyAdmin** funcional en `http://localhost/phpmyadmin/`,
aunque considerando que solamente se sirve esta aplicación, podemos moverla a `http://localhost/`.

```bash
gerard@database:/etc/apache2/conf-available$ pwd
/etc/apache2/conf-available
gerard@database:/etc/apache2/conf-available$ diff phpmyadmin.conf.orig phpmyadmin.conf
3c3
< Alias /phpmyadmin /usr/share/phpmyadmin
---
> Alias / /usr/share/phpmyadmin/
gerard@database:/etc/apache2/conf-available$ sudo systemctl restart apache2
gerard@database:/etc/apache2/conf-available$
```

**TRUCO**: En este punto no se puede acceder al **PHPMyAdmin** con el usuario
**root**, porque la autenticación se hace con *password* y el usuario **root**
no tiene. Es un buen momento para darle una contraseña, como se indica más arriba.

Si no queremos tener que autenticarnos en el **PHPMyAdmin**, podemos modificar
su configuración para que lo haga automáticamente:

```bash
gerard@database:/etc/phpmyadmin$ pwd
/etc/phpmyadmin
gerard@database:/etc/phpmyadmin$ diff config.inc.php.orig config.inc.php
59c59,61
<     $cfg['Servers'][$i]['auth_type'] = 'cookie';
---
>     $cfg['Servers'][$i]['auth_type'] = 'config';
>     $cfg['Servers'][$i]['user'] = 'root';
>     $cfg['Servers'][$i]['password'] = 's3cr3t';
gerard@database:/etc/phpmyadmin$
```

**WARNING**: Esto dará acceso a todas las bases de datos a cualquiera que pueda
llegar a la aplicación web. Revisad muy bien vuestras políticas de seguridad y accesos.

La operativa del servidor desde la herramienta es muy simple e intuitiva.
Investigad su uso con cariño porque os ayudará mucho. Por ejemplo, para crear
usuario y base de datos "de aplicación", basta con ir a "Cuentas de usuario",
"Agregar cuenta de usuario" y recordar de darle al *checkbox* "Crear base de
datos con el mismo nombre y otorgar todos los privilegios".

## Desplegando en un Docker Swarm

Hay algunas veces que desplegamos en **Docker**, porque es lo que utilizamos o
porque es más cómodo en un entorno concreto. En estos casos, el despliegue se
vuelve tan fácil como un *stack* dedicado de "poner y quitar". Se deja el *stack*
aquí mismo para referencias futuras:

```bash
gerard@docker:~/mariadb$ cat stack.yml
version: '3'
services:
  mariadb:
    image: mariadb:10.6
    environment:
      MARIADB_ROOT_PASSWORD: ${MARIADB_ROOT_PASSWORD}
    volumes:
      - mariadb_data:/var/lib/mysql
    ports:
      - "3306:3306"
  phpmyadmin:
    image: phpmyadmin:5.1
    environment:
      PMA_HOST: mariadb
      PMA_USER: root
      PMA_PASSWORD: ${MARIADB_ROOT_PASSWORD}
    ports:
      - "8080:80"
volumes:
  mariadb_data:
gerard@docker:~/mariadb$
```

```bash
gerard@docker:~/mariadb$ cat deploy.sh
#!/bin/bash

source secret_vars
export MARIADB_ROOT_PASSWORD

docker stack deploy -c stack.yml mariadb
gerard@docker:~/mariadb$
```

```bash
gerard@docker:~/mariadb$ cat secret_vars
MARIADB_ROOT_PASSWORD="s3cr3t"
gerard@docker:~/mariadb$
```
