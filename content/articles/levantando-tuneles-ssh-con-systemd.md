Title: Levantando túneles SSH con systemd
Slug: levantando-tuneles-ssh-con-systemd
Date: 2016-11-14 08:00
Category: Operaciones
Tags: ssh, túnel, systemd


Ya vimos en un [artículo anterior]({filename}/articles/creando-tuneles-con-ssh.md) como levantar túneles **SSH** para llegar a través del protocolo **SSH**, a destinos que no están alcanzables normalmente. Esto está muy bien para aplicaciones puntuales, pero si tenemos que usar esos túneles una temporada, y deseamos que se mantengan levantados, ya es mas difícil.

Hay miles de gestores de procesos que pueden hacer este trabajo por nosotros, como **runit**, **monit**, **supervisor** entre otros. Personalmente no soy fan de instalar nada que proporcione una funcionalidad duplicada, así que... ¿por que no **systemd**?

Para este tutorial vamos a suponer que tenemos acceso a un servidor intermedio con **SSH**, que ve a un servidor de bases de datos, y a través del que vamos a hacer el salto. Respectivamente, los vamos a llamar *jump* y *database*, en una explosión de creatividad.

## El túnel básico

Lo primero es darnos cuenta que no llegamos a la base de datos; no importa que intentemos conectar a *localhost* o a *database* directamente. No llegamos y punto.

```bash
gerard@aldebaran:~$ mongo
MongoDB shell version: 3.2.10
connecting to: test
2016-10-17T15:39:25.766+0200 W NETWORK  [thread1] Failed to connect to 127.0.0.1:27017, reason: errno:111 Connection refused
2016-10-17T15:39:25.766+0200 E QUERY    [thread1] Error: couldn't connect to server 127.0.0.1:27017, connection attempt failed :
connect@src/mongo/shell/mongo.js:229:14
@(connect):1:6

exception: connect failed
gerard@aldebaran:~$ 
```

Vamos a levantar un túnel **SSH** que muestre en el puerto local 27017 el destino *database*, al puerto 27017, tal como lo ve el servidor de salto.

```bash
gerard@aldebaran:~$ ssh -L 27017:database:27017 jump@jump -N
Warning: Permanently added 'jump' (ECDSA) to the list of known hosts.
```

Es especialmente importante que pongamos autenticación por claves, de forma que no nos pida la contraseña para levantar el túnel. Ahora no es un gran problema, pero si pretendemos que lo haga **systemd**, no podemos instruirle a poner una contraseña dada.

Ahora podemos comprobar que si llegamos a la base de datos, en nuestro puerto local:

```bash
gerard@aldebaran:~$ mongo
MongoDB shell version: 3.2.10
connecting to: test
Server has startup warnings: 
2016-10-17T13:29:27.640+0000 I CONTROL  [initandlisten] 
2016-10-17T13:29:27.640+0000 I CONTROL  [initandlisten] ** WARNING: /sys/kernel/mm/transparent_hugepage/defrag is 'always'.
2016-10-17T13:29:27.640+0000 I CONTROL  [initandlisten] **        We suggest setting it to 'never'
2016-10-17T13:29:27.640+0000 I CONTROL  [initandlisten] 
> db.serverBuildInfo()
{
	"version" : "3.2.10",
	"gitVersion" : "79d9b3ab5ce20f51c272b4411202710a082d0317",
	"modules" : [ ],
	"allocator" : "tcmalloc",
	"javascriptEngine" : "mozjs",
	"sysInfo" : "deprecated",
	"versionArray" : [
		3,
		2,
		10,
		0
	],
	"openssl" : {
		"running" : "OpenSSL 1.0.1t  3 May 2016",
		"compiled" : "OpenSSL 1.0.1t  3 May 2016"
	},
	"buildEnvironment" : {
		"distmod" : "debian81",
		"distarch" : "x86_64",
		"cc" : "/opt/mongodbtoolchain/bin/gcc: gcc (GCC) 4.8.2",
		"ccflags" : "-fno-omit-frame-pointer -fPIC -fno-strict-aliasing -ggdb -pthread -Wall -Wsign-compare -Wno-unknown-pragmas -Winvalid-pch -Werror -O2 -Wno-unused-local-typedefs -Wno-unused-function -Wno-deprecated-declarations -Wno-unused-but-set-variable -Wno-missing-braces -fno-builtin-memcmp",
		"cxx" : "/opt/mongodbtoolchain/bin/g++: g++ (GCC) 4.8.2",
		"cxxflags" : "-Wnon-virtual-dtor -Woverloaded-virtual -Wno-maybe-uninitialized -std=c++11",
		"linkflags" : "-fPIC -pthread -Wl,-z,now -rdynamic -fuse-ld=gold -Wl,-z,noexecstack -Wl,--warn-execstack",
		"target_arch" : "x86_64",
		"target_os" : "linux"
	},
	"bits" : 64,
	"debug" : false,
	"maxBsonObjectSize" : 16777216,
	"storageEngines" : [
		"devnull",
		"ephemeralForTest",
		"mmapv1",
		"wiredTiger"
	],
	"ok" : 1
}
> 
```

## Añadiendo systemd a la ecuación

