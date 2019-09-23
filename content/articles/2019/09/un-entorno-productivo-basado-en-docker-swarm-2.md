---
title: "Un entorno productivo basado en Docker Swarm (II)"
slug: "un-entorno-productivo-basado-en-docker-swarm-2"
date: "2019-09-23"
categories: ['Sistemas']
tags: ['linux', 'entorno', 'docker', 'swarm', 'gateway', 'cluster']
series: "Un entorno productivo basado en Docker Swarm"
---

Continuamos con esta serie de artículos con la finalidad de crear un entorno
dockerizado completo. Vamos a ir creando la infraestructura necesaria para alojar
nuestro *cluster* de **docker swarm**. Esto implica crear una red privada,
un *gateway* para esconderla, y finalmente ataremos el *cluster* de **docker swarm**.<!--more-->

Como ya comenté, todo este depliegue de servidores se va a hacer mediante el
uso de virtualización en mi propia máquina, y se va a usar **VirtualBox**.
Dadas las limitaciones debido a los recursos disponibles, se va a hacer un entono
más bien pequeño, que puede ser ampliado según se necesite:

* Un *gateway* con 256mb de memoria
* Seis servidores para el **docker swarm** con 1gb de memoria
    * Tres van a actuar como *managers*
    * Tres van a actuar como *workers*

Todos ellos van a tener conexión de red a la red interna, y el *gateway* también va a
tener una conexión a la red externa, que en mi caso va a ser un NAT con reenvío de puertos.

**TRUCO**: Instalar los 7 servidores es un trabajo largo y pesado; es más inteligente
instalar uno solo con SSH y clonarlo, adaptando las peculiaridades de cada uno.

Otro detalle es la elección del segmento de red privado: **docker** utiliza las
direcciones del tipo `172.x.x.x` y la red de mi casa las del tipo `192.168.x.x`;
esto nos deja el rango `10.x.x.x` para que convivan las direcciones de la red local
con las direcciones de las redes *overlay* de **docker**. Así que tengamos claro:

* `10.0.0.x` &rarr; Red local entre los servidores virtualizados
* `10.1.x.x` &rarr; Segmento de red que servirá para las redes *overlay* del *swarm*

Hay que hacer esta distinción porque el *swarm* utiliza la red `10.x.x.x` por
defecto, y eso puede causar direcciones duplicadas entre ambas redes.

## El gateway

**AVISO**: Estas instrucciones están sacadas de [este otro artículo][1].
Por comodidad se exponen aquí también, a modo de referencia.

El *gateway* es una máquina visible desde el exterior de la red privada, y tiene por
función la de permitir el acceso al exterior a los servidores de la red privada;
adicionalmente, muchas funcionan como *firewall* e incluso ofrecen otros servicios
a los servidores de la red privada.

Esto nos obliga a darle una interfaz de red por segmento de red en el que está.
Como es el único visible desde el exterior, también conviene que dirija el tráfico
entrante al servidor que corresponda, siendo necesario que bloquee el tráfico
que no nos interesa, o que puede representar una amenaza.

```bash
gerard@gateway:~$ ip a | grep "inet "
    inet 127.0.0.1/8 scope host lo
    inet 10.0.2.15/24 brd 10.0.2.255 scope global dynamic enp0s3
    inet 10.0.0.1/24 brd 10.0.0.255 scope global enp0s8
gerard@gateway:~$ 
```

```bash
gerard@gateway:~$ cat /etc/network/interfaces
...
auto enp0s8
iface enp0s8 inet static
	address 10.0.0.1
	netmask 255.255.255.0
gerard@gateway:~$ 
```

Para permitir las comunicaciones y servir DHCP a los servidores de la red local,
vamos instalar y configurar **shorewall** y **dnsmasq**, como ya hicimos en el
[artículo de referencia][1].

```bash
gerard@gateway:~$ sudo apt install shorewall dnsmasq
...
gerard@gateway:~$ 
```

### Configuración de dnsmasq: DNS y DHCP

Configuramos el DHCP e instruimos al *gateway* a utilizarse a sí mismo como servidor DNS;
Ya de paso establecemos direcciones IP "fijas" para los nodos del *swarm*, que usarán DHCP.

```bash
gerard@gateway:~$ cat /etc/dnsmasq.d/custom 
interface=enp0s8
dhcp-range=10.0.0.200,10.0.0.250,1h
dhcp-host=docker01,10.0.0.3,1h
dhcp-host=docker02,10.0.0.4,1h
dhcp-host=docker03,10.0.0.5,1h
dhcp-host=docker04,10.0.0.6,1h
dhcp-host=docker05,10.0.0.7,1h
dhcp-host=docker06,10.0.0.8,1h
gerard@gateway:~$ 
```

