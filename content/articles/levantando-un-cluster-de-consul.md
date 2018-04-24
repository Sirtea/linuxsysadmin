Title: Levantando un cluster de consul
Slug: levantando-un-cluster-de-consul
Date: 2018-04-30 10:00
Category: Sistemas
Tags: consul, service discovery, cluster



Ya vimos que **consul** nos permitía mantener una foto del estado de nuestros servidores y de los servicios que corren en ellos. Es todavía más importante cuando contamos con varios servidores, y todos declaran sus partes a un servidor central, de forma que tenemos una foto global de la situación.

Para este ejemplo, vamos a contar con 3 servidores; uno de los cuales va a actuar de *servidor* y el resto harán de *clientes*. Los servidores son:

* **node1** &rarr; Dirección IP 10.0.0.2 (será el *servidor*)
* **node2** &rarr; Dirección IP 10.0.0.3 (será un *cliente*)
* **node3** &rarr; Dirección IP 10.0.0.4 (será un *cliente*)

**NOTA**: Es posible poner varios *servidores* para obtener alta disponibilidad, pero al no ser un servício crítico, no vamos a extender el artículo innecesariamente.

## Instalación

Ya vimos en [otro articulo]({filename}/articles/monitorizacion-y-service-discovery-con-consul.md) que **consul** no necesita instalación, ya que es un binario estático. Para su fácil distribución entre las máquinas, lo he empaquetado en una imagen de **docker**, acompañado de una carpeta */data/* que es donde **consul** deja sus ficheros operativos. Vamos a inyectar la configuración desde el servidor mediante *host volumes*.

Para tener el artículo completo, adjunto el contexto con el que se contruyó la imagen que usamos en el mismo.

```bash
gerard@atlantis:~/projects/consul/build$ cat Dockerfile
FROM scratch
ADD rootfs.tar.gz /
ENTRYPOINT ["/consul"]
gerard@atlantis:~/projects/consul/build$ tar tf rootfs.tar.gz
consul
data/
gerard@atlantis:~/projects/consul/build$
```

Esto nos deja una imagen de unos 28mb. He usado el *tag* `sirrtea/consul:1.0.5` y lo he subido de forma temporal a [DockerHub](https://hub.docker.com/), que va a funcionar como repositorio de imágenes. No hace falta decir que 1.0.5 es la versión de **consul** en el momento de escribir el artículo...

**TRUCO**: Los *clientes* son volátiles; no necesitamos persistir su carpeta de datos porque no guardan nada importante. Sin embargo, la carpeta */data/* de los servidores guardan información importante del *cluster* y debe asegurarse que no se pierden en el reinicio del contenedor.

## Levantando el master

Ponemos en **node1** un carpeta con el fichero *docker-compose.yml* y la configuración vacía, en donde lo tendremos todo ordenado.

Es importante recalcar que la configuración la mapeamos desde el *host* y también la carpeta de datos, para que al reiniciar el contenedor no de pierda. Si eso pasara, habría que volver a añadir manualmente todos los otros nodos.

```bash
gerard@node1:~/consul$ cat docker-compose.yml
version: '2'
services:
  consul:
    image: sirrtea/consul:1.0.5
    container_name: consul
    hostname: consul
    network_mode: host
    volumes:
      - ./consul.json:/consul.json
      - ./data:/data
    command: agent -node node1 -advertise 10.0.0.2 -data-dir /data --config-file /consul.json -server -bootstrap-expect=1
    restart: always
gerard@node1:~/consul$ cat consul.json
{}
gerard@node1:~/consul$
```

Levantamos el servidor con **docker-compose** de la forma habitual:

```bash
gerard@node1:~/consul$ docker-compose up -d
Creating consul ... done
gerard@node1:~/consul$
```

Podemos ver que el *cluster* solo tiene el servidor, ya que no hemos puesto otros nodos:

```bash
gerard@node1:~/consul$ docker exec consul /consul members
Node   Address        Status  Type    Build  Protocol  DC   Segment
node1  10.0.0.2:8301  alive   server  1.0.5  2         dc1  <all>
gerard@node1:~/consul$
```

Solo nos queda por ver que el *servidor* asume el rol de *leader*:

```bash
gerard@node1:~/consul$ docker-compose logs | grep -o "New leader elected.*"
New leader elected: node1
gerard@node1:~/consul$
```

## Añadiendo los clientes

De forma similar, vamos a crear una carpeta en **node2** y en **node3** (y en un futuro en el resto de nodos) para contener el fichero *docker-compose.yml* y la configuración de **consul**.

Vamos a poner una configuración vacía; más adelante ya añadiremos servicios y *health checks*.

```bash
gerard@node2:~/consul$ cat docker-compose.yml
version: '2'
services:
  consul:
    image: sirrtea/consul:1.0.5
    container_name: consul
    hostname: consul
    network_mode: host
    volumes:
      - ./consul.json:/consul.json
    command: agent -node node2 -advertise 10.0.0.3 -data-dir /data --config-file /consul.json -join node1
    restart: always
gerard@node2:~/consul$ cat consul.json
{}
gerard@node2:~/consul$
```

**TRUCO**: La operación de *join* se puede hacer en el comando de inicio o manualmente *a posteriori*; la primera forma nos simplifica bastante el trabajo.

Levantamos el contenedor de **consul** y verificamos que el *cluster* conoce al nuevo miembro:

```bash
gerard@node2:~/consul$ docker-compose up -d
Creating consul ... done
gerard@node2:~/consul$
```

```bash
gerard@node1:~/consul$ docker exec consul /consul members
Node   Address        Status  Type    Build  Protocol  DC   Segment
node1  10.0.0.2:8301  alive   server  1.0.5  2         dc1  <all>
node2  10.0.0.3:8301  alive   client  1.0.5  2         dc1  <default>
gerard@node1:~/consul$
```

Repetimos lo mismo para el **node3** (cuidado con la IP de *advertise*)

```bash
gerard@node1:~/consul$ docker exec consul /consul members
Node   Address        Status  Type    Build  Protocol  DC   Segment
node1  10.0.0.2:8301  alive   server  1.0.5  2         dc1  <all>
node2  10.0.0.3:8301  alive   client  1.0.5  2         dc1  <default>
node3  10.0.0.4:8301  alive   client  1.0.5  2         dc1  <default>
gerard@node1:~/consul$
```

La misma verificación se puede hacer solicitando la dirección de los nuevos nodos:

```bash
gerard@node1:~/consul$ dig @127.0.0.1 -p 8600 node1.node.consul +short
10.0.0.2
gerard@node1:~/consul$ dig @127.0.0.1 -p 8600 node2.node.consul +short
10.0.0.3
gerard@node1:~/consul$ dig @127.0.0.1 -p 8600 node3.node.consul +short
10.0.0.4
gerard@node1:~/consul$
```

## Añadiendo servicios

Supongamos ahora que queremos declarar un servicio *web* en **node1** y **node2**. Simplemente vamos a añadir una configuración adecuada y a reiniciar el contenedor de **consul**.

A pesar de que **node1** es un *servidor* y **node2** es un *cliente*, eso solo afecta a la mecánica del *cluster*. Siguen siendo dos *agentes* normales a todos los efectos; se configuran y se operan de la misma forma.

```bash
gerard@node1:~/consul$ cat consul.json
{
  "services": [
    { "id": "web", "name": "web", "port": 8080 }
  ],
  "checks": [
    { "id": "web", "name": "web", "service_id": "web", "http": "http://localhost:8080/", "interval": "5s", "timeout": "5s" }
  ]
}
gerard@node1:~/consul$ docker-compose restart
Restarting consul ... done
gerard@node1:~/consul$
```

**TRUCO**: al tener la carpeta */data/* en el *host* en donde corre el *servidor*, no perdemos la lista de *clientes*.

```bash
gerard@node1:~/consul$ docker exec consul /consul members
Node   Address        Status  Type    Build  Protocol  DC   Segment
node1  10.0.0.2:8301  alive   server  1.0.5  2         dc1  <all>
node2  10.0.0.3:8301  alive   client  1.0.5  2         dc1  <default>
node3  10.0.0.4:8301  alive   client  1.0.5  2         dc1  <default>
gerard@node1:~/consul$
```

Y lo mismo para **node2**:

```bash
gerard@node2:~/consul$ cat consul.json
{
  "services": [
    { "id": "web", "name": "web", "port": 8080 }
  ],
  "checks": [
    { "id": "web", "name": "web", "service_id": "web", "http": "http://localhost:8080/", "interval": "5s", "timeout": "5s" }
  ]
}
gerard@node2:~/consul$ docker-compose restart
Restarting consul ... done
gerard@node2:~/consul$
```

Solo nos queda por observar que el servidor DNS integrado nos devuelve ambos, ya que están saludables:

```bash
gerard@node1:~/consul$ dig @127.0.0.1 -p 8600 web.service.consul +short
10.0.0.2
10.0.0.3
gerard@node1:~/consul$
```

## Caídas e incrementos de servicio

Si se cayera, por ejemplo, la web de **node1**, el servidor DNS no la devolvería, al no estar saludable:

```bash
gerard@node1:~/consul$ dig @127.0.0.1 -p 8600 web.service.consul +short
10.0.0.3
gerard@node1:~/consul$
```

Este detalle hace que podamos añadir el servicio en otro nodo **antes** del mismo servicio. Como la web no funciona, **consul** no devolvería el nuevo nodo hasta que la web estuviera instalada, funcionando y saludable.

Así pues, vamos a declarar el servicio *web* también en **nodo3**:

```bash
gerard@node3:~/consul$ cat consul.json
{
  "services": [
    { "id": "web", "name": "web", "port": 8080 }
  ],
  "checks": [
    { "id": "web", "name": "web", "service_id": "web", "http": "http://localhost:8080/", "interval": "5s", "timeout": "5s" }
  ]
}
gerard@node3:~/consul$ docker-compose restart
Restarting consul ... done
gerard@node3:~/consul$
```

Y sin sorpresas, el servidor DNS (y la API) de **consul** no nos devolverían las 3 direcciones, ya que la tercera no funciona.

```bash
gerard@node1:~/consul$ dig @127.0.0.1 -p 8600 web.service.consul +short
10.0.0.3
10.0.0.2
gerard@node1:~/consul$
```

Solo nos faltaría levantar la web en el **nodo3** para que el servidor nos devolviera este nodo como proveedor del servicio *web*.

```bash
gerard@node1:~/consul$ dig @127.0.0.1 -p 8600 web.service.consul
...
;; QUESTION SECTION:
;web.service.consul.            IN      A

;; ANSWER SECTION:
web.service.consul.     0       IN      A       10.0.0.4
web.service.consul.     0       IN      A       10.0.0.3
web.service.consul.     0       IN      A       10.0.0.2

;; Query time: 0 msec
;; SERVER: 127.0.0.1#8600(127.0.0.1)
...
gerard@node1:~/consul$
```

A partir de ahora, es responsabilidad del que use este DNS elegir una entre las respuestas dadas.
