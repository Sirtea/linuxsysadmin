---
title: "Dirección IP compartida manualmente entre servidores"
slug: "direccion-ip-compartida-manualmente-entre-servidores"
date: 2016-07-11
categories: ['Operaciones']
tags: ['linux', 'failover', 'arping']
---

Cuando hablamos de alta disponibilidad, uno de los métodos mas utilizados es el **failover**. La idea es que una de las máquinas es la que asume la totalidad del servicio, y el resto están preparadas para ejercer la misma función en el caso de que la primera deje de funcionar.<!--more-->

En este campo hay varias soluciones como **keepalived** y **pacemaker**, pero en este artículo se pretende mostrar los conceptos mas básicos; haciendo manualmente los pasos y entendiendo como funciona todo, desde un punto de vista didáctico.

Realmente esto es un intento mío para hacer una solución de alta disponibilidad, pero se quedó a medias. Lo escribo porque creo que puede ser útil en otro momento.

## Punto de partida

Tenemos dos servidores normales, que vamos a convertir en un **cluster** con configuración manual de **failover**.

```bash
root@lxc:~# lxc-ls -f
NAME     STATE    IPV4      IPV6  AUTOSTART
-------------------------------------------
server1  RUNNING  10.0.0.3  -     NO
server2  RUNNING  10.0.0.4  -     NO
root@lxc:~#
```

Digamos que queremos dar un servicio web, aunque podríamos hacer de balanceadores, servidores de aplicación o lo que se necesite, en general.

Vamos a poner un servidor web **nginx**, que sirva una página HTML que nos indique la máquina que recibe las peticiones, a modo de comprobación.

Vamos a instalar el servicio **nginx** en ambas máquinas:

```bash
root@server1:~# apt-get install -y nginx-light
...  
root@server1:~#

root@server2:~# apt-get install -y nginx-light
...  
root@server2:~#
```

Creamos una página HTML con el nombre de cada máquina para ver quien recibe la petición HTTP:

```bash
root@server1:~# hostname > /var/www/html/index.html
root@server1:~#

root@server2:~# hostname > /var/www/html/index.html
root@server2:~#
```

Y comprobamos que podemos diferenciar el servidor destino que recibe cada una de las peticiones:

```bash
root@lxc:~# wget -qO- http://10.0.0.3/
server1
root@lxc:~# wget -qO- http://10.0.0.4/
server2
root@lxc:~#
```

## Moviendo la dirección IP compartida

Además de la dirección IP de cada máquina, vamos a tener una que represente al miembro activo del **cluster**, que por ejemplo, será la 10.0.0.2

Si solo una de las máquinas tiene esa dirección IP asignada, el truco ya está hecho. Sin embargo, ¿que pasará si los dos nodos tienen la dirección IP compartida asignada? Puede pasará cualquier cosa.

Para evitar este caso, un nodo que asuma el rol de primario también va a forzar a sus vecinos a actualizar sus tablas ARP, consiguiendo así **robar** la dirección IP. Esto se puede conseguir con el comando **arping** y por lo tanto, hay que instalarlo.

```bash
root@server1:~# apt-get install -y iputils-arping
...  
root@server1:~#

root@server2:~# apt-get install -y iputils-arping
...  
root@server2:~#
```

### Promocionando server1 a primario

El proceso de **failover** consiste en agenciarse la dirección compartida. Para ello, tenemos que añadir una nueva dirección IP en nuestra interfaz de red. Como es posible que esta IP pertenezca a otro servidor, hay que lanzar el comando **arping**.

```bash
root@server1:~# ip addr add 10.0.0.2/24 dev eth0
root@server1:~# arping -U -c1 10.0.0.2
ARPING 10.0.0.2 from 10.0.0.2 eth0
Sent 1 probes (1 broadcast(s))
Received 0 response(s)
root@server1:~#
```

El siguiente paso, aunque opcional, es educado; el servidor desplazado de primario a reserva, no necesita tener esa dirección asignada, en caso de que la tuviera (que no es el caso, pero no importa y lo ignoramos).

```bash
root@server2:~# ip addr del 10.0.0.2/24 dev eth0
RTNETLINK answers: Cannot assign requested address
root@server2:~#
```

El resultado es que *server1* tiene dos direcciones asignadas: la suya propia y la compartida, mientras que *server2* solo tiene la suya.

```bash
root@lxc:~# lxc-ls -f
NAME     STATE    IPV4                IPV6  AUTOSTART
-----------------------------------------------------
server1  RUNNING  10.0.0.2, 10.0.0.3  -     NO
server2  RUNNING  10.0.0.4            -     NO
root@lxc:~#
```

Y nuestras peticiones web, caen efectivamente en *server1*.

```bash
root@lxc:~# wget -qO- http://10.0.0.2/
server1
root@lxc:~#
```

### Cambiando el primario de server1 a server2

El proceso es el mismo, pero al revés: *server2* reclama la dirección compartida y *server1* se deshace de ella por cortesía.

```bash
root@server2:~# ip addr add 10.0.0.2/24 dev eth0
root@server2:~# arping -U -c1 10.0.0.2
ARPING 10.0.0.2 from 10.0.0.2 eth0
Sent 1 probes (1 broadcast(s))
Received 0 response(s)
root@server2:~#

root@server1:~# ip addr del 10.0.0.2/24 dev eth0
root@server1:~#
```

Y nuevamente, podemos ver donde está la dirección compartida y en que servidor caen nuestras peticiones.

```bash
root@lxc:~# lxc-ls -f
NAME     STATE    IPV4                IPV6  AUTOSTART
-----------------------------------------------------
server1  RUNNING  10.0.0.3            -     NO
server2  RUNNING  10.0.0.2, 10.0.0.4  -     NO
root@lxc:~#

root@lxc:~# wget -qO- http://10.0.0.2/
server2
root@lxc:~#
```

## Usos poco éticos de esta técnica

Estamos en nuestra oficina y no queremos trabajar, con la excusa de que no hay internet. ¿Que nos impide asignarnos la dirección del *router* a nuestra máquina? Esto haría que toda la oficina usara nuestra máquina de *gateway*, que por supuesto, no sabe salir a internet, cortando efectivamente el tráfico exterior.

Parece que esta idea ya se les ocurrió a los fabricantes de *routers*, así que sus productos ya se preocupan de ir reclamando su dirección IP. Así que os puede funcionar puntualmente, y si queréis hacer la broma por un periodo largo, tendréis que librar una batalla de *arpings* contra el *router*.
