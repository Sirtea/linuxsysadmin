Title: Un entorno web estático con nginx, rsync y docker
Slug: un-entorno-web-estatico-con-nginx-rsync-y-docker
Date: 2017-03-27 10:00
Category: Sistemas
Tags: docker, docker-compose, nginx, volumenes, rsync, rssh



Hemos hablado de generar nuestro contenido HTML estático con otras herramientas, y finalmente ha llegado la hora de servirlo. Normalmente, los ficheros que cambian tal y como vamos generando páginas son pocos y nos interesa copiarlo de forma remota, pero no podemos hacerlo con **docker** porque hacen falta dos servicios.

Si has asentido con la cabeza, mal. Es verdad que se necesitan dos servicios, pero hay maneras de ejecutar dos procesos en un mismo contenedor, por ejemplo [con un gestor de procesos]({filename}/articles/multiples-servicios-en-un-mismo-contenedor-docker.md). Sin embargo, esa no es la filosofía de **docker**. Un contenedor solo debería ejecutar un proceso, simplificando su contenido y siendo necesarios varios contenedores para hacer nuestro sistema modular.

Así que solo nos queda pensar las partes que tiene nuestro pequeño entorno, para luego levantar contenedores que ejecuten todos los servicios necesarios, posiblemente con **docker-compose**:

* Un servidor web
* Un servicio de transferencia de archivos
* Algún sitio compartido para dejar los ficheros

**TRUCO**: Puesto que ambos servicios van a necesitar acceder al mismo sitio, necesitamos volúmenes. Sin embargo, no queremos mezclar los datos con ninguno de los otros contenedores, ya que en caso de actualizarlos, perderíamos el volumen. Eso nos deja dos opciones: un *host volume* o un *data container*, que usaremos por portabilidad.

## El servidor web

Vamos a utilizar **nginx** por su eficiencia y velocidad. Consume poco, ocupa poco, y es simple de configurar. Como ligereza adicional, vamos a partir de una imagen de *Alpine Linux*.

La imagen no tiene misterio: un *Dockerfile*, un fichero de arranque ejecutable y dos ficheros de configuración.

```bash
gerard@aldebaran:~/docker/syncweb/web$ cat Dockerfile 
FROM alpine:3.5
RUN apk add --no-cache nginx tini && \
    ln -s /dev/stdout /var/log/nginx/access.log && \
    ln -s /dev/stderr /var/log/nginx/error.log && \
    mkdir /run/nginx && \
    mkdir /srv/www && \
    rm /etc/nginx/conf.d/default.conf
COPY nginx.conf /etc/nginx/
COPY conf.d/* /etc/nginx/conf.d/
COPY start.sh /
ENTRYPOINT ["/sbin/tini", "--"]
CMD ["/start.sh"]
gerard@aldebaran:~/docker/syncweb/web$ cat start.sh 
#!/bin/sh

exec /usr/sbin/nginx -g "daemon off;"
gerard@aldebaran:~/docker/syncweb/web$ cat nginx.conf 
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
gerard@aldebaran:~/docker/syncweb/web$ cat conf.d/web 
server {
	server_name _;
	listen 80;
	root /srv/www;
	index index.html;
}
gerard@aldebaran:~/docker/syncweb/web$ 
```

Vamos a asumir que la carpeta `/srv/www/` existe, puesto que la montaremos como un volumen.

## Transfiriendo ficheros

Dada la naturaleza incremental de nuestro contenido HTML, nos viene muy bien utilizar **rsync**, que funciona sobre **ssh** y nos aporta encriptación, compresión y copia diferencial. Vamos a restringir el uso del **ssh** mediante **rssh**, permitiendo solamente usar **rsync**.

Nuevamente vamos a partir de una imagen *Alpine Linux*, que es pequeña, segura y en este caso nos sirve de maravilla. Creamos la imagen con un simple *Dockerfile* y un fichero de arranque, con permiso de ejecución.

```bash
gerard@aldebaran:~/docker/syncweb/rsync$ cat Dockerfile 
FROM alpine:3.5
RUN apk add --no-cache openssh rsync rssh tini && \
    sed 's/^#allowrsync/allowrsync/g' /etc/rssh.conf.default > /etc/rssh.conf && \
    adduser web -s /usr/bin/rssh -D -H && \
    echo "web:web" | chpasswd
COPY start.sh /
ENTRYPOINT ["/sbin/tini", "--"]
CMD ["/start.sh"]
gerard@aldebaran:~/docker/syncweb/rsync$ cat start.sh 
#!/bin/sh

chown -R web:web /srv/www
ssh-keygen -t rsa -f /etc/ssh/ssh_host_rsa_key -N ''
exec /usr/sbin/sshd -D -e
gerard@aldebaran:~/docker/syncweb/rsync$ 
```

Lo más interesante de decir es que la carpeta `/srv/www/` va a ser montada como volumen. Como no podemos asegurar que los permisos sean correctos, los forzamos al usuario *web*, que es el que va a poder entrar por **rsync**. Otro punto a tener en cuenta es que se ha movido la creación de la clave de *host* al fichero *start.sh* para evitar duplicarla a base de crear contenedores a partir de la clave de la imagen.

## El contenedor de datos

Se trata de un contenedor que va a acabar tras levantar. Su única función es albergar un volumen de datos para exportarlo a otros contenedores.

Lo crearemos usando una imagen mínima, que solo tiene el comando *true*, así podemos ejecutar un comando que no hace nada y no cargamos nada adicional. Le ponemos un contenido básico, que nos permite ver que todo funciona y que luego será sustituido mediante **rsync**.

