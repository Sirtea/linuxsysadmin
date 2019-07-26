---
title: "Virtualizando contenedores LXC tras bridge interno"
slug: "virtualizando-contenedores-lxc-tras-bridge-interno"
date: 2015-11-23
categories: ['Virtualización']
tags: ['linux', 'debian', 'jessie', 'lxc', 'bridge', 'firehol']
---

En un artículo anterior propusimos virtualizar contenedores en la red de la máquina *host*. Sin embargo, puede ser mas interesante esconder los contenedores detrás de una máquina que haga las funciones de *host* y de *firewall*. Expondremos una serie de puertos tras la misma dirección *IP* mediante el protocolo *NAT*.<!--more-->

Para conseguir este objetivo, se van a usar las siguientes tecnologías:

* **Debian jessie**: Es necesario usar alguna distribución de linux para hacer funcionar LXC
* **LXC**: Tecnología que permite aislar los contenedores entre sí y darles entidad propia
* **Bridges**: Un bridge es en software el equivalente a un switch hardware
* **Firehol**: Una serie de scripts para construir firewalls basados en iptables de forma fácil

En cuanto a las capacidades hardware, vamos a hacer el tutorial con un equipo de capacidades modestas, virtualizado en una máquina virtual VirtualBox.

* **CPUs**: 1
* **Memoria**: 256 Mb
* **Disco**: 2 Gb
* **Red**: 1 interfaz (*eth0*) *host-only* o *bridged* con IP fija

Partimos de una distribución *Debian jessie* instalada con un CD *netinstall* y con el único paquete instalado *openssh-server*, para mi comodidad.

## Preparar el servidor

El primer paso consiste en instalar las tecnologías usadas:

```bash
root@lxc:~# apt-get install bridge-utils firehol lxc
Leyendo lista de paquetes... Hecho
Creando árbol de dependencias       
Leyendo la información de estado... Hecho
...
Configurando lxc (1:1.0.6-6+deb8u2) ...
Configurando dh-python (1.20141111-2) ...
Procesando disparadores para libc-bin (2.19-18+deb8u1) ...
Procesando disparadores para systemd (215-17+deb8u2) ...
root@lxc:~# 
```

Ahora vamos a modificar la configuración de red, para habilitar el *bridge* en el que vamos a conectar el resto de contenedores virtualizados. Como dato importante, se define una interfaz falsa en la directiva *bridge_ports* para que la *unit* de red lo levante automáticamente.

**ANTES**:

```bash
root@lxc:~# cat /etc/network/interfaces
source /etc/network/interfaces.d/*

auto lo
iface lo inet loopback

auto eth0
iface eth0 inet static
	address 192.168.56.4
	netmask 255.255.255.0
	gateway 192.168.56.1
root@lxc:~# 
```

**DESPUES**:

```bash
root@lxc:~# cat /etc/network/interfaces
source /etc/network/interfaces.d/*

auto lo
iface lo inet loopback

auto eth0
iface eth0 inet static
	address 192.168.56.4
	netmask 255.255.255.0
	gateway 192.168.56.1

auto lxc0
iface lxc0 inet static
	bridge_ports dummy
	address 10.0.0.1
	netmask 255.255.255.0
root@lxc:~# 
```

Ahora toca reiniciar el servicio de red, para que el nuevo *bridge* quede configurado como debe estarlo.

```bash
root@lxc:~# service networking restart
root@lxc:~# 
```

El siguiente paso consiste en poner las reglas de *firewall* necesarias para proteger al equipo anfitrión y para permitirle actuar como *gateway* para los contenedores tras el *bridge*.


```bash
root@lxc:~# cat /etc/firehol/firehol.conf 
interface eth0 world
	policy drop
	protection strong
	server ssh accept
	client all accept

interface lxc0 lan
	policy drop
	client all accept

router lan2world inface lxc0 outface eth0
	masquerade
	route all accept
root@lxc:~# 
```

Hay que modificar otro fichero para permitir el inicio del *firewall*:

**ANTES**:

```bash
root@lxc:~# grep START /etc/default/firehol 
#To enable firehol at startup set START_FIREHOL=YES
START_FIREHOL=NO
root@lxc:~# 
```

**DESPUES**:

```bash
root@lxc:~# grep START /etc/default/firehol 
#To enable firehol at startup set START_FIREHOL=YES
START_FIREHOL=YES
root@lxc:~# 
```

Y para acabar, reiniciamos el servicio *firehol*.

