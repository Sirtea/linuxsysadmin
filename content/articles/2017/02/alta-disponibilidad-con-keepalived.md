---
title: "Alta disponibilidad con Keepalived"
slug: "alta-disponibilidad-con-keepalived"
date: 2017-02-27
categories: ['Sistemas']
tags: ['keepalived', 'failover', 'ansible', 'ip flotante']
---

Cuando tenemos un servicio balanceado, los *backends* no tienen relación entre sí y podemos poner tantos como queramos, sin miedo a que alguno se caiga. Sin embargo, para los servicios tipo "ventanilla única" interesa tener varios dispuestos a dar un servicio *failover*; si uno se cae, otro asume la carga.<!--more-->

La idea general es que existe una dirección IP flotante y existe un servicio que se dedica a decidir quién la tiene asignada. Uno de estos servicios es **keepalived**, que es sencillo y fácil de montar.

## El entorno de trabajo

Para hacer este ejemplo, he dispuesto dos máquinas, una como prioritaria, y una de *failover*, que va a asumir el servicio siempre que la otra no pueda hacerlo.

Para mi comodidad, he dispuesto contenedores **docker**, como se describe en [otro artículo]({{< relref "/articles/2016/06/controlando-contenedores-docker-con-ansible.md" >}}) y voy a hacer la instalación por **ansible**. Aunque el entorno no es muy complejo, por comodidad lo he levantado con **docker-compose**.

```bash

gerard@gatria:~/docker/keepalived$ cat docker-compose.yml 
version: '2'
services:
  gemini:
    image: master
    hostname: gemini
    container_name: gemini
    volumes:
      - ./playbooks:/root/playbooks:ro
      - ./inventory/hosts:/root/inventory/hosts:ro
    ports:
      - "22:22"
  castor:
    image: slave
    hostname: castor
    container_name: castor
    privileged: true
  pollux:
    image: slave
    hostname: pollux
    container_name: pollux
    privileged: true
gerard@gatria:~/docker/keepalived$ 
```

La diferencia radica en que he puesto un servidor **SSH** en la máquina *master* para poder acceder fácilmente a ella y que los *playbooks* y parte del inventario vienen de la máquina *host*, para su fácil edición con un editor adecuado.

**AVISO**: Las máquinas *slave* van a disputarse la dirección flotante; esto no es posible en un contenedor normal. Para evitar ese problema, les he puesto el *flag privilieged*, para que puedan hacer lo que quieran.

Finalmente creamos el entorno, con el comando adecuado.

```bash
gerard@gatria:~/docker/keepalived$ docker-compose up -d
Creating network "keepalived_default" with the default driver
Creating gemini
Creating castor
Creating pollux
gerard@gatria:~/docker/keepalived$ 
```

Todos los comandos a partir de ahora se vana ejecutar en *gemini*, que es el *master* de **ansible**, y al que vamos a acceder por **SSH**.

```bash
gerard@gatria:~/docker/keepalived$ ssh root@localhost
Warning: Permanently added 'localhost' (ECDSA) to the list of known hosts.
root@localhost's password: 

The programs included with the Debian GNU/Linux system are free software;
the exact distribution terms for each program are described in the
individual files in /usr/share/doc/*/copyright.

Debian GNU/Linux comes with ABSOLUTELY NO WARRANTY, to the extent
permitted by applicable law.
root@gemini:~# 
```

El fichero de *hosts* no tiene ningún secreto (aparte de las variables dependientes de cada máquina, que ya veremos), pero lo ponemos por completitud:

```bash
root@gemini:~# cat inventory/hosts 
[gemini]
castor keepalived_priority=101
pollux keepalived_priority=100
root@gemini:~# 
```

## Ofreciendo un servicio cualquiera

Normalmente, las máquinas en configuración de *failover* suelen ser balanceadores o servidores web. En realidad, esto es irrelevante para **keepalived**, así que vamos a poner cualquiera.

Nos hemos decantado por un servidor **nginx** en configuración de servidor web estático, para que no absorba la atención del artículo. En la vida real, estaría en configuración de balanceador web, o sería directamente un **haproxy**.

