---
title: "Migrando este blog de Pelican a Hugo"
slug: "migrando-este-blog-de-pelican-a-hugo"
date: "2019-08-05"
categories: ['Miscelánea']
tags: ['migración', 'blog', 'pelican', 'hugo']
---

Hace tiempo me enamoré de un generador de webs estáticas llamado **pelican**;
puede que fuera por estar escrito en **python**, o por tener una gran colección
de temas y *plugins* disponibles. Con el tiempo, han aparecido [muchas alternativas][1],
y una de ellas me llamó la atención por su sencillez y velocidad: **hugo**.<!--more-->

Ya he utilizado este generador como ejemplo en [otro artículo][2], pero nunca
vi el momento de utilizarlo en algún proyecto serio, hasta ahora. Y es que este
*blog* iba arrastrando una serie de carencias importantes:

* Un tiempo de *build* de unos 45 segundos, cada vez que corregía una falta de ortografía.
* Dependencias con **python**, que me obligaba a montar el entorno en cada ordenador.
* Versiones de **pelican** con cambios incompatibles entre ellas.
* Una sola carpeta con todos los artículos escritos en 4 años de existencia del *blog*.
* Una lista de *plugins* que asustaba de ver.
* Un tema demasiado complejo, escrito por otro.
    * Lo entendía vagamente, y me era difícil de mantener y modificar.
    * Utilizaba librerías *javascript* pesadas e innecesarias.

**RESULTADO**: En algún punto me planteé la gran pregunta: ¿Y si migro a **hugo**?

Por supuesto, cada vez que me hacía esta pregunta me hacía para atrás; se trataba de
adaptar unos 200 artículos, crear un tema adecuado (o volver a pecar con un tema prefabricado),
y probar que todo era satisfactorio sin dejar de servir alguna versión del *blog*.

> Sin embargo, esta vez fue diferente; **simplemente lo empecé a hacer, a ver cuán lejos podía llegar**.

Una migración a **hugo** arreglaba casi todas las carencias: un *build* del orden
de milisegundos, niguna dependencia siendo un solo binario estático, una documentación
fija y estable, y todos los *plugins* integrados en el binario `hugo`. Solo necesitaba
reordenar la carpeta de artículos y conseguir un nuevo tema similar al que tenía.

## Como lo hice

Creé el esqueleto de lo que sería el nuevo tema, minimizando el número de plantillas; al
principio era HTML básico, con el CSS estrictamente necesario, pero con enlaces a todas
las posibles páginas, para poder probar todo el funcionamiento.

Escribí un *script* en **bash** capaz de mover los diferentes artículos a carpetas
del estilo `/201x/xx/` según su *metadata*, poniendo orden a la gran carpeta de
artículos, separándolos según el año y el mes en que los publiqué (esto se saca
de la cabecera `Date`).

El siguiente escollo era adaptar los artículos a **hugo**, lo justo para que se
pudiera construir el sitio; esto limitaba mi trabajo a transformar los *metadatos*
a lo que **hugo** llama el *front matter*, que es lo mismo en esencia. Nuevamente
me ayudé de un *script*, esta vez en **python**, que leía las cabeceras de los
artículos, y las reescribía con el formato YAML que tienen ahora, aprovechando
la rígida forma de los *metadatos* y el abuso de *copy-paste* que venía haciendo.

El resto del contenido se hizo a mano: adaptar las páginas que no son artículos,
adaptar los enlaces locales con los *shortcodes* de **hugo** adecuados, y revisar
que las pocas imágenes que hay en el *blog* se siguieran viendo bien.

Como no me llevó mucho trabajo, seguí con la maquetación; mi idea inicial era la de
crear un tema simple, propio y desde cero. Quería hacer uso simple de CSS, quitar
casi todo el *javascript* y, aún así, repetar ligeramente el *look and feel* del *blog*
inicial; esto me llevó a complicar el tema un poco, pero creo que ha valido la pena.

Ya con algo decente, decidí perder un poco más de tiempo para añadir otras
funcionalidades, como por ejemplo el paginado, el *snippet* de **Google Analytics**,
el *banner* de *cookies* y un pie de página con un enlace a mi **GitHub**.

A nivel de *hosting* también quise simplificar: en vez de publicarlo como
**GitHub Pages** usando una rama nueva, me he limitado a publicar la carpeta `docs`;
esto requiere un pequeño cambio en el `config.toml` pero simplifica muchísimo el
proceso de publicación, bastando con un `git commit` y un `git push`.

## Conclusión

Para "instalar" el entorno de desarrollo, solo necesito **git** y el binario `hugo`,
que es estático y puedo poner en cualquier sitio; yo lo tengo normalmente en la
carpeta `~/bin/`, que viene en el *path*.

Por mi parte, me limito a trabajar con un repositorio remoto en **GitHub**, con las
operaciones más básicas de **git**, concretamente usando las operaciones de *clone*,
*pull*, *commit* y *push*. El resto es automático por parte de **GitHub Pages**.

```bash
gerard@atlantis:~/sites/linuxsysadmin$ hugo

                   | EN   
+------------------+-----+
  Pages            | 506  
  Paginator pages  |  51  
  Non-page files   |   0  
  Static files     |  51  
  Processed images |   0  
  Aliases          | 310  
  Sitemaps         |   1  
  Cleaned          |   0  

Total in 159 ms
gerard@atlantis:~/sites/linuxsysadmin$ 
```

El nuevo *blog* se construye en unos 150 milisegundos, tiene servidor de desarrollo
integrado, viene con todos los *plugins* necesarios integrados y no hay que instalar
absolutamente nada. Así se agradece redactar nuevos artículos y hacer pequeñas
modificaciones en el tema.

[1]: https://www.staticgen.com/
[2]: {{< relref "/articles/2017/03/generadores-de-contenido-web-estaticos.md" >}}
