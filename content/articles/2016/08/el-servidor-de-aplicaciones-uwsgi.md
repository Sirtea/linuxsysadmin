---
title: "El servidor de aplicaciones uWSGI"
slug: "el-servidor-de-aplicaciones-uwsgi"
date: 2016-08-01
categories: ['Sistemas']
tags: ['uWSGI', 'plugins', 'PHP', 'ruby', 'python']
---

Estaba yo el otro día buscando un servidor de aplicaciones para aplicaciones *python*, y entre todas las opciones encontré uno que es una auténtica joya: **uWSGI**. Se trata de un servidor modular, que permite servir un amplio abanico de posibilidades en cuanto a lenguajes se refiere, usando un *plugin* adecuado.<!--more-->

Concretamente me llamó la atención el modo de funcionamiento llamado *emperor*, que es un proceso que se dedica a monitorizar una carpeta concreta, de forma que se asegura de que cada fichero de configuración mantiene levantada una instancia que la sirva.

Si levantamos el *emperor*, leerá la carpeta de *vassals*, levantando todos los que entienda. Si añadimos un fichero de configuración nuevo en caliente, levantará una instancia nueva. Si eliminamos un fichero de configuración, matará la instancia referida. Finalmente, si ese mismo fichero de configuración se modifica (un *touch* vale), se adaptará a las nuevas directrices, recargando el código de nuestra aplicación.

Vamos a empezar instalando la variante *emperor*, que no es mas que el **uwsgi** básico, con una configuración de *emperor* y un *init script* adecuado.

```bash
root@server:~# apt-get install -y uwsgi-emperor
Leyendo lista de paquetes... Hecho
Creando árbol de dependencias
Leyendo la información de estado... Hecho
...  
0 actualizados, 11 nuevos se instalarán, 0 para eliminar y 0 no actualizados.
Se necesita descargar 2.258 kB de archivos.
Se utilizarán 5.724 kB de espacio de disco adicional después de esta operación.
..  
root@server:~#
```

Para entender un lenguaje cualquiera, hay que declarar el uso de un *plugin* para ese lenguaje. Vamos a poner los *plugins* para tres de los lenguajes mas utilizados, que nos van a servir como demostración para este artículo: **python**, **PHP** y **ruby**.

```bash
root@server:~# apt-get install -y uwsgi-plugin-python uwsgi-plugin-php uwsgi-plugin-rack-ruby2.1
Leyendo lista de paquetes... Hecho
Creando árbol de dependencias
Leyendo la información de estado... Hecho
...  
0 actualizados, 22 nuevos se instalarán, 0 para eliminar y 0 no actualizados.
Se necesita descargar 12,0 MB de archivos.
Se utilizarán 49,9 MB de espacio de disco adicional después de esta operación.
...  
root@server:~#
```

Adicionalmente, el *plugin* de **ruby** necesita tener el paquete *rack* instalado, así que lo ponemos también.

```bash
root@server:~# apt-get install -y ruby-rack
Leyendo lista de paquetes... Hecho
Creando árbol de dependencias
Leyendo la información de estado... Hecho
...  
0 actualizados, 8 nuevos se instalarán, 0 para eliminar y 0 no actualizados.
Se necesita descargar 1.354 kB de archivos.
Se utilizarán 2.687 kB de espacio de disco adicional después de esta operación.
...  
root@server:~#
```

En todos los casos, bastará con poner un fichero de configuración en */etc/uwsgi-emperor/vassals/* para activar cada una de las aplicaciones.

## Sirviendo ficheros PHP

Crearemos una carpeta contenedora para nuestros ficheros **PHP**:

```bash
root@server:~# mkdir /opt/php/
root@server:~#
```

En esa carpeta vamos a poner algún fichero *.php* para tener algo que servir y demostrar que funciona. Con algo simple nos vale.

```bash
root@server:~# cat /opt/php/index.php
Hello from PHP, version <?php echo phpversion(); ?>
root@server:~#
```

Vamos a poner un fichero de configuración que sirva **PHP**, prácticamente copiado de la documentación.

```bash
root@server:~# cat /etc/uwsgi-emperor/vassals/php.ini
[uwsgi]
plugins = 0:php
http-socket = :8080
master = true
workers = 2
project_dir = /opt/php/
check-static = %(project_dir)
static-skip-ext = .php
static-skip-ext = .inc
php-docroot = %(project_dir)
php-allowed-ext = .php
php-index = index.php
root@server:~#
```

Y el *emperor* se dedicará a levantar un proceso para servir esta aplicación. No hay que reiniciar nada. Lo comprobamos con una petición desde una máquina que vea a nuestro servidor:

```bash
root@lxc:~# wget -qO- http://10.0.0.2:8080/; echo ''
Hello from PHP, version 5.6.20-0+deb8u1
root@lxc:~#
```

## Sirviendo una aplicación ruby mediante el protocolo rack

Siguiendo los mismos pasos que en el paso anterior, creamos la carpeta contenedora.

```bash
root@server:~# mkdir /opt/ruby/
root@server:~#
```

En esta carpeta ponemos una aplicación *rack* mínima, que he copiado de internet. Normalmente, la gente suele usar *frameworks*, pero el resultado es el mismo.

```bash
root@server:~# cat /opt/ruby/ruby.ru
app = lambda do |env|
  body = "Hello, World!"
  [200, {"Content-Type" => "text/plain", "Content-Length" => body.length.to_s}, [body]] end
run app
root@server:~#
```

Y basta con declarar un fichero de configuración para que se active la nueva aplicación.

```bash
root@server:~# cat /etc/uwsgi-emperor/vassals/ruby.ini
[uwsgi]
plugins = rack_ruby21
http-socket = :3031
master = true
workers = 2
rack = /opt/ruby/ruby.ru
root@server:~#
```

Nuevamente podemos comprobar que el resultado es el esperado:

```bash
root@lxc:~# wget -qO- http://10.0.0.2:3031/; echo ''
Hello, World!
root@lxc:~#
```

## Sirviendo una aplicación python mediante el protocolo WSGI

Supongamos que tenemos una carpeta contenedora para nuestra aplicación, como en los casos anteriores:

```bash
root@server:~# mkdir /opt/py/
root@server:~#
```

En ella tenemos una aplicación que cumple con el protocolo **WSGI**. Nuevamente vamos a simplificar el ejemplo a base de no utilizar ningún *framework*.

```bash
root@server:~# cat /opt/py/app.py
def application(environ, start_response):
    start_response('200 OK', [('Content-Type', 'text/plain')])
    yield 'Hello World from python'
root@server:~#
```

Configuramos el *vassal* que va a dar a conocer la aplicación al *emperor*, de forma que este la pueda levantar automáticamente.

```bash
root@server:~# cat /etc/uwsgi-emperor/vassals/py.ini
[uwsgi]
plugins = python
http-socket = :5000
master = true
workers = 2
chdir = /opt/py/
module = app:application
root@server:~#
```

Y vemos como todo funciona como debe:

```bash
root@lxc:~# wget -qO- http://10.0.0.2:5000/; echo ''
Hello World from python
root@lxc:~#
```

Es importante indicar que el *plugin* de **python** soporta muchas mas directivas, entre ellas, la posibilidad de añadir variables de sistema como el *PYTHONPATH*, o la de usar un *virtualenv* propio para nuestra aplicación. Es por este motivo que me enamoré de este servidor de aplicaciones.
