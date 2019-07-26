---
title: "Un balanceador dinámico con consul-template"
slug: "un-balanceador-dinamico-con-consul-template"
date: 2018-05-07
categories: ['Sistemas']
tags: ['consul', 'service discovery', 'balanceador']
---

Aquellos que leéis mis artículos habitualmente ya sabéis lo que es un balanceador de carga, especialmente los de peticiones HTTP; en especial conocemos **nginx** y **haproxy**. La parte mala de estos servicios es que la configuración es estática e inmutable, y en un mundo *cloud*, eso no es lo ideal.<!--more-->

En el momento en que pasamos de servidores tradicionales al modelo *cloud*, nos damos cuenta que no es importante que el servidor X o el servidor Y funcionen; lo que queremos es **dar un servicio**, y no nos importan los servidores que sean; incluso podemos aumentar o decrementar su número con facilidad.

En estos casos, es muy conveniente tener un servicio de *discovery*, que nos sepa decir qué servidores tenemos y qué servicios hay alojados en ellos; **Consul** es uno de ellos, que ya vimos con anterioridad.

Sin embargo, seguimos teniendo que reconfigurar los balanceadores manualmente y recargando su configuración. Para ello se creó **consul-template**, que no es más que un proceso que se dedica a construir ficheros de configuración cuando **consul** le indica que ha habido un cambio relevante; en este momento, **consul-template** regenerará la configuración del servicio y opcionalmente lanzará un comando indicado.

Juntando nuestro servicio de balanceador con **consul-template** podemos conseguir fácilmente la ilusión de un balancear dinámico: **consul-template** regenerará la configuración del balanceador y lanzará el comando necesario para que el balanceador la recargue.

## Un ejemplo: balanceando peticiones web con HAProxy

Como decisión de diseño, y para simplificar vamos a ver el siguiente escenario:

* Tenemos un servidor web en *localhost:8001*.
* Tenemos un servidor web en *localhost:8002*.
* Vamos a exponer en *localhost:80* las peticiones, con **HAProxy** y con un algoritmo de *round-robin*.
* El balanceador es un contenedor **Docker**.
* **consul-template** también ejecuta como un contendor **Docker**.

De hecho, todo esto también sirve para otros servicios, como por ejemplo, **nginx**.

### Ejecutando consul

Lo primero es ejecutar un proceso **consul** con los servicios declarados y con sus respectivos *checks*:

```bash
gerard@atlantis:~/projects/services/consul$ cat consul.json
{
  "services": [
    { "id": "web1", "name": "web", "port": 8001 },
    { "id": "web2", "name": "web", "port": 8002 }
  ],
  "checks": [
    { "id": "web1", "service_id": "web1", "http": "http://localhost:8001/", "interval": "5s", "timeout": "5s" },
    { "id": "web2", "service_id": "web2", "http": "http://localhost:8002/", "interval": "5s", "timeout": "5s" }
  ]
}
gerard@atlantis:~/projects/services/consul$
```

Es especialmente crítico que ambos servicios y ambos *checks* tengan identificadores diferentes, porque sino, **consul** no los percibe como cosas diferentes.

```bash
gerard@atlantis:~/projects/services/consul$ ./consul agent -dev --advertise 10.0.2.15 -client 0.0.0.0 -config-file consul.json
==> Starting Consul agent...
==> Consul agent running!
           Version: 'v1.0.6'
           Node ID: '7d05eed1-f9db-2b02-499f-1bcdb37bf73c'
         Node name: 'atlantis'
        Datacenter: 'dc1' (Segment: '<all>')
            Server: true (Bootstrap: false)
       Client Addr: [0.0.0.0] (HTTP: 8500, HTTPS: -1, DNS: 8600)
      Cluster Addr: 10.0.2.15 (LAN: 8301, WAN: 8302)
           Encrypt: Gossip: false, TLS-Outgoing: false, TLS-Incoming: false

==> Log data will now stream in as it occurs:
...
```

Y lo dejamos funcionado.

### El balanceador y consul-template

