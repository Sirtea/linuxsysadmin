Title: Montando una wiki interna con MediaWiki y Docker
Slug: montando-una-wiki-interna-con-mediawiki-y-docker
Date: 2018-12-03 10:00
Category: Sistemas
Tags: wiki, docker, mediawiki, mariadb, mysql



Tras cambiar de equipo de trabajo, me encuentro con un repositorio de información procedimental consistente en una carpeta compartida con varias versiones de documentos que hacen referencia al mismo procedimiento. Esto convierte la tarea de buscar un procedimiento en un infierno, por no mencionar el gran esfuerzo de mantenerlos actualizados.

Lo normal es que las empresas te pongan pegas porque propones una herramienta no autorizada, o "porque siempre se ha utilizado esto"; no me son excusas nuevas. Lo que me tocó las narices en esta situación es que la excusa era más que cutre: "montar esto va a llevar mucho tiempo".

Así pues, y en virtud de tan necias palabras he decidido hacer este artículo: montar una aplicación PHP clásica con **Docker**, con una inversión temporal negligible porque todo está en la librería estándar o creado por un tercero.

## Una wiki de estar por casa

En el equipo somos un número tirando a pequeño de chicos de operaciones, de variado conocimiento y experiencia. Pero desengañémonos: me quiero ir de vacaciones y no tener que hacerlo con un móvil y un portátil. Muchas cosas deben estar en manos de colaboradores más o menos capaces.

No es tan importante el motor de *wiki* como lo es el procedimiento y la facilidad de acceso y modificación. Como amantes del software libre y gracias a su presencia en [DockerHub](https://hub.docker.com/_/mediawiki/), la solución casi obligada es **MediaWiki**.

Aunque esta *wiki* puede funcionar con una base de datos **SQLite**, parece más natural utilizar la compañera clásica de un sistema **LAMP**, aunque como los tiempos varian, he elegido **MariaDB**, también en la librería oficial de **DockerHub**.

El *setup* no puede ser más simple:

* Una base de datos tipo **MySQL**
* Un contendor **MediaWiki**, configurado para apuntar a la base de datos

Por simplicidad, vamos a utilizar **docker-compose** para levantar ambos servicios (o el *stack* si usáis **Docker Swarm**). Este es el fichero *docker-compose.yml* que he utilizado:

```bash
gerard@atlantis:~/tools/wiki$ cat docker-compose.yml
version: '3'
services:
  wiki_ops:
    image: mediawiki
    container_name: wiki_ops
    hostname: wiki_ops
    ports:
      - 8080:80
  mariadb:
    image: mariadb
    container_name: mariadb
    hostname: mariadb
    environment:
      MYSQL_DATABASE: wiki_ops
      MYSQL_USER: wiki_ops
      MYSQL_PASSWORD: changeme
      MYSQL_RANDOM_ROOT_PASSWORD: "yes"
gerard@atlantis:~/tools/wiki$
```

```bash
gerard@atlantis:~/tools/wiki$ docker-compose up -d
Creating network "wiki_default" with the default driver
Creating wiki_ops ... done
Creating mariadb  ... done
gerard@atlantis:~/tools/wiki$
```

El resultado lo podemos ver en <http://atlantis:8080/>

**NOTA**: No me voy a meter en manejar volúmenes, reinicios y otras cuestiones como múltiples instancias o balancedores; esto solo va a alargar el artículo innecesariamente.

## Configurando nuestra instancia

Cuando vamos a la página web con un navegador, el *software* se da cuenta que no existe una configuración local, es decir, que no tenemos nuestra wiki configurada. La reacción programada es la de levantar el asistente de configuración.

La configuración es trivial, de acuerdo a los parámetros de nuestro *docker-compose.yml*, siendo los de la base de datos los más importantes. Si completamos el asistente, descargaremos un fichero `LocalSettings.php` que deberemos colocar en `/var/www/html/`; yo lo he hecho mediante un *file volume*:

```bash
gerard@atlantis:~/tools/wiki$ tree
.
├── docker-compose.yml
└── LocalSettings.php

0 directories, 2 files
gerard@atlantis:~/tools/wiki$
```

```bash
gerard@atlantis:~/tools/wiki$ cat docker-compose.yml
version: '3'
services:
  wiki_ops:
    image: mediawiki
    container_name: wiki_ops
    hostname: wiki_ops
    volumes:
      - ./LocalSettings.php:/var/www/html/LocalSettings.php
    ports:
      - 8080:80
  mariadb:
    image: mariadb
    container_name: mariadb
    hostname: mariadb
    environment:
      MYSQL_DATABASE: wiki_ops
      MYSQL_USER: wiki_ops
      MYSQL_PASSWORD: changeme
      MYSQL_RANDOM_ROOT_PASSWORD: "yes"
gerard@atlantis:~/tools/wiki$
```

```bash
gerard@atlantis:~/tools/wiki$ docker-compose up -d
mariadb is up-to-date
Recreating wiki_ops ... done
gerard@atlantis:~/tools/wiki$
```

Y con esto tenemos nuestra *wiki*, gracias a **Docker**. ¿Os ha parecido mucho tiempo?
