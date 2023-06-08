---
title: "Un Jenkins distribuido en Docker con agentes JNLP"
slug: "un-jenkins-distribuido-en-docker-con-agentes-jnlp"
date: "2023-06-08"
categories: ['Sistemas']
tags: ['jenkins', 'docker', 'swarm']
---

Ya sabéis que me encantan los sistemas reconstruibles y, en ese aspecto, nada supera a **Docker**.
Sin embargo, la imagen oficial de **Jenkins** para **Docker** normalmente no contiene las herramientas
que nos interesan. Por eso podemos descargar los trabajos a  agentes más adecuados, posiblemente
desplegados también en contenedores **Docker**.<!--more-->

Partiremos de un *clúster* de **Docker Swarm**, aunque este hecho es irrelevante; podría ser un
*clúster* de **Kubernetes**, un solo servidor, o cualquier otra arquitectura que tengamos. En este
caso concreto, utilizaremos un *clúster* de un solo nodo que ejecuta **Debian Bullseye** y dispone
de 1gb de memoria (con 512mb no conseguí levantar el servicio **Jenkins** y un solo agente).

## El servidor de Jenkins

Empezamos con el servicio **Jenkins**, con un *stack* bastante normal. Solo tendremos la precaución
de guardar la carpeta de estado de **Jenkins** en un volumen y expondremos el puerto para poder
entrar cómodamente a la interfaz web.

```bash
gerard@sandbox:~/jenkins$ cat stack.yml
version: '3'
services:
  jenkins:
    image: jenkins/jenkins
    volumes:
      - data:/var/jenkins_home
    ports:
      - "8080:8080"
volumes:
  data:
gerard@sandbox:~/jenkins$
```

```bash
gerard@sandbox:~/jenkins$ cat deploy.sh
#!/bin/bash

docker stack deploy -c stack.yml jenkins
gerard@sandbox:~/jenkins$
```

Desplegamos el *stack* usando los comandos y métodos habituales:

```bash
gerard@sandbox:~/jenkins$ ./deploy.sh
Creating network jenkins_default
Creating service jenkins_jenkins
gerard@sandbox:~/jenkins$
```

Solo nos queda seguir el proceso de *setup* que nos ofrece la interfaz web. Seguimos los pasos que nos
indica, sacando el valor secreto del contenedor (en `/var/jenkins_home/secrets/initialAdminPassword`) o
de los logs del servicio `jenkins_jenkins`. Solamente necesitamos instalar un único *plugin* que es el
"Instance Identity", aunque no sale en la lista de *plugins* durante el *setup* y tenemos que instalarlo
*a posteriori*; podemos encontrarlo siguiendo los menús: `Panel de Control > Administrar Jenkins > Plugins (Available plugins)`.

Con esto tenemos el servidor levantado y listo para utilizar, aunque no tenemos agentes con tecnologías
concretas, que es el punto de este artículo. Seguiremos por este camino, de ahora en adelante.

## Un agente de Docker

Ahora necesitamos añadir agentes que nos ofrezcan los comandos necesarios para ejecutar nuestros *jobs*.
Como ya sabéis que me gusta **Docker**, voy a añadir su agente para obtener acceso a los comandos propios
del cliente `docker`.

Añadiremos un nuevo nodo en la interfaz web, en `Panel de Control > Administrar Jenkins > Nodos`. Crearemos
un "New node" y del tipo "Permanent Agent". El único campo requerido es el "Directorio raíz remoto", que
hay que poner a `/home/jenkins/agent`. También me gusta limitar las tareas que se ejecutan en él, de forma
que solo se ejecuten los que así lo configuren; esto se hace indicando el campo "Usar", y poner en
"Dejar este nodo para ejecutar solamente tareas vinculadas a él". Ahora ya podemos "Guardar".

Si volvemos a abrir el nodo, veremos que nos indica diferentes formas de levantar el agente. De esta página
necesitamos anotar dos cosas: el nombre del agente y el *secret* del mismo. El resto lo levantaremos añadiendo
el agente en nuestro *stack* en el *swarm*.

Nos vamos a nuestro nodo *manager* del *swarm*, en donde añadiremos un nuevo servicio a nuestro *stack*,
que en este caso será el de **Docker**.

```bash
gerard@sandbox:~/jenkins$ cat stack.yml
version: '3'
services:
  jenkins:
    image: jenkins/jenkins
    volumes:
      - data:/var/jenkins_home
    ports:
      - "8080:8080"
  agent-docker:
    image: jenkins/jnlp-agent-docker
    user: 1000:998
    environment:
      JENKINS_URL: http://jenkins:8080/
      JENKINS_AGENT_NAME: docker
      JENKINS_SECRET: 456326a4974441a24fe21be2495ef1177d1b660c8177376e5765b2cd9b1cb975
    volumes:
      - "/var/run/docker.sock:/var/run/docker.sock"
volumes:
  data:
gerard@sandbox:~/jenkins$
```

Hay varios puntos importantes, y algunos específicos, de este agente concreto:

* La imagen es la que nos convenga, utilizando el protocolo JNLP.
* Las variables de entorno `JENKINS_URL`, `JENKINS_AGENT_NAME` y `JENKINS_SECRET` (los dos últimos anotados de la interfaz web).
* Otros específicos del agente JNLP de **Docker**
	* El volumen que inserta el *socket* del servidor **Docker** del *host* (tiene que ser de un nodo *manager*).
	* Un usuario y grupo de ejecución que nos permita escribir el *socket* anterior:
		* Dejamos "1000" que es el usuario **jenkins** original del contenedor.
		* Ponemos "998" de grupo, que se corresponde con el grupo **docker** en el *host*, con permisos de escritura.

Desplegamos el *stack* de nuevo, para que se cree el servicio del agente nuevo, y observamos
en la interfaz web que el nodo pasa a estar disponible.

```bash
gerard@sandbox:~/jenkins$ ./deploy.sh
Creating service jenkins_agent-docker
Updating service jenkins_jenkins (id: uaee5mcowov3vl2jlx99yk051)
gerard@sandbox:~/jenkins$
```

**TRUCO**: Ya que estamos en la página de nodos, podemos asignar 0 ejecutores al nodo "principal" para
que no ejecute tareas, cosa que se desaconseja y que es responsabilidad de los agentes que vayamos levantando.

## Una tarea de prueba

Podemos probar que nuestro agente funciona asignándole una tarea y viendo que sus comandos básicos
ejecutan en caso de ser necesarios. Como seguimos hablando de **Docker**, nos basta configurar una
tarea que lance un `docker info` o similar.

Para ello vamos a `Panel de control > Nueva Tarea`, creando una tarea estándar con un nombre cualquiera
y un proyecto de tipo libre eligiendo "Crear un proyecto de estilo libre"; añadimos un "Build Step" tipo
"shell" y escribimos `docker info`. Es importante marcar la casilla "Restringir dónde se puede ejecutar este proyecto"
y poner una expresión que seleccione los agentes **Docker**, por ejemplo, indicando "docker", que es el
nombre del agente que hemos puesto.

Lanzamos la tarea y deberíamos ver la salida con la información solicitada. En un caso real, esta tarea
estaría parametrizada y haría algo más impresionante, pero esto queda como deberes para el lector.