Nos movemos a la carpeta de trabajo para este *playbook*.

```bash
root@gemini:~# cd ~/playbooks/webserver/
root@gemini:~/playbooks/webserver# 
```

El *playbook* en sí no tiene mucho misterio; instala **nginx**, lo levanta con una configuración propia y pone un fichero **HTML** con una plantilla indicando el nombre de la máquina que ha servido la petición, a modo de chivato.

```bash
root@gemini:~/playbooks/webserver# cat webserver.yml 
- hosts: gemini
  gather_facts: false
  tasks:
    - apt: name=nginx-light state=present
    - file: path=/etc/nginx/sites-enabled/default state=absent
    - file: path=/www state=directory
    - template: src=web.j2 dest=/etc/nginx/sites-enabled/web
    - template: src=index.html.j2 dest=/www/index.html
    - service: name=nginx state=started
    - service: name=nginx state=reloaded
root@gemini:~/playbooks/webserver# cat web.j2 
server {
	listen 80;
	server_name _;
	root /www;
	index index.html;
}
root@gemini:~/playbooks/webserver# cat index.html.j2 
<p>Hello from <em>{{ inventory_hostname }}</em></p>
root@gemini:~/playbooks/webserver# 
```

Lo lanzamos y ya tenemos dos servidores web para nuestra demostración:

```bash
root@gemini:~/playbooks/webserver# ansible-playbook webserver.yml 

PLAY [gemini] ******************************************************************

TASK [apt] *********************************************************************
changed: [castor]
changed: [pollux]

TASK [file] ********************************************************************
changed: [castor]
changed: [pollux]

TASK [file] ********************************************************************
changed: [pollux]
changed: [castor]

TASK [template] ****************************************************************
changed: [pollux]
changed: [castor]

TASK [template] ****************************************************************
changed: [castor]
changed: [pollux]

TASK [service] *****************************************************************
changed: [castor]
changed: [pollux]

TASK [service] *****************************************************************
changed: [pollux]
changed: [castor]

PLAY RECAP *********************************************************************
castor                     : ok=7    changed=7    unreachable=0    failed=0   
pollux                     : ok=7    changed=7    unreachable=0    failed=0   

root@gemini:~/playbooks/webserver# 
```

Comprobamos que funciona, y con esto estamos:

```bash
root@gemini:~/playbooks/webserver# wget -qO- http://castor/
<p>Hello from <em>castor</em></p>
root@gemini:~/playbooks/webserver# wget -qO- http://pollux/
<p>Hello from <em>pollux</em></p>
root@gemini:~/playbooks/webserver# 
```

## Keepalived, o como compartir una dirección IP

Ante nada, nos movemos a la carpeta de trabajo:

```bash
root@gemini:~/playbooks/webserver# cd ~/playbooks/keepalived/
root@gemini:~/playbooks/keepalived# 
```

Realmente, el servicio **keepalived** es como cualquier otro: instalar, configurar y recargar la configuración. Lo importante en este caso son las configuraciones. Así que el *playbook* queda un poco simple, pero mejor. Solo cabe destacar que he instalado también **rsyslog** que me va a proporcionar capacidades de *syslog*, que es donde **keepalived** deja lo *logs*. Gracias este *log*, pude ver que hacía una operación no permitida para un contenedor normal.

```bash
root@gemini:~/playbooks/keepalived# cat keepalived.yml 
- hosts: gemini
  gather_facts: false
  tasks:
    - apt: name=rsyslog state=present
    - service: name=rsyslog state=started
- hosts: gemini
  gather_facts: false
  tasks:
    - apt: name=keepalived state=present
    - template: src=keepalived.conf.j2 dest=/etc/keepalived/keepalived.conf
    - service: name=keepalived state=restarted
root@gemini:~/playbooks/keepalived# cat keepalived.conf.j2 
vrrp_script chk_nginx {
      script "killall -0 nginx"
      interval 2
      weight 2
}

vrrp_instance VI_1 {
      interface eth0
      state MASTER
      virtual_router_id 51
      priority {{ keepalived_priority }}
      virtual_ipaddress {
           172.18.0.10
      }
      track_script {
           chk_nginx
      }
}
root@gemini:~/playbooks/keepalived# 
```

