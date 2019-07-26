---
title: "Un balanceador dinámico para Docker: traefik"
slug: "un-balanceador-dinamico-para-docker-traefik"
date: 2018-09-17
categories: ['Sistemas']
tags: ['traefik', 'docker', 'balanceador']
---

Cuando escalamos nuestros servicios o añadimos nuevos en **Docker**, suele ser un problema la configuración del balanceador. Se necesita modificar su configuración y reiniciarlo para que la nueva configuración aplique. Con el tiempo han aparecido nuevas soluciones para simplificar estos casos, con configuraciones dinámicas. Una de estas soluciones es **Traefik**.<!--more-->

**Traefik** es un proxy reverso y balanceador moderno que facilita el despliegue de microservicios. Se integra con algunos componentes de nuestra infraestructura (**Docker**, **Docker Swarm**, **Kubernetes**, **Consul**, **Amazon ECS**, ...) y se configura automáticamente leyendo sus metadatos. Suele bastar con apuntar **Traefik** al orquestador que usemos.

## Un ejemplo con Docker

**Traefik** es un binario único hecho en lenguaje **Go** y como viene siendo habitual, lo podemos instalar simplemente "tirándolo por ahí". También se nos ofrece como una imagen oficial de **Docker**. Vamos a usar esta última por simplicidad.

Lo primero que tenemos que tener en cuenta es que **Traefik** va a pasar las peticiones a otros servicios, y para ello tiene que poder alcanzarlos. En el caso de **Docker** sin cluster, los contenedores tienen conectividad si estan en la misma red. Eso se puede conseguir de dos formas:

* Ponemos todos los servicios en el mismo *docker-compose.yml* para que vayan todos a la misma red
* Definimos una red global para que varios *docker-compose.yml* se encarguen solamente de sus servicios relevantes.

**NOTA**: Optamos por la segunda para separar los servicios por proyectos; así podemos reiniciarlos fácilmente sin afectar a sus vecinos.

```bash
gerard@atlantis:~/workspace$ docker network create global
ebd9af59c9d2c8e2ce61db17885b777a343a6b354465f2a5b4cddba5bf92b9b7
gerard@atlantis:~/workspace$
```

### El balanceador

Ahora necesitamos levantar el contenedor que va a ejecutar **Traefik**, y por comodidad, lo haremos con **docker-compose**.

```bash
gerard@atlantis:~/workspace$ cat traefik/docker-compose.yml
version: '3'
services:
  traefik:
    image: traefik
    command: --api --docker --docker.exposedbydefault=false
    ports:
      - "80:80"
      - "8080:8080"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
    networks:
      - global
networks:
  global:
     external: true
gerard@atlantis:~/workspace$
```

Básicamente instruimos a **Traefik** para que use **Docker**, le mapeamos el *socket* para que pueda consultar los metadatos de los servicios. Como detalle adicional levantamos el *dashboard* con el *flag* `--api`, lo enchufamos a la red `global` que hemos creado antes y -por preferencia personal- no exponemos ningún servicio por defecto.

```bash
gerard@atlantis:~/workspace$ (cd traefik/ && docker-compose up -d)
Creating traefik_traefik_1 ... done
gerard@atlantis:~/workspace$
```

Y con esto ya podemos acceder al *dashboard* en <http://localhost:8080/>, aunque no tenemos ningún dominio registrado, con lo que obtendremos errores 404 en el puerto 80.

### Un servicio de ejemplo

Para la demostración, vamos a utilizar una imagen que vuelca el *hostname* el contenedor; eso nos sirve para verificar el balanceo. Como no quiero reinventar la rueda, y para agilizar, vamos a utilizar la imagen `emilevauge/whoami` que podemos sacar de *DockerHub*.

```bash
gerard@atlantis:~/workspace$ cat whoami/docker-compose.yml
version: '3'
services:
  whoami:
    image: emilevauge/whoami
    labels:
      - "traefik.frontend.rule=Host:whoami.docker.localhost"
      - "traefik.enable=true"
    networks:
      - global
networks:
  global:
    external: true
gerard@atlantis:~/workspace$
```

Un punto interesante de mencionar es que **Traefik** viene con una configuración estándar, pero se puede modificar algunas cosas que afectan a los contenedores mediante *labels*.

La más evidente es `traefik.enable`, que sobreescribe el comportamiente de no exponer por defecto los servicios; con ello evitamos que se expongan servicios que no deseamos hacer públicos (bases de datos, depliegues blue-green, otros servicios, ...).

Otra *label* interesante es `traefik.frontend.rule` que básicamente indica que este contenedor es uno de los miembros del *pool* de balanceo cuando se pida el *host* indicado. Una *label* que podemos necesitar es `traefik.port`, que indica contra que puerto del contenedor hay que lanzar las peticiones; por defecto se pasan al puerto 80 (que es donde escucha la imagen elegida).

