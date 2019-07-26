---
title: "Testear dominios sin tener el DNS con curl"
slug: "testear-dominios-sin-tener-el-dns-con-curl"
date: 2017-04-17
categories: ['Operaciones']
tags: ['curl', 'dns']
---

En mi trabajo, los problemas llegan sin previo aviso. De repente, alguien te pone en aviso que su aplicación web está caída y es inaccesible. Se trata de un problema de resolución DNS, pero queremos probarlo para estar seguros de que solo es ese el problema y no es general.<!--more-->

Lo primero que nos viene a la cabeza es montar un servidor DNS local e intentar acceder de nuevo, pero es mucho trabajo. Luego nos acordamos del fichero */etc/hosts*, pero no siempre es posible editarlo. Sin embargo, el comando **curl** nos ofrece una opción para suplantar un dominio con la dirección IP que queramos.

## Preparación

Vamos a crear un servidor web con contenido irrelevante solo para ver una demostración de como funciona esta opción. Para ello empezaremos instalando un servidor web cualquiera. Ya sabéis que me gusta mucho el **nginx**...

```bash
root@helium:~# apt-get install -y nginx-light
Reading package lists... Done
Building dependency tree       
Reading state information... Done
The following extra packages will be installed:
  nginx-common
Suggested packages:
  fcgiwrap nginx-doc ssl-cert
The following NEW packages will be installed:
  nginx-common nginx-light
0 upgraded, 2 newly installed, 0 to remove and 2 not upgraded.
Need to get 421 kB of archives.
After this operation, 1020 kB of additional disk space will be used.
...
root@helium:~# 
```

Vamos a eliminar el *site* que viene por defecto porque es un ejemplo y no es relevante.

```bash
root@helium:~# unlink /etc/nginx/sites-enabled/default 
root@helium:~# 
```

Crearemos una carpeta para alojar el contenido web. Según la [FHS](https://es.wikipedia.org/wiki/Filesystem_Hierarchy_Standard), lo correcto es usar */srv/www*, que no viene en una distribución **Debian** por defecto.

```bash
root@helium:~# mkdir /srv/www
root@helium:~# 
```

Ponemos una página web cualquiera, solo para ver si llegamos o no a nuestro servidor.

```bash
root@helium:~# echo "Hello World" > /srv/www/index.html
root@helium:~# 
```

Y vamos a crear un *site* para que nuestro **nginx** sepa lo que tiene que servir:

```bash
root@helium:~# cat /etc/nginx/sites-enabled/example 
server {
	listen 80;
	server_name _;
	root /srv/www;
	index index.html;
}
root@helium:~# 
```

Recargamos o reiniciamos el servidor web para que use la nueva configuración y listo.

```bash
root@helium:~# service nginx reload
[ ok ] Reloading nginx configuration: nginx.
root@helium:~# 
```

Ahora tenemos un servidor web normal y corriente en nuestro entorno.

## Funcionamiento

Vamos ha hacer una petición a nuestro dominio. Voy a usar esta misma web por comodidad, pero si tenéis un dominio que no funciona por culpa del DNS, también lo podéis comprobar ahí.

```bash
gerard@aldebaran:~$ curl -s http://www.linuxsysadmin.tk/ | grep '<title>'
    <title>Linux Sysadmin</title>
gerard@aldebaran:~$ 
```

Magnífico; esta es la web. Vamos ahora a pedirle a **curl** que resuelva las peticiones a este mismo dominio y puerto 80 usando la dirección de nuestro servidor, con la opción *--resolve*. Más información en las páginas **man**.

```bash
gerard@aldebaran:~$ curl -s --resolve www.linuxsysadmin.tk:80:172.18.0.2 http://www.linuxsysadmin.tk/
Hello World
gerard@aldebaran:~$ 
```

Y con esto vemos que este comando ha pasado olímpicamente de lo que le decía el DNS y ha lanzado la petición a nuestro servidor, cuya dirección IP es 172.18.0.2, que es el que hemos preparado más arriba.

Y con este truco tan simple pudimos comprobar que el problema era solo de DNS, ya que si lo evitamos con **curl**, el resto funcionaba a la perfección.