La idea es que cada máquina del *cluster* tiene una prioridad, y la máquina con mas prioridad va a obtener la IP flotante, dando el servicio efectivo. Esta prioridad se ve afectada por los *checks* que pongamos, sumando el *weight* de cada *check* que devuelva un código de retorno 0 (se considera un OK).

Con los valores 101 y 100 (que salen del fichero de *hosts*) y el propio funcionamiento de **keepalived**, nos aseguramos de que:

* Si una máquina está caída no es candidata a tener la IP flotante (las dos caídas son un tema serio).
* Si *castor* tiene el **nginx** funcional, suma 103, y gana a *pollux* (102 o 100, dependiendo si corre o no el **nginx**).
* Si el **nginx** de *castor* no funciona, depende; si el de *pollux* funciona, pasa este a ser el *MASTER* del *cluster* (101 vs 102); sino, gana *castor* (101 vs 100), aunque este caso también es un problema.

Lanzamos el *playbook* para instalar **keepalived** y su configuración:

```bash
root@gemini:~/playbooks/keepalived# ansible-playbook keepalived.yml 

PLAY [gemini] ******************************************************************

TASK [apt] *********************************************************************
changed: [castor]
changed: [pollux]

TASK [service] *****************************************************************
changed: [pollux]
changed: [castor]

PLAY [gemini] ******************************************************************

TASK [apt] *********************************************************************
changed: [pollux]
changed: [castor]

TASK [template] ****************************************************************
changed: [castor]
changed: [pollux]

TASK [service] *****************************************************************
changed: [castor]
changed: [pollux]

PLAY RECAP *********************************************************************
castor                     : ok=5    changed=5    unreachable=0    failed=0   
pollux                     : ok=5    changed=5    unreachable=0    failed=0   

root@gemini:~/playbooks/keepalived# 
```

Y solo nos queda observar quien tiene la IP flotante (es *castor* porque ambos **nginx** funcionan y es un 103 vs 102).

```bash
root@gemini:~/playbooks/keepalived# ansible -m raw -a 'ip addr | grep "inet "' gemini
castor | SUCCESS | rc=0 >>

    inet 127.0.0.1/8 scope host lo
    inet 172.18.0.3/16 scope global eth0
    inet 172.18.0.10/32 scope global eth0


pollux | SUCCESS | rc=0 >>

    inet 127.0.0.1/8 scope host lo
    inet 172.18.0.4/16 scope global eth0


root@gemini:~/playbooks/keepalived# wget -qO- http://172.18.0.10/
<p>Hello from <em>castor</em></p>
root@gemini:~/playbooks/keepalived# 
```

## Pruebas de alta disponibilidad

Vamos a simular una caída de *castor* o de su **nginx** (el resultado es el mismo):

```bash
root@gemini:~/playbooks/keepalived# ansible -m service -a "name=nginx state=stopped" castor
castor | SUCCESS => {
    "changed": true, 
    "name": "nginx", 
    "state": "stopped"
}
root@gemini:~/playbooks/keepalived# 
```

¿Que pasa con la IP flotante? Por supuesto, la hereda *pollux*.

```bash
root@gemini:~/playbooks/keepalived# ansible -m raw -a 'ip addr | grep "inet "' gemini
castor | SUCCESS | rc=0 >>

    inet 127.0.0.1/8 scope host lo
    inet 172.18.0.3/16 scope global eth0


pollux | SUCCESS | rc=0 >>


    inet 127.0.0.1/8 scope host lo
    inet 172.18.0.4/16 scope global eth0
    inet 172.18.0.10/32 scope global eth0


root@gemini:~/playbooks/keepalived# wget -qO- http://172.18.0.10/
<p>Hello from <em>pollux</em></p>
root@gemini:~/playbooks/keepalived# 
```

Ahora simularemos que se cae *pollux*. Esto nos deja sin servicio...

