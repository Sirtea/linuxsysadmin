---
title: "Un entorno productivo basado en Docker Swarm (IV)"
slug: "un-entorno-productivo-basado-en-docker-swarm-4"
date: "2019-10-07"
categories: ['Sistemas']
tags: ['linux', 'entorno', 'docker', 'swarm', 'traefik', 'keepalived']
series: "Un entorno productivo basado en Docker Swarm"
---

El siguiente artículo de la serie está dedicado a los balanceadores. Harto de mantener
varias instancias sincronizadas entre sí y modificar los *pools* de balanceo cada vez
que hay que hacer un despliegue, he optado por la versión fácil de **traefik**, que
nos permite "montar y olvidar", con mantenimiento cero.<!--more-->

**NOTA**: El artículo está enormemente basado en [este otro][1], aunque esta vez sí
que disponemos de varios nodos *managers*. Una vez montado, podremos apuntar a cada
uno de los nodos indistintamente con los mismos resultados; resolveré la parte de alta
disponibilidad usando una IP flotante entre los *managers*, con un procedimiento similar
al de [este otro artículo][2] (aunque sin el *failover* voluntario, para abreviar).

## Los balanceadores individuales

Lo que vamos a hacer es montar una instancia de **traefik** en cada *manager*, así
tendremos varios y cumpliremos con la restricción de ejecutar en un *manager* del *swarm*.
Ya vimos que **traefik** no requiere ningún mantenimiento una vez montado, así que es de
esperar que cada instancia sepa reconfigurarse individualmente. De esta forma aseguramos
que no importa el que usemos; todos están configurados de forma idéntica.

De forma similar al artículo anterior, vamos a crear una red *overlay* llamada *frontend*,
que nos permita comunicar los balanceadores con la capa de aplicación. De esta manera,
una aplicación que pertenezca a las redes de *backend* y *frontend* podrá ser balanceada
y, a su vez, acceder a la capa de bases de datos, en un intento de separar partes lógicas.

```bash
gerard@docker01:~$ docker network create -d overlay frontend
51rx4s8znxrmhkreeouf9bzxv
gerard@docker01:~$ 
```

Vamos a poner las recetas en una carpeta, lo que lo mantiene todo ordenado y nos permite
trabajar con un sistema de versiones, en vista a utilizar buenas prácticas en el futuro.

```bash
gerard@docker01:~$ mkdir traefik
gerard@docker01:~$ cd traefik/
gerard@docker01:~/traefik$ 
```

En este caso, no necesitamos para nada varios servicios, porque no nos interesa resolver
sus direcciones IP por el nombre de servicio concreto; esto nos simplifica mucho la receta.

```bash
gerard@docker01:~/traefik$ cat traefik.yml 
version: '3.2'
services:
  traefik:
    image: traefik:2.0
    command: --api.insecure=true --providers.docker.swarmmode --providers.docker.exposedbydefault=false --providers.docker.network=frontend
    ports:
      - target: 80
        published: 80
        protocol: tcp
        mode: host
      - target: 8080
        published: 8080
        protocol: tcp
        mode: host
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
    networks:
      - frontend
    deploy:
      mode: global
      placement:
        constraints:
          - node.role == manager
networks:
  frontend:
    external: true
gerard@docker01:~/traefik$ 
```

**TRUCO**: **Traefik** tiene una visión de todos los contenedores y redes del **swarm**,
y es capaz de ver las redes a las que pertenece cada contenedor. Sin embargo, no es tan
bueno para detectar la red por la que debe enrutar las peticiones a los diferentes contenedores.
Eso se puede indicar en las *labels* de cada contenedor, e incluso dar un valor por defecto;
en este caso es lo que usamos porque todos los contenedores están en la red *frontend*.

**NOTA**: En el [citado artículo][1] se utilizaba la versión *latest* de **traefik**,
que correspondía con la versión 1.7. Se ha especificado el *tag* por ser una buena
práctica y se ha utilizado la última versión, que es la 2.0; esto nos obliga a
actualizar los *flags* usados, que han cambiado considerablemente.

Simplemente tenemos que desplegar el servicio:

```bash
gerard@docker01:~/traefik$ docker stack deploy -c traefik.yml traefik
Creating service traefik_traefik
gerard@docker01:~/traefik$ 
```

En este punto solo nos quedaría confirmar que tenemos una instancia en cada nodo,
y que cada máquina expone su propio **traefik** individualmente.

```bash
gerard@docker01:~/traefik$ docker stack ls
NAME                SERVICES            ORCHESTRATOR
mongo               3                   Swarm
traefik             1                   Swarm
gerard@docker01:~/traefik$ docker stack ps traefik
ID                  NAME                                        IMAGE               NODE                DESIRED STATE       CURRENT STATE                ERROR               PORTS
oonfohn1zkja        traefik_traefik.io9916f6d5u9a4lq4gufwu58i   traefik:latest      docker02            Running             Running about a minute ago                       *:8080->8080/tcp,*:80->80/tcp
jnt8uuudu82s        traefik_traefik.ai1kllx5blrdxqq0r8azm8lam   traefik:latest      docker01            Running             Running about a minute ago                       *:8080->8080/tcp,*:80->80/tcp
d0og9xnx5xip        traefik_traefik.i8gf5d8zmpikkwep0yu4ml105   traefik:latest      docker03            Running             Running about a minute ago                       *:80->80/tcp,*:8080->8080/tcp
gerard@docker01:~/traefik$ 
```

