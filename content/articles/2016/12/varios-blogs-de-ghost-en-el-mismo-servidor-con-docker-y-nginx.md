---
title: "Varios blogs de Ghost en el mismo servidor con Docker y Nginx"
slug: "varios-blogs-de-ghost-en-el-mismo-servidor-con-docker-y-nginx"
date: 2016-12-26
categories: ['Miscelánea']
tags: ['ghost', 'blog', 'virtual hosts']
---

Como ya vimos en [un artículo anterior]({{< relref "/articles/2016/11/ghost-un-motor-para-hacer-blogs.md" >}}) cada instancia de **Ghost** necesita una combinación de dirección y puerto distinta. Esto supone un problema porque la pesadez de indicar el puerto en el navegador. Podemos poner un único servidor **Nginx** que redirija las peticiones de forma transparente según el dominio pedido.<!--more-->

Ya vimos la facilidad de levantar un contenedor con un *blog* de **Ghost**. De hecho, podemos levantar tantos como queramos, porque **Docker** provee a cada uno de su propia dirección IP. Sin embargo, la red de contenedores **Docker** es privada y no es visible para el resto del mundo.

Podemos solventar este problema exponiendo los puertos en la máquina huésped. Sin embargo, el hecho de que cada usuario tenga que indicar el puerto en la URL no es bonito. Así pues, vamos a esconder todos los contenedores sin exponer sus puertos. La única parte expuesta va a ser un contenedor **Nginx** representante de todo el sistema (esto es lo que se llama un *proxy* reverso), en el puerto 80. Este servicio va a recibir todas las peticiones a nuestro servidor, y las va a dirigir al contenedor que le corresponda de acuerdo con el dominio pedido.

Vamos a simplificarnos el proceso usando **docker-compose** para declarar el entorno y levantarlo de un solo comando. Es especialmente importante que las imágenes no se repitan, porque implicaría reconstruirlas cada vez. En vez de eso, vamos a abusar de las configuraciones vía variables de entorno.

Así nos quedaría la carpeta de proyecto:

```bash
gerard@sirius:~/docker/multighost$ tree
.
├── ghost_blog
│   ├── config.js
│   └── Dockerfile
├── proxy
│   ├── Dockerfile
│   ├── entrypoint.sh
│   ├── generate_configs.sh
│   └── nginx.conf
└── docker-compose.yml

2 directories, 7 files
gerard@sirius:~/docker/multighost$ 
```

## La imagen de ghost

Vamos a hacer una imagen para el entono de producción y vamos a dejar que use su propia base de datos **sqlite**. Como ya vimos, la configuración por defecto de la imagen para el entorno *production* está mal. Incluso aunque estuviera bien, hay parámetros que querremos cambiar, por ejemplo, la URL de nuestra web.

Por estos problemas, vamos a poner una nueva configuración. Como la imagen oficial no necesita mas cambios, el *Dockerfile* se limitará a poner la configuración en su sitio, partiendo de la imagen base.

```bash
gerard@sirius:~/docker/multighost$ cat ghost_blog/Dockerfile 
FROM ghost
COPY config.js /usr/src/ghost/config.example.js
gerard@sirius:~/docker/multighost$ 
```

Como no quiero crear una configuración e imagen para cada instancia de **Ghost**, voy a poner todas las partes diferentes en variables de entorno. El encargado de pasar estas variables de entorno va a ser el fichero *docker-compose.yml*, aunque se podría hacer a mano. El mismo intérprete de **nodejs** permite acceder a las mismas en el fichero *config.js*.

```bash
gerard@sirius:~/docker/multighost$ cat ghost_blog/config.js 
var path = require('path'),
    config;

config = {
    production: {
        url: process.env['GHOST_URL'],
        mail: {},
        database: {
            client: 'sqlite3',
            connection: {
                filename: path.join(__dirname, '/content/data/ghost.db')
            },
            debug: false
        },
        server: {
            host: '127.0.0.1',
            port: '2368'
        },
        paths: {
            contentPath: path.join(__dirname, '/content/')
        }
    }
};

module.exports = config;
gerard@sirius:~/docker/multighost$ 
```

La suerte en este caso es que solo hay una parte variable, que es la URL de nuestro sitio.

## La imagen del proxy HTTP

Esta imagen es la de nuestro representante. Va a estar mapeada en el puerto 80 de nuestro servidor y va a recibir todas las peticiones que se nos hagan. Luego las enviará al contenedor responsable y devolverá la respuesta que este genera al usuario final. Podéis pensar en él como un policía de tráfico.

