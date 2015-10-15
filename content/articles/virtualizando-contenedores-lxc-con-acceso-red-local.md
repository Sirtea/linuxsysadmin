Title: Virtualizando contenedores LXC con acceso a la red local
Slug: virtualizando-contenedores-lxc-con-acceso-red-local
Date: 2015-10-15 12:00
Category: Virtualización
Tags: linux, debian, jessie, lxc, bridge, firehol



En este tutorial se propone montar un servidor de contenedores LXC,
de forma que todos los contenedores queden expuestos a la misma red
que el servidor que los aloja. Para protegerlos de posibles ataques
de esta red, pondremos un firewall basado en *iptables* mediante una
capa de abstracción llamada *firehol*.

Para conseguir este objetivo, se van a usar las siguientes tecnologías:

* **Debian jessie**: Es necesario usar alguna distribución de linux para hacer funcionar LXC
* **LXC**: Tecnología que permite aislar los contenedores entre sí y darles entidad propia
* **Bridges**: Un bridge es en software el equivalente a un switch hardware
* **Firehol**: Una serie de scripts para construir firewalls basados en iptables de forma fácil

En cuanto a las capacidades hardware, vamos a hacer el tutorial con un equipo
de capacidades modestas, virtualizado en una máquina virtual VirtualBox.

* **CPUs**: 1
* **Memoria**: 256 Mb
* **Disco**: 2 Gb
* **Red**: 1 interfaz (*eth0*) *host-only* o *bridged* con IP fija

Partimos de una distribución *Debian jessie* instalada con un CD *netinstall*
y con el único paquete instalado *openssh-server*, para mi comodidad.

## Preparar el servidor

El primer paso consiste en instalar las tecnologías usadas:

```bash
root@lxc:~# apt-get install bridge-utils firehol lxc
Leyendo lista de paquetes... Hecho
Creando árbol de dependencias       
Leyendo la información de estado... Hecho
...
Configurando lxc (1:1.0.6-6+deb8u1) ...
Configurando dh-python (1.20141111-2) ...
Procesando disparadores para libc-bin (2.19-18+deb8u1) ...
Procesando disparadores para systemd (215-17+deb8u2) ...
root@lxc:~# 
```

Acto seguido debemos modificar la configuración de red, para que la interfaz
de red de la máquina represente la salida de todas las IPs que maneja el bridge
y para que el host obtenga una dirección de red en el bridge.

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

auto lxc0
iface lxc0 inet static
    bridge_ports eth0
    address 192.168.56.4
    netmask 255.255.255.0
    gateway 192.168.56.1
root@lxc:~# 
```

En este punto es necesario reconfigurar la red, siendo especialmente importante
que *eth0* quede sin dirección IP asignada (en mi caso tuve que reiniciar la máquina).

```bash
root@lxc:~# ip addr
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default 
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
    inet 127.0.0.1/8 scope host lo
       valid_lft forever preferred_lft forever
    inet6 ::1/128 scope host 
       valid_lft forever preferred_lft forever
2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc pfifo_fast master lxc0 state UP group default qlen 1000
    link/ether 08:00:27:e4:0a:60 brd ff:ff:ff:ff:ff:ff
3: lxc0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue state UP group default 
    link/ether 08:00:27:e4:0a:60 brd ff:ff:ff:ff:ff:ff
    inet 192.168.56.4/24 brd 192.168.56.255 scope global lxc0
       valid_lft forever preferred_lft forever
    inet6 fe80::a00:27ff:fee4:a60/64 scope link 
       valid_lft forever preferred_lft forever
root@lxc:~# 
```

El último paso consiste en activar el firewall con unas reglas básicas,
para proteger el equipo anfitrión de posibles ataques o intrusiones, dejando
solamente el acceso a SSH. Con firehol es posible combinar el demonio *knockd*
para ocultar el puerto tras una secuencia de port knocking; en principio
sería suficiente con forzar la entrada SSH por claves RSA.

```bash
root@lxc:~# cat /etc/firehol/firehol.conf 
interface lxc0 world
    policy drop
    protection strong
    server ssh accept
    client all accept
root@lxc:~# 
```

Hay que modificar otro fichero para permitir el inicio del firewall:

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

Y para acabar, (re)iniciamos el servicio firehol.

```bash
root@lxc:~# service firehol restart

Broadcast message from systemd-journald@lxc (Wed 2015-10-14 16:59:30 CEST):

FireHOL[620]: Firewall has been stopped. Policy is ACCEPT EVERYTHING!


Message from syslogd@lxc at Oct 14 16:59:30 ...
 FireHOL[493]: Firewall has been stopped. Policy is ACCEPT EVERYTHING!
