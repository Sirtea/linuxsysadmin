---
title: "Una breve introducción a Firewalld"
slug: "una-breve-introduccion-a-firewalld"
date: "2023-03-31"
categories: ['Sistemas']
tags: ['linux', 'firewall', 'iptables', 'firewalld']
---

Como ya sabéis, este blog ha ido cambiando las tecnologías tal como han ido saliendo nuevas o
más adecuadas. La siguiente que me veo obligado a apartar es **Shorewall**, debido a que su
desarrollador se ha retirado y no lo va a seguir adaptando a las situaciones siempre cambiantes.
<!--more-->

Hace relativamente poco, me enteré por [dos][1] [artículos][2] que su creador, **Tom Eastep**,
se retiraba para disfrutar de su jubilación. Aunque sigo creyendo que es la mejor capa de
abstracción sobre **iptables**, se va a quedar atrás rápidamente.

> Shorewall Community ...
> 
> I am now in my mid 70s and have spent almost 50 years in tech-related
> industries. More than three years ago, I retired from my position at
> Hewlett Packard Enterprise, and while I have continued to develop and
> support Shorewall, I feel that it is now time to say goodbye.
> 
> Shorewall 5.2.3 will be my last Shorewall release. If you find problems
> with that release, I will attempt to resolve them. But, I am now
> departing on an extended trip to visit some of the places in the world
> that I have always dreamed of seeing.
> 
> If I have left you with unresolved problems, I am sorry. If you would
> like to see Shorewall continue and are willing to help with development
> and support, please let me know. I am more than willing to help ensure
> that Shorewall continues.
> 
> Most of all, I want to thank all of you who have used Shorewall and who
> have helped make it better over the years. You are the ones that I will
> miss the most.
> 
> -Tom

Esto me obligó a buscar otra solución, y esta llegó en forma de **Firewalld**. Aunque no he
conseguido crear *firewalls* de 3 o más patas con **Firewalld**, ha llegado el momento de
escribir una ligera introducción que pueda servirle a alguien en el futuro.

## Conceptos básicos

Empecemos por lo básico: **firewalld** utiliza el concepto de **zonas**. Aviso para el que
venga de **Shorewall**, estas no tienen nada que ver entre sí. Las zonas de **Firewalld** son
solamente pegamento que permite agrupar un conjunto de reglas y políticas, el origen de los
paquetes afectados y otras reglas aplicables.

Empezaremos por instalar el paquete **firewalld** si no lo tuviéramos ya:

```bash
gerard@bastion:~$ sudo apt install firewalld
...
gerard@bastion:~$
```

Aunque podemos crear zonas nuevas, vamos a aprovechar que **Firewalld** viene con algunas
zonas prefabricadas para ver un ejemplo:

```bash
gerard@bastion:~$ sudo firewall-cmd --get-zones
block dmz drop external home internal public trusted work
gerard@bastion:~$

gerard@bastion:~$ sudo firewall-cmd --zone=public --list-all
public
  target: default
  icmp-block-inversion: no
  interfaces:
  sources:
  services: dhcpv6-client ssh
  ports:
  protocols:
  forward: no
  masquerade: no
  forward-ports:
  source-ports:
  icmp-blocks:
  rich rules:
gerard@bastion:~$
```

En este caso se trata de una zona llamada "public" (el nombre no es importante), que no afecta
a nada (directivas `interfaces` y `sources`) y que permitiría acceder a ella a los servicios
**dhcpv6-client** y **ssh**, sin otros protocolos o puertos (directivas `services`, `protocols`
y `ports`).

Un punto interesante es que los comandos de **firewall-cmd** nos permiten modificar el *firewall*
en caliente o de forma permanente, nunca ambos estados a la vez. Esto nos obliga a repetir los
comandos con y sin el *flag* `--permanent`. Alternativamente, podemos salvar el *runtime* con el
comando `firewall-cmd --runtime-to-permanent` o aplicar lo salvado con `firewall-cmd --reload`.

**NOTA**: No pretendo abarcar todo lo que puede hacer **Firewalld**, solo lo básico. Si queréis
seguir tirando del hilo, el proyecto dispone de [una amplia documentación][3].

## Un firewall simple

Supongamos que tenemos un servidor que ofrece HTTP y HTTPS en los puertos estándar, así como
un servicio SSH en el puerto TCP 2222. La idea es que vamos a hacer un DROP de todo lo demás.

