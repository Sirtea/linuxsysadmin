Title: Desactivando nuestras APIs con un frontal nginx
Slug: desactivando-nuestras-apis-con-un-frontal-nginx
Date: 2017-07-10 10:00
Category: Sistemas
Tags: api, gateway, proxy, nginx



El otro día recibí una petición algo atípica en mi trabajo: querían activar y desactivar en un único punto centralizado cada una de las varias APIs que tenemos. Se trata de poner un **nginx** frontal que gestione los *virtualhosts* existentes y haga *proxy_pass* o no en función de un *flag*.

La propuesta me pareció bastante interesante, así que decidí hacer una prueba de concepto que aquí queda reflejada. Se trata de ofrecer un frontal web (por ejemplo un **jenkins**) mediante el cual se puedan poner los ficheros cuya presencia le indican a **nginx** si ese *virtualhost* concreto debe dar un error o no.

## Simulando las APIs

Vamos a poner un par de contenedores **docker** con **nginx**, que sirvan una página personalizada y nos sirva para simular la API. No es especialmente complejo, así que solo se adjunta por completitud.

el único punto interesante es que, para no repetirnos, vamos a pasar el contenido del fichero *index.html* como una variable de entorno. Así no hay que construir varias imágenes.

Empezamos con un *Dockerfile*.

```bash
gerard@aldebaran:~/docker/gw-poc$ cat api/Dockerfile 
FROM alpine:3.5
RUN apk add --no-cache nginx && \
    ln -s /dev/stdout /var/log/nginx/access.log && \
    ln -s /dev/stderr /var/log/nginx/error.log && \
    mkdir /run/nginx && \
    mkdir /srv/www && \
    rm /etc/nginx/conf.d/default.conf
COPY nginx.conf /etc/nginx/
COPY conf.d/* /etc/nginx/conf.d/
COPY start.sh /
CMD ["/start.sh"]
gerard@aldebaran:~/docker/gw-poc$ 
```

Y lo acompañamos con sus ficheros auxiliares.

```bash
gerard@aldebaran:~/docker/gw-poc$ cat api/nginx.conf 
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
gerard@aldebaran:~/docker/gw-poc$ cat api/conf.d/api 
server {
	server_name _;
	listen 80;
	root /srv/www;
	index index.html;
}
gerard@aldebaran:~/docker/gw-poc$ cat api/start.sh 
#!/bin/sh

echo ${GREETING} > /srv/www/index.html
exec /usr/sbin/nginx -g "daemon off;"
gerard@aldebaran:~/docker/gw-poc$ 
```

Y con esto tenemos nuestra imagen lista para ser construida.

```bash
gerard@aldebaran:~/docker/gw-poc$ dbuild -t api api/
Sending build context to Docker daemon 5.632 kB
...  
Successfully built c91adbf6534e
gerard@aldebaran:~/docker/gw-poc$ 
```

## Creando un proxy como fachada

Esta es la piedra angular de la solución. Vamos a empezar con un **nginx**, pero la novedad es que cada *virtualhost* va a incluir una condición nueva: si existe un fichero con el mismo nombre que el dominio en la carpeta raíz (la misma para todos los dominios vale), devolveremos un error 503 en JSON sin pasar la petición a nuestro *backend*.

```bash
gerard@aldebaran:~/docker/gw-poc$ cat gw/Dockerfile 
FROM alpine:3.5
RUN apk add --no-cache nginx && \
    ln -s /dev/stdout /var/log/nginx/access.log && \
    ln -s /dev/stderr /var/log/nginx/error.log && \
    mkdir /run/nginx && \
    mkdir /srv/www && \
    rm /etc/nginx/conf.d/default.conf
COPY nginx.conf /etc/nginx/
COPY conf.d/* /etc/nginx/conf.d/
COPY start.sh /
CMD ["/start.sh"]
gerard@aldebaran:~/docker/gw-poc$ 
```

Y también ponemos las configuraciones necesarias para dos APIs de *backend*, que nos basta para ver si funciona.

```bash
gerard@aldebaran:~/docker/gw-poc$ cat gw/nginx.conf 
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
gerard@aldebaran:~/docker/gw-poc$ cat gw/conf.d/api1 
server {
	server_name api1;
	listen 80;
	root /srv/www;

	location / {
		if (-f $document_root/$host) { return 503; }
		proxy_pass http://api1:80;
	}

	error_page 503 @maintenance;

	location @maintenance {
		default_type application/json;
		return 503 '{"message":"Sorry you! This entity (api1) is in maintenance mode"}';
	}
}
gerard@aldebaran:~/docker/gw-poc$ cat gw/conf.d/api2 
server {
	server_name api2;
	listen 80;
	root /srv/www;

	location / {
		if (-f $document_root/$host) { return 503; }
		proxy_pass http://api2:80;
	}

	error_page 503 @maintenance;

	location @maintenance {
		default_type application/json;
		return 503 '{"message":"Sorry you! This entity (api2) is in maintenance mode"}';
	}
}
gerard@aldebaran:~/docker/gw-poc$ cat gw/start.sh 
#!/bin/sh

exec /usr/sbin/nginx -g "daemon off;"
gerard@aldebaran:~/docker/gw-poc$ 
```

