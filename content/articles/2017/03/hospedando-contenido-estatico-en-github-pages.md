---
title: "Hospedando contenido estático en Github pages"
slug: "hospedando-contenido-estatico-en-github-pages"
date: 2017-03-20
categories: ['Miscelánea']
tags: ['git', 'github', 'github pages', 'html']
---

Algunas veces nos hemos planteado la posibilidad de tener nuestro propio servidor con nuestras propias aplicaciones, pero el coste del *hosting* nos lo ha hecho replantear, especialmente para proyectos de pruebas sin beneficio. Si no nos importa hospedar contenido **HTML** estático, las páginas de **GitHub** pueden cumplir con nuestras necesidades.<!--more-->

De hecho, este *blog* está hospedado en *GitHub pages* sin ningún coste de *hosting*. Añadimos un nombre de registro gratuito, y obtenemos una plataforma sin coste de mantenimiento.

La contrapartida es que este *blog* está compuesto de páginas **HTML** y no dispone de ninguna base de datos ni de ningún tipo de procesado en el servidor. Mantener este contenido sería una pesadilla, a no ser que se utilicen [generadores automáticos de HTML]({{< relref "/articles/2017/03/generadores-de-contenido-web-estaticos.md" >}}), que es lo que utilizo en este *blog*.

Las páginas de *GitHub* pueden ser de dos tipos: una por cada cuenta de usuario, y una por cada proyecto. De esta forma, como usuarios normales, deberíamos trabajar con las páginas de proyecto, puesto que solo disponemos de una página personal.

## Páginas de proyecto

Cada repositorio puede disponer de un espacio web propio. Solo se necesita indicar a *GitHub* qué rama tratar como *document root*, para que pueda servirla adecuadamente. Vamos a ilustrar como se hace con un ejemplo:

Vamos a empezar creando un nuevo repositorio en <https://github.com/new>, de acuerdo a vuestras preferencias. En mi caso, me he dejado llevar por la sugerencia, puesto que este nombre no influye en nada; de esta forma nuestro repositorio se llama `didactic-meme`.

Como no puede ser de otra forma, vamos a tener que clonar este repositorio para poder trabajar con él.

```bash
gerard@aldebaran:~/projects$ git clone https://github.com/Sirtea/didactic-meme.git
Cloning into 'didactic-meme'...
warning: You appear to have cloned an empty repository.
Checking connectivity... done.
gerard@aldebaran:~/projects$ 
```

Tras poner algún fichero en la rama `master` y hacer un *commit*, podemos crear una rama para alojar nuestro contenido **HTML**. Esta rama se puede llamar `master` (que viene por defecto) o `gh-pages`. Esto es una decisión personal, pero como yo utilizo un generador de páginas **HTML**, yo prefiero dejar la rama `master` para el contenido escrito, y la rama `gh-pages` para el contenido generado.

```bash
gerard@aldebaran:~/projects/didactic-meme$ git checkout -b gh-pages master
Switched to a new branch 'gh-pages'
gerard@aldebaran:~/projects/didactic-meme$ git branch -v
* gh-pages 9b33086 Some master content
  master   9b33086 Some master content
gerard@aldebaran:~/projects/didactic-meme$ 
```

A partir de aquí el flujo de trabajo es el que usaríamos normalmente con **Git**. Creamos el contenido **HTML**, lo copiamos a lo generamos; el resto es tan simple como hacer un *commit* y subirlo a *GitHub* con un *push*.

```bash
gerard@aldebaran:~/projects/didactic-meme$ cat index.html 
<h1>Hello World</h1>
gerard@aldebaran:~/projects/didactic-meme$ 
```

Un detalle del *push*:

```bash
gerard@aldebaran:~/projects/didactic-meme$ git push origin gh-pages
Username for 'https://github.com': sirtea
Password for 'https://sirtea@github.com': 
Total 0 (delta 0), reused 0 (delta 0)
To https://github.com/Sirtea/didactic-meme.git
 * [new branch]      gh-pages -> gh-pages
gerard@aldebaran:~/projects/didactic-meme$ 
```

