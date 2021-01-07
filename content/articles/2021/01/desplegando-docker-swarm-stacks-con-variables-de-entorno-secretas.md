---
title: "Desplegando Docker Swarm stacks con variables de entorno secretas"
slug: "desplegando-docker-swarm-stacks-con-variables-de-entorno-secretas"
date: "2021-01-07"
categories: ['Sistemas']
tags: ['docker', 'swarm', 'templating']
---

Soy un fanático del paradigma *everything as code* y del *nada en local*.
Esto me lleva a versionar en un repositorio todo lo que hago y a tenerlo alojado
en algún servicio *cloud*. Esto significa que necesito alguna forma de ocultar
las variables de entorno problemáticas de un *stack* de **Docker Swarm**.<!--more-->

Ya hice un intento de parametrizar mis ficheros de *stack* usando [docker-app][1],
pero la aplicación está lejos de estar completa y no me gusta la dirección que
están tomando las decisiones de diseño. Reniego especialmente de los *CNAB bundles*.

Así que me planteé volver a lo básico y preguntarme si ya existe algo que me
permita simplificar la tarea de crear un `stack.yml` con parámetros incorporados;
el mismo `docker stack deploy` ya lo hace.

Si juntamos el hecho de que ya suelo tener *scripts* en **bash** que hagan el
*deploy* con el hecho de que el comando `docker stack deploy` ya substituye
las variables de entorno en el `stack.yml`, tenemos todo lo necesario.

**TRUCO**: Otra posibilidad habría sido utilizar el comando `envsubst` y componer
manualmente el `stack.yml` en salida estándar, para alimentar al comando de *deploy*,
leyendo el `stack.yml` desde la entrada estándar.

## Estado inicial

Tenemos un *stack* definido por un fichero `stack.yml` y un `deploy.sh`, que se
limitan a hacernos la vida más fácil. Solamente tenemos que ejecutar el *script*
`deploy.sh` y nuestro servicio quedaría desplegado en el **swarm**.

**NOTA**: Para no alargar el artículo con irrelevancias, voy a utilizar una imagen
cualquiera, ya que solo nos interesa el comportamiento del comando de *deploy*.

```bash
gerard@atlantis:~/deployment/myapi$ cat stack.yml 
version: '3'
services:
  myapi:
    image: nginx:alpine
    environment:
      MONGODB_URI: mongodb://myuser:mypassword@mongoserver/mydatabase
    ports:
      - "8080:80"
gerard@atlantis:~/deployment/myapi$ 
```

```bash
gerard@atlantis:~/deployment/myapi$ cat deploy.sh 
#!/bin/bash

docker stack deploy -c stack.yml myapi
gerard@atlantis:~/deployment/myapi$ 
```

```bash
gerard@atlantis:~/deployment/myapi$ ./deploy.sh 
Creating network myapi_default
Creating service myapi_myapi
gerard@atlantis:~/deployment/myapi$ 
```

Esto nos plantea el problema de que no podemos versionar el fichero `stack.yml`,
tanto porque contiene secretos (usuario y contraseña de la base de datos),
como porque expone la topología de la base de datos y, por lo tanto, no es
fácil mover nuestro *stack* a otra infraestructura.

## Primera mejora: apartamos los secretos del *stack*

En este punto nos vamos a aprovechar de que el comando `docker stack deploy`
ya sustituye las variables de entorno que le pasa el *script* de *deploy*.

Nos vamos a limitar a añadir esta variable en el *script* de *deploy* y a
retirarla del `stack.yml`. Como el `stack.yml` ya no está completo, me parece
correcto renombrarlo para dejar claro que es un plantilla (*template* en inglés).

```bash
gerard@atlantis:~/deployment/myapi$ cat stack.yml.tpl 
version: '3'
services:
  myapi:
    image: nginx:alpine
    environment:
      MONGODB_URI: ${MONGODB_URI}
    ports:
      - "8080:80"
gerard@atlantis:~/deployment/myapi$ 
```

```bash
gerard@atlantis:~/deployment/myapi$ cat deploy.sh 
#!/bin/bash

export MONGODB_URI="mongodb://myuser:mypassword@mongoserver/mydatabase"

docker stack deploy -c stack.yml.tpl myapi
gerard@atlantis:~/deployment/myapi$ 
```

```bash
gerard@atlantis:~/deployment/myapi$ ./deploy.sh 
Creating network myapi_default
Creating service myapi_myapi
gerard@atlantis:~/deployment/myapi$ 
```

