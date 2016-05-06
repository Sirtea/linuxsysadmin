Title: Algunas ideas sueltas sobre Ansible
Slug: algunas-ideas-sueltas-sobre-ansible
Date: 2016-05-09 08:00
Category: Operaciones
Tags: ansible, playbook



En un [artículo anterior]({filename}/articles/instalando-ansible-para-gestionar-servidores.md) vimos qué era **Ansible** y como instalarlo, dejando su funcionamiento para el lector; Hay miles de tutoriales por internet, y muchos son mejores de los que pueda poner aquí. Sin embargo, hay algunas ideas que no son fáciles de ver juntas, así que aquí las dejo.

## Playbooks plantilla

Si solo queremos los *playbooks* como una manera fácil de aprovisionar una máquina, nos conviene que no tenga un *host* asignado en el mismo, para poder pasar el objetivo por parámetro. Por ejemplo:

```bash
root@ansible:~# cat ping.yml
- hosts: '{{ target }}'
  tasks:
    - ping:
root@ansible:~#
```

En este caso hay que pasar un argumento extra como *target*, y en caso de no ponerlo, el *playbook* no haría nada. Con este truco, podemos ir variando el objetivo, siempre que esté en el fichero *hosts*.

```bash
root@ansible:~# ansible-playbook ping.yml

PLAY [{{ target }}] ***********************************************************
skipping: no hosts matched

PLAY RECAP ********************************************************************

root@ansible:~# ansible-playbook ping.yml --extra-vars "target=appservers"

PLAY [appservers] *************************************************************

GATHERING FACTS ***************************************************************
ok: [10.0.0.3]
ok: [10.0.0.4]

TASK: [ping ] *****************************************************************
ok: [10.0.0.4]
ok: [10.0.0.3]

PLAY RECAP ********************************************************************
10.0.0.3                   : ok=2    changed=0    unreachable=0    failed=0
10.0.0.4                   : ok=2    changed=0    unreachable=0    failed=0

root@ansible:~# ansible-playbook ping.yml --extra-vars "target=10.0.0.3"

PLAY [10.0.0.3] ***************************************************************

GATHERING FACTS ***************************************************************
ok: [10.0.0.3]

TASK: [ping ] *****************************************************************
ok: [10.0.0.3]

PLAY RECAP ********************************************************************
10.0.0.3                   : ok=2    changed=0    unreachable=0    failed=0

root@ansible:~#
```

## Variar el entorno sin cambiar los playbooks

Aunque las máquinas y las redes asignadas a cada entorno sean variables, los grupos y funcionalidades son las mismas. Suponiendo que los *playbooks* actúen contra los grupos, variando el fichero de *hosts* podemos conseguir todos los entornos necesarios.

De hecho, podemos tener varios ficheros de *hosts* y especificarlos por parámetro en el momento de lanzar **ansible-playbook**. Por ejemplo, para el entorno de *preproducción*:

```bash
root@ansible:~# cat hosts-pre
[loadbalancer]
172.20.0.2

[appservers]
172.20.0.3
172.20.0.4

[dbservers]
172.20.0.5
root@ansible:~# ansible-playbook -i hosts-pre --list-hosts setup.yml

playbook: setup.yml

  play #1 (loadbalancer): Setup load balancer...        TAGS: []
    pattern: [u'loadbalancer']
    hosts (1):
      172.20.0.2

  play #2 (appservers): Setup application servers...    TAGS: []
    pattern: [u'appservers']
    hosts (2):
      172.20.0.3
      172.20.0.4

  play #3 (dbservers): Setup database servers...        TAGS: []
    pattern: [u'dbservers']
    hosts (1):
      172.20.0.5
root@ansible:~#
```

Y casi lo mismo para el entono de *producción*:

```bash
root@ansible:~# cat hosts-pro
[loadbalancer]
10.0.0.2

[appservers]
10.0.0.3
10.0.0.4
10.0.0.5
10.0.0.6
10.0.0.7

[dbservers]
10.0.0.8
10.0.0.9
10.0.0.10
root@ansible:~# ansible-playbook -i hosts-pro --list-hosts setup.yml

playbook: setup.yml

  play #1 (loadbalancer): Setup load balancer...        TAGS: []
    pattern: [u'loadbalancer']
    hosts (1):
      10.0.0.2

  play #2 (appservers): Setup application servers...    TAGS: []
    pattern: [u'appservers']
    hosts (5):
      10.0.0.5
      10.0.0.4
      10.0.0.7
      10.0.0.6
      10.0.0.3

  play #3 (dbservers): Setup database servers...        TAGS: []
    pattern: [u'dbservers']
    hosts (3):
      10.0.0.9
      10.0.0.8
      10.0.0.10
root@ansible:~#
```

## Inventario autogenerado

