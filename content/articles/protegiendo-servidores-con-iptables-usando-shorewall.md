Title: Protegiendo servidores con iptables usando Shorewall
Slug: protegiendo-servidores-con-iptables-usando-shorewall
Date: 2019-04-15 10:00
Category: Sistemas
Tags: linux, firewall, iptables, shorewall, perl



Cada vez que me toca proteger un servidor con **iptables** me desanimo solo de pensarlo. No es que la herramienta sea mala (que me encanta), sino porque no es intuitiva y hay que tener en cuenta muchos casos raros. Por suerte hay utilidades que construyen el conjunto de reglas fácilmente.

Una de las herramientas que he utilizado en el pasado es [Firehol](/tag/firehol.html), pero últimamente he estado trabajando con otra muy interesante: [Shorewall](http://shorewall.org/). A pesar de necesitar tener **perl** instalado, nos simplifica mucho la vida con una configuración simple, clara y concisa.

Los más importantes de estos ficheros de configuración son solamente 4 y se encuentran en `/etc/shorewall/`:

* `zones` &rarr; Aquí se define las zonas (o segmentos de red) en los que va a participar el *firewall*
* `interfaces` &rarr; Aquí se asocian las zonas con las interfaces de red del *firewall*
* `policy` &rarr; Políticas por defecto para los paquetes que se mueven entre dos zonas
* `rules` &rarr; Reglas específicas para aquellas comunicaciones que no siguen la política por defecto

## Un caso simple

Supongamos que tenemos un servidor **Debian Stretch**, que va a servir peticiones HTTP por el puerto 80, y se administra con SSH, por el puerto 22. Vamos a llamar a este servidor **Bastion**.

El servidor **Bastion** es un servidor solitario con una sola interfaz de red, que se llama `enp0s3`.

```bash
gerard@bastion:/etc/shorewall$ ip a
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
    inet 127.0.0.1/8 scope host lo
       valid_lft forever preferred_lft forever
    inet6 ::1/128 scope host 
       valid_lft forever preferred_lft forever
2: enp0s3: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc pfifo_fast state UP group default qlen 1000
    link/ether 08:00:27:f8:e9:01 brd ff:ff:ff:ff:ff:ff
    inet 10.0.2.15/24 brd 10.0.2.255 scope global enp0s3
       valid_lft forever preferred_lft forever
    inet6 fe80::a00:27ff:fef8:e901/64 scope link 
       valid_lft forever preferred_lft forever
gerard@bastion:/etc/shorewall$ 
```

Empezaremos por proteger el resto de puertos con **iptables**, utilizando **shorewall** para simplificar. Como no lo tenemos instalado, lo instalamos:

```bash
gerard@bastion:~$ sudo apt install shorewall
[sudo] password for gerard: 
Leyendo lista de paquetes... Hecho
Creando árbol de dependencias       
Leyendo la información de estado... Hecho
Se instalarán los siguientes paquetes adicionales:
  bc libnetfilter-cthelper0 libperl5.24 perl perl-modules-5.24 rename shorewall-core
Paquetes sugeridos:
  perl-doc libterm-readline-gnu-perl | libterm-readline-perl-perl make shorewall-doc
Se instalarán los siguientes paquetes NUEVOS:
  bc libnetfilter-cthelper0 libperl5.24 perl perl-modules-5.24 rename shorewall shorewall-core
0 actualizados, 8 nuevos se instalarán, 0 para eliminar y 0 no actualizados.
Se necesita descargar 7.378 kB de archivos.
Se utilizarán 43,1 MB de espacio de disco adicional después de esta operación.
¿Desea continuar? [S/n] s
...
gerard@bastion:~$ 
```

La configuración de **shorewall** se hace modificando ficheros en la carpeta `/etc/shorewall/`, en donde vamos a trabajar de ahora en adelante.

```bash
gerard@bastion:~$ cd /etc/shorewall/
gerard@bastion:/etc/shorewall$ 
```

Como se trata de un servidor solitario, solo tiene una interfaz de red, lo que nos limita a dos "zonas", siendo el *firewall* lo que queremos proteger de la red en la que se encuentra, que llamaremos `net`.

```bash
gerard@bastion:/etc/shorewall$ cat zones 
fw firewall
net ipv4
gerard@bastion:/etc/shorewall$ 
```

Vamos a declarar la interfaz de red conectada a la zona `net`. En este caso es una relación trivial, ya que solo tenemos una interfaz de red; otros casos con más interfaces si que necesitan revisar este fichero con cuidado.

```bash
gerard@bastion:/etc/shorewall$ cat interfaces 
net enp0s3 detect dhcp,tcpflags,nosmurfs,routefilter,logmartians
gerard@bastion:/etc/shorewall$ 
```

El siguiente fichero es el de políticas, o lo que hay que hacer para el tráfico para el que no se especifique una regla más específica. Opcionalmente se puede indicar el nivel de log, que nos va a generar líneas de log en `/var/log/syslog`.

```bash
gerard@bastion:/etc/shorewall$ cat policy 
net all DROP info
fw all ACCEPT
all all REJECT info
gerard@bastion:/etc/shorewall$ 
```

En este caso se han definido 3 políticas:

* Se descartan las peticiones que vengan de la red, si no hay una regla que diga lo contrario.
* Se permite que el *firewall* establezca y mantenga tráfico a donde quiera.
* La tercera es una regla a la que -en teoría- no se llega; se pone como protección por si nos dejáramos alguna combinación.

El último paso es el de definir reglas específicas que no sigan las políticas. En nuestro servidor se permite acceder al servicio de SSH; no es lo más seguro, pero para la demostración nos vale.

```bash
gerard@bastion:/etc/shorewall$ cat rules 
ACCEPT net fw tcp 22
gerard@bastion:/etc/shorewall$ 
```

**NOTA**: Este es el fichero que más vamos a modificar, según las necesidades del servicio. El resto no se deberían modificar casi nunca, a excepción de modificaciones *hardware* o cambios de políticas.

Solamente nos falta iniciar el servicio `shorewall` para que aplique las reglas que resulten de interpretar los ficheros de configuración.

```bash
gerard@bastion:/etc/shorewall$ sudo systemctl start shorewall
gerard@bastion:/etc/shorewall$ 
```

Vamos a hacer dos pruebas simples: una conexión SSH y una petición al servicio HTTP.

La primera es muy simple; basta con iniciar una nueva sesión SSH desde la red al *firewall*. Como funciona, la damos por buena.

La segunda es lanzar una petición HTTP al puerto 80 de nuestro servidor, que va a dar un *timeout*. Esto es así porque no hemos especificado ninguna regla que lo permita, y la política por defecto de la red al *firewall* es DROP. Esto se puede ver en `/var/log/syslog`, porque esa política incluye un *loglevel* de *info*:

```bash
gerard@bastion:~$ sudo grep Shorewall /var/log/syslog | tail -1
Apr  8 10:35:29 bastion kernel: [  268.309955] Shorewall:net-fw:DROP:IN=enp0s3 OUT= MAC=08:00:27:f8:e9:01:52:54:00:12:35:02:08:00 SRC=10.0.2.2 DST=10.0.2.15 LEN=44 TOS=0x00 PREC=0x00 TTL=64 ID=7736 PROTO=TCP SPT=33066 DPT=80 WINDOW=65535 RES=0x00 SYN URGP=0 
gerard@bastion:~$ 
```

Eso se puede modificar fácilmente editando el fichero de reglas y añadiendo una que lo permita:

```bash
gerard@bastion:~$ cat /etc/shorewall/rules 
ACCEPT net fw tcp 22
ACCEPT net fw tcp 80
gerard@bastion:~$ 
```

Recargamos el servicio **shorewall** para que interprete la configuración nueva y cree las reglas necesarias para permitir o prohibir el tráfico implicado, de acuerdo con lo que hemos indicado.

```bash
gerard@bastion:~$ sudo systemctl restart shorewall
gerard@bastion:~$ 
```

Y con esto tenemos nuestro servidor con una protección de red básica, pero mejor de lo que habríamos puesto a base de comandos **iptables** manuales.
