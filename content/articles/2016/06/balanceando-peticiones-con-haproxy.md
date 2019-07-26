---
title: "Balanceando peticiones con HAProxy"
slug: "balanceando-peticiones-con-haproxy"
date: 2016-06-27
categories: ['Sistemas']
tags: ['balanceador', 'haproxy', 'ansible', 'docker']
---

Cuando tenemos un entorno grande o con previsiones de crecimiento, nos interesa poder poner a trabajar varios servidores similares. En casos así nos hace falta un **balanceador de carga**, que actúa como un agente de tráfico, dirigiendo las peticiones que él mismo recibe a los diferentes servidores, por ejemplo, **haproxy**.<!--more-->

En este artículo vamos a montar el balanceador **haproxy**, usando **ansible**, basándonos en las imágenes **docker** de [otro artículo]({{< relref "/articles/2016/06/controlando-contenedores-docker-con-ansible.md" >}}). La ideas es que vamos a poner un único balanceador que va a escuchar en dos puertos, balanceando dos *backends* en cada uno, por ejemplo una web y una *api*.

```bash
gerard@sirius:~/build$ docker images
REPOSITORY          TAG                 IMAGE ID            CREATED             SIZE
slave               latest              22a9312a1315        About an hour ago   186 MB
ansible             latest              225b431d2133        About an hour ago   245.5 MB
debian              latest              bb5d89f9b6cb        2 weeks ago         125.1 MB
gerard@sirius:~/build$ 
```

## Preparando el entorno

El primer paso es disponer de una red para que todos los servidores implicados se puedan comunicar entre ellos. La red que viene por defecto nos permite eso, pero vamos a crear una red *user defined* que nos va a permitir que los contenedores **docker** se conozcan entre ellos por su nombre.

```bash
gerard@sirius:~/build$ docker network create --subnet=172.20.0.0/16 balancing
4585a1abd0ed69bc9d1daf0dd019e1f129a9e7328471da77541f5b4a54c19626
gerard@sirius:~/build$ 
```

Se trata de levantar 5 servidores: 1 para **haproxy** y otros 4 para representar los servidores de *backend*, que vamos a trucar para que parezca lo que no son. Es importante *publicar* los puertos que queramos exponer, para ver que funciona la solución final; si queremos balancear los puertos 8080 (web), 8081 (api) y 1936 (haproxy stats), pondríamos algo como esto:

```bash
gerard@sirius:~$ docker run -d -h balancer --name balancer --net balancing -p 8080:8080 -p 8081:8081 -p 1936:1936 slave
70e4811e6a498c7ecdec11ed91609d43749c327e33bd3b06b1532b507f3f2141
gerard@sirius:~/build$ for host in web1 web2 api1 api2; do docker run -d -h $host --name $host --net balancing slave; done
82be4f7788f0186834311fe625f4ae24908a59a25df8b246aeb18d13cdff7b3d
a0514880a44ed9109d19dc594ae991245e052554d91f0b08da80d57808df3d29
1217fd05aa321e52e0038e4870dd29776e843d88de03520ad0bffee6cb786b54
635c9b2d04482018053dca4b4225a34d3a11be1c366e372b9536fcadea12a15a
gerard@sirius:~/build$ 
```

Verificamos que tenemos todos nuestros contenedores corriendo:

```
gerard@sirius:~/build$ docker ps
CONTAINER ID        IMAGE               COMMAND               CREATED              STATUS              PORTS                                                      NAMES
635c9b2d0448        slave               "/usr/sbin/sshd -D"   10 seconds ago       Up 8 seconds                                                                   api2
1217fd05aa32        slave               "/usr/sbin/sshd -D"   11 seconds ago       Up 9 seconds                                                                   api1
a0514880a44e        slave               "/usr/sbin/sshd -D"   12 seconds ago       Up 10 seconds                                                                  web2
82be4f7788f0        slave               "/usr/sbin/sshd -D"   13 seconds ago       Up 12 seconds                                                                  web1
70e4811e6a49        slave               "/usr/sbin/sshd -D"   About a minute ago   Up About a minute   0.0.0.0:1936->1936/tcp, 0.0.0.0:8080-8081->8080-8081/tcp   balancer
gerard@sirius:~/build$ 
```

## Preparando las herramientas