El primer paso consiste en crear o adaptar una zona para cubrir este caso; por no ir creando
zonas, voy a adaptar la zona "public". Como hemos visto un poco más arriba, viene con algunos
servicios aceptados, que no queremos, así que los quitamos:

```bash
gerard@bastion:~$ sudo firewall-cmd --zone=public --remove-service=dhcpv6-client --remove-service=ssh --permanent
success
gerard@bastion:~$
```

Podemos añadir lo que nos interesa, que es la política DROP, los servicios HTTP y HTTPS y un
puerto TCP "no común". Podríamos haber permitido los tres puertos sin usar servicios, pero así
queda más bonito.

```bash
gerard@bastion:~$ sudo firewall-cmd --zone=public --set-target DROP --permanent
success
gerard@bastion:~$

gerard@bastion:~$ sudo firewall-cmd --zone=public --add-service=http --permanent
success
gerard@bastion:~$

gerard@bastion:~$ sudo firewall-cmd --zone=public --add-service=https --permanent
success
gerard@bastion:~$

gerard@bastion:~$ sudo firewall-cmd --zone=public --add-port=2222/tcp --permanent
success
gerard@bastion:~$
```

Ahora que tenemos el conjunto de reglas y políticas listas, solo nos falta indicar qué
paquetes de red deben usar esta zona. En mi caso, vamos a utilizar esta zona para todo
lo que entre por la única interfaz de red que tengo. Es importante saber que la interfaz
de *localhost* no quedará nunca afectada, hagamos lo que hagamos.

```bash
gerard@bastion:~$ sudo firewall-cmd --zone=public --add-interface=enp0s3 --permanent
success
gerard@bastion:~$
```

Ahora, todos estos cambios están guardados en ficheros de configuración; esto significa
que van a aplicar en el siguiente reinicio. Como no tengo paciencia para ello, voy a
recargar la configuración a mano:

```bash
gerard@bastion:~$ sudo firewall-cmd --reload
success
gerard@bastion:~$
```

Solo nos queda ver que la zona queda como **activa** (es decir, que se aplica a *algo*),
y ver que las reglas son las que queríamos:

```bash
gerard@bastion:~$ sudo firewall-cmd --get-active-zones
public
  interfaces: enp0s3
gerard@bastion:~$

gerard@bastion:~$ sudo firewall-cmd --zone=public --list-all
public (active)
  target: DROP
  icmp-block-inversion: no
  interfaces: enp0s3
  sources:
  services: http https
  ports: 2222/tcp
  protocols:
  forward: no
  masquerade: no
  forward-ports:
  source-ports:
  icmp-blocks:
  rich rules:
gerard@bastion:~$
```

## Un firewall de dos patas

Este otro ejemplo se basa en una máquina tipo *firewall* de dos patas que conecta una red
externa con una interna. La interfaz de red externa es **enp0s3** y la interfaz conectada
a la red interna es la **enp0s8**.

La idea es la misma, se trata de dos patas de red que estarán afectadas por una zona cada
una. Podría usar la misma zona para ambas, pero prefiero utilizar reglas diferentes en cada
pata de red.

Mirando las zonas prefabricadas, veo que hay dos que tienen un nombre muy descriptivo para
las redes que estoy separando: **internal** y **external**. Así pues, voy a reutilizarlas.

```bash
gerard@firewall:~$ sudo firewall-cmd --get-zones
block dmz drop external home internal public trusted work
gerard@firewall:~$
```

Empezaremos por la fácil: la pata interna. La revisamos y vemos su configuración por defecto:

```bash
gerard@firewall:~$ sudo firewall-cmd --zone=internal --list-all
internal
  target: default
  icmp-block-inversion: no
  interfaces:
  sources:
  services: dhcpv6-client mdns samba-client ssh
  ports:
  protocols:
  forward: no
  masquerade: no
  forward-ports:
  source-ports:
  icmp-blocks:
  rich rules:
gerard@firewall:~$
```

De todos estos servicios, no nos interesa conservar ninguno; no queremos que los servidores de
la red interna puedan acceder a ninguno de ellos. En cambio, vamos a suponer que este *firewall*
tiene instalado el paquete **dnsmasq** y ofrece DHCP y DNS a las máquinas de la red interna,
por lo que hay que permitirlos. La política que viene por defecto es `default`, que resulta
en un conveniente REJECT.

