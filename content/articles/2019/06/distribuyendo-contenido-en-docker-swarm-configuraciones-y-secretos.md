---
title: "Distribuyendo contenido en Docker Swarm: configuraciones y secretos"
slug: "distribuyendo-contenido-en-docker-swarm-configuraciones-y-secretos"
date: 2019-06-25
categories: ['Operaciones']
tags: ['docker', 'swarm', 'secrets', 'configs']
---

Muchas veces he utilizado los volúmenes de **Docker** para "inyectar" un fichero de configuración que sobreescriba a otro. Cuando utilizamos **Docker Swarm** suele ser un problema distribuir estos ficheros de configuración; además, a veces necesitamos que se transmitan encriptados para que no los puedan ver los contenedores hermanos, por seguridad.<!--more-->

En estos casos se hacía necesario otro sistema de distribución de contenido que funcionara en el ámbito de **Docker Swarm**, y el equipo de **Docker** respondió; ahora disponemos de **configs** y **secrets**, que es la forma en la que podemos pasar contenido a ficheros del contenedor de forma segura y distribuida.

El sistema es simple: existen piezas de texto en los metadatos del *swarm*, ya sean *secrets* o *configs*, y estas se exponen en el sistema de ficheros del contenedor que los necesite en modo de solo lectura.

En principio, ambos funcionan de forma similar, con solo dos características diferentes que yo haya podido ver:

* Los *secrets* se guardan en el *swarm* encriptados
* La posición final de los *secrets* es `/run/secrets/<secret>`, mientras que las *configs* se dejan en `/<config>`

**AVISO**: El *path* en el que se dejan los *secrets* es fijo, mientras que las *configs* pueden modificarlo.

## Un ejemplo

Podemos ver la funcionalidad de ambos con un simple ejemplo. Por ejemplo vamos a servir contenido estático por HTTPS en un **nginx**. Es un caso representativo porque:

* Necesitamos pasar certificados SSL a los contenedores del servicio **nginx** (por supuesto encriptados, así que serán *secrets*).
* Hay que pasar la configuración de los *virtualhosts* individuales (no hace falta que esté encriptada, así que es una *config*).

En ambos casos los ficheros estarían en un *manager* del **swarm**, el tiempo justo para hacer el `docker stack deploy`. La distribución de este contenido entre los demás nodos del **swarm** es responsabilidad del *cluster*.

### Generar los certificados

Normalmente compraríamos un certificado SSL de un emisor confiable, pero para este ejemplo, lo vamos a generar autofirmado. No hagáis esto en sitio de producción.

```bash
gerard@atlantis:~/workspace/exampleweb$ openssl genrsa -out www.example.com.key 2048
Generating RSA private key, 2048 bit long modulus
....................................................+++++
.......................................................................+++++
e is 65537 (0x010001)
gerard@atlantis:~/workspace/exampleweb$ 
```

```bash
gerard@atlantis:~/workspace/exampleweb$ openssl req -new -x509 -key www.example.com.key -out www.example.com.crt -days 3650 -subj /CN=www.example.com
gerard@atlantis:~/workspace/exampleweb$ 
```

Esto nos deja con un `.key` y un `.crt` necesarios para el *setup* del SSL de nuestro sitio.

```bash
gerard@atlantis:~/workspace/exampleweb$ ls -1
www.example.com.crt
www.example.com.key
gerard@atlantis:~/workspace/exampleweb$ 
```

```bash
gerard@atlantis:~/workspace/exampleweb$ head -1 www.example.com.*
==> www.example.com.crt <==
-----BEGIN CERTIFICATE-----

==> www.example.com.key <==
-----BEGIN RSA PRIVATE KEY-----
gerard@atlantis:~/workspace/exampleweb$ 
```

**AVISO**: Se ha optado por un fichero `.key` sin *password*, para evitar que nos la pregunte para levantar el **nginx**; otra opción sería crearla con *password* (*flag* `-des3`) y utilizar la directiva `ssl_password_file` de **nginx**.

Como los vamos a utilizar como *secrets*, la posición final de ambos va a ser `/run/secrets/<secret>`, concretamente (y por decisión arbitraria), los pondremos en:

* `/run/secrets/www.example.com.key`
* `/run/secrets/www.example.com.crt`

### Creando algo de contenido

