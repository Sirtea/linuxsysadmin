Title: Sincronizando ficheros con ownCloud
Slug: sincronizando-ficheros-con-owncloud
Date: 2017-02-20 10:00
Category: Miscelánea
Tags: owncloud, docker, docker-compose



Finalmente ha sucedido: el ingeniero de seguridad de la empresa ha decidido cerrar servicios de sincronizado de ficheros, dejando inútiles servicios como **Dropbox**, **Mega** y otros. Sin embargo, cualquier bloqueo que se haga mediante el dominio hace que sea imposible cerrar todos estos servicios, e incluso podemos poner el nuestro.

La forma mas simple de tener un servicio privado es utilizar algo que ya esté hecho, y en esta categoría tenemos un contendiente ganador: [ownCloud](https://owncloud.org/). Solo sería necesario alojarlo en algún lugar desde donde todos nuestros dispositivos tengan acceso.

Vamos a tirar de **Docker** y de **DockerHub**, concretamente de la imagen oficial, que podemos encontrar [aquí](https://hub.docker.com/_/owncloud/). Como necesitamos una base de datos, vamos a utilizar **docker-compose** para levantar fácilmente ambas, usando también la imagen oficial de **MariaDB**.

Así nos queda el *docker-compose.yml*:

```bash
gerard@sirius:~/docker/owncloud$ cat docker-compose.yml 
version: '2'

services:
  owncloud:
    image: owncloud
    container_name: owncloud
    hostname: owncloud
    ports:
      - "80:80"
  mysql:
    image: mariadb
    container_name: mysql
    hostname: mysql
    environment:
      MYSQL_ROOT_PASSWORD: root1234
gerard@sirius:~/docker/owncloud$ 
```

Levantamos el servicio con los comandos habituales:

```bash
gerard@sirius:~/docker/owncloud$ docker-compose up -d
Creating network "owncloud_default" with the default driver
Creating owncloud
Creating mysql
gerard@sirius:~/docker/owncloud$ 
```

Y solamente nos queda acceder al puerto expuesto, desde un navegador cualquiera, usando la URL que corresponda. En mi caso, accedo desde la máquina local, que es donde he levantado ambos contenedores; simplemente usamos <http://localhost/>.

![Owncloud setup]({filename}/images/owncloud_setup.jpg)

Vemos que la primera vez que accedemos nos pide configurar algunas cosas. Rellenamos los campos con los valores mas apropiados, con un usuario de administrador y su contraseña, y los datos de conexión de la base de datos, con cuidado de elegir **mysql**. Usad los valores del *docker-compose.yml*.

* **Database user**: root
* **Database password**: root1234
* **Database name**: owncloud (cualquiera valdría)
* **Database host**: mysql (el *container_name*)

Si le damos a "Finalizar", no hay mas pasos a seguir; finalmente ya lo tenemos funcional.

![Owncloud setup]({filename}/images/owncloud_panel.jpg)

Ahora podemos descargarnos cualquier cliente para sincronizar nuestros datos desde cualquier dispositivo, sea para escritorio, *android* o *iphone*. Solamente necesitamos la precaución de crear usuarios para garantizar la privacidad entre todos ellos.
