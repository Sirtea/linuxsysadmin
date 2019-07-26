---
title: "Creando túneles con SSH"
slug: "creando-tuneles-con-ssh"
date: 2016-10-31
categories: ['Operaciones']
tags: ['ssh', 'túnel']
---

Todos conocemos las bondades de **SSH** cuando se trata de acceder a un servidor remoto con una sesión interactiva. Sin embargo, pocos conocen otra habilidad que este servicio nos ofrece: encapsular tráfico de cualquier protocolo a través de un túnel **SSH**, cifrando nuestro tráfico y pasando potencialmente por otro puerto.<!--more-->

La idea es que **SSH** encapsula el tráfico mediante el mismo protocolo **SSH**, evitando que curiosos accedan a nuestros datos, y pasando por el puerto **SSH** para llegar a puertos a los que normalmente no llegaríamos, sea porque no están visibles, o sea porque un *firewall* bloquea el resto de tráfico.

Estos túneles pueden ser de dos tipos: locales o remotos; la única diferencia es donde están los extremos, desde el punto de vista del que creó el túnel. En el caso de los túneles remotos, el puerto expuesto es local a la máquina que lanza el comando *ssh* y conecta en el otro extremo con una máquina remota. En el caso de un túnel remoto, el puerto en escucha se sitúa en la máquina remota y conecta con un puerto local.

## Un ejemplo de túnel local

Vamos a suponer que tenemos una máquina que tiene instalado un servicio que no es accesible desde la red, por ejemplo, una base de datos **mongodb**.

```bash
root@dbserver:~# netstat -lntp
Active Internet connections (only servers)
Proto Recv-Q Send-Q Local Address           Foreign Address         State       PID/Program name
tcp        0      0 127.0.0.1:27017         0.0.0.0:*               LISTEN      3194/mongod     
tcp        0      0 0.0.0.0:22              0.0.0.0:*               LISTEN      1/sshd          
tcp6       0      0 :::22                   :::*                    LISTEN      1/sshd          
root@dbserver:~# 
```

Queremos acceder desde nuestra máquina a esa base de datos, usando un cliente local. Como la máquina remota no ofrece el puerto remotamente, pero si dispone de **SSH**, vamos a crear un túnel local.

```bash
gerard@sirius:~$ ssh -L 27272:localhost:27017 user@dbserver -N
user@dbserver's password: 
```

La idea es que estamos indicando que en la máquina local va a haber un puerto 27272 que va a conectar con *localhost:27017*, **desde el punto de vista de la máquina remota**. El *flag* -L significa que el puerto es local, y el *flag* -N indica que la sesión **SSH** no va a ejecutar ningún comando, ni sesión interactiva.

Otro *flag* interesante es el -f, que crearía el túnel en *background*, sin bloquear el terminal. Eso significa que no nos pueden pedir la *password* del usuario y la autenticación tendría que ser por [claves SSH]({{< relref "/articles/2016/05/autenticacion-ssh-por-claves.md" >}}).

Solo nos falta conectar con el cliente en el puerto 27272. Esto va a causar que el tráfico se encapsule de acuerdo con el protocolo **SSH** y pase por el puerto 22. Una vez en destino, se va a deshacer el encapsulado y se va a entregar el mensaje a *localhost:27017* que, por supuesto, es el servidor de **mongodb**.

```bash
gerard@sirius:~$ mongo --port 27272
MongoDB shell version: 3.2.9
connecting to: 127.0.0.1:27272/test
Server has startup warnings: 
2016-09-02T07:22:02.640+0000 I CONTROL  [initandlisten] ** WARNING: You are running this process as the root user, which is not recommended.
2016-09-02T07:22:02.640+0000 I CONTROL  [initandlisten] 
2016-09-02T07:22:02.640+0000 I CONTROL  [initandlisten] 
2016-09-02T07:22:02.640+0000 I CONTROL  [initandlisten] ** WARNING: /sys/kernel/mm/transparent_hugepage/defrag is 'always'.
2016-09-02T07:22:02.640+0000 I CONTROL  [initandlisten] **        We suggest setting it to 'never'
2016-09-02T07:22:02.640+0000 I CONTROL  [initandlisten] 
> db
test
> show dbs
local  0.000GB
> 
```

Por defecto, en la máquina local se utiliza *localhost* para hacer el *bind* del *socket*, con lo que solamente nuestra máquina vería ese puerto abierto. Para ofrecer este puerto en todas las interfaces, basta con indicarlo:

```bash
gerard@sirius:~$ ssh -L 0.0.0.0:27272:localhost:27017 user@dbserver -N
user@dbserver's password: 
```

Otro detalle importante es que el destino *localhost:27017* es visto del punto de vista del servidor remoto. Aunque en este caso, lo hemos conectado a un puerto local del servidor remoto, nada nos impediría poner otro servidor, en vez de *localhost*, siempre y cuando el servidor remoto pudiera acceder a ese servidor y puerto.