Los *secrets* y *configs* nos permiten "inyectar" ficheros individuales en el sistema de ficheros del contenedor. Esto hace que no sea práctico poner el contenido mediante estos mecanismos y nos invita a distribuir el contenido de una forma más inteligente (por ejemplo copiarlos en la imagen o una hacer una sincronización inicial).

Como no quiero alargar el artículo con complejidades no relacionadas, voy a saltarme mi propio consejo y voy a poner el contenido mediante una *config*, con el entendido que solo va a ser un solo `index.html` de ejemplo, y por eso no va a ser un problema.

```bash
gerard@atlantis:~/workspace/exampleweb$ cat index.html 
<h1>hello ssl</h1>
gerard@atlantis:~/workspace/exampleweb$ 
```

Siguiendo la convención, el contenido va a acabar en `/srv/www/`, que se va a convertir en nuestro *document root*. Esto nos permite demostrar como cambiar el *path* de una *config*.

### Configurando nuestro sitio

Tras haber tomado las decisiones sobre la posición final de nuestros certificados y contenido, podemos generar una configuración para nuestro **nginx**, que no tiene mucha complicación:

```bash
gerard@atlantis:~/workspace/exampleweb$ cat web.conf 
server {
    server_name www.example.com;

    listen 443 ssl;
    ssl_certificate /run/secrets/www.example.com.crt;
    ssl_certificate_key /run/secrets/www.example.com.key;

    root /srv/www;
    index index.html;
    error_page 404 /404.html;

    location /404.html {
        internal;
    }
}
gerard@atlantis:~/workspace/exampleweb$ 
```

Habrá que dejar la configuración en el contenedor de **nginx**; puesto que voy a utilizar [sirrtea/nginx:alpine](https://hub.docker.com/r/sirrtea/nginx), un sitio adecuado para el *virtualhost* es `/etc/nginx/conf.d/`.

### Levantando el stack

Como buena práctica vamos a utilizar un fichero tipo `docker-compose.yml`, que es versionable y nos permite levantar nuestros servicios de forma reproducible:

```bash
gerard@atlantis:~/workspace/exampleweb$ cat web.yml 
version: '3.3'
services:
  web:
    image: sirrtea/nginx:alpine
    ports:
      - "443:443"
    secrets:
      - source: www.example.com.key
        mode: 0400
      - source: www.example.com.crt
        mode: 0400
    configs:
      - source: web.conf
        target: /etc/nginx/conf.d/web.conf
      - source: index.html
        target: /srv/www/index.html
secrets:
  www.example.com.key:
    file: www.example.com.key
  www.example.com.crt:
    file: www.example.com.crt
configs:
  web.conf:
    file: web.conf
  index.html:
    file: index.html
gerard@atlantis:~/workspace/exampleweb$ 
```

Podemos ver en el fichero `web.yml` que hay dos partes diferenciadas:

* Al final del fichero se declaran los *secrets* y *configs*, así como el fichero de los que proceden.
* En los servicios (servicio *web*, en este caso) se declaran los *secrets* y *configs* **que ese servicio va a tener disponibles**, así como detalles más específicos:
    * Cambiamos el *path* de las *configs*, para que la configuración del **nginx** y el contenido vayan a la carpeta que hemos decidido.
    * Cambiamos los permisos de los *secrets* para que solo el usuario los pueda leer (el usuario por defecto es **root**, que es el que los lee: el *master process* de **nginx**).

En cuanto al comando para levantar el *stack*, usamos el de siempre:

```bash
gerard@atlantis:~/workspace/exampleweb$ docker stack deploy -c web.yml web
Creating network web_default
Creating secret web_www.example.com.key
Creating secret web_www.example.com.crt
Creating config web_index.html
Creating config web_web.conf
Creating service web_web
gerard@atlantis:~/workspace/exampleweb$ 
```

Y finalmente nos cargamos los certificados y otros datos, solo para demostrar que los *secrets* y las *configs* "viven" en los metadatos del *cluster*:

```bash
gerard@atlantis:~/workspace$ rm -R exampleweb
gerard@atlantis:~/workspace$ 
```

### Verificando el funcionamiento

Para verificar el funcionamiento solo necesitamos dos cosas:

* Solicitar la página web para ver que el servidor responde.
* Verificar que el contenido es la página de ejemplo usada.
* Inspeccionar el certificado para ver que es el que le hemos puesto.

En ambos casos basta con utilizar un navegador. Como se trata de un puerto expuesto en un *swarm*, podemos ir a dicho puerto de cualquier nodo del *swarm*, por ejemplo a `https://atlantis/`.
