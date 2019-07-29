---
title: "Generadores de contenido web estáticos"
slug: "generadores-de-contenido-web-estaticos"
date: 2017-03-13
categories: ['Miscelánea']
tags: ['html', 'generador estático', 'hugo']
---

Antes de la masiva invasión de **PHP** y **mysql** en todos los proveedores de internet, existían solamente las páginas **HTML** estáticas. Los servidores eran más simples y tenían menos superficie de ataque, aunque mantener las páginas web era un auténtica pesadilla; para eso se han creado los generadores web estáticos.<!--more-->

Cuando solicitamos una página web a un servidor dinámico, existe un código fuente que se suele encargar de conseguir los datos de una base de datos y mezclarlos con un tema para generar la página, todo en tiempo de *runtime*. Este modelo es relativamente lento y exige la existencia de una base de datos y de un procesado en el servidor, aunque suele ofrecer una bonita interfaz para añadir contenido *online* desde casi cualquier sitio.

Este modelo es muy adecuado para páginas y **APIs** con un contenido rápidamente cambiante, pero para una página tipo *blog* es poco eficiente. Si tenemos en cuenta que un *blog* se actualiza relativamente poco, pero se lee teóricamente mucho, entonces necesitamos reducir el tiempo de *renderizado* de la página, incluso suprimiéndolo.

Sin embargo, a alguien se le ocurrió una idea nueva: ¿que pasaría si cuando un editor cambia su contenido, generara **TODAS** las páginas posibles y el servidor se limitara a servir esos ficheros previamente generados?

En este caso, solamente necesitaríamos un servidor web normal, como por ejemplo *Apache* o *Nginx*, e incluso se podría alojar gratuitamente en servicios que sirvan páginas **HTML** estáticas, como por ejemplo, en *GitHub*.

**NOTA**: La combinación de *GitHub Pages* con el generador estático *Pelican* es lo que utiliza este *blog* para llegar al público general.

La clave de éxito para simplificar el mantenimiento de cualquier página web consiste en separar el contenido de la presentación, de forma que un editor no necesita conocer **HTML** para crear su web, mientras que un diseñador se puede limitar a crear temas. También es interesante usar un formato de ficheros para no depender de una base de datos.

