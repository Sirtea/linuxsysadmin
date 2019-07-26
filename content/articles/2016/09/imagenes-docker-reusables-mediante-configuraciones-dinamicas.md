---
title: "Imágenes docker reusables mediante configuraciones dinámicas"
slug: "imagenes-docker-reusables-mediante-configuraciones-dinamicas"
date: 2016-09-12
categories: ['Operaciones']
tags: ['docker', '12factor', 'configuración', 'templating']
---

Muchos de los servicios que necesitamos son siempre los mismos, cambiando solamente algunos parámetros. Incluso los mismos servicios pueden sufrir variaciones en su configuración, por ejemplo, un balanceador al que se añaden o quitan *hosts*. Siguiendo las prácticas de [12factor](http://12factor.net/es/) podemos ahorrar trabajo, mediante el uso de variables de entorno.<!--more-->

El problema es que las variables de entorno no siempre son bienvenidas en las configuraciones de una aplicación, siendo mucho mas comunes los ficheros con un formato concreto. Eso significa que necesitamos varias imágenes **docker** para los diferentes proyectos y entornos.

Harto de escribir configuraciones **nginx** y reconstruir la imagen cada vez que añadíamos *hosts*, me hice la pregunta: ¿Hay alguna forma mas inteligente de hacer esto?

La única forma de cambiar el contenido de una imagen **docker** es mapeando las configuraciones en volúmenes o mediante el uso de variables de entorno. Pero **nginx** no admite variables de entorno, y lo de los volúmenes me parece una chapuza.

La solución es tan simple como efectiva: generar las configuraciones estáticas de forma dinámica. La idea es pasar las variables de entorno al contenedor, y que antes de ejecutar su servicio, genere la configuración a partir de las variables recibidas. Un ejercicio de *templating* básico.

## Un ejemplo: un balanceador con nginx con backends variables.

El esquema de un balanceador en **nginx** sigue siempre el mismo patrón:

```nginx
upstream backend {
	...
}

server {
	listen 80;
	server_name _;

	location / {
		proxy_pass http://backend;
	}
}
```

El truco consiste en que el contenedor va a ejecutar un *script* que va a generar la configuración y va a lanzar nuestro binario. Para hacerlo limpiamente, vamos a separar la ejecución, del *script* de generación.

```bash
gerard@sirius:~/docker/dynamic_configs$ cat entrypoint.sh 
#!/bin/sh

./config.sh > /etc/nginx/conf.d/balancer
exec /usr/sbin/nginx -g "daemon off;"
gerard@sirius:~/docker/dynamic_configs$ 
```

Y el *script* de generación solo tiene la responsabilidad de leer las variables de entorno y sacar la configuración por pantalla. Por simplicidad, estoy usando un *script* en **bash**, pero se podría hacer con otro lenguaje e incluso con un motor de plantillas. Me gusta especialmente la combinación **python** + **jinja2**.

```bash
gerard@sirius:~/docker/dynamic_configs$ cat config.sh 
#!/bin/sh

echo "upstream backend {"
for BACKEND in $(echo ${BACKENDS} | sed 's/,/ /g'); do
echo "	server $BACKEND;"
done
echo """\
}

server {
	listen 80;
	server_name _;

	location / {
		proxy_pass http://backend;
	}
}
"""
gerard@sirius:~/docker/dynamic_configs$ 
```

Podemos comprobar que la configuración generada depende de la variable de entorno *BACKENDS*, por ejemplo, con dos nodos.

```bash
gerard@sirius:~/docker/dynamic_configs$ BACKENDS=server1:8080,server2:8080 ./config.sh 
upstream backend {
	server server1:8080;
	server server2:8080;
}

server {
	listen 80;
	server_name _;

	location / {
		proxy_pass http://backend;
	}
}

gerard@sirius:~/docker/dynamic_configs$ 
```

El *script* *entrypoint.sh* llamará este otro *script* y va a salvar esta configuración en algún sitio que **nginx** pueda cargar, por ejemplo, en una carpeta incluida en la configuración principal.

```bash
gerard@sirius:~/docker/dynamic_configs$ cat nginx.conf 
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
gerard@sirius:~/docker/dynamic_configs$ 
```

Finalmente, solo nos queda poner todas las piezas en su sitio, mediante el *Dockerfile* correspondiente:

```bash
gerard@sirius:~/docker/dynamic_configs$ cat Dockerfile 
FROM alpine:3.4
RUN apk add --no-cache nginx && \
    ln -s /dev/stdout /var/log/nginx/access.log && \
    ln -s /dev/stderr /var/log/nginx/error.log && \
    mkdir /run/nginx
COPY nginx.conf /etc/nginx/
COPY config.sh entrypoint.sh /
ENTRYPOINT ["/entrypoint.sh"]
gerard@sirius:~/docker/dynamic_configs$ 
```

Y finalmente podemos crear un balanceador indicando simplemente los parámetros en el *docker run*, previo *docker build*.

```bash
gerard@sirius:~/docker/dynamic_configs$ docker run -ti --rm -e "BACKENDS=server1:8080,server2:8080,server3:8080" balancer
...  
```
