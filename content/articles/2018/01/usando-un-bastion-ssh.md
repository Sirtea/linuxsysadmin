---
title: "Usando un bastión SSH"
slug: "usando-un-bastion-ssh"
date: 2018-01-02
categories: ['Operaciones']
tags: ['ssh', 'bastion', 'pubkey']
---

Hoy vamos a presentar un patrón de conectividad para acceder a un conjunto de máquinas, exponiendo solamente una de ellas, y aprovechando el protocolo SSH para pasar el tráfico a través, de forma transparente. Eso facilita los casos en los que no podemos tener una VPN o una red dedicada.<!--more-->

Vamos a suponer que tenemos un entorno con 4 máquinas, una de las cuales tiene el protocolo SSH abierto a una red menos confiable. Por supuesto, en casos así se recomienda encarecidamente no permitir la autenticación por claves, ya que os pueden acabar entrando usando ataques de fuerza bruta o de diccionario.

![SSH bastion host](/images/ssh-bastion-host.png)

En nuestro caso vamos a llamar a la primera máquina como *bastion* y las otras tres como *server1*, *server2* y *server3* respectivamente. Todas ellas disponen de acceso por claves SSH y un usuario dedicado. No hace falta que ninguna de las máquinas tenga las mismas claves ni los mismos usuarios, pero hacerlo nos va a facilitar bastante la configuración SSH del cliente. En nuestro caso vamos a usar la misma clave para todos y el mismo usuario *jump*.

El truco está en usar la directiva *ProxyCommand* para que el tráfico hacia los servidores privados se haga **a través** de una sesión SSH al servidor *bastion*. Es importante decir que para que esto pase, el servidor *bastion* debe poder resolver el nombre de la máquina que pasemos al comando SSH, ya que es lo que se va a usar para acceder a la misma.

Para hacerme la vida más fácil he creado los usuarios mediante un *playbook* de **ansible**, aunque esto es opcional. Basta con crear los usuarios y poner la clave SSH pública en el fichero *authorized_keys*.

```bash
gerard@purgatory:~$ cat create_users.yml 
- hosts: all
  gather_facts: no
  tasks:
    - user: name=jump shell=/bin/bash state=present
    - file: dest=/home/jump/.ssh owner=jump group=jump state=directory
    - copy: src=../keys/id_jump.pub dest=/home/jump/.ssh/authorized_keys owner=jump group=jump
gerard@purgatory:~$ 
```

A partir de aquí definimos dos reglas en nuestra configuración SSH cliente; una para el servidor *bastion* (que no necesita de un *proxy* SSH) y otra serie de reglas para las que sí necesitan del *proxy*. Fijaos que cuentan cada una con su propio usuario y su clave SSH, que son la misma, pero podrían ser diferentes. Además, como la configuración de los servidores privados coincide, podemos acortar usando las mismas directivas para los 3 *hosts*.

```bash
gerard@purgatory:~$ cat .ssh/config 
...
Host bastion
	HostName 172.20.0.4
	User jump
	IdentityFile ~/.ssh/id_jump

Host server1 server2 server3
	User jump
	IdentityFile ~/.ssh/id_jump
	ProxyCommand ssh -F ssh_config -W %h:%p bastion
gerard@purgatory:~$ 
```

Solo nos queda comprobar que podemos acceder a la máquina *bastion* sin problemas:

```bash
gerard@purgatory:~$ ssh bastion uname -a
Linux bastion 3.16.0-4-amd64 #1 SMP Debian 3.16.36-1+deb8u2 (2016-10-19) x86_64 GNU/Linux
gerard@purgatory:~$ 
```

Y también podemos comprobar que llegamos a las máquinas a las que de otra forma no llegaríamos:

```bash
gerard@purgatory:~$ ssh server1 uname -a
Linux server1 3.16.0-4-amd64 #1 SMP Debian 3.16.36-1+deb8u2 (2016-10-19) x86_64 GNU/Linux
gerard@purgatory:~$ ssh server2 uname -a
Linux server2 3.16.0-4-amd64 #1 SMP Debian 3.16.36-1+deb8u2 (2016-10-19) x86_64 GNU/Linux
gerard@purgatory:~$ ssh server3 uname -a
Linux server3 3.16.0-4-amd64 #1 SMP Debian 3.16.36-1+deb8u2 (2016-10-19) x86_64 GNU/Linux
gerard@purgatory:~$ 
```

Es interesante comprobar que tras acceder desde nuestra máquina, la segunda sesión nos informa que la anterior se realizó desde *bastion*, y no desde la nuestra; la nuestra se conecta a *bastion* que es la que se conecta al resto, llegando a servidores en los que no habríamos llegado de otra manera.

```bash
gerard@aldebaran:~$ ssh server1
...  
Last login: Thu Nov 17 14:35:30 2016 from bastion
jump@server1:~$ 
```
