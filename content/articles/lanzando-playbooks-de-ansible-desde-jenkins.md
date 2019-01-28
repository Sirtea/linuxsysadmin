Title: Lanzando playbooks de Ansible desde Jenkins
Slug: lanzando-playbooks-de-ansible-desde-jenkins
Date: 2016-09-26 08:00
Category: Operaciones
Tags: ansible, playbook, jenkins, docker, git



Somos muchos los amantes del terminal para ejecutar nuestras tareas, sea con **Ansible** o con otras herramientas. A veces nos puede convenir dotar la herramienta de un entorno gráfico o web para que lo hagan otras personas. Aunque ya existe como producto **Ansible Tower**, su precio es prohibitivo para muchos.

Desarrollar una solución propia no suele ser una opción viable, pero afortunadamente, hay muchas soluciones que pueden satisfacer nuestras necesidades. Una de ellas es **Jenkins**.

En este tutorial y, por comodidad, nos vamos a ahorrar la instalación de **Jenkins** usando la imagen oficial para **Docker**. Sobre esta imagen vamos a añadir aquello que podamos necesitar para lanzar nuestros *playbooks*.

Vamos a adoptar un modelo de trabajo en el que nuestro inventario y nuestros *playbooks* están alojados en un servidor **git**. Nuestro **Jenkins** va a descargarse este repositorio como "fuente" de código y va a "construir" ejecutando los *playbooks* del repositorio.

## Preparando nuestro contenedor

Vamos a empezar por un *Dockerfile* que parte de la imagen oficial de **Jenkins**. A esa imagen habría que añadir **Ansible**, el cliente de **SSH** necesario por **Ansible** y el paquete **sshpass** para que pueda entrar en las máquinas usando autenticación tradicional de usuario y contraseña. El cliente de **git** ya viene en la imagen base.

Vamos a poner también en esta imagen una configuración de **Ansible** para el usuario *jenkins* que levanta la web, y el fichero con la contraseña de los *vaults*; de esta forma podemos versionar los fichero *vault* sin miedo a que se puedan descifrar si alguien obtiene una copia de nuestro repositorio.

Así nos quedaría el *Dockerfile*:

```bash
gerard@seginus:~/docker/jenkins_ansible$ cat Dockerfile 
FROM jenkins
USER root
RUN echo "deb http://ftp.debian.org/debian jessie-backports main" > /etc/apt/sources.list.d/backports.list && \
    apt-get update && \
    apt-get install -y openssh-client sshpass && \
    apt-get install -y -t jessie-backports ansible && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
ADD ansible.cfg /var/jenkins_home/.ansible.cfg
ADD vault-passfile /var/jenkins_home/.vault-passfile
USER jenkins
gerard@seginus:~/docker/jenkins_ansible$ 
```

Y los ficheros auxiliares:

```bash
gerard@seginus:~/docker/jenkins_ansible$ cat ansible.cfg 
[defaults]
host_key_checking = False
vault_password_file = /var/jenkins_home/.vault-passfile
gerard@seginus:~/docker/jenkins_ansible$ cat vault-passfile 
5up3r53cr37
gerard@seginus:~/docker/jenkins_ansible$ 
```

Construimos nuestra nueva imagen con las herramientas necesarias, con el comando habitual.

