---
title: "Un entorno de jenkins distribuido en contenedores"
slug: "un-entorno-de-jenkins-distribuido-en-contenedores"
date: 2018-11-12
categories: ['Operaciones']
tags: ['jenkins', 'docker', 'master', 'slave']
---

Estaba yo el otro día intentando montar un **jenkins** con acceso al binario de **docker** y **python**. Como no quería instalar **jenkins**, me limité a extender la imagen [jenkins/jenkins](https://hub.docker.com/r/jenkins/jenkins/) para dotarlo de las herramientas necesarias, como [ya hicimos con ansible]({{< relref "/articles/2016/09/lanzando-playbooks-de-ansible-desde-jenkins.md" >}}) que, aunque funciona, no es ni elegante ni escalable.<!--more-->

El resultado es una imagen que hace demasiadas cosas, no es modular y un cambio requiere la recreación de la herramienta completa. Así que se me ocurrió otra forma de hacer las cosas, teniendo en cuenta que la herramienta funciona en modo *master/slave*. Básicamente se trata de dejar al **jenkins** como *master* y delegar los *jobs* a otros contenedores con las herramientas necesarias.

Para estos *workers* solo necesitamos un contenedor con **SSH** y **Java**. El resto de herramientas serían las necesarias para lanzar los comandos que conforman nuestro *job*. Veamos un ejemplo.

## El master: Jenkins

Lo primero que necesitamos es que el **jenkins** y sus *slaves* estén en la misma red; el *master* va a empujar los comandos a los *slaves* mediante **SSH**. Crearemos una red tipo "bridge" de usuario, que nos garantiza que los contenedores resuelvan DNS por su nombre.

Normalmente dejaría que lo hiciera **docker-compose**, pero pretendo separar el entorno en varios *docker-compose.yml* para poder actualizar los *workers* según su tipo. En caso de utilizar **docker swarm**, podríamos usar una red *overlay* para que sea irrelevante en las comunicaciones el nodo de *swarm* en el que estén desplegados.

```bash
gerard@atlantis:~$ docker network create jenkins
898c8a3b77761ac4a886d0a7a2546bfc475fc3ae1280cf1ddc37a55b2057c084
gerard@atlantis:~$
```

Sobre esta red solamente necesitamos levantar el **jenkins** usando la imagen `jenkins/jenkins`, en la versión y sistema operativo deseado. Solamente vamos a usar un volúmen para mantener las configuraciones de forma persistente, y vamos a publicar el puerto de **jenkins** para su uso por parte de otras máquinas de nuestra red.

```bash
gerard@atlantis:~/workspace/jenkins$ cat docker-compose.yml
version: '3'
services:
  jenkins:
    image: jenkins/jenkins:alpine
    container_name: jenkins
    hostname: jenkins
    volumes:
      - jenkins_home:/var/jenkins_home
    networks:
      jenkins: {}
    ports:
      - "8080:8080"
volumes:
  jenkins_home:
networks:
  jenkins:
    external: true
gerard@atlantis:~/workspace/jenkins$
```

Levantamos el **jenkins** con `docker-compose up -d` y nos vamos a su panel de trabajo en `http://atlantis:8080/`. La primera vez nos va a hacer varias preguntas para crear el usuario de administración y demás; esto es un **jenkins** normal.

## Unos slaves de ejemplo

Los *slaves* son solamente máquinas con **SSH** y **Java** instalados; por supuesto, para entrar por **SSH**, **jenkins** va a necesitar un usuario y una contraseña Para no levantar más máquinas virtuales, vamos a crear estos *slaves* como contenedores **docker**, con un usuario y *password* configurables (por si hubiera que cambiarlos en un futuro).

```bash
gerard@atlantis:~/workspace/base_worker$ cat Dockerfile
FROM alpine:3.8
RUN apk add --no-cache openssh openjdk8-jre
COPY start.sh /
CMD ["/start.sh"]
gerard@atlantis:~/workspace/base_worker$
```

```bash
gerard@atlantis:~/workspace/base_worker$ cat start.sh
#!/bin/sh

for key in rsa ecdsa ed25519; do
    test -e /etc/ssh/ssh_host_${key}_key || ssh-keygen -t ${key} -N "" -f /etc/ssh/ssh_host_${key}_key -q
done

if [ -n "${SSH_USER}" ]; then
    adduser -D ${SSH_USER}
    echo "${SSH_USER}:${SSH_PASSWORD}" | chpasswd
fi

exec /usr/sbin/sshd -D -e
gerard@atlantis:~/workspace/base_worker$
```

Construimos la imagen y le damos el *tag* `worker:base`. Lo vamos a utilizar tal cual, pero una estrategia interesante sería extender esta imagen para añadir lo que se pueda necesitar. Eso daría pie a varios contenedores con diferentes herramientas de compilación; cada *job* de **jenkins** se configurará para usar las que puedan satisfacer sus comandos de construcción.

Levantar dos instancias de estos *workers* no entraña ninguna dificultad; lo importante es el `container_name`, que es el nombre de DNS de la máquina dentro de la red `jenkins`.

```bash
gerard@atlantis:~/workspace/workers$ cat docker-compose.yml
version: '3'
services:
  worker01:
    image: worker:base
    build: ../base_worker
    container_name: worker01
    hostname: worker01
    environment:
      SSH_USER: jenkins
      SSH_PASSWORD: s3cr3t
    networks:
      jenkins: {}
  worker02:
    image: worker:base
    build: ../base_worker
    container_name: worker02
    hostname: worker02
    environment:
      SSH_USER: jenkins
      SSH_PASSWORD: s3cr3t
    networks:
      jenkins: {}
networks:
  jenkins:
    external: true
gerard@atlantis:~/workspace/workers$
```

De nuevo, levantamos ls *workers* con `docker-compose up -d` y ya los tenemos listos para ser usados.

## Configurando Jenkins con los nuevos slaves

Para que **jenkins** pueda controlar *slaves* por **SSH**, se necesita instalar el **SSH Slaves plugin**:

> Administrar Jenkins > Administrar Plugins > Todos los plugins

Reiniciamos el **jenkins** y ya tenemos todo lo necesario para seguir.

Ahora se necesita configurar los nuevos nodos para que **jenkins** los pueda monitorizar y controlar:

> Administrar Jenkins > Administrar Nodos > Nuevo nodo

Aquí solo hay que dar un nombre para identificarlo, el tipo "Permanent Agent" y el botón "OK". En la siguiente pantalla hay que rellenar la carpeta de trabajo, el nombre del equipo y las credenciales SSH. Tras guardar, solo queda esperar que el agente esté *online* en la siguiente pantalla.

**TRUCO**: Cuidado con la "Host Key Verification Strategy", que suele dar problemas de acceso por SSH. Yo suelo poner "Non verifying Verification Strategy".

Al configurar cada proyecto, podremos elegir ejecutar en nodos concretos, con la opción "Restringir dónde se puede ejecutar este proyecto.". Esto nos permite elegir los nodos que puedan cumplir con nuestro *build*; por ejemplo elegir un nodo con **docker** para hacer un `docker build` y un `docker push`.

Con la imagen de *slave* que hemos utilizado tenemos **Java JRE** y los binarios propios de un **Alpine Linux** básico, así que no esperéis mucho más...
