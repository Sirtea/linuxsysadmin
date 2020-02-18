---
title: "Usando un balanceador Nginx en un entorno Docker Swarm"
slug: "usando-un-balanceador-nginx-en-un-entorno-docker-swarm"
date: "2020-02-18"
categories: ['Sistemas']
tags: ['docker', 'swarm', 'nginx', 'balanceador', 'healthcheck', 'https']
---

Cuando trabajamos en un entorno de varias aplicaciones tipo web o API nos solemos
encontrar con la necesidad casi absoluta de poner un balanceador o *proxy reverso*;
a veces es para balancear, otras es para la terminación SSL, y otras es para forzar
la redirección a HTTPS. Para todas ellas nos sirve **nginx**.
<!--more-->

Si tenemos la suerte de poder trabajar en un *cluster* basado en **docker swarm**,
podemos utilizar balanceadores que ya saben que ejecutan en **docker** y pueden
reconfigurarse según sea necesario; de hecho, en este *blog* se ha intentado utilizar
**traefik** en varias ocasiones, como por ejemplo [esta][1], [esta][2] o [esta otra][3].

**Traefik** es una gran herramienta una vez que ha sido configurada, pero su
configuración es un poco difícil, con unas directivas cambiantes entre versiones,
una documentación escasa y una cantidad de despliegues limitada. De hecho, sigo
intentando hacer que [Let’s Encrypt][4] funcione correctamente en el *swarm*.

Al final, siempre me acabo decantando por soluciones más conocidas, siendo **nginx**
mi favorita. Será por su configuración simple, la gran cantidad de recursos *online*
con los que contamos, o simplemente por la gran familiaridad que le tengo; por eso
decidí acabar usándolo en mis entorno *swarm*.

El truco es simple: solo hay que tener en cuenta que la configuración del balanceador
puede cambiar, los certificados también, y que necesitamos tener plena seguridad de
que, en caso de un despliegue, haya alguna de las *replicas* del servicio funcional.
Y todo esto ya lo sabemos hacer:

* Incluir una configuración y certificados, utilizando [configuraciones y secretos][5]
* Evitar tener que destruir el servicio cuando cambie la configuración, mediante las [configuraciones mutables][6]
* Indicamos a **docker** como saber si un contenedor funciona bien con [healthchecks][7]
* Aseguramos que haya siempre un contenedor como mínimo funcionando, usando replicas y orden de *update*

## Unos servicios de test en el *swarm*

Vamos a suponer que tenemos dos aplicaciones web en nuestro *swarm*, que nos van
a servir para ver como configurar los *virtualhosts*, los certificados individuales
y nos servirán para probar que todo funciona como es debido.

**NOTA**: En este punto se asume que el *swarm* cuenta con una red tipo *overlay*,
que llamaremos `frontend`, y que sirve para ser compartida entre el balanceador y
los servicios (así tendrán conectividad de red y se podrán pasar las peticiones).

```bash
gerard@shangrila:~/swarmbalancer$ docker network create -d overlay frontend
iv7yaa90pb755ygbkl1h2yyh0
gerard@shangrila:~/swarmbalancer$ 
```

### Un servicio *whoami*

Ya hemos utilizado esta imagen antes, y no tiene complicación. Se trata de un
servicio web que devuelve el nombre del servidor y sus direcciones IP (en **docker**
las devuelve del contenedor que responda).

El fichero tipo *compose* es relativamente simple, e incluso nos permitimos el
lujo de automatizar el despliegue en un *script* (así evitaremos cambiar el
nombre del *stack*, que puede darnos problemas en el futuro).

```bash
gerard@shangrila:~/swarmbalancer/whoami$ cat whoami.yml 
version: '3'
services:
  whoami:
    image: emilevauge/whoami
    networks:
      - frontend
networks:
  frontend:
    external: true
gerard@shangrila:~/swarmbalancer/whoami$ 
```

