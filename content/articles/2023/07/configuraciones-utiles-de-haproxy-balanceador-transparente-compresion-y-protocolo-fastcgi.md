---
title: "Configuraciones útiles de HAProxy: balanceador transparente, compresión y protocolo FastCGI"
slug: "configuraciones-utiles-de-haproxy-balanceador-transparente-compresion-y-protocolo-fastcgi"
date: "2023-07-24"
categories: ['Sistemas']
tags: ['haproxy', 'balanceador', 'transparente', 'compresión', 'php', 'php-fpm']
---

Cada vez que trabajo con HAProxy me gusta más, y es que si tienes la documentación a mano, verás
que las posibilidades son infinitas. Para no ir perdiendo estas configuraciones, las estoy poniendo
en artículos en este blog; espero que me sean útiles en un futuro no muy lejano.<!--more-->


## Balanceador transparente

Poner balanceadores o *proxies* delante de nuestros servidores de aplicaciones nos ofrece un sinfín
de posibilidades en cuanto a seguridad y escalabilidad. Sin embargo, no están exentos de problemas;
las peticiones que se reciben en el servidor de aplicaciones se ven como si vinieran del balanceador,
y esto puede provocar algunos problemas en la aplicación.

Los dos problemas más frecuentes suelen darse en la generación de nuevas URLs al crear redirecciones,
y en bucles de redirección HTTP/HTTPS cuando la aplicación así lo fuerza. Por suerte, la mayoría de
aplicaciones o *frameworks* respetan el estándar definido y pueden deducir los parámetros relevantes
de cabeceras HTTP extras.

Las cabeceras que podemos definir -sacándolas de la petición original- son las siguientes:

* **X-Forwarded-For** &rarr; Contiene la lista de IPs por las que la petición ha pasado; de ahí se puede deducir la IP origen de la petición original contra el balanceador.
* **X-Forwarded-Port** &rarr; Contiene el puerto original al que se hizo la petición contra el balanceador.
* **X-Forwarded-Proto** &rarr; Suele indicarse "https" en el caso de que la petición original se hiciera usando ese protocolo, y le sirve a la aplicación para no forzar otra redirección a HTTPS.

Indicar estas tres cabeceras no tiene ningún misterio en HAProxy: basta con indicar en un *frontend*
o en un *backend* una configuración como la que sigue:

```bash
frontend web
        bind :80
        bind :443 ssl crt /etc/haproxy/certs/
        http-request redirect scheme https unless { ssl_fc }
        option forwardfor
        http-request set-header X-Forwarded-Port %[dst_port]
        http-request add-header X-Forwarded-Proto https if { ssl_fc }
        default_backend myapp

backend myapp
        server myapp 127.0.0.1:8080 check
```

**NOTA**: Cabe indicar que el *frontend* "web" puede atender peticiones en ambos protocolos (aunque
en este caso hace una redirección...). En este caso indicamos el protocolo solamente en el caso de
HTTPS, utilizando la función `ssl_fc`.

## Compresión de respuestas

Tenemos un sistema que responde por HTTP(S). No es importante si se trata de páginas web estáticas,
dinámicas o respuestas de una API. Estas respuestas pueden ser bastante largas y nos puede interesar
utilizar un poco de CPU en el balanceador para comprimirlas, quitando presión a la red.

Como este tipo de respuestas suelen comprimir bien, muchos sistemas ya hacen esto por defecto. Si
no es el caso, podemos instruir a **HAProxy** para que se encargue de eso, con una configuración
bastante sencilla.

Vamos a suponer que tenemos un sistema por HTTP que nos da páginas web. Lo simularemos con un
servidor **Nginx** local y una página de contenido irrelevante:

```bash
gerard@server:~$ sudo apt update && sudo apt install nginx-light
...
gerard@server:~$
```

```bash
gerard@server:~$ cat /etc/nginx/sites-enabled/*
server {
        listen 127.0.0.1:8080;
        root /srv/www;
        index index.html;
        gzip off;

        location / {
                try_files $uri $uri/ =404;
        }
}
gerard@server:~$
```

```bash
gerard@server:~$ ls /srv/www/
index.html
gerard@server:~$
```

```bash
gerard@server:/srv/www$ sudo systemctl reload nginx
gerard@server:/srv/www$
```

**NOTA**: Es importante deshabilitar la compresión de **Nginx** explícitamente con la directiva
`gzip off`, puesto que viene habilitada en `/etc/nginx/nginx.conf` en la mayoría de distribuciones
**Linux**. Para este artículo concreto y por un tema puramente académico, nos interesa que la
compresión la haga el **HAProxy**.

El siguiente paso es tener un **HAProxy** instalado y listo para darnos las respuestas del servidor web.

```bash
gerard@server:~$ sudo apt update && sudo apt install haproxy
...
gerard@server:~$
```

Para ver las diferencias, vamos a crear dos puertos en el balanceador; se comportan igual, pero vamos
a poner compresión en uno de ellos, y en el otro no. No hay que olvidar de aplicar la nueva configuración.

