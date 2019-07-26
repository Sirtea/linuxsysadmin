---
title: "Generando ficheros docker-compose parametrizables con docker-app"
slug: "generando-ficheros-docker-compose-parametrizables-con-docker-app"
date: 2019-05-16
categories: ['Operaciones']
tags: ['docker', 'docker-compose', 'swarm', 'docker-app']
---

Casi siempre he utilizado **docker-compose** en mi local, y eso me ayudó mucho cuando empecé a usar **Docker Swarm**. El fichero `docker-compose.yml` varía un poco en cada entorno y cada vez que se modifica se degrada respecto al original, por no mencionar el problema de mantener actualizadas las copias.<!--more-->

Luego vienen los destrozos, con compañeros que hacen desaparecer pedazos de fichero, especialmente la lista completa de variables de entorno necesarias. Por eso es necesario mantener un `docker-compose.yml` único como si de una plantilla se tratara, y proveer alguna forma de sobreescribir los parámetros propios de cada entorno.

Vamos a suponer para este artículo que tenemos un *webservice* en un contenedor. Por brevedad voy a utilizar un servidor que responda solamente con un texto parametrizable.

```bash
gerard@atlantis:~/workspace/dockerapp$ cat docker-compose.yml 
version: '3.2'
services:
  hello:
    image: hashicorp/http-echo
    command: ["-text", "hello world"]
    ports:
      - 5678:5678
gerard@atlantis:~/workspace/dockerapp$ 
```

Lo levantamos y comprobamos que devuelve lo esperado:

```bash
gerard@atlantis:~/workspace/dockerapp$ docker-compose up -d
Creating network "dockerapp_default" with the default driver
Creating dockerapp_hello_1 ... done
gerard@atlantis:~/workspace/dockerapp$ 
```

```bash
gerard@atlantis:~/workspace/dockerapp$ curl http://localhost:5678
hello world
gerard@atlantis:~/workspace/dockerapp$ 
```

Ahora empezad a pensar en varias copias del fichero, con modificaciones locales según el servidor o el entorno... En fin, mantenerlo o versionarlo es **una auténtica pesadilla**.

