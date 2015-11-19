Title: Ocultando puertos con port knocking
Slug: ocultando-puertos-con-port-knocking
Date: 2015-10-29 11:30
Category: Seguridad
Tags: linux, debian, jessie, firehol, port knocking, ssh, nmap



En este artículo vamos a enseñar como ocultar un puerto tras el firewall, de forma que solamente se abra tras utilizar el protocolo *port knocking*. Las tecnologías usadas van a ser *firehol* como firewall y el demonio *knockd* ocultando el *SSH*, aunque vamos a permitir acceder al puerto de HTTP.

El protocolo de *port knocking* es un sistema en el que para abrir la conectividad en un puerto se debe primero abrir una secuencia concreta a otros puertos, sean *TCP* o *UDP*.

Para conseguir este objetivo, se van a usar las siguientes tecnologías:

* **Debian jessie**: Como distribución base; podría ser cualquier otra
* **Firehol**: Scripts para levantar un firewall basado en *iptables*

El hardware va a ser uno con capacidades limitadas, virtualizado en VirtualBox.

* **CPUs**: 1
* **Memoria**: 256 Mb
* **Disco**: 2 Gb
* **Red**: 1 interfaz (*eth0*) *host-only* o *bridged* con IP fija

La instalación base es una *Debian* mínima instalada con el CD netinstall, con todo desmarcado y con el servidor de *SSH* previamente instalado.

## Instalación del servidor

Para empezar, vamos a instalar los dos servicios implicados:

```bash
root@server:~# apt-get install firehol knockd
...
root@server:~# 
```

Configuramos las reglas del firewall, de acuerdo a la documentación relacionada con *port knocking*. Se define un nivel de protección máximo, ya que se trata de la interfaz que deberá estar accesible desde internet; esto nos evita la mayoría de ataques conocidos en la capa 3 y 4.

En cuanto a las conectividad, vamos a permitir que este servidor acceda a servicios *DNS* y *HTTP*, que es lo justo para actualizarse. Como servidor vamos a permitir el acceso a *HTTP* (ya que en el ejemplo, esta máquina va a servir como servidor *HTTP*) y a *SSH* siempre y cuando se cumpla con el protocolo de seguridad.

```bash
root@server:~# cat /etc/firehol/firehol.conf 
version 5

interface any world
    protection strong
    client "dns http" accept
    server http accept
    server ssh accept with knock hidden
root@server:~# 
```

Acto seguido vamos a definir las reglas para que se abra el *knock hidden* (que corresponde con el puerto *SSH*) si se completa la secuencia de *knock*. En este caso concreto, se indica una secuencia de los puertos *TCP* 123, 456 y 789; aunque es posible definir puertos *UDP*, dejamos sin indicarlo, que nos los va a definir como *TCP*.

Como medida de seguridad vamos a indicar un tiempo máximo de 10 segundos para completar la secuencia de *knock* y un autocierre del puerto a los 5 segundos (aunque firehol va a permitir las conexiones que se hayan establecido en esos 5 segundos).

Es especialmente interesante ver que la regla incluye la dirección origen, con lo que la apertura de puerto solo será visible desde la máquina que completó la secuencia de *knock*.

```bash
root@server:~# cat /etc/knockd.conf 
[options]
    UseSyslog

[SSH]
    sequence      = 123,456,789
    seq_timeout   = 10
    start_command = iptables -A knock_hidden -s %IP% -j ACCEPT
    cmd_timeout   = 5
    stop_command  = iptables -D knock_hidden -s %IP% -j ACCEPT
root@server:~# 
```

Como medida de seguridad, *Debian* tiene una protección para levantar ambos servicios, así que tenemos que indicarle que queremos que se puedan levantar, editando otros ficheros de configuración.

```bash
root@server:~# cat /etc/default/knockd 
...
START_KNOCKD=1
...
root@server:~# cat /etc/default/firehol 
...
START_FIREHOL=YES
...
root@server:~# 
```

Finalmente podemos levantar los servicios de *port knocking* y de *firewall*, usando las herramientas estándares que nos ofrece la distribución.

```bash
root@server:~# service knockd restart
root@server:~# service firehol restart
root@server:~# 
```

## Comprobación de funcionamiento

Para comprobar el funcionamiento basta con comprobar que el puerto está normalmente cerrado. Personalmente he usado *nmap*, aunque se podría usar *netcat* o *telnet*.

```bash
gerard@workstation:~$ nmap -PN 192.168.56.3 -p 22

Starting Nmap 5.21 ( http://nmap.org ) at 2015-10-28 17:33 CET
Nmap scan report for server (192.168.56.3)
Host is up.
PORT   STATE    SERVICE
22/tcp filtered ssh

Nmap done: 1 IP address (1 host up) scanned in 2.13 seconds
gerard@workstation:~$ 
```

Vemos que sale **filtered**, que significa que el firewall lo está bloqueando. Ahora vamos a lanzar la secuencia de *knock* usando el helper **knock**, que en *Debian* se encuentra en el mismo paquete *knockd*. Acto seguido, el puerto de *SSH* queda abierto (en otras palabras: escuchando). Ahora sería posible iniciar sesión por *SSH* en la máquina.

```bash
gerard@workstation:~$ knock 192.168.56.3 123 456 789
gerard@workstation:~$ nmap -PN 192.168.56.3 -p 22

Starting Nmap 5.21 ( http://nmap.org ) at 2015-10-28 17:34 CET
Nmap scan report for server (192.168.56.3)
Host is up (0.0011s latency).
PORT   STATE SERVICE
22/tcp open  ssh

Nmap done: 1 IP address (1 host up) scanned in 0.07 seconds
gerard@workstation:~$ 
```

Finalmente comprobamos que, transcurridos los 5 segundos configurados, el puerto vuelve a verse como **filtrado**, con lo que no se puede establecer nuevas conexiones en este puerto.

```bash
gerard@workstation:~$ nmap -PN 192.168.56.3 -p 22

Starting Nmap 5.21 ( http://nmap.org ) at 2015-10-28 17:34 CET
Nmap scan report for server (192.168.56.3)
Host is up.
PORT   STATE    SERVICE
22/tcp filtered ssh

Nmap done: 1 IP address (1 host up) scanned in 2.08 seconds
gerard@workstation:~$ 
```

Y con esto queda protegido el acceso por *SSH* a la máquina.
