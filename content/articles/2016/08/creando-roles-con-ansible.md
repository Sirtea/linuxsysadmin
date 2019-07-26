---
title: "Creando roles con ansible"
slug: "creando-roles-con-ansible"
date: 2016-08-29
categories: ['Operaciones']
tags: ['ansible', 'playbook', 'rol']
---

Ya vimos que es muy fácil crear varias máquinas iguales con **ansible**. A veces nos puede interesar disponer de recetas y decidir en un *playbook* general cuales de ellas ponemos en cada servidor. Una receta podría añadir un servidor de aplicaciones mientras que otra podría habilitarnos una bases de datos.<!--more-->

Esto nos permite combinar las recetas para desplegar toda la funcionalidad de nuestro servicio, distribuyéndolas entre nuestros servidores de acuerdo a las necesidades. Como ejemplo, podríamos poner el servidor de *PHP* y el de *MySQL* en recetas distintas; pondríamos las 2 en el mismo servidor para un entorno de test, y podríamos separar los servicios entre servidores (incluso replicando) en entornos mas profesionales.

Para esta demostración, vamos a crear *roles* para un entorno de un balanceador y dos servidores web normales. En ambos casos, el servicio estándar va a ser **nginx**, lo que nos abre a la posibilidad de reusar partes comunes, usando dependencias entre ellos.