```bash
gerard@seginus:~/docker/jenkins_ansible$ docker build -t jenkins_ansible .
Sending build context to Docker daemon 4.096 kB
Step 1 : FROM jenkins
 ---> 2da1d8d90b7e
Step 2 : USER root
 ---> Running in f994443d27bd
 ---> 18e3df2ad21f
Removing intermediate container f994443d27bd
Step 3 : RUN echo "deb http://ftp.debian.org/debian jessie-backports main" > /etc/apt/sources.list.d/backports.list &&     apt-get update &&     apt-get install -y openssh-client sshpass &&     apt-get install -y -t jessie-backports ansible &&     apt-get clean &&     rm -rf /var/lib/apt/lists/*
 ---> Running in 2c3371ad61b0
Get:1 http://security.debian.org jessie/updates InRelease [63.1 kB]
Get:2 http://ftp.debian.org jessie-backports InRelease [166 kB]
Get:3 http://security.debian.org jessie/updates/main amd64 Packages [389 kB]
Get:4 http://ftp.debian.org jessie-backports/main amd64 Packages [879 kB]
Ign http://httpredir.debian.org jessie InRelease
Get:5 http://httpredir.debian.org jessie-updates InRelease [142 kB]
Get:6 http://httpredir.debian.org jessie-backports InRelease [166 kB]
Get:7 http://httpredir.debian.org jessie Release.gpg [2373 B]
Get:8 http://httpredir.debian.org jessie Release [148 kB]
Get:9 http://httpredir.debian.org jessie-updates/main amd64 Packages [17.6 kB]
Get:10 http://httpredir.debian.org jessie/main amd64 Packages [9032 kB]
Get:11 http://httpredir.debian.org jessie-backports/main amd64 Packages [879 kB]
Fetched 11.9 MB in 19s (606 kB/s)
Reading package lists...
Reading package lists...
Building dependency tree...
Reading state information...
openssh-client is already the newest version.
The following NEW packages will be installed:
  sshpass
0 upgraded, 1 newly installed, 0 to remove and 1 not upgraded.
Need to get 11.2 kB of archives.
After this operation, 65.5 kB of additional disk space will be used.
Get:1 http://httpredir.debian.org/debian/ jessie/main sshpass amd64 1.05-1 [11.2 kB]
debconf: delaying package configuration, since apt-utils is not installed
Fetched 11.2 kB in 0s (35.3 kB/s)
Selecting previously unselected package sshpass.
(Reading database ... 17572 files and directories currently installed.)
Preparing to unpack .../sshpass_1.05-1_amd64.deb ...
Unpacking sshpass (1.05-1) ...
Setting up sshpass (1.05-1) ...
Reading package lists...
Building dependency tree...
Reading state information...
The following extra packages will be installed:
  ieee-data libyaml-0-2 python-crypto python-ecdsa python-httplib2
  python-jinja2 python-markupsafe python-netaddr python-paramiko
  python-pkg-resources python-selinux python-yaml
Suggested packages:
  python-crypto-dbg python-crypto-doc python-jinja2-doc ipython
  python-netaddr-docs python-setuptools
The following NEW packages will be installed:
  ansible ieee-data libyaml-0-2 python-crypto python-ecdsa python-httplib2
  python-jinja2 python-markupsafe python-netaddr python-paramiko
  python-pkg-resources python-selinux python-yaml
0 upgraded, 13 newly installed, 0 to remove and 27 not upgraded.
Need to get 3359 kB of archives.
After this operation, 19.5 MB of additional disk space will be used.
...  
 ---> d8ed3d7ffdb3
Removing intermediate container 2c3371ad61b0
Step 4 : ADD ansible.cfg /var/jenkins_home/.ansible.cfg
 ---> cd63da025c0a
Removing intermediate container fe8b889557ae
Step 5 : ADD vault-passfile /var/jenkins_home/.vault-passfile
 ---> 6cb532911067
Removing intermediate container bc522e9f464a
Step 6 : USER jenkins
 ---> Running in 6c0f9cde92e5
 ---> 89e5cae2d376
Removing intermediate container 6c0f9cde92e5
Successfully built 89e5cae2d376
gerard@seginus:~/docker/jenkins_ansible$ 
```

