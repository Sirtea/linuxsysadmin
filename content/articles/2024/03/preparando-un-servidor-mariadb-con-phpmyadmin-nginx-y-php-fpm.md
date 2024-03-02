---
title: "Preparando un servidor MariaDB con phpMyAdmin, Nginx y php-fpm"
slug: "preparando-un-servidor-mariadb-con-phpmyadmin-nginx-y-php-fpm"
date: "2024-03-02"
categories: ['Sistemas']
tags: ['linux', 'debian', 'mysql', 'mariadb', 'phpmyadmin', 'nginx', 'php-fpm']
---

En el mundo de PHP, hemos visto una tendencia de sustitución del venerable **Apache**
por **Nginx** y **php-fpm**. Hay muchas razones para ello, con muchos indicando que el
rendimiento de este último par es claramente superior; a mí me gusta mucho la separación
de responsabilidades entre el servidor web y el intérprete de PHP.<!--more-->

Para servidores de **MariaDB** o **MySQL** de desarrollo es frecuente poner una herramienta
de gestión de la misma, siendo **phpMyAdmin** el estándar *de facto*. Esto introduce un
riesgo de seguridad, pero si tenemos las limitaciones de acceso adecuadas, nos puede
quitar mucho trabajo diario.

En este artículo vamos a montar todo el conjunto en un servidor **Debian 12 (bookworm)**,
que es el actual estable; seguramente, los pasos van a ser los mismos para todas las
distribuciones **Debian**, **Ubuntu** y derivadas.

Primero, antes de empezar, nos vamos a traer la lista actualizada de paquetes disponibles
para nuestra distribución:

```bash
gerard@database:~$ sudo apt update
...
gerard@database:~$
```

La primera parte, y posiblemente la más fácil, es instalar la base de datos, que por ser
**Debian**, es **MariaDB**.

```bash
gerard@database:~$ sudo apt install mariadb-server
...
gerard@database:~$
```

Para poder servir una aplicación PHP, como puede ser **phpMyAdmin**, vamos a necesitar
el combo **nginx** + **php-fpm**. Nuevamente es bastante fácil:

```bash
gerard@database:~$ sudo apt install nginx php-fpm
...
gerard@database:~$
```

En este punto, basta con instalar la aplicación PHP. Hacerlo desde los repositorios de
la distribución nos va a facilitar la instalación de las dependencias PHP necesarias.

```bash
gerard@database:~$ sudo apt install phpmyadmin
...
gerard@database:~$
```

**NOTA**: Este último comando nos va a preguntar dos cosas; podemos decir que no queremos
configurar automáticamente ni **apache2** ni **lighttpd** (no los tenemos), y que **sí**
queremos configurar **phpmyadmin** automáticamente (una contraseña vacía nos lo va a dejar
todo funcional con una contraseña autogenerada).

Para que podamos servir el **phpMyAdmin**, vamos a tener que añadir alguna configuración
en el **nginx** que nos permita servir la carpeta de la aplicación en alguna combinación
de IP, puerto y URL. Dado que no quiero servir nada más en este servidor, desactivo el
servidor que viene por defecto, y pongo uno en el puerto 8080:

```bash
gerard@database:~$ sudo unlink /etc/nginx/sites-enabled/default
gerard@database:~$
```

```bash
gerard@database:~$ cat /etc/nginx/sites-enabled/phpmyadmin
server {
        listen 8080;
        root /usr/share/phpmyadmin;
        index index.php;

        location / {
                try_files $uri $uri/ =404;
        }

        location ~ \.php$ {
                include snippets/fastcgi-php.conf;
                fastcgi_pass unix:/run/php/php8.2-fpm.sock;
        }
}
gerard@database:~$
```

**TRUCO**: Podemos localizar fácilmente la carpeta base de la aplicación buscando ficheros
`index.php` en el paquete **phpmyadmin**:

```bash
gerard@database:~$ dpkg -L phpmyadmin | grep index.php
/usr/share/phpmyadmin/index.php
gerard@database:~$
```

Solo nos queda aplicar la configuración mediante un `systemctl restart nginx` o un `systemctl reload nginx`.

```bash
gerard@database:~$ sudo systemctl restart nginx
gerard@database:~$
```

En este momento, podemos acceder con un navegador al puerto 8080 del servidor y la aplicación
ya funciona. Cabe indicar que no vamos a poder entrar a la aplicación porque no existe ningún
usuario que pueda acceder a **MariaDB** de forma remota.

En este punto, basta con habilitar un usuario para poder  acceder, pudiendo poner un usuario
por base de datos, o pudiendo habilitar al usuario **root** para acceder como administrador.
Me decanto por este último modo de acceso.

```bash
gerard@database:~$ sudo mysql
...
MariaDB [(none)]> ALTER USER 'root'@'localhost' IDENTIFIED BY 's3cr3t';
Query OK, 0 rows affected (0,014 sec)
MariaDB [(none)]> exit
Bye
gerard@database:~$
```

Y ya podríamos acceder a la aplicación con el usuario **root** y la contraseña especificada.
Opcionalmente, podemos configurar la aplicación para que use esas credenciales sin pasar
por un formulario de *login*:

```bash
gerard@database:~$ diff /etc/phpmyadmin/config.inc.php.orig /etc/phpmyadmin/config.inc.php
63c63,65
<     $cfg['Servers'][$i]['auth_type'] = 'cookie';
---
>     $cfg['Servers'][$i]['auth_type'] = 'config';
>     $cfg['Servers'][$i]['user'] = 'root';
>     $cfg['Servers'][$i]['password'] = 's3cr3t';
gerard@database:~$
```
**WARNING**: Aplicad con cautela; esto va a dar permisos de administrador a todo el que
llegue a esa IP y puerto. Revisad vuestra política de accesos al servidor.
