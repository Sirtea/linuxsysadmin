---
title: "Usando el servidor integrado de PHP en un contenedor Docker"
slug: "usando-el-servidor-integrado-de-php-en-un-contenedor-docker"
date: 2019-01-07
categories: ['Sistemas']
tags: ['docker', 'php']
---

En mi trabajo estamos renovando el proveedor de infraestructura de nuestros servicios. Al migrar las máquina nos estamos encontrando servicios desorganizados, en varios lenguajes y en versiones antiguas. Uno de estos servicios es un frontal PHP mugriento, y lo migramos rápidamente en un contenedor usando el servidor incorporado de PHP.<!--more-->

Normalmente, estoy en contra de usar servidores de desarrollo para servir la aplicación final, pero dada la prisa de la migración y el escaso número de usuarios que usan este frontal (¡tres!), fue una medida más que aceptable, en vistas a una futura mejora.

El resultado no fue tan malo como esperaba, y como me gusta como servidor de desarrollo, me lo he apuntado. Como no soy de programar PHP, lo mantendré en mi máquina hasta que me harte de verlo, momento en que su eliminación va a dejar mi máquina 100% libre de PHP, gracias a **Docker**.

Para mantener limpio mi entorno, lo voy a poner todo en una carpeta local, con el *docker-compose.yml* de runtime, el *Dockerfile* para construir el contenedor, y una carpeta de código que voy a montar como volumen para no tener que reconstruir la imagen a cada cambio.

```bash
gerard@atlantis:~/workspace/phpserver$ tree
.
├── app
│   └── info.php
├── docker-compose.yml
└── Dockerfile

1 directory, 3 files
gerard@atlantis:~/workspace/phpserver$
```

El *Dockerfile* es bastante simple, y se limita a instalar **PHP**, y las extensiones que nuestro código pueda necesitar. El uso de **tini** es simplemente para que el contenedor pueda parar de forma correcta; más información en [este otro artículo]({{< relref "/articles/2017/09/un-proceso-inicial-para-docker-tini-y-dumb-init.md" >}}).

```bash
gerard@atlantis:~/workspace/phpserver$ cat Dockerfile
FROM alpine:3.8
RUN apk add --no-cache tini php7 php7-session php7-pdo_mysql
ENTRYPOINT ["/sbin/tini", "--"]
CMD ["/usr/bin/php7", "-S", "0.0.0.0:8080", "-t", "/srv/app"]
gerard@atlantis:~/workspace/phpserver$
```

**NOTA**: Es posible que necesitéis ajustar las dependencias `php7-*` en base a vuestro código. Las extensiones `php7-session` y `php7-pdo_mysql` las puse porque son lo que se necesita para ejecutar [Adminer](https://www.adminer.org/); al acabar la prueba de concepto me puse a probar de hacer una API REST y tuve que poner `php7-json`.

Tanto para el *runtime* como para el *build time*, voy a utilizar **docker-compose**, que me permite versionar ambos procesos y su manejo de forma fácil:

```bash
gerard@atlantis:~/workspace/phpserver$ cat docker-compose.yml
version: '3'
services:
  phpserver:
    image: phpserver
    build: .
    container_name: phpserver
    hostname: phpserver
    volumes:
      - ./app:/srv/app:ro
    ports:
      - "8080:8080"
gerard@atlantis:~/workspace/phpserver$
```

Finalmente, y para ver que todo funciona necesitamos una aplicación, que en este caso es un `phpinfo()` estándar. Como he mencionado también puse **adminer**, pero esto es ahora irrelevante. Se pone algo solo para que el artículo quede completo y funcional, pero cambiaremos el código según lo vayamos desarrollando.

```bash
gerard@atlantis:~/workspace/phpserver$ cat app/info.php
<?php phpinfo(); ?>
gerard@atlantis:~/workspace/phpserver$
```

La construcción no tiene secreto alguno; se construye con el contexto de la carpeta local (solo se usa el `Dockerfile`) y se le asigna el *tag* de imagen del campo `image`.

```bash
gerard@atlantis:~/workspace/phpserver$ docker-compose build
Building phpserver
Step 1/4 : FROM alpine:3.8
 ---> 196d12cf6ab1
Step 2/4 : RUN apk add --no-cache tini php7 php7-session php7-pdo_mysql
 ---> Running in 565e2b5f767b
...
Removing intermediate container 565e2b5f767b
 ---> 2df4637bc4bc
Step 3/4 : ENTRYPOINT ["/sbin/tini", "--"]
 ---> Running in 3069cd1a57d4
Removing intermediate container 3069cd1a57d4
 ---> 5c34542dde4f
Step 4/4 : CMD ["/usr/bin/php7", "-S", "0.0.0.0:8080", "-t", "/srv/app"]
 ---> Running in 00027b5023e2
Removing intermediate container 00027b5023e2
 ---> de340d9fb385
Successfully built de340d9fb385
Successfully tagged phpserver:latest
gerard@atlantis:~/workspace/phpserver$
```

La verdad es que no paro de maravillarme de lo poco que ocupan las imagenes con base de **Alpine Linux**... ¡Solo 15mb!

```bash
gerard@atlantis:~/workspace/phpserver$ docker images
REPOSITORY          TAG                 IMAGE ID            CREATED             SIZE
phpserver           latest              de340d9fb385        19 seconds ago      14.3MB
alpine              3.8                 196d12cf6ab1        2 months ago        4.41MB
gerard@atlantis:~/workspace/phpserver$
```

Levantamos el servidor con el comando habitual, si más complicaciones:

```bash
gerard@atlantis:~/workspace/phpserver$ docker-compose up -d
Creating network "phpserver_default" with the default driver
Creating phpserver ... done
gerard@atlantis:~/workspace/phpserver$
```

Podemos ver el resultado en <http://atlantis:8080/info.php>. Dada la naturaleza de **PHP**, solo os queda abrir la carpeta `app` y meter vuestro código, bien sea copiándolo, o bien sea desarrollándolo ahí directamente. No os olvidéis de ir revisando la salida usando `docker-compose logs -f` por si os faltaran extensiones, o simplemente para ver los errores que vuestro código pueda generar.
