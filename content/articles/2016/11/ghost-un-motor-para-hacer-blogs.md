---
title: "Ghost: Un motor para hacer blogs"
slug: "ghost-un-motor-para-hacer-blogs"
date: 2016-11-21
categories: ['Miscelánea']
tags: ['ghost', 'blog']
---

Hace tiempo que me recorre la idea de crear un motor genérico de *blogs*. Son varias las veces que he empezado alguno aprovechando los *frameworks*, especialmente de **python**. Todas ellas han acabado en la papelera por falta de ganas. Finalmente me di por vencido y decidí utilizar algo ya hecho.<!--more-->

Prueba de mi pereza es este *blog*, que está hecho con **Pelican**, que es un generador de contenido estático, juntando un tema y un contenido. Como control de versiones usa **git** y está alojado en **Github Pages**. Para publicar hace falta crear el contenido, invocar algunos comandos para generar el contenido **HTML** y levantar un servidor local para ver los cambios. Todo muy *techie*.

He seguido buscando para encontrar una solución con base de datos, que se rellene fácilmente mediante un formulario y que pueda utilizar cualquiera. Basta con mirar un poco por internet para ver que las soluciones con miles: desde los omnipresentes **Wordpress** hasta los todopoderosos **Drupal** y **Joomla**, pasando por cosas mas esotéricas.

La solución la encontré hace un par de meses; era bonita, simple y tenía material de soporte suficiente, sin ser agobiante. Se trata de [Ghost](https://ghost.org/), encontrando su repositorio en [GitHub](https://github.com/TryGhost/Ghost).

La instalación es también muy simple:

1. Descargar la última versión de **Ghost**.
2. Descomprimir el fichero comprimido en la carpeta en donde lo queramos.
3. Instalar las dependencias con *npm install --production*
4. Levantar el servicio con *npm start* (desarrollo) o *npm start --production*.

Y ya tenemos nuestro *blog* visible en <http://localhost:2368/> con su interfaz de administración en <http://localhost:2368/ghost/>. Estos valores pueden cambiarse en el fichero *config.js*.

El problema de esta aproximación es que la versión de **Ghost**, de **NPM** y de **NodeJS** son demasiado importantes, exigiendo versiones elevadas que no están en los repositorios oficiales de la mayoría de distribuciones. Lo pude instalar en una *Ubuntu 16.04* y, aun así, el binario exigido */usr/bin/node* no se llamaba así, sino que estaba en */usr/bin/nodejs*. Esto se puede solucionar con un simple enlace simbólico, pero busca el error...

Lo que realmente me llamó a probarlo es la facilidad adicional de tenerlo funcionando sin problemas, mediante una imágen de **Docker** prefabricada en **DockerHub**. De hecho la imagen es oficial, y la podéis encontrar en <https://hub.docker.com/_/ghost/>.

Levantamos la imagen con el habitual y recomendado *docker run*:

```bash
gerard@janus:~$ docker run -d -p 2368:2368 ghost
6a0d4ed51f2b7c04b7b0c54cac44256d12fe7fa999f548314858ea5838faae73
gerard@janus:~$ 
```

Esto nos da un **Ghost** levantado en modo de *development*. Si queremos levantarlo en modo *production*, basta con añadir una variable de entorno *NODE_ENV=production*. Tal como escribo este artículo, la configuración por defecto para producción está incompleta: falta la directiva *paths* en la sección *production*, aunque la podéis copiar tal cual de la sección *development*. Las otras directivas las podéis editar según vuestras necesidades.

**TRUCO**: si usáis **docker**, no vale con poner una configuración adecuada en */var/lib/ghost/config.js*, porque entonces el instalador detecta que ya hay cosas y no copia el resto de ficheros en */usr/src/ghost/*. Vuestras configuraciones deberían reescribir el fichero */usr/src/ghost/config.example.js*.

```bash
gerard@telesto:~/docker/custom_ghost$ cat Dockerfile 
FROM ghost
COPY config.js /usr/src/ghost/config.example.js
gerard@telesto:~/docker/custom_ghost$ 
```

**TRUCO**: la configuración de **Ghost** es un *script* en **NodeJS** y es capaz de leer las variables de entorno, por si queréis pasar algunas variables en *runtime*, sin construir varias imágenes.

```bash
gerard@telesto:~/docker/custom_ghost$ cat config.js 
var path = require('path'),
    config;

config = {
    production: {
        url: process.env['GHOST_URL'],
        mail: {},
        database: {
            client: 'sqlite3',
            connection: {
                filename: path.join(__dirname, '/content/data/ghost.db')
            },
            debug: false
        },
        server: {
            host: '127.0.0.1',
            port: '2368'
        },
        paths: {
            contentPath: path.join(__dirname, '/content/')
        }
    }
};

module.exports = config;
gerard@telesto:~/docker/custom_ghost$ 
```

Apuntamos nuestro navegador a la URL configurada, y ya tenemos un *blog* funcional. Queda para el propietario ir a la sección de administración para añadir contenido, cambiar los temas y lo que haga falta, cómodamente desde la web.

![Ghost Blog](/images/ghost_blog.jpg)

La parte "mala" es que cada instancia de **Ghost** es un proceso propio, que usa su propia dirección y su propio puerto. Si se quiere desplegar varios *blogs* en el mismo servidor, podemos usar un **nginx**, que los diferencie por el dominio solicitado mediante *virtualhosts*; luego hacemos un *proxy_pass* al puerto de verdad, y ya tenemos el servidor montado. Esto queda como material para otro artículo.