Levantamos un contenedor para la nueva imagen creada, de la misma forma que levantaríamos la imagen de **Jenkins** oficial. Mas información en [Docker Hub](https://hub.docker.com/_/jenkins/).

```bash
gerard@seginus:~/docker/jenkins_ansible$ docker run -p 8080:8080 -d jenkins_ansible
f9b6a9d23fde25411cd2086d13b7a171633eb2cf0b18295fde89c4466c08ef54
gerard@seginus:~/docker/jenkins_ansible$ 
```

Ya de paso, levantamos otras 4 máquinas como las que se indican en [otro artículo]({filename}/articles/controlando-contenedores-docker-con-ansible.md) para que ejecuten nuestros *playbooks*.

```bash
gerard@seginus:~/docker/jenkins_ansible$ docker run -d slave
ae3f8fe7d4448566c3481069d6c85d74ea3c6df7b9506c3f86e271247f5cbc52
gerard@seginus:~/docker/jenkins_ansible$ docker run -d slave
c27f99a68d0e4a5d5d9897d3971f6a230c10ee44239bce2deb85a2e6e31e6536
gerard@seginus:~/docker/jenkins_ansible$ docker run -d slave
0d33995bacf4d266f4f1bb2afc86a92b586be569ca10b1584bf48c5aed6b1277
gerard@seginus:~/docker/jenkins_ansible$ docker run -d slave
221ae5b4c1cfe171530d5d9e9663222292da72144fdf2f62589acc50b72f3f2e
gerard@seginus:~/docker/jenkins_ansible$ 
```

## Configurando nuestro Jenkins

Ya podemos abrir la página de nuestro contenedor, de forma que se puedan efectuar las configuraciones iniciales. Nos vamos a dirigir a <http://localhost:8080/>, que es desde donde se va a controlar nuestro servidor de ahora en adelante.

La parte mas importante de nuestro despliegue de **Jenkins** son los *plugins*. En nuestro caso, solo queremos clonar nuestros *playbooks* desde **git** y lanzarlos mediante **Ansible**. Para ello necesitamos estos dos *plugins*: *git plugin* y *ansible plugin*. Se pueden instalar en la primera visita a nuestro contenedor o a *posteriori*. Los instalamos.

Y finalmente tenemos un **Jenkins** funcional aunque si ninguna tarea configurada.

![Ansible desde Jenkins 01]({static}/images/ansible_jenkins_01.jpg)

## El repositorio de playbooks

Necesitamos algún lugar desde donde obtener nuestros *playbooks*. De acuerdo con la decisión del flujo de trabajo van a estar alojados en un servidor **git**, y en este caso, voy a usar un repositorio de usar y tirar en [GitHub](https://github.com/).

Por poner a nuestro repositorio alguna estructura, he usado dos carpetas: una para contener los *playbooks* y otra para el inventario. La carpeta del inventario es similar a la de [este otro artículo]({filename}/articles/encriptando-datos-sensibles-con-ansible.md).

```bash
gerard@seginus:~/docker/ansible$ tree
.
├── inventory
│   ├── hosts
│   └── vault
└── playbooks
    ├── ping_all.yml
    └── ping_some.yml

2 directories, 4 files
gerard@seginus:~/docker/ansible$ 
```

En *inventory/vault* tenemos los datos de conexión a las máquinas, como indica el artículo antes citado. El resto de ficheros son los *playbooks* que vamos a usar, y los *hosts* que tenemos en sus grupos correspondientes. Hay que tirar de imaginación para imaginar un *playbook* un poco mas útil.

```bash
gerard@seginus:~/docker/ansible$ cat inventory/hosts 
[group1]
172.17.0.3
172.17.0.4

[group2]
172.17.0.5
172.17.0.6
gerard@seginus:~/docker/ansible$ cat playbooks/ping_all.yml 
- hosts: all
  tasks:
    - ping:
gerard@seginus:~/docker/ansible$ cat playbooks/ping_some.yml 
- hosts: "{{ target }}"
  tasks:
    - ping:
gerard@seginus:~/docker/ansible$ 
```

## Creando una tarea básica

Vamos a crear una tarea que consista en lanzar el fichero *playbooks/ping_all.yml*. Para ello pinchamos en el enlace "create new job", le damos un nombre (por ejemplo "Ping All") y lo creamos de tipo "Freestyle project".

El primer paso consiste en obtener los *playbooks* del repositorio. Para ello rellenaremos el apartado "Source code management", eligiendo "Git" e indicando la *URL* del repositorio.

![Ansible desde Jenkins 02]({static}/images/ansible_jenkins_02.jpg)

Lo siguiente es indicar un "Build step" que se "Invoke Ansible Playbook". Hay que indicar el *playbook* desde la carpeta pertinente, de forma relativa. Eso significa que en nuestro caso es *playbooks/ping_all.yml*. Adicionalmente vamos a indicar que el fichero de inventario es la carpeta *inventory*, que es lo que se le va a pasar a **Ansible**.

![Ansible desde Jenkins 03]({static}/images/ansible_jenkins_03.jpg)

Le damos a guardar y ya tenemos nuestra tarea. Bastará con lanzar la tarea con "Build now" y esperar resultados, en "Console Output" de la ejecución en curso.

![Ansible desde Jenkins 04]({static}/images/ansible_jenkins_04.jpg)

## Creando una tarea con parámetros

Muchas de las tareas que hacemos son repetitivas. Cambian las versiones de código a desplegar, los entornos, los proyectos y poco mas. ¿No sería maravilloso tener un solo *playbook* que admita parámetros? **Jenkins** nos ofrece la posibilidad de añadir parámetros, que luego pueden ser usados en los "Build steps", por ejemplo, para pasárselas a los *playbooks*.

Vamos a crear otra tarea, esta vez llamada "Ping Some". Va a ser idéntica a la otra, pero con el *playbook* llamado *ping_some.yml*. Vamos a marcar la casilla "This project is parameterized" en la casilla general y le añadiremos un parámetro, al que llamaremos "target" y va a ser un "Choice Parameter" con los valores "all", "group1" y "group2".

![Ansible desde Jenkins 05]({static}/images/ansible_jenkins_05.jpg)

Vamos a los "Build steps" a poner ese parámetro al comando *ansible*. Tras dar al botón "Advanced..." podemos poner mas parámetros para **Ansible**. Esto nos permite poner "-e target=$target" para que el *playbook* reciba un parámetro *target* que contenga el valor del mismo parámetro en **Jenkins**.

![Ansible desde Jenkins 06]({static}/images/ansible_jenkins_06.jpg)

Tras salvar la tarea, vemos que la opción de "Build" se ha convertido en "Build with Parameters", y podemos elegir entre los valores específicos.

![Ansible desde Jenkins 07]({static}/images/ansible_jenkins_07.jpg)

Y con esto conseguimos pasar parámetros al *playbook*, que pueden ser texto libre, elecciones simples o valores fijos. Con un poco de imaginación, estos parámetros nos pueden ayudar mucho, en el sentido de no repetirnos.

![Ansible desde Jenkins 08]({static}/images/ansible_jenkins_08.jpg)
