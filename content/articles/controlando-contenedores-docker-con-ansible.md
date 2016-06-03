Title: Controlando contenedores docker con ansible
Slug: controlando-contenedores-docker-con-ansible
Date: 2016-06-06 08:00
Category: Operaciones
Tags: linux, docker, dockerfile, ansible, playbook



La facilidad de levantar un contenedor **docker** nos lleva a la pregunta del millón: ¿es posible usar **docker** para crear contenedores de usar y tirar para probar otras tecnologías? La respuesta es que sí, y para demostrarlo, vamos a generar un entorno minimalista en contenedores **docker**, desplegados mediante **ansible** *playbooks*.

**AVISO**: De acuerdo con el autor de **docker**, nunca deberíais poner **SSH** en un contenedor **docker** (artículo [aquí](https://jpetazzo.github.io/2014/06/23/docker-ssh-considered-evil/)). Sin embargo, hoy vamos a hacer una excepción para esta demostración.

## Las imágenes base

La idea es que vamos a levantar una serie de máquinas y vamos a dejar que **ansible** las provisiones mediante *playbooks*; para ello necesitamos una imagen base. También vamos a crear una imagen que solo sirva para ejecutar **ansible**, que vamos a crear y a destruir según lo necesitemos.

Vamos a empezar creando la imagen *master*, que contiene la herramienta **ansible** (vamos a poner una versión superior desde los *backports*) y sus dependencias. Este es nuestro *Dockerfile* y el fichero *ansible.cfg* que va a gobernarlo:

```bash
gerard@sirius:~/build$ cat ansible.cfg 
[defaults]
host_key_checking = False
gerard@sirius:~/build$ cat Dockerfile.master 
FROM debian:jessie-backports
RUN apt-get update && \
    apt-get install -y openssh-client sshpass nano
RUN apt-get install -y -t jessie-backports ansible
ADD ["ansible.cfg", "/root/.ansible.cfg"]
CMD ["/bin/bash"]
gerard@sirius:~/build$ 
```

Construimos la imagen mediante el comando *build* y le ponemos el *tag* "master".

```bash
gerard@sirius:~/build$ docker build -f Dockerfile.master -t master .
Sending build context to Docker daemon 4.096 kB
Step 1 : FROM debian:jessie-backports
 ---> 99552579b6f6
Step 2 : RUN apt-get update &&     apt-get install -y openssh-client sshpass nano
 ---> Running in 6e311500cbeb
...
 ---> d014d43ddf74
Removing intermediate container 6e311500cbeb
Step 3 : RUN apt-get install -y -t jessie-backports ansible
 ---> Running in d047144fce1b
...
 ---> 10881f414b84
Removing intermediate container d047144fce1b
Step 4 : ADD ansible.cfg /root/.ansible.cfg
 ---> 08fd2580e558
Removing intermediate container c6b3c29e8682
Step 5 : CMD /bin/bash
 ---> Running in 7b1199ff749f
 ---> 58689ad42e3e
Removing intermediate container 7b1199ff749f
Successfully built 58689ad42e3e
gerard@sirius:~/build$ 
```

Ahora vamos a crear la imagen para las máquinas controladas, mediante un *Dockerfile* creado a tal efecto:

```bash
gerard@sirius:~/build$ cat Dockerfile.slave 
FROM debian:jessie
RUN apt-get update && \
    apt-get install -y python openssh-server sudo && \
    useradd ansible -G sudo -s /bin/bash -m && \
    echo "ansible:s3cr3t" | chpasswd && \
    mkdir /var/run/sshd
CMD ["/usr/sbin/sshd", "-D"]
gerard@sirius:~/build$ 
```

Nuevamente lanzamos el *build* con el *tag* "slave".

```bash
gerard@sirius:~/build$ docker build -f Dockerfile.slave -t slave .
Sending build context to Docker daemon 4.096 kB
Step 1 : FROM debian:jessie
 ---> bb5d89f9b6cb
Step 2 : RUN apt-get update &&     apt-get install -y python openssh-server sudo &&     useradd ansible -G sudo -s /bin/bash -m &&     echo "ansible:s3cr3t" | chpasswd &&     mkdir /var/run/sshd
 ---> Running in ecc6f15ffdc1
...
 ---> ecd77bdcc643
Removing intermediate container ecc6f15ffdc1
Step 3 : CMD /usr/sbin/sshd -D
 ---> Running in 09b2642eb314
 ---> 306389180c9f
Removing intermediate container 09b2642eb314
Successfully built 306389180c9f
gerard@sirius:~/build$ 
```

Podemos comprobar que tenemos ambas imágenes preparadas para crear nuestros contenedores:

```bash
gerard@sirius:~/build$ docker images
REPOSITORY          TAG                 IMAGE ID            CREATED             SIZE
slave               latest              306389180c9f        5 seconds ago       186 MB
master              latest              58689ad42e3e        2 minutes ago       245.4 MB
debian              jessie-backports    99552579b6f6        6 days ago          125.1 MB
debian              jessie              bb5d89f9b6cb        6 days ago          125.1 MB
gerard@sirius:~/build$ 
```

## Creando los contenedores necesarios

La idea es que vamos a crear un micro entorno compuesto por dos servidores y un balanceador, que es la fachada del sistema. La salida de cada petición web va a indicar el nombre de la máquina que la sirvió, para poder comprobar que balancea adecuadamente.

Los *flags* de ejecución son *--name* (el nombre con el que nos referiremos en los comandos *docker*), el *-h* (para dar un nombre de sistema operativo a la máquina), el *-d* (*detach*, para que no nos bloquee el terminal) y la imagen *slave* que tiene instalados **ssh**, **python** y **sudo**. Adicionalmente la imagen del balanceador *publica* su puerto 80 en el puerto 8000 de la máquina *host*, para poder acceder por **HTTP** desde nuestra máquina.

```bash
gerard@sirius:~/build$ docker run --name balancer -h balancer -d -p 8000:80 slave
7a80942c69a70e729fc7090983fc59735fd0c10818a5b62b64a26a98e58fc101
gerard@sirius:~/build$ docker run --name server1 -h server1 -d slave
745acb30c5c1b7067a15f593dfefce3e769d2a7b5423f001b6a080296c3aeb3f
gerard@sirius:~/build$ docker run --name server2 -h server2 -d slave
a469c0f69bb42a3c979037b125750a4cc1bf01750c24bd7cef277b9b6e7dc2d0
gerard@sirius:~/build$ 
```

Es importante anotar las direcciones IP de las máquinas, para saber qué tenemos en cada sitio. Esta información nos sirve para montar la configuración del balanceador y para el inventario de **ansible**.

```bash
gerard@sirius:~/build$ docker inspect balancer | grep IPAddress
            "SecondaryIPAddresses": null,
            "IPAddress": "172.17.0.2",
                    "IPAddress": "172.17.0.2",
gerard@sirius:~/build$ docker inspect server1 | grep IPAddress
            "SecondaryIPAddresses": null,
            "IPAddress": "172.17.0.3",
                    "IPAddress": "172.17.0.3",
gerard@sirius:~/build$ docker inspect server2 | grep IPAddress
            "SecondaryIPAddresses": null,
            "IPAddress": "172.17.0.4",
                    "IPAddress": "172.17.0.4",
gerard@sirius:~/build$ 
```

Ahora podemos crear un contenedor de la imagen *master* que tiene **ansible** para *empujar* los *playbooks* a las *slaves*. Esta máquina es de "usar y tirar".

```bash
gerard@sirius:~/build$ docker run -ti --rm -h ansible master
root@ansible:/# cd /root/
root@ansible:~# 
```

## Manos a la obra: los playbooks

Este punto es similar al uso de **ansible** sin **docker**. Se trata de definir el fichero de *hosts*, los *playbooks* y los ficheros que estos puedan necesitar. En este caso concreto, vemos que necesitamos (*hosts* y *playbooks* aparte) la aplicación **python** que vamos a servir, la configuracion para **uwsgi** y la configuración del balanceador.

```bash
root@ansible:~# tree
.
|-- balancer.yml
|-- files
|   |-- balancer
|   |-- myapp.ini
|   `-- myapp.py
|-- hosts
`-- servers.yml

1 directory, 6 files
root@ansible:~# 
```

Un paso necesario es crear el fichero de *hosts*, que incluye los grupos, los contenedores que los forman y los parámetros de conexión a los mismos (como los declaramos en los *Dockerfiles*).

```bash
root@ansible:~# cat hosts 
[all:vars]
ansible_user = ansible
ansible_ssh_pass = s3cr3t
ansible_become = true
ansible_become_method = sudo
ansible_become_user = root
ansible_become_pass = s3cr3t

[balancer]
172.17.0.2

[servers]
172.17.0.3
172.17.0.4
root@ansible:~# 
```

### Los servidores de aplicaciones

La idea es que este grupo va a servir una aplicación **python** mediante el servidor **uwsgi**. Esta aplicación es un ejemplo muy simple, que se limita a indicar el *hostname* de la máquina, en forma de saludo. Esta aplicación se sirve en el puerto TCP 8080. Estos son el *playbook* y los ficheros necesarios para su ejecución:

```bash
root@ansible:~# cat files/myapp.py 
import os

def application(environ, start_response):
    start_response('200 OK', [('Content-Type', 'text/plain')])
    yield 'Hello from %s\n' % os.uname()[1]
root@ansible:~# cat files/myapp.ini 
[uwsgi]
plugins = python
master = true
workers = 2
http-socket = 0.0.0.0:8080
chdir = /opt/
module = myapp:application
root@ansible:~# cat servers.yml 
- hosts: servers
  gather_facts: false
  tasks:
    - apt: name={{ item }} state=installed
      with_items:
        - uwsgi-emperor
        - uwsgi-plugin-python
    - service: name=uwsgi-emperor state=started
    - copy: src=files/myapp.py dest=/opt/myapp.py
    - copy: src=files/myapp.ini dest=/etc/uwsgi-emperor/vassals/myapp.ini
    - file: path=/etc/uwsgi-emperor/vassals/myapp.ini state=touch
root@ansible:~# 
```

Y con esta información, es todo tan fácil como lanzar el *playbook* con el inventario creado.

```bash
root@ansible:~# ansible-playbook -i hosts servers.yml 

PLAY ***************************************************************************

TASK [apt] *********************************************************************
changed: [172.17.0.4] => (item=[u'uwsgi-emperor', u'uwsgi-plugin-python'])
changed: [172.17.0.3] => (item=[u'uwsgi-emperor', u'uwsgi-plugin-python'])

TASK [service] *****************************************************************
changed: [172.17.0.3]
changed: [172.17.0.4]

TASK [copy] ********************************************************************
changed: [172.17.0.3]
changed: [172.17.0.4]

TASK [copy] ********************************************************************
changed: [172.17.0.3]
changed: [172.17.0.4]

TASK [file] ********************************************************************
changed: [172.17.0.3]
changed: [172.17.0.4]

PLAY RECAP *********************************************************************
172.17.0.3                 : ok=5    changed=5    unreachable=0    failed=0   
172.17.0.4                 : ok=5    changed=5    unreachable=0    failed=0   

root@ansible:~# 
```

Y ya podríamos hacer peticiones al puerto para obtener respuestas adecuadas.

### El balanceador

Vamos a utilizar **nginx** con una configuración propia de balanceador, que también necesitamos:

```bash
root@ansible:~# cat files/balancer 
upstream servers {
	server 172.17.0.3:8080;
	server 172.17.0.4:8080;
}

server {
	location / {
		proxy_pass http://servers;
	}
}
root@ansible:~# cat balancer.yml 
- hosts: balancer
  gather_facts: false
  tasks:
    - apt: name=nginx-light state=installed
    - service: name=nginx state=started
    - file: path=/etc/nginx/sites-enabled/default state=absent
    - copy: src=files/balancer dest=/etc/nginx/sites-enabled/balancer
    - service: name=nginx state=reloaded
root@ansible:~# 
```

Y con esto tenemos lo suficiente para lanzar la provisión. Allá vamos!

```bash
root@ansible:~# ansible-playbook -i hosts balancer.yml 

PLAY ***************************************************************************

TASK [apt] *********************************************************************
changed: [172.17.0.2]

TASK [service] *****************************************************************
changed: [172.17.0.2]

TASK [file] ********************************************************************
changed: [172.17.0.2]

TASK [copy] ********************************************************************
changed: [172.17.0.2]

TASK [service] *****************************************************************
changed: [172.17.0.2]

PLAY RECAP *********************************************************************
172.17.0.2                 : ok=5    changed=5    unreachable=0    failed=0   

root@ansible:~# 
```

Se puede verificar que funciona lanzando peticiones al puerto 80 de esta máquina.

## Comprobación del resultado

La mala noticia es que la red 172.17.0.0/16 es privada, y no podemos acceder a ella a menos que sea desde un contenedor. La buena, es que tuvimos la previsión de publicar el puerto 80 del contenedor, mapeado en el puerto 8000 del *host*.

Así pues, es como si el puerto 80 del balanceador fuera el puerto 8000 de nuestra máquina. Basta con hacer algunas peticiones para darse cuenta de que tenemos las máquinas perfectamente funcionales.

```bash
gerard@sirius:~/build$ curl http://localhost:8000/
Hello from server1
gerard@sirius:~/build$ curl http://localhost:8000/
Hello from server2
gerard@sirius:~/build$ curl http://localhost:8000/
Hello from server1
gerard@sirius:~/build$ curl http://localhost:8000/
Hello from server2
gerard@sirius:~/build$ 
```