```bash
gerard@server:~$ cat /etc/haproxy/haproxy.cfg
...
listen web-plain
        bind :8001
        server nginx 127.0.0.1:8080 check

listen web-gzip
        bind :8002
        compression algo gzip
        compression type text/html
        server nginx 127.0.0.1:8080 check
gerard@server:~$
```

```bash
gerard@server:~$ sudo systemctl reload haproxy
gerard@server:~$
```

**NOTA**: Esta configuración solamente aplicaría compresión en los ficheros tipo "text/html".
Con un poco más de trabajo podemos comprimir CSS, Javascript, APIs o texto plano; comprimir
imágenes, vídeos y sonido no suele valer la pena.

Vamos a hacer una petición a cada puerto; es importante indicar que aceptamos respuestas en
formato **gzip**, con la cabecera `Accept-Encoding: gzip` en el caso de utilizar **curl**.

```bash
gerard@client:~$ curl -H "Accept-Encoding: gzip" http://server:8001/ >/dev/null
  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
100  2873  100  2873    0     0   561k      0 --:--:-- --:--:-- --:--:--  561k
gerard@client:~$
```

```bash
gerard@client:~$ curl -H "Accept-Encoding: gzip" http://server:8002/ >/dev/null
  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
100  1744    0  1744    0     0   283k      0 --:--:-- --:--:-- --:--:--  340k
gerard@client:~$
```

En el primer caso, vamos a ver un tamaño descargado (columna "Total") de 2873 bytes, que es el
tamaño original del fichero HTML. En el segundo (que es el puerto que aplica la compresión)
recibimos solamente 1744 bytes, que asumo que es el tamaño comprimido.

## Protocolo FastCGI

Muchos de nosotros servimos PHP utilizando **php-fpm** detrás de un **nginx**. Este **nginx**
se encarga de la traducción de protocolo de HTTP a FastCGI, más otras funciones que se puedan
necesitar (*virtualhosts*, terminación SSL...).

La verdad es que podemos reemplazar el **nginx** por un **haproxy**. Las últimas modificaciones
nos permiten directamente definir *backends* que usan el protocolo FastCGI.

Solo necesitamos declarar dos bloques nuevos: el `fastcgi-app` que nos permite definir los
parámetros, y declarar el protocolo `fcgi` en los diferentes servidores de *backend*.

```bash
gerard@balancer:~$ diff /etc/haproxy/haproxy.cfg{,.orig}
35,48d34
<
< frontend www
<     bind :8080
<     default_backend php
<
< backend php
<     use-fcgi-app php
<     server php01 127.0.0.1:9000 proto fcgi
<
< fcgi-app php
<     log-stderr global
<     docroot /
<     index index.php
<     path-info ^(/.+\.php)(/.*)?$
gerard@balancer:~$
```

En este caso, declaramos que el *path* en donde encontraremos los ficheros PHP es en `/`, del
servidor php01. Como esto va cambiando de servidor en servidor, he decidido enjaular el proceso
**php-fpm** para estandarizar el *path* y poder reutilizar el bloque `fcgi-app` entre varios *backend*.

Para conseguir esto, necesitamos modificar la configuración del proceso **fpm** para cumplir
dos cosas: el enjaulado y escuchar en un puerto TCP.

```bash
gerard@balancer:~$ diff /etc/php/8.2/fpm/pool.d/www.conf{,.orig}
41c41
< listen = 127.0.0.1:9000
---
> listen = /run/php/php8.2-fpm.sock
420c420
< chroot = /srv/www
---
> ;chroot =
gerard@balancer:~$
```

Si ejecutamos varios *pools* de **php-fpm** en la misma máquina, quedamos afectados por el
*bug* [siguiente][1], lo que nos obliga a poner otra cosa:

```bash
gerard@balancer:~$ diff /etc/php/8.2/fpm/php.ini{,.orig}
1922c1922
< opcache.validate_root=1
---
> ;opcache.validate_root=0
gerard@balancer:~$
```

Aplicamos ambas configuraciones y ya tenemos nuestro combo **haproxy**/**php-fpm** funcionando:

```bash
gerard@balancer:~$ sudo systemctl restart php8.2-fpm
gerard@balancer:~$
```

```bash
gerard@balancer:~$ sudo systemctl reload haproxy
gerard@balancer:~$
```

Solo nos faltaría lanzar algunas peticiones al balanceador para ver que todo funciona según lo esperado:

```bash
gerard@balancer:~$ curl -s http://localhost:8080/
hello world
gerard@balancer:~$
```

```bash
gerard@balancer:~$ curl -s http://localhost:8080/info.php | grep phpinfo
<title>PHP 8.2.7 - phpinfo()</title><meta name="ROBOTS" content="NOINDEX,NOFOLLOW,NOARCHIVE" /></head>
gerard@balancer:~$
```

**NOTA**: El balanceador **haproxy** es incapaz de servir contenido estático; esto limita la
efectividad de esta solución a aplicaciones que solo ejecutan PHP puro. Eso nos limita a APIs,
pero nos elimina la posibilidad de servir una web tradicional.

[1]: https://regilero.github.io/english/drupal/2013/05/16/Warning_chrooted_php_fpm_and_apc/