```bash
gerard@gateway:~$ grep gateway /etc/hosts
10.0.0.1	gateway
gerard@gateway:~$ 
```

```bash
gerard@gateway:~$ grep prepend /etc/dhcp/dhclient.conf
prepend domain-name-servers 127.0.0.1;
gerard@gateway:~$ 
```

### Configuración de shorewall: firewall y NAT

Repitiendo el [artículo de referencia][1], nos limitamos a declarar las zonas,
interfaces, políticas y reglas específicas; no nos podemos olvidar tampoco del
*MASQUERADE* ni del *FORWARDING*.

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
gerard@gateway:~$ 
```

```bash
gerard@gateway:~$ grep FORWARDING /etc/shorewall/shorewall.conf
IP_FORWARDING=Yes
gerard@gateway:~$ 
```

```bash
gerard@gateway:~$ cat /etc/shorewall/snat 
MASQUERADE 10.0.0.0/24 enp0s3
gerard@gateway:~$ 
```

### El gateway listo

Solo necesitamos habilitar el servicio **shorewall** y reiniciamos el servidor:

```bash
gerard@gateway:~$ sudo systemctl enable shorewall
Synchronizing state of shorewall.service with SysV service script with /lib/systemd/systemd-sysv-install.
Executing: /lib/systemd/systemd-sysv-install enable shorewall
gerard@gateway:~$ 
```

```bash
gerard@gateway:~$ sudo reboot
Connection to gateway closed by remote host.
```

## El cluster de docker swarm

Para crear el *cluster* de **docker swarm** vamos a necesitar una serie de servidores
con **docker** instalado; basándonos en las decisiones del principio del artículo van
a ser 3 *managers* y, de momento, 3 *workers*. Me limitaré a instalar uno, que iré clonando.

### Los servidores

Partimos de una imagen básica con SSH, conectada a la red interna (la misma que la
segunda pata del *gateway*); con una configuración de red básica por DHCP debería funcionar,
ya que el *gateway* le suministrará una dirección IP.

Vamos a llamar a esta máquina **docker**, por poner algo; los clones van a cambiar ese nombre.
Es importante que no incluyan la relación entre el nombre del servidor y su dirección en
`/etc/hosts`; de esa resolución ya se encargará el servidor DNS del *gateway*.

A partir de aquí, solo nos queda instalar **docker**, y vamos a optar por la versión fácil:

```bash
gerard@docker:~$ wget -qO- http://get.docker.com/ | bash
...
gerard@docker:~$ sudo usermod -aG docker gerard
gerard@docker:~$ 
```

Y teniendo la imagen base, solo nos queda clonarla, creando las máquinas **docker01**,
**docker02**, **docker03**, **docker04**, **docker05** y **docker06**. Como punto a aclarar,
se recomienda levantarlas una por una; los clones declaran el mismo *hostname*, como indica
el fichero `/etc/hostname`, y por lo tanto, **dnsmasq** se hace un lío con la asignación de IPs.

Así pues la clono, la levanto, modifico el fichero `/etc/hostname` y la reinicio; repito hasta
tener las 6 máquinas que van a formar el *cluster* de **docker swarm**. La idea es que tengamos:

* **docker01**, **docker02** y **docker03** &rarr; Serán los *managers*
* **docker04**, **docker05** y **docker06** &rarr; Serán los *workers*

Si lo hemos hecho bien, tendremos las máquinas registradas en **dnsmasq** y con las direcciones
IP "fijas" que indicamos en la configuración de **dnsmasq**; algo así:

```bash
gerard@gateway:~$ cat /var/lib/misc/dnsmasq.leases | awk '{print $4": "$3}' | sort
docker01: 10.0.0.3
docker02: 10.0.0.4
docker03: 10.0.0.5
docker04: 10.0.0.6
docker05: 10.0.0.7
docker06: 10.0.0.8
gerard@gateway:~$ 
```

### Montando el cluster

Para montar el *cluster* de **docker swarm** solo necesitamos lanzar en sus servidores algún comando:

* Un `docker swarm init` en uno de los nodos, que se va a convertir en *manager*
* Un `docker swarm join` en el resto de nodos
    * Con el *token* de *manager* en los que vayan a serlo
    * Con el *token* de *worker* en el resto
    * Alternativamente podemos hacerlos todos *workers* y promocionarlos después

Así que vamos a **docker01** y lanzamos:

```bash
gerard@docker01:~$ docker swarm init --default-addr-pool 10.1.0.0/16
Swarm initialized: current node (ai1kllx5blrdxqq0r8azm8lam) is now a manager.

