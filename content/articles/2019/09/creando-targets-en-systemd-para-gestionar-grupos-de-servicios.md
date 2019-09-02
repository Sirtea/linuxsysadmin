---
title: "Creando targets en systemd para gestionar grupos de servicios"
slug: "creando-targets-en-systemd-para-gestionar-grupos-de-servicios"
date: "2019-09-02"
categories: ['Operaciones']
tags: ['linux', 'systemd', 'target']
---

Tras aprender más de **systemd** y su modo de usuario, vi infinitas posibilidades para los servicios de usuario. Dependiendo del tipo de tarea en la que iba a trabajar, parecía lógico tener un subconjunto de servicios ejecutando en segundo plano. ¿Había alguna manera de levantar varios con un solo comando?<!--more-->

Hay muchas ideas corriendo por internet, pero parece que la más correcta es aquella que fue diseñada específicamente para ello: los *targets*. Básicamente se trata de un conjunto de otras *units* (sean *services*, *timers* u otros *targets*).

Y es que no puede ser más fácil: se declara una *unit* tipo *target* y se hace que el resto de *units* tengan la directiva `WantedBy=`. Así pues, cuando se activa ese servicio con `systemctl enable`, se crea el árbol de dependencias que causa que -si se levanta el *target*- se levante todo el resto.

A modo de ejemplo voy a documentar una de las tareas más simples que puse en práctica inmediatamente; se trata de un *target* para levantar dos "servicios" que utilizo cuando trabajo con el generador estático **hugo**:

* Un servidor web para servir el sitio
* Un timer que dispare una reconstrucción del sitio

La configuración nos quedaría así:

```bash
gerard@eden:~$ tree .config/systemd/
.config/systemd/
└── user
    ├── build-loremipsum.service
    ├── build-loremipsum.timer
    ├── hugo.target
    └── ran.service

1 directory, 4 files
gerard@eden:~$ 
```

La verdad es que mucho de este trabajo ya lo hicimos en otros artículos, concretamente [este][1] y [este otro][2]; leerlos simplifica mucho este artículo.

## El target para trabajar con hugo

Un *target* es el más simple de las *units* de **systemd**. Como no hace nada y son los demás los que "se le instalan", las directivas necesarias son mínimas:

```bash
gerard@eden:~$ cat .config/systemd/user/hugo.target 
[Unit]
Description=Hugo development: server and builder
gerard@eden:~$ 
```

No he puesto sección `[Install]` porque no deseo hacer un `systemctl enable`; la idea es que este *target* no se levante solo, sino a petición mía. Esto lo voy a poder cambiar en el futuro si lo necesito.

## Creamos un sitio web básico

No tiene mucho sentido hablar de servir una web hecha con **hugo** o de construirla si no existe; así que necesitamos un esqueleto básico de trabajo.

```bash
gerard@eden:~$ hugo new site loremipsum
Congratulations! Your new Hugo site is created in /home/gerard/loremipsum.

Just a few more steps and you're ready to go:

1. Download a theme into the same-named folder.
   Choose a theme from https://themes.gohugo.io/, or
   create your own with the "hugo new theme <THEMENAME>" command.
2. Perhaps you want to add some content. You can add single files
   with "hugo new <SECTIONNAME>/<FILENAME>.<FORMAT>".
3. Start the built-in live server via "hugo server".

Visit https://gohugo.io/ for quickstart guide and full documentation.
gerard@eden:~$ 
```

Basta que trabajemos en un esqueleto capaz de generar la carpeta `public/` (es la que vamos a servir) y el fichero `404.html` (porque **ran** requiere que exista este fichero).

Vamos a poner un *theme* adecuado (basta que genere el fichero `404.html` por ahora) y vamos a generar la configuración mínima e indispensable, lo que nos deja un esqueleto así:

```bash
gerard@eden:~/loremipsum$ tree
.
├── config.toml
├── content
└── themes
    └── loremipsum
        ├── layouts
        │   ├── 404.html
        │   └── index.html
        └── static

5 directories, 3 files
gerard@eden:~/loremipsum$ 
```

Generamos el contenido HTML para obtener el contenido a servir y verificamos que funciona y que cumplimos con los requisitos:

```bash
gerard@eden:~/loremipsum$ hugo

                   | EN  
+------------------+----+
  Pages            |  2  
  Paginator pages  |  0  
  Non-page files   |  0  
  Static files     |  0  
  Processed images |  0  
  Aliases          |  0  
  Sitemaps         |  0  
  Cleaned          |  0  

Total in 8 ms
gerard@eden:~/loremipsum$ tree public/
public/
├── 404.html
└── index.html

0 directories, 2 files
gerard@eden:~/loremipsum$ 
```

Y con esto podemos seguir.

## El servidor web

Esto es prácticamente un *copy-paste* de [este artículo anterior][1]. Básicamente se trata de escribir una *service unit* y hacer el respectivo `systemctl enable`, para ligarlo con el nuevo *target*.

```bash
gerard@eden:~$ cat .config/systemd/user/ran.service 
[Unit]
Description=Ran: a simple static web server written in Go
PartOf=hugo.target

[Service]
ExecStart=/home/gerard/bin/ran -r /home/gerard/loremipsum/public/ -404=/404.html

[Install]
WantedBy=hugo.target
gerard@eden:~$ 
```

