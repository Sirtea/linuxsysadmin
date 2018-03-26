Title: Compartiendo Docker namespaces
Slug: compartiendo-docker-namespaces
Date: 2018-04-03 10:00
Category: Operaciones
Tags: docker, namespaces, keepalived, haproxy



Como ya sabéis, la tecnología **docker** me encanta; seguía con mi cruzada para *dockerizar* todos mis sistemas, cuando me topé con [un artículo antiguo]({filename}/articles/alta-disponibilidad-con-keepalived.md). En este artículo os contaré los problemas con los que me enfrenté en esta tarea y como los pude superar, explicando lo aprendido en el proceso.

No soy fan de meter varios procesos en el mismo contenedor, así que quise intentar una aproximación de varios contenedores, uno por proceso, levantados mediante **docker-compose**.

El proceso *keepalived* en si mismo no tiene mucha complicación, solo hay que tener en cuenta dos cosas:

* Al gestionar una IP flotante del *host* el contenedor debe estar en su misma red, con la que vamos a necesitar el *flag* `--net=host`
* El otro asunto peliagudo es que un contenedor no puede manejar la parte de redes por permisos, y por lo tanto debe lanzarse con el *flag* `--privileged` o con la *capability* `NET_ADMIN`, que es lo mínimo necesario.

El problema lo tenemos cuando queremos ejecutar el *check* de *keepalived* referente al proceso hermano **nginx** o **haproxy**. Solamente la idea de tener que hacer un **kill** a un proceso de otro contenedor era suficiente para desistir, ya que los procesos de un contenedor no se ven con los de otro. **¿O si?**

El truco está en el *flag* `--pid` que como indica la página de ayuda, gestiona el "PID namespace to use". Esto nos permite ejecutar un contenedor en el espacio de PIDs de otro, de forma que los procesos de ambos contenedores se ven entre sí, aunque solo uno de ellos puede ser el proceso 1 inicial, y la caída de este ocasiona la parada de ambos contenedores.

## Un ejemplo práctico: keepalived y haproxy

Vamos a hacer un par de instancias de **keepalived** en dos *hosts* distintos, y cada uno de ellos también va a tener un **haproxy**.

### Las imágenes

La imagen de **keepalived** no tiene misterios; cualquier sistema operativo con **keepalived** instalado nos vale. Adicionalmente, lo vamos a iniciar mediante un *script* que va a generar la configuración, en base a unas variables de entorno, que nos van a servir para discernir entre las configuraciones del *master* y del *slave*.

```bash
gerard@atlantis:~/projects/ha-loadbalancer$ cat keepalived/Dockerfile
FROM alpine:3.7
RUN apk add --no-cache keepalived
COPY start.sh /
CMD ["/start.sh"]
gerard@atlantis:~/projects/ha-loadbalancer$ cat keepalived/start.sh
#!/bin/sh

echo """\
vrrp_script chk_${SERVICE} {
      script \"/bin/busybox killall -0 ${SERVICE}\"
      interval ${CHECK_INTERVAL}
      weight ${CHECK_WEIGHT}
}

vrrp_instance VI_1 {
      interface ${INTERFACE}
      state ${STATE}
      virtual_router_id ${VIRTUAL_ROUTER}
      priority ${PRIORITY}
      virtual_ipaddress {
           ${VIP}
      }
      track_script {
           chk_${SERVICE}
      }
}""" > /etc/keepalived/keepalived.conf

exec /usr/sbin/keepalived -l -n
gerard@atlantis:~/projects/ha-loadbalancer$
```

Construiremos la imagen bajo el *tag* `sirrtea/keepalived:alpine` para su uso futuro.

