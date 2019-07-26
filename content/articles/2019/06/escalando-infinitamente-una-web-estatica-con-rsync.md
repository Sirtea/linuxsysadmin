---
title: "Escalando infinitamente una web estática con rsync"
slug: "escalando-infinitamente-una-web-estatica-con-rsync"
date: 2019-06-17
categories: ['Sistemas']
tags: ['rsync', 'html', 'docker']
---

Hace unos meses recibí una petición interesante; unos conocidos querían exponer un sitio web estático, pero lo querían replicado en muchos sitios porque era posible que les fueran cerrando sitios por su dudosa legalidad. Por supuesto me negué, pero el desafío era muy estimulante, así que intenté diseñarlo *a posteriori*.<!--more-->

Ir copiando ficheros estáticos cada vez que se hace una modificación o se pone en circulación un nuevo servidor no es escalable, especialmente si hablamos de números grandes de servidores; así que mi solución pasó porque cada *replica* se clonara de otra de forma automatizada.

La idea es simple:

* El nodo *master* dispone del sitio original, y posiblemente es donde se genera.
* Los nodos *replica* se limitan a clonar a un *master* o a una *replica* con soporte a clonado.
    * Opcionalmente pueden servir el sitio para su clonado por parte de otras *replicas*.
    * Opcionalmente pueden servir el sitio mediante un servidor web.

De esta manera, podemos descargar al *master* clonando de *replicas* y tenemos el sitio alojado en un montón de *replicas*. Con un diseño inteligente de nuestra red, podemos escalar bastante clonando de *replicas* intermedias y reconfigurando las *replicas* dependientes de una que nos hayan podido cerrar.

Si nos creemos que la cadena de clonado funciona, eventualmente todas las *replicas* se irán actualizando tal como la original vaya cambiando. Si algún nodo no actualizara, siempre dispondría de una copia ligeramente desactualizada, aunque funcional.

**TRUCO**: Dada la naturaleza incremental y la escasa modificación del sitio, una herramienta tipo **rsync** puede ser de gran utilidad.

## Preparando las piezas

De acuerdo con el diseño anterior, todo los nodos se pueden montar con tres piezas simples y con una función bien especificada:

* Un servidor de ficheros **rsync**
* Un clonador de ficheros que sea un cliente de **rsync**
* Un servidor web para ofrecer el contenido

Cada nodo tendría una configuración de las anteriores, dependiendo de su función:

* El nodo *master* sirve por **rsync** su carpeta de ficheros HTML
* Los nodos *replicas* clonan por **rsync** el contenido estático y opcionalmente pueden:
    * Ofrecer la replica por **rsync** para otras *replicas*
    * Ofrecer los ficheros replicados vía web
    * Por supuesto pueden hacer ambas funciones, pero tendrán que hacer al menos una de ellas para ser útiles

Tiene sentido empaquetar las piezas como imágenes **docker**, para su fácil distribución y montado en cada nodo. Es responsabilidad del administrador de cada nodo saber qué servicios tiene que levantar, monitorizar la salud de la *replica* de la que están clonando y reconfigurar el clonador si es necesario.

### El servidor rsync

Aunque estamos acostumbrados a utilizar **rsync** por SSH, este puede funcionar de forma independiente. Para ello vamos a necesitar una imagen con **rsync** instalado y una configuración relevante:

```bash
gerard@tartarus:~$ cat build/fileserver/Dockerfile 
FROM alpine:3.9
RUN apk add --no-cache rsync
COPY rsyncd.conf /etc/
CMD ["rsync", "--daemon", "--no-detach"]
gerard@tartarus:~$ 
```

Indicamos la configuración, simple pero potente; la único importante es la carpeta que servimos y que el servidor solo va a permitir que lean los ficheros, de forma que no nos puedan modificar desde las *replicas*.

```bash
gerard@tartarus:~$ cat build/fileserver/rsyncd.conf 
use chroot = yes
read only = yes
log file = /dev/stdout

[public]
path = /srv/public
gerard@tartarus:~$ 
```

**TRUCO**: Con esta configuración servimos el *path* `/srv/public` (es la directiva `path`) en la ruta `/public` (es la sección de la configuración).

La construcción de la imagen tampoco tiene ningún misterio:

```bash
gerard@tartarus:~$ docker build -t fileserver build/fileserver/
...
gerard@tartarus:~$ 
```

### El cliente de clonación

No vamos a hacer nada demasiado complicado en este paso; se trata de una imagen con **rsync** que va a ejecutar un *script*.

```bash
gerard@tartarus:~$ cat build/cloner/Dockerfile 
FROM alpine:3.9
RUN apk add --no-cache rsync
COPY run.sh /
CMD ["/run.sh"]
gerard@tartarus:~$ 
```

Este *script* se limita a lanzar el comando `rsync` para el clonado de su origen, de forma infinita y con una espera entre llamadas para no saturar a su nodo origen.

