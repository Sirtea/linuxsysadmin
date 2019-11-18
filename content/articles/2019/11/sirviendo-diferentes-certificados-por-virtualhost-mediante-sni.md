---
title: "Sirviendo diferentes certificados por virtualhost mediante SNI"
slug: "sirviendo-diferentes-certificados-por-virtualhost-mediante-sni"
date: "2019-11-18"
categories: ['Sistemas']
tags: ['virtual hosts', 'HTTPS', 'SNI', 'haproxy']
---

Como el número de direcciones IPv4 empieza a escasear, es una práctica habitual
utilizar varios dominios para una misma dirección IP. Con HTTP normal lo llamamos
**virtualhosts** y es relativamente sencillo; la cosa se complica cuando estos
dominios funcionan por HTTPS y hay que servirlos usando certificados distintos.<!--more-->

El protocolo utilizado en estos casos es SNI, que básicamente significa que la
cabecera de la petición viaja sin encriptar. Esto permite que el elemento web
encargado de la terminación SSL sepa el dominio antes de seleccionar el certificado
que debe presentar al que hizo la petición.

**NOTA**: La mayoría de navegadores admiten este protocolo, pero no todos.

Cada servidor web tiene su forma para indicar el certificado de un dominio concreto:

* **Apache** &rarr; Se puede indicar un certificado por *virtualhost*, cada uno con su `ServerName`.
* **Nginx** &rarr; Cada bloque `upstream` (con su `server_name`) admite su propio certificado.
* **HAproxy** &rarr; Los certificados se indican en los bloques `frontend`; hay que dar varios y dejar que **haproxy** elija.

## Un ejemplo con HAproxy

Vamos a crear un ejemplo en el que tenemos dos servidores de *backend*, ambos
por HTTPS; uno sirve una web y el otro sirve una API. Como no queremos alargar
el artículo, voy a poner un servidor **nginx** sirviendo dos webs simples, aunque
el contenido va a indicar si es la web o la API.

### Los servidores web

La configuración de los servidores web puede ser muy simple, ya que no incluye
nada relacionado con SSL (de esto se encargará **haproxy**), y solo nos interesa
servir una web pequeña:

```bash
gerard@atlantis:~/sni_haproxy$ cat conf/www.conf 
server {
	listen 80;
	server_name _;
	root /srv/www;
	index index.html;
}
gerard@atlantis:~/sni_haproxy$ 
```

```bash
gerard@atlantis:~/sni_haproxy$ cat www/index_web.html 
hello web
gerard@atlantis:~/sni_haproxy$ 
```

```bash
gerard@atlantis:~/sni_haproxy$ cat www/index_api.html 
hello api
gerard@atlantis:~/sni_haproxy$ 
```

### La terminación SSL con HAproxy

Delante de estos servidores web, vamos a poner una terminación SSL con **haproxy**.
Para ello vamos a necesitar un certificado para cada dominio, que vamos a crear como
autofirmados por ser un ejemplo rápido.

```bash
gerard@atlantis:~/sni_haproxy$ mkdir certs
gerard@atlantis:~/sni_haproxy$ 
```

```bash
gerard@atlantis:~/sni_haproxy$ openssl req -newkey rsa:2048 -nodes -sha256 -keyout certs/web.local.pem -x509 -days 365 -out certs/web.local.pem -subj '/CN=web.local'
Generating a RSA private key
....................+++++
...................+++++
writing new private key to 'certs/web.local.pem'
-----
gerard@atlantis:~/sni_haproxy$ 
```

```bash
gerard@atlantis:~/sni_haproxy$ openssl req -newkey rsa:2048 -nodes -sha256 -keyout certs/api.local.pem -x509 -days 365 -out certs/api.local.pem -subj '/CN=api.local'
Generating a RSA private key
.................................................+++++
........+++++
writing new private key to 'certs/api.local.pem'
-----
gerard@atlantis:~/sni_haproxy$ 
```

Para especificar varios certificados en un *frontend* se indica en la directiva `bind`,
necesitando solamente indicar varias veces la coletilla `crt <certificado>` tras `ssl`:

```bash
gerard@atlantis:~/sni_haproxy$ cat conf/haproxy.cfg 
global
    chroot /var/lib/haproxy
    user haproxy
    group haproxy
    tune.ssl.default-dh-param 2048

defaults
    mode http
    timeout connect 10s
    timeout client 30s
    timeout server 30s

listen stats
    bind *:8080
    stats enable
    stats uri /

frontend www
    bind *:80
    bind *:443 ssl crt /run/secrets/web.local.pem crt /run/secrets/api.local.pem
    http-request redirect scheme https unless { ssl_fc }
    use_backend web if { hdr(host) -i web.local }
    use_backend api if { hdr(host) -i api.local }

backend web
    server web web:80 check

backend api
    server api api:80 check
gerard@atlantis:~/sni_haproxy$ 
```

### Levantando los servidores