```bash
gerard@docker01:~/traefik$ for domain in docker0{1,2,3,4,5,6}; do echo -n "${domain} -> "; curl http://${domain}:80/; done
docker01 -> 404 page not found
docker02 -> 404 page not found
docker03 -> 404 page not found
docker04 -> curl: (7) Failed to connect to docker04 port 80: Conexión rehusada
docker05 -> curl: (7) Failed to connect to docker05 port 80: Conexión rehusada
docker06 -> curl: (7) Failed to connect to docker06 port 80: Conexión rehusada
gerard@docker01:~/traefik$ 
```

Eso significa que se llega a un **traefik** en los nodos **docker01**, **docker02** y
**docker03** (aunque no hay ningún servicio expuesto), pero no al resto (ya que no son
*managers* y por lo tanto, no tienen una instancia ejecutando, como indica el `docker stack ps`).

## Alta disponibilidad con una IP flotante

Ahora mismo, vayamos al *manager* que vayamos tenemos servicio. Sin embargo, el
*gateway* solo puede pasar las peticiones externas a **una sola dirección IP**.

Para asegurar que el servidor apuntado por el *gateway* esté disponible, vamos a
utilizar **keepalived**, de forma que se pasen la IP flotante de uno a otro en
caso necesario. De esta forma, el *gateway* solo tiene que apuntar a la IP flotante.

**NOTA**: Esto lo vamos a hacer **sin docker**; es posible, pero implica privilegios
adicionales y no vale la pena. Así que lo vamos a hacer a la antigua, servidor por servidor.

Empezaremos instalando el servicio **keepalived** en los 3 servidores:

```bash
gerard@docker01:~$ sudo apt install keepalived
...
gerard@docker01:~$ 
```

```bash
gerard@docker02:~$ sudo apt install keepalived
...
gerard@docker02:~$ 
```

```bash
gerard@docker03:~$ sudo apt install keepalived
...
gerard@docker03:~$ 
```

Los configuramos de la forma más básica posible; pongo solamente la configuración para
**docker01** ya que el resto son iguales. Solo voy a cambiar la directiva `priority` para
que sea previsible quién tiene la VIP en cada momento. He decidido utilizar la dirección
`10.0.0.2/24` que ya dejé libre en la asignación DHCP del *gateway* para este fin.

```bash
gerard@docker01:~$ cat /etc/keepalived/keepalived.conf
vrrp_instance VI_1 {
    interface enp0s3
    priority 3   # 2 para docker02 y 1 para docker03
    virtual_router_id 51
    virtual_ipaddress {
        10.0.0.2
    }
}
gerard@docker01:~$ 
```

**NOTA**: No hay que olvidarnos de configurar todos los *managers* del *swarm*.

Solo nos faltaría reiniciar el servicio de los 3 *managers*:

```bash
gerard@docker01:~$ sudo systemctl restart keepalived
gerard@docker01:~$ 
```

```bash
gerard@docker02:~$ sudo systemctl restart keepalived
gerard@docker02:~$ 
```

```bash
gerard@docker03:~$ sudo systemctl restart keepalived
gerard@docker03:~$ 
```

Con esto ya deberíamos tener la VIP asignada a uno de los nodos (seguramente a **docker01**).

```bash
gerard@gateway:~$ ssh 10.0.0.2 hostname
gerard@10.0.0.2's password: 
docker01
gerard@gateway:~$ 
```

## Dirigir el tráfico a la IP flotante

**Traefik** utiliza dos puertos con la actual configuración:

* El 80 para el tráfico balanceado normal
* El 8080 para exponer el *dashboard*

Nos interesa exponer ambos para mirar cómodamente desde un navegador. Esto lo hacemos con
dos simples reglas DNAT en el *gateway* (una por puerto). Luego reiniciamos **shorewall**.

```bash
gerard@gateway:~$ cat /etc/shorewall/rules 
ACCEPT net fw tcp 22
DNS(ACCEPT) loc fw
DNAT net loc:10.0.0.2:80 tcp 80
DNAT net loc:10.0.0.2:8080 tcp 8080
gerard@gateway:~$ 
```

```bash
gerard@gateway:~$ sudo systemctl restart shorewall
gerard@gateway:~$ 
```

Podemos ver el *dashboard* en un navegador, usando la URL `http://gateway:8080/dashboard/`,
y podríamos hacer peticiones web en el puerto 80 del *gateway*, aunque de momento, no
hay servicios expuestos, con lo que nos seguirá dando errores 404...

**NOTA**: Lo importante es que la plataforma está lista; solo tendremos que ir poniendo servicios
según vayamos desplegando aplicaciones; **traefik** los separa usando *virtualhosts*.
Lo siguiente es poner los servicios, pero esto queda para el siguiente artículo de la serie.

[1]: {{< relref "/articles/2018/10/usando-traefik-en-un-cluster-de-docker-swarm.md" >}}
[2]: {{< relref "/articles/2019/05/un-cluster-de-3-nodos-con-failover-voluntario-usando-keepalived.md" >}}