Vamos a escribir nuestro propio *service* de **systemd**. Para ello, vamos a seguir [otro artículo]({filename}/articles/escribiendo-units-en-systemd.md). Solo por la posibilidad de tener que levantar varios túneles, vale la pena usar las plantillas. Como solo podemos pasar un parámetro al *service*, vamos a crear un *script* que nos permita elegir los parámetros del túnel en función de una palabra clave.

```bash
gerard@aldebaran:~$ cat /home/gerard/bin/tunnel_to.sh 
#!/bin/bash

case "$1" in
  database) ssh -L 27017:database:27017 jump@localhost -N ;;
esac
gerard@aldebaran:~/docker/systemd-tunnel$ 
```

Y le damos permisos de ejecución.

```bash
gerard@aldebaran:~/docker/systemd-tunnel$ chmod +x /home/gerard/bin/tunnel_to.sh 
gerard@aldebaran:~/docker/systemd-tunnel$ 
```

De momento tenemos el mismo túnel, pero simplificado a un *script* con un solo parámetro:

```bash
gerard@aldebaran:~$ tunnel_to.sh database
Warning: Permanently added 'localhost' (ECDSA) to the list of known hosts.
```

Vamos a trabajar en las carpetas de sistema de **systemd**, en donde se supone que, por convención, debemos dejar nuestras *units*.

```bash
root@aldebaran:~# cd /etc/systemd/system/
root@aldebaran:/etc/systemd/system# 
```

Siguiendo el citado artículo, creamos la plantilla base que va a invocar el *script* de los túneles, con el parámetro que le demos.

```bash
root@aldebaran:/etc/systemd/system# cat tunnel\@.service 
[Unit]
Description=SSH Tunnel

[Service]
User=gerard
ExecStart=/home/gerard/bin/tunnel_to.sh %i
Restart=always

[Install]
WantedBy=multi-user.target
root@aldebaran:/etc/systemd/system# 
```

Creamos un *soft link* para cada uno de los túneles que queramos levantar:

```bash
root@aldebaran:/etc/systemd/system# ls -lh tunnel*
lrwxrwxrwx 1 root root  15 oct 17 15:43 tunnel@database.service -> tunnel@.service
-rw-r--r-- 1 root root 134 oct 17 15:43 tunnel@.service
root@aldebaran:/etc/systemd/system# 
```

De esta forma, el servicio *tunnel@database* va a levantar el *script* con el parámetro *database*, que a su vez, va a levantar el túnel como le hayamos indicado. Activamos el servicio para futuros reinicios de la máquina, y lo levantamos para esta sesión.

```bash
root@aldebaran:/etc/systemd/system# systemctl enable tunnel@database
Created symlink from /etc/systemd/system/multi-user.target.wants/tunnel@database.service to /etc/systemd/system/tunnel@.service.
root@aldebaran:/etc/systemd/system# systemctl start tunnel@database
root@aldebaran:/etc/systemd/system# 
```

Y ya podemos comprobar como el túnel está levantado, sea mediante la inspección de los procesos en *runtime* o directamente accediendo a la base de datos.

```bash
gerard@aldebaran:~$ mongo
MongoDB shell version: 3.2.10
connecting to: test
Server has startup warnings: 
2016-10-17T13:29:27.640+0000 I CONTROL  [initandlisten] 
2016-10-17T13:29:27.640+0000 I CONTROL  [initandlisten] ** WARNING: /sys/kernel/mm/transparent_hugepage/defrag is 'always'.
2016-10-17T13:29:27.640+0000 I CONTROL  [initandlisten] **        We suggest setting it to 'never'
2016-10-17T13:29:27.640+0000 I CONTROL  [initandlisten] 
> exit
bye
gerard@aldebaran:~$ ps faux | grep database | grep -v grep
gerard   22679  0.0  0.0  13228  2632 ?        Ss   15:46   0:00 /bin/bash /home/gerard/bin/tunnel_to.sh database
gerard   22680  0.0  0.0  44428  5320 ?        S    15:46   0:00  \_ ssh -L 27017:database:27017 jump@localhost -N
gerard@aldebaran:~$ 
```

Solo nos queda comprobar que si matamos el proceso, simulando que se cae solo, **systemd** se encarga de levantarlo de nuevo, en honor a la directiva *reload=always*.

```bash
gerard@aldebaran:~$ kill 22679
gerard@aldebaran:~$ ps faux | grep database | grep -v grep
gerard@aldebaran:~$ 
```

Y antes de que podamos siquiera repetir el comando *ps*, ya lo tenemos de nuevo en marcha:

```bash
gerard@aldebaran:~$ ps faux | grep database | grep -v grep
gerard   22854  0.0  0.0  13228  2632 ?        Ss   15:49   0:00 /bin/bash /home/gerard/bin/tunnel_to.sh database
gerard   22855  0.0  0.0  44428  5200 ?        S    15:49   0:00  \_ ssh -L 27017:database:27017 jump@localhost -N
gerard@aldebaran:~$ 
```

**TRUCO**: A pesar de que nuestro túnel pueda estar vivo, algunos servidores están configurados para cerrar conexiones que llevan mucho tiempo de inactividad. Podemos generar tráfico de *keepalive* para que esto no suceda, con una simple directiva **SSH** cliente. Por ejemplo, la podemos poner en la configuración local del usuario que levante los túneles.

```bash
gerard@aldebaran:~$ cat .ssh/config 
...
Host *
	ServerAliveInterval 60
...
gerard@aldebaran:~$ 
```
