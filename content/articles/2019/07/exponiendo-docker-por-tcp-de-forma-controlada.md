---
title: "Exponiendo Docker por TCP de forma controlada"
slug: "exponiendo-docker-por-tcp-de-forma-controlada"
date: 2019-07-22
categories: ['Operaciones']
tags: ['docker', 'tcp', 'unix socket', 'nginx', 'haproxy']
---

Tengo un usuario que es muy cómodo; él solo consiguió una excepción de seguridad para poder abrir el puerto TCP de **docker** de un servidor concreto, para chafardear cómodamente desde su máquina. A pesar de mis reticencias, cumplí con lo que se me pedía, y no tardamos mucho en lamentarlo.<!--more-->

Normalmente, el servicio **docker** abre un *unix socket* en `/var/run/docker.sock`; se utiliza por defecto desde el cliente para lanzar las diferentes operaciones, por ejemplo, un `docker ps`. Otra opción es ejecutar el comando `docker` bajo la influencia de la variable de entorno `DOCKER_HOST`, que permitiría lanzar el comando contra un *host* remoto, **suponiendo que este _host_ remoto esté escuchando mediante TCP**.

## La opción fácil

Abrir el flujo TCP no es complicado; basta con iniciar el servicio **docker** con el *flag* `-H tcp://0.0.0.0(:<puerto>)` (el puerto por defecto es 2375), usando el *init* del sistema. Por ejemplo, en **Debian** hablaríamos de **systemd** y podríamos utilizar un fichero *override*.

Para ello observamos el comando que se está ejecutando en el fichero `docker.service`:

```bash
gerard@procyon:~$ cat /lib/systemd/system/docker.service 
...
[Service]
Type=notify
ExecStart=/usr/bin/dockerd -H fd:// --containerd=/run/containerd/containerd.sock
...
gerard@procyon:~$ 
```

Y lo copiamos en el fichero de *override*, con el parámetro añadido; posteriormente indicamos a **systemd** que recargue configuraciones y reinicie **docker**:

```bash
gerard@procyon:~$ cat /etc/systemd/system/docker.service.d/override.conf 
[Service]
ExecStart=
ExecStart=/usr/bin/dockerd -H fd:// --containerd=/run/containerd/containerd.sock -H tcp://0.0.0.0
gerard@procyon:~$ sudo systemctl daemon-reload
gerard@procyon:~$ sudo systemctl restart docker
gerard@procyon:~$ 
```

Podemos comprobar como el puerto por defecto 2375 queda abierto en el servidor:

```bash
gerard@procyon:~$ sudo ss -lntp
State      Recv-Q Send-Q                                                  Local Address:Port                                                                 Peer Address:Port              
LISTEN     0      128                                                                 *:22                                                                              *:*                   users:(("sshd",pid=350,fd=3))
LISTEN     0      128                                                                :::2375                                                                           :::*                   users:(("dockerd",pid=5107,fd=3))
LISTEN     0      128                                                                :::22                                                                             :::*                   users:(("sshd",pid=350,fd=4))
gerard@procyon:~$ 
```

Y con esto podríamos gestionar el servicio remoto cómodamente desde nuestro terminal en otra máquina:

```bash
gerard@aldebaran:~$ DOCKER_HOST=procyon docker info | grep ^Name
Name: procyon
WARNING: API is accessible on http://0.0.0.0:2375 without encryption.
         Access to the remote API is equivalent to root access on the host. Refer
         to the 'Docker daemon attack surface' section in the documentation for
         more information: https://docs.docker.com/engine/security/security/#docker-daemon-attack-surface
WARNING: No swap limit support
gerard@aldebaran:~$ 
```

Creo que el mensaje de *warning* es bastante claro; con un *unix socket* contábamos con permisos del sistema de ficheros limitados al grupo `docker`, pero ahora cualquiera que llegue a **procyon** por TCP puede hacer lo que le dé la gana...

**RESULTADO**: A la semana teníamos redes, imágenes y contenedores de usuarios que no deberían haber utilizado el sistema o que solo necesitaban acceso de lectura, lo que nos llevó a volver al *status quo* inicial cerrando el puerto de **docker** en **procyon**.