Para ello, los mismos desarrolladores de **Docker** han pensado en una forma de parametrizar estos ficheros y, aunque todavía está muy verde, es un paso en la dirección correcta. Las llaman **docker apps**, y [esta es su documentación](https://github.com/docker/app).

Vamos a empezar "instalando" el binario `docker-app`, que no es más que descargarlo de <https://github.com/docker/app/releases> y ponerlo en el *path* del usuario que lo necesite. Personalmente, yo lo he puesto en `/usr/local/bin`.

## Creando una docker app

Una **docker app** no es otra cosa que la unión de 3 partes:

* Metadatos de la aplicación: nombre, versión, mantenedores, ...
* El fichero `docker-compose.yml`, posiblemente con variables declaradas
* Una sección de variables que, aunque se pueden sobreescribir, nos valen como "las habituales" que se usan por defecto

Estas partes se pueden distribuir como 3 ficheros dentro de una carpeta, o como un solo fichero. Como es fácil de juntarlos y partirlos *a posteriori*, vamos a empezar con uno solo. Esto nos simplifica las salidas, y no perdemos legibilidad por ser un ejemplo pequeño.

```bash
gerard@atlantis:~/workspace/dockerapp$ docker-app init --single-file myapp
gerard@atlantis:~/workspace/dockerapp$ 
```

Esto nos genera un fichero con el nombre indicado y la extensión `.dockerapp`.

```bash
gerard@atlantis:~/workspace/dockerapp$ ls
docker-compose.yml  myapp.dockerapp
gerard@atlantis:~/workspace/dockerapp$ 
```

Este fichero está lleno de comentarios explicativos, pero creo personalmente que no hacen ninguna falta, así que no los mostraré. Veamos las 3 partes indicadas:

```bash
gerard@atlantis:~/workspace/dockerapp$ cat myapp.dockerapp | grep -v ^#
version: 0.1.0
name: myapp
description: 
maintainers:
  - name: gerard
    email: 

---
version: '3.2'
services:
  hello:
    image: hashicorp/http-echo
    command: ["-text", "hello world"]
    ports:
      - 5678:5678

---
{}
gerard@atlantis:~/workspace/dockerapp$ 
```

Es un buen momento para eliminar el fichero original, para mantener el ejemplo mínimo.

```bash
gerard@atlantis:~/workspace/dockerapp$ rm docker-compose.yml 
gerard@atlantis:~/workspace/dockerapp$ 
```

```bash
gerard@atlantis:~/workspace/dockerapp$ ls
myapp.dockerapp
gerard@atlantis:~/workspace/dockerapp$ 
```

La idea es que un fichero tipo `docker-compose.yml` se **renderiza** a demanda:

```bash
gerard@atlantis:~/workspace/dockerapp$ docker-app render
version: "3.2"
services:
  hello:
    command:
    - -text
    - hello world
    image: hashicorp/http-echo
    ports:
    - mode: ingress
      target: 5678
      published: 5678
      protocol: tcp
gerard@atlantis:~/workspace/dockerapp$ 
```

Hasta aquí, no ha cambiado nada. Es el momento de sacarle provecho a la complejidad añadida.

## Introduciendo las variables

Es normal que los entornos o servidores apliquen pequeños cambios en este fichero, y para ello, `docker-app` introduce las variables. Se trata de declarar como variables lo que pueda cambiar, darles valores por defecto, y luego ya las sobreescribiremos si nos hace falta.

Por la sencillez del ejemplo, poco podemos cambiar; como ejemplo podemos usar el texto devuelto o el puerto en el que vamos a mapear el servicio en el servidor. Se trata de reemplazar los valores modificables de la segunda sección de la **docker app** por variables de la forma `${variable}`, dándole valores por defecto en la tercera sección de la **docker app**.

```bash
gerard@atlantis:~/workspace/dockerapp$ cat myapp.dockerapp 
version: 0.1.0
name: myapp
description: 
maintainers:
  - name: gerard
    email: 

---
version: '3.2'
services:
  hello:
    image: hashicorp/http-echo
    command: ["-text", "${text}"]
    ports:
      - ${port}:5678

---
text: hello world
port: 5678
gerard@atlantis:~/workspace/dockerapp$ 
```

Si renderizamos la aplicación, no vamos a ver cambio ninguno:

```bash
gerard@atlantis:~/workspace/dockerapp$ docker-app render
version: "3.2"
services:
  hello:
    command:
    - -text
    - hello world
    image: hashicorp/http-echo
    ports:
    - mode: ingress
      target: 5678
      published: 5678
      protocol: tcp
gerard@atlantis:~/workspace/dockerapp$ 
```

## Sobreescribiendo las variables

Si necesitamos modificar alguna de las variables, `docker-app` nos ofrece dos formas:

* Con un parámetro durante el *renderizado*
* Con un fichero de cambios

La primera es la más fácil, necesitando solamente indicar el *flag* `--set` para indicar el cambio. Veamos la sobreescritura del puerto, pero dejando el texto por defecto:

```bash
gerard@atlantis:~/workspace/dockerapp$ docker-app render --set port=8080
version: "3.2"
services:
  hello:
    command:
    - -text
    - hello world
    image: hashicorp/http-echo
    ports:
    - mode: ingress
      target: 5678
      published: 8080
      protocol: tcp
gerard@atlantis:~/workspace/dockerapp$ 
```

Esta opción está bien para un caso aislado o prueba, pero si queremos versionar los cambios, no es lo recomendable. Para ello se nos ofrece la otra opción, que es creando un fichero de cambios:

```bash
gerard@atlantis:~/workspace/dockerapp$ cat test.yml 
text: lorem ipsum
gerard@atlantis:~/workspace/dockerapp$ 
```

```bash
gerard@atlantis:~/workspace/dockerapp$ docker-app render -f test.yml 
version: "3.2"
services:
  hello:
    command:
    - -text
    - lorem ipsum
    image: hashicorp/http-echo
    ports:
    - mode: ingress
      target: 5678
      published: 5678
      protocol: tcp
gerard@atlantis:~/workspace/dockerapp$ 
```

## Un caso práctico

Vamos a suponer que tenemos 3 servidores, con las excepciones que siguen:

* **serverA**: Es el servidor de desarrollo; vamos a cambiar el texto para que no hayan confusiones durante los tests
* **serverB**: Primera réplica de producción; como el puerto 5678 está ocupado, lo cambiamos por el 5679
* **serverC**: Segunda réplica de producción; este no necesita cambios respecto a la plantilla

Así pues, vamos a organizar el repositorio en donde guardamos las configuraciones con un fichero plantilla, y 3 ficheros especificando las diferencias de cada instancia, que quedan así:

```bash
gerard@atlantis:~/workspace/dockerapp$ cat dev.yml 
text: lorem ipsum (this is development)
gerard@atlantis:~/workspace/dockerapp$ 
```

```bash
gerard@atlantis:~/workspace/dockerapp$ cat prod1.yml 
port: 5679
gerard@atlantis:~/workspace/dockerapp$ 
```

```bash
gerard@atlantis:~/workspace/dockerapp$ cat prod2.yml 
gerard@atlantis:~/workspace/dockerapp$ 
```

Vemos claramente que según el fichero usado se cumple con las necesidades específicas, pero manteniendo la plantilla unificada.

```bash
gerard@atlantis:~/workspace/dockerapp$ docker-app render -f dev.yml 
version: "3.2"
services:
  hello:
    command:
    - -text
    - lorem ipsum (this is development)
    image: hashicorp/http-echo
    ports:
    - mode: ingress
      target: 5678
      published: 5678
      protocol: tcp
gerard@atlantis:~/workspace/dockerapp$ 
```

```bash
gerard@atlantis:~/workspace/dockerapp$ docker-app render -f prod1.yml 
version: "3.2"
services:
  hello:
    command:
    - -text
    - hello world
    image: hashicorp/http-echo
    ports:
    - mode: ingress
      target: 5678
      published: 5679
      protocol: tcp
gerard@atlantis:~/workspace/dockerapp$ 
```

```bash
gerard@atlantis:~/workspace/dockerapp$ docker-app render -f prod2.yml 
version: "3.2"
services:
  hello:
    command:
    - -text
    - hello world
    image: hashicorp/http-echo
    ports:
    - mode: ingress
      target: 5678
      published: 5678
      protocol: tcp
gerard@atlantis:~/workspace/dockerapp$ 
```

Solo nos queda lanzar los comandos que los aplican en cada servidor, que a su vez, tendrá un clon del repositorio:

```bash
gerard@serverA:~/workspace/dockerapp$ docker-app render -f dev.yml | docker-compose -f - up -d
Creating network "dockerapp_default" with the default driver
Creating dockerapp_hello_1 ... done
gerard@serverA:~/workspace/dockerapp$ 
```

```bash
gerard@serverA:~/workspace/dockerapp$ curl http://localhost:5678
lorem ipsum (this is development)
gerard@serverA:~/workspace/dockerapp$ 
```

```bash
gerard@serverB:~/workspace/dockerapp$ docker-app render -f prod1.yml | docker-compose -f - up -d
Creating network "dockerapp_default" with the default driver
Creating dockerapp_hello_1 ... done
gerard@serverB:~/workspace/dockerapp$ 
```

```bash
gerard@serverB:~/workspace/dockerapp$ curl http://localhost:5679
hello world
gerard@serverB:~/workspace/dockerapp$ 
```

```bash
gerard@serverC:~/workspace/dockerapp$ docker-app render -f prod2.yml | docker-compose -f - up -d
Creating network "dockerapp_default" with the default driver
Creating dockerapp_hello_1 ... done
gerard@serverC:~/workspace/dockerapp$ 
```

```bash
gerard@serverC:~/workspace/dockerapp$ curl http://localhost:5678
hello world
gerard@serverC:~/workspace/dockerapp$ 
```

Y con esto mantenemos un solo repositorio, una sola plantilla, y los cambios de forma centralizada y controlada.
