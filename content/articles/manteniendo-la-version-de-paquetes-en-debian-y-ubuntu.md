Title: Manteniendo la versión de paquetes en Debian y Ubuntu
Slug: manteniendo-la-version-de-paquetes-en-debian-y-ubuntu
Date: 2017-12-26 10:00
Category: Operaciones
Tags: debian, ubuntu, apt, apt-mark, pinning



Una de las operaciones más rutinarias que podemos tener como administradores de sistemas Linux es la actualización de un servidor. Mecánicamente lanzas **apt-get upgrade** y te quedas tan tranquilo con la tarea completa. Poco después te encuentras con alguien cabreado porque alguna librería o servicio no va adecuadamente como antes.

Lo que realmente ha pasado es que hemos cambiado de versión alguna pieza de *software*, y la nueva tiene incompatibilidades con lo que hay funcionando. Es un caso raro, pero a veces se da, y muchas veces con previo aviso.

¿Como se puede evitar que un servicio cambie de versión cuando actualiza? Muy sencillo: se llama *pinning* y es muy fácil de hacer con **Debian** o **Ubuntu**. Veamos un ejemplo:

Supongamos que tenemos un servidor de contenedores **Docker**. Por un tema de estabilidad queremos mantener la versión actual. Para ello necesitamos saber el nombre del paquete que queramos congelar.

```bash
gerard@atlantis:~$ dpkg -l | grep docker
ii  docker-ce                     17.09.0~ce-0~debian            amd64        Docker: the open-source application container engine
gerard@atlantis:~$
```

En nuestro caso, el paquete es **docker-ce**. Solo hace falta utilizar el comando **apt-mark** para que lo mantenga en la version actual.

```bash
gerard@atlantis:~$ sudo apt-mark hold docker-ce
docker-ce fijado como retenido.
gerard@atlantis:~$
```

A partir de ahora, este paquete **no se va a actualizar**. Si queremos ver que paquetes tenemos congelados, el mismo comando ofrece la operación *showhold* que nos listaría los paquetes en modo *pinning*:

```bash
gerard@atlantis:~$ sudo apt-mark showhold
docker-ce
gerard@atlantis:~$
```

Si en algún momento quisieramos volver a actualizarlo, bastaría con quitarle el *hold*, con el mismo comando:

```bash
gerard@atlantis:~$ sudo apt-mark unhold docker-ce
Se ha cancelado la retención de docker-ce.
gerard@atlantis:~$
```

Y ahora ya podríamos modificar la versión de **docker-ce**. Necesitaríamos los comandos habituales **apt-get**, **aptitude** u otro frontal gráfico. Podéis verificar que vuestro paquete ya no está en modo *hold* listando los paquetes en dicho estado.

```bash
gerard@atlantis:~$ sudo apt-mark showhold
gerard@atlantis:~$
```

Y con esto nos evitamos esos molestos cambios de versión que nos traen incompatibilidades con las aplicaciones que mantenemos.