Y como ya tenemos las dos ramas en *GitHub*, podemos continuar con el *setup* de nuestro sitio. Para ello vamos a la página de nuestro repositorio y cambiamos a la pestaña *Settings*. En esta sección existe un desplegable para elegir la rama que queremos servir como página de proyecto. Seleccionamos `gh-pages` y guardamos.

Solo nos queda visitar la dirección que nos proporcionan en la misma página de *Settings*, y ver que ya tenemos un espacio web.

```bash
gerard@aldebaran:~$ curl https://sirtea.github.io/didactic-meme/
<h1>Hello World</h1>
gerard@aldebaran:~$ 
```

**TRUCO**: las páginas se sirven usando mecanismos de *caché*, así que puede pasar algunos segundos hasta que el contenido se actualice o aparezca. Sed pacientes.

## Sirviendo la página de proyecto con un dominio propio

La verdad es que la dirección que nos ha quedado no es bonita. La buena noticia es que puede ser mejor; podemos servir el contenido en un dominio propio, sin la coletilla del nombre del repositorio.

El primer paso es conseguir un dominio al que tengamos acceso a los registros; vamos a tener que poner un registro *CNAME* apuntando a *GitHub*. Para evitar la lentitud del proceso, vamos a mostrar el caso de este *blog*, ya configurado.

Para que *GitHub* sepa qué página de proyecto debe servir con cada dominio, nos sugieren que pongamos un fichero *CNAME* en la raíz del espacio web. Este fichero solo puede contener un dominio, y debe coincidir con el del dominio elegido.

```
gerard@aldebaran:~$ curl http://www.linuxsysadmin.tk/CNAME
www.linuxsysadmin.tk
gerard@aldebaran:~$ 
```

Ahora solo falta instruir a nuestro DNS para que resuelva las peticiones contra *GitHub*. La forma recomendada es poner un registro *CNAME* apuntando a `<usuario>.github.io`, dejando a su criterio donde apunta este dominio, y despreocupándonos en el caso de que esta dirección IP final cambiara.

```bash
gerard@aldebaran:~$ dig www.linuxsysadmin.tk
...  
;; QUESTION SECTION:
;www.linuxsysadmin.tk.		IN	A
  
;; ANSWER SECTION:
www.linuxsysadmin.tk.	14018	IN	CNAME	sirtea.github.io.
sirtea.github.io.	2394	IN	CNAME	github.map.fastly.net.
github.map.fastly.net.	20	IN	A	151.101.120.133
...  
gerard@aldebaran:~$ 
```

Cada vez que pidamos nuestro dominio, *GitHub* se va a encargar a servir la página de proyecto que corresponde a ese dominio, cosa que sabe porque el fichero *CNAME* se lo indica. con esto nos queda una dirección mas bonita en el navegador web.

```bash
gerard@aldebaran:~$ curl -s http://www.linuxsysadmin.tk/ | head
<!DOCTYPE html>
<html lang="es" prefix="og: http://ogp.me/ns# fb: https://www.facebook.com/2008/fbml">
<head>
    <title>Linux Sysadmin</title>
    <!-- Using the latest rendering mode for IE -->
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">


gerard@aldebaran:~$ 
```

De hecho, si solicitamos la dirección anterior, *GitHub* nos devuelve una redirección al nuevo dominio, ya que asume que es la dirección "oficial".

```bash
gerard@aldebaran:~$ curl -i http://sirtea.github.io/www.linuxsysadmin.tk/
HTTP/1.1 301 Moved Permanently
...  
Location: http://www.linuxsysadmin.tk/
...  

<html>
<head><title>301 Moved Permanently</title></head>
<body bgcolor="white">
<center><h1>301 Moved Permanently</h1></center>
<hr><center>nginx</center>
</body>
</html>
gerard@aldebaran:~$ 
```

## Páginas personales

Las páginas personales son las que se encargan de servir las direcciones tipo `<http|https>://<usuario>.github.io/`, sin la coletilla del proyecto.

El funcionamiento es el mismo, con dos excepciones:

* El repositorio debe llamarse igual que el dominio (`<usuario>.github.io`)
* La rama que se sirve SIEMPRE es la rama `master`

Entonces solo hace falta cargar esa rama de contenido **HTML**. De hecho, el truco del *CNAME* también funciona.