Para los que ya lo sospecharan por la posición de los certificados, vamos a utilizar
**docker** para levantar todos los procesos de forma fácil. El truco reside en
[utilizar configuraciones y secretos][1], tanto para inyectar las configuraciones,
como para los ficheros HTML y los certificados.

No es el objetivo de este artículo centrarnos en la parte de **docker**, así que
solo incluyo la configuración para que no nos falte en un futuro. Por ejemplo podemos
utilizar un *stack* como este:

```bash
gerard@atlantis:~/sni_haproxy$ cat stack.yml 
version: '3.6'
services:
  lb:
    image: sirrtea/haproxy:alpine
    configs:
      - source: haproxy.cfg
        target: /etc/haproxy/haproxy.cfg
    secrets:
      - source: web.local.pem
      - source: api.local.pem
    ports:
      - "80:80"
      - "443:443"
      - "8080:8080"
  web:
    image: sirrtea/nginx:alpine
    configs:
      - source: www.conf
        target: /etc/nginx/conf.d/www.conf
      - source: index_web.html
        target: /srv/www/index.html
  api:
    image: sirrtea/nginx:alpine
    configs:
      - source: www.conf
        target: /etc/nginx/conf.d/www.conf
      - source: index_api.html
        target: /srv/www/index.html
configs:
  haproxy.cfg:
    file: conf/haproxy.cfg
  www.conf:
    file: conf/www.conf
  index_web.html:
    file: www/index_web.html
  index_api.html:
    file: www/index_api.html
secrets:
  web.local.pem:
    file: certs/web.local.pem
  api.local.pem:
    file: certs/api.local.pem
gerard@atlantis:~/sni_haproxy$ 
```

Solo faltaría deplegar el *stack* en nuestro **docker swarm**. Si no diponéis
de un *swarm* a mano, podéis convertir vuestra instalación en uno con el comando
`docker swarm init`; cuando acabemos podéis destruirlo con `docker swarm leave -f`.

```bash
gerard@atlantis:~/sni_haproxy$ docker stack deploy -c stack.yml sni
Creating network sni_default
Creating secret sni_web.local.pem
Creating secret sni_api.local.pem
Creating config sni_www.conf
Creating config sni_index_web.html
Creating config sni_index_api.html
Creating config sni_haproxy.cfg
Creating service sni_web
Creating service sni_api
Creating service sni_lb
gerard@atlantis:~/sni_haproxy$ 
```

Y tras unos segundos necesarios para que se deplieguen los servicios de forma
asíncrona, deberíamos tener todos los contenedores levantados, y listos para hacer
nuestras pruebas. Podéis verificarlo en la página de estado de **haproxy** en
el puerto 8080, que hemos publicado por conveniencia.

### Verificando el funcionamiento

Se puede verificar el funcionamiento con un navegador, pidiendo los dominios
por HTTPS y verificando el certificado de forma manual, suponiendo que tenemos
ya habilitada la resolución DNS de los nombres `web.local` y `api.local`.

Lo cómodo, sin embargo, es utilizar herramientas en el mismo terminal en el que
acabamos de montarlo todo. Para ello necesitamos una herramienta que acepte SNI
para hacer las peticiones de prueba; el mismo **curl** nos sirve para este propósito.

**NOTA**: Como no dispongo de resolución DNS, voy a utilizar el *flag* `--resolve`
como se indica en [este otro artículo][2]. Utilizar solamente la cabecera `Host`
**no funciona**, ya que no activa las funciones SNI de **curl**.

```bash
gerard@atlantis:~/sni_haproxy$ curl -vk --resolve web.local:443:127.0.0.1 https://web.local/
...
* Server certificate:
*  subject: CN=web.local
...
> GET / HTTP/1.1
> Host: web.local
> User-Agent: curl/7.52.1
> Accept: */*
...
hello web
...
gerard@atlantis:~/sni_haproxy$ 
```

```bash
gerard@atlantis:~/sni_haproxy$ curl -vk --resolve api.local:443:127.0.0.1 https://api.local/
...
* Server certificate:
*  subject: CN=api.local
...
> GET / HTTP/1.1
> Host: api.local
> User-Agent: curl/7.52.1
> Accept: */*
...
hello api
...
gerard@atlantis:~/sni_haproxy$ 
```

En ambos casos podemos verificar los 3 puntos clave de la solución:

* Solicitamos el dominio `web.local` (cabecera `Host`)
* El certificado que se nos presenta es el adecuado (*subject* del certificado: `CN=web.local`)
* El contenido servido es el de la web, como vemos en la respuesta

Podemos verificar los 3 puntos adaptados a la petición de `api.local`. De esta
forma, podemos dar por validada la solución propuesta. La parte mala es que añadir
más dominios y certificados va a suponer una larga lista en la directiva `bind`.

[1]: {{< relref "/articles/2019/06/distribuyendo-contenido-en-docker-swarm-configuraciones-y-secretos.md" >}}
[2]: {{< relref "/articles/2017/04/testear-dominios-sin-tener-el-dns-con-curl.md" >}}
