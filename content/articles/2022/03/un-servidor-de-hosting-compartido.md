---
title: "Un servidor de hosting compartido"
slug: "un-servidor-de-hosting-compartido"
date: "2022-03-22"
categories: ['Sistemas']
tags: ['hosting', 'linux', 'debian', 'ssh', 'sftp', 'nginx', 'php-fpm', 'openssl']
---

Ya hace tiempo que trabajo a nivel personal con varios *blogs* hechos con generadores estáticos
y algunas aplicaciones simples PHP. Como ninguno tiene una carga demasiado alta, decidí unificarlos
en pocos servidores pequeños para economizar. En algún momento se me ocurrió que podía hacerlo
de forma estándar.<!--more-->

La idea es simple: un servidor pequeño basta para alojar estas pequeñas webs de forma fácil
y autónoma, con el entendido de que:

* El código se sube por SFTP, con usuarios y carpetas *root* enjauladas
* El servidor web tiene los *virtualhosts* automatizados de alguna manera
	* Hay la posibilidad de poner algo de PHP
	* Hay la posibilidad de tener HTTPS

La elección de servidor web se debió a una funcionalidad ganadora: la directiva `server_name` de
**nginx** permite poner comodines y expresiones regulares. Para el PHP y el SFTP se utilizarán
**php-fpm** y **openssh** respectivamente por decisión personal.

**NOTA**: Los comandos proporcionados asumen una distribución **Debian**, aunque deberían
funcionar en distribuciones derivadas sin cambios, e incluso con otras distribuciones no
relacionadas con algún cambio simple.

## El enjaulado SFTP

Haremos un enjaulado estándar basado en **openssh**, que es lo que tenemos instalado en casi todo
servidor. Se asume que ya está instalado, hacedlo si procede.

La estrategia es la de enjaular cada usuario del grupo **sftponly** en una carpeta `/srv/jails/<usuario>`.
Por requisitos de SSH, esta carpeta debe pertenecer al usuario **root** del sistema y ser este el único
que puede escribir en ella; entonces vamos a crearle al usuario una subcarpeta `www` que será en donde
deba dejar el código y que será la que se sirva desde el navegador.

Empezamos creando el grupo, que haremos "de sistema":

```bash
gerard@hosting:~$ sudo groupadd --system sftponly
gerard@hosting:~$
```

Añadiremos en `/etc/ssh/sshd_config` un bloque que se encargue del enjaulado de los usuarios de este grupo:

```bash
gerard@hosting:~$ cat /etc/ssh/sshd_config
...
Match Group sftponly
  ChrootDirectory /srv/jails/%u
  ForceCommand internal-sftp
gerard@hosting:~$
```

Finalmente, reiniciaremos el servicio SSH para que aplique los cambios.

```bash
gerard@hosting:~$ sudo systemctl restart ssh
gerard@hosting:~$
```

## El servidor web

Como ya dijimos, vamos a utilizar un combo de **nginx** + **php-fpm**. Vamos a instalarlos, usando el
paquete `nginx-light`, que es el que viene con los módulos necesarios y justos para lo que necesitamos;
habrá que instalar también cualquier módulo PHP que se vaya a necesitar *a posteriori* (por ejemplo,
`php-mysql` o `php-intl`).

```bash
gerard@hosting:~$ sudo apt install nginx-light php-fpm
...
gerard@hosting:~$
```

Ahora viene el truco de todo esto: un `server_name` que incluya el nombre del usuario, que gracias a
las expresiones regulares, podemos obtener en una variable, que luego pondremos en la directiva `root`.
Esta variable **no puede ir** en las directivas `ssl_certificate` y `ssl_certificate_key`, hay que
emplear la variable `ssl_server_name`.

```bash
gerard@hosting:~$ ls /etc/nginx/sites-enabled/
sites
gerard@hosting:~$
```

```bash
gerard@hosting:~$ cat /etc/nginx/sites-enabled/sites
server {
        server_name ~^(?<user>.+)\.myhosting\.local$;
        listen 80;
        listen 443 ssl;
        ssl_certificate /srv/certs/$ssl_server_name.pem;
        ssl_certificate_key /srv/certs/$ssl_server_name.pem;
        index index.php index.html;
        root /srv/jails/$user/www;

        location ~ \.php$ {
                include snippets/fastcgi-php.conf;
                fastcgi_pass unix:/run/php/php7.4-fpm.sock;
        }

        location / { try_files $uri $uri/ =404; }
}
gerard@hosting:~$
```

Y como viene siendo costumbre, recargamos el servicio para que aplique el cambio en la configuración:

```bash
gerard@hosting:~$ sudo systemctl reload nginx
gerard@hosting:~$
```

## Creando usuarios

En este momento necesitamos crear un usuario, con todo lo que implica:

* Crear el usuario, asignarle un *password* y añadirlo al grupo *sftponly*
* Crear su carpeta `www` dentro de la jaula, con los permisos para que pueda escribir en ella
* Crear una carpeta `/srv/certs` con un certificado autofirmado y con permisos para que los *workers* de nginx lo puedan leer

**TRUCO**: En circunstancias normales, el proceso que lee los certificados es el nginx inicial,
que funciona con el usuario **root**. Al poner una variable en el `ssl_certificate` y en el
`ssl_certificate_key` se va a leer el fichero del certificado **en cada petición**. Rendimiento
aparte, eso significa que los procesos que lo lean son los *workers* del **nginx**, que ejecutan
con otro usuario (**www-data** en caso de **Debian**).

Para facilitar las cosas, crearemos todos estos pasos en un *script*, que tomará el nombre
del usuario de su primer parámetro, y generará todo el resto.

```bash
gerard@hosting:~$ cat create_user.sh
#!/bin/bash

useradd -m -G sftponly ${1}
echo ${1}:changeme | chpasswd

mkdir -p /srv/jails/${1}/www
chown ${1}:${1} /srv/jails/${1}/www

mkdir -p /srv/certs
openssl req -newkey rsa:2048 -days 365 -nodes -x509 -keyout /srv/certs/${1}.myhosting.local.pem -out /srv/certs/${1}.myhosting.local.pem -subj "/CN=${1}.myhosting.local"
chown www-data:www-data /srv/certs/${1}.myhosting.local.pem
gerard@hosting:~$
```

Este *script* requiere de **openssl** para funcionar, así que también lo instalamos:

```bash
gerard@hosting:~$ sudo apt install openssl
...
gerard@hosting:~$
```

## Testeando el montaje

Para hacer las pruebas, solo necesitamos crear algunos usuarios, y ver que pueden acceder por SFTP a
su jaula, y ver que lo que hacen se refleja en su web. Vamos a crear dos usuarios: **user1** y **user2**:

```bash
gerard@hosting:~$ sudo ./create_user.sh user1
Generating a RSA private key
..........................+++++
................................................+++++
writing new private key to '/srv/certs/user1.myhosting.local.pem'
-----
gerard@hosting:~$
```

```bash
gerard@hosting:~$ sudo ./create_user.sh user2
Generating a RSA private key
...........................................+++++
..............................................................................................................................................+++++
writing new private key to '/srv/certs/user2.myhosting.local.pem'
-----
gerard@hosting:~$
```

Ahora entramos por SFTP con cada usuario; basta con ver que solo tenemos la carpeta `www`, por
supuesto con contenido diferente para cada usuario. Digamos que **user1** deja un fichero
`index.html` básico, y que el **user2** deja un `index.php` con un `phpinfo()`.

```bash
gerard@hosting:~$ tree /srv/
/srv/
├── certs
│   ├── user1.myhosting.local.pem
│   └── user2.myhosting.local.pem
└── jails
    ├── user1
    │   └── www
    │       └── index.html
    └── user2
        └── www
            └── index.php

6 directories, 4 files
gerard@hosting:~$
```

Ahora vamos a hacer algunas peticiones, tanto por HTTP como por HTTPS en cada uno de los dominios,
solo para ver que se devuelve lo que toca, que es el `index.html` en el caso de **user1**, y el
`index.php` en el caso de **user2**. Se van a utilizar los *flags* `-s` (no mostrar nada más que
la respuesta) y `-k` (confiar en el certificado autofirmado) según se necesiten.

```bash
gerard@hosting:~$ curl --resolve user1.myhosting.local:80:127.0.0.1 http://user1.myhosting.local/
<h1>Hello from user1!</h1>
gerard@hosting:~$
```

```bash
gerard@hosting:~$ curl -s --resolve user2.myhosting.local:80:127.0.0.1 http://user2.myhosting.local/ | grep title
<title>PHP 7.4.28 - phpinfo()</title><meta name="ROBOTS" content="NOINDEX,NOFOLLOW,NOARCHIVE" /></head>
gerard@hosting:~$
```

```bash
gerard@hosting:~$ curl -k --resolve user1.myhosting.local:443:127.0.0.1 https://user1.myhosting.local/
<h1>Hello from user1!</h1>
gerard@hosting:~$
```

```bash
gerard@hosting:~$ curl -sk --resolve user2.myhosting.local:443:127.0.0.1 https://user2.myhosting.local/ | grep title
<title>PHP 7.4.28 - phpinfo()</title><meta name="ROBOTS" content="NOINDEX,NOFOLLOW,NOARCHIVE" /></head>
gerard@hosting:~$
```

Con esto solo faltaría modificar los registros DNS y poner certificados confiables,
antes de exponer el servidor a internet.
