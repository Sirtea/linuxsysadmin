Title: Creando un entorno escalable (I)
Slug: creando-un-entorno-escalable
Date: 2016-02-29 08:00
Category: Sistemas
Tags: linux, entorno, escalable
Series: Creando un entorno escalable



Mucha gente tiene un servidor único para alojar páginas web dinámicas, por ejemplo con **PHP** y con **MySQL**. Sin embargo, a veces esto puede resultar insuficiente; nos puede interesar tener un entorno de bajas especificaciones y de bajo coste, pero preparado crecer al mismo ritmo que lo hacen los usuarios.

En este caso, el truco consiste en hacer trabajar a varias máquinas como si fueran una sola, escondidas en una o varias subredes privadas y poniendo un representante único de todo el sistema (que es el que va a recibir **todas** las peticiones).

Este representante suele ser lo que llamamos un **balanceador de carga**, cuya función es repartir el trabajo entre varios servidores de **backend**. Al tratarse solo de un "policía de tráfico" su rendimiento es elevado con unas especificaciones modestas, mientras que los servidores de **backend** consiguen resolver las mismas peticiones por unidad de tiempo; la mejora reside en que pueden haber varios servidores de **backend** resolviendo peticiones en paralelo.

Normalmente, estos servidores de **backend** suelen conectarse a otros servicios (idealmente en otros servidores) para cumplir con sus funciones, por ejemplo con un grupo de servidores de **bases de datos** dispuestos como un *cluster*, que suelen tener una topología propia.

En este tutorial se va a montar un entorno pequeño de estas características, sirviendo una *API* pública en servidores de **backend**, una aplicación web de administración de los datos de la *API* en un servidor de **backoffice**, y un *cluster* de **bases de datos** representado por una *replica set* de MongoDB; todo ello oculto en una red privada y un balanceador usando *virtualhosts* para ir a una aplicación u otra según el protocolo usado.

Esto es lo que propongo montar:

![Entorno propuesto]({filename}/images/entorno_propuesto.png)

Para ello, vamos a crear las máquinas virtuales necesarias. En este caso, voy a usar mi servidor de **virtualización con LXC**, tal como lo monté en [este artículo](/2015/11/virtualizando-contenedores-lxc-tras-bridge-interno.html).

```bash
root@lxc:~# lxc-ls -f
NAME        STATE    IPV4        IPV6  AUTOSTART
------------------------------------------------
backend1    RUNNING  10.0.0.3    -     YES
backend2    RUNNING  10.0.0.4    -     YES
backoffice  RUNNING  10.0.0.5    -     YES
frontend    RUNNING  10.0.0.2    -     YES
mongo1      RUNNING  10.0.0.6    -     YES
mongo2      RUNNING  10.0.0.7    -     YES
root@lxc:~#
```

Para hacer mas fácil las referencias a las diferentes máquinas, vamos a utilizar sus nombres; como no me apetece montar un servidor DNS, vamos a ponerlas en el fichero */etc/hosts* en todas las máquinas virtuales.

```
root@mongo1:~# cat /etc/hosts
...
10.0.0.2        frontend
10.0.0.3        backend1
10.0.0.4        backend2
10.0.0.5        backoffice
10.0.0.6        mongo1
10.0.0.7        mongo2
...
root@mongo1:~#
```

Vamos a ir montando todas las máquinas una por una; es laborioso pero no es nada complicado. Las reglas del *firewall* también las iremos explicando según el rol de cada máquina.

El orden de montaje no es importante, pero como queremos ir comprobando en cada caso que va funcionando, se montarán de acuerdo al orden de requisitos:

* El *cluster* de **bases de datos**, que no tiene dependencias.
* Los servidores de **backend** y **backoffice** que dependen del *cluster* de **bases de datos**.
* Finalmente, pondremos el servidor de **frontend**, con los *virtualhosts* y el balanceador, lanzando las peticiones contra los **backends** y el **backoffice**.

***Sabiendo lo que vamos a montar, solo queda decir: ¡Manos a la obra!***
