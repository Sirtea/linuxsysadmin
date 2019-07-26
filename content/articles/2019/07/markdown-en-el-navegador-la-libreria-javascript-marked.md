---
title: "Markdown en el navegador: la librería javascript Marked"
slug: "markdown-en-el-navegador-la-libreria-javascript-marked"
date: 2019-07-15
categories: ['Miscelánea']
tags: ['html', 'markdown', 'marked']
---

En otros artículos hablé de una librería *javascript* que nos permitía escribir documentación de forma fácil, escribiendo en el fichero `.html` el contenido en lenguaje de marcado **markdown**. Se trataba de [Strapdown]({{< relref "/articles/2016/12/documentacion-facil-con-markdown-y-strapdownjs.md" >}}) y le he dado mucho uso desde entonces; aunque soy minimalista y me gusta ir a lo básico.<!--more-->

Y es que este proyecto es muy claro en los créditos de [su página web](https://strapdownjs.com/); basan su trabajo en:

> Marked - Fast Markdown parser in JavaScript  
> Google Code Prettify - Syntax highlighting in JavaScript  
> Twitter Bootstrap - Beautiful, responsive CSS framework  
> Bootswatch - Additional Bootstrap themes

Si asumimos que no necesitamos iluminación de sintaxis, y queremos evitar el *framework bootstrap* por su pesadez, lo lógico es usar directamente la librería de **markdown**; esto también nos da más control sobre los *tags* que deben interpretarse como **markdown** y reemplazarse por el HTML generado.

Lo primero para entender como funciona es ir a [su documentación](https://marked.js.org/#/README.md). El primer ejemplo es de lo más simple y no entraña ninguna complicación:

```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8"/>
  <title>Marked in the browser</title>
</head>
<body>
  <div id="content"></div>
  <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
  <script>
    document.getElementById('content').innerHTML =
      marked('# Marked in browser\n\nRendered by **marked**.');
  </script>
</body>
</html>
```

Lo que debemos entender es que el contenido **markdown** se entrega a una función llamada `marked` que devuelve el contenido HTML. Este contenido es utilizado para llenar el *innerHTML* del elemento que queramos utilizar para pintarlo.

Este ejemplo ha decidido no utilizar complicaciones; uso un contenido básico, lo paso a la función y lo pongo en el elemento con `id=content`. Esto se hace inmediatamente y no hay ni editores, ni repintado mientras escribimos ni nada. Si os interesa, esto lo tenéis que implementar vosotros.

Para intentar emular el funcionamiento de **Strapdown** necesitamos tomar algunas decisiones de diseño:

* El contenido no cambia, así que ya nos viene bien que se pinte al principio.
* El contenido está escrito en un elemento HTML y se va a reemplazar por el equivalente en HTML.
* Ya puestos a pedir, podemos querer poner varias zonas de contenido **markdown**, por ejemplo, los que tengan `class=markdown`.

Con estas premisas, no es difícil modificar el ejemplo para que haga lo que nos interesa. Solo habrían dos grandes cambios que hacer:

* Iterar todos los posibles elementos con `class=markdown`, que pueden ser varios.
* Reemplazar los `innerHTML` de los elementos **markdown** por el HTML resultante de `marked(innerHTML)`.

De esta manera, quedaría algo como esto:

```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8"/>
  <title>Lorem Ipsum</title>
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <link rel="stylesheet" href="style.css" />
</head>
<body>
  <div class="markdown">

# Tenebor nunc praedictaque

## Constitit forte delubraque gladio soporem dum odium

Lorem markdownum gratare stellamque senis quiescere auxiliaria tuos tetigere
horrenda reposcunt, vulnera aether deus saevior merguntque cortex spatii;
sucoque? Falcato omnes, laborum quem quaeris
[nomen](http://www.praequestus.com/loqui.html) cede dolore, nebulas *Pandione*.

  </div>
  <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
  <script>
    var l = document.getElementsByClassName('markdown');
    var i;
    for (i = 0; i < l.length; i++) {
      l[i].innerHTML = marked(l[i].innerHTML);
    }
  </script>
</body>
</html>
```

De esta forma solo tenemos que implementar un estilo propio y añadir un título más adecuado. Esto se consigue cambiando el HTML base, y posiblemente creando un fichero `style.css` a nuestro gusto. En mi caso seguí los consejos de [otro artículo]({{< relref "/articles/2018/10/trucos-simples-de-css-para-que-tu-pagina-se-vea-aceptable.md" >}}).

**TRUCO**: Para el contenido de ejemplo he utilizado una herramienta web externa, que bien merece una mención: <https://jaspervdj.be/lorem-markdownum/>.