root@lxc:~# 
```

## Creación de contenedores

La creación de contenedores pasa por usar las herramientas estándar
de la distribución, a lo solo tendremos que modificar algunas
configuraciones propias de nuestra red.

Creamos un contenedor *webserver* como demostración. La primera que se
crea es un poco lenta porque hace un *debootstrap* de una distribución
debian estable para crear una cache en */var/cache/lxc*; las siguientes
se benefician de esta caché y solo la actualizan, acelerando el proceso.

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
Local time is now:      Wed Oct 14 17:26:37 CEST 2015.
Universal Time is now:  Wed Oct 14 15:26:37 UTC 2015.

Root password is 'sFj7Jm9N', please change !
root@lxc:~# 
```

Acabada la generación del contenedor, vamos a configurarle algunos
parámetros; que tenga una interfaz *eth0* activa y enchufada al bridge
*lxc0*, y que el contenedor se autoinicie en cada reinicio del anfitrión.

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

Y para que su interfaz de red sea funcional, vamos a configurarle una
dirección IP. Todo esto se hace en los ficheros habituales, teniendo
en cuenta que un contenedor es una jaula, y que esta se encuentra en
*/var/lib/lxc/webserver/rootfs/*

```bash
root@lxc:~# cat /var/lib/lxc/webserver/rootfs/etc/network/interfaces
auto lo
iface lo inet loopback

auto eth0
iface eth0 inet static
    address 192.168.56.10
    netmask 255.255.255.0
    gateway 192.168.56.1
root@lxc:~# 
```

El contenedor ya está funcional, y se puede levantar:

```bash
root@lxc:~# lxc-start -n webserver -d
root@lxc:~# 
```

Sin embargo, el firewall impide que se llegue al mismo; tendremos que
poner reglas para permitir el flujo de red hacia la nueva dirección IP
configurada para el contenedor. Esto se consigue con reglas de *forward*
que entren por el bridge y salgan por el mismo hacia nuestro contenedor.

Ya de paso habilitamos reglas para que todo lo que pase por el bridge
hacia internet se permita. Como particularidad de nuestra red, el
servidor anfitrión tiene un servidor DNS *dnsmasq*; así que añadimos
también esa ruta.

Por ejemplo, suponiendo que queremos habilitar el servicio *SSH* (tcp 22)
y el puerto del servicio *HTTP* (tcp 80), pondremos lo siguiente en la
configuración del firewall (tras lo cual lo reiniciaremos):

```bash
root@lxc:~# cat /etc/firehol/firehol.conf 
interface lxc0 world
    policy drop
    protection strong
    server ssh accept
    client all accept

router internal inface lxc0 outface lxc0
    policy drop
    client all accept
    group with dst not "${UNROUTABLE_IPS}"
        route all accept
    group end
    group with dst 192.168.56.1
        route dns accept
    group end
    group with dst 192.168.56.10
        route ssh accept
        route http accept
    group end
root@lxc:~# service firehol restart

Broadcast message from systemd-journald@lxc (Wed 2015-10-14 17:43:38 CEST):

FireHOL[8690]: Firewall has been stopped. Policy is ACCEPT EVERYTHING!


Message from syslogd@lxc at Oct 14 17:43:38 ...
 FireHOL[8565]: Firewall has been stopped. Policy is ACCEPT EVERYTHING!
root@lxc:~# 
```

Y solamente queda entrar al contenedor, por ejemplo por *SSH* para
instalar lo que se necesite; en este caso con un *nginx* sería
suficiente como demostración.

```bash
gerard@workstation:~$ ssh root@192.168.56.10
root@192.168.56.10's password: 

The programs included with the Debian GNU/Linux system are free software;
the exact distribution terms for each program are described in the
individual files in /usr/share/doc/*/copyright.

Debian GNU/Linux comes with ABSOLUTELY NO WARRANTY, to the extent
permitted by applicable law.
root@webserver:~# apt-get install nginx-light
Leyendo lista de paquetes... Hecho
Creando árbol de dependencias... Hecho
Se instalarán los siguientes paquetes extras:
  nginx-common
Paquetes sugeridos:
  fcgiwrap nginx-doc ssl-cert
Se instalarán los siguientes paquetes NUEVOS:
  nginx-common nginx-light
0 actualizados, 2 nuevos se instalarán, 0 para eliminar y 0 no actualizados.
Se necesita descargar 439 kB de archivos.
Se utilizarán 1.040 kB de espacio de disco adicional después de esta operación.
¿Desea continuar? [S/n] s
...
Configurando nginx-common (1.6.2-5) ...
Configurando nginx-light (1.6.2-5) ...
Procesando disparadores para systemd (215-17+deb8u2) ...
root@webserver:~# 
```

Y con esto ya tenemos nuestro contenedor en marcha y ofreciendo
servicios en nuestra red local de forma segura.