```bash
gerard@aldebaran:~/docker/syncweb/data$ cat Dockerfile 
FROM tianon/true
COPY index.html /srv/www/
gerard@aldebaran:~/docker/syncweb/data$ cat index.html 
<h1>Hello world</h1>
<p>This is a placeholder file</p>
gerard@aldebaran:~/docker/syncweb/data$ 
```

Este contenedor solamente ejecuta *true* y acaba. Sin embargo, su volumen sigue siendo accesible por aquellos contenedores que lo exporten.

## Todo junto

Antes que nada creamos las imágenes, según los comandos habituales:

```bash
gerard@aldebaran:~/docker/syncweb$ docker build -t data data/
...  
gerard@aldebaran:~/docker/syncweb$ docker build -t web web/
...  
gerard@aldebaran:~/docker/syncweb$ docker build -t rsync rsync/
...  
gerard@aldebaran:~/docker/syncweb$ 
```

Comprobamos las imágenes que hemos creado, viendo que se han hecho bien y que ocupan una cantidad de espacio razonable.

```bash
gerard@aldebaran:~/docker/syncweb$ docker images
REPOSITORY          TAG                 IMAGE ID            CREATED              SIZE
rsync               latest              cb33669eb5f6        54 seconds ago       8.77 MB
web                 latest              1ae71f497ae0        About a minute ago   5.75 MB
data                latest              cc6555822fd9        About a minute ago   180 B
gerard@aldebaran:~/docker/syncweb$ 
```

Y ya solo nos queda levantar el entorno con **docker-compose**, por ejemplo con un *docker-compose.yml* como el que sigue:

```bash
gerard@aldebaran:~/docker/syncweb$ cat docker-compose.yml 
version: '2'
services:
  data:
    image: data
    hostname: data
    container_name: data
    volumes:
      - /srv/www
  rsync:
    image: rsync
    hostname: rsync
    container_name: rsync
    ports:
      - "22:22"
    volumes_from:
      - data
  web:
    image: web
    hostname: web
    container_name: web
    ports:
      - "8000:80"
    volumes_from:
      - data
gerard@aldebaran:~/docker/syncweb$ docker-compose up -d
Creating network "syncweb_default" with the default driver
Creating data
Creating rsync
Creating web
gerard@aldebaran:~/docker/syncweb$ 
```

De esta forma, todos importan el contenedor de datos, y podemos copiar ficheros por **rsync** al puerto 22, y ver la web en el puerto 8000. Cambiad estos valores según vuestras necesidades.

## Comprobaciones

Vemos que si hacemos una petición normal, nos devuelve el contenido inicial.

```bash
gerard@aldebaran:~/docker/syncweb$ curl http://localhost:8000/
<h1>Hello world</h1>
<p>This is a placeholder file</p>
gerard@aldebaran:~/docker/syncweb$ 
```

Eso significa que el servidor web funciona y está sirviendo el contenido del contenedor de datos. Ahora vamos a probar que el contenedor **rsync** puede actualizar este contenido. Para comodidad lo he puesto en un *script*.

```bash
gerard@aldebaran:~/docker/syncweb$ cat sync.sh 
#!/bin/bash

rsync -rvzc --delete content/ web@localhost:/srv/www/
gerard@aldebaran:~/docker/syncweb$ 
```

Asumimos que tenemos la carpeta `content/` con otro fichero *index.html*. Lo he creado a mano para la prueba, pero esto podría aparecer generado por un [generador de contenido estático]({filename}/articles/generadores-de-contenido-web-estaticos.md). Lanzamos el *script* por primera vez:

```bash
gerard@aldebaran:~/docker/syncweb$ ./sync.sh 
Warning: Permanently added 'localhost' (RSA) to the list of known hosts.
web@localhost's password: 
Could not chdir to home directory /home/web: No such file or directory
sending incremental file list
index.html

sent 182 bytes  received 41 bytes  63.71 bytes/sec
total size is 60  speedup is 0.27
gerard@aldebaran:~/docker/syncweb$ 
```

El fichero *index.html* ha cambiado, así que lo vuelve a enviar, y por supuesto, es lo que el servidor web va a servir, cosa que demuestra que también hace uso del contenedor de datos.

```bash
gerard@aldebaran:~/docker/syncweb$ curl http://localhost:8000/
<h1>My autogenerated blog</h1>
<p>This is the home page</p>
gerard@aldebaran:~/docker/syncweb$ 
```
Para comprobar el carácter incremental de **rsync**, vamos a añadir un nuevo fichero *.html* y a ejecutar de nuevo. En caso de un generador estático, veremos que solo se enviarían las nuevas páginas y aquellos índices que hayan cambiado, resultando en una ganancia alta, a nivel de tamaño enviado y tiempo invertido.

```bash
gerard@aldebaran:~/docker/syncweb$ ./sync.sh 
Warning: Permanently added 'localhost' (RSA) to the list of known hosts.
web@localhost's password: 
Could not chdir to home directory /home/web: No such file or directory
sending incremental file list
newpage.html

sent 179 bytes  received 35 bytes  47.56 bytes/sec
total size is 71  speedup is 0.33
gerard@aldebaran:~/docker/syncweb$ 
```

Solo ha enviado el fichero nuevo, puesto que es un cambio con respecto a lo que ya tiene. De hecho, de no haber cambios, no se enviaría nada.

```bash
gerard@aldebaran:~/docker/syncweb$ ./sync.sh 
Warning: Permanently added 'localhost' (RSA) to the list of known hosts.
web@localhost's password: 
Could not chdir to home directory /home/web: No such file or directory
sending incremental file list

sent 128 bytes  received 12 bytes  56.00 bytes/sec
total size is 71  speedup is 0.51
gerard@aldebaran:~/docker/syncweb$ 
```

Y con esto tenemos nuestro pequeño entorno funcional.
