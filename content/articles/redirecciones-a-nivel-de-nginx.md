Title: Redirecciones a nivel de nginx
Slug: redirecciones-a-nivel-de-nginx
Date: 2017-11-13 10:00
Category: Sistemas
Tags: nginx, redirecciones



No son pocas las veces que queremos hacer una redirección de algunos de nuestros dominios a otros. Puede que queramos añadir el clásico `www` delante del dominio, o tal vez queramos forzar el uso de `https`. Hacer copias de nuestro dominio no es viable, pero podemos usar redirecciones fijas 301.

Vamos a suponer en este artículo que tenemos un servidor **nginx** configurado para servir *virtualhosts*. En este ejemplo, vamos a poner uno por defecto y otro de ejemplo.

Las reglas son simples:

* Serviremos la web de ejemplo para el dominio *www.example.com*
* Queremos ver la misma web para el dominio *example.com* y no queremos duplicar contenido
* Serviremos una web por defecto en cualquier otro caso, para ver si lo hemos hecho bien

## Preparación del ejemplo

Para que se pueda seguir el artículo, se proporciona el contexto necesario para construir una imagen **docker** en donde probarlo. Empezamos por el *Dockerfile*:

```bash
gerard@aldebaran:~/docker/nginx_redirects$ cat Dockerfile 
FROM alpine:3.5
RUN apk add --no-cache nginx && \
    ln -s /dev/stdout /var/log/nginx/access.log && \
    ln -s /dev/stderr /var/log/nginx/error.log && \
    mkdir /run/nginx && \
    rm /etc/nginx/conf.d/default.conf
COPY nginx.conf /etc/nginx/
CMD ["/usr/sbin/nginx", "-g", "daemon off;"]
COPY conf.d/* /etc/nginx/conf.d/
COPY www/ /srv/www/
gerard@aldebaran:~/docker/nginx_redirects$ 
```

Y añadimos las configuraciones que **nginx** necesita:

```bash
gerard@aldebaran:~/docker/nginx_redirects$ cat nginx.conf 
worker_processes 1;
events {
	worker_connections 1024;
}
http {
	include mime.types;
	default_type application/octet-stream;
	sendfile on;
	keepalive_timeout 65;
	include conf.d/*;
}
gerard@aldebaran:~/docker/nginx_redirects$ cat conf.d/www 
server {
	listen 80 default;
	server_name _;
	root /srv/www/default;
	index index.html;
}

server {
	listen 80;
	server_name www.example.com;
	root /srv/www/www.example.com;
	index index.html;
}
gerard@aldebaran:~/docker/nginx_redirects$ 
```

A modo de ejemplo, adjuntamos dos sitios de juguete que nos permitirnán probar nuestros *virtualhosts*:

```bash
gerard@aldebaran:~/docker/nginx_redirects$ tree www/
www/
├── default
│   └── index.html
└── www.example.com
    └── index.html

2 directories, 2 files
gerard@aldebaran:~/docker/nginx_redirects$ cat www/default/index.html 
default site
gerard@aldebaran:~/docker/nginx_redirects$ cat www/www.example.com/index.html 
example site
gerard@aldebaran:~/docker/nginx_redirects$ 
```

Construid la imagen y ponedla a correr, con los comandos habituales.

**TRUCO**: Como queremos probar *virtualhosts* y no queremos marear con servidores DNS, podemos tirar del fichero */etc/hosts*, para que todos los dominios apunten a nuestro contenedor.

```bash
gerard@aldebaran:~$ cat /etc/hosts
...  
172.17.0.2	example.com www.example.com www.otherdomain.com
gerard@aldebaran:~$ 
```

## Problema y solución

Lanzamos una batería de peticiones con **curl** o alguna herramienta similar.

```bash
gerard@aldebaran:~$ curl http://www.example.com/
example site
gerard@aldebaran:~$ curl http://www.otherdomain.com/
default site
gerard@aldebaran:~$ curl http://example.com/
default site
gerard@aldebaran:~$ 
```

Todos los dominios apuntan a la dirección IP del mismo contenedor, y de ello sacamos algunas conclusiones:

* El dominio *www.example.com* funciona según lo esperado
* El dominio por defecto salta ante las peticiones que no pertenecen al dominio *www.example.com*
* Las peticiones al dominio *example.com* caen en el *virtualhost* por defecto

Podríamos haber creado otro *virtualhost* que sirviera una copia (o la misma carpeta) del dominio de ejemplo, pero no es elegante y en el caso de querer HTTPS no serviría. En estos casos, el estándar *de facto* es hacer una redirección al dominio correcto, mediante un código HTTP 301. Esto le indicará al navegador que la redirección es permanente y hará que este "se acuerde" de la redirección.

Para ello necesitamos un nuevo *virtualhost*, o adaptar el que tenemos para que acepte expresiones regulares; no vamos a seguir este camino por simplicidad.

Solo necesitaríamos utilizar el [rewrite module](http://nginx.org/en/docs/http/ngx_http_rewrite_module.html#return) de **nginx** para forzar un código de retorno a la URL correcta. Exponemos este ejemplo a continuación:

```bash
gerard@aldebaran:~/docker/nginx_redirects$ cat conf.d/www 
server {
	listen 80 default;
	server_name _;
	root /srv/www/default;
	index index.html;
}

server {
	listen 80;
	server_name www.example.com;
	root /srv/www/www.example.com;
	index index.html;
}

server {
	listen 80;
	server_name example.com;
	return 301 http://www.example.com$request_uri;
}
gerard@aldebaran:~/docker/nginx_redirects$ 
```

Si recreamos la imagen y la ejecutamos de nuevo, vemos que nuestra web se comporta de la forma especificada al principio del artículo.

```bash
gerard@aldebaran:~$ curl -I http://example.com/
HTTP/1.1 301 Moved Permanently
Server: nginx/1.10.3
Date: Tue, 06 Jun 2017 14:47:57 GMT
Content-Type: text/html
Content-Length: 185
Connection: keep-alive
Location: http://www.example.com/

gerard@aldebaran:~$ 
```

De esta forma, el navegador buscará la nueva página, de acuerdo a esta respuesta. Se fuerza la opción "follow redirects" en la salida del **curl** para poder observar este comportamiento:

```bash
gerard@aldebaran:~$ curl http://www.example.com/
example site
gerard@aldebaran:~$ curl http://www.otherdomain.com/
default site
gerard@aldebaran:~$ curl -L http://example.com/
example site
gerard@aldebaran:~$ 
```

Y lo mismo sería válido para forzar una redirección a HTTPS, aunque se deja como ejercicio al lector.