La imagen de **haproxy** no es especial, y podemos utilizar cualquiera que ya tengamos, por ejemplo, [esta](https://hub.docker.com/r/sirrtea/haproxy/).

### Desplegando las imágenes

Por comodidad, vamos a utilizar **docker-compose** que levante el conjunto de **kepalived** y **haproxy**, uno en cada *host*. Es importante recalcar que la directiva `pid` solo funciona con la versión 2.1 o superior de **docker-compose**.

**TRUCO**: Vamos a levantar el **nginx** en el *namespace* de **keepalived**. esto se hace así porque **keepalived** no se va a caer y puede comprobar si el **haproxy** está corriendo o no. De hacerlo al revés, la caída del **haproxy** (que sería el PID 1), causaría el fin del contenedor, y la parada de todos los procesos del *namespace*, incluyendo **keepalived**. Esto que haría que el *check* del servicio **haproxy** no sirviera de nada.

#### El host master

```bash
gerard@atlantis:~/projects/ha-loadbalancer$ cat master/docker-compose.yml
version: '2.1'
services:
  keepalived:
    image: sirrtea/keepalived:alpine
    container_name: keepalived
    hostname: keepalived
    environment:
      SERVICE: haproxy
      CHECK_INTERVAL: 2
      CHECK_WEIGHT: 2
      INTERFACE: enp0s3
      STATE: MASTER
      VIRTUAL_ROUTER: 51
      PRIORITY: 11
      VIP: 10.0.0.2
    network_mode: host
    cap_add:
      - NET_ADMIN
  haproxy:
    image: sirrtea/haproxy:alpine
    container_name: haproxy
    hostname: haproxy
    pid: "service:keepalived"
    ports:
      - "80:8080"
    depends_on:
      - keepalived
gerard@atlantis:~/projects/ha-loadbalancer$
```

En este *docker-compose.yml* podemos ver varias cosas interesantes:

* En el servicio *keepalived*:
    * Unas variables de entorno que solo sirven para generar la configuración de **keepalived**, tal como se hace en el *script* `start.sh`
    * La directiva `network_mode: host` que sirve para que el contenedor use la red del *host*, pudiendo manejar sus direcciones IP
    * La directiva `cap_add: NET_ADMIN`, que es la *capability* mínima y necesaria para que el contenedor pueda modificar las configuraciones de red
* En el servicio *haproxy*:
    * La directiva `pid` que nos permite estar en el *namespace* de *keepalived*, para que sus procesos se vean entre sí
	* La directiva `depends_on`, de forma que se tenga que levantar primero *keepalived*; de lo contrario, no podríamos estar en su *namespace*...

#### El host slave

El truco es el mismo, pero teniendo en cuenta que la configuración de **keepalived** es un poco distinta. Eso lo conseguimos cambiando las variables de entorno que la genera.

```bash
gerard@atlantis:~/projects/ha-loadbalancer$ cat slave/docker-compose.yml
version: '2.1'
services:
  keepalived:
    image: sirrtea/keepalived:alpine
    container_name: keepalived
    hostname: keepalived
    environment:
      SERVICE: haproxy
      CHECK_INTERVAL: 2
      CHECK_WEIGHT: 2
      INTERFACE: enp0s3
      STATE: BACKUP
      VIRTUAL_ROUTER: 51
      PRIORITY: 10
      VIP: 10.0.0.2
    network_mode: host
    cap_add:
      - NET_ADMIN
  haproxy:
    image: sirrtea/haproxy:alpine
    container_name: haproxy
    hostname: haproxy
    pid: "service:keepalived"
    ports:
      - "80:8080"
    depends_on:
      - keepalived
gerard@atlantis:~/projects/ha-loadbalancer$
```

Los cambios son las variables de entorno `STATE` y `PRIORITY` en el servicio *keepalived*; el resto se mantiene igual.

```bash
gerard@atlantis:~/projects/ha-loadbalancer$ diff master/docker-compose.yml slave/docker-compose.yml
12c12
<       STATE: MASTER
---
>       STATE: BACKUP
14c14
<       PRIORITY: 11
---
>       PRIORITY: 10
gerard@atlantis:~/projects/ha-loadbalancer$
```

Solo nos faltaría desplegar ambos *docker-compose.yml* cada uno en un *host* distinto y ver que funciona como debe.
