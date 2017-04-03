Title: Una toolbox empaquetada en contenedores
Slug: una-toolbox-empaquetada-en-contenedores
Date: 2017-04-10 10:00
Category: Operaciones
Tags: toolbox, docker, pwgen, sysbench, apache benchmark, nmap, nikto



Muchas veces necesitamos herramientas para nuestro trabajo y no las usamos desde la misma máquina; otras veces no queremos instalar muchos paquetes en nuestra máquina. Tener una máquina virtual suele ser *overkill* para ejecutar algunos binarios. En este caso podemos tener nuestras imágenes **docker** listas para ser usadas según convenga.

En este artículo vamos a ver algunos ejemplos de imágenes de mi *toolbox* como inspiración para otras, demostrando que podemos tener nuestras herramientas con una portabilidad máxima, y sin ocupar tanto espacio como nos podríamos imaginar; y lo mejor de todo: de usar y tirar, sin ensuciar nuestras distribuciones habituales.

## Generando contraseñas

Creo que este es el peor ejemplo, ya que hay miles de webs que hacen esto mismo, pero cumple con la función didáctica. Hay un paquete en linux llamado **pwgen** que nos ofrece el binario con el mismo nombre. Solo necesitamos un contenedor que invoque esta herramienta, escriba una contraseña aleatoria y se acabe, sin dejar nada instalado.

Este paquete está disponible en **Alpine Linux**, así que es muy fácil generar el contenedor con un tamaño adecuado. solamente necesitamos instalarlo y darle el comando base.

```bash
gerard@hermes:~/docker/tools$ cat pwgen/Dockerfile 
FROM alpine:3.4
RUN apk add --no-cache pwgen
CMD ["pwgen", "-cnyB", "8", "1"]
gerard@hermes:~/docker/tools$ 
```

Lo podemos construir si no lo tuviéramos, o lo podemos descargar de un registro **docker**. Ocupa menos de 5 mb, contando el sistema operativo; nada mal.

```bash
gerard@hermes:~/docker/tools$ docker build -t pwgen pwgen/
...
gerard@hermes:~/docker/tools$ docker images
REPOSITORY                                                                            TAG                 IMAGE ID            CREATED             SIZE
pwgen                                                                                 latest              4b338afada4e        19 seconds ago      4.844 MB
gerard@hermes:~/docker/tools$ 
```

La ejecución es bastante simple también; basta con ejecutar hasta encontrar una contraseña que nos guste:

```bash
gerard@hermes:~/docker/tools$ docker run --rm pwgen
Es4toh(f
gerard@hermes:~/docker/tools$ docker run --rm pwgen
ieV7yoh}
gerard@hermes:~/docker/tools$ docker run --rm pwgen
jei!s7ph
gerard@hermes:~/docker/tools$ 
```

## Analizando el rendimiento de un servidor

Existe una aplicación llamada **sysbench** que hace una batería de pruebas para determinar el rendimiento de los parámetros básicos de una máquina. Como no podemos ir instalando este paquete, y como no tenemos la certeza que el sistema operativo del servidor soporte este binario, lo podemos poner en un contenedor y acompañarlo del sistema operativo que nos apetezca.

En este caso, el contenedor ejecuta usando los recursos de la máquina *host*, y eso es precisamente lo que **sysbench** mide. Así obtendremos diferentes resultados en cada máquina, a pesar de que la imagen es la misma.

La mala noticia es que este paquete no está disponible para **Alpine Linux**, así que usaré otra imagen, por ejemplo, **Debian Jessie**.

```bash
gerard@hermes:~/docker/tools$ cat sysbench/Dockerfile 
FROM debian:jessie
RUN apt-get update && \
    apt-get install -y sysbench && \
    rm -rf /var/lib/apt/lists/*
COPY bench.sh /
ENTRYPOINT ["/bench.sh"]
gerard@hermes:~/docker/tools$ cat sysbench/bench.sh 
#!/bin/bash

# CPU
echo "CPU: $(sysbench --test=cpu run | grep "total time:" | awk '{print $3}')"

# Memory
echo "Memory: $(sysbench --test=memory run | grep "transferred" | cut -d\( -f2 | cut -d\) -f1)"

# Disk
sysbench --test=fileio prepare > /dev/null
echo "Disk: $(sysbench --test=fileio --file-test-mode=rndrw run | grep "transferred" | cut -d\( -f2 | cut -d\) -f1)"
sysbench --test=fileio cleanup > /dev/null
gerard@hermes:~/docker/tools$ 
```

**CUIDADO**: el *script bench.sh* tiene permisos de ejecución, por lo que también lo tendrá en la imagen.

Tras construir o hacer el correspondiente *docker pull*, comprobamos que el tamaño es bastante superior, debido al sistema operativo base.

