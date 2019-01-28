Title: Acumulando los logs en un servidor centralizado con Kibana
Slug: acumulando-los-logs-en-un-servidor-centralizado-con-kibana
Date: 2017-01-16 10:00
Category: Operaciones
Tags: ELK, elastic search, logstash, kibana, logs



Buscar en los *logs* es fácil cuando tenemos una máquina de cada tipo, pero es una actividad muy poco gratificante cuando tenemos un número grande o variable de cada tipo. La mejor manera de tenerlos controlados es hacer que envíen sus *logs* a un almacén central, para su fácil consulta.

En este artículo se pretende dar a conocer una de estas soluciones de acumulación y búsqueda de *logs*, conocida como **ELK** (hace poco se renombró a **Elastic Stack**). Se trata de un conjunto de servicios que cooperan para obtener una solución completa:

* **Elastic search**: se trata de la base de datos que almacena todos los *logs* que se le envían.
* **Logstash**: Es un agente que envía los *logs* de varias fuentes al **elastic search**.
* **Kibana**: Es una interfaz gráfica que nos permite buscar *logs* y dibujar bonitas gráficas, partiendo de los datos del **elastic search**.

![Esquema de un ELK]({static}/images/the-elk-stack.jpg)

De esto se puede deducir que vamos a necesitar una instancia de cada tipo, a excepción de **logstash**, que debe ponerse en todos los servidores que recojan *logs*. Se podría poner, por ejemplo, el **elastic search** y el **kibana** en una misma máquina, dedicada solamente al consumo de los *logs* de todos los servidores productivos.

## Un ejemplo rápido

Si miramos en [DockerHub](https://hub.docker.com/), podremos comprobar que las 3 piezas disponen de una imagen que las satisface. Eso nos va a ahorrar mucho tiempo, a costa de las particularidades de cada imagen.

Vamos a poner todas las imágenes en el mismo servidor por economía, pero lo ideal sería un **logstash** por servidor y otro servidor con **elastic search** y **kibana**.

El primer paso es acondicionar la memoria que pueden usar nuestros procesos. Esto se hace porque el **elastic search** consume mucha memoria y va a fallar iniciándose.

```bash
gerard@styx:~/docker/elk$ sudo sysctl -w vm.max_map_count=262144
vm.max_map_count = 262144
gerard@styx:~/docker/elk$ 
```

La mayoría de imágenes funcionan bien de serie, pero no es el caso de **logstash**, que necesita una configuraciṕon para indicar qué *logs* recoger, las transformaciones que deben sufrir, y el destino al que ir. Más información en [la documentación](https://www.elastic.co/guide/en/logstash/current/index.html). De momento nos vamos a limitar a recoger todos los ficheros *.log* recursivamente de la carpeta */logs*; esta va a ser un volumen de */var/log* del servidor real.

```bash
gerard@styx:~/docker/elk$ cat logstash.conf 
input {
  file {
    path => "/logs/**/*.log"
    start_position => "beginning"
  }
}

output {
  elasticsearch {
    hosts => ["elasticsearch:9200"]
  }
}
gerard@styx:~/docker/elk$ 
```

Para simplificar el despliegue, vamos a usar **docker-compose**, con algunas variaciones interesantes.

```bash
gerard@styx:~/docker/elk$ cat docker-compose.yml 
version: '2'
services:
  elasticsearch:
    image: elasticsearch
    container_name: elasticsearch
    hostname: elasticsearch
  kibana:
    image: kibana
    container_name: kibana
    hostname: kibana
    ports:
      - "5601:5601"
  logstash:
    image: logstash
    container_name: logstash
    hostname: logstash
    volumes:
      - ./logstash.conf:/logstash.conf:ro
      - /var/log:/logs:ro
    user: root
    command: [bash, -c, "logstash -f /logstash.conf"]
gerard@styx:~/docker/elk$ 
```

Se hace notar especialmente que publicamos el puerto del **kibana**, para poderlo ver cómodamente en nuestro navegador. Aparte de esto, vamos a poner el fichero de configuración de **logstash** como un volumen local, tal como la carpeta de *logs*. Un último detalle es que modificamos el comando a ejecutar para que el *entrypoint* que viene por defecto no nos fuerce el usuario *logstash*, puesto que entonces no podríamos leer muchos de los *logs*.

```bash
gerard@styx:~/docker/elk$ docker-compose up -d
Creating network "elk_default" with the default driver
Creating elasticsearch
Creating logstash
Creating kibana
gerard@styx:~/docker/elk$ 
```

Solo nos falta acceder a la interfaz del **Kibana** en <http://localhost:5601/> y disfrutar del resultado.

![Frontend de Kibana]({static}/images/kibana-frontend.jpg)
