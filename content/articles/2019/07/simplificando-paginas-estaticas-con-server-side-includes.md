---
title: "Simplificando páginas estáticas con Server Side Includes"
slug: "simplificando-paginas-estaticas-con-server-side-includes"
date: 2019-07-01
categories: ['Miscelánea']
tags: ['server side includes', 'SSI', 'nginx']
---

Los *Server Side Includes* (SSI) son una extensión de algunos servidores web que nos permiten hacer manipulaciones en el fichero HTML servido de forma fácil. Esto nos permite, por ejemplo, incluir *snippets* de código en nuestras páginas estáticas, lo que contribuye en el principio **Dont Repeat Yourself**, sin contenido duplicado.<!--more-->

Los SSI funcionan incrustando directivas en nuestras páginas web, en forma de comentarios con una sintaxis específica. El servidor web "interpreta" esas directivas antes de enviarle la respuesta al usuario, dándonos una especie de contenido dinámico sin repercutir en el rendimiento de servicio.

Aunque es una tecnología de los años 90 y va camino a caer en desuso, creo que tiene todavía uso con el auge de las páginas estáticas, probablemente autogeneradas. Algunos servidores web todavía conservan esta extensión:

* Apache
* IIS
* Lighttpd
* Nginx

Desde mi punto de vista personal, su *killer feature* es la incorporación de *snippets*, de forma que no nos repitamos y podamos cambiar todas las páginas editando solo un fichero.

## Un escenario problemático

Hace tiempo que descubrí [una librería magnífica para hacer documentación]({{< relref "/articles/2016/12/documentacion-facil-con-markdown-y-strapdownjs.md" >}}). De hecho, sirve también para hacer sitios web simples; solo hace falta rodear nuestro contenido **markdown** con algunos *tags* HTML:

```html
<!DOCTYPE html>
<html>
<title>Lorem Ipsum</title>
<xmp theme="spacelab" style="display:none;">

# Esto es markdown

</xmp>
<script src="http://strapdownjs.com/v/0.2/strapdown.js"></script>
</html>
```

Como la prueba de concepto nos gusta, nos la quedamos; pasan los meses y vamos añadiendo páginas nuevas a nuestro sitio simple, llegando al centenar de páginas. Con el paso del tiempo se nos puede ocurrir hacer algunos cambios:

* Cambiar el título del sitio
* Cambiar el tema base del sitio
* Reestructurar los elementos HTML de forma radical
* Hospedar una copia local de **strapdown**

Esto supone cambiar todas las páginas, y son muchas a estas alturas. Incluso si lo automatizamos es una tarea bastante poco deseable.

## Server Side Includes al rescate

Imaginemos que los *tags* necesarios se externalizan en *snippets* de código en fichero distintos:

* Tags anteriores al contenido &rarr; Los metemos en `header.shtml`
* Tags posteriores al contenido &rarr; Los metemos en `footer.shtml`

**TRUCO**: La extensión `.shtml` no es necesaria, pero es la tradición. Podéis cambiarla por la que os convenga (`.html`, `.inc`, `.snippet`, ...)

Ahora nuestro *document root* tiene dos ficheros más, que agruparé en una carpeta propia para poder poner reglas extras de **nginx** sobre ella.

```bash
gerard@atlantis:~/workspace/ssi$ tree www/
www/
├── include
│   ├── footer.shtml
│   └── header.shtml
└── index.html

1 directory, 3 files
gerard@atlantis:~/workspace/ssi$ 
```

```bash
gerard@atlantis:~/workspace/ssi$ cat www/include/header.shtml 
<!DOCTYPE html>
<html>
<title>Lorem Ipsum</title>
<xmp theme="spacelab" style="display:none;">
gerard@atlantis:~/workspace/ssi$ 
```

```bash
gerard@atlantis:~/workspace/ssi$ cat www/include/footer.shtml 
</xmp>
<script src="http://strapdownjs.com/v/0.2/strapdown.js"></script>
</html>
gerard@atlantis:~/workspace/ssi$ 
```

Los ficheros HTML no se libran de modificaciones, pero esto se debería hacer con antelación a la crecida de contenido...

```bash
gerard@atlantis:~/workspace/ssi$ cat www/index.html 
<!--#include file="/include/header.shtml" -->

# Esto es markdown

<!--#include file="/include/footer.shtml" -->
gerard@atlantis:~/workspace/ssi$ 
```

Esto causará que el comentario se sustituya por el contenido de los ficheros indicados.

## Activando SSI en Nginx

Para que el servidor web **nginx** pueda interpretar estos comentarios solo se necesita activar el módulo SSI. Esto se hace con la directiva `ssi on`, a nivel de servidor o a nivel de *virtualhost*.

```bash
gerard@atlantis:~/workspace/ssi$ cat web.conf 
server {
    listen 80;
    server_name _;
    root /srv/www;
    index index.html;
    ssi on;
    error_page 404 /404.html;

    location /404.html {
        internal;
    }

    location /include/ {
        internal;
    }
}
gerard@atlantis:~/workspace/ssi$ 
```

**TRUCO**: La última `location` sirve para "marginar" la carpeta `include`. Cualquier intento de solicitar una URL que empiece por `/include/` va a devolver directamente un error 404, como si no exisitiera la carpeta ni su contenido. Ese es el motivo real para mover los *snippets* a su propia carpeta.

Ahora ya no necesitamos temer los cambios en los *tags* HTML, ya que solo habría que modificar dos *snippets*. La inclusión de los mismos la hace **nginx** en cada petición que se le haga, y lo conseguimos sin utilizar ningún lenguaje de programación.
