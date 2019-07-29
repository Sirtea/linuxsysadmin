---
title: "Documentación fácil con markdown y strapdown.js"
slug: "documentacion-facil-con-markdown-y-strapdownjs"
date: 2016-12-12
categories: ['Miscelánea']
tags: ['html', 'markdown', 'strapdownjs']
---

Últimamente estoy harto de realizar documentación en formato *word*; pierdo la mayoría de mi tiempo dando formato, colores y maquetando el poco contenido que alcanzo a poner. Tras mucho meditar y, a partir de ahora, la voy a escribir en **markdown**, y se lea en **HTML**, como lenguaje mas usado.<!--more-->

Revisando por la web, he encontrado una librería magnífica que se llama [strapdown.js](http://strapdownjs.com/), que combina la elegancia de **bootstrap** con un compilador **markdown** de lado cliente. De esta forma, ni siquiera necesito hacer el paso previo de convertir mis ficheros **markdown** a **HTML**.

Como plus extra, como el fichero se interpreta en el navegador, no necesito nada muy caprichoso en el servidor para servir las páginas; con un **nginx** nos basta. Incluso podemos sacar partido de las [GitHub Pages](https://pages.github.com/), para tener *hosting* gratuito.

Las páginas son ficheros *.html* estándares, con la única diferencia de que todo lo que vaya en el *tag xmp* será interpretado como **markdown**. Ahí pongo el esqueleto básico de una página.

```html
<!DOCTYPE html>
<html>
<title>Sin título</title>

<xmp theme="spacelab" style="display:none;">
...
</xmp>

<script src="http://strapdownjs.com/v/0.2/strapdown.js"></script>
</html>
```

De hecho, el fichero incluido *strapdown.js*, y el resto de ficheros necesarios se pueden alojar en nuestro mismo servidor, para una velocidad de acceso óptima.

## Un ejemplo

Supongamos que queremos hacer una web de dos páginas: el índice y otra de ejemplo. Para ello vamos a poner dos ficheros **HTML**, de la misma manera que lo haríamos para una página web normal.

```bash
gerard@aldebaran:~/www$ ls -1
example.html
index.html
gerard@aldebaran:~/www$ 
```

Empezaremos creando un *index.html* con el siguiente contenido:

```html
<!DOCTYPE html>
<html>
<title>Home page</title>

<xmp theme="spacelab" style="display:none;">
# Hello world!

You are in the Home page.

Navigation:

* [Home page](/)
* [Example page](/example.html)
</xmp>

<script src="http://strapdownjs.com/v/0.2/strapdown.js"></script>
</html>
```

Hemos puesto un enlace a la página de ejemplo, así que la vamos a crear también, para no tener enlaces rotos. Pongamos algo similar:

```html
<!DOCTYPE html>
<html>
<title>Example page</title>

<xmp theme="spacelab" style="display:none;">
# This is an example

You are in the example page.

Navigation:

* [Home page](/)
* [Example page](/example.html)
</xmp>

<script src="http://strapdownjs.com/v/0.2/strapdown.js"></script>
</html>
```

Y no hay que hacer nada más. Solo hay que servir el contenido de esta carpeta. Podemos montar un servidor web o podemos sincronizarla a otro servidor que tengamos. Como no me quiero entretener con esto, y dado que no tiene nada que ver, me voy a limitar a levantar el servidor estándar que viene con **python**.

```bash
gerard@aldebaran:~/www$ python -m SimpleHTTPServer
Serving HTTP on 0.0.0.0 port 8000 ...
```

Y con esto solo nos queda verificar el resultado en `http://localhost:8000/`. Si miráis el código fuente de la página, veréis que se ve el lenguaje de marcado tal cual; incluso puede que veáis la página antes de su *renderizado*, mientras se carga la librería **javascript**. Al menos, habré cumplido con mi objetivo, que era el de escribir contenido sin perder tiempo en la maquetación.
