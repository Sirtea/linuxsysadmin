---
title: "Modificando secretos y configuraciones en servicios de Docker Swarm"
slug: "modificando-secretos-y-configuraciones-en-servicios-de-docker-swarm"
date: "2019-12-03"
categories: ['Sistemas']
tags: ['docker', 'swarm', 'secrets', 'configs', 'haproxy']
---

Todos aquellos que hemos desplegado *stacks* en **docker swarm** que usan algunas
configuraciones o secretos, nos hemos topado con problemas cuando el contenido de
estos ficheros cambia. Esto es así porque el sistema los ha diseñado para ser
objetos de lectura, y no de modificación, pero hay maneras de arreglar este problema.
<!--more-->

**NOTA**: Se asume que se conoce el uso de las configuraciones y de los secretos.
Si no es así, os puede interesar leer otro artículo con [una introducción a ambos][1].

## El problema

Supongamos que tenemos un balanceador **haproxy** que utiliza una configuración y
un conjunto de certificados inyectados como secretos. La configuración y los
secretos no son relevantes, así que vamos a centrarnos en exponer el problema.

Véase este ejemplo, al que ponemos dos certificados:


```bash
gerard@atlantis:~/mutable_configs$ tree
.
├── certs
│   ├── api.local.pem
│   └── web.local.pem
└── stack.yml

1 directory, 3 files
gerard@atlantis:~/mutable_configs$ 
```

```bash
gerard@atlantis:~/mutable_configs$ cat stack.yml 
version: '3.5'
services:
  web:
    image: sirrtea/haproxy:alpine
    secrets:
      - source: web.local.pem
      - source: api.local.pem
secrets:
  web.local.pem:
    file: certs/web.local.pem
  api.local.pem:
    file: certs/api.local.pem
gerard@atlantis:~/mutable_configs$ 
```

El contenido de los certificados no es relevante; no se usan en el contenedor porque
no he puesto la configuración relevante, así que su contenido puede ser cualquiera:

```bash
gerard@atlantis:~/mutable_configs$ cat certs/web.local.pem 
web v1
gerard@atlantis:~/mutable_configs$ 
```

```bash
gerard@atlantis:~/mutable_configs$ cat certs/api.local.pem 
api v1
gerard@atlantis:~/mutable_configs$ 
```

Hacemos un *deploy* y todo parece correcto:

```bash
gerard@atlantis:~/mutable_configs$ docker stack deploy -c stack.yml stack
Creating network stack_default
Creating secret stack_api.local.pem
Creating secret stack_web.local.pem
Creating service stack_web
gerard@atlantis:~/mutable_configs$ 
```

Más adelante decidimos actualizar o renovar el certificado de la API:

```bash
gerard@atlantis:~/mutable_configs$ cat certs/api.local.pem 
api v2
gerard@atlantis:~/mutable_configs$ 
```

Y vemos como el despliegue falla:

```bash
gerard@atlantis:~/mutable_configs$ docker stack deploy -c stack.yml stack
failed to update secret stack_api.local.pem: Error response from daemon: rpc error: code = InvalidArgument desc = only updates to Labels are allowed
gerard@atlantis:~/mutable_configs$ 
```

Eso pasa porque el nombre del secreto ya está usado, y su contenido no se puede cambiar.

## La solución

### La versión simple

Solo hay una cosa que podamos hacer en **docker swarm**: crear un secreto nuevo,
pero con un nombre nuevo, que podemos indicar manualmente en el `stack.yml`:

```bash
gerard@atlantis:~/mutable_configs$ cat stack.yml 
version: '3.5'
services:
  web:
    image: sirrtea/haproxy:alpine
    secrets:
      - source: web.local.pem
      - source: api.local.pem
secrets:
  web.local.pem:
    file: certs/web.local.pem
  api.local.pem:
    name: stack_api.local.pem-2
    file: certs/api.local.pem
gerard@atlantis:~/mutable_configs$ 
```

Y podemos desplegar con normalidad, creando el nuevo secreto y modificando el
servicio que depende de él. Ahora mismo tenemos 3 secretos: los dos certificados
inciales y el certificado de la API, versión 2; en cambio, eventualmente los
secretos antiguos del servicio `stack_web` van a quedar huérfanos y va a
haber que ir haciendo limpieza (**cron** es un amigo en esto).

```bash
gerard@atlantis:~/mutable_configs$ docker stack deploy -c stack.yml stack
Creating secret stack_api.local.pem-2
Updating service stack_web (id: rl7hia0hhft8lz076aur49xln)
gerard@atlantis:~/mutable_configs$ 
```

**TRUCO**: Ir cambiando el nombre del servicio es tedioso, pero podemos utilizar
variables de entorno para evitar modificar el `stack.yml`; este es el pilar de
este artículo, y en lo que se basa enteramente.

### Usando variables de entorno

Si no queremos modificar el `stack.yml` podemos utilizar las variables de entorno
para cambiar el nombre del secreto. Eso nos permite simplificar, pero no automatizar:

```bash
gerard@atlantis:~/mutable_configs$ cat stack.yml 
version: '3.5'
services:
  web:
    image: sirrtea/haproxy:alpine
    secrets:
      - source: web.local.pem
      - source: api.local.pem
secrets:
  web.local.pem:
    name: stack_web.local.pem-${WEB_VERSION}
    file: certs/web.local.pem
  api.local.pem:
    name: stack_api.local.pem-${API_VERSION}
    file: certs/api.local.pem
gerard@atlantis:~/mutable_configs$ 
```

Ahora la invocación es algo más compleja:

```bash
gerard@atlantis:~/mutable_configs$ WEB_VERSION=2 API_VERSION=2 docker stack deploy -c stack.yml stack
Creating secret stack_web.local.pem-2
Updating service stack_web (id: rl7hia0hhft8lz076aur49xln)
gerard@atlantis:~/mutable_configs$ 
```

Podemos crear un *script* de *deploy* que nos va a servir para guardar estas variables
y para simplificar la invocación del *deploy*:

```bash
gerard@atlantis:~/mutable_configs$ cat deploy.sh 
#!/bin/bash

WEB_VERSION=2 \
API_VERSION=2 \
docker stack deploy -c stack.yml stack
gerard@atlantis:~/mutable_configs$ 
```

### Versionado con fechas

Ya que hemos creado un *script*, podemos delegar el versionado a **bash**: podemos
crear una lógica autoincremental en cada despliegue (por ejemplo guardando la
versión en un fichero), o directamente poner una versión basada en un *timestamp*.

```bash
gerard@atlantis:~/mutable_configs$ cat deploy.sh 
#!/bin/bash

TIMESTAMP=$(date +%Y%m%d%H%M%S)

WEB_VERSION=${TIMESTAMP} \
API_VERSION=${TIMESTAMP} \
docker stack deploy -c stack.yml stack
gerard@atlantis:~/mutable_configs$ 
```

Y así cada vez que despleguemos se va a crear el secreto de nuevo, acumulándolos
sin control, pero sin causar errores en nuestros despliegues:

```bash
gerard@atlantis:~/mutable_configs$ ./deploy.sh 
Creating secret stack_web.local.pem-20191022162626
Creating secret stack_api.local.pem-20191022162626
Updating service stack_web (id: rl7hia0hhft8lz076aur49xln)
gerard@atlantis:~/mutable_configs$ 
```

Lo malo es que recreamos el secreto tanto si se cambia como si no, y el servicio
del que depende se redespliega sí o sí; aunque el certificado no haya cambiado. Eso
es así porque el servicio pasa a usar **otro secreto**.

### Versionado por contenido del fichero

Podemos crear un versionado que sea un *checksum* del fichero. Esto va a evitar
que el secreto (y por lo tanto el servicio) se recree cada vez, haciéndolo solamente
si el fichero referido ha cambiado.

Así pues, podemos hacer una suma MD5 del fichero y utilizarla en el nombre del
secreto, para indicarle a **docker** si ha cambiado o no, y siendo así, la pueda
recrear de acuerdo con el fichero modificado.

```bash
gerard@atlantis:~/mutable_configs$ cat stack.yml 
version: '3.5'
services:
  web:
    image: sirrtea/haproxy:alpine
    secrets:
      - source: web.local.pem
      - source: api.local.pem
secrets:
  web.local.pem:
    name: web.local.pem-${WEB_LOCAL_PEM_DIGEST}
    file: certs/web.local.pem
  api.local.pem:
    name: api.local.pem-${API_LOCAL_PEM_DIGEST}
    file: certs/api.local.pem
gerard@atlantis:~/mutable_configs$ 
```

Y la suma MD5 la vamos a calcular en el *script* de despliegue:

```bash
gerard@atlantis:~/mutable_configs$ cat deploy.sh 
#!/bin/bash

function md5 { md5sum ${1} | cut -b 1-32; }

WEB_LOCAL_PEM_DIGEST=$(md5 certs/web.local.pem) \
API_LOCAL_PEM_DIGEST=$(md5 certs/api.local.pem) \
docker stack deploy -c stack.yml stack
gerard@atlantis:~/mutable_configs$ 
```

Ahora solo nos queda ir desplegando cuando cambiemos nuestros secretos, sin miedo
a que nos reinicien el servicio de forma innecesaria, solo creando los secretos
estrictamente necesarios, y reinciando los servicios que los utilicen.

```bash
gerard@atlantis:~/mutable_configs$ ./deploy.sh 
Creating secret api.local.pem-46cadbee594fd787aa0a0bda4383d429
Creating secret web.local.pem-aac3007d4e783449fd6f8a11c2a5f857
Updating service stack_web (id: rl7hia0hhft8lz076aur49xln)
gerard@atlantis:~/mutable_configs$ 
```

Así pues, si no cambiamos los ficheros, no hay modificaciones en el estado del *swarm*:

```bash
gerard@atlantis:~/mutable_configs$ ./deploy.sh 
Updating service stack_web (id: rl7hia0hhft8lz076aur49xln)
gerard@atlantis:~/mutable_configs$ 
```

Supongamos ahora que actualizamos el certificado de la API, con una nueva versión:

```bash
gerard@atlantis:~/mutable_configs$ cat certs/api.local.pem 
api v3
gerard@atlantis:~/mutable_configs$ 
```

Podemos comprobar que se actualiza el servicio relativo al fichero modificado, no a ambos:

```bash
gerard@atlantis:~/mutable_configs$ ./deploy.sh 
Creating secret api.local.pem-68f314f0964e435b504724fd9213e2b8
Updating service stack_web (id: rl7hia0hhft8lz076aur49xln)
gerard@atlantis:~/mutable_configs$ 
```

Y con esto podemos modificar alegremente nuestras configuraciones y secretos.

## Un poco de limpieza

Si vamos operando con los secretos y las configuraciones, estos se van acumulando.

```bash
gerard@atlantis:~/mutable_configs$ docker secret ls
ID                          NAME                                             DRIVER              CREATED              UPDATED
qecmz9fkhbexvztz0rs78pc8a   api.local.pem-46cadbee594fd787aa0a0bda4383d429                       3 minutes ago        3 minutes ago
g6fzy2tmaol0gj2b6rclt7jww   api.local.pem-68f314f0964e435b504724fd9213e2b8                       About a minute ago   About a minute ago
wahu4pnsti2jcd31ws6zjxz1n   stack_api.local.pem                                                  44 minutes ago       44 minutes ago
gh6s8f1whnxsk3kird98u8ps8   stack_api.local.pem-2                                                38 minutes ago       22 minutes ago
rs5w351apbjbsgni8semxutk4   stack_api.local.pem-20191022162626                                   14 minutes ago       14 minutes ago
1r775dkhgpbarrkn6gdv0uxrl   stack_web.local.pem                                                  44 minutes ago       38 minutes ago
ia6jp34t7qz839ef5q71c4l33   stack_web.local.pem-2                                                25 minutes ago       22 minutes ago
a19ea3617txl142qfjs87taub   stack_web.local.pem-20191022162626                                   14 minutes ago       14 minutes ago
e0ou2k00z4swzzfiqhgie4t0f   web.local.pem-aac3007d4e783449fd6f8a11c2a5f857                       3 minutes ago        About a minute ago
gerard@atlantis:~/mutable_configs$ 
```

No existe ningún proceso que vaya limpiando aquellos que usemos, así que deberíamos
encargarnos personalmente de esta limpieza. La mala notícia es que no hay una forma
fácil de saber los que ya no necesitamos.

Destruir el *stack* entero va a eliminar los secretos que creó, pero esta operación
no es algo que queramos hacer con cierta periodicidad. Sin embargo, podemos aprovechar
que **docker** no elimina nada que esté en uso. Esto nos permite lanzar una operación
de eliminación completa y dejar que **docker** salve aquellos que le son útiles:

```bash
gerard@atlantis:~/mutable_configs$ docker secret ls -q | xargs docker secret rm
qecmz9fkhbexvztz0rs78pc8a
wahu4pnsti2jcd31ws6zjxz1n
gh6s8f1whnxsk3kird98u8ps8
rs5w351apbjbsgni8semxutk4
1r775dkhgpbarrkn6gdv0uxrl
ia6jp34t7qz839ef5q71c4l33
a19ea3617txl142qfjs87taub
Error response from daemon: rpc error: code = InvalidArgument desc = secret 'api.local.pem-68f314f0964e435b504724fd9213e2b8' is in use by the following service: stack_web
Error response from daemon: rpc error: code = InvalidArgument desc = secret 'web.local.pem-aac3007d4e783449fd6f8a11c2a5f857' is in use by the following service: stack_web
gerard@atlantis:~/mutable_configs$ 
```

```bash
gerard@atlantis:~/mutable_configs$ docker secret ls
ID                          NAME                                             DRIVER              CREATED             UPDATED
g6fzy2tmaol0gj2b6rclt7jww   api.local.pem-68f314f0964e435b504724fd9213e2b8                       6 minutes ago       6 minutes ago
e0ou2k00z4swzzfiqhgie4t0f   web.local.pem-aac3007d4e783449fd6f8a11c2a5f857                       8 minutes ago       6 minutes ago
gerard@atlantis:~/mutable_configs$ 
```

Solo haría falta hacer esta operación con cierta frecuencia, posiblemente en un
**cron**, o mediante algún contenedor auxiliar que vaya lanzando la operación.
Dependiendo del tamaño de vuestras configuraciones y secretos, os puede interesar
implementar esto cuanto antes, pero dado que mis secretos ocupan unos pocos
*kilobytes*, voy a dejarlo para más adelante.

[1]: {{< relref "/articles/2019/06/distribuyendo-contenido-en-docker-swarm-configuraciones-y-secretos.md" >}}