To add a worker to this swarm, run the following command:

    docker swarm join --token SWMTKN-1-3lbcngwk7frrtgz627p9r4xna5tbh5rre3tjlmggeb7ka5y9dk-aejxw8c8rospdwk3vpkbcwc29 10.0.0.3:2377

To add a manager to this swarm, run 'docker swarm join-token manager' and follow the instructions.

gerard@docker01:~$ 
```

**NOTA**: Acordáos de cambiar el rango de red para no colisionar con las IPs de la red privada.

Sacamos los *tokens* para unirse al *swarm*, tanto para *managers* como para *workers*:

```bash
gerard@docker01:~$ docker swarm join-token manager
To add a manager to this swarm, run the following command:

    docker swarm join --token SWMTKN-1-3lbcngwk7frrtgz627p9r4xna5tbh5rre3tjlmggeb7ka5y9dk-2ufy46xqt0w6etkh6oxksc0br 10.0.0.3:2377

gerard@docker01:~$ 
```

```bash
gerard@docker01:~$ docker swarm join-token worker
To add a worker to this swarm, run the following command:

    docker swarm join --token SWMTKN-1-3lbcngwk7frrtgz627p9r4xna5tbh5rre3tjlmggeb7ka5y9dk-aejxw8c8rospdwk3vpkbcwc29 10.0.0.3:2377

gerard@docker01:~$ 
```

Solo tenemos que ejecutar el primero en **docker02** y en **docker03** (**docker01** ya es
parte del *cluster* y un *manager*), y el segundo en **docker04**, **docker05** y **docker06**.

```bash
gerard@docker02:~$ docker swarm join --token SWMTKN-1-3lbcngwk7frrtgz627p9r4xna5tbh5rre3tjlmggeb7ka5y9dk-2ufy46xqt0w6etkh6oxksc0br 10.0.0.3:2377
This node joined a swarm as a manager.
gerard@docker02:~$ 
```

```bash
gerard@docker03:~$ docker swarm join --token SWMTKN-1-3lbcngwk7frrtgz627p9r4xna5tbh5rre3tjlmggeb7ka5y9dk-2ufy46xqt0w6etkh6oxksc0br 10.0.0.3:2377
This node joined a swarm as a manager.
gerard@docker03:~$ 
```

```bash
gerard@docker04:~$ docker swarm join --token SWMTKN-1-3lbcngwk7frrtgz627p9r4xna5tbh5rre3tjlmggeb7ka5y9dk-aejxw8c8rospdwk3vpkbcwc29 10.0.0.3:2377
This node joined a swarm as a worker.
gerard@docker04:~$ 
```

```bash
gerard@docker05:~$ docker swarm join --token SWMTKN-1-3lbcngwk7frrtgz627p9r4xna5tbh5rre3tjlmggeb7ka5y9dk-aejxw8c8rospdwk3vpkbcwc29 10.0.0.3:2377
This node joined a swarm as a worker.
gerard@docker05:~$ 
```

```bash
gerard@docker06:~$ docker swarm join --token SWMTKN-1-3lbcngwk7frrtgz627p9r4xna5tbh5rre3tjlmggeb7ka5y9dk-aejxw8c8rospdwk3vpkbcwc29 10.0.0.3:2377
This node joined a swarm as a worker.
gerard@docker06:~$ 
```

Si lo hemos hecho bien, podremos ver la lista de nodos del *swarm* desde cualquier *manager*, así como su estado:

```bash
gerard@docker01:~$ docker node ls
ID                            HOSTNAME            STATUS              AVAILABILITY        MANAGER STATUS      ENGINE VERSION
ai1kllx5blrdxqq0r8azm8lam *   docker01            Ready               Active              Leader              19.03.1
io9916f6d5u9a4lq4gufwu58i     docker02            Ready               Active              Reachable           19.03.1
i8gf5d8zmpikkwep0yu4ml105     docker03            Ready               Active              Reachable           19.03.1
6djbscl0ka50r3dx5uoynhxqf     docker04            Ready               Active                                  19.03.1
ek2thbbuapf13k5sgznpv0hhp     docker05            Ready               Active                                  19.03.1
xagr8a97pw3phevilhcnu6bdu     docker06            Ready               Active                                  19.03.1
gerard@docker01:~$ 
```

Y con esto ya tenemos la infraestructura lista.

[1]: {{< relref "/articles/2019/07/otro-gateway-con-debian-shorewall-y-dnsmasq.md" >}}