Y construimos la imagen.

```bash
gerard@aldebaran:~/docker/gw-poc$ dbuild -t gw gw/
Sending build context to Docker daemon 6.656 kB
...
Successfully built ddf3f294c99c
gerard@aldebaran:~/docker/gw-poc$ 
```
## Ponemos todo junto

El último paso es montar un entorno que nos permita lanzar pruebas y ver que funciona. Para ello, vamos a usar **docker-compose** por la comodidad que supone.

```bash
gerard@aldebaran:~/docker/gw-poc$ cat docker-compose.yml 
version: '2'
services:
  gw:
    image: gw
    container_name: gw
    hostname: gw
    volumes:
      - ./volume:/srv/www
    ports:
      - "80:80"
    depends_on:
      - api1
      - api2
  api1:
    image: api
    container_name: api1
    hostname: api1
    environment:
      GREETING: "Hello from api1"
  api2:
    image: api
    container_name: api2
    hostname: api2
    environment:
      GREETING: "Bye from api2"
gerard@aldebaran:~/docker/gw-poc$ 
```

Levantamos el entorno entero con los comandos habituales:

```bash
gerard@aldebaran:~/docker/gw-poc$ docker-compose up -d
Creating network "gwpoc_default" with the default driver
Creating api1
Creating api2
Creating gw
gerard@aldebaran:~/docker/gw-poc$ 
```

Tras levantar el entorno, podemos hacer algunas peticiones, tanto a los contenedores que sirven la API, como al *gateway* que las engloba.

```bash
gerard@aldebaran:~/docker/gw-poc$ curl http://172.18.0.2/
Hello from api1
gerard@aldebaran:~/docker/gw-poc$ curl http://172.18.0.3/
Bye from api2
gerard@aldebaran:~/docker/gw-poc$ curl -H "Host: api1" http://localhost/
Hello from api1
gerard@aldebaran:~/docker/gw-poc$ curl -H "Host: api2" http://localhost/
Bye from api2
gerard@aldebaran:~/docker/gw-poc$ 
```

Y ahora solo nos falta la magia: tiramos un fichero en */srv/www/*, cómodamente mapeados como un *host volume* en la carpeta *volume/*. Un fichero con el nombre del *virtualhost* va a deshabilitar dicho *virtualhost*.

```bash
gerard@aldebaran:~/docker/gw-poc$ touch volume/api2
gerard@aldebaran:~/docker/gw-poc$ curl -H "Host: api1" http://localhost/
Hello from api1
gerard@aldebaran:~/docker/gw-poc$ curl -H "Host: api2" http://localhost/
{"message":"Sorry you! This entity (api2) is in maintenance mode"}
gerard@aldebaran:~/docker/gw-poc$ 
```

De la misma manera, podemos rehabilitarlo quitando ese fichero de ahí.

```bash
gerard@aldebaran:~/docker/gw-poc$ rm volume/api2 
gerard@aldebaran:~/docker/gw-poc$ curl -H "Host: api1" http://localhost/
Hello from api1
gerard@aldebaran:~/docker/gw-poc$ curl -H "Host: api2" http://localhost/
Bye from api2
gerard@aldebaran:~/docker/gw-poc$ 
```

Y lo mismo aplica para el primer dominio, aunque no lo repito por brevedad.

## Siguientes pasos

El hecho de habilitar y deshabilitar las APIs se necesitaba hacer por parte de gente que no tiene necesariamente conocimientos técnicos para acceder al entorno, o no queremos simplemente por seguridad. La solución cómoda es una bonita interfaz web que les permita hacerlo a golpe de click y con una gestión de permisos adecuada ya incorporada.

Como no queremos inventar la rueda nuevamente, podemos usar algo que ya esté hecho, como por ejemplo un **jenkins**. De hecho, nada nos impide que el **jenkins** lance *playbooks* de **ansible**. Sin embargo este ya es otro proyecto y en caso de que os interese, [ya he escrito sobre esto]({filename}/articles/lanzando-playbooks-de-ansible-desde-jenkins.md).
