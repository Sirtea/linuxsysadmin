Title: Construyendo firewalls complejos de varias patas con Shorewall
Slug: construyendo-firewalls-complejos-de-varias-patas-con-shorewall
Date: 2019-04-24 14:00
Category: Sistemas
Tags: linux, firewall, iptables, shorewall, perl



Tras ver la facilidad con la que monté un *firewall* para un servidor solitario usando **shorewall**, he estado investigando sobre como hacer *firewalls* dedicados que enruten el tráfico en mis redes. En este artículo expongo lo que llegué a conseguir, esperando que le sirva a alguien en un futuro cercano.

Ya sabemos como instalar **shorewall** y cuales son los 4 ficheros básicos de su configuración, y de lo que hay que poner en ellos. En caso de no ser así, recomiendo empezar por el artículo anterior a este sobre **shorewall**, que es [este]({filename}/articles/protegiendo-servidores-con-iptables-usando-shorewall.md).

Adicionalmente voy a especificar otros ficheros que se puedan necesitar, al tratarse de un *firewall* un poco más complejo.

## Un firewall de dos patas

El primer caso a contemplar es el más simple: un *firewall* de dos patas, por el que circula en tráfico entre dos redes. Para ello vamos a poner una máquina con dos interfaces de red, una para esconder nuestra red local y otra para conectarse a una red de confiabilidad menor.

```bash
gerard@firewall:/etc/shorewall$ ip a
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
    inet 127.0.0.1/8 scope host lo
       valid_lft forever preferred_lft forever
    inet6 ::1/128 scope host 
       valid_lft forever preferred_lft forever
2: enp0s3: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc pfifo_fast state UP group default qlen 1000
    link/ether 08:00:27:a4:3a:22 brd ff:ff:ff:ff:ff:ff
    inet 10.0.2.15/24 brd 10.0.2.255 scope global enp0s3
       valid_lft forever preferred_lft forever
    inet6 fe80::a00:27ff:fea4:3a22/64 scope link 
       valid_lft forever preferred_lft forever
3: enp0s8: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc pfifo_fast state UP group default qlen 1000
    link/ether 08:00:27:e5:f9:ed brd ff:ff:ff:ff:ff:ff
    inet 10.0.0.1/24 brd 10.0.0.255 scope global enp0s8
       valid_lft forever preferred_lft forever
    inet6 fe80::a00:27ff:fee5:f9ed/64 scope link 
       valid_lft forever preferred_lft forever
gerard@firewall:/etc/shorewall$ 
```

Vamos a definir los nombres con los que nos vamos a referir al *firewall* y a los dos segmentos de red. En este caso, `net` se refiere a la red menos confiable, `loc` a nuestra red local y `fw` al propio servidor *firewall*.

```bash
gerard@firewall:/etc/shorewall$ cat zones 
fw firewall
net ipv4
loc ipv4
gerard@firewall:/etc/shorewall$ 
```

Asociamos los nombres de las zonas con las interfaces de red adecuadas. Esto requiere un poco de conocimiento del *hardware* y de como lo hemos enchufado. En mi caso, las suelo poner en orden de confiabilidad.

```bash
gerard@firewall:/etc/shorewall$ cat interfaces 
net enp0s3 detect dhcp,tcpflags,nosmurfs,routefilter,logmartians
loc enp0s8 detect dhcp,tcpflags,nosmurfs,routefilter,logmartians
gerard@firewall:/etc/shorewall$ 
```

De forma similar, defino las políticas por defecto que se usan en todas las configuraciones. De forma casi mecánica le asigno capacidad para salir a internet a todo el mundo, descarto paquetes del exterior al *firewall* y a la red local, y rechazo todo el resto.

La política `REJECT` corta también la conectividad, pero a diferencia de `DROP`, lo hace de forma instantánea e informada, con lo que no hay *timeouts* dentro de nuestros segmentos de red. Esto también hace menos frustrante para nuestros compañeros si se equivocan de puerto o no se ha habilitado una regla adecuada todavía.

```bash
gerard@firewall:/etc/shorewall$ cat policy 
net all DROP info
fw all ACCEPT
loc fw REJECT info
loc net ACCEPT
all all REJECT info
gerard@firewall:/etc/shorewall$ 
```

Vamos a asumir que nuestro *firewall* tiene instalado **dnsmasq**, como era el caso de [este otro artículo]({filename}/articles/un-gateway-con-debian-iptables-y-dnsmasq.md). Adicionalmente, vamos a hacer `DNAT` para pasar las peticiones que hagan al *firewall* al puerto 80 a un servidor de la red local que sirva para ese fin (acordáos que es la IP pública de la red).