Con esto en mente, la mayoría de los generadores estáticos son mas o menos iguales: se trata de un *software* que se dedica a generar todas las páginas web a partir de un contenido (normalmente en ficheros) y de unas plantillas (el tema). Como la lista es gigantesca, vamos a dejar a otros que la mantengan, pero ejemplo en [StaticGen - Top Open-Source Static Site Generators](https://www.staticgen.com/).

## Un caso práctico con Hugo

Ojeando el *ranking*, vemos que la lista es muy larga y elegir una de estas soluciones no es fácil. Vamos a ser prácticos: no quiero instalar **ruby** en mi máquina, así que usaremos el siguiente, que es un binario solitario y no ensucia mi entorno de trabajo; además presume de ser rápido. Así pues, el candidato es [Hugo](http://gohugo.io/).

Otros enlaces de interés para seguir este artículo se localizan en la documentación, concretamente en [Installing](http://gohugo.io/overview/installing/) y en [Quickstart](http://gohugo.io/overview/installing/). Encontraréis una buena documentación de cada aspecto del funcionamiento en la barra lateral de cualquier página de documentación.

### Instalación

En mi caso, la *release* que necesito es <https://github.com/spf13/hugo/releases/download/v0.18.1/hugo_0.18.1_Linux-64bit.tar.gz>. Así que la descargo. El fichero comprimido lleva el binario y otros ficheros de documentación.

```bash
gerard@aldebaran:~$ tar tf hugo_0.18.1_Linux-64bit.tar.gz 
hugo_0.18.1_linux_amd64/hugo_0.18.1_linux_amd64
hugo_0.18.1_linux_amd64/README.md
hugo_0.18.1_linux_amd64/LICENSE.md
gerard@aldebaran:~$ 
```

Lo descomprimimos y lo ponemos en algún lugar del *path* por comodidad, asegurando que tiene permisos de ejecución y que lo ejecutamos sin problemas:

```bash
gerard@aldebaran:~$ tar xf hugo_0.18.1_Linux-64bit.tar.gz 
gerard@aldebaran:~$ cp hugo_0.18.1_linux_amd64/hugo_0.18.1_linux_amd64 ~/bin/hugo
gerard@aldebaran:~$ chmod a+x bin/hugo 
gerard@aldebaran:~$ hugo version
Hugo Static Site Generator v0.18.1 BuildDate: 2017-02-14T13:43:15+01:00
gerard@aldebaran:~$ 
```

### Creación de una nueva web

Nuestra nueva web necesita una estructura de carpetas muy concreta que podemos crear con un simple comando, indicando la carpeta contenedora.

```bash
gerard@aldebaran:~/workspace$ hugo new site site1
Congratulations! Your new Hugo site is created in /home/gerard/workspace/site1.

Just a few more steps and you're ready to go:

1. Download a theme into the same-named folder.
   Choose a theme from https://themes.gohugo.io/, or
   create your own with the "hugo new theme <THEMENAME>" command.
2. Perhaps you want to add some content. You can add single files
   with "hugo new <SECTIONNAME>/<FILENAME>.<FORMAT>".
3. Start the built-in live server via "hugo server".

Visit https://gohugo.io/ for quickstart guide and full documentation.
gerard@aldebaran:~/workspace$ 
```

O de forma similar, para usar la carpeta actual:

```bash
gerard@aldebaran:~/workspace$ mkdir site2
gerard@aldebaran:~/workspace$ cd site2
gerard@aldebaran:~/workspace/site2$ hugo new site .
Congratulations! Your new Hugo site is created in /home/gerard/workspace/site2.

Just a few more steps and you're ready to go:

1. Download a theme into the same-named folder.
   Choose a theme from https://themes.gohugo.io/, or
   create your own with the "hugo new theme <THEMENAME>" command.
2. Perhaps you want to add some content. You can add single files
   with "hugo new <SECTIONNAME>/<FILENAME>.<FORMAT>".
3. Start the built-in live server via "hugo server".

Visit https://gohugo.io/ for quickstart guide and full documentation.
gerard@aldebaran:~/workspace/site2$ cd ..
gerard@aldebaran:~/workspace$ 
```

Así nos queda el esqueleto de nuestra carpeta contenedora:

```bash
gerard@aldebaran:~/workspace/site1$ tree -F
.
├── archetypes/
├── content/
├── data/
├── layouts/
├── static/
├── themes/
└── config.toml

6 directories, 1 file
gerard@aldebaran:~/workspace/site1$ 
```

Ahora necesitamos un tema para *renderizar* nuestra web. Podemos crear un tema propio siguiendo la documentación, si así lo deseamos; para no extendernos, voy a utilizar uno que ya existe y que podemos encontrar en el sitio de [temas de Hugo](http://themes.gohugo.io/). Por defecto no viene ningún tema, así que las páginas saldrían en blanco.

```bash
gerard@aldebaran:~/workspace/site1$ (cd themes; git clone https://github.com/comfusion/after-dark)
Cloning into 'after-dark'...
remote: Counting objects: 542, done.
remote: Total 542 (delta 0), reused 0 (delta 0), pack-reused 542
Receiving objects: 100% (542/542), 6.26 MiB | 941.00 KiB/s, done.
Resolving deltas: 100% (296/296), done.
Checking connectivity... done.
gerard@aldebaran:~/workspace/site1$ 
```

Si miramos en la carpeta `themes/`, veremos que ha aparecido una nueva carpeta con el tema deseado; el nombre de la carpeta es el parámetro que vamos a usar para indicar que tema usaremos.

```bash
gerard@aldebaran:~/workspace/site1$ ls themes/
after-dark
gerard@aldebaran:~/workspace/site1$ 
```

Es un buen momento para modificar la configuración del sitio, siendo especialmente importante indicar el tema a usar. Si no lo hacemos, tendremos que indicarlo como parámetro cada vez que invoquemos el resto de comandos.

```bash
gerard@aldebaran:~/workspace/site1$ cat config.toml 
languageCode = "en-us"
title = "My New Hugo Site"
baseurl = "http://example.org/"
theme = "after-dark"
gerard@aldebaran:~/workspace/site1$ 
```

**TRUCO**: Para cambiar el tema de nuestra web, solo hace falta poner un tema nuevo en la carpeta `themes/` y configurar el fichero con el nuevo tema. Esto nos permite probar temas diferentes; de hecho, todas las páginas van a ser reconstruidas con el nuevo tema. Si solo queremos ver que tal queda un tema, no hace falta modificar el fichero de configuración; con ejecutar `hugo` con el *flag* `--theme <tema>` nos bastaría.

### Generando contenido

La mecánica básica de trabajo es muy simple: creamos un nuevo contenido, levantamos el servidor de desarrollo y nos limitamos a ir viendo como cambia la página tal como vamos modificando y guardando el contenido.

El servidor de desarrollo es una herramienta muy útil, y no hay ningún motivo por el que no esté permanentemente corriendo mientras trabajamos:

* Levanta un servidor web local que sirve las páginas desde memoria
* Reconstruye el contenido en memoria cada vez que un fichero cambia
* Sustituye todas las ocurrencias del parámetro `baseurl` por `localhost`, para su funcionamiento local

Esto significa que se generará ningún fichero en disco. Para eso hay otros comandos.

```bash
gerard@aldebaran:~/workspace/site1$ hugo server
Started building sites ...
Built site for language en:
0 draft content
0 future content
0 expired content
0 regular pages created
1 other pages created
0 non-page files copied
0 paginator pages created
0 tags created
0 categories created
total in 14 ms
Watching for changes in /home/gerard/workspace/site1/{data,content,layouts,static,themes}
Serving pages from memory
Web Server is available at http://localhost:1313/ (bind address 127.0.0.1)
Press Ctrl+C to stop
```

Ahora creamos una nueva página, por ejemplo un *post* nuevo:

```bash
gerard@aldebaran:~/workspace/site1$ hugo new post/lorem-ipsum.md
/home/gerard/workspace/site1/content/post/lorem-ipsum.md created
gerard@aldebaran:~/workspace/site1$ 
```

Y lo editamos a placer. Me voy a limitar a usar un generador de texto *markdown*, que se encuentra [aquí](https://jaspervdj.be/lorem-markdownum/).

```bash
+++
description = "no description"
date = "2017-02-14T15:51:57+01:00"
title = "Gratia retia iamque"
tags = ["lorem", "ipsum"]
categories = ["uncathegorized"]
draft = false
+++



## Mihi arguit hastam securaque face vigilans obruta

Lorem markdownum amoris illis, spicea, daedalus intonsum procul certo dubioque, inmitibus. Verti frondescere et natura Hymettia carmine *candidus Agenorides* perdere.

    swappableEbookHard.metaSkinNybble(simmApple);
    desktopWebMouse = page(analog_rt_regular, eSession, menu_oem);
    var prompt = dns_megabit(softShell(duplexMediaYoutube, netiquette, fontBrouterPng), 2);

## Imagine sub nomine occursu

Parvas pater. Ter modo quassaque collo. Aequora chori nec tumulum *gemitus quibus*.

Odiumque duo, aera prolem mox silvas poteratque sagittis quoque crine fert. Longo ferarum temptaminis stagna vultum et urbe Peripha, Aeginam. Ne O acuto tam Thetis solita cognati robora sit tellure, et Alcyone moenia vitiorum. Solis iam omnes Lucina non suis *utroque novis* sagittam suo carchesia Achivi repleri ingratus quem.

## Iactasque caelatus me foret aequi

Has serta relictis, non Lucina, Phylius falsa adflata sudore. [Fago inserit palpitat](http://romamtot.io/hos) rubentia adspicit et dolore *refert ita*, et. Quod suppressis novat sororis ubique astu; pedibus spectabat dixere loquax comitem, nobis effugit; tibi cibo nunc oppugnant.

Inania agat cum vidi cruribus et lanas nepotem Tethyn, umbris Agenorides stamina omnes sed fecit absumitur acclinia. Morati femina deam thyrsos vultus aequales suo deum faciem draconis diurnis liquor contentus.

Sine in robora aureus ignavis bella vaga super multa saepe atque tot **sceleratior sunt**, est furiale. Felix flammas quiete; omnis vidi quoque sagittas cruentum prosunt tot vultus iamque! Auget comis me precibus vetus, hausit diversa an tulimus laniem amores *retro aequalique*. Molli arbore, altera nota; furore posuisset in post Midan pollice et multos poteras.
```

Vemos que el servidor de desarrollo ha detectado el cambio y ha regenerado el contenido:

```bash
gerard@aldebaran:~/workspace/site1$ hugo server
...
Change detected, rebuilding site
2017-02-14 15:56 +0100
Source changed /home/gerard/workspace/site1/content/post/lorem-ipsum.md
Built site for language en:
0 draft content
0 future content
0 expired content
1 regular pages created
7 other pages created
1 non-page files copied
5 paginator pages created
2 tags created
1 categories created
total in 8 ms
```

Y si apuntamos nuestro navegador a la URL sugerida `http://localhost:1313/` podremos ver nuestro sitio web con las modificaciones pertinentes.

A lo largo de la vida de la página, vamos a repetir este paso muchas veces, tal como queramos ir añadiendo más páginas.

### Listos para publicar

Finalmente estamos contentos con el contenido y decidimos que está listo para ser generado como ficheros **HTML** para su publicación. Esto se consigue con el uso del comando `hugo` sin mas parámetros.

```bash
gerard@aldebaran:~/workspace/site1$ hugo
Started building sites ...
Built site for language en:
0 draft content
0 future content
0 expired content
1 regular pages created
7 other pages created
0 non-page files copied
5 paginator pages created
2 tags created
1 categories created
total in 27 ms
gerard@aldebaran:~/workspace/site1$ 
```

Y esto nos deja los ficheros en la carpeta `public/` para que los publiquemos según nuestro método de despliegue favorito, sea **FTP**, **rsync**, o cualquier otro método. Encuentro especialmente interesante el [uso de GitHub](https://gohugo.io/tutorials/github-pages-blog/) para alojar la web.