```bash
gerard@shangrila:~/swarmbalancer/whoami$ cat deploy.sh 
#!/bin/bash

docker stack deploy -c whoami.yml whoami
gerard@shangrila:~/swarmbalancer/whoami$ 
```

```bash
gerard@shangrila:~/swarmbalancer/whoami$ ./deploy.sh 
Creating service whoami_whoami
gerard@shangrila:~/swarmbalancer/whoami$ 
```

### Un servicio *echo*

Otro servicio muy socorrido para hacer pruebas tipo HTTP es este; simplemente
se limita a respondernos a cualquier petición con un texto especificado. Esto
nos sirve para ver que las peticiones le llegan a través del balanceador.

Siguiendo la anterior metodología, declararemos el servicio en un fichero tipo
*compose*, le daremos un *script* de *deploy* y pondremos el servicio en marcha.

```bash
gerard@shangrila:~/swarmbalancer/echo$ cat echo.yml 
version: '3'
services:
  echo:
    image: hashicorp/http-echo
    command: -text="hello world"
    networks:
      - frontend
networks:
  frontend:
    external: true
gerard@shangrila:~/swarmbalancer/echo$ 
```

```bash
gerard@shangrila:~/swarmbalancer/echo$ cat deploy.sh 
#!/bin/bash

docker stack deploy -c echo.yml echo
gerard@shangrila:~/swarmbalancer/echo$ 
```

```bash
gerard@shangrila:~/swarmbalancer/echo$ ./deploy.sh 
Creating service echo_echo
gerard@shangrila:~/swarmbalancer/echo$ 
```

## El balanceador nginx

**ESTADO**: En este momento tenemos una red *overlay* llamada `frontend`, en la
que tenemos dos servicios ejecutando: el servicio *whoami* (puerto TCP 80) y el
servicio *echo* (puerto TCP 5678).

Vamos a exponer un servicio **nginx** en el *swarm*, pero también en la red
`frontend`. De esta forma podremos lanzar las peticiones que correspondan desde
cualquier nodo del *swarm*, y a su vez, pasarlas al servicio adecuado. Por
supuesto, vamos a utilizar SSL para los mismos y vamos a forzar las peticiones
HTTP a ir por las equivalentes en HTTPS.

Vamos a utilizar un sistema similar a los anteriores: un fichero tipo *compose*
para declarar el *stack*, y un *script* de deploy (en donde calcularemos las sumas
MD5 de los ficheros auxiliares, como se explica [aquí][6]); sobre esta base solo
nos quedará añadir la configuración del **nginx** y los certificados de los
servicios que queramos proteger.

### Los certificados SSL

Los certificados SSL se generan aparte del propio *swarm*; podemos generar
certificados autofirmados, pagar por unos certificados válidos, o utilizar una
aproximación como la que explicamos en [este artículo][8]. Para acortar, voy
a poner unos certificados autofirmados.

El servidor **nginx** nos permite trabajar con los certificados en 2 ficheros
(clave y certificado), o especificar un único fichero que los contenga a ambos
en las dos directivas relacionadas. Voy a optar por esta opción para reducir
la cantidad de secretos en el fichero *compose* resultante.

```bash
gerard@shangrila:~/swarmbalancer/balancer$ grep ^ certs/*
certs/echo.local.pem:-----BEGIN RSA PRIVATE KEY-----
...
certs/echo.local.pem:-----END RSA PRIVATE KEY-----
certs/echo.local.pem:-----BEGIN CERTIFICATE-----
...
certs/echo.local.pem:-----END CERTIFICATE-----
certs/whoami.local.pem:-----BEGIN RSA PRIVATE KEY-----
...
certs/whoami.local.pem:-----END RSA PRIVATE KEY-----
certs/whoami.local.pem:-----BEGIN CERTIFICATE-----
...
certs/whoami.local.pem:-----END CERTIFICATE-----
gerard@shangrila:~/swarmbalancer/balancer$ 
```

### La configuración del nginx

Para configurar el **nginx** vamos a definir 3 *virtualhosts*:

* Uno para las peticiones que lleguen por HTTP, que redigiremos a HTTPS
* Uno para las peticiones HTTPS, con sus certificados SSL
* Uno para exponer el módulo *stub status*, que nos servirá a modo de *healthcheck*

Esta configuración quedará así:

```bash
gerard@shangrila:~/swarmbalancer/balancer$ cat conf/balancer.conf 
resolver 127.0.0.11 valid=5s;

map $ssl_server_name $docker_service {
	whoami.local whoami_whoami:80;
	echo.local echo_echo:5678;
}

server {
	listen 8080;
	stub_status;
}

server {
	listen 80;
	return 308 https://$host$request_uri;
}

server {
	listen 443 ssl;
	ssl_certificate_key /run/secrets/$ssl_server_name.pem;
	ssl_certificate /run/secrets/$ssl_server_name.pem;
	location / { proxy_pass http://$docker_service; }
}
gerard@shangrila:~/swarmbalancer/balancer$ 
```

Hay que tener en cuenta algunos puntos para entender esta configuración:

* El *virtualhost* en el puerto 8080 sirve de *healthcheck*
    * Su información es poco útil, pero si responde, es que el **nginx** se ha levantado
    * No vamos a publicar este puerto fuera del contenedor, pero se usará en el *healthcheck*
* El *virtualhost* en el puerto 80 es el de HTTP
    * Esperamos que redirija todo el tráfico a su equivalente HTTPS
    * Será una redirección 308 (no 301); esto es porque esperamos recibir peticiones de API y el 308 respeta el verbo HTTP (POST, ...)
* El *virtualhost* en el puerto 443 es el de HTTPS
    * Esperamos que los certificados estén en `/run/secrets/<dominio>.pem`, sino dará un error
    * Pasaremos la petición al servicio `$docker_service`
        * Esta variable se calcula con el `map` de `$ssl_server_name` y `$docker_service`
            * `ssl_server_name = whoami.local` &rarr; `$docker_service = whoami_whoami:80`
            * `ssl_server_name = echo.local` &rarr; `$docker_service = echo_echo:5678`
        * La directiva `resolver` sirve para indicar el DNS del contenedor, de donde obtendremos la VIP del servicio
        * La VIP del servicio es un balanceador entre todos los contenedores saludables del servicio

**TRUCO**: Todo contenedor en un *swarm* tiene un servidor DNS expuesto que sabe
resolver los servicios que estén en sus mismas redes, así como de otros dominios;
lo encontraremos en la IP 127.0.0.11 (esto no cambia nunca).

**WARNING**: Esta configuración es muy genérica, pero la petición fallará si llega
una petición que no sea para `whoami.local` o `echo.local`. Si váis a poner más
servicios, apuntad el registro DNS hacia el *swarm* cuando ya tengamos la configuración
activa y los certificados en su sitio.

### El *stack* y su *deploy*

Vamos a hacer un *stack* relativamente simple; es un **nginx** genérico con una
configuración propia y unos certificados puestos como secretos. La única complicación
es que vamos a utilizar [este método][6] (concretamente con sumas MD5) para poder
modificar la configuración y los certificados y no recibir un error durante el
subsiguiente *redeploy*.

Las otras dos curiosidades son el *healthcheck* y los parámetros de *deploy*;
gracias al *healthcheck* podemos dar a conocer a **docker** si el contenedor está
respondiendo (no vale con levantado solamente), y gracias al *deploy* tendremos 4
contenedores funcionando y los reemplazaremos de 1 en 1 (momento en el que podremos
tener 5 en marcha, hasta que este dé *healthcheck* correcto y se pueda reemplazar
uno de los antiguos).