```bash
gerard@firewall:~$ sudo firewall-cmd --zone=internal --remove-service=dhcpv6-client --remove-service=mdns --remove-service=samba-client --remove-service=ssh --permanent
success
gerard@firewall:~$

gerard@firewall:~$ sudo firewall-cmd --zone=internal --add-service=dhcp --add-service=dns --permanent
success
gerard@firewall:~$
```

Solo nos falta asignar la zona a la pata de la red interna y cargar esa configuración guardada
en los ficheros de configuración:

```bash
gerard@firewall:~$ sudo firewall-cmd --zone=internal --add-interface=enp0s8 --permanent
success
gerard@firewall:~$

gerard@firewall:~$ sudo firewall-cmd --reload
success
gerard@firewall:~$
```

Ahora le toca el turno a la pata de la red externa. Miramos lo que lleva por defecto:

```bash
gerard@firewall:~$ sudo firewall-cmd --zone=external --list-all
external
  target: default
  icmp-block-inversion: no
  interfaces:
  sources:
  services: ssh
  ports:
  protocols:
  forward: no
  masquerade: yes
  forward-ports:
  source-ports:
  icmp-blocks:
  rich rules:
gerard@firewall:~$
```

El SSH ya nos viene bien, pero hay que cambiar la política por un DROP. Adicionalmente,
vamos a poner una regla de *port forward*, de forma que todo lo que entre por los puertos
TCP 80 y 443 (HTTP y HTTPS) se los vamos a tirar al servidor web (10.0.0.2), mismos
puertos (directivas `toaddr` y `toport`).

```bash
gerard@firewall:~$ sudo firewall-cmd --zone=external --set-target=DROP --permanent
success
gerard@firewall:~$

gerard@firewall:~$ sudo firewall-cmd --zone=external --add-forward-port=port=80:proto=tcp:toaddr=10.0.0.2:toport=80 --permanent
success
gerard@firewall:~$

gerard@firewall:~$ sudo firewall-cmd --zone=external --add-forward-port=port=443:proto=tcp:toaddr=10.0.0.2:toport=443 --permanent
success
gerard@firewall:~$
```

Asignamos la pata de red externa y recargamos las reglas, desde el "permanent" hasta el "runtime":

```bash
gerard@firewall:~$ sudo firewall-cmd --zone=external --add-interface=enp0s3 --permanent
success
gerard@firewall:~$

gerard@firewall:~$ sudo firewall-cmd --reload
success
gerard@firewall:~$
```

El último paso para permitir que los paquetes salgan por la pata externa y sepan volver al
*firewall* es hacer SNAT o MASQUERADE. Eso se consigue con el comando `firewall-cmd --add-masquerade`;
sin embargo, la zona "external" ya lo llevaba activado (directiva `masquerade: yes` cuando hemos
revisado la configuración inicial).

**TRUCO**: Para que los paquetes pasen de una red a otra, hay que cambiar el fichero
`/proc/sys/net/ipv4/ip_forward` a "1". Si ponemos el *masquerade* o una regla de *port forward*,
**Firewalld** ya lo hace por nosotros...

```bash
gerard@firewall:~$ cat /proc/sys/net/ipv4/ip_forward
1
gerard@firewall:~$
```

## Sobre la configuración permanente y los backups

Cuando instalamos el paquete **firewalld**, viene con varios objetos prefabricados. Estos se
encuentran en `/usr/lib/firewalld/`. En caso de crear objetos nuevos (o modificar los existentes),
la política de la herramienta es la de utilizar otro sitio en donde guardar las modificaciones.

Este otro sitio es `/etc/firewalld/` y es donde deberíamos hacer copias de seguridad, para cubrir
nuestra política de *backups* en caso de desastre.

```bash
gerard@firewall:~$ sudo tree /etc/firewalld/
/etc/firewalld/
├── firewalld.conf
├── helpers
├── icmptypes
├── ipsets
├── lockdown-whitelist.xml
├── policies
├── services
└── zones
    ├── external.xml
    ├── external.xml.old
    ├── internal.xml
    └── internal.xml.old

6 directories, 6 files
gerard@firewall:~$
```



[1]: https://news.ycombinator.com/item?id=19219212
[2]: https://sourceforge.net/p/shorewall/mailman/message/36589783/
[3]: https://firewalld.org/documentation/
