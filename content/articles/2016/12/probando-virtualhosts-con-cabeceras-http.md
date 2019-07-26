---
title: "Probando virtualhosts con cabeceras HTTP"
slug: "probando-virtualhosts-con-cabeceras-http"
date: 2016-12-19
categories: ['Operaciones']
tags: ['curl', 'virtual hosts']
---

Algunas veces tenemos que montar servidores web que responden con distinto contenido dependiendo del dominio. En estas ocasiones, es posible usar un servidor DNS local o incluso resolviendo los dominios mediante el fichero */etc/hosts*. Sin embargo, hay una forma fácil, elegante y que no requiere modificar configuraciones del sistema.<!--more-->

La idea es muy fácil: se trata de suministrar la cabecera *Host* con el dominio que queramos consultar, y el servidor web se va a comportar como si hubiéramos pedido ese *virtualhost*.

## El escenario de ejemplo

Supongamos que tenemos un servidor web **nginx** (por poner algún ejemplo). Este servidor está configurado con dos *server* (lo que en **apache** se llama *virtualhost*).

Ambos se limitan a servir contenido estático, de diferentes carpetas, con la configuración siguiente:

```bash
/etc/nginx/conf.d # cat server1
server {
	listen 80;
	server_name server1;
	root /srv/www/server1;
	index index.html;
}
/etc/nginx/conf.d # 
```

Y una configuración análoga para el otro *virtualhost*:

```bash
/etc/nginx/conf.d # cat server2
server {
	listen 80;
	server_name server2;
	root /srv/www/server2;
	index index.html;
}
/etc/nginx/conf.d # 
```

Por supuesto, vamos a poner contenido en las carpetas raíz de cada *virtualhost*, para que podamos ver fácilmente lo que estamos sirviendo.

```bash
/srv/www # cat server1/index.html 
<h1>Hello from server1</h1>
/srv/www # 
```

Y algo similar para el segundo dominio:

```bash
/srv/www # cat server2/index.html 
<p>This comes from server2</p>
/srv/www # 
```

A partir de aquí, se asume que el servidor está recargado y corriendo.

## Como se hace

Podemos hacer una petición directa con las herramientas que nos parezcan adecuadas, por ejemplo, **wget**, **curl** o un navegador normal; el único requisito es que podamos añadir cabeceras, de forma nativa o mediante un *plugin*.

La dirección IP usada es la que corresponda; incluso se puede usar *localhost* si hacemos las pruebas desde la misma máquina.

```bash
gerard@sirius:~$ curl -s http://192.168.1.48/
<h1>Hello from server1</h1>
gerard@sirius:~$ 
```

Como vemos, obtenemos un resultado... ¿Pero cuál?

No podemos saber *a priori* de que dominio vamos a obtener las páginas. En este caso obtuvimos *server1* porque **nginx** suministra el primero que lee en las configuraciones. Pero eso no nos sirve.

Nosotros queremos probar todos los dominios, uno por uno, y posiblemente de forma automatizada. Así, por ejemplo, si queremos el dominio *server1*, basta con indicarlo en la cabecera *Host* de la petición. Se añade el ejemplo con **curl**, pero debería poder hacerse con cualquier cliente HTTP, de acuerdo a la documentación.

```bash
gerard@sirius:~$ curl -s -H "Host: server1" http://192.168.1.48/
<h1>Hello from server1</h1>
gerard@sirius:~$ 
```

Solo nos queda pedir el otro dominio, y verificar que se nos está sirviendo *server2*, demostrando que este truco funciona:

```bash
gerard@sirius:~$ curl -s -H "Host: server2" http://192.168.1.48/
<p>This comes from server2</p>
gerard@sirius:~$ 
```

Y con esto vemos que nuestros *virtualhosts* funcionan como deben. A partir de aquí, podemos enriquecer las configuraciones de acuerdo a nuestras necesidades.
