Title: Instalando ansible para gestionar servidores
Slug: instalando-ansible-para-gestionar-servidores
Date: 2016-04-11 08:00
Category: Operaciones
Tags: linux, redhat, centos, python, ansible, ssh, virtualenv



Cuando nos encontramos delante de servidores únicos, es bastante fácil su gestión. Sin embargo, cuando tenemos 8 instancias de cada tipo de servidor, las tareas se vuelven lentas y repetitivas. Podemos incluso automatizar la gestión de una sola máquina para hacer su entorno fácilmente reproducible, en vistas a su reconstrucción.

Para ello existen algunas herramientas capaces de modificar los servidores, sea mediante un protocolo de **pull** (**puppet**, **chef**) que tienen agentes capaces de pedir a un servidor central las reglas a aplicarse, o mediante un protocolo de **push** (**fabric**, **ansible**) que simplemente son formas de enviar esas órdenes desde el servidor central.

Hoy vamos a instalar **ansible**, herramienta que considero muy interesante por su simplicidad; carece de agentes activos, funcionando como un conjunto de *scripts* en una máquina cualquiera que actúa de servidor y utilizando el protocolo **SSH** para empujar los *scripts*, que se ejecutan con un **python** en el servidor destino.

Si estuviéramos en una máquina tipo **Debian**/**Ubuntu**, la instalación es tan fácil como lanzar **apt-get**:

```bash
root@server:~$ apt-get install ansible
...  
root@server:~$ 
```

Sin embargo, instalarlo a nivel de sistema es un problema en algunos entornos, así que podemos instalarlo en una carpeta local, concretamente en un **virtualenv** dedicado en nuestra carpeta personal. Esta es la forma que se explica en este tutorial.

Empezaremos con un servidor cualquiera; al no tener agentes activos y ser *scripts*, nos vale cualquiera. En este caso se ha usado una máquina tipo **RedHat**. Realmente no nos importa demasiado la versión de **python** que utilice.

```bash
[gerard@toolbox ~]$ cat /etc/redhat-release
Red Hat Enterprise Linux Server release 6.7 (Santiago)
[gerard@toolbox ~]$ python -V
Python 2.6.6
[gerard@toolbox ~]$
```

## Creación del virtualenv con ansible

Vamos a construir el **virtualenv** desde cero. Si nos interesara hacerlo en otra máquina en la que tengamos permisos para instalar paquetes, bastaría con copiar la carpeta del **virtualenv** en el mismo sitio, y sin instalar nada mas.

Las únicas dependencias que se necesitan para construir el **virtualenv** es **python**, **gcc** y **python-devel** (o **python-dev** si se tratara de una máquina tipo **Debian**/**Ubuntu**). Como ya tenemos **gcc** y **python**, instalamos solamente **python-devel**.

```bash
gerard@toolbox:~$ sudo yum install python-devel
Loaded plugins: product-id, subscription-manager
This system is not registered to Red Hat Subscription Management. You can use subscription-manager to register.
Setting up Install Process
...
Installed:
  python-devel.x86_64 0:2.6.6-64.el6

Complete!
gerard@toolbox:~$
```

Para no instalar nada innecesario en la máquina, vamos a descargar el comando *virtualenv*, que va a cumplir su función y va a ser eliminado. Lo descargamos y lo descomprimimos, en cualquier carpeta.

```bash
[gerard@toolbox ~]$ wget https://pypi.python.org/packages/source/v/virtualenv/virtualenv-15.0.1.tar.gz
--2016-04-05 11:54:27--  https://pypi.python.org/packages/source/v/virtualenv/virtualenv-15.0.1.tar.gz
Resolving pypi.python.org... 23.235.43.223
Connecting to pypi.python.org|23.235.43.223|:443... connected.
HTTP request sent, awaiting response... 200 OK
Length: 1842776 (1.8M) [application/octet-stream]
Saving to: “virtualenv-15.0.1.tar.gz”

100%[========================================================================================>] 1,842,776   2.90M/s   in 0.6s

2016-04-05 11:54:28 (2.90 MB/s) - “virtualenv-15.0.1.tar.gz” saved [1842776/1842776]

[gerard@toolbox ~]$ tar xzf virtualenv-15.0.1.tar.gz
[gerard@toolbox ~]$
```

Utilizamos el comando *virtualenv* para generar la estructura contenedora, de la misma manera que otros *virtualenv*.