```bash
gerard@firewall:/etc/shorewall$ cat rules 
ACCEPT net fw tcp 22
DNS(ACCEPT) loc fw
DNAT net loc:10.0.0.2:80 tcp 80
gerard@firewall:/etc/shorewall$ 
```

**AVISO**: Los siguientes dos ficheros de configuración no eran necesarios en caso de un servidor solitario, y por lo tanto, son añadidos al artículo anterior.

Lo primero es hacer `MASQUERADE`, que es el proceso por el que los paquetes "adoptan" la dirección IP pública del *firewall* para salir a través de él. De esta forma, los paquetes sabrán volver, y el *firewall* los pasará al servidor original; sin esto, los paquetes no sabrían donde volver, ya que la red local queda oculta y normalmente tiene una dirección privada.

```bash
gerard@firewall:/etc/shorewall$ cat snat 
MASQUERADE 10.0.0.0/24 enp0s3
gerard@firewall:/etc/shorewall$ 
```

Al haber varias interfaces de red implicadas, hay que activar el `IP_FORWARDING` para permitir pasar paquetes de interfaz en interfaz. Esto se puede hacer a nivel de sistema con el fichero `/etc/sysctl.conf`, o podemos delegarlo al servicio **shorewall**, para que se active y desactive con el servicio mismo.

```bash
gerard@firewall:~$ grep IP_FORWARD /etc/shorewall/shorewall.conf 
# IP_FORWARDING=Keep
IP_FORWARDING=Yes
gerard@firewall:~$ 
```

**AVISO**: La directiva `IP_FORWARDING` solo puede aparecer una vez, y por ello hay que comentar la anterior. Si no se hace esto, el funcionamiento de la configuración es errático.

Finalmente activamos el servicio para que se levante tras cada reinicio.

```bash
gerard@firewall:~$ sudo systemctl enable shorewall
Synchronizing state of shorewall.service with SysV service script with /lib/systemd/systemd-sysv-install.
Executing: /lib/systemd/systemd-sysv-install enable shorewall
gerard@firewall:~$ 
```


Como hemos acabado, solo falta reiniciar el servidor; con reiniciar el servicio bastaría, pero me quiero asegurar de que levanta automáticamente.

```bash
gerard@firewall:~$ sudo reboot
...
```

## Un firewall de tres patas

Este es otro caso de uso habitual, en instalaciones que tienen una red DMZ y una red local. En realidad no cambia gran cosa desde el caso de las dos patas, pero servirá de ejemplo de como ir añadiendo configuraciones.

Es servidor tiene tres interfaces de red, y siguiendo mi convención van a ir en orden de confiabilidad:

* `enp0s3` &rarr; Red no confiable; vamos a llamar a su zona `net`
* `enp0s8` &rarr; Red DMZ; vamos a llamar a su zona `dmz`
* `enp0s9` &rarr; Red interna; vamos a llamar a su zona `loc`

Se pasa la configuración, para que se vean las direcciones del *firewall* en las 3 patas y los bloques de direcciones IP asignadas a cada segmento.

```bash
gerard@firewall:~$ ip a
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
    inet 127.0.0.1/8 scope host lo
       valid_lft forever preferred_lft forever
    inet6 ::1/128 scope host 
       valid_lft forever preferred_lft forever
2: enp0s3: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc pfifo_fast state UP group default qlen 1000
    link/ether 08:00:27:a4:3a:22 brd ff:ff:ff:ff:ff:ff
    inet 10.0.2.15/24 brd 10.0.2.255 scope global enp0s3
       valid_lft forever preferred_lft forever
    inet6 fe80::a00:27ff:fea4:3a22/64 scope link 
       valid_lft forever preferred_lft forever
3: enp0s8: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc pfifo_fast state UP group default qlen 1000
    link/ether 08:00:27:e5:f9:ed brd ff:ff:ff:ff:ff:ff
    inet 10.0.0.1/24 brd 10.0.0.255 scope global enp0s8
       valid_lft forever preferred_lft forever
    inet6 fe80::a00:27ff:fee5:f9ed/64 scope link 
       valid_lft forever preferred_lft forever
4: enp0s9: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc pfifo_fast state UP group default qlen 1000
    link/ether 08:00:27:ef:0a:20 brd ff:ff:ff:ff:ff:ff
    inet 10.0.1.1/24 brd 10.0.1.255 scope global enp0s9
       valid_lft forever preferred_lft forever
    inet6 fe80::a00:27ff:feef:a20/64 scope link 
       valid_lft forever preferred_lft forever
gerard@firewall:~$ 
```