Es fácil de ver como `docker stack deploy` hace la sustitución de esa variable
de entorno, que ha sido rellenada previamente por el *script* de *deploy*.
Basta con inspeccionar las variables de entorno en alguno de los contenedores
desplegados por el *script*.

```bash
gerard@atlantis:~/deployment/myapi$ docker exec myapi_myapi.1.zrwucww7qz89k33acncdd79co env | grep MONGO
MONGODB_URI=mongodb://myuser:mypassword@mongoserver/mydatabase
gerard@atlantis:~/deployment/myapi$ 
```

En este punto ya podríamos versionar el fichero `stack.yml.tpl`, pero no el
*script* de *deploy*, ya que este sigue teniendo secretos que no deberíamos
versionar, especialmente en un servidor *cloud* como por ejemplo **GitHub**.

## Segunda mejora: apartamos los secretos del *script* de *deploy*

La idea es mover todos los secretos de nuestros despliegues en un solo fichero,
que no vayamos a versionar y del que vamos a hacer *backups* para asegurar que
no lo perdemos. El resto es un poco de **bash** para incluir las variables
declaradas en este fichero.

Vamos a empezar con el fichero de secretos, que he puesto fuera de la carpeta
de mi servicio, porque voy a juntar los secretos de todos los ficheros en un
solo fichero para su fácil *backup*. Si optáis por hacerlo así, tened en cuenta
no repetir el nombre de las variables de entorno, por ejemplo, prefijándolas
por el nombre del servicio o un prefijo que lo identifique.

```bash
gerard@atlantis:~/deployment/myapi$ cat ../secrets 
MONGODB_URI="mongodb://myuser:mypassword@mongoserver/mydatabase"
gerard@atlantis:~/deployment/myapi$ 
```

El fichero `stack.yml` no muestra ningún cambio respecto al apartado anterior;
sigue recibiendo una variable de entorno que sale "de algún sitio".

```bash
gerard@atlantis:~/deployment/myapi$ cat stack.yml.tpl 
version: '3'
services:
  myapi:
    image: nginx:alpine
    environment:
      MONGODB_URI: ${MONGODB_URI}
    ports:
      - "8080:80"
gerard@atlantis:~/deployment/myapi$ 
```

El *script* de *deploy* ya no incluye directamente la variable de entorno;
ahora hace un `source` del fichero de secretos. Un punto interesante es que
el comando `docker stack deploy` va a recibir las variables de entorno del
*script* solamente **si se han exportado con anterioridad**.

Esto nos obliga a hacer el `export` en el fichero de secretos o en el *script*
de *deploy*. He optado por lo segundo para dejar el fichero de secretos lo
más declarativo posible.

```bash
gerard@atlantis:~/deployment/myapi$ cat deploy.sh 
#!/bin/bash

. ../secrets
export $(cut -d= -f1 ../secrets)

docker stack deploy -c stack.yml.tpl myapi
gerard@atlantis:~/deployment/myapi$ 
```

Solo falta hacer el correspondiente *deploy* y verificar que la variable de
entorno ha sido efectivamente reemplazada en la definición del *stack*.

```bash
gerard@atlantis:~/deployment/myapi$ ./deploy.sh 
Creating network myapi_default
Creating service myapi_myapi
gerard@atlantis:~/deployment/myapi$ 
```

```bash
gerard@atlantis:~/deployment/myapi$ docker exec myapi_myapi.1.itc0f0mhg2tg7nt7ok8n4oqfn env | grep MONGO
MONGODB_URI=mongodb://myuser:mypassword@mongoserver/mydatabase
gerard@atlantis:~/deployment/myapi$ 
```

## Consideraciones de seguridad

Hemos conseguido eliminar las variables sensibles de nuestros *stacks* y limitarlos
a un solo fichero. Este fichero es el secreto más grande de cada entorno, y debe
ser tratado como tal. Si usamos **Git** para versionar nuestros *stacks*, ya estáis
tardando en añadir el fichero de secretos en el fichero `.gitignore`.

De la misma forma, al no estar versionado el fichero de secretos, no tenemos una
copia en el *cloud*, así que deberíais intentar mantener un sistema de *backup*
adecuado para no perder este fichero.

[1]: {{< relref "/articles/2019/05/generando-ficheros-docker-compose-parametrizables-con-docker-app.md" >}}
