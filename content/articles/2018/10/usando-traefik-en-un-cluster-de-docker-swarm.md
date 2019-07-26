---
title: "Usando Traefik en un cluster de Docker Swarm"
slug: "usando-traefik-en-un-cluster-de-docker-swarm"
date: 2018-10-29
categories: ['Sistemas']
tags: ['traefik', 'docker', 'swarm']
---

Hace unas semanas, hablamos de un balanceador que trabaja muy bien con **docker**. Se trataba de **traefik** y nos permitía olvidarnos de su configuración, que él mismo podía extraer de los metadatos de los contenedores y reconfigurarse dinámicamente. Hoy vamos a explicar como funciona con un *cluster* de **docker swarm**.<!--more-->

Para ello vamos a partir de un *swarm* bastante simple de dos nodos (un *manager* y un *worker*). No es el ideal, pero es lo mínimo que puedo virtualizar sin acabar con los recursos de mi máquina y sin complicar demasiado las cosas.

```bash
gerard@manager:~$ docker node ls
ID                            HOSTNAME            STATUS              AVAILABILITY        MANAGER STATUS      ENGINE VERSION
d9uluevfbh7vftbnhf2upmdnw *   manager             Ready               Active              Leader              18.06.1-ce
83tb1sa8l1z06h7vl6c4f4ucd     worker              Ready               Active                                  18.06.1-ce
gerard@manager:~$
```

Para asegurar que el balanceador está en la misma red que los contenedores (y por lo tanto, les pueda pasar peticiones), vamos a crear una red *overlay* que permita comunicarse a todos los contenedores de forma independiente del *host* en el que se encuentren.

```bash
gerard@manager:~$ docker network create --driver=overlay traefik-net
pe1s0yl4r402jagfgapmo10oc
gerard@manager:~$
```

**AVISO**: Por algún motivo, este comando creó una red que en el mismo rango que la red de los servidores del *swarm*. Esto da muchos problemas de comunicación en el futuro. Simplemente cread otra, para que la dirección de red cambie.

## El balanceador

Levantar el balanceador es tan fácil como poner un contenedor que ejecute la imagen oficial **traefik**; partimos del artículo anterior sobre [este servicio]({{< relref "/articles/2018/09/un-balanceador-dinamico-para-docker-traefik.md" >}}). El único *flag* añadido es `--docker.swarmMode`, que es el que indica que el balanceador tiene que sacar los metadatos del *cluster swarm*.

Para poder leer la información del *cluster*, es condición necesaria que se ejecute en un *manager*. Ello lo podemos conseguir mediante las *constraints* de *placement*. Otra decisión de diseño es que voy a ejecutar un **traefik** en cada *manager* con `mode: global` y con las restricciones anteriores (aunque en este caso solo hay uno).

También quiero que el puerto 8080 de cada *manager* sea ese **traefik** concreto (`mode: host`), y no el balanceador *ingress* que viene por defecto. Por supuesto, el balanceador va a estar en la red de servicio antes creada, en donde también pondremos los contenedores de servicio.

```bash
gerard@manager:~/traefik$ cat docker-compose.yml
version: '3.2'
services:
  traefik:
    image: traefik
    command: --api --docker --docker.swarmMode --docker.exposedbydefault=false
    ports:
      - target: 80
        published: 80
        protocol: tcp
        mode: host
      - target: 8080
        published: 8080
        protocol: tcp
        mode: host
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
    networks:
      - traefik-net
    deploy:
      mode: global
      placement:
        constraints:
          - node.role == manager
networks:
  traefik-net:
    external: true
gerard@manager:~/traefik$
```

Desplegamos el *stack* de un solo servicio que hemos creado y verificamos que está corriendo en todos los *managers*:

```bash
gerard@manager:~/traefik$ docker stack deploy -c docker-compose.yml traefik
Creating service traefik_traefik
gerard@manager:~/traefik$
```

```bash
gerard@manager:~/traefik$ docker stack ps traefik
ID                  NAME                                        IMAGE               NODE                DESIRED STATE       CURRENT STATE            ERROR               PORTS
k83hxjvqmp6n        traefik_traefik.d9uluevfbh7vftbnhf2upmdnw   traefik:latest      manager             Running             Running 12 minutes ago                     
gerard@manager:~/traefik$
```

Podemos ver que **traefik** responde solo en la máquina en la que está ejecutando, y no en el resto. Así nos ahorramos balancear el balanceador.