```bash
[gerard@toolbox ~]$ ./virtualenv-15.0.1/virtualenv.py ansible
New python executable in /home/gerard/ansible/bin/python
Installing setuptools, pip, wheel...done.
[gerard@toolbox ~]$
```

Hacemos limpieza de **virtualenv**, que ya no vamos a necesitar mas.

```bash
[gerard@toolbox ~]$ rm -R virtualenv-15.0.1*
[gerard@toolbox ~]$
```

La instalación es la misma que haríamos con cualquier módulo de **python**, con la excepción que va a generar fichero *.so*, dependientes de la arquitectura del procesador que los genere. Si movéis el **virtualenv**, tened esto en cuenta.

```bash
[gerard@toolbox ~]$ source ansible/bin/activate
(ansible) [gerard@toolbox ~]$ pip install ansible
DEPRECATION: Python 2.6 is no longer supported by the Python core team, please upgrade your Python. A future version of pip will drop support for Python 2.6
Collecting ansible
...
Installing collected packages: ecdsa, pycrypto, paramiko, MarkupSafe, jinja2, PyYAML, ansible
Successfully installed MarkupSafe-0.23 PyYAML-3.11 ansible-2.0.1.0 ecdsa-0.13 jinja2-2.8 paramiko-1.16.0 pycrypto-2.6.1
(ansible) [gerard@toolbox ~]$ deactivate
[gerard@toolbox ~]$
```

## Controlando nuestro primer esclavo

Vamos a habilitar una máquina cualquiera como receptora de **ansible**. Los puntos básicos a tener en cuenta es que vamos a habilitar **SSH** por claves (sin contraseña) y debemos asegurar que la máquina destino tiene un **python** instalado.

Empezaremos generando las claves privada y pública en la máquina controladora. Esto se hace mediante el comando *ssh-keygen*.

```bash
[gerard@toolbox ~]$ ssh-keygen
Generating public/private rsa key pair.
Enter file in which to save the key (/home/gerard/.ssh/id_rsa):
Created directory '/home/gerard/.ssh'.
Enter passphrase (empty for no passphrase):
Enter same passphrase again:
Your identification has been saved in /home/gerard/.ssh/id_rsa.
Your public key has been saved in /home/gerard/.ssh/id_rsa.pub.
The key fingerprint is:
8e:74:f9:49:70:ba:15:d0:93:ff:88:5a:6a:f5:ad:cd gerard@toolbox
The key's randomart image is:
+--[ RSA 2048]----+
|        .. .     |
|         .+      |
|        . oo     |
|         = ..    |
|      . S o. o   |
|     . + =+.. .  |
|      . o=o. .   |
|        +   .o.  |
|       .    ..E  |
+-----------------+
[gerard@toolbox ~]$
```

Esto va a generar una carpeta *.ssh* en nuestra carpeta personal, con dos ficheros generados: *id_rsa* (clave privada) e *id_rsa.pub* (clave pública). La idea es que la clave privada se va a ofrecer automáticamente cuando se haga **ssh**, y si la parte pública esta en *~/.ssh/authorized_keys* del usuario remoto, el login se hace automático.

La clave privada es sagrada, y no debe entregarse a nadie. Sin embargo, la parte pública es la que se va a poner en todas las máquinas controladas. Se trata de una línea que vamos a añadir al *authorized_keys* de todas las máquinas, así que la apuntamos en algún sitio.

```bash
[gerard@toolbox ~]$ cat .ssh/id_rsa.pub
ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEAo/hobjbaSNX4zP/wjke5FY910xk5VwW0WaAO10ILAbvhuswdghLbMBdgt+4tWIwFM4DgOwA62wQ04lPsxpQ7Ya4VVmVVZLN5oN2BGQ2ixV6ofB8PA51vNDO5p0xz4ExYebXu8qshrOi4ulcSsc1rEDhlT+zZkYApjVOcgmO7T7T6149XWWBH0YSFEOto8qF+YiyS2yMlVy5p6QruHNPwcr6kC0z13aYrNUnk5VXFwlOSRtUTYMZ+c0ysh49uTDm50AWoccuDUK0v0juNWnHfQw1PFYLaQZLmJEWIkIsND3pBACHdFTyJDGDOB2Kuw+DCaAxp5vqPt5zFuidVS0h5Mw== gerard@toolbox
[gerard@toolbox ~]$
```

En la máquina controlada, añadimos la línea de la clave pública en el fichero *authorized_keys*. Vamos a controlar login automático contra el usuario *root* en nuestra máquina de ejemplo misma.

