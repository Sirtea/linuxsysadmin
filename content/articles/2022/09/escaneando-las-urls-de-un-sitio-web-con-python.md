---
title: "Escaneando las URLs de un sitio web con Python"
slug: "escaneando-las-urls-de-un-sitio-web-con-python"
date: "2022-09-12"
categories: ['Desarrollo']
tags: ['python', 'sitemap', 'xml', 'cache']
---

Hay muchos motivos para recolectar las URLs de un sitio web, tanto legítimas como
ilegítimas; es una herramienta que, como todas, se puede utilizar para el bien o para
el mal. En mi caso, la petición recibida era legítima: un cliente necesitaba hacer
peticiones web con regularidad para mantenerlas *cacheadas* en la CDN que usaba.<!--more-->

Pensándolo bien, solo hay dos tareas necesarias para cumplir con esto:

* Extraer las URLs de alguna lista o, mejor todavía, de un *sitemap*.
* Una forma de lanzar esas peticiones con cierta regularidad:
    * Un *script* en una tarea tipo **cron** que las vaya pidiendo todas, una tras otra.
    * Un servicio en *background* que vaya lanzándolas poco a poco, posiblemente desde una cola circular previamente cargada.

En este artículo nos vamos a centrar en la primera parte, que es la de extraer las
URLs de un *sitemap*, con el único propósito de demostrar una vez más que **python**
nos ofrece todo lo que podamos necesitar.

Es bien cierto que si rebuscamos entre los paquetes de [PyPi][1] podemos encontrar
paquetes que nos hacen el trabajo sucio, como por ejemplo [este][2] [mismo][3].

Si hacemos esto, vamos a necesitar confiar en librerías de terceras personas, que
normalmente tienen un soporte limitado o no reciben atención desde hace años
(ahora mismo, el último *commit* es de septiembre de 2020). Mejor nos centramos en
la librería estándar de **python**.

## Construyendo nuestro propio extractor de URLs

Todos sabemos lo que es un *sitemap*: un documento formal XML que puede incluir URLs
de páginas y otros *sitemaps*. Podemos descargarnos ese documento XML con cualquier
librería que nos permita hacer una petición web, y luego *parsear* el resultado
buscando lo que nos interesa.

Para limitarme a la librería estándar, voy a utilizar los módulos **urllib** y
**xml**, que me ofrecen el método `urlopen` y el *parser* `minidom` en la misma
librería estándar de **python**. Esto solo es una decisión personal y hay otras
maneras de hacerlo, como por ejemplo el módulo **lxml**, **beautifulsoup** o
**requests** para las peticiones al *sitemap*.

Lo importante a tener en cuenta es que el *tag* `url` puede estar en dos contextos:
dentro de un `urlset` (que indica que es un grupo de URLs de páginas), o dentro del
*tag* `sitemap` dentro de un *tag* `sitemapindex`.

El resto no tiene ninguna complicación: creamos un generador `extract_urls` que
reciba la URL del *sitemap* y nos vaya dando sus URLs, con la opción de mirar
en los otros posibles *sitemaps* encontrados, de forma recursiva.

A partir de aquí, lo que se haga con la lista, entraría en otro objetivo. Para
tener la foto completa, me limitaré a recoger las URLs (quitando posibles repetidos)
y a pedirlas una a una, separadas por una pequeña espera.

El resultado en toda su gloria, apenas 10 líneas del generador, otras tantas para
el lanzador de peticiones y poco más...

```python
#!/usr/bin/env python3

import sys
from urllib.request import Request, urlopen
from xml.dom.minidom import parseString
import time
import requests

SITEMAP = sys.argv[1]


def extract_urls(sitemap_url, recurse=True):
    with urlopen(Request(sitemap_url)) as resp:
        dom = parseString(resp.read())
        for urls in dom.getElementsByTagName('urlset'):
            for loc in urls.getElementsByTagName('loc'):
                yield loc.childNodes[0].data
        if recurse:
            for sitemaps in dom.getElementsByTagName('sitemap'):
                for loc in sitemaps.getElementsByTagName('loc'):
                    yield from extract_urls(loc.childNodes[0].data)


if __name__ == '__main__':
    print(f'Warming URLs from {SITEMAP}')
    urls = set(extract_urls(SITEMAP, recurse=True))
    i = 0
    for url in urls:
        i += 1
        print(f'{i}/{len(urls)} - {url}')
        r = requests.get(url)
        time.sleep(0.1)
```

**NOTA**: El lanzador de peticiones web se ha puesto con **requests**. Esto obedece
a un intento de simplificar la solución; como no es la parte importante del artículo,
no le voy a prestar más atención. Podéis cambiar el `requests.get` por un `urlopen`
que ya hemos hecho más arriba.

```bash
gerard@tropico:~/workspace$ ./warmer.py https://www.linuxsysadmin.ml/sitemap.xml
Warming URLs from https://www.linuxsysadmin.ml/sitemap.xml
1/578 - https://www.linuxsysadmin.ml/tag/backup.html
2/578 - https://www.linuxsysadmin.ml/tag/libc.html
3/578 - https://www.linuxsysadmin.ml/tag/blog.html
4/578 - https://www.linuxsysadmin.ml/tag/mongodb.html
5/578 - https://www.linuxsysadmin.ml/tag/isolinux.html
6/578 - https://www.linuxsysadmin.ml/2017/05/generacion-facil-de-certificados-con-easyrsa.html
7/578 - https://www.linuxsysadmin.ml/2022/07/haciendo-backups-de-repositorios-git.html
...
```

Y con esto, sumo otro éxito para **python**, con una solución simple, rápida y elegante.

[1]: https://pypi.org/
[2]: https://pypi.org/project/ultimate-sitemap-parser/
[3]: https://github.com/mediacloud/ultimate-sitemap-parser
