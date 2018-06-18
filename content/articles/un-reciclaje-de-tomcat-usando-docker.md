Title: Un reciclaje de Tomcat usando Docker
Slug: un-reciclaje-de-tomcat-usando-docker
Date: 2018-06-25 10:00
Category: Sistemas
Tags: tomcat, docker



Hace poco he cambiado de trabajo por motivos personales. En mi nueva posición me he encontrado con un cambio en las tecnologías usadas; lo que me he encontrado es algo que hacía tiempo que no tocaba: basan sus sistemas en **Java** y **Tomcat**. He necesitado un ligero reciclaje en ellos.

Por supuesto, no voy a perder el tiempo en instalar un servidor y luego el **Tomcat** pertinente; experiencias pasadas nos demuestran que es mucho más fácil utilizar imágenes **Docker**, que son fáciles de usar y no necesitan tiempo de *setup*.

Vamos a partir de la imagen de **Tomcat** oficial que podemos encontrar [aquí](https://hub.docker.com/_/tomcat/). Uno de los grandes aciertos de los que mantienen las imágenes es que, por muchos *tags* que generen, todos funcionan bajo los mismos parámetros; esto nos permite hacer pruebas con el *tag* de *Alpine Linux*, y luego -si fuera necesario- saltar a algunos de los *tags* basados en *Debian*.

En los ejemplos también se hace uso de un fichero *.war* de prueba, llamado *sample.war*, que he sacado de [aquí](https://tomcat.apache.org/tomcat-7.0-doc/appdev/sample/), concretamente [este](https://tomcat.apache.org/tomcat-7.0-doc/appdev/sample/sample.war). Lo que hace nuestra aplicación es irrelevante en este momento, y solamente lo vamos a utilizar para probar su disponibilidad.

El concepto que debemos tener claro en una instalación de **Tomcat** es la carpeta en la que está instalado, marcada por la variable de entorno CATALINA_HOME; el resto es relativo a esta carpeta. En esta imagen concreta tenemos:

* **Carpeta base**: CATALINA_HOME &rarr; /usr/local/tomcat
* **Carpeta de aplicaciones**: CATALINA_HOME/webapps &rarr; /usr/local/tomcat/webapps
* **Carpeta de logs**: CATALINA_HOME/logs &rarr; /usr/local/tomcat/logs

## Un despliegue básico

La opción más fácil para exponer nuestras aplicaciones es dejarlas simplemente en la carpeta de aplicaciones y reiniciar el servidor de aplicaciones. No es la opción más correcta desde el punto de vista de la disponibilidad, pero con un uso inteligente de los balanceadores es una opción válida.

La idea de fondo es que **Tomcat** descomprime el fichero *.war* en el momento de levantarse. Solo tenemos que asegurar que el fichero *.war* está en su sitio. Para ir rápido, no voy a generar imágenes nuevas y voy a inyectar el *.war* mediante el uso de volúmenes.

```bash
gerard@atlantis:~/workspace/tomcat$ cat docker-compose.yml
version: '3'
services:
  appserver:
    image: tomcat:alpine
    container_name: appserver
    hostname: appserver
    ports:
      - "8080:8080"
    volumes:
      - ./tomcat/sample.war:/usr/local/tomcat/webapps/sample.war:ro
    restart: always
gerard@atlantis:~/workspace/tomcat$
```

Solo nos queda levantar el servicio, pudiendo encontrar el resultado en [http://localhost:8080/sample/](http://localhost:8080/sample/).

```bash
gerard@atlantis:~/workspace/tomcat$ docker-compose up -d
Creating network "tomcat_default" with the default driver
Creating appserver ... done
gerard@atlantis:~/workspace/tomcat$
```

## Exponiendo el manager

Cuando tenemos una aplicación es natural que hayan evolutivos y se necesite cambiar el fichero. Como **Tomcat** maneja varias aplicaciones, un reinicio las afecta a todas y causa un *downtime* importante, por no mencionar que el tiempo para levantar el servicio se dispara.

Afortunadamente, **Tomcat** nos ofrece una aplicación que tiene como única finalidad, administrar otras aplicaciones. Es el *manager* y lo podemos localizar en [http://localhost:8080/manager/html](http://localhost:8080/manager/html), o siguiendo un botón desde la página inicial en [http://localhost:8080/](http://localhost:8080/).

Este *manager* se puede acceder definiendo un usuario en `conf/tomcat-users.xml`, y por defecto permite entrar a los usuario en la máquina local. Este comportamiento se puede cambiar mediante un fichero de contexto, que pondremos en `conf/Catalina/localhost/<aplicación>.xml`. Veamos como habilitar el *manager* y el *host-manager*, mediante el añadido de los ficheros de configuración usando volúmenes:

```bash
gerard@atlantis:~/workspace/tomcat$ cat docker-compose.yml
version: '3'
services:
  appserver:
    image: tomcat:alpine
    container_name: appserver
    hostname: appserver
    ports:
      - "8080:8080"
    volumes:
      - ./tomcat/tomcat-users.xml:/usr/local/tomcat/conf/tomcat-users.xml:ro
      - ./tomcat/context.xml:/usr/local/tomcat/conf/Catalina/localhost/manager.xml:ro
      - ./tomcat/context.xml:/usr/local/tomcat/conf/Catalina/localhost/host-manager.xml:ro
    restart: always
gerard@atlantis:~/workspace/tomcat$
```

```bash
gerard@atlantis:~/workspace/tomcat$ cat tomcat/tomcat-users.xml
<?xml version="1.0" encoding="UTF-8"?>
<tomcat-users xmlns="http://tomcat.apache.org/xml"
              xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
              xsi:schemaLocation="http://tomcat.apache.org/xml tomcat-users.xsd"
              version="1.0">
  <role rolename="manager-gui"/>
  <role rolename="admin-gui"/>
  <user username="manager" password="manager1234" roles="manager-gui,admin-gui"/>
</tomcat-users>
gerard@atlantis:~/workspace/tomcat$
```

```bash
gerard@atlantis:~/workspace/tomcat$ cat tomcat/context.xml
<Context privileged="true" antiResourceLocking="false"
         docBase="${catalina.home}/webapps/manager">
    <Valve className="org.apache.catalina.valves.RemoteAddrValve" allow="^.*$" />
</Context>
gerard@atlantis:~/workspace/tomcat$
```

**TRUCO**: Como el contenido del fichero `context.xml` vale para habilitar ambas aplicaciones, podemos crear la ilusión dentro del contenedor de que son 2 ficheros, aunque realmente se trata del mismo.

Con esto deberíamos ser capaces de acceder al *manager* y al *host-manager*.

## Añadiendo virtualhosts

Cada aplicación que pongamos en **Tomcat** acaba disponible en `http://dominio:8080/<aplicacion>/`. Esto nos plantea una serie de cuestiones:

* Como montamos una aplicación por (sub)dominio?
* Como nos libramos de la coletilla `/<aplicacion>/`?
* Como añado autenticación básica?
* Como tratamos una terminación SSL?

El servidor de aplicaciones **Tomcat** no se encarga de eso. Si bien es cierto que se puede encargar de la parte de SSL, es una configuración complicada; la parte de los dominios se debería tratar en la aplicación misma, con lo que es trabajo extra y la limpieza de la URL es imposible.

En estos casos, la recomendación es tener un *proxy reverso* delante que cree estas ilusiones de forma fácil y confiable; mi recomendación personal es poner un **nginx**, que resume todo el truco en un fichero de configuración y que podemos inyectar también como un volumen.

```bash
gerard@atlantis:~/workspace/tomcat$ cat docker-compose.yml
version: '3'
services:
  webserver:
    image: sirrtea/nginx:alpine
    container_name: webserver
    hostname: webserver
    ports:
      - "8080:80"
    volumes:
      - ./nginx/sample.conf:/etc/nginx/conf.d/sample.conf:ro
    depends_on:
      - appserver
    restart: always
  appserver:
    image: tomcat:alpine
    container_name: appserver
    hostname: appserver
    volumes:
      - ./tomcat/sample.war:/usr/local/tomcat/webapps/sample.war:ro
    restart: always
gerard@atlantis:~/workspace/tomcat$
```

```bash
gerard@atlantis:~/workspace/tomcat$ cat nginx/sample.conf
server {
        listen 80;
        server_name sample.example.com;
        location / {
                proxy_pass http://appserver:8080/sample/;
        }
}
gerard@atlantis:~/workspace/tomcat$
```

Tras levantar el conjunto de contenedores con *docker-compose*, sucede la magia:

* Solo llegaremos al **Tomcat** mediante el dominio `sample.example.com`, puerto 80
* Todas las peticiones hechas a `/loremipsum` van parar a `appserver:8080/sample/loremipsum`
* El **Nginx** consume la parte de la aplicación `/sample` en la URL
* No hay SSL en este ejemplo, pero ponerlo no entraña ninguna dificultad extra
* No se ha puesto autenticación básica, pero tampoco cuesta demasiado

Con esto podemos ocultar el *manager* y otras aplicaciones, que podríamos exponer mediante otros (sub)dominios, o puertos; eso nos permite hacer un uso inteligente de un *firewall* para evitar la exposición de partes privadas de nuestro proyecto.