```bash
root@gemini:~/playbooks/keepalived# ansible -m service -a "name=nginx state=stopped" pollux
pollux | SUCCESS => {
    "changed": true, 
    "name": "nginx", 
    "state": "stopped"
}
root@gemini:~/playbooks/keepalived# 
```

Como las dos máquinas están levantadas, se trata de un 101 vs 100, lo que le da la IP a *castor*. El servicio no responde porque el **nginx** de *castor* está caído. Mal asunto.

```bash
root@gemini:~/playbooks/keepalived# ansible -m raw -a 'ip addr | grep "inet "' gemini
pollux | SUCCESS | rc=0 >>

    inet 127.0.0.1/8 scope host lo
    inet 172.18.0.4/16 scope global eth0


castor | SUCCESS | rc=0 >>

    inet 127.0.0.1/8 scope host lo
    inet 172.18.0.3/16 scope global eth0
    inet 172.18.0.10/32 scope global eth0


root@gemini:~/playbooks/keepalived# wget -O- http://172.18.0.10/
converted 'http://172.18.0.10/' (ANSI_X3.4-1968) -> 'http://172.18.0.10/' (UTF-8)
--2016-10-14 11:00:08--  http://172.18.0.10/
Connecting to 172.18.0.10:80... failed: Connection refused.
root@gemini:~/playbooks/keepalived# 
```

Ahora, supongamos que *pollux* se recupera.

```bash
root@gemini:~/playbooks/keepalived# ansible -m service -a "name=nginx state=started" pollux
pollux | SUCCESS => {
    "changed": true, 
    "name": "nginx", 
    "state": "started"
}
root@gemini:~/playbooks/keepalived# 
```

Sin sorpresas, asume la IP flotante (101 vs 102).

```bash
root@gemini:~/playbooks/keepalived# ansible -m raw -a 'ip addr | grep "inet "' gemini
pollux | SUCCESS | rc=0 >>

    inet 127.0.0.1/8 scope host lo
    inet 172.18.0.4/16 scope global eth0
    inet 172.18.0.10/32 scope global eth0


castor | SUCCESS | rc=0 >>

    inet 127.0.0.1/8 scope host lo
    inet 172.18.0.3/16 scope global eth0


root@gemini:~/playbooks/keepalived# wget -qO- http://172.18.0.10/
<p>Hello from <em>pollux</em></p>
root@gemini:~/playbooks/keepalived# 
```

Y finalmente se recupera *castor*, lo que le da la prioridad para asumir su posición como *master* del *cluster*.

```bash
root@gemini:~/playbooks/keepalived# ansible -m service -a "name=nginx state=started" castor
castor | SUCCESS => {
    "changed": true, 
    "name": "nginx", 
    "state": "started"
}
root@gemini:~/playbooks/keepalived# 
```

Y sin sorpresas, recibe las peticiones para sí mismo:

```bash
root@gemini:~/playbooks/keepalived# ansible -m raw -a 'ip addr | grep "inet "' gemini
castor | SUCCESS | rc=0 >>

    inet 127.0.0.1/8 scope host lo
    inet 172.18.0.3/16 scope global eth0
    inet 172.18.0.10/32 scope global eth0


pollux | SUCCESS | rc=0 >>

    inet 127.0.0.1/8 scope host lo
    inet 172.18.0.4/16 scope global eth0


root@gemini:~/playbooks/keepalived# wget -qO- http://172.18.0.10/
<p>Hello from <em>castor</em></p>
root@gemini:~/playbooks/keepalived# 
```

En caso de haberse levantado antes *castor*, habría ejercido como *master* enseguida, y el levantamiento de *pollux* no habría provocado un *failover* nuevo (103 vs 100 y 103 vs 102, respectivamente).

Y con esto ya podemos tener nuestros servicios y balanceadores tipo "ventanilla única" redundados y con alta disponibilidad. Cabe indicar que esto no es útil ni con los *backends* (el balanceador ya suele controlar si una de ellos está caído o no), ni con los *clusters* con tecnología de *clustering* propia (bases de datos, colas, ...).