Como punto final, indico que puse el *flag* -N porque no me interesa abrir una sesión interactiva en el servidor destino, que es el comportamiento por defecto. Sin embargo, indicando un comando distinto se podría haber conseguido ejecutar de paso otro comando en el servidor destino. Esto nos puede venir bien para ir creando túneles en la misma línea de comandos.

```bash
ssh -L 1234:localhost:1111 user1@server1 \
ssh -L 1111:localhost:2222 user2@server2 \
ssh -L 2222:localhost:3333 user3@server3 -N
```

En este caso, el puerto local 1234 conecta con *localhost(server1):1111* y en *server1* ejecuta el resto del comando. Es segundo *ssh* crearía un puerto 1111 local (en *server1*) que conecta con *localhost(server2):2222* y ejecuta el tercer *ssh* en el mismo, que crea un nuevo túnel que conecta el puerto 2222 de *server2* al 3333 en *server3*.

Entonces el usuario inicial se conecta a su local en el puerto 1234. Lo que envíe por ese *socket* va a aparecer en *server1:1111*, que lo entregará al otro túnel, y este al tercero. Esto significa que lo que hemos enviado por el *socket* va a ir a parar a *server3:3333*.

## Un ejemplo de túnel remoto

Imaginemos que tenemos un servicio en una máquina que no es visible desde internet, y que tenemos un proyecto en desarrollo que queremos hacer accesible. La idea es que vamos a crear túnel remoto, de forma que un puerto en una máquina remota conecte con un puerto en nuestra máquina local.

Para simplificar, vamos a exponer una web simple, por ejemplo, con **nginx**. Podemos fijarnos que el puerto escucha solamente en *localhost*, aunque podría ser tráfico cortado por un *firewall*.

```bash
root@webserver:~# netstat -lntp
Active Internet connections (only servers)
Proto Recv-Q Send-Q Local Address           Foreign Address         State       PID/Program name
tcp        0      0 127.0.0.1:80            0.0.0.0:*               LISTEN      3169/nginx: master 
root@webserver:~# 
```

Disponemos de un servidor accesible de forma pública por internet, que es el que va a exponer el puerto web. Creamos el túnel remoto de forma simple.

```bash
root@webserver:~# ssh -R 0.0.0.0:8888:localhost:80 user@publicserver -N
user@publicserver's password: 
```

En este caso, vamos a crear un *bind* en *publicserver*, de forma que va a escuchar en *0.0.0.0:8888* y esto va a llevar a el puerto 80 de *webserver*. Es el mismo caso que antes, pero en este caso, el origen del túnel esta en el servidor remoto, desde el punto de vista del que lanza el comando *ssh*.

Otro detalle importante es que hemos declarado que el puerto origen del túnel escuche en todas las direcciones IP, ya que queremos que cualquier persona en internet lo pueda ver.

Como detalle extra, **SSH** no permite el *bind* en *0.0.0.0* por defecto, y para que lo permita, el demonio **SSH** deber ser configurado con la directiva *GatewayPorts*, que ponemos previamente al reinicio del servicio.

```bash
root@publicserver:~# grep -i gatewayports /etc/ssh/sshd_config 
GatewayPorts yes
root@publicserver:~# 
```

Y podemos ver como el servidor *publicserver* ha expuesto correctamente el puerto en todas las interfaces.

```bash
root@publicserver:~# netstat -lntp
Active Internet connections (only servers)
Proto Recv-Q Send-Q Local Address           Foreign Address         State       PID/Program name
tcp        0      0 0.0.0.0:8888            0.0.0.0:*               LISTEN      13/sshd: root   
tcp        0      0 0.0.0.0:22              0.0.0.0:*               LISTEN      1/sshd          
tcp6       0      0 :::8888                 :::*                    LISTEN      13/sshd: root   
tcp6       0      0 :::22                   :::*                    LISTEN      1/sshd          
root@publicserver:~# 
```

Ahora ya podemos acceder a nuestra web desde cualquier punto conectado a internet, solo que lo haremos en el puerto abierto en el servidor público. El túnel se encarga de entregarlo al servidor no visible en internet.

```bash
gerard@sirius:~$ curl http://172.17.0.2:8888/
<!DOCTYPE html>
<html>
<head>
<title>Welcome to nginx on Debian!</title>
<style>
    body {
        width: 35em;
        margin: 0 auto;
        font-family: Tahoma, Verdana, Arial, sans-serif;
    }
</style>
</head>
<body>
<h1>Welcome to nginx on Debian!</h1>
<p>If you see this page, the nginx web server is successfully installed and
working on Debian. Further configuration is required.</p>

<p>For online documentation and support please refer to
<a href="http://nginx.org/">nginx.org</a></p>

<p>
      Please use the <tt>reportbug</tt> tool to report bugs in the
      nginx package with Debian. However, check <a
      href="http://bugs.debian.org/cgi-bin/pkgreport.cgi?ordering=normal;archive=0;src=nginx;repeatmerged=0">existing
      bug reports</a> before reporting a new bug.
</p>

<p><em>Thank you for using debian and nginx.</em></p>


</body>
</html>
gerard@sirius:~$ 
```