```bash
gerard@gateway:~$ curl http://manager:8080/
<a href="/dashboard/">Found</a>.
gerard@gateway:~$ curl http://worker:8080/
curl: (7) Failed to connect to worker port 8080: Conexión rehusada
gerard@gateway:~$
```

Y con esto el balanceador está listo.

## Un servicio de ejemplo

Desde el punto de vista de los servicios, no cambia nada; cada **traefik** se actualizará con lo que lea de los metadatos del *cluster*. Solo hay que recordar que debe estar en la misma red que los balanceadores...

```bash
gerard@manager:~/whoami$ cat docker-compose.yml
version: '3'
services:
  whoami:
    image: emilevauge/whoami
    networks:
      - traefik-net
    deploy:
      replicas: 4
      labels:
        traefik.frontend.rule: Host:whoami.docker.localhost
        traefik.port: 80
        traefik.enable: "true"
networks:
  traefik-net:
    external: true
gerard@manager:~/whoami$
```

Tras desplegar el servicio y ver que todas las instáncias están funcionando, podremos empezar las pruebas.

```bash
gerard@manager:~/whoami$ docker stack deploy -c docker-compose.yml whoami
Creating service whoami_whoami
gerard@manager:~/whoami$
```

```bash
gerard@manager:~/whoami$ docker stack ps whoami
ID                  NAME                  IMAGE                      NODE                DESIRED STATE       CURRENT STATE             ERROR               PORTS
hgsz3vgfyorj        whoami_whoami.1       emilevauge/whoami:latest   worker              Running             Running 30 minutes ago
ita8jth3nxvn        whoami_whoami.2       emilevauge/whoami:latest   manager             Running             Running 22 minutes ago
pib7gf0dixjl        whoami_whoami.3       emilevauge/whoami:latest   worker              Running             Running 2 minutes ago
s9c965gqq2gy        whoami_whoami.4       emilevauge/whoami:latest   manager             Running             Running 2 minutes ago
gerard@manager:~/whoami$
```

Las pruebas son tan simples como verificar que realmente se está balanceando entre todos los contenedores que, debido a la imagen usada, es trivial.

```bash
gerard@gateway:~$ curl -sH "Host: whoami.docker.localhost" http://manager/ | grep Hostname
Hostname: 8c98d5545ce6
gerard@gateway:~$ curl -sH "Host: whoami.docker.localhost" http://manager/ | grep Hostname
Hostname: a9b2b58e98bb
gerard@gateway:~$ curl -sH "Host: whoami.docker.localhost" http://manager/ | grep Hostname
Hostname: 2eb66b929b01
gerard@gateway:~$ curl -sH "Host: whoami.docker.localhost" http://manager/ | grep Hostname
Hostname: 9040b20f948e
gerard@gateway:~$ curl -sH "Host: whoami.docker.localhost" http://manager/ | grep Hostname
Hostname: 8c98d5545ce6
gerard@gateway:~$ curl -sH "Host: whoami.docker.localhost" http://manager/ | grep Hostname
Hostname: a9b2b58e98bb
gerard@gateway:~$ curl -sH "Host: whoami.docker.localhost" http://manager/ | grep Hostname
Hostname: 2eb66b929b01
gerard@gateway:~$ curl -sH "Host: whoami.docker.localhost" http://manager/ | grep Hostname
Hostname: 9040b20f948e
gerard@gateway:~$
```

Para desplegar el servicio no se necesita tocar el balanceador; aquí reside la fuerza de **traefik**. De hecho, podemos desplegar un *stack* nuevo con una segunda versión, y al rato eliminar el viejo; con eso tendríamos un despliegue sin cortes y, con un poco de juego de etiquetas, un [blue-green deployment]({{< relref "/articles/2018/05/despliegues-sin-corte-de-servicio-blue-green-deployments.md" >}}) sin complicaciones.

## Otras posibles mejoras

Esta es una lista con las ideas que todavía quedan en el tintero, y que pueden ayudarnos a crear el *cluster* perfecto, aunque no las he implementado:

* Incrementar los *managers* para tener alta disponibilidad, tanto del balanceador, como del *swarm*
* Se van a necesitar más nodos *worker* para repartir la carga de contenedores y servicios
* Se recomienda limitar el despliegue de servicios solamente en nodos *workers*
* Podemos tener un IP flotante entre los *managers* usando algo como **keepalived**