**TRUCO**: Se añade la directiva `PartOf=` para que se pare este *service* si se para el *target*.

```bash
gerard@eden:~$ systemctl --user enable ran.service
Created symlink /home/gerard/.config/systemd/user/hugo.target.wants/ran.service → /home/gerard/.config/systemd/user/ran.service.
gerard@eden:~$ 
```

**WARNING**: Antes de levantar el servicio habría que asegurar que tanto la carpeta `/home/gerard/loremipsum/public/` como el fichero `404.html` existen, o **ran** va a acabar prematuramente con un error.

## El constructor del sitio

Para que se vaya actualizando el contenido en función a los cambios de contenidos vamos a necesitar un "algo" que lo haga, y sea invocado cada cierto tiempo. Para la primera parte, vamos a hacer un *script* que construya el sitio, y vamos a confiar en un *timer* de **systemd** para que se vaya lanzando; nuevamente, es un *copy-paste* de [un artículo anterior][2].

La parte importante para el *script* de construcción es que se ejecuta en la carpeta personal y sin las variables de entorno, especialmente el `PATH`. Podemos corregir ambos problemas utilizando *paths* absolutos en nuestro *script*.

```bash
gerard@eden:~$ cat bin/build-loremipsum.sh 
#!/bin/bash

cd /home/gerard/loremipsum
rm -Rf public/*
/home/gerard/bin/hugo
rm -Rf resources
gerard@eden:~$ 
```

Comprobar su funcionamiento es trivial:

```bash
gerard@eden:~$ ./bin/build-loremipsum.sh 

                   | EN  
+------------------+----+
  Pages            |  2  
  Paginator pages  |  0  
  Non-page files   |  0  
  Static files     |  0  
  Processed images |  0  
  Aliases          |  0  
  Sitemaps         |  0  
  Cleaned          |  0  

Total in 8 ms
gerard@eden:~$ 
```

Para ejecutar periodicamente necesitamos dos *units*: un *timer* y el *service* para que este lo invoque. Mas información en el citado artículo.

```bash
gerard@eden:~$ cat .config/systemd/user/build-loremipsum.service 
[Unit]
Description=LoremIpsum site builder

[Service]
Type=oneshot
ExecStart=/home/gerard/bin/build-loremipsum.sh
gerard@eden:~$ 
```

```bash
gerard@eden:~$ cat .config/systemd/user/build-loremipsum.timer 
[Unit]
Description=Ejecutar build-loremipsum.sh cada 5 segundos
PartOf=hugo.target

[Timer]
OnActiveSec=2
OnUnitActiveSec=5
AccuracySec=1us

[Install]
WantedBy=hugo.target
gerard@eden:~$ 
```

**TRUCO**: La directiva `PartOf=` es la responsable de parar este *timer* si se para el *target*.

**TRUCO**: Con la directiva `OnActiveSec=` conseguimos que se retrase el *timer* dos segundos desde su inicio; esto sirve para que **ran** se levante antes del *build* y no coincida el borrado del fichero `404.html` con el levantamiento de **ran**, lo que causaría un error.

Activamos el *timer* para que se levante con el `hugo.target` y listo:

```bash
gerard@eden:~$ systemctl --user enable build-loremipsum.timer
Created symlink /home/gerard/.config/systemd/user/hugo.target.wants/build-loremipsum.timer → /home/gerard/.config/systemd/user/build-loremipsum.timer.
gerard@eden:~$ 
```

## Algunas comprobaciones

Como no hicimos el `systemctl --user enable hugo.target`, hay que levantar el *target* a mano. Lo hacemos:

```bash
gerard@eden:~$ systemctl --user start hugo.target
gerard@eden:~$ 
```

Ahora ya podemos trabajar en el contenido o el tema del sitio **hugo**. Solo hay que tener en cuenta que el (re)generado de la web puede tardar hasta 5 segundos, pero nos ahorramos de hacerlo manualmente.

Si abrimos la web en `https://localhost:8080/` veremos la versión inicial; creamos contenido en la carpeta del sitio web y, tras 5 segundos máximo, vemos los cambios si recargamos el navegador.

Finalmente decidimos dejar de trabajar en el sitio, y decidimos que no necesitamos esos *services* y *timers*; queremos pararlos, y para ello disponemos de 2 maneras:

* Cerrar sesión, dejando a **systemd** limpiar lo que hemos dejado en marcha.
* Utilizar el comando `systemctl stop` para parar el *target*, y con ello sus servicios `PartOf=`.

Vamos a optar por la segunda opción, solamente para probar que funciona:

```bash
gerard@eden:~$ systemctl --user stop hugo.target
gerard@eden:~$ 
```

Solo nos queda comprobar con un `ps faux` que no queda ni rastro del servidor web **ran**. Comprobar que el *builder* no sigue ejecutando es más complejo; podemos:

* Lanzar `ps faux` a intervalos con la esperanza de ver que se ha lanzado el *builder*.
* Revisar el tiempo de generación del contenido y observar que no cambia su *timestamp*.
* Revisar los *logs* de **systemd** con `journalctl` para comprobar que no se sigue ejecutando nada.

Visto que todo está correctamente parado, lo doy por bueno.

[1]: {{< relref "/articles/2019/08/utilizando-systemd-a-nivel-de-usuario.md" >}}
[2]: {{< relref "/articles/2019/08/programando-tareas-con-timers-en-systemd.md" >}}