```bash
[root@toolbox ~]# cat .ssh/authorized_keys
ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEAo/hobjbaSNX4zP/wjke5FY910xk5VwW0WaAO10ILAbvhuswdghLbMBdgt+4tWIwFM4DgOwA62wQ04lPsxpQ7Ya4VVmVVZLN5oN2BGQ2ixV6ofB8PA51vNDO5p0xz4ExYebXu8qshrOi4ulcSsc1rEDhlT+zZkYApjVOcgmO7T7T6149XWWBH0YSFEOto8qF+YiyS2yMlVy5p6QruHNPwcr6kC0z13aYrNUnk5VXFwlOSRtUTYMZ+c0ysh49uTDm50AWoccuDUK0v0juNWnHfQw1PFYLaQZLmJEWIkIsND3pBACHdFTyJDGDOB2Kuw+DCaAxp5vqPt5zFuidVS0h5Mw== gerard@toolbox
[root@toolbox ~]#
```

Una vez que tengamos las claves **SSH** distribuidas, y **python** instalado en las máquinas controladas, podemos probar. Para ello, vamos a añadir esta máquina en el fichero de *hosts*, sea por nombre o por dirección IP.

```bash
[gerard@toolbox ~]$ cat hosts
127.0.0.1
[gerard@toolbox ~]$
```

Y lanzamos el módulo **ping** a todas las máquinas (que solo es la de test, de momento).

```bash
[gerard@toolbox ~]$ ./ansible/bin/ansible -u root -i hosts -m ping all
127.0.0.1 | SUCCESS => {
    "changed": false,
    "ping": "pong"
}
[gerard@toolbox ~]$
```

## Creando un fichero de configuración

Las opciones por defecto de **ansible** son bastante correctas, pero hay algunos parámetros que se pueden poner por fichero de configuración; esto nos facilita bastante las cosas. Este fichero de configuración es el primero que se encuentre siguiendo este orden:

* ANSIBLE_CONFIG (lo que diga esta variable de entorno)
* ansible.cfg (en el directorio actual de trabajo)
* .ansible.cfg (en la carpeta personal de nuestro usuario)
* /etc/ansible/ansible.cfg

De hecho, si os parece bien utilizar carpetas de sistema, la última opción es la normal. Sin embargo, me interesa restringirme a mi carpeta local, por falta de permisos habitualmente.

De la misma manera, el fichero de *hosts* se busca en un sitio concreto, que con la configuración estándar es */etc/ansible/hosts*, a menos que se indique explícitamente el flag *-i* en los comandos.

Para evitar usar estos dos ficheros fuera de nuestra carpeta, vamos a crearlos en el **virtualenv** creado, añadiéndolos en una carpeta *etc*, que vamos a crear. Todos los parámetros se van a poner en el fichero de configuración y vamos a explicitar la localización del fichero de configuración.

```bash
[gerard@toolbox ~]$ mkdir ansible/etc
[gerard@toolbox ~]$ cat ansible/etc/ansible.cfg
[defaults]
inventory = /home/gerard/ansible/etc/hosts
host_key_checking = False
remote_user = root
[gerard@toolbox ~]$ mv hosts ansible/etc/
[gerard@toolbox ~]$
```

Tras crear la configuración, la probamos:

```bash
[gerard@toolbox ~]$ ANSIBLE_CONFIG=/home/gerard/ansible/etc/ansible.cfg ./ansible/bin/ansible -m ping all
127.0.0.1 | SUCCESS => {
    "changed": false,
    "ping": "pong"
}
[gerard@toolbox ~]$
```

Para conseguir eliminar el *path* absoluto del binario de ansible, lo añadimos en la variable de entorno *PATH*. Para nuestra comodidadd, podemos definir ambas variables de entorno en el fichero *.bashrc*. Este fichero se va a activar cada vez que se inicie **bash**; para no cerrar y abrir sesión lo incluimos a mano.

```bash
[gerard@toolbox ~]$ tail -2 .bashrc
export ANSIBLE_CONFIG=~/ansible/etc/ansible.cfg
export PATH=~/ansible/bin:$PATH
[gerard@toolbox ~]$ source .bashrc
[gerard@toolbox ~]$
```

Y finalmente obtenemos la versión mínima del comando a ejecutar.

```bash
[gerard@toolbox ~]$ ansible -m ping all
127.0.0.1 | SUCCESS => {
    "changed": false,
    "ping": "pong"
}
[gerard@toolbox ~]$
```

Ahora solo queda poner mas servidores en el fichero de *hosts* y lanzar comandos y *playbooks* útiles contra los mismos.