```bash
gerard@hermes:~/docker/tools$ docker build -t sysbench sysbench/
...  
gerard@hermes:~/docker/tools$ docker images
REPOSITORY                                                                            TAG                 IMAGE ID            CREATED             SIZE
sysbench                                                                              latest              ec75e66aae41        5 seconds ago       127.1 MB
gerard@hermes:~/docker/tools$ 
```

Solo queda ejecutar para ver el rendimiento de la máquina testeada, sin dejar basura en la máquina destino.

```bash
gerard@hermes:~/docker/tools$ docker run --rm sysbench
CPU: 11.1682s
Memory: 3059.66 MB/sec
Disk: 12.088Mb/sec
gerard@hermes:~/docker/tools$ 
```

## Pruebas de carga web

Hay muchas herramientas en este campo, pero a mi me sigue gustando mucho el *Apache benchmark*. El binario **ab** se suele encontrar en el paquete **apache2-utils** y este está disponible en **Alpine Linux**.

```bash
gerard@hermes:~/docker/tools$ cat ab/Dockerfile 
FROM alpine:3.4
RUN apk add --no-cache apache2-utils
ENTRYPOINT ["/usr/bin/ab"]
gerard@hermes:~/docker/tools$ 
```

Conseguimos nuestra imagen por los medios habituales; la imagen no llega a los 10 mb.

```bash
gerard@hermes:~/docker/tools$ docker build -t ab ab/
...  
gerard@hermes:~/docker/tools$ docker images
REPOSITORY                                                                            TAG                 IMAGE ID            CREATED             SIZE
ab                                                                                    latest              51b78f9dfeea        4 seconds ago       9.808 MB
gerard@hermes:~/docker/tools$ 
```

Y solo nos queda testear contra la víctima de nuestra prueba de estrés.

```bash
gerard@hermes:~/docker/tools$ docker run --rm ab -k -c5 -t5 http://www.linuxsysadmin.tk/
This is ApacheBench, Version 2.3 <$Revision: 1748469 $>
Copyright 1996 Adam Twiss, Zeus Technology Ltd, http://www.zeustech.net/
Licensed to The Apache Software Foundation, http://www.apache.org/

Benchmarking www.linuxsysadmin.tk (be patient)
Completed 5000 requests
Completed 10000 requests
Finished 10152 requests


Server Software:        GitHub.com
Server Hostname:        www.linuxsysadmin.tk
Server Port:            80

Document Path:          /
Document Length:        37545 bytes

Concurrency Level:      5
Time taken for tests:   5.001 seconds
Complete requests:      10152
Failed requests:        0
Keep-Alive requests:    10152
Total transferred:      387253740 bytes
HTML transferred:       381176513 bytes
Requests per second:    2030.04 [#/sec] (mean)
Time per request:       2.463 [ms] (mean)
Time per request:       0.493 [ms] (mean, across all concurrent requests)
Transfer rate:          75622.04 [Kbytes/sec] received

Connection Times (ms)
              min  mean[+/-sd] median   max
Connect:        0    0   0.0      0       1
Processing:     2    2   3.9      2     216
Waiting:        1    2   2.5      1     109
Total:          2    2   3.9      2     216

Percentage of the requests served within a certain time (ms)
  50%      2
  66%      2
  75%      2
  80%      2
  90%      3
  95%      3
  98%      4
  99%      4
 100%    216 (longest request)
gerard@hermes:~/docker/tools$ 
```

## Pruebas de penetración de puertos

La herramienta más versátil en este campo es **nmap**. El uso de este comando no es trivial, y un *pentester* experto puede hacer cosas realmente impresionantes. De momento nos basta con que funcione.

```bash
gerard@hermes:~/docker/tools$ cat nmap/Dockerfile 
FROM alpine:3.4
RUN apk add --no-cache nmap
ENTRYPOINT ["/usr/bin/nmap"]
gerard@hermes:~/docker/tools$ 
```

Usamos el anterior *Dockerfile* para crear la imagen (o hacemos el *docker pull* correspondiente) y vemos que la imagen se nos va a 18 mb. Nada mal.

```bash
gerard@hermes:~/docker/tools$ docker build -t nmap nmap/
...  
gerard@hermes:~/docker/tools$ docker images
REPOSITORY                                                                            TAG                 IMAGE ID            CREATED             SIZE
nmap                                                                                  latest              d808ce19de05        4 seconds ago       17.58 MB
gerard@hermes:~/docker/tools$ 
```

Solo nos faltaría probar que todo funciona, lanzando un contenedor para testear alguna IP o nombre de dominio. En este caso, con escanear los puertos web, ssh, mongodb y mysql, nos vale. El resultado es que solamente los puertos web están abiertos, con un *firewall* cortando los demás.

