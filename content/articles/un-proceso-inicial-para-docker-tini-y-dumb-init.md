Title: Un proceso inicial para docker: tini y dumb-init
Slug: un-proceso-inicial-para-docker-tini-y-dumb-init
Date: 2017-09-11 10:00
Category: Sistemas
Tags: docker, Dockerfile, tini, dumb-init



Siempre nos han vendido que **docker** ejecuta un solo proceso, y que este puede ser cualquiera. Sin embargo, este proceso se ejecuta con PID 1, que es un poco especial y que tiene unas responsabilidades adicionales. Si no queremos implementarlas, podemos usar alguna solución que ya lo haga para nosotros.

Entre estas responsabilidades, podemos citar 3 que se consideran básicas:

* Tiene que adoptar y controlar todos aquellos procesos que quedan huérfanos debido a una mala gestión de su anterior padre
* No puede dejar que ningún proceso *zombie* quede sin su correspondiente *wait*
* Debe ser capaz de progresar las señales de terminación a sus procesos hijos

Muchos de los binarios que utilizamos habitualmente no incumplen estas responsabilidades, sea por una buena gestión, o porque directamente no levantan procesos hijos.

El problema es cuando alguno de estos procesos sí que incumple. En estos casos **docker** puede enviar señales de acabado, y viendo que no todos los procesos han acabado, tiene que entrar tras 10 segundos a arreglar el desaguisado. Aunque **docker** hace un trabajo magnífico en este aspecto, el resultado es un contenedor que es caro de apagar, en cuanto a tiempo se refiere.

Y es por eso que han habido varios intentos de crear un proceso **init** que pueda levantar otro proceso único, pero cumpliendo con las responsabilidades que se le presuponen. Entre estos binarios, me gustaría mencionar dos: **tini** y **dumb-init**.

## El problema

Vamos a hacer este ejemplo con un servicio afectado por el problema, para su fácil demostración. No se trata de un servicio raro o de uso minoritario, sino que estamos hablando de **haproxy**.

Vamos a partir del más simple de los balanceadores basados en **haproxy** y **alpine linux**, con una configuración mínima (por no decir nula).

```bash
gerard@docker:~/docker/docker-init$ cat context/Dockerfile
FROM alpine:3.6
RUN apk add --no-cache haproxy
COPY haproxy.cfg /etc/haproxy/
CMD ["haproxy", "-f", "/etc/haproxy/haproxy.cfg", "-db"]
gerard@docker:~/docker/docker-init$ cat context/haproxy.cfg
global
    chroot /var/lib/haproxy
    user haproxy
    group haproxy

defaults
    mode http

listen stats
    bind *:8080
    stats enable
    stats uri /

#listen web
#    bind *:80
#    balance roundrobin
#    server web1 web1:80 check
#    server web2 web2:80 check
gerard@docker:~/docker/docker-init$
```

La vamos a construir siguiendo los comandos habituales:

```bash
gerard@docker:~/docker/docker-init$ docker build -t balancer context/
Sending build context to Docker daemon 3.072 kB
...
Successfully built 499dc4873adb
gerard@docker:~/docker/docker-init$
```

Lo que vamos a ver es que la imagen no se detiene en un tiempo adecuado. Para ellos vamos a automatizar su levantamiento y su parada con **docker-compose** y vamos a cronometrar lo segundo. Os adjunto el fichero *docker-compose.yml*, aunque es relativamente simple.

```bash
gerard@docker:~/docker/docker-init$ cat docker-compose.yml
version: '2'
services:
  balancer:
    image: balancer
    container_name: balancer
    hostname: balancer
gerard@docker:~/docker/docker-init$ docker-compose up -d
Creating network "dockerinit_default" with the default driver
Creating balancer
gerard@docker:~/docker/docker-init$
```

Y podemos ver que este contenedor tan simple no acaba decentemente, teniendo que esperar 10 segundos para que **docker** elimine el resto, cosa que es molesta y puede llevar a problemas futuros.

```bash
gerard@docker:~/docker/docker-init$ time docker-compose down
Stopping balancer ... done
Removing balancer ... done
Removing network dockerinit_default

real    0m10,486s
user    0m0,348s
sys     0m0,028s
gerard@docker:~/docker/docker-init$
```

## La solución

Ambas soluciones propuestas (**tini** y **dumb-init**) funcionan de la misma forma: ejecutan el comando que se les pasa en los argumentos. De esta forma, el comando "peligroso" se ejecuta con PID diferente de 1, siendo el PID 1 el mismo *init*. Podemos anteponer el *init* sin muchas modificaciones; basta con instalar el *init* y usar la directiva `ENTRYPOINT` para anteponer el nuevo *init*. Veamos ambos como ejemplo.