El balanceador no tiene ningún misterio; se trata de un **haproxy** normal y corriente, con la única peculiaridad de que la carpeta */etc/haproxy/* es un volúmen, de forma que el contenedor de **consul-template** lo pueda exportar y escribir en él. De esta forma podemos "dar un cambiazo" al fichero de configuración desde otro contenedor.

Estaría bien tener en la imagen del balanceador un *script* que supiera como recargar la configuración del balanceador de forma fina y delicada, de forma que el otro contenedor simplemente ejecutaría un `docker exec` para "pedirle" que lo hiciera, sin entrar en detalles de como se hace. Para agilizar el artículo, nos limitaremos a hacer un `docker restart`, que no es ideal, pero nos vale de momento.

Por su parte, el contenedor que ejecuta **consul-template** tampoco tiene ningún misterio. Se limita a exportar la carpeta de configuración de **haproxy** y ejecutar **consul-template**, de forma continua y limitándose a crear `/etc/haproxy/haproxy.cfg` a partir de la información del **consul** local y la plantilla suministrada.

Si se diera el caso de un cambio en el servicio implicado, **consul-template** regeneraría la configuración de **haproxy**; como *bonus*, va a reiniciar el contenedor de **haproxy** para que este aplique la nueva configuración. No es la mejor manera de hacer las cosas, pero el "como reinicar un **haproxy**" no es la parte relevante del artículo.

**TRUCO**: Para más información de como controlar un contenedor alojado en el mismo *host* en que corre el nuestro, podemos seguir [este otro artículo]({{< relref "/articles/2018/04/controlando-docker-desde-un-contenedor.md" >}}).

El contenedor de **consul-template** solo tiene lo necesario para usar el comando `docker` y el mismo `consul-template`. Los añado como referencia:

```bash
gerard@atlantis:~/projects/balancer$ tree templater_build/
templater_build/
├── consul-template
└── Dockerfile

0 directories, 2 files
gerard@atlantis:~/projects/balancer$ cat templater_build/Dockerfile
FROM alpine:3.7
RUN apk add --no-cache docker && \
    rm /usr/bin/docker-proxy && \
    rm /usr/bin/docker-containerd-shim && \
    rm /usr/bin/docker-runc && \
    rm /usr/bin/docker-containerd-ctr && \
    rm /usr/bin/docker-containerd && \
    rm /usr/bin/dockerd
COPY consul-template /usr/bin/
gerard@atlantis:~/projects/balancer$
```

También añado como referencia el *docker-compose.yml* con el que se levantan ambos contenedores.

```bash
gerard@atlantis:~/projects/balancer$ cat docker-compose.yml
version: '2'
services:
  loadbalancer:
    image: sirrtea/haproxy:alpine
    container_name: balancer
    hostname: balancer
    network_mode: host
    volumes:
      - /etc/haproxy
  templater:
    image: templater
    container_name: templater
    hostname: templater
    network_mode: host
    volumes:
      - ./haproxy.ctmpl:/tmp/haproxy.ctmpl:ro
      - /var/run/docker.sock:/var/run/docker.sock
    volumes_from:
      - loadbalancer
    command: consul-template -template "/tmp/haproxy.ctmpl:/etc/haproxy/haproxy.cfg:docker restart balancer"
gerard@atlantis:~/projects/balancer$
```

Fijáos especialmente en:

* El volumen en */etc/haproxy/*, para poder compartir el fichero de configuración.
* El volumen */var/run/docker.sock* para controlar el servidor **docker** del *host*.
* La plantilla, que también se añade como volumen.
* Y como curiosidad, el comando **consul-template** necesario, con el comando de *restart* del contendor *balancer*.

La plantilla de **haproxy** tampoco tiene ninguna complejidad...

```bash
gerard@atlantis:~/projects/balancer$ cat haproxy.ctmpl
global
    chroot /var/lib/haproxy
    user haproxy
    group haproxy

defaults
    mode http

listen stats
    bind *:8080
    stats enable
    stats uri /

listen web
    bind *:80
    balance roundrobin
{{ range service "web" }}
    server {{ .ID }} {{ .Address }}:{{ .Port }}
{{ end }}
gerard@atlantis:~/projects/balancer$
```

### Resultado

Com ambos servicios *web* funcionando todo va como se espera (también lo podemos comprobar en la página de estadísticas de **haproxy**, en el puerto 8080):

```bash
gerard@atlantis:~/projects/balancer$ docker exec balancer cat /etc/haproxy/haproxy.cfg | grep server
    server web1 10.0.2.15:8001
    server web2 10.0.2.15:8002
gerard@atlantis:~/projects/balancer$ curl http://localhost:80/
web1
gerard@atlantis:~/projects/balancer$ curl http://localhost:80/
web2
gerard@atlantis:~/projects/balancer$ curl http://localhost:80/
web1
gerard@atlantis:~/projects/balancer$ curl http://localhost:80/
web2
gerard@atlantis:~/projects/balancer$
```

Si se cae, por ejemplo, el servicio *web1* en el puerto 8001, **consul** lo detecta. En este momento, **consul-template** regenera la configuración y reinica el contenedor *balancer*:

```bash
gerard@atlantis:~/projects/balancer$ docker exec balancer cat /etc/haproxy/haproxy.cfg | grep server
    server web2 10.0.2.15:8002
gerard@atlantis:~/projects/balancer$ curl http://localhost:80/
web2
gerard@atlantis:~/projects/balancer$ curl http://localhost:80/
web2
gerard@atlantis:~/projects/balancer$ curl http://localhost:80/
web2
gerard@atlantis:~/projects/balancer$
```

Se cae el servicio *web2*, y nos quedamos sin servicio completamente, pero la configuración queda como se espera:

```bash
gerard@atlantis:~/projects/balancer$ docker exec balancer cat /etc/haproxy/haproxy.cfg | grep server
gerard@atlantis:~/projects/balancer$ curl http://localhost:80/
<html><body><h1>503 Service Unavailable</h1>
No server is available to handle this request.
</body></html>
gerard@atlantis:~/projects/balancer$
```

Solo nos quedaría restablecer el servicio tanto en *web1* como en *web2*, y verificar que el servicio global se restablece:

```bash
gerard@atlantis:~/projects/balancer$ docker exec balancer cat /etc/haproxy/haproxy.cfg | grep server
    server web1 10.0.2.15:8001
    server web2 10.0.2.15:8002
gerard@atlantis:~/projects/balancer$ curl http://localhost:80/
web1
gerard@atlantis:~/projects/balancer$ curl http://localhost:80/
web2
gerard@atlantis:~/projects/balancer$ curl http://localhost:80/
web1
gerard@atlantis:~/projects/balancer$ curl http://localhost:80/
web2
gerard@atlantis:~/projects/balancer$
```

El siguiente paso sería añadir nuevos nodos con **consul** para observar como la configuración de **hoproxy** crece. De esta forma, no tendremos que preocuparnos de la configuración del balanceador nunca más; solamente de tener la plantilla actualizada si añadimos más aplicaciones.