Nuevamente vamos a tirar de la reusabilidad, definiendo el comportamiento de este *proxy* mediante variables de entorno, que nos va a evitar reconstruirlo cada vez que añadamos mas *blogs*. La técnica de las plantillas para su configuración se vio en [otro artículo]({{< relref "/articles/2016/09/imagenes-docker-reusables-mediante-configuraciones-dinamicas.md" >}}).

Hacemos un *Dockerfile* propio, partiendo de una imagen mínima, a la que instalaremos **nginx** y sus configuraciones.

```bash
gerard@sirius:~/docker/multighost$ cat proxy/Dockerfile 
FROM alpine:3.4
RUN apk add --no-cache nginx && \
    ln -s /dev/stdout /var/log/nginx/access.log && \
    ln -s /dev/stderr /var/log/nginx/error.log && \
    mkdir /run/nginx
COPY nginx.conf /etc/nginx/
COPY generate_configs.sh entrypoint.sh /
ENTRYPOINT ["/entrypoint.sh"]
gerard@sirius:~/docker/multighost$ 
```

Solo falta poner la configuración general, el punto de acceso al contenedor y el generador de configuraciones específicas según las variables de entorno.

```bash
gerard@sirius:~/docker/multighost$ cat proxy/nginx.conf 
worker_processes  1;
events {
	worker_connections  1024;
}
http {
	include mime.types;
	default_type application/octet-stream;
	sendfile on;
	keepalive_timeout 65;
	include conf.d/*;
}
gerard@sirius:~/docker/multighost$ cat proxy/generate_configs.sh 
#!/bin/sh

for LINE in $(echo ${DOMAINS} | sed 's/;/ /g'); do
    DOMAIN=$(echo $LINE | cut -d, -f1)
    BACKEND=$(echo $LINE | cut -d, -f2)
    echo -n "\
server {
	listen 80;
	server_name ${DOMAIN};
	location / {
		proxy_pass http://${BACKEND}:2368;
	}
}
" > /etc/nginx/conf.d/${DOMAIN}
done
gerard@sirius:~/docker/multighost$ cat proxy/entrypoint.sh 
#!/bin/sh

/generate_configs.sh
exec /usr/sbin/nginx -g "daemon off;"
gerard@sirius:~/docker/multighost$ 
```

Como apunte, cabe decir que la configuración se genera a partir de la variable de entorno DOMAINS, que no es otra cosa que pares de dominio y *backend* (separados por una coma). Estos pares se separan de otros pares mediante el uso de un punto y coma.

## Declarando el entorno

Vamos a suponer que tenemos dos dominios *ghost1.my* y *ghost2.my*. Como no los tengo de verdad, he usado el fichero */etc/hosts* para que acaben en mi local, asignándoles la dirección IP 127.0.0.1.

Vamos a tener que declarar un servicio de *proxy* y dos de **ghost**. El motivo es porque todos los contenedores del mismo servicio heredan las mismas variables de entorno, con lo que eso de *escalar* no vale. Vamos a llamar a estos servicios *ghost1* y *ghost2*, aunque el nombre es arbitrario.

Otro tema puntiagudo son los nombres de los *backends*. De acuerdo con la convención usada por **docker-compose**, una instancia se llama {carpeta contenedora}\_{nombre del servicio}\_{numero de instancia}. Eso significa que los contenedores de los dos *blogs* van a llamarse *multighost_ghost1_1* y *multighost_ghost2_1* respectivamente.

El *docker-compose.yml* no tiene ningún misterio en sí mismo. Solo hay que tener en cuenta que necesitamos indicar las variables de entorno necesarias y que el *proxy* no se puede levantar antes que los *blogs*. Esto es porque **nginx** se cae si no puede resolver el nombre de las máquinas que forman parte de su configuración.

Así quedaría el *docker-compose.yml*:

```bash
gerard@sirius:~/docker/multighost$ cat docker-compose.yml 
version: '2'
services:
  proxy:
    build: proxy
    depends_on:
      - ghost1
      - ghost2
    links:
      - ghost1
      - ghost2
    ports:
      - "80:80"
    environment:
      - DOMAINS=ghost1.my,multighost_ghost1_1;ghost2.my,multighost_ghost2_1
  ghost1:
    build: ghost_blog
    expose:
      - 2368
    environment:
      - NODE_ENV=production
      - GHOST_URL=http://ghost1.my
  ghost2:
    build: ghost_blog
    expose:
      - 2368
    environment:
      - NODE_ENV=production
      - GHOST_URL=http://ghost2.my
gerard@sirius:~/docker/multighost$ 
```

