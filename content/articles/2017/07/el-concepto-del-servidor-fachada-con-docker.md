---
title: "El concepto del servidor fachada con Docker"
slug: "el-concepto-del-servidor-fachada-con-docker"
date: 2017-07-03
categories: ['Sistemas']
tags: ['docker', 'fachada', 'docker-compose']
---

Muchos de nosotros tenemos un servidor en casa o en algún *hosting*. Como no tenemos mucho tráfico y cada servidor tiene un coste, acabamos llenándolo con un conjunto de servicios bastante grande. Esto supone un problema para actualizar el sistema operativo, suponiendo que los servicios no se molesten entre sí.<!--more-->

En estos casos podemos valernos de **docker** (o de cualquier otro sistema de contenedores) para aislar cada servicio en su propio contenedor y para facilitar su portabilidad hacia un nuevo servidor. Con un poco de habilidad con reglas de *networking*, podemos hacer esta transición sin cortes y poco a poco.

El truco es utilizar el concepto **fachada**, es decir, nuestro servidor es solo la fachada de cada una de nuestros contenedores. Estos exponen su servicio como un puerto en la máquina *host* y así parece que el *host* es un único servidor. Este *host* también nos puede servir para albergar los *host volumes* y para hacer tareas de mantenimiento tales como *backups* o *logrotate*.

## Un ejemplo práctico

Supongamos que queremos un servidor casero con 3 servicios:

* Un servidor **mariadb** y su interfaz de administración web **adminer**
* Un servidor de **mongodb**
* Un servidor web **nginx**

En vez de instalarlo todo en nuestro servidor, vamos a aplicar la técnica antes descrita, de mapear en los puertos oficiales los puertos de los contenedores que ejecutan los servicios. Para simplificar el artículo, vamos a utilizar las imágenes oficiales en *DockerHub*.

Para su fácil lanzamiento, vamos a usar **docker-compose**, que nos simplifica bastante la línea de comandos, ocultando en el fichero *docker-compose.yml* cosas como las variables de entorno, el mapeo de puertos o los volúmenes.

### MariaDB y Adminer

Necesitaremos un *docker-compose.yml* para levantar los contenedores de **mariadb** y **adminer**. En el caso de **mariadb**, tiene una parte de datos persistentes, que vamos a dejar como un *host volume* local.

```bash
gerard@aldebaran:~/docker/homeserver$ tree mariadb/
mariadb/
├── data
└── docker-compose.yml

1 directory, 1 file
gerard@aldebaran:~/docker/homeserver$ cat mariadb/docker-compose.yml 
version: '3'
services:
  mariadb:
    image: mariadb
    container_name: mariadb
    hostname: mariadb
    volumes:
      - ./data:/var/lib/mysql
    environment:
      MYSQL_ROOT_PASSWORD: root1234
    ports:
      - "3306:3306"
  adminer:
    image: adminer
    container_name: adminer
    hostname: adminer
    ports:
      - 8080:8080
gerard@aldebaran:~/docker/homeserver$ docker-compose -f mariadb/docker-compose.yml up -d
Creating network "mariadb_default" with the default driver
Creating mariadb
Creating adminer
gerard@aldebaran:~/docker/homeserver$ 
```

### MongoDB

De forma análoga, vamos a usar un *docker-compose.yml*, mapeando el puerto de **mongodb** y su carpeta de datos en el *host*.

```bash
gerard@aldebaran:~/docker/homeserver$ tree mongodb/
mongodb/
├── data
└── docker-compose.yml

1 directory, 1 file
gerard@aldebaran:~/docker/homeserver$ cat mongodb/docker-compose.yml 
version: '3'
services:
  mongodb:
    image: mongo
    container_name: mongodb
    hostname: mongodb
    volumes:
      - ./data:/data/db
    ports:
      - "27017:27017"
gerard@aldebaran:~/docker/homeserver$ docker-compose -f mongodb/docker-compose.yml up -d
Creating network "mongodb_default" with the default driver
Creating mongodb
gerard@aldebaran:~/docker/homeserver$ 
```

### Nginx

Y volvemos a repetir el proceso; un *docker-compose.yml*, un puerto mapeado, y un *host volume* para albergar el contenido web.

```bash
gerard@aldebaran:~/docker/homeserver$ tree nginx/
nginx/
├── www
│   └── index.html
└── docker-compose.yml

1 directory, 2 files
gerard@aldebaran:~/docker/homeserver$ cat nginx/docker-compose.yml 
version: '3'
services:
  nginx:
    image: nginx
    container_name: nginx
    hostname: nginx
    volumes:
      - ./www:/usr/share/nginx/html:ro
    ports:
      - "80:80"
gerard@aldebaran:~/docker/homeserver$ docker-compose -f nginx/docker-compose.yml up -d
Creating network "nginx_default" with the default driver
Creating nginx
gerard@aldebaran:~/docker/homeserver$ 
```

### El resultado

Si miramos los puertos abiertos en nuestro servidor, podemos ver fácilmente que responde los 4 puertos que suministran los servicios antes citados, y nada nos impide seguir creando servicios para ofrecer más puertos en nuestro servidor. 

```bash
gerard@aldebaran:~/docker/homeserver$ netstat -lnt
Active Internet connections (only servers)
Proto Recv-Q Send-Q Local Address           Foreign Address         State      
tcp6       0      0 :::27017                :::*                    LISTEN     
tcp6       0      0 :::3306                 :::*                    LISTEN     
tcp6       0      0 :::80                   :::*                    LISTEN     
tcp6       0      0 :::8080                 :::*                    LISTEN     
gerard@aldebaran:~/docker/homeserver$ 
```

En caso de querer actualizar el sistema operativo base, solo tenemos que crear un nuevo servidor y levantar los contenedores de servicio, uno por uno; si usamos algún elemento de red como un *firewall*, podemos desviar tráfico sin que se note, hasta que estemos preparados para reemplazar el servidor viejo con el nuevo.

Al tratarse de contenedores individuales, lo que pase en un contendedor no va a interferir en lo que pase en otro, ganando así el concepto de aislamiento, pudiendo convivir varias versiones de un mismo *software* o diversos servicios que ofrezcan el mismo protocolo. solo hay que tener en cuenta que los puertos mapeados en el *host* deben ser únicos.
