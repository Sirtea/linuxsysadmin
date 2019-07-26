---
title: "Un terminal SSH en nuestro navegador web usando Wetty"
slug: "un-terminal-ssh-en-nuestro-navegador-web-usando-wetty"
date: 2017-09-25
categories: ['Operaciones']
tags: ['ssh', 'terminal', 'wetty']
---

No siempre tenemos acceso a nuestro terminal SSH favorito para acceder a nuestros entornos en caso de emergencia. De hecho, en muchas redes suelen prohibir el tráfico por otros puertos ajenos a la navegación web. Para estos casos podemos tener un terminal SSH a través de una página web propia.<!--more-->

El truco consiste en usar **Wetty**. Si os interesa, podéis encontrar el repositorio de GitHub [aquí](https://github.com/krishnasrinivas/wetty).

> Terminal over HTTP and HTTPS. Wetty is an alternative to ajaxterm/anyterm but much better than them because wetty uses ChromeOS' terminal emulator (hterm) which is a full fledged implementation of terminal emulation written entirely in Javascript. Also it uses websockets instead of Ajax and hence better response time.

Podemos encontrar una imagen en [DockerHub](https://hub.docker.com/r/nathanleclaire/wetty/), que nos vale para una demostración rápida. Sin embargo, el gran tamaño de su imagen la hace impracticable para un uso habitual.

```bash
gerard@aldebaran:~/docker/wetty$ docker images | grep wetty
nathanleclaire/wetty   latest              94635175ccb6        2 years ago         1.2 GB
gerard@aldebaran:~/docker/wetty$ 
```

Así pues, podemos construir otra imagen, basándonos en los pasos de instalación que aparecían en GitHub, con el único añadido de un fichero *.tar.gz* con una imagen del repositorio.

```bash
gerard@aldebaran:~/docker/wetty$ tar tf wetty.tar.gz 
.gitignore
Dockerfile
Gruntfile.js
LICENSE
README.md
app.js
bin/
bin/wetty.conf
bin/wetty.js
bin/wetty.service
package.json
public/
public/index.html
public/wetty/
public/wetty/hterm_all.js
public/wetty/index.html
public/wetty/wetty.js
terminal.png
gerard@aldebaran:~/docker/wetty$ cat Dockerfile 
FROM alpine:3.5
RUN apk add --no-cache nodejs tini
ENV NODE_ENV=production
ADD wetty.tar.gz /srv/app/
WORKDIR /srv/app/
RUN apk add --no-cache python2 make g++ && \
    npm install && \
    apk del python2 make g++
RUN adduser guest -D && \
    echo "guest:guest" | chpasswd
ENTRYPOINT ["/sbin/tini", "--"]
CMD ["node", "app.js", "-p", "3000"]
gerard@aldebaran:~/docker/wetty$ 
```

Esto nos deja una imagen mucho más pequeña, pero nos limita a entrar por SSH en un terminal de *Alpine Linux*, que aunque magnífico, no es tan completo como el de otras distribuciones. Usad la distribución que más os convenga.

```bash
gerard@aldebaran:~/docker/wetty$ docker images | grep wetty
wetty                  latest              45635173077e        35 minutes ago      56.2 MB
gerard@aldebaran:~/docker/wetty$ 
```

Como pretendo utilizarla como un máquina de salto, este tamaño y limitación son más que adecuados. Sin embargo no estaba dispuesto a pagar 1,2 gb por un contenedor que no hace nada por sí mismo...

Solo nos queda ejecutar la imagen exponiendo el puerto 3000 del contenedor, para poder acceder remotamente desde el navegador, que en mi caso estaría en <http://localhost:3000/>.

```bash
gerard@aldebaran:~/docker/wetty$ docker run -ti --rm -p 3000:3000 wetty
http on port 3000
```

**AVISO**: Esta página está desprotegida, sin autenticación ni encriptación. Una buena opción está en dotarla de ambos usando un servidor web **nginx** como frontal. También es interesante modificar el usuario de entrada con par de claves, añadir un cliente de SSH para saltar, y lo que más nos interese.