También podemos encontrar roles prefabricados y listos para usarse en [Ansible Galaxy](https://galaxy.ansible.com/).

## El entorno

Disponemos de 3 máquinas en el entorno, y de otra máquina desde la que lanzaremos los *playbooks*. Hemos utilizado los contenedores **Docker** de [otro artículo]({{< relref "/articles/2016/06/controlando-contenedores-docker-con-ansible.md" >}}) por comodidad.

```bash
~ # cat inventory/hosts 
[balancer]
slave1

[web]
slave2
slave3
~ # ansible -i inventory/ -m ping balancer
slave1 | SUCCESS => {
    "changed": false, 
    "ping": "pong"
}
~ # ansible -i inventory/ -m ping web
slave2 | SUCCESS => {
    "changed": false, 
    "ping": "pong"
}
slave3 | SUCCESS => {
    "changed": false, 
    "ping": "pong"
}
~ # 
```

## Como crear un rol

Lo primero para entender que es un rol y como funcionan es mirar en [la documentación](http://docs.ansible.com/ansible/playbooks_roles.html#roles). Es especialmente interesante saber que tiene cada carpeta y para que sirve; solo voy a explicar las que usemos.

Lanzamos el comando **ansible-galaxy** para crear un rol vacío:

```bash
~ # ansible-galaxy init --offline roles/test
- roles/test was created successfully
~ # tree roles/test/
roles/test/
├── README.md
├── defaults
│   └── main.yml
├── files
├── handlers
│   └── main.yml
├── meta
│   └── main.yml
├── tasks
│   └── main.yml
├── templates
├── tests
│   ├── inventory
│   └── test.yml
└── vars
    └── main.yml

8 directories, 8 files
~ # 
```

Las carpetas mas interesantes son la de *tasks* la de *meta*, la de *files* y la de *templates*.

* **tasks** &rarr; es donde se ponen los pasos a ejecutar en el *playbook*.
* **meta** &rarr; es donde se especifican las dependencias con otros roles.
* **files** y **templates** &rarr; aquí se ponen los ficheros que se utilizan en los módulos de ficheros y de plantillas, respectivamente.

A partir de aquí se trata de eliminar las que no usemos y rellenar las que sí vayamos a usar.

## Diseño de roles

Queremos preparar 2 tipos distintos de máquinas: el balanceador y los servidores web. En ambos casos se trata de instalar **nginx**, poner una configuración para la tarea que desempeñen, y en caso de los servidores web, poner el contenido estático.

Vamos a crear un *role* para el balanceador, y otro para los servidores web. Siguiendo la filosofía [DRY (Don't repeat yourself)](https://es.wikipedia.org/wiki/No_te_repitas), vamos a delegar la instalación de **nginx** a un tercer *role*, que a su vez será una dependencia para los otros dos.

Eso nos da 3 roles, con una estructura de ficheros simple; un rol para el **nginx** que solo ejecuta tareas, otro para el balanceador (con la dependencia y los ficheros auxiliares) y otro rol para el servidor web (con la dependencia y sus ficheros).

```bash
~ # tree roles/
roles/
├── balancer
│   ├── meta
│   │   └── main.yml
│   ├── tasks
│   │   └── main.yml
│   └── templates
│       └── balancer.j2
├── nginx
│   └── tasks
│       └── main.yml
└── web
    ├── meta
    │   └── main.yml
    ├── tasks
    │   └── main.yml
    └── templates
        ├── index.j2
        └── web.j2

10 directories, 8 files
~ # 
```

### El rol de nginx

El único propósito de este rol es instalar **nginx**, retirar el *site* que viene por defecto, y asegurar que esté corriendo el servicio (en contenedores **docker** no se levantan tras instalarse). La idea es que el resto de roles van a poner una configuración y a recargar el **nginx** para aplicarla; así que de momento, nos vale.

```bash
~ # cat roles/nginx/tasks/main.yml 
---
- name: Install nginx
  apt: name=nginx-light state=installed
- name: Ensure example virtualhost is not there
  file: path=/etc/nginx/sites-enabled/default state=absent
- name: Ensure nginx is running
  service: name=nginx state=started
~ # 
```

El resto de carpetas son innecesarias, así que las borramos.

### El rol web

Este rol espera tener **nginx** instalado y se limita a poner la configuración del mismo, así como el contenido web.

El primer paso es declarar que tenemos una dependencia con el rol *nginx*. Esto se hace en la carpeta *meta*, y nos asegura que se habrá ejecutado antes el rol *nginx*.

```bash
~ # cat roles/web/meta/main.yml 
dependencies:
  - nginx
~ # 
```

Ahora podemos especificar los pasos para tener nuestro rol completo, partiendo de un rol *nginx* aplicado. Básicamente se trata de poner la directiva *server* que nos interese, el contenido web en */var/www/html* y hacer un *reload* del **nginx**.

Como punto interesante, se han usado plantillas para crear los ficheros destino. Esto nos permite crear las configuraciones basándonos en variables, que vendrán del *playbook* general. En el caso concreto de la configuración del **nginx** no era necesario usar plantillas porque no usa variables; se podría haber puesto el fichero en la carpeta *files* y usar el módulo *copy*.

```bash
~ # cat roles/web/tasks/main.yml 
---
- name: Put content virtualhost
  template: src=web.j2 dest=/etc/nginx/sites-enabled/web
- name: Put HTML files
  template: src=index.j2 dest=/var/www/html/index.html
- name: Reload nginx configuration
  service: name=nginx state=reloaded
~ # 
```

Finalmente, necesitamos poner las plantillas en *templates*, siguiendo la sintaxis adecuada.

```bash
~ # cat roles/web/templates/web.j2 
server {
	root /var/www/html;
	server_name _;
}
~ # cat roles/web/templates/index.j2 
Hello from {{ name }}
~ # 
```

Eliminamos todas las carpetas que no nos sirven, y hemos acabado.

### El rol balancer

Partiendo de que tenemos **nginx** instalado, solo hay que poner una configuración concreta para que se haga balanceo, tras lo que haremos un *reload* del **nginx**.

Como en el caso anterior, tenemos que declarar la dependencia con el rol *nginx*.

```bash
~ # cat roles/balancer/meta/main.yml 
dependencies:
  - nginx
~ # 
```

Los pasos, de forma análoga al caso anterior, se ponen en la carpeta *tasks*.

```bash
~ # cat roles/balancer/tasks/main.yml 
---
- name: Put balancer virtualhost
  template: src=balancer.j2 dest=/etc/nginx/sites-enabled/balancer
- name: Reload nginx configuration
  service: name=nginx state=reloaded
~ # 
```

Y finalmente ponemos la plantilla para la configuración en *templates*. Nuevamente esperamos la variable *backends* desde el *playbook* principal, que es una lista de servidores de *backend*.

```bash
~ # cat roles/balancer/templates/balancer.j2 
upstream backends {
{% for backend in backends %}
	server {{ backend }};
{% endfor %}
}

server {
	server_name _;
	location / {
		proxy_pass http://backends;
	}
}
~ # 
```

Y limpiamos el resto de carpetas.

## Usando los roles

Disponemos de tres máquinas, accesibles desde la red, con los nombres *slave1*, *slave2* y *slave3*. Como hemos visto en el fichero de inventario, el *slave1* va a ejercer de balanceador, mientras que los otros dos harán de servidores web.

Para ello solo hay que asignarles el rol que les toca, con las variables que estos roles necesitan. Teniendo los roles preparados, es tan fácil como indicar que servidor hace cada rol, indicando las variables que nos interesan en este entorno concreto.

```bash
~ # cat myenv.yml 
- name: Install balancer
  hosts: balancer
  roles:
    - role: balancer
      backends:
        - slave2:80
        - slave3:80
- name: Install webservers
  hosts: web
  roles:
    - role: web
      name: "web_{{ ansible_hostname }}"
~ # 
```

Lanzamos el *playbook*, para que nos monte nuestro entorno:

```bash
~ # ansible-playbook -i inventory/ myenv.yml 

PLAY [Install balancer] ********************************************************

TASK [setup] *******************************************************************
ok: [slave1]

TASK [nginx : Install nginx] ***************************************************
changed: [slave1]

TASK [nginx : Ensure example virtualhost is not there] *************************
changed: [slave1]

TASK [nginx : Ensure nginx is running] *****************************************
changed: [slave1]

TASK [balancer : Put balancer virtualhost] *************************************
changed: [slave1]

TASK [balancer : Reload nginx configuration] ***********************************
changed: [slave1]

PLAY [Install webservers] ******************************************************

TASK [setup] *******************************************************************
ok: [slave2]
ok: [slave3]

TASK [nginx : Install nginx] ***************************************************
changed: [slave2]
changed: [slave3]

TASK [nginx : Ensure example virtualhost is not there] *************************
changed: [slave3]
changed: [slave2]

TASK [nginx : Ensure nginx is running] *****************************************
changed: [slave3]
changed: [slave2]

TASK [web : Put content virtualhost] *******************************************
changed: [slave3]
changed: [slave2]

TASK [web : Put HTML files] ****************************************************
changed: [slave2]
changed: [slave3]

TASK [web : Reload nginx configuration] ****************************************
changed: [slave3]
changed: [slave2]

PLAY RECAP *********************************************************************
slave1                     : ok=6    changed=5    unreachable=0    failed=0   
slave2                     : ok=7    changed=6    unreachable=0    failed=0   
slave3                     : ok=7    changed=6    unreachable=0    failed=0   

~ # 
```

Y verificamos que todo funciona como debe:

```bash
~ # for i in `seq 1 8`; do wget -qO- http://slave2:80/; done
Hello from web_slave2
Hello from web_slave2
Hello from web_slave2
Hello from web_slave2
Hello from web_slave2
Hello from web_slave2
Hello from web_slave2
Hello from web_slave2
~ # for i in `seq 1 8`; do wget -qO- http://slave3:80/; done
Hello from web_slave3
Hello from web_slave3
Hello from web_slave3
Hello from web_slave3
Hello from web_slave3
Hello from web_slave3
Hello from web_slave3
Hello from web_slave3
~ # for i in `seq 1 8`; do wget -qO- http://slave1:80/; done
Hello from web_slave2
Hello from web_slave3
Hello from web_slave2
Hello from web_slave3
Hello from web_slave2
Hello from web_slave3
Hello from web_slave2
Hello from web_slave3
~ # 
```

En caso de cambiar a un entorno con 8 servidores web, podemos usar los roles que tenemos y solamente cambiar *myenv.yml*.

***Fácil, ¿no?***