**NOTA**: Para una lista completa, podemos ir a [la documentación](https://docs.traefik.io/configuration/backends/docker/#on-containers).

Levantamos el servicio con una sola instancia de momento:

```bash
gerard@atlantis:~/workspace$ (cd whoami/ && docker-compose up -d)
Creating whoami_whoami_1 ... done
gerard@atlantis:~/workspace$
```

Comprobamos que funciona como esperamos:

```bash
gerard@atlantis:~/workspace$ curl http://localhost:80/
404 page not found
gerard@atlantis:~/workspace$ curl -H "Host: whoami.docker.localhost" http://localhost:80/
Hostname: 831400b7faf2
IP: 127.0.0.1
IP: 172.25.0.3
GET / HTTP/1.1
Host: whoami.docker.localhost
User-Agent: curl/7.52.1
Accept: */*
Accept-Encoding: gzip
X-Forwarded-For: 172.25.0.1
X-Forwarded-Host: whoami.docker.localhost
X-Forwarded-Port: 80
X-Forwarded-Proto: http
X-Forwarded-Server: dd0bdbb8d6fb
X-Real-Ip: 172.25.0.1

gerard@atlantis:~/workspace$
```

Y vemos como, sin tocar el balanceador, ha aparecido un nuevo *virtualhost* que pasa las peticiones a nuestro contenedor. Ahora vamos a escalar el servicio:

```bash
gerard@atlantis:~/workspace$ (cd whoami/ && docker-compose up -d --scale whoami=4)
Starting whoami_whoami_1 ... done
Creating whoami_whoami_2 ... done
Creating whoami_whoami_3 ... done
Creating whoami_whoami_4 ... done
gerard@atlantis:~/workspace$
```

Y así sin tocar nada más, **Traefik** se ha dado cuenta del cambio en el número de contenedores y ha añadido los 3 nuevos en el *pool* de balanceo de `whoami.docker.localhost`, como indican sus *labels*:

```bash
gerard@atlantis:~/workspace$ for i in $(seq 1 8); do curl -sH "Host: whoami.docker.localhost" http://localhost:80/ | grep Hostname; done
Hostname: 831400b7faf2
Hostname: 7de8d5739178
Hostname: 01aa52cb5c66
Hostname: 4f64cac4a4d2
Hostname: 831400b7faf2
Hostname: 7de8d5739178
Hostname: 01aa52cb5c66
Hostname: 4f64cac4a4d2
gerard@atlantis:~/workspace$
```

Y estas son las *labels* de cada contenedor:

```bash
gerard@atlantis:~/workspace$ for c in whoami_whoami_{1,2,3,4}; do echo $c; docker inspect ${c} | grep traefik; done
whoami_whoami_1
                "traefik.enable": "true",
                "traefik.frontend.rule": "Host:whoami.docker.localhost"
whoami_whoami_2
                "traefik.enable": "true",
                "traefik.frontend.rule": "Host:whoami.docker.localhost"
whoami_whoami_3
                "traefik.enable": "true",
                "traefik.frontend.rule": "Host:whoami.docker.localhost"
whoami_whoami_4
                "traefik.enable": "true",
                "traefik.frontend.rule": "Host:whoami.docker.localhost"
gerard@atlantis:~/workspace$
```

**TRUCO**: No es necesario que tengáis un solo tipo de contenedores con la *label* del *host*. Se puede hacer un balanceo de contenedores distintos, con distintos puertos y funciones. Esto es útil en el caso de un cambio de versión sin corte; basta con añadir la nueva versión con otro *docker-compose.yml* y retirar el servicio viejo poco después.

## Conclusión

Con la facilidad que supone crear un *docker-compose.yml* para añadir un nuevo *virtualhost* en **Traefik**, podemos desplegar servicios y microservicios sin mucha complicación, y sin estar pendientes del balanceador. Eso reduce la necesidad de un administrador dedicado, pero hace que las cosas se puedan descontrolar fácilmente.

Cuando os déis cuenta que el servidor único con **Docker** se os queda corto, váis a necesitar un cluster más adecuado, como **Docker Swarm** o **Kubernetes**. La integración de **Traefik** con ambos es muy simple, y no váis a necesitar mucha más investigación.

Cabe mencionar que **Traefik** se integra también con varis servidores de SSL (por ejemplo **LetsEncrypt**) y nos puede gestionar fácilmente la terminación SSL y las redirecciones de un protocolo a otro. Tampoco hemos hablado del magnífico *dashboard* y de sus métricas; creo que os encantará verlo a vosotros mismos.
