Title: Un servidor git con frontal web: Gitea
Slug: un-servidor-git-con-frontal-web-gitea
Date: 2018-06-11 10:00
Category: Sistemas
Tags: git, gitea, docker



Los servidores de **git** son muy útiles, pero si solo lo accedemos mediante terminal, se quedan limitados a pocos usuarios avanzados. Sin embargo, las soluciones con interfaz web, como **GitHub** llegan a todo tipo de usuarios. En un intento de abaratar costes, se han hecho varios clones, entre ellos, **Gitea**.

Realmente hay muchos clones, como **Gitlab** o **Gogs**; de hecho, **Gitea** es un clon de **Gogs** hecho en lenguaje **Go**. Y lo que me llama especialmente la atención es la facilidad en que lo pude instalar: se trata simplemente de ejecutar un contenedor **Docker** que, a diferencia de otros, ocupa relativamente poco espacio de disco.

## Instalación

Lo primero es hacer un `docker pull gitea/gitea`, que es la forma de traernos la imagen desde su correspondiente [repositorio de **DockerHub**](https://hub.docker.com/r/gitea/gitea/). La misma documentación del repositorio indica como debe ejecutarse.

Como punto interesante, **Gitea** utiliza una base de datos para guardar toda aquella información de la página web que no queda reflejada en el propio repositorio. Esta pequeña configuración se indica de forma web, en la primera invocación de la interfaz; las posibilidades son varias: **MySQL**, **MSSQL**, **PostgreSQL** e incluso una base de datos local **SQLite3**.

Es vuestra decisión elegir la que usar, pero por brevedad voy a levantar la instancia de pruebas sin un servidor de base de datos dedicado, confiando en **SQLite3**. Por otra parte, los repositorios se alojan en el sistema de ficheros local; para evitar perderlos en caso de reinicio, lo voy a poner como un volumen local. Os pongo un *docker-compose.yml* de ejemplo, para simplificar el despliegue:

```bash
gerard@sirius:~/tools/gitea$ cat docker-compose.yml 
version: '2'
services:
  gitea:
    image: gitea/gitea
    volumes:
      - ./data:/data
    ports:
      - "3000:3000"
      - "22:22"
gerard@sirius:~/tools/gitea$ 
```

Evidentemente, la carpeta de datos de **Gitea** debe existir en el servidor, con lo que la he creado en la misma carpeta:

```bash
gerard@sirius:~/tools/gitea$ tree
.
├── data
└── docker-compose.yml

1 directory, 1 file
gerard@sirius:~/tools/gitea$ 
```

Solo nos queda levantar los contenedores usando los comandos habituales de *docker-compose*:

```bash
gerard@sirius:~/tools/gitea$ docker-compose up -d
Creating network "gitea_default" with the default driver
Creating gitea_gitea_1
gerard@sirius:~/tools/gitea$ 
```

Nuestra instancia de **Gitea** queda expuesta en *localhost*, concretamente el puerto 3000 para la web, y el puerto 22 para la comunicación SSH con la que se lanzan las peticiones de *clone*, *push* o *pull*.

Cabe decir que la primera vez que entremos en la web habrá que configurar algunos detalles; solo recomiendo tocar los de la base de datos y aquellos que son meramente cosméticos, como por ejemplo el título del sitio. Si no rellenáis la parte del administrador, este rol va a recaer en el primer usuario que se registre; aseguraos de ser vosotros.

Os dejo una imagen que vale más que mil palabras.

![Frontal de Gitea]({static}/images/gitea.jpg)