```bash
gerard@shangrila:~/swarmbalancer/balancer$ cat balancer.yml 
version: '3.5'
services:
  nginx:
    image: sirrtea/nginx:alpine
    configs:
      - source: balancer.conf
        target: /etc/nginx/conf.d/balancer.conf
    secrets:
      - source: whoami.local.pem
      - source: echo.local.pem
    networks:
      - frontend
    deploy:
      replicas: 4
      update_config:
        parallelism: 1
        order: start-first
    healthcheck:
      test: ["CMD", "wget", "--spider", "-q", "http://localhost:8080/"]
      interval: 5s
      timeout: 3s
      retries: 3
      start_period: 10s
    ports:
      - "80:80"
      - "443:443"
configs:
  balancer.conf:
    name: balancer_balancer.conf-${BALANCER_CONF_DIGEST}
    file: conf/balancer.conf
secrets:
  whoami.local.pem:
    name: balancer_whoami.local.pem-${WHOAMI_LOCAL_PEM_DIGEST}
    file: certs/whoami.local.pem
  echo.local.pem:
    name: balancer_echo.local.pem-${ECHO_LOCAL_PEM_DIGEST}
    file: certs/echo.local.pem
networks:
  frontend:
    external: true
gerard@shangrila:~/swarmbalancer/balancer$ 
```

```bash
gerard@shangrila:~/swarmbalancer/balancer$ cat deploy.sh 
#!/bin/bash

function md5 { md5sum ${1} | cut -b 1-32; }

export BALANCER_CONF_DIGEST=$(md5 conf/balancer.conf)
export WHOAMI_LOCAL_PEM_DIGEST=$(md5 certs/whoami.local.pem)
export ECHO_LOCAL_PEM_DIGEST=$(md5 certs/echo.local.pem)

docker stack deploy -c balancer.yml balancer
gerard@shangrila:~/swarmbalancer/balancer$ 
```

Levantamos el *stack* de balanceador y esperamos a que sus servicios estén funcionando.
Futuros *deploys* deberían hacerse sin *downtime*, reemplazándose los contenedores 1 a 1
según las políticas declaradas. Esto nos permite cambiar las configuraciones y los
certificados sin parada, de forma gradual.

```bash
gerard@shangrila:~/swarmbalancer/balancer$ ./deploy.sh 
Creating secret balancer_echo.local.pem-7fefb7759833a6a0fedd1208b724a065
Creating secret balancer_whoami.local.pem-3f3abec4ba2f29adc60c691f858c8f7f
Creating config balancer_balancer.conf-38919a938105c010a25ca26b7bfc823e
Creating service balancer_nginx
gerard@shangrila:~/swarmbalancer/balancer$ 
```

**TRUCO**: La VIP del servicio solo va a balancear las peticiones al **nginx** entre
los contenedores que pasen el *healthcheck*, así que deberíamos tener respuesta desde
el primer contenedor levantado, y nunca desde un **nginx** que se esté levantando
(su *healthcheck* fallará hasta que esté listo para recibir peticiones).

## Comprobaciones

Lo primero es ver que nuestros **nginx** están ejecutando y en estado *healthy*;
podemos verificarlo con un `docker ps` o revisar que hay las replicas necesarias
en el servicio (en este caso 4/4).

```bash
gerard@shangrila:~/swarmbalancer$ docker service ls
ID                  NAME                MODE                REPLICAS            IMAGE                        PORTS
wq4cr5ya4air        balancer_nginx      replicated          4/4                 sirrtea/nginx:alpine         *:80->80/tcp, *:443->443/tcp
u6cc79nd8nc8        echo_echo           replicated          1/1                 hashicorp/http-echo:latest   
0dz5ad69e55h        whoami_whoami       replicated          1/1                 emilevauge/whoami:latest     
gerard@shangrila:~/swarmbalancer$ 
```

Solo nos queda ver que el comportamiento de la configuración del **nginx**:

* Redirige las peticiones HTTP de cada *virtualhost* a su HTTPS correspondiente
* Las peticiones HTTPS responden por virtualhost y con sus respectivos certificados

Todas ellas son verificables con simples peticiones usando `curl`. Voy a poner
la salida de los dos servicios configurados para probar, y un dominio no configurado
para poder ver el error que nos daría un posible despiste.

### Peticiones HTTP

