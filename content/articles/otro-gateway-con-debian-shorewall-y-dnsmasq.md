Title: Otro gateway con Debian, shorewall y dnsmasq
Slug: otro-gateway-con-debian-shorewall-y-dnsmasq
Date: 2019-07-08 13:00
Category: Sistemas
Tags: linux, debian, stretch, buster, gateway, shorewall, dnsmasq



Hace ya algún tiempo escribí [un artículo]({filename}/articles/un-gateway-con-debian-iptables-y-dnsmasq.md) sobre como montar un *gateway* utilizando **Debian**, **iptables** y **dnsmasq**. Siguiendo mi política de ir actualizando los artículos más útiles, y visto la aparición en mi *toolbox* de [una nueva herramienta](/tag/shorewall.html) para simplificar **iptables**, le ha tocado una reescritura al artículo mencionado anteriormente.

Haciendo memoria, se trataba de un servidor *gateway* que permitía esconder una red privada de máquinas y actuar como representante. Lo que era una curiosidad, se volvió muy útil durante el proceso de *clusterización* de mi infraestructura, así como de los artículos de *clusteres* que he escrito desde entonces.

Las funciones de este *gateway* eran:

* Comunicar una red pública con una red privada:
    * Añadimos seguridad con reglas de *firewall* para restringir las comunicaciones indeseadas.
    * Utilizamos DNAT para "abrir los puertos" que queramos ofrecer a la red pública.
    * Haciendo SNAT o MASQUERADE para que los servidores de la red privada puedan acceder a internet.
* Ofrecer servicios a los servidores de la red interna, concretamente DNS y DHCP

## El servidor base

Partimos de un servidor **Debian Stretch** básico, con SSH y nada más. Por sus funciones va a necesitar dos interfaces de red, conectadas a cada una de las redes implicadas.

**UPDATE**: Se ha probado con éxito el mismo procedimiento con la **Debian Buster**, que este fin de semana se publicó como la nueva estable.

```bash
gerard@gateway:~$ ip a | grep "inet "
    inet 127.0.0.1/8 scope host lo
    inet 10.0.2.15/24 brd 10.0.2.255 scope global enp0s3
    inet 10.0.0.1/24 brd 10.0.0.255 scope global enp0s8
gerard@gateway:~$ 
```

Se ha dado una IP fija en la red privada por comodidad, y hemos dejado la red pública con su configuración habitual. Concretamente se ha hecho modificando el fichero `/etc/network/interfaces`, como sigue:

```bash
gerard@gateway:~$ cat /etc/network/interfaces
...
auto enp0s8
iface enp0s8 inet static
	address 10.0.0.1
	netmask 255.255.255.0
gerard@gateway:~$ 
```

**TRUCO**: En este punto, se entiende que la configuración está aplicada, sea manualmente o por reinicio del servidor.

## Instalando los servicios básicos

De entrada, vamos a necesitar los dos paquetes que nos ofrecen todos los servicios que necesitamos: **shorewall** y **dnsmasq**; los instalamos:

```bash
gerard@gateway:~$ sudo apt install shorewall dnsmasq
...
gerard@gateway:~$ 
```

### Configuración de dnsmasq: DNS y DHCP

Para que **dnsmasq** ofrezca el servicio DHCP, necesitaremos alguna configuración adicional; para mantener las configuraciones limpias, vamos a utilizar un fichero extra de configuración en `/etc/dnsmasq.d/`.

```bash
gerard@gateway:~$ cat /etc/dnsmasq.d/custom 
interface=enp0s8
dhcp-range=10.0.0.200,10.0.0.250,1h
#dhcp-host=server,10.0.0.251,1h
gerard@gateway:~$ 
```

El servicio DNS ya se ofrece por defecto, sin cambios adicionales. Solamente nos vamos a asegurar que el *gateway* se resuelva a una IP privada (no a 127.0.0.1), por si algún servidor de la red privada lo quisiera referenciar por nombre.

```bash
gerard@gateway:~$ grep gateway /etc/hosts
10.0.0.1	gateway
gerard@gateway:~$ 
```