```bash
gerard@tartarus:~$ cat build/cloner/run.sh 
#!/bin/sh

while true; do
    echo "-------------------------"
    date +"%F %T %z"
    echo "-------------------------"
    rsync -rvzc --delete rsync://${UPSTREAM}/public /srv/files
    sleep ${INTERVAL}
done
gerard@tartarus:~$ 
```

**TRUCO**: El *script* tiene permisos de escritura; sino la imagen no lo ejecuta.

Construimos la imagen de la forma habitual:

```bash
gerard@tartarus:~$ docker build -t cloner build/cloner/
gerard@tartarus:~$ 
```

**TRUCO**: El resultado de la clonación acaba en `/srv/files`, tal como indica el comando `rsync` del *script*.

### El servidor web

Por su escaso uso de recursos y su fácil configuración, elijo **nginx**. Esta es una decisión arbitraria y se puede cambiar.

```bash
gerard@tartarus:~$ cat build/webserver/Dockerfile 
FROM sirrtea/nginx:alpine
COPY www.conf /etc/nginx/conf.d/
gerard@tartarus:~$ 
```

La configuración es clara y concisa y no necesita más explicaciones:

```
gerard@tartarus:~$ cat build/webserver/www.conf 
server {
    listen 80;
    server_name _;
    root /srv/www;
    index index.html;
    error_page 404 /404.html;

    location /404.html {
        internal;
    }
}
gerard@tartarus:~$ 
```

Construimos la imagen sin complicaciones:

```bash
gerard@tartarus:~$ docker build -t webserver build/webserver/
gerard@tartarus:~$ 
```

**TRUCO** El servidor web va a servir el contenido web localizado en `/srv/www`

## Distribuyendo las imágenes

Tras la preparación de las piezas en el punto anterior, hemos obtenido 3 imágenes:

```bash
gerard@tartarus:~$ docker images
REPOSITORY          TAG                 IMAGE ID            CREATED             SIZE
webserver           latest              b282a42d624d        2 minutes ago       6.97MB
cloner              latest              dc7d403cedc4        6 minutes ago       6.08MB
fileserver          latest              f05e021118f5        17 minutes ago      6.08MB
gerard@tartarus:~$ 
```

Vamos a necesitar que estas imágenes lleguen de alguna manera a cada *replica* que pongamos en circulación, mediante alguno de los siguientes métodos:

* Uso de un registro de **docker**
* Construcción local en cada *replica*
* Distribución de las imágenes en un medio físico

Utilizaré la tercera por comodidad. Para ello, voy a utilizar el comando `docker save` para obtener las imágenes un un fichero comprimido, y el comando `docker load` para cargar las imágenes del fichero comprimido a cada *replica*.

De momento, obtenemos las imágenes en un fichero comprimido y lo restableceremos en las *replicas* cuando las vayamos montando:

```bash
gerard@tartarus:~$ docker save fileserver cloner webserver | gzip -9c > images.tar.gz
gerard@tartarus:~$ 
```

## Montando la red de replicas

### El nodo master

Vamos a empezar con el nodo inicial, al que llamamos *master*. La responsabilidad de este nodo es ofrecer los ficheros para ser clonados. De esta forma solo necesitaríamos el servidor de **rsync**.

Supongamos que el contenido web se aloja en la carpeta `~/html`; recordemos que el servidor **rsync** sirve la carpeta `/srv/public`.

```bash
gerard@tartarus:~$ tree html/
html/
└── index.html

0 directories, 1 file
gerard@tartarus:~$ 
```

La forma más fácil de exponer este contenido es con un volumen, específicamente montando la carpeta local de nuestra máquina de generación de contenido HTML.

```bash
gerard@tartarus:~$ docker run -d --rm -p 873:873 -v ~/html:/srv/public:ro fileserver
bc7bfffd6f8d548fff0955b5da980684d89ad600efaf94544406e2f70735ea9d
gerard@tartarus:~$ 
```

### Algunos nodos replicas

Lo primero es restablecer las imagenes en los nodos *replica*. Puesto que decidimos montarlo "a pendrive", las imagenes estan en un fichero comprimido que tenemos que cargar. Esto se repite en todas las *replicas*, tal como las vayamos montando, aunque solo vamos a poner una de ellas para simplificar.

```bash
gerard@mirror1:~$ docker load < images.tar.gz 
f1b5933fe4b5: Loading layer [==================================================>]  5.796MB/5.796MB
1e89db8db04f: Loading layer [==================================================>]  559.6kB/559.6kB
4aa21c716e77: Loading layer [==================================================>]   2.56kB/2.56kB
Loaded image: fileserver:latest
b11b8db9873c: Loading layer [==================================================>]  2.048kB/2.048kB
Loaded image: cloner:latest
47f5beca9909: Loading layer [==================================================>]  1.478MB/1.478MB
258810e67818: Loading layer [==================================================>]  3.072kB/3.072kB
00c03d47392d: Loading layer [==================================================>]  3.584kB/3.584kB
Loaded image: webserver:latest
gerard@mirror1:~$ 
```

La función principal e ineludible de las *replicas* es replicar desde un nodo padre. También decidimos parametrizar el intervalo en segundos que íbamos a esperar entre llamadas a **rsync**. Vamos a poner estos parámetros arbitrarios:

* **mirror1** &rarr; Sincronizamos de **tartarus** cada 60 segundos.
* **mirror2** &rarr; Sincronizamos de **tartarus** cada 10 segundos.
* **mirror3** &rarr; Sincronizamos de **mirror1** cada 60 segundos.

Esto nos supone lanzar el `docker run` con las variables de entorno pertinentes. Es importante que la carpeta `/srv/files` sea un volumen compartido con los otros servicios, para que podamos servir lo clonado, tanto por **rsync** como por HTTP.

```bash
gerard@mirror1:~$ docker run -d --rm -v data:/srv/files -e "UPSTREAM=tartarus" -e "INTERVAL=60" cloner
59fb9353635150f502e18fce31a596f10beaeb226c8699b5ad89b11c8400a917
gerard@mirror1:~$ 
```

```bash
gerard@mirror2:~$ docker run -d --rm -v data:/srv/files -e "UPSTREAM=tartarus" -e "INTERVAL=10" cloner
9ed674f1bea94422bac503a859aa9ec844a29436ebdecf43500b5388c6ecede2
gerard@mirror2:~$ 
```

```bash
gerard@mirror3:~$ docker run -d --rm -v data:/srv/files -e "UPSTREAM=mirror1" -e "INTERVAL=60" cloner
b3af2fed84b09d2ed0634a749a0f0a9ff42f8fdfddb45fb8e5ae0d05cfd09e4d
gerard@mirror3:~$ 
```

**NOTA**: En este punto, **mirror1** no está sirviendo por **rsync**, así que **mirror3** no va a poder sincronizarse hasta que levantemos la imagen `fileserver`. Basta hacer un `docker logs` para comprobarlo.

La siguiente función es la de servir los ficheros por **rsync**. Supongamos de nuevo que el administrador de **mirror2** decide que no quiere ofrecer este servicio, así que no lo levanta. Eso significa que nadie lo va a poder utilizar como nodo padre, aunque podrá servir los ficheros por HTTP.

```bash
gerard@mirror3:~$ docker run -d --rm -p 873:873 -v data:/srv/public:ro fileserver
ec50b9d46b02bed01c1881b391792e31f7dd3cd07cfdbd9a80bcea4fe8f80b4e
gerard@mirror3:~$ 
```

```bash
gerard@mirror1:~$ docker run -d --rm -p 873:873 -v data:/srv/public:ro fileserver
cf151e53490a1fc2798669f70b89ff927541fd874bedde67bf8e1b6ffbb187f9
gerard@mirror1:~$ 
```

**NOTA**: La siguiente ejecución del clonador de **mirror3** debería dejar de fallar, ya que el servicio **rsync** de **mirror1** se ha levantado.

La última función de los nodos es la de servir la web por HTTP. Asumamos que el administrador de **mirror1** decide mantenerse como un nodo de solo clonación, y no ofrece ese servicio, así que no lo levanta.

```bash
gerard@mirror2:~$ docker run -d --rm -p 80:80 -v data:/srv/www:ro webserver
85304bcf17e4b2bca55f1fb044d271857b06dec6c0c6aa89939539a19fd292c9
gerard@mirror2:~$ 
```

```bash
gerard@mirror3:~$ docker run -d --rm -p 80:80 -v data:/srv/www:ro webserver
addfe34788283b88b5c44dd8ced5ba834c319b3e0e6787976ad4f098140e9dff
gerard@mirror3:~$ 
```

Solo nos queda comprobar que el contenido HTML es el esperado, lo solicitemos a **mirror2** o  **mirror3**. Evidentemente, **mirror1** va a fallar porque no levantó el **nginx**.

```bash
gerard@anywhere:~$ curl http://mirror1:80/
curl: (7) Failed to connect to mirror1 port 80: Conexión rehusada
gerard@anywhere:~$ curl http://mirror2:80/
<h1>Hello world</h1>
gerard@anywhere:~$ curl http://mirror3:80/
<h1>Hello world</h1>
gerard@anywhere:~$ 
```

Solo queda indicar que el contenido se va a actualizar a intervalos, y puede ser que clonar de otras *replicas* vaya introduciendo un retardo de actualización. Una cadena de 5 nodos puede suponer 5 minutos de retardo usando un intervalo de 60 segundos, pero creo que es aceptable y muy escalable...

## Otros detalles

El responsable de cada *replica* debería monitorizar los *logs* del clonador; en caso de caída o cierre del nodo padre, habría que buscar otra *replica* de la que clonar. Eso supone parar el clonador y relanzarlo con un nuevo *upstream*, o simplemente quedarse sin actualizar hasta el restablecimiento del nodo padre.

En cuanto a la escalabilidad, podemos concluir que si una *replica* sirve como nodo padre de varias otras *replicas*, el crecimiento de la red puede ser exponencial...

Lo único que no se resuelve es donde poner la lista de webs disponibles para el consumidor de este contenido de dudosa legalidad. Sed creativos y portáos bien.