```bash
root@lxc:~# service firehol restart
...
root@lxc:~# 
```

## Creación de contenedores

La creación de contenedores pasa por usar las herramientas estándar de la distribución, a lo solo tendremos que modificar algunas configuraciones propias de nuestra red.

Creamos un contenedor *webserver* como demostración. La primera que se crea es un poco lenta porque hace un *debootstrap* de una distribución *Debian estable* para crear una cache en */var/cache/lxc*; las siguientes se benefician de esta caché y solo la actualizan, acelerando el proceso.

```bash
root@lxc:~# lxc-create -n webserver -t debian
debootstrap is /usr/sbin/debootstrap
Checking cache download in /var/cache/lxc/debian/rootfs-jessie-i386 ... 
Downloading debian minimal ...
...

I: Base system installed successfully.
Download complete.
Copying rootfs to /var/lib/lxc/webserver/rootfs...
...
Current default time zone: 'Europe/Madrid'
Local time is now:      Mon Nov 23 16:29:36 CET 2015.
Universal Time is now:  Mon Nov 23 15:29:36 UTC 2015.

Root password is 'E3+K9SpU', please change !
root@lxc:~# 
```

Acabada la generación del contenedor, vamos a configurarle algunos parámetros; que tenga una interfaz *eth0* activa y enchufada al bridge *lxc0*, y que el contenedor se inicie automáticamente en cada reinicio del anfitrión.

```bash
root@lxc:~# cat /var/lib/lxc/webserver/config 
...
lxc.start.auto = 1
lxc.network.type = veth
lxc.network.flags = up
lxc.network.link = lxc0
lxc.network.name = eth0
root@lxc:~# 
```

Y para que su interfaz de red sea funcional, vamos a configurarle una dirección IP. Todo esto se hace en los ficheros habituales, teniendo en cuenta que un contenedor es una jaula, y que esta se encuentra en */var/lib/lxc/webserver/rootfs/*

```bash
root@lxc:~# cat /var/lib/lxc/webserver/rootfs/etc/network/interfaces
auto lo
iface lo inet loopback

auto eth0
iface eth0 inet static
	address 10.0.0.2
	netmask 255.255.255.0
	gateway 10.0.0.1
root@lxc:~# 
```

El contenedor ya está funcional, y se puede levantar:

```bash
root@lxc:~# lxc-start -n webserver -d
root@lxc:~# 
```

Supongamos que este nuevo contenedor tiene un servidor web y queremos hacerlo disponible en puerto 80 del *host*, mediante el protocolo *NAT*. También se necesita definir una regla de *forward* para permitir ese tráfico. Se reinicia el servicio *firehol* para aplicar las nuevas reglas.

```bash
root@lxc:~# cat /etc/firehol/firehol.conf 
dnat 10.0.0.2:80 proto tcp dst 192.168.56.4 dport 80

interface eth0 world
	policy drop
	protection strong
	server ssh accept
	client all accept

interface lxc0 lan
	policy drop
	client all accept

router lan2world inface lxc0 outface eth0
	masquerade
	route all accept

router world2lan inface eth0 outface lxc0
	route http accept dst 10.0.0.2
root@lxc:~# service firehol restart
...
root@lxc:~# 
```

Ahora podemos acceder al servidor web instalado en el contenedor *webserver* mediante el puerto 80 del *host*.

Supongamos que tenemos otro contenedor con un servidor de aplicaciones escuchando en el puerto 8080 con dirección 10.0.0.3 y pretendemos que el contenedor original haga de *proxy HTTP*. Esta funcionalidad requiere que el contenedor *webserver* pueda conectarse al puerto 8080 del nuevo contenedor *appserver*. Esta regla de *forward* aplica a todas las conexiones que inician y finalizan en el *bridge*.

```bash
root@lxc:~# cat /etc/firehol/firehol.conf 
dnat 10.0.0.2:80 proto tcp dst 192.168.56.4 dport 80

interface eth0 world
	policy drop
	protection strong
	server ssh accept
	client all accept

interface lxc0 lan
	policy drop
	client all accept

router lan2world inface lxc0 outface eth0
	masquerade
	route all accept

router world2lan inface eth0 outface lxc0
	route http accept dst 10.0.0.2

router internal inface lxc0 outface lxc0
	route webcache accept src 10.0.0.2 dst 10.0.0.3
root@lxc:~# 
```

Y con eso tenemos nuestro *proxy HTTP* funcionando.
