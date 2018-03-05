Title: Un gateway con Debian, iptables y dnsmasq
Slug: un-gateway-con-debian-iptables-y-dnsmasq
Date: 2018-03-12 10:00
Category: Sistemas
Tags: linux, debian, stretch, gateway, iptables, dnsmasq



En algunas ocasiones no nos basta con tener un servidor único. Queremos tener un conjunto de servidores que se comuniquen abiertamente entre ellos usando una red privada, pero solo queremos exponer al mundo una sola dirección IP. El resto de servidores necesitan acceso a internet a través de un representante.

Este representante, llamando *gateway*, es un servidor con una interfaz en la red privada y una en la red pública, de forma que los paquetes de red puedan fluir desde cualquier servidor hasta internet a través de este representante.

De forma obligatoria, un *gateway* solo necesita hacer dos cosas:

* Permitir el reenvío (o *forward*) de paquetes a través del servidor *gateway*.
* Enmascarar la dirección de origen mediante NAT para que los paquetes sepan como volver desde internet.

Idealmente, suelen hacer otras funciones y ofrecer servicios a sus servidores protegidos, como por ejemplo:

* Funciones de *firewall* para proteger de accesos no autorizados contra la red protegida.
* Servidor DHCP para asignar direcciones IP a los servidores de la red interna.
* Servidor DNS para que los servidores de la red interna se conozcan entre ellos.

Las 3 primeras funciones quedan fácilmente cubiertas en el mismo *kernel* de un sistema *linux*; los servidores DHCP y DNS se pueden añadir fácilmente con un servicio adicional llamado **dnsmasq**.

## El servidor base

Partimos de un servidor **Debian stretch** con dos direcciones asignadas, una en cada red.

* **enp0s3**: La interfaz que da al exterior, configurada como nos sea conveniente.
* **enp0s8**: Esta es la interfaz que da a la red interna, con una dirección IP estática (en este caso 10.0.0.1/24).

**NOTA**: Vamos a retrasar la aplicación de todas las configuraciones hasta el final, momento en el que reiniciaremos el servidor.

## Las funciones básicas: forward, masquerade y firewall

El primer paso es permitir el paso de paquetes de red a través de nuestro *gateway*. Ello se consigue configurando los parámetros del sistema.

```bash
root@gateway:~# tail -1 /etc/sysctl.conf
net.ipv4.ip_forward = 1
root@gateway:~#
```

El resto se consigue mediante el módulo del *kernel* llamado *netfilter*. La herramienta que modifican *netfilter* se llama **iptables**, y por comodidad, vamos a utilizar el paquete **iptables-persistent**.

```bash
root@gateway:~# apt-get install iptables-persistent
...
root@gateway:~#
```

Ahora nos falta crear el fichero de reglas que será cargado en cada reinicio:

```bash
root@gateway:~# cat /etc/iptables/rules.v4
*nat
-A POSTROUTING -o enp0s3 -j MASQUERADE
COMMIT

*filter
-A INPUT -i lo -j ACCEPT
-A INPUT -i enp0s3 -p tcp -m tcp --dport 22 -j ACCEPT
-A INPUT -m state --state RELATED,ESTABLISHED -j ACCEPT
-A INPUT -i enp0s3 -j DROP
COMMIT
root@gateway:~#
```

La regla de la tabla *nat* es la que enmascara la dirección origen y pone la de salida del *gateway*, para que los paquetes sepan volver.

El resto de reglas en la tabla de *filter* hacen la función de un *firewall* básico, que acepta conexiones que vengan del mismo servidor, las conexiones SSH, las conexiones que ya estén establecidas o estén pasando a través y descarta todo el resto.

**NOTA**: Ahora solo haría falta reiniciar el servidor, pero lo retrasamos para instalar el resto de servicios.

## Algunos servicios útiles: DHCP y DNS

Todos los servicios que queramos ofrecer en la red interna se hacen igual: instalar el paquete que lo proporciona y configurarlo. En este caso, el paquete **dnsmasq** ofrece ambos servicios.

```bash
root@gateway:~# apt-get install dnsmasq
...
root@gateway:~#
```

La configuración del servicio se hace en el fichero */etc/dnsmasq.conf*. Sin embargo es un fichero muy largo; vamos a beneficiarnos de la carpeta */etc/dnsmasq.d/* para añadir nuestras configuraciones. Lo hago en dos ficheros, de forma que tengamos la configuración organizada en dos ficheros, en función de la frecuencia de modificación.

```bash
root@gateway:~# cat /etc/dnsmasq.d/00-base
interface=enp0s8
dhcp-range=10.0.0.200,10.0.0.250,1h
root@gateway:~# cat /etc/dnsmasq.d/01-hosts
#dhcp-host=server,10.0.0.2,1h
root@gateway:~#
```

De esta forma, cuando queramos añadir un nuevo servidor en la red interna con dirección fija, podemos configurarlo para usar DHCP, poner una nueva línea en el fichero */etc/dnsmasq.d/01-hosts* similar a la de comentada de arriba, y reinicar el servicio **dnsmasq**.

Como *bonus*, el servidor *gateway* va a poder resolver por DNS el nombre declarado por el servidor protegido, al que ya dio dirección por DHCP. Para que los servidores de la red interna puedan resolver por nombre la máquina *gateway*, solo necesitamos añadir esa relación en el fichero */etc/hosts* del *gateway*:

```bash
root@gateway:~# grep gateway /etc/hosts
10.0.0.1        gateway
root@gateway:~#
```

Es importante que nuestro servidor *gateway* utilice *localhost* como primer DNS, de forma que se beneficie de las funciones *DNS cache* y pueda resolver los servidores de la red interna por su nombre. Esto se hace poniendo *127.0.0.1* en el fichero */etc/resolv.conf*.

**TRUCO**: Como configuré la interfaz principal por DHCP y el fichero */etc/resolv.conf* se sobreescribe de forma automática, podemos instruir el cliente DHCP para que lo incluya antes de los que reciba por DHCP.

```bash
root@gateway:~# tail -1 /etc/dhcp/dhclient.conf
prepend domain-name-servers 127.0.0.1;
root@gateway:~#
```

## Aplicar los cambios

En este punto podemos reiniciar el servidor, para que apliquen todos los cambios.

```bash
root@gateway:~# reboot
...
```

## Añadir un servidor en la red interna

Un servidor que se quiera unir a la red puede hacerlo con una dirección estática, pero es mas fácil hacerlo por DHCP; basta con tenerlo configurado para usar DHCP.

**TRUCO**: Si clonamos una máquina virtual, es necesario asegurarse que la dirección MAC de la interfaz cambia, ya que la relación entre el servidor y su IP se guarda usando la dirección MAC, y por lo tanto, no deben haber dos iguales.

**TRUCO**: Podemos eliminar la relación *localhost* del servidor con su nombre en */etc/hosts*; **dnsmasq** resuelve eso por nosotros y para otros servidores de la red.

Si queremos que tenga una dirección fija, se puede hacer fácilmente. Necesitamos configurar el servidor DHCP para que asigne una IP concreta basándonos en el nombre del servidor, y recargar este servicio.

```bash
root@gateway:~# cat /etc/dnsmasq.d/01-hosts
dhcp-host=database,10.0.0.5,1h
root@gateway:~# service dnsmasq restart
root@gateway:~#
```

Solo faltará darle un nombre al servidor candidato en en */etc/hostname* y reiniciarlo. Tanto la dirección IP, el *gateway* por defecto y el servidor DNS se cargan en la resolución DHCP.
