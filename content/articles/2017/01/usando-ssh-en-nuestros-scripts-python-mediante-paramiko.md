---
title: "Usando SSH en nuestros scripts python mediante paramiko"
slug: "usando-ssh-en-nuestros-scripts-python-mediante-paramiko"
date: 2017-01-23
categories: ['Desarrollo']
tags: ['ssh', 'python', 'paramiko', 'script']
---

Es muy útil lanzar comandos **SSH** desde un *script* de **bash**. Sin embargo, los *scripts* en **bash** se vuelve ilegibles rápidamente, y no nos ofrece el poderío de la librería **python**. No es de extrañar que herramientas como **ansible** o **fabric** estén escritas en **python**, usando una librería llamada **paramiko**.<!--more-->

Una vez en el terreno de **python**, disponemos de todas las opciones que tenemos habitualmente en el lenguaje, como por ejemplo, el módulo de expresiones regulares para *parsear* la salida. Estos *scripts* quedan muy pequeños, legibles y limpios.

En este artículo vamos a explicar como instalar y usar **paramiko**, con un ejemplo simple. El resto quedará a la imaginación de los lectores.

## Instalando la librería en un virtualenv

Vamos a hacernos con el control de *root*, de forma interactiva o mediante **sudo** para instalar las herramientas básicas para utilizar *virtualenvs*.

```bash
root@desktop:~# apt-get install python-virtualenv  
...
root@desktop:~# 
```

Como adelanto, el comando **pip** se va a ir quejando porque no dispone de un compilador y de ciertas librerías para construir las librerías de las que **paramiko** depende. Podéis ir instalando estas librerías a medida que las vaya pidiendo, o por comodidad, las instalamos ahora de golpe.

```bash
root@desktop:~# apt-get install gcc python-dev libssl-dev libffi-dev
...  
root@desktop:~# 
```

Y ya con las dependencias cumplidas, volvemos a utilizar un usuario sin privilegios, por seguridad. Vamos a crear un *virtualenv* en una localización arbitraria.

```bash
gerard@desktop:~/ssl$ virtualenv env
Running virtualenv with interpreter /usr/bin/python2
New python executable in env/bin/python2
Also creating executable in env/bin/python
Installing setuptools, pip...done.
gerard@desktop:~/ssl$ 
```

Activamos el *virtualenv*, para asegurar que la instalación de **paramiko** se hace en el mismo, y así no ensuciamos el sistema con nuestras librerías propias.

```bash
gerard@desktop:~/ssl$ . env/bin/activate
(env)gerard@desktop:~/ssl$ 
```

Instalar la librería es tan fácil como utilizar **pip** o **easy_install** para instalarla. Como **pip** es el futuro de las herramientas **python**, vamos con este comando. Este se va a bajar todos los paquetes y va a construir las librerías auxiliares; es un proceso con mucha salida, pero tarda poco.

```bash
(env)gerard@desktop:~/ssl$ pip install paramiko
...  
Successfully installed paramiko pyasn1 cryptography idna six setuptools enum34 ipaddress cffi pycparser
Cleaning up...
(env)gerard@desktop:~/ssl$ 
```

A partir de aquí, solo queda hacer un script que satisfaga nuestras necesidades.

## Un script de ejemplo

Vamos a suponer que tenemos un servidor llamado *server*, con un usuario *gerard* con permiso para hacer **sudo**. Vamos a lanzar tres comandos por **SSH**, que nos van a indicar su *hostname* y el usuario con el que ejecutamos los comandos, con y sin **sudo**.

Siguiendo [la documentación](http://docs.paramiko.org/en/2.1/), rápidamente sacamos un *script* mínimo. Para poder reutilizarlo en futuras aventuras, vamos a separar la lógica de ejecutar un comando del resto, mediante una función.

```bash
(env)gerard@desktop:~/ssl$ cat test.py 
#!/usr/bin/env python

import paramiko

def execute_command(command, host, user, password, sudo=False):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, username=user, password=password, timeout=2)
    if sudo:
        stdin, stdout, stderr = client.exec_command('sudo -S ' + command)
        stdin.write(password + '\n')
    else:
        stdin, stdout, stderr = client.exec_command(command)
    output = stdout.read()
    client.close()
    return output

HOST = '172.17.0.2'
USER = 'gerard'
PASSWORD = 's3cr3t'

print 'Remote hostname:', execute_command('hostname', HOST, USER, PASSWORD),
print 'Remote user:', execute_command('whoami', HOST, USER, PASSWORD),
print 'Remote user after sudo:', execute_command('whoami', HOST, USER, PASSWORD, sudo=True),
(env)gerard@desktop:~/ssl$ 
```

Solo nos queda ejecutar para comprobar que funciona como debe:

```bash
(env)gerard@desktop:~/ssl$ ./test.py 
Remote hostname: server
Remote user: gerard
Remote user after sudo: root
(env)gerard@desktop:~/ssl$ 
```

En un *script* real, posiblemente habríamos sacado información mas útil, y habríamos *parseado* la salida para no mostrar nada que no nos aporte valor. De momento, nos basta con obtener la salida y mostrarla.
