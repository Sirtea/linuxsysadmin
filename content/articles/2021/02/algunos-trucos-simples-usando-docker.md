---
title: "Algunos trucos simples usando Docker"
slug: "algunos-trucos-simples-usando-docker"
date: "2021-02-20"
categories: ['Sistemas']
tags: ['docker', 'registro', 'build', 'swarm', 'overlay']
---

Hace ya mucho tiempo que trabajo con **Docker** y **Docker Swarm**. He intentado
documentar lo que voy haciendo para futuras referencias y eso se refleja en los
artículos de este *blog*. Sin embargo, algunos de los trucos que he usado no
tienen suficiente material para justificar un artículo nuevo.<!--more-->

Por supuesto, esto no significa que tengan que caer en el olvido, y de vez en
cuando es necesario hacer artículos recopilatorios de trucos que podemos requerir
en algún momento dado. Este es uno de estos artículos.

## Login en un registro Docker desde un script

Si utilizamos herramientas existentes para trabajar con registros **Docker**,
por ejemplo **Jenkins** o **Ansible**, muchos de ellos ya tienen estas
funcionalidades disponibles. Pero usar estas herramientas es demasiado para los
usos más comunes que necesitamos.

Por qué negarlo: en este *blog* somos fans de los *scripts* de **bash**, y muchas
veces se trata de la forma más rápida de tener algo funcional listo. Pero los
*scripts* suelen ejecutarse de forma **no interactiva** con lo que no deberían
preguntar por ningún tipo de entrada de usuario (ni usuarios, ni *passwords*, ...).

Afortunadamente, **Docker** nos ofrece la posibilidad de leer la *password* como
un parámetro o desde la entrada estándar. La primera opción se considera insegura;
basta con hacer un `ps` en el servidor para ver la línea de comandos usada y sus
parámetros. La segunda es mejor opción, y nos permite sacar la *password* desde
un fichero o desde una variable de entorno.

Un ejemplo de uso de parámetro (evitad esta opción):

```bash
docker login --username "user" --password "s3cr3t"
```

Un segundo ejemplo, sacando la *password* de un fichero:

```bash
cat .dockerhub_pass | docker login --username "user" --password-stdin
```

Y finalmente, usando variables de entorno:

```bash
DH_USER="user"
DH_PASSWORD="s3cr3t"
echo "${DH_PASSWORD}" | docker login --username "${DH_USER}" --password-stdin
```

**TRUCO**: No os olvidéis de hacer el correspondiente *logout* para no dejar
el fichero con credenciales en el servidor en `~/.docker/config.json`.

## Docker build directamente desde repositorios Git

Otra de las grandes barbaridades que he visto, es utilizar *jobs* de **Jenkins**
para construir y hacer el *push* al registro de **Docker**; esto es una idea
bastante razonable, hasta que ves como delegan la descarga de las fuentes al
servidor de *build*, que lo suele dejar descargado en el *workspace* y parasitando
el espacio de disco del servidor.

El comando `docker build` puede construir utilizando directamente como contexto un
repositorio **Git** remoto, incluso especificando un *tag* u otra referencia. Y lo
que es más interesante: solo se descarga lo necesario para construir la referencia
solicitada, lo hace en una carpeta temporal, y la elimina al acabar. Vaya, que nos
queda la imagen local lista para hacer el `docker push`, sin nada de residuos.

Podemos poner un ejemplo, que nos va a dejar más claras las cosas:

```bash
REGISTRY=127.0.0.1:5000
REPOSITORY=git@gitserver:myapi.git
IMAGE=myapi
TAG=v1.0.0

docker build -t ${REGISTRY}/${IMAGE}:${TAG} ${REPOSITORY}#${TAG}
docker push ${REGISTRY}/${IMAGE}:${TAG}
```

O lo que sería lo mismo, tras sustituir las variables:

```bash
docker build -t 127.0.0.1:5000/myapi:v1.0.0 git@gitserver:myapi.git#v1.0.0
docker push 127.0.0.1:5000/myapi:v1.0.0
```

**WARNING**: Para que este estilo de URL de repositorio **Git** sea reconocido
como tal, el usuario SSH debe ser `git`. Por algún motivo no funciona con otros
nombres de usuario.

Si estos comandos los ejecuta un servidor de *build* tipo **Jenkins**, podemos
utilizar el *tag* recogido como un parámetro del *job* que vayamos a lanzar.
Tampoco es casualidad que lo pongamos tanto en el *tag* de **Docker** como en
el *tag* de **Git**; nombrar ambos *tags* de forma idéntica es una convención
que nos va a ahorrar campos de formulario y posibles errores futuros.

**TRUCO**: Recordad que si el `docker push` necesita antes hacer un `docker login`,
podemos utilizar el truco expuesto en este artículo, un poco más arriba.

## Creando redes en Docker si no existieran previamente

En muchos de los artículos que hay en este *blog* se trabaja con redes *overlay*
creadas a mano, que nos permiten juntar servicios de diferentes *stacks* para
que se vean entre sí. En estos artículos se indican los comandos manuales de
creación de estas redes, y en tantos otros artículos se utilizan *scripts* de
*deploy*, para añadir lógica antes del `docker stack deploy` usado.

Tener *scripts* y hacer tareas manuales, parece una contradicción. Vamos a
delegar la creación de la red en estos *scripts* de *deploy*, aunque esto
requiere un poco de lógica adicional: "crea la red si no existe". Esto nos permite
poner esta lógica en todos los *scripts* sin miedo a que cada uno cree la red,
evitando de paso que repetidas ejecuciones la dupliquen.

Esta lógica es muy simple: si hacemos un `docker network inspect` de una red
existente, el valor de retorno es "cierto"; en caso contrario, la creamos. La
salida del comando la podemos ignorar directamente.

```bash
gerard@atlantis:~/projects/stacks/myapp$ cat deploy.sh 
#!/bin/bash

docker network inspect apps >/dev/null 2>&1 || docker network create -d overlay apps

docker stack deploy -c stack.yml myapp
gerard@atlantis:~/projects/stacks/myapp$ 
```

**TRUCO**: Esta línea la pondríamos en todos los *scripts* de *deploy* que pudieran
necesitar esta red; esto podría incluir más aplicaciones y el *proxy* o balanceador
que pusiéramos delante. De esta forma no importa el *stack* que se despliegue primero.
