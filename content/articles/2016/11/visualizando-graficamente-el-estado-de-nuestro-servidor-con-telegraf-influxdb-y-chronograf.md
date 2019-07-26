---
title: "Visualizando gráficamente el estado de nuestro servidor con Telegraf, InfluxDB y Chronograf"
slug: "visualizando-graficamente-el-estado-de-nuestro-servidor-con-telegraf-influxdb-y-chronograf"
date: 2016-11-07
categories: ['Operaciones']
tags: ['chronograf', 'telegraf', 'influxdb', 'docker']
---

No hay nada mas visualmente atractivo que ver nuestros servidores en tiempo real mediante gráficos temporales, y existen algunas buenas herramientas ya hechas. Necesitaremos un agente que recolecte los datos del servidor y los envíe a una base de datos temporales, para que se pueden dibujar en una página web.<!--more-->

Estamos hablando del combo **Telegraf**, **InfluxDB** y **Chronograf**, que para ponernos la vida mas fácil, se pueden levantar como contenedores **Docker**.

## Servicios necesarios

### La base de datos temporal

Una base de datos temporal especialmente diseñada para este trabajo se llama **InfluxDB**. Solo neceitamos levantar un contenedor en el almacenar nuestras series de datos. Para ello, no tenemos mas que levantar nuestro contenedor, de entre la imágenes oficiales.

```bash
gerard@sodium:~/docker$ docker run -d influxdb
9ee87def20cda02c273acb6ae4dbd15a2473a1d93821533ea92e375a0ef54313
gerard@sodium:~/docker$ 
```

### El recolector de datos

El proceso encargado de recoger los datos de un servidor es **Telegraf**. En principio, necesitamos uno en cada servidor que queramos monitorizar. Para no alargar en el artículo, lo vamos a levantar en la misma máquina.

Hay que empezar generando una configuración, que vamos a cambiar para ajustar a nuestras necesidades. Esta configuración se encarga de decidir que muestras se van a tomar de nuestro servidor, y sirve también para indicar la localización de la base de datos en donde las va a guardar.

```bash
gerard@sodium:~/docker$ docker run --rm telegraf -sample-config > telegraf.conf
gerard@sodium:~/docker$ 
```

En este caso, vamos a cambiar solamente la dirección de la base de datos:

```bash
gerard@sodium:~/docker$ cat telegraf.conf 
...
[[outputs.influxdb]]
...
  urls = ["http://172.17.0.2:8086"] # required
...
gerard@sodium:~/docker$ 
```

Ahora hay que levantar el agente con la nueva configuración. Podemos hacerlo con una imagen modificada, o si eso no nos gusta, podemos utilizar un contenedor a la máquina local. Haremos esto último.

```bash
gerard@sodium:~/docker$ docker run -v $PWD/telegraf.conf:/etc/telegraf/telegraf.conf:ro -d telegraf
e5cbaed75570d22c709c940a7d5ccf4a633fc2453df37e05dfa094ae4913572a
gerard@sodium:~/docker$ 
```

### El panel web

Hay muchas herramientas para visualizar datos, pero nos vamos a limitar a la herramienta de la misma *suite*, que es **Chronograf**. Para eso tenemos que levantar su contenedor. Es especialmente importante exponer el puerto, para poder ver la web desde fuera del contenedor.

```bash
gerard@sodium:~/docker$ docker run -p 10000:10000 -d chronograf
b3fb6777bac2ad5c061ff5ea6603305c0c43d6103c552a47fafb1414a7434c34
gerard@sodium:~/docker$ 
```

Solo nos faltaría abrir un navegador a la URL configurada, que en mi caso es <http://localhost:10000/>. Es un buen momento para configurar nuestra base de datos. Aunque se pueden usar varias, no lo haremos por hoy.

Le damos al botón "Add new server" y le indicamos los valores de acceso al servidor **InfluxDB**. En mi caso, solo he tenido que tocar la dirección IP, que al tratarse del primer contenedor levantado, es la 172.17.0.2; mirad la salida de un *docker inspect* en caso de dudas.

## Configurando visualizaciones y dashboards

Una visualización es un gráfico basado en una serie de valores de una serie. Un *dashboard* es un conjunto de visualizaciones puestas en la misma pantalla, para su fácil observación.

Podemos crear visualizaciones mediante el botón "Add Visualization" desde la sección "Visualizations" o desde un *dashboard*. La configuración es trivial; basta con darle un nombre al gráfico y seleccionar base de datos, medidas y el valor o valores de la medida que queremos ver.

Por ejemplo, podemos crear el gráfico "Memory". Seleccionamos la base de datos *telegraf*, la serie *mem* en "Filter by" y el campo *used_percent* en "Extract by". La consulta resultante a **InfluxDB** quedaría así:

> SELECT used_percent FROM telegraf..mem WHERE tmpltime()

Insuficiente con este valor, creamos un *dashboard* llamado "Server". Le añadimos la visualización ya existente llamada "Memory" y porque no, creamos una visualización nueva "CPU" con dos valores en el campo "Extract by". Así de fácil.

![Chronograf dashboard](/images/chronograf.jpg)

Y con eso acabamos. Solo falta poner esto en un sitio visible y sacar nuestras conclusiones.