### Usando tini

Podemos instalar el paquete **tini** sin añadir una nueva línea en el *Dockerfile*, aprovechando el `apk add` del mismo **haproxy**. Prefijamos nuestro `CMD` con el binario **tini** mediante el uso de `ENTRYPOINT` y listo.

```bash
gerard@docker:~/docker/docker-init$ cat context/Dockerfile.2
FROM alpine:3.6
RUN apk add --no-cache haproxy tini
COPY haproxy.cfg /etc/haproxy/
ENTRYPOINT ["tini", "--"]
CMD ["haproxy", "-f", "/etc/haproxy/haproxy.cfg", "-db"]
gerard@docker:~/docker/docker-init$
```

Construimos la nueva imagen, y tras modificar el *docker-compose.yml*, la levantamos. Modificad el parámetro *image* en el *docker-compose.yml*, para reflejar el nuevo *tag*.

```bash
gerard@docker:~/docker/docker-init$ docker build -t balancer:v2 -f context/Dockerfile.2 context/
Sending build context to Docker daemon  5.12 kB
...
Successfully built 179697bbd3ed
gerard@docker:~/docker/docker-init$ docker-compose up -d
Creating network "dockerinit_default" with the default driver
Creating balancer
gerard@docker:~/docker/docker-init$
```

Y midiendo el tiempo de parada, vemos que el problema ha desaparecido:

```bash
gerard@docker:~/docker/docker-init$ time docker-compose down
Stopping balancer ... done
Removing balancer ... done
Removing network dockerinit_default

real    0m0,473s
user    0m0,284s
sys     0m0,020s
gerard@docker:~/docker/docker-init$
```

### Usando dumb-init

Este caso es análogo al anterior, sin más cambios que el nombre del paquete a instalar y el binario del `ENTRYPOINT`. Es importante notar que a pesar de partir del primer ejemplo, el resultado es prácticamente idéntico al segundo.

```bash
gerard@docker:~/docker/docker-init$ cat context/Dockerfile.3
FROM alpine:3.6
RUN apk add --no-cache haproxy dumb-init
COPY haproxy.cfg /etc/haproxy/
ENTRYPOINT ["dumb-init", "--"]
CMD ["haproxy", "-f", "/etc/haproxy/haproxy.cfg", "-db"]
gerard@docker:~/docker/docker-init$
```

Construimos la nueva imagen, y tras modificar el *docker-compose.yml*, la levantamos, justo como antes. Tened la precaución de usar nuevo *tag* en el *docker-compose.yml*.

```bash
gerard@docker:~/docker/docker-init$ docker build -t balancer:v3 -f context/Dockerfile.3 context/
Sending build context to Docker daemon  5.12 kB
...
Successfully built 928c992c5251
gerard@docker:~/docker/docker-init$ docker-compose up -d
Creating network "dockerinit_default" with the default driver
Creating balancer
gerard@docker:~/docker/docker-init$
```

Y midiendo el tiempo de parada, vemos que el problema también desaparece:

```bash
gerard@docker:~/docker/docker-init$ time docker-compose down
Stopping balancer ... done
Removing balancer ... done
Removing network dockerinit_default

real    0m0,520s
user    0m0,252s
sys     0m0,060s
gerard@docker:~/docker/docker-init$
```

## Conclusión

El hecho de tener procesos *zombie* es más una molestia que un problema real, al menos mientras **docker** pueda limpiar lo que quede al final. Sin embargo, las buenas maneras, y un proceso ágil de despliegue, nos sugieren encarecidamente que tratemos estos detalles de forma adecuada.

En cuanto al peso adicional en las imágenes por poner nuestros procesos *init*, podemos ver que es casi nula:

```bash
gerard@docker:~/docker/docker-init$ docker images
REPOSITORY          TAG                 IMAGE ID            CREATED              SIZE
balancer            v3                  928c992c5251        About a minute ago   5.674 MB
balancer            v2                  179697bbd3ed        5 minutes ago        5.651 MB
balancer            latest              499dc4873adb        9 minutes ago        5.631 MB
alpine              3.6                 7328f6f8b418        7 days ago           3.966 MB
gerard@docker:~/docker/docker-init$
```

Así pues, en caso de duda, ponerlo siempre nos puede ahorrar algunos dolores de cabeza, aunque por ahora los desconozcamos.