A veces nos conviene sacar la lista de *hosts* y de *grupos* de otro lugar, por ejemplo, de una base de datos corporativa. En estos casos, basta con saber que el fichero *hosts* puede ser ejecutable y se espera que devuelva un diccionario JSON de *grupos*, cada uno con una lista de los *hosts* que lo componen. **Ansible** va a ejecutar el *script* para sacar esa información.

Vamos a hacer un ejercicio de imaginación: supongamos este *script* saca los datos de algún sitio (LDAP, BBDD, una API de nuestra CMDB, ...), y los saca en formato JSON:

```bash
root@ansible:~# cat hosts.py
#!/usr/bin/env python

import json

inventory = {
    'loadbalancer': ['10.0.0.2'],
    'appservers': ['10.0.0.3', '10.0.0.4'],
    'dbservers': ['10.0.0.5'],
}

print json.dumps(inventory)
root@ansible:~# chmod 755 hosts.py
root@ansible:~# ./hosts.py
{"appservers": ["10.0.0.3", "10.0.0.4"], "loadbalancer": ["10.0.0.2"], "dbservers": ["10.0.0.5"]}
root@ansible:~#
```

Veamos que es capaz de sacar los grupos que le pidamos de forma fácil:

```bash
root@ansible:~# ansible -i hosts.py --list-hosts loadbalancer
  hosts (1):
    10.0.0.2
root@ansible:~# ansible -i hosts.py --list-hosts appservers
  hosts (2):
    10.0.0.3
    10.0.0.4
root@ansible:~# ansible -i hosts.py --list-hosts dbservers
  hosts (1):
    10.0.0.5
root@ansible:~# ansible -i hosts.py --list-hosts all
  hosts (4):
    10.0.0.3
    10.0.0.4
    10.0.0.2
    10.0.0.5
root@ansible:~#
```

## Desplegar ficheros según el host

En los *playbooks* podemos usar variables, bien sean de ejecución, o las que indiquemos nosotros. Esto puede jugar a nuestro favor en caso, por ejemplo, de querer desplegar ficheros distintos en cada servidor. Un ejemplo:

Supongamos que tenemos esta estructura de ficheros, con su fichero de *hosts* y su *playbook*:

```bash
root@ansible:~/multiple_webservers# tree
.
├── hosts
├── playbook.yml
└── webs
    ├── server1
    │   ├── index.html
    │   └── sitemap.xml
    └── server2
        ├── adminer.php
        └── index.php

3 directories, 6 files
root@ansible:~/multiple_webservers# cat hosts
[webservers]
server1
server2
root@ansible:~/multiple_webservers# cat playbook.yml
- hosts: webservers
  gather_facts: false
  tasks:
    - copy: src=webs/{{ inventory_hostname }}/ dest=/var/www/
root@ansible:~/multiple_webservers#
```

Lanzamos el *playbook* para aprovisionar los ficheros *web* a los servidores:

```bash
root@ansible:~/multiple_webservers# ansible-playbook -i hosts playbook.yml

PLAY ***************************************************************************

TASK [copy] ********************************************************************
changed: [server1]
changed: [server2]

PLAY RECAP *********************************************************************
server1                    : ok=1    changed=1    unreachable=0    failed=0
server2                    : ok=1    changed=1    unreachable=0    failed=0

root@ansible:~/multiple_webservers#
```

Y fácilmente comprobamos que cada servidor tiene los suyos:

```bash
root@ansible:~/multiple_webservers# ssh root@server1 ls /var/www/
index.html
sitemap.xml
root@ansible:~/multiple_webservers# ssh root@server2 ls /var/www/
adminer.php
index.php
root@ansible:~/multiple_webservers#
```

## Variables en el inventario

Hay algunas variables que dependen de la máquina en la que se ejecutan. Aunque es posible definir estructuras condicionales en los *playbooks*, no escala. Para no ensuciar los *playbooks*, las podemos definir en el fichero de *hosts*. Así pues, cada *grupo* puede tener sus propias variables; pueden ser variables "nuestras" o variables que entienda **ansible**. Como ejemplo, un *inventario* con variables de acceso:

```
root@ansible:~# cat hosts
[slaves]
10.0.0.2
10.0.0.3

[slaves:vars]
ansible_user = ansible
ansible_ssh_pass = s3cr3t
ansible_become = true
ansible_become_method = sudo
ansible_become_user = root
ansible_become_pass = s3cr3t
root@ansible:~#
```

De esta forma, y de acuerdo con la [documentación oficial](http://docs.ansible.com/ansible/intro_inventory.html#list-of-behavioral-inventory-parameters) de **ansible**, entraríamos con el usuario *ansible* para hacer seguidamente **sudo** para actuar con el usuario *root*.

```host
root@ansible:~# ansible -i hosts -m command -a id slaves
10.0.0.3 | SUCCESS | rc=0 >>
uid=0(root) gid=0(root) grupos=0(root)

10.0.0.2 | SUCCESS | rc=0 >>
uid=0(root) gid=0(root) grupos=0(root)

root@ansible:~#
```