Como ya hemos comentado, vamos a utilizar **ansible**. Para ejecutar los *playbooks*, vamos a levantar una máquina para usar y tirar.

```bash
gerard@sirius:~/build$ docker run -ti --rm --net balancing -h ansible --name ansible ansible
root@ansible:/# cd /root
root@ansible:~# 
```

Especificamos un fichero de *hosts* que va a servir para indicar los contenedores que tenemos y vamos a instalar paquetes en función de su grupo.

```bash
root@ansible:~# cat hosts 
[all:vars]
ansible_user = ansible
ansible_ssh_pass = s3cr3t
ansible_become = true
ansible_become_method = sudo
ansible_become_user = root
ansible_become_pass = s3cr3t

[balancers]
balancer

[webs]
web1
web2

[apis]
api1
api2
root@ansible:~# 
```

Opcionalmente, verificamos que todos los contenedores son accesibles desde **ansible**. Eso nos puede evitar sorpresas futuras.

```bash
root@ansible:~# ansible -i hosts -m ping all
balancer | SUCCESS => {
    "changed": false, 
    "ping": "pong"
}
api2 | SUCCESS => {
    "changed": false, 
    "ping": "pong"
}
api1 | SUCCESS => {
    "changed": false, 
    "ping": "pong"
}
web2 | SUCCESS => {
    "changed": false, 
    "ping": "pong"
}
web1 | SUCCESS => {
    "changed": false, 
    "ping": "pong"
}
root@ansible:~# 
```

## Instalando unos backends sustitutos

Sea lo que sea que vayan a ejecutar los *backends* reales, los podemos ver como una caja negra que ofrecen sus servicios mediante protocolo TCP/IP en un puerto concreto.

Como no nos importa demasiado lo que hagan, y para simplificar el artículo, los vamos a reemplazar con servidores web **nginx**, sirviendo un fichero HTML con su nombre (para poder distinguirlos en las pruebas). De esta forma, podremos ver el tipo de servidor que responde (api o web) y su número, ya que ambos datos están en su *hostname*.

Así pues, basta con un *playbook* que instale el servidor web y ponga el fichero *.html* en su sitio. Como **docker** está ejecutando el servidor **ssh** y no **systemd**, el **nginx** no se levanta. Con otra tarea para asegurar que está corriendo, basta.

```bash
root@ansible:~# cat backends.yml 
- hosts: webs, apis
  tasks:
    - apt: name=nginx-light state=present
    - copy: content="Content from {{ inventory_hostname }}" dest=/var/www/html/index.html
    - service: name=nginx state=started
root@ansible:~# 
```

Lanzamos el *playbook*, y los dejamos preparados para que el balanceador los pueda usar. En un entorno real, dedicaríamos mas tiempo en poner servidores de aplicaciones normales, con aplicaciones adecuadas, y que posiblemente usarían algún tipo de base de datos.

```bash
root@ansible:~# ansible-playbook -i hosts backends.yml 

PLAY [webs, apis] **************************************************************

TASK [setup] *******************************************************************
ok: [web2]
ok: [api1]
ok: [web1]
ok: [api2]

TASK [apt] *********************************************************************
changed: [api1]
changed: [api2]
changed: [web1]
changed: [web2]

TASK [copy] ********************************************************************
changed: [web1]
changed: [web2]
changed: [api2]
changed: [api1]

TASK [service] *****************************************************************
changed: [web1]
changed: [web2]
changed: [api1]
changed: [api2]

PLAY RECAP *********************************************************************
api1                       : ok=4    changed=3    unreachable=0    failed=0   
api2                       : ok=4    changed=3    unreachable=0    failed=0   
web1                       : ok=4    changed=3    unreachable=0    failed=0   
web2                       : ok=4    changed=3    unreachable=0    failed=0   

root@ansible:~# 
```

## Montando el balanceador

Para obtener un balanceador HTTP (o TCP, si lo necesitáramos), basta con elegir uno. Normalmente yo usaría un servidor **nginx** para balancear HTTP (que además ofrece otras funcionalidades, aunque no soporte TCP directo); en este caso, y para variar un poco, vamos a poner **haproxy**, que nos ofrece una bonita página de estadísticas.

El truco está en instalar **haproxy**, darle un fichero de configuración adecuado y recargar su configuración. Nuevamente, al tratarse de **docker** hay que asegurarse que el servicio esté levantado.