```bash
gerard@hermes:~/docker/tools$ docker run --rm nmap www.linuxsysadmin.tk -p80,443,22,27017,3306 -Pn

Starting Nmap 7.12 ( https://nmap.org ) at 2016-12-21 10:14 UTC
Nmap scan report for www.linuxsysadmin.tk (151.101.0.133)
Host is up (0.0011s latency).
Other addresses for www.linuxsysadmin.tk (not scanned): 151.101.192.133 151.101.128.133 151.101.64.133
PORT      STATE    SERVICE
22/tcp    filtered ssh
80/tcp    open     http
443/tcp   open     https
3306/tcp  filtered mysql
27017/tcp filtered mongod

Nmap done: 1 IP address (1 host up) scanned in 1.41 seconds
gerard@hermes:~/docker/tools$ 
```

## Pruebas de seguridad web

Una *suite* muy interesante para descubrir vulnerabilidades web es **nikto**. Se trata de un *script* de **perl** bastante completo, que va a probar las vulnerabilidades conocidas y nos va a dar los códigos en la [Open_Source_Vulnerability_Database](https://en.wikipedia.org/wiki/Open_Source_Vulnerability_Database), ahora cerrada.

Para obtener nuestra imagen, basta con instalar el paquete en una imagen **Alpine Linux**:

```bash
gerard@hermes:~/docker/tools$ cat nikto/Dockerfile 
FROM alpine:3.4
RUN apk add --no-cache nikto
ENTRYPOINT ["/usr/bin/nikto.pl"]
gerard@hermes:~/docker/tools$ 
```

Tras la construcción vemos que esta imagen es la mas grande de las anteriormente mencionadas, de entre las que hemos basado en **Alpine Linux**, ocupando mas de 60 mb; pensad en el tamaño de una máquina virtual dedicada: no bajaría de 1 gb.

```bash
gerard@hermes:~/docker/tools$ docker build -t nikto nikto/
...  
gerard@hermes:~/docker/tools$ docker images
REPOSITORY                                                                            TAG                 IMAGE ID            CREATED             SIZE
nikto                                                                                 latest              9167dce64715        3 seconds ago       61.05 MB
gerard@hermes:~/docker/tools$ 
```

El comando **nikto** tiene muchas opciones, que saltan a la vista si usáis el contenedor sin parámetros adicionales. Para verificar su funcionamiento me voy a limitar a escanear un solo *host* con la batería de pruebas estándares.

```bash
gerard@hermes:~/docker/tools$ docker run --rm nikto -host www.linuxsysadmin.tk
- ***** SSL support not available (see docs for SSL install) *****
- Nikto v2.1.5
---------------------------------------------------------------------------
+ Target IP:          151.101.192.133
+ Target Hostname:    www.linuxsysadmin.tk
+ Target Port:        80
+ Start Time:         2016-12-21 10:19:15 (GMT0)
---------------------------------------------------------------------------
+ Server: GitHub.com
+ Retrieved via header: 1.1 varnish
+ Retrieved x-served-by header: cache-cdg8733-CDG
+ The anti-clickjacking X-Frame-Options header is not present.
+ Uncommon header 'x-github-request-id' found, with contents: 689C5D15:51BA:5DE0B1A:585A54BB
+ Uncommon header 'x-served-by' found, with contents: cache-cdg8733-CDG
+ Uncommon header 'x-fastly-request-id' found, with contents: 43f82a2690743c1b1b674d92672b1e277016f83e
+ Uncommon header 'x-cache-hits' found, with contents: 3
+ Uncommon header 'access-control-allow-origin' found, with contents: *
+ Uncommon header 'x-timer' found, with contents: S1482315555.254611,VS0,VE0
+ Uncommon header 'x-cache' found, with contents: HIT
+ Server leaks inodes via ETags, header found with file /JoHeWXqS.AP, fields: 0x585799bc 0x8045 
+ No CGI Directories found (use '-C all' to force check all possible dirs)
+ Uncommon header 'content-security-policy' found, with contents: default-src 'none'; style-src 'unsafe-inline'; img-src data:; connect-src 'self'
+ Server banner has changed from 'GitHub.com' to 'Varnish' which may suggest a WAF, load balancer or proxy is in place
+ OSVDB-3092: /sitemap.xml: This gives a nice listing of the site content.
+ 6544 items checked: 0 error(s) and 13 item(s) reported on remote host
+ End Time:           2016-12-21 10:31:23 (GMT0) (728 seconds)
---------------------------------------------------------------------------
+ 1 host(s) tested
gerard@hermes:~/docker/tools$ 
```