Nos conviene que el *gateway* se use a sí mismo para resolver DNS, por ejemplo, para poder utilizar el nombre de los servidores privados en vez de su IP; esta relación solo la sabe **dnsmasq**. Como nuestro *gateway* consigue sus DNS por DHCP de la red pública, necesitamos configurar "algo" para que se añada su propia IP al principio de la lista; esto lo conseguimos en la configuración del **dhclient**:

```bash
gerard@gateway:~$ grep prepend /etc/dhcp/dhclient.conf
prepend domain-name-servers 127.0.0.1;
gerard@gateway:~$ 
```

### Configuración de shorewall: firewall y NAT

**AVISO**: La configuración de **shorewall** pasa por editar un puñado de ficheros de configuración. Para aquellos que no lo tengáis claro, podéis [leer más al respecto]({filename}/articles/protegiendo-servidores-con-iptables-usando-shorewall.md).

Para las funciones de *firewall*, empezaremos definiendo las zonas, las interfaces, las políticas por defecto y las excepciones a las políticas editando los ficheros de `zones`, `interfaces`, `policy` y `rules`, todos ellos en `/etc/shorewall/`. Utilizaré la convención de que `net` es la red pública y `loc` es la red privada o local.

```bash
gerard@gateway:~$ cat /etc/shorewall/zones
fw firewall
net ipv4
loc ipv4
gerard@gateway:~$ 
```

```bash
gerard@gateway:~$ cat /etc/shorewall/interfaces 
net enp0s3 detect dhcp,tcpflags,nosmurfs,routefilter,logmartians
loc enp0s8 detect dhcp,tcpflags,nosmurfs,routefilter,logmartians
gerard@gateway:~$ 
```

```bash
gerard@gateway:~$ cat /etc/shorewall/policy 
net all DROP info
fw all ACCEPT
loc net ACCEPT
all all REJECT info
gerard@gateway:~$ 
```

```bash
gerard@gateway:~$ cat /etc/shorewall/rules 
ACCEPT net fw tcp 22
DNS(ACCEPT) loc fw
#DNAT net loc:10.0.0.2:80 tcp 80
gerard@gateway:~$ 
```

**TRUCO**: El fichero `rules` es bastante simple, y tiene unas reglas muy dependientes de las necesidades particulares de cada *firewall*. Váis a perder mucho tiempo editando este fichero en varias ocasiones; por el momento, permito SSH y DNS desde la red privada.

Las funciones de *gateway* o NAT, pasan por permitir el *FORWARDING* de paquetes de red, y hacer el MASQUERADE pertinente de los paquetes que salgan por `enp0s3`. Esto se hace editando otros ficheros, tal como indico en [otro artículo]({filename}/articles/construyendo-firewalls-complejos-de-varias-patas-con-shorewall.md).

```bash
gerard@gateway:~$ grep FORWARDING /etc/shorewall/shorewall.conf
#IP_FORWARDING=Keep
IP_FORWARDING=Yes
gerard@gateway:~$ 
```

```bash
gerard@gateway:~$ cat /etc/shorewall/snat 
MASQUERADE 10.0.0.0/24 enp0s3
gerard@gateway:~$ 
```

Finalmente, hay que activar el servicio **shorewall** para que levante en cada reinicio; esto no lo hace por defecto porque **shorewall** viene sin configurar y representaría un problema de seguridad.

```bash
gerard@gateway:~$ sudo systemctl enable shorewall
Synchronizing state of shorewall.service with SysV service script with /lib/systemd/systemd-sysv-install.
Executing: /lib/systemd/systemd-sysv-install enable shorewall
gerard@gateway:~$ 
```

## Activando los servicios

Tras instalar y configurar los servicios, estos deben levantarse. Esto no se hace por defecto, y aunque lo hicieran, deberían reiniciarse para aplicar las nuevas configuraciones. Dependiendo de vuestro caso de uso, podéis hacerlo de dos maneras:

* Reiniciando manualmente los servicios: `sudo systemctl restart dnsmasq` y `sudo systemctl restart shorewall`
* Reiniciando directamente el servidor; personalmente prefiero esta para comprobar que todo se levanta bien de forma independiente.

Hecho esto ya tenemos el *gateway* plenamente funcional y podemos empezar a enchufar servidores en la red privada. La configuración a modificar de ahora en adelante es mínima (reglas de firewall y asignación de DHCP), así que es un buen momento para hacer un *backup*...