## Abriendo el puerto con un proxy reverso

Desde entonces ha habido un nuevo intento para proteger quien accede al servidor y qué acciones puede efectuar. Utilizando un servidor **nginx**, podemos hacer un `proxy_pass` al *unix socket*. La ventaja es que podemos utilizar las directivas de los diferentes módulos para limitar el acceso o los métodos que se utilizan; hay que recordar que el acceso al servicio **docker** no deja de ser [un servicio REST](https://docs.docker.com/engine/api/v1.39/).

Por ejemplo, podemos limitar el acceso a todo, excepto a GETs en `/networks` u otros métodos en `/networks` si estás en cierto rango de red:

```bash
gerard@procyon:~/dockerproxy$ cat docker.conf 
server {
	server_name _;
	listen 2375;

	location /v1.39/networks {
		limit_except GET {
			allow 10.0.0.5;
			deny all;
		}
		allow all;
		proxy_pass http://unix:/var/run/docker.sock;
	}
	deny all;
}
gerard@procyon:~/dockerproxy$ 
```

Basta con levantar un **nginx** con este *virtualhost*, siguiendo el procedimiento habitual:

```bash
docker run --rm -d --name dockerproxy -v /var/run/docker.sock:/var/run/docker.sock:ro -v $(pwd)/docker.conf:/etc/nginx/conf.d/docker.conf:ro -p 2375:2375 sirrtea/nginx:alpine
360f9de7f8ddec500320363de706f4239f731692e2df55aaa9bbca6b01fa5e43
gerard@procyon:~/dockerproxy$
```

**AVISO**: El usuario **nginx** debe poder escribir a `/var/run/docker.sock` para que esto funcione.

El resultado es evidente: el comando `docker ps` (que utiliza un GET a `/v1.39/containers/json`), vería su acceso cortado.

```bash
gerard@aldebaran:~$ DOCKER_HOST=procyon docker ps
Error response from daemon: <html>
<head><title>403 Forbidden</title></head>
<body bgcolor="white">
<center><h1>403 Forbidden</h1></center>
<hr><center>nginx/1.14.2</center>
</body>
</html>
gerard@aldebaran:~$ 
```

El comando `docker network ls` (un GET a `/v1.39/networks`) funciona según lo esperado:

```bash
gerard@aldebaran:~$ DOCKER_HOST=procyon docker network ls
NETWORK ID          NAME                DRIVER              SCOPE
b92cd9288207        bridge              bridge              local
c4ecadf8c3d2        host                host                local
5d8f3437caa2        none                null                local
gerard@aldebaran:~$ 
```

Sin embargo, no se me permite hacer un `docker network create` (que es un POST a `/v1.39/networks/create`):

```bash
gerard@aldebaran:~$ DOCKER_HOST=procyon docker network create mynet
Error response from daemon: <html>
<head><title>403 Forbidden</title></head>
<body bgcolor="white">
<center><h1>403 Forbidden</h1></center>
<hr><center>nginx/1.14.2</center>
</body>
</html>
gerard@aldebaran:~$ 
```

## Usando un proxy reverso, de la forma fácil

Configurar el *proxy* es una tarea complicada, y mantener dicha configuración cuando la API va cambiando, es casi imposible. Eso nos obliga a buscar otras opciones de gente que ha tenido el mismo problema que yo; como no puede ser de otra manera, ya existen varios proyectos que nos pueden servir.

Especialmente interesante me parece la opción de [Tecnativa/docker-socket-proxy](https://github.com/Tecnativa/docker-socket-proxy), que utiliza la misma técnica que la anterior. El *proxy* en sí mismo es un **haproxy**, al que le añade un solo fichero de configuración. Este fichero es capaz de permitir o bloquear URLs y métodos en función de variables de entorno concretas.

```bash
$ docker container run \
    -d --privileged \
    --name dockerproxy \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -p 127.0.0.1:2375:2375 \
    tecnativa/docker-socket-proxy
```

Lo que no me gusta de esta imagen es que ejecuta como **root**, resolviendo la escritura al *unix socket* de una forma bastante poco elegante.