```bash
gerard@shangrila:~/swarmbalancer$ curl -i http://whoami.local/
HTTP/1.1 308 Permanent Redirect
...
Location: https://whoami.local/
...
gerard@shangrila:~/swarmbalancer$ 
```

```bash
gerard@shangrila:~/swarmbalancer$ curl -i http://echo.local/
HTTP/1.1 308 Permanent Redirect
...
Location: https://echo.local/
...
gerard@shangrila:~/swarmbalancer$ 
```

```bash
gerard@shangrila:~/swarmbalancer$ curl -i http://server.local/
HTTP/1.1 308 Permanent Redirect
...
Location: https://server.local/
...
gerard@shangrila:~/swarmbalancer$ 
```

### Peticiones HTTPS

**NOTA**: Añado el *flag* `-k` porque el certificado es autofirmado y falla verificación.

```bash
gerard@shangrila:~/swarmbalancer$ curl -k https://whoami.local/
Hostname: a1370d06574a
IP: 127.0.0.1
IP: 10.0.0.3
IP: 172.17.0.3
GET / HTTP/1.1
Host: whoami_whoami
User-Agent: curl/7.52.1
Accept: */*
Connection: close

gerard@shangrila:~/swarmbalancer$ 
```

```bash
gerard@shangrila:~/swarmbalancer$ curl -k https://echo.local/
hello world
gerard@shangrila:~/swarmbalancer$ 
```

```bash
gerard@shangrila:~/swarmbalancer$ curl -k https://server.local/
curl: (35) error:14077438:SSL routines:SSL23_GET_SERVER_HELLO:tlsv1 alert internal error
gerard@shangrila:~/swarmbalancer$ 
```

Este último caso era esperable, porque el servicio no está configurado; de hecho,
no llega siquiera a intentar pasar la petición a nadie, porque el error salta antes,
concretamente cuando intenta obtener el certificado SSL, que debería estar en el
fichero `/run/secrets/server.local.pem` (y no está):

```bash
gerard@shangrila:~/swarmbalancer$ docker service logs balancer_nginx
...
balancer_nginx.2.ezfu64cjr1dw@shangrila    | 2020/01/14 11:39:37 [error] 6#6: *130 cannot load certificate "/run/secrets/server.local.pem": BIO_new_file() failed (SSL: error:02001002:system library:fopen:No such file or directory:fopen('/run/secrets/server.local.pem','r') error:2006D080:BIO routines:BIO_new_file:no such file) while SSL handshaking, client: 10.255.0.2, server: 0.0.0.0:443
...
gerard@shangrila:~/swarmbalancer$ 
```

Solo nos quedaría que las peticiones llegaran desde fuera del *swarm* a cualquier
nodo del mismo; este sabría enrutar la peticiones a alguno de los 4 contenedores
**nginx**. De hecho, podemos asegurar alta disponibilidad del servicio si balanceamos
las peticiones entre los nodos saludables del *swarm*, o compartiendo una VIP con
*keepalived* entre algunos de los nodos del *swarm*.

[1]: {{< relref "/articles/2018/09/un-balanceador-dinamico-para-docker-traefik.md" >}}
[2]: {{< relref "/articles/2018/10/usando-traefik-en-un-cluster-de-docker-swarm.md" >}}
[3]: {{< relref "/articles/2019/10/un-entorno-productivo-basado-en-docker-swarm-4.md" >}}
[4]: https://letsencrypt.org/es/
[5]: {{< relref "/articles/2019/06/distribuyendo-contenido-en-docker-swarm-configuraciones-y-secretos.md" >}}
[6]: {{< relref "/articles/2019/12/modificando-secretos-y-configuraciones-en-servicios-de-docker-swarm.md" >}}
[7]: {{< relref "/articles/2019/06/verificando-la-salud-de-nuestros-contenedores-en-docker.md" >}}
[8]: {{< relref "/articles/2019/11/con-confianza-una-autoridad-certificadora-propia.md" >}}