```bash
root@ansible:~# cat balancer.yml 
- hosts: balancer
  tasks:
    - apt: name=haproxy state=present
    - service: name=haproxy state=started
    - copy: src=haproxy.cfg dest=/etc/haproxy/haproxy.cfg
    - service: name=haproxy state=reloaded
root@ansible:~# 
```

La funcionalidad con la que cumpla el balanceador se controla en */etc/haproxy/haproxy.cfg*, que el *playbook* pone en su sitio, desde una carpeta en el contexto.

HAProxy funciona mapeando *frontends* (entradas del balanceador) con sus respectivos *backends* (servidores que atienden peticiones).

Disponemos de varios algoritmos de balanceo, así que vamos a poner uno distinto para cada *backend*. Para la web, vamos a usar *roundrobin*, que básicamente se trata de una petición a cada uno por turnos; la *api* va a contar con el algoritmo *leastconn*, que significa darle una petición al servidor que menos conexiones tiene abiertas.

Como *bonus track*, vamos a habilitar la página de estadísticas, siempre que la queramos, claro. La he copiado tal cual de la documentación de **haproxy**.

```
root@ansible:~# cat haproxy.cfg 
listen stats :1936
    mode http
    stats enable
    stats hide-version
    stats uri /

frontend web
    bind :8080
    default_backend webs

backend webs
    balance roundrobin
    server web1 web1:80
    server web2 web2:80

frontend api
    bind :8081
    default_backend apis

backend apis
    balance leastconn
    server api1 api1:80
    server api2 api2:80
root@ansible:~# 
```

Solo nos faltaría lanzar el *playbook* para que quede todo correctamente montado. Si la configuración cambiara o hubiera que corregirla, se debe modificar el fichero local *haproxy.cfg* y relanzar el *playbook*. **Ansible** no intentará cambiar nada que ya esté como debía; no instalará **haproxy** de nuevo, no lo levantará si ya estaba corriendo, no copiará el fichero a menos que haya cambiado, y siempre va a recargar la configuración del servicio.

```bash
root@ansible:~# ansible-playbook -i hosts balancer.yml 

PLAY [balancer] ****************************************************************

TASK [setup] *******************************************************************
ok: [balancer]

TASK [apt] *********************************************************************
changed: [balancer]

TASK [service] *****************************************************************
changed: [balancer]

TASK [copy] ********************************************************************
changed: [balancer]

TASK [service] *****************************************************************
changed: [balancer]

PLAY RECAP *********************************************************************
balancer                   : ok=5    changed=4    unreachable=0    failed=0   

root@ansible:~# 
```

## Comprobando el funcionamiento

Si hacemos peticiones individuales, vemos que cada servidor funciona, pero lo que nos importa es el conjunto. Para ello vamos a solicitar peticiones a cada uno de los puertos que representan el *cluster* de web y de *api*. Puesto que los hemos publicado con el mismo número de puerto en la máquina anfitriona, lo podemos lanzar ahí mismo.

Hacemos unas peticines al *cluster* de web, que se esconde detrás del puerto 8080, y comprobamos que van alternando un *backend* u otro por turnos.

```bash
gerard@sirius:~$ curl http://localhost:8080/ ; echo ''
Content from web1
gerard@sirius:~$ curl http://localhost:8080/ ; echo ''
Content from web2
gerard@sirius:~$ curl http://localhost:8080/ ; echo ''
Content from web1
gerard@sirius:~$ curl http://localhost:8080/ ; echo ''
Content from web2
gerard@sirius:~$ 
```

Repetimos el procedimiento para la *api*, que se esconde en el puerto 8081 del balanceador:

```bash
gerard@sirius:~$ curl http://localhost:8081/ ; echo ''
Content from api1
gerard@sirius:~$ curl http://localhost:8081/ ; echo ''
Content from api2
gerard@sirius:~$ curl http://localhost:8081/ ; echo ''
Content from api1
gerard@sirius:~$ curl http://localhost:8081/ ; echo ''
Content from api2
gerard@sirius:~$ 
```

Y solo nos queda ver que la página de estadísticas funciona y nos resulta útil. Puesto que devuelve una página web completa, lo vamos a ver en un navegador cualquiera.

![HAProxy Stats](/images/haproxy-stats.jpg)
