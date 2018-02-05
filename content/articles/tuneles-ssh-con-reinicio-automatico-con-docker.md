Title: Túneles SSH con reinicio automático con Docker
Slug: tuneles-ssh-con-reinicio-automatico-con-docker
Date: 2018-02-12 10:00
Category: Operaciones
Tags: ssh, túnel, docker, docker-compose



Ya vimos en [un artículo anterior]({filename}/articles/levantando-tuneles-ssh-con-systemd.md) como delegar en **SystemD** la persistencia de túneles SSH. El otro día intenté reproducirlo sin éxito en un servidor con una versión baja de **SystemD**; finalmente me di cuenta de que había otra herramienta en el servidor capaz de reiniciar un túnel caído: **Docker**.

## El problema

El contexto no cambia respecto al citado artículo: tengo un servidor ejecutando los servicios de **MongoDB** y **SSH**, pero no puedo acceder a la base de datos porque expone su *socket* solo a *localhost*.

En circunstancias normales, el túnel es trivial:

```bash
ssh -L 9999:localhost:27017 usuario@servidor -Nf
```

Pero en mi entorno de trabajo, debido a directivas de seguridad arbitrarias, ese túnel se caía demasiado a menudo, y levantarlo manualmente era muy pesado.

## La solución

Fallado el intento con **SystemD**, decidí dar un intento a **Docker**, y este es el resultado; se trata solamente de una imagen con el cliente **SSH** que más nos convenga, con una distribución base de nuestro agrado, por ejemplo, **Alpine Linux**.

```bash
gerard@sirius:~/docker/tunnelmaker$ cat context/Dockerfile 
FROM alpine:3.6
RUN apk add --no-cache openssh-client
gerard@sirius:~/docker/tunnelmaker$ 
```

Con estas herramientas, nos valdría con lanzar el comando del túnel, pero habrá que acompañar el contenedor hecho a partir de esta imagen de varias cosas:

* La clave **SSH** para levantar el túnel sin contraseña, evitando una intervención manual o el fallo directo del `docker run`. Por supuesto, el servidor destino debe aceptar la clave para el usuario indicado en el comando del túnel.
* Una configuración **SSH** cliente que impida detenernos en el momento de aceptar el *fingerprint* del servidor destino.
* El propio comando del túnel **SSH**, que no hemos puesto en el *Dockerfile* para poder levantar diferentes túneles con la misma imagen.

Es especialmente importante respetar el usuario y los permisos de los fichero *id_rsa* y *config*, siendo `root:root:600` para el primero y `root:root:644` para el segundo.

Podemos levantar esta imagen con el comando `docker run` habitual, pero como tiene varios añadidos, y por comodidad, usaremos **docker-compose**.

```bash
gerard@sirius:~/docker/tunnelmaker$ cat docker-compose.yml 
version: '2'
services:
  mongotunnel:
    build: context
    volumes:
      - ./id_rsa:/root/.ssh/id_rsa
      - ./config:/root/.ssh/config
    ports:
      - "27777:9999"
    extra_hosts:
      - "mongoserver:192.168.1.135"
    command: ssh -L 0.0.0.0:9999:localhost:27017 jump@mongoserver -N
    stdin_open: true
    restart: always
gerard@sirius:~/docker/tunnelmaker$ 
```

Podemos observar el el fichero *docker-compose.yml* otras varias anomalías:

* **restart: always** &rarr; Este es el punto de todo el artículo; queremos que cuando el túnel se caiga, el mismo demonio de **Docker** se ocupe de levantarlo de nuevo.
* ** stdin_open: true** &rarr; Sin este parámetro, el túnel se cerraba nada más establecerse; sospecho que esta era la causa de que no funcionara la solución con **SystemD**.
* **extra_hosts** &rarr; No es indispensable, pero he querido utilizar nombres de servidor por claridad, aunque no dispongo de resolución de nombres para mis servidores locales. Esto añade la correspondiente entrada en */etc/hosts*.
* **ports** &rarr; Nuestro contenedor va a levantar el túnel en el puerto arbitrario 9999; lo mapeamos en cualquier puerto que tengamos libre en nuestro ordenador.

Adjunto la configuración **SSH** para tener el ejemplo completo. No pongo la clave privada **SSH** por razones de seguridad obvias; tendréis que generar vuestro propio par con el comando **ssh-keygen**.

```bash
gerard@sirius:~/docker/tunnelmaker$ cat config 
Host *
    StrictHostKeyChecking no
    UserKnownHostsFile /dev/null
    ServerAliveInterval 60
gerard@sirius:~/docker/tunnelmaker$ 
```

## El resultado

Solo necesitamos levantar el contenedor usando **docker-compose** para poder observar el resultado.

```bash
gerard@sirius:~/docker/tunnelmaker$ docker-compose up -d
Creating network "tunnelmaker_default" with the default driver
Creating tunnelmaker_mongotunnel_1
gerard@sirius:~/docker/tunnelmaker$ 
```

Ahora podremos acceder sin problemas a dicho servidor de bases de datos como si se encontrase en el puerto 27777 local; solo hace falta comprobarlo usando, por ejemplo, el mismo cliente de **MongoDB**.

```bash
gerard@sirius:~/docker$ mongo --port 27777
MongoDB shell version v3.4.7
connecting to: mongodb://127.0.0.1:27777/
MongoDB server version: 3.4.4
...  
> 
```

No importa cuantas veces se caiga el túnel; cuando eso pase, el contenedor acabará y el demonio de **Docker** lo va a volver a levantar.
