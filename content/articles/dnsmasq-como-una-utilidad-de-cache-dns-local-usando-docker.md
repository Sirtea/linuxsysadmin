Title: DNSmasq como una utilidad de cache DNS local usando Docker
Slug: dnsmasq-como-una-utilidad-de-cache-dns-local-usando-docker
Date: 2018-10-01 10:00
Category: Sistemas
Tags: dnsmasq, docker



Ya vimos en otros artículos lo fácilmente que podemos utilizar **dnsmasq** en un *gateway* para ayudar a los servidores a que se conozcan entre sí por nombre y como una forma de ocultar el DNS real de la red interna. Sin embargo es una caché excelente para un sistema aislado.

Cualquier sistema, sea un servidor o no, puede utilizar un proceso **dnsmasq** local como caché y como forma de resolver por nombre entornos que todavia no tienen un DNS disponible en internet. Realmente es un proceso que no consume casi ninguna memoria y nos puede ayudar mucho en caso de una caída del DNS global, o en caso de desconectarnos de la red por cualquier motivo.

Lo que suele ser problemático es instalarlo en nuestro sistema, por un tema de permisos o de conflictos; en estos casos podemos confiar en convertirlo en un contenedor, que no pasa de los 5mb de disco.

## La imagen con DNSmasq

La imagen en sí misma no oculta ninguna complicación; se trata de instalar **dnsmasq** en nuestro sistema base y asegurarnos que ejectua en *foreground*. Para evitar una imagen muy grande, podemos utilizar **Alpine Linux**.

```bash
gerard@atlantis:~/workspace/dnsmasq$ cat build/Dockerfile
FROM alpine:3.8
RUN apk add --no-cache dnsmasq
CMD ["/usr/sbin/dnsmasq", "-k"]
gerard@atlantis:~/workspace/dnsmasq$
```

Para construir y levantar el servicio, podemos utilizar **docker-compose**:

```bash
gerard@atlantis:~/workspace/dnsmasq$ cat docker-compose.yml
version: '3'
services:
  dnsmasq:
    image: dnsmasq
    build: build
    container_name: dnsmasq
    hostname: dnsmasq
    cap_add:
      - NET_ADMIN
    network_mode: host
    restart: always
    volumes:
      - ./hosts:/etc/hosts:ro
gerard@atlantis:~/workspace/dnsmasq$
```

```bash
gerard@atlantis:~/workspace/dnsmasq$ docker-compose build
Building dnsmasq
...
Successfully tagged dnsmasq:latest
gerard@atlantis:~/workspace/dnsmasq$ docker images
REPOSITORY          TAG                 IMAGE ID            CREATED             SIZE
...
dnsmasq             latest              b43fd1b79394        7 minutes ago       4.76MB
...
gerard@atlantis:~/workspace/dnsmasq$
```

Y con esto tenemos nuestra imagen.

## Ejecutando el contenedor

Como decisión de diseño, he preferido montar el fichero `/etc/hosts` desde una carpeta local, para poder modificarlo a placer y sin tener permisos de superusuario.

Levantamos el servicio encima de la red local; de esta forma, crearemos la ilusión de que **dnsmasq** corre en la misma máquina que la va a utilizar directamente en *localhost*.

**NOTA**: **dnsmasq** utiliza algunas operaciones especiales de redes. Podéis ejecutar en modo privilegiado (`--privileged`) o podéis darle la *capability* `NET_ADMIN`.

```bash
gerard@atlantis:~/workspace/dnsmasq$ docker-compose up -d
Creating dnsmasq ... done
gerard@atlantis:~/workspace/dnsmasq$
```

Y con esto tenemos el servicio **dnsmasq** accesible desde nuestro servidor, en el puerto estándar:

```bash
gerard@atlantis:~/workspace/dnsmasq$ ss -lnt | grep 53
LISTEN     0      32           *:53                       *:*
LISTEN     0      32          :::53                      :::*
gerard@atlantis:~/workspace/dnsmasq$
```

## Utilizando el nuevo servidor DNS

Solo falta indicar que el servidor DNS que nuestra máquina debe utilizar es *localhost* en `/etc/resolv.conf`, posiblemente seguido de otros. De esta forma, la primera petición DNS fallará, se irá a buscar en el siguiente servidor, y se guardará en *caché*.

```bash
gerard@atlantis:~/workspace/dnsmasq$ cat /etc/resolv.conf
domain ...
search ...
nameserver 127.0.0.1
nameserver ...
nameserver ...
gerard@atlantis:~/workspace/dnsmasq$
```

En el caso de utilizar DHCP para obtener dirección IP automáticamente, el fichero `/etc/resolv.conf` se sobreescribe con lo que nos pase el *router*. Podemos instruir al cliente de DHCP para que siempre nos añada *localhost* en el fichero (es lo que tuve que hacer yo).

```bash
gerard@atlantis:~/workspace/dnsmasq$ cat /etc/dhcp/dhclient.conf 
...
prepend domain-name-servers 127.0.0.1;
gerard@atlantis:~/workspace/dnsmasq$
```

## Probando el servidor DNS

El paso más interesante de este *setup* es la capacidad de *cachear* las peticiones DNS, y esto lo podemos probar haciendo simplemente varias peticiones:

```bash
root@atlantis:~# dig www.linuxsysadmin.ml
...
;; Query time: 30 msec
;; SERVER: 127.0.0.1#53(127.0.0.1)
...
root@atlantis:~# dig www.linuxsysadmin.ml
...
;; Query time: 0 msec
;; SERVER: 127.0.0.1#53(127.0.0.1)
...
root@atlantis:~# dig www.linuxsysadmin.ml
...
;; Query time: 0 msec
;; SERVER: 127.0.0.1#53(127.0.0.1)
...
root@atlantis:~#
```

Podemo ver claramente dos cosas:

* Estamos utilizando nuestro servidor local DNS
* La primera petición no está en *caché* y tarda un poco, pero el resto son inmediatas

La otra funcionalidad que ganamos con **dnsmasq** es la de resolver nombres desde el fichero `/etc/hosts` del contenedor. Para evitarme modificar sistemas de ficheros privilegiados, el *docker-compose.yml* añade este fichero desde un fichero local, que podemos modificar a placer segun nuestros gustos (no os olvidéis de reiniciar el contenedor para que pille los cambios).

```bash
gerard@atlantis:~/workspace/dnsmasq$ cat hosts
127.0.0.1 test.api.local
10.0.0.3 auth.api.private
gerard@atlantis:~/workspace/dnsmasq$ docker-compose restart
Restarting dnsmasq ... done
gerard@atlantis:~/workspace/dnsmasq$
```

Y con esto podemos resolver dominios que no existen fuera de nuestra red, con la comodidad de hacerlo por nombre, y sin modificar direcciones IP si los recolocamos en otros servidores.

```bash
root@atlantis:~# dig test.api.local +short
127.0.0.1
root@atlantis:~# dig auth.api.private +short
10.0.0.3
root@atlantis:~#
```

Y con esto ya podemos decir que lo tenemos todo funcionando.
