---
title: "Monitorización y service discovery con Consul"
slug: "monitorizacion-y-service-discovery-con-consul"
date: 2018-04-23
categories: ['Operaciones']
tags: ['consul', 'service discovery', 'monitoring']
---

Hace poco me topé con una excelente pieza de *software* llamada **Consul**. Se trata de un binario que proporciona varios servicios: *node autodiscovery*, *service autodiscovery*, *health checking* y almacén de valores *key-value*. Todo ello mostrado en una interfaz web y suministrando un servidor DNS y una API que podemos usar.<!--more-->

La idea es que todo servidor de tu infraestructura ejecuta un agente de **Consul**, y tras un protocolo de *gossip*, todos saben el estado general de nuestra infraestructura.

Aunque es muy interesante tener uno o varios *server nodes* y varios *client nodes*, esto queda abierto para un artículo posterior. De momento nos vamos a limitar a tener un *server node* para demostración y desarrollo local.

## Instalación

**Consul** no necesita instalación; es un solo binario estático que solo tenemos que descargar de la [página de descargas](https://www.consul.io/downloads.html) y ejecutar.

En mi caso, y dada mi arquitectura **Linux** de 64 bits, me descargo el apropiado:

```bash
gerard@atlantis:~/projects/consul$ wget https://releases.hashicorp.com/consul/1.0.3/consul_1.0.3_linux_amd64.zip
--2018-02-02 13:29:34--  https://releases.hashicorp.com/consul/1.0.3/consul_1.0.3_linux_amd64.zip
Conectando con 192.168.62.4:3128... conectado.
Petición Proxy enviada, esperando respuesta... 200 OK
Longitud: 11102212 (11M) [application/zip]
Grabando a: “consul_1.0.3_linux_amd64.zip”

consul_1.0.3_linux_amd64.zip    100%[=======================================================>]  10,59M  1,29MB/s    in 6,4s

2018-02-02 13:29:41 (1,66 MB/s) - “consul_1.0.3_linux_amd64.zip” guardado [11102212/11102212]

gerard@atlantis:~/projects/consul$
```

Es un fichero *.zip* que solamente contiene el binario indicado.

```bash
gerard@atlantis:~/projects/consul$ unzip -l consul_1.0.3_linux_amd64.zip
Archive:  consul_1.0.3_linux_amd64.zip
  Length      Date    Time    Name
---------  ---------- -----   ----
 46660030  2018-01-24 16:06   consul
---------                     -------
 46660030                     1 file
gerard@atlantis:~/projects/consul$
```

Solo necesitamos extraer el contenido del fichero *.zip* y ponerlo en algún lugar del *path*, o simplemente ejecutarlo con el formato `./consul` que es lo que yo voy a hacer.

**TRUCO**: El binario viene con los símbolos de *debug*. Se puede reducir de 45mb a 26mb haciendo un `strip consul`.

## Ejecución en modo de desarrollo

Todos los agentes de consul son servidores o clientes de un *cluster* más grande. Sin embargo, y con el único objeto de probar y escribir una configuración útil, se nos ofrece la posibilidad de levantar el agente en modo de desarrollo.

Esto significa que ejecuta en memoria, sin necesidad de una carpeta local para escribir ninguna información de *runtime*, que se levanta como un *cluster* de un solo nodo y que levanta la interfaz web, lo que nos viene de perlas para la demostración.

**NOTA**: En un artículo futuro hablaremos de un *cluster* adecuado que implique varios nodos.

Así sin más, lanzamos el comando; no es necesario nada más para algo simple.

```bash
gerard@atlantis:~/projects/consul$ ./consul agent -dev
==> Starting Consul agent...
==> Consul agent running!
           Version: 'v1.0.3'
           Node ID: '2feeb781-3422-98ef-1938-e5b8494de0dc'
         Node name: 'atlantis'
        Datacenter: 'dc1' (Segment: '<all>')
            Server: true (Bootstrap: false)
       Client Addr: [127.0.0.1] (HTTP: 8500, HTTPS: -1, DNS: 8600)
      Cluster Addr: 127.0.0.1 (LAN: 8301, WAN: 8302)
           Encrypt: Gossip: false, TLS-Outgoing: false, TLS-Incoming: false

==> Log data will now stream in as it occurs:
...
```

**TRUCO**: Se recomienda usar el *flag* `-advertise` para que sepa cual es la dirección que queremos usar para el *cluster*. **Consul** intenta detectarla por sí mismo, pero es fácil que no lo haga como esperamos; es mejor indicarlo explícitamente.

Esto nos levanta otros dos servicios en *localhost* y en diferentes puertos (tanto la IP como los puertos son configurables):

* Un servidor DNS en el puerto 8600
* Una bonita interfaz web en el puerto 8500, y una API en el mismo puerto

Probemos el DNS; solo hay que saber que el nombre en el DNS se saca añadiendo al *hostname* el infijo *.node* y el sufijo *.consul* (configurable también).

```bash
gerard@atlantis:~$ dig @127.0.0.1 -p 8600 atlantis.node.consul

; <<>> DiG 9.10.3-P4-Debian <<>> @127.0.0.1 -p 8600 atlantis.node.consul
; (1 server found)
;; global options: +cmd
;; Got answer:
;; ->>HEADER<<- opcode: QUERY, status: NOERROR, id: 4332
;; flags: qr aa rd; QUERY: 1, ANSWER: 1, AUTHORITY: 0, ADDITIONAL: 1
;; WARNING: recursion requested but not available

;; OPT PSEUDOSECTION:
; EDNS: version: 0, flags:; udp: 4096
;; QUESTION SECTION:
;atlantis.node.consul.          IN      A

;; ANSWER SECTION:
atlantis.node.consul.   0       IN      A       10.0.2.15

;; Query time: 0 msec
;; SERVER: 127.0.0.1#8600(127.0.0.1)
;; WHEN: Thu Feb 08 12:28:38 CET 2018
;; MSG SIZE  rcvd: 65

gerard@atlantis:~$
```

La interfaz web la podemos abrir en un navegador en <http://localhost:8500/> y sería algo como esto:

![Consul UI](/images/consul-ui.png)

## Declarando servicios

Vamos a levantar el agente de la misma forma, pero con el *flag* `-config-file`, lo que nos permite poner una configuración específica a nuestras necesidades.

```bash
gerard@atlantis:~/projects/consul$ ./consul agent -dev -advertise 10.0.2.15 --config-file consul.json
==> Starting Consul agent...
==> Consul agent running!
           Version: 'v1.0.3'
           Node ID: '183c31b0-33aa-e4f4-ef77-fb844b371403'
         Node name: 'atlantis'
        Datacenter: 'dc1' (Segment: '<all>')
            Server: true (Bootstrap: false)
       Client Addr: [127.0.0.1] (HTTP: 8500, HTTPS: -1, DNS: 8600)
      Cluster Addr: 10.0.2.15 (LAN: 8301, WAN: 8302)
           Encrypt: Gossip: false, TLS-Outgoing: false, TLS-Incoming: false

==> Log data will now stream in as it occurs:
...
```

El fichero de configuración declara servicios, en formato JSON; este es el ejemplo que he usado:

```bash
gerard@atlantis:~/projects/consul$ cat consul.json
{
  "services": [
    { "id": "web", "name": "web", "port": 8001 },
    { "id": "api", "name": "api", "port": 8002 }
  ]
}
gerard@atlantis:~/projects/consul$
```

Ambos servicios van a aparecer en la interfaz web y en la resolución DNS:

```bash
gerard@atlantis:~$ dig @127.0.0.1 -p 8600 web.service.consul

; <<>> DiG 9.10.3-P4-Debian <<>> @127.0.0.1 -p 8600 web.service.consul
; (1 server found)
;; global options: +cmd
;; Got answer:
;; ->>HEADER<<- opcode: QUERY, status: NOERROR, id: 21560
;; flags: qr aa rd; QUERY: 1, ANSWER: 1, AUTHORITY: 0, ADDITIONAL: 1
;; WARNING: recursion requested but not available

;; OPT PSEUDOSECTION:
; EDNS: version: 0, flags:; udp: 4096
;; QUESTION SECTION:
;web.service.consul.            IN      A

;; ANSWER SECTION:
web.service.consul.     0       IN      A       10.0.2.15

;; Query time: 0 msec
;; SERVER: 127.0.0.1#8600(127.0.0.1)
;; WHEN: Thu Feb 08 12:40:37 CET 2018
;; MSG SIZE  rcvd: 63

gerard@atlantis:~$ dig @127.0.0.1 -p 8600 api.service.consul

; <<>> DiG 9.10.3-P4-Debian <<>> @127.0.0.1 -p 8600 api.service.consul
; (1 server found)
;; global options: +cmd
;; Got answer:
;; ->>HEADER<<- opcode: QUERY, status: NOERROR, id: 6767
;; flags: qr aa rd; QUERY: 1, ANSWER: 1, AUTHORITY: 0, ADDITIONAL: 1
;; WARNING: recursion requested but not available

;; OPT PSEUDOSECTION:
; EDNS: version: 0, flags:; udp: 4096
;; QUESTION SECTION:
;api.service.consul.            IN      A

;; ANSWER SECTION:
api.service.consul.     0       IN      A       10.0.2.15

;; Query time: 0 msec
;; SERVER: 127.0.0.1#8600(127.0.0.1)
;; WHEN: Thu Feb 08 12:40:38 CET 2018
;; MSG SIZE  rcvd: 63

gerard@atlantis:~$
```

**TRUCO**: Si los servicios se declaran en varios nodos del *cluster*, el DNS nos va a devolver varias respuestas, indicando todas las direcciones IP en donde esté el servicio.

## Declarando health checks

Los *health checks* nos permiten indicar a **consul** si el nodo o sus servicios están funcionales. Esto se refleja en la web y en la resolución DNS, de forma que no se nos responde una IP si esta no está bien.

Hay varios modelos de *checks*, de acuerdo con [la documentación](https://www.consul.io/docs/agent/checks.html). Además, estos *checks* pueden estar opcionalemente ligados a un servicio.

* Si falla un *check* ligado a un servicio, dicho servicio se da por malo.
* Si falla un *check* que no está ligado a ningún servicio, el nodo (servidor) entero se da por malo.

Veamos un ejemplo:

```bash
gerard@atlantis:~/projects/consul$ cat consul.json
{
  "services": [
    { "id": "web", "name": "web", "port": 8001 },
    { "id": "api", "name": "api", "port": 8002 }
  ],
  "checks": [
    { "id": "ssh", "tcp": "localhost:22", "interval": "5s", "timeout": "5s" },
    { "id": "web", "name": "web", "service_id": "web", "http": "http://localhost:8001/", "interval": "5s", "timeout": "5s" },
    { "id": "api", "name": "api", "service_id": "api", "http": "http://localhost:8002/", "interval": "5s", "timeout": "5s" }
  ]
}
gerard@atlantis:~/projects/consul$
```

En este caso, los *checks* ligados a servicios son el de web y el de la API. Esto se consigue mediante el parámetro *service_id*, que referencia al parámetro *id* del servicio.

Supongamos que el *check* del servicio web falla, lo que simularemos parando el servidor web.

```bash
gerard@atlantis:~$ dig @127.0.0.1 -p 8600 atlantis.node.consul +short
10.0.2.15
gerard@atlantis:~$ dig @127.0.0.1 -p 8600 web.service.consul +short
gerard@atlantis:~$ dig @127.0.0.1 -p 8600 api.service.consul +short
10.0.2.15
gerard@atlantis:~$
```

Como podemos apreciar, el servicio web que no está funcionando, no se computa por **consul** como bueno, por lo que lo quita de las respuestas. Eso no afecta a los otros servicios o al nodo mismo.

Así pues, si tenemos el servicio en 4 servidores y uno se cae, **consul** lo sabrá; y por lo tanto, solo va a devolver los 3 que quedan activos. Lo mismo pasa cuando el servicio se recupere.

Si consumimos directamente este DNS, podemos ahorrarnos un balanceador; cada cliente es responsable de elegir una de las direcciones de la respuesta aleatoriamente.

## Conclusión

Teniendo una foto del estado de nuestros servicios, las posibilidades son infinitas:

* Podemos monitorizar directamente con la interfaz web
* Podemos consumir la API de **consul** con fines de automatización reactiva (por ejemplo notificando de alguna manera desde un *script*)
* Podemos limitarnos a usar el DNS
* Incluso podemos generar las configuraciones de un balanceador de forma automática usando la API, aunque eso es otra historia.