Lo primero es no olvidarnos el `IP_FORWARD`; lo ponemos ahora y listo. Es una configuraciñon que posiblemente no tocaremos nunca más...

```bash
gerard@firewall:~$ grep IP_FORWARD /etc/shorewall/shorewall.conf 
# IP_FORWARDING=Keep
IP_FORWARDING=Yes
gerard@firewall:~$ 
```

Las zonas se declaran, una por línea; basta con añadir la zona correspondiente a la tercera interfaz de red.

```bash
gerard@firewall:~$ cat /etc/shorewall/zones 
fw firewall
net ipv4
loc ipv4
dmz ipv4
gerard@firewall:~$ 
```

Las interfaces también se declaran individualmente en cada línea; añadimos la nueva y listo. Hay que tener en cuenta la topología de la red; es crucial saber cuál esta enchufada en cada red.

```bash
gerard@firewall:~$ cat /etc/shorewall/interfaces 
net enp0s3 detect dhcp,tcpflags,nosmurfs,routefilter,logmartians
dmz enp0s8 detect dhcp,tcpflags,nosmurfs,routefilter,logmartians
loc enp0s9 detect dhcp,tcpflags,nosmurfs,routefilter,logmartians
gerard@firewall:~$ 
```

Las políticas se complican; cuantas más zonas tenemos, más combinaciones entre ellas salen. Por suerte disponemos del *keyword* `all` que nos simplifica mucho las políticas.

```bash
gerard@firewall:~$ cat /etc/shorewall/policy 
net all DROP info
fw all ACCEPT
all net ACCEPT
all all REJECT info
gerard@firewall:~$ 
```

Las reglas son similares al caso anterior, ya que solo hay que especificar lo que es estrictamente necesario. Es importante recalcar que se pueden indicar varias zonas, simplemente separándolas por comas.

```bash
gerard@firewall:~$ cat /etc/shorewall/rules 
ACCEPT net fw tcp 22
DNS(ACCEPT) dmz,loc fw
DNAT net dmz:10.0.0.2:80 tcp 80
gerard@firewall:~$ 
```

Como ahora hay dos redes detrás del *firewall*, tenemos que hacer el mecanismo de `MASQUERADE` para ambas, de forma que puedan salir a internet y recibir las respuestas de vuelta.

```bash
gerard@firewall:~$ cat /etc/shorewall/snat 
MASQUERADE 10.0.0.0/24 enp0s3
MASQUERADE 10.0.1.0/24 enp0s3
gerard@firewall:~$ 
```

## Uso de variables

En un sistema de 3 o más patas se hace difícil de mantener las reglas que comunican todas las redes propias, especialmente porque las máquinas pueden cambiar sus direcciones, o pueden aparecer nuevos servidores de un tipo concreto. En este caso, es interesante saber que las reglas se pueden definir usando variables, que se declararían en el fichero `params`.

Esto se observa fácilmente con un ejemplo: nuestro servidor web es en realidad un balanceador, que reparte las peticiones entre un número indeterminado de *backends*. El balanceador está en la *dmz* y los *backends* en la red local, con lo que hay que habilitar una regla para evitar la política por defecto de `REJECT`.

Definimos las variables en el fichero `/etc/shorewall/params`, que pueden ser servidores solos o listas, separadas por comas. En realidad, durante la interpretación de reglas se hace una sustitución de dichas variables por sus cadenas, así que el formato importa poco, y depende del contexto en el que se inyecte.

```bash
gerard@firewall:~$ sudo cat /etc/shorewall/params 
WEBSERVER=10.0.0.2
BACKENDS=10.0.1.2,10.0.1.3
gerard@firewall:~$ 
```

Solo faltaría añadir o modificar la regla para usar variables; de esta forma, solo habría que ir actualizando las listas en el fichero `params`.

```bash
gerard@firewall:~$ cat /etc/shorewall/rules 
ACCEPT net fw tcp 22
DNS(ACCEPT) dmz,loc fw
DNAT net dmz:$WEBSERVER:80 tcp 80
ACCEPT dmz:$WEBSERVER loc:$BACKENDS tcp 8080
gerard@firewall:~$ 
```

## Conclusión

Con **shorewall** podemos hacer *firewalls* con tantas patas como queramos, de forma fácil y rápida. Definir *ip_forwarding*, *masquerade*, zonas, interfaces y políticas es realmente simple. Añadir reglas es fácil y más aún con el uso de variables.

A partir de aquí tenemos el conocimento y las herramientas para extender el patrón de *firewall* a tantas patas como queramos, aunque personalmente no usaría nunca más de tres, por la complejidad que suponen.