## Levantando el entorno

Esto no supone ningún misterio; usaremos los mismo comandos de **docker-compose**.

```bash
gerard@sirius:~/docker/multighost$ docker-compose up -d
Creating network "multighost_default" with the default driver
Building ghost1
Step 1 : FROM ghost
 ---> c8799e5d02e1
Step 2 : COPY config.js /usr/src/ghost/config.example.js
 ---> a59babea33ac
Removing intermediate container 4afdb804e150
Successfully built a59babea33ac
Creating multighost_ghost1_1
Building ghost2
Step 1 : FROM ghost
 ---> c8799e5d02e1
Step 2 : COPY config.js /usr/src/ghost/config.example.js
 ---> Using cache
 ---> a59babea33ac
Successfully built a59babea33ac
Creating multighost_ghost2_1
Building proxy
Step 1 : FROM alpine:3.4
 ---> 7d23b3ca3463
Step 2 : RUN apk add --no-cache nginx &&     ln -s /dev/stdout /var/log/nginx/access.log &&     ln -s /dev/stderr /var/log/nginx/error.log &&     mkdir /run/nginx
 ---> Running in aa6bdbca5088
fetch http://dl-cdn.alpinelinux.org/alpine/v3.4/main/x86_64/APKINDEX.tar.gz
fetch http://dl-cdn.alpinelinux.org/alpine/v3.4/community/x86_64/APKINDEX.tar.gz
(1/3) Installing nginx-common (1.10.1-r1)
Executing nginx-common-1.10.1-r1.pre-install
(2/3) Installing pcre (8.38-r1)
(3/3) Installing nginx (1.10.1-r1)
Executing busybox-1.24.2-r11.trigger
OK: 6 MiB in 14 packages
 ---> 6cb42f2e3eb3
Removing intermediate container aa6bdbca5088
Step 3 : COPY nginx.conf /etc/nginx/
 ---> f6f9c012d7e4
Removing intermediate container 881e06b92225
Step 4 : COPY generate_configs.sh entrypoint.sh /
 ---> aa0c311dec7d
Removing intermediate container f5351cfa8268
Step 5 : ENTRYPOINT /entrypoint.sh
 ---> Running in cf8151378f7e
 ---> 7451c8ccbfe9
Removing intermediate container cf8151378f7e
Successfully built 7451c8ccbfe9
Creating multighost_proxy_1
gerard@sirius:~/docker/multighost$ 
```

Y ya tenemos nuestro entorno funcional.

```bash
gerard@sirius:~/docker/multighost$ docker-compose ps
       Name                   Command            State         Ports        
---------------------------------------------------------------------------
multighost_ghost1_1   /entrypoint.sh npm start   Up      2368/tcp           
multighost_ghost2_1   /entrypoint.sh npm start   Up      2368/tcp           
multighost_proxy_1    /entrypoint.sh             Up      0.0.0.0:80->80/tcp 
gerard@sirius:~/docker/multighost$ 
```

Solo faltaría abrir en un navegador y apuntar a <http://ghost1.my/> y a <http://ghost2.my/> para ver los resultados.

Es importante notar que la topología del entorno se declara solamente en el *docker-compose.yml*; en caso de poner mas *blogs*, no hay que tocar otros ficheros. Bastaría con declarar un *ghost3* y modificar las variables de entorno del *proxy*, para que genere su configuración.

## Esto no es el final

A partir de aquí, se pueden aplicar muchas mejoras. Por ejemplo:

* Se podría levantar una base de datos **mysql** (u otra) en el fichero *docker-compose.yml*. El resto de instancias de **Ghost** podrían conectarse a esta base de datos, pasando los parámetros de conexión como variables de entorno, con lo que habría que modificar el *config.js*.
* Otra posibilidad sería la de aprovecharnos de la capacidad de *escalar* el número de contenedores. Modificando la variable de entorno *DOMAINS* del *proxy* y el *script* generador de configuraciones *generate_configs.sh*, se podría balancear cada dominio entre varios contenedores. Esto tendría sentido siempre y cuando la base de datos no sea **sqlite**.

La lista de mejoras podría crecer indefinidamente, pero por brevedad lo vamos a dejar como ejercicio para el lector.
