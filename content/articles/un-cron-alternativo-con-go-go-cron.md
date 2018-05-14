Title: Un cron alternativo con go: go-cron
Slug: un-cron-alternativo-con-go-go-cron
Date: 2018-05-21 10:00
Category: Operaciones
Tags: cron, go, go-cron



Quiero presentar una de esas herramientas que ya existen, pero que alguien ha reescrito con el lenguaje **go**. Se trata de una utilidad tipo *cron*, pero está compilada de forma estática, no necesita de otras librerías y, por lo tanto, lo podemos usar en donde no tengamos permisos de *root*.

## Instalación de go-cron

El binario **go-cron** no depende de librerías externas, tratándose de un binario estático que podemos tener, por ejemplo, en nuestra carpeta personal.

Su instalación se limita a descargarse el binario de [GitHub](https://github.com/odise/go-cron/releases) y usar; el fichero descargado es un binario precompilado y comprimido.

```bash
gerard@sirius:~/workspace$ wget -O go-cron.gz https://github.com/odise/go-cron/releases/download/v0.0.7/go-cron-linux.gz
...  
Petición HTTP enviada, esperando respuesta... 200 OK
Longitud: 1755640 (1,7M) [application/octet-stream]
Grabando a: “go-cron.gz”

go-cron.gz               100%[====================================>]   1,67M  1,49MB/s   en 1,1s   

2018-04-25 11:13:41 (1,49 MB/s) - “go-cron.gz” guardado [1755640/1755640]

gerard@sirius:~/workspace$ gunzip go-cron.gz 
gerard@sirius:~/workspace$ chmod 755 go-cron 
gerard@sirius:~/workspace$ strip go-cron 
gerard@sirius:~/workspace$ 
```

**TRUCO**: El binario viene con los símbolos de *debug*; si ejecutamos el comando *strip*, lo podemos bajar de 6mb a 4.3mb.

## Uso de go-cron

Empezamos con una visión general de lo que podemos hacer con el binario, que no es mucho:

```bash
gerard@sirius:~/workspace$ ./go-cron -h
Usage of ./go-cron (build 6f160c2 )
./go-cron  [ OPTIONS ] -- [ COMMAND ]
  -h=false: display usage
  -p="18080": bind healthcheck to a specific port, set to 0 to not open HTTP port at all
  -s="* * * * *": schedule the task the cron style
gerard@sirius:~/workspace$ 
```

**AVISO**: A diferencia de otras herramienta tipo *cron*, esta se encarga de gestionar **una sola tarea**. Junto con el hecho de que el proceso ejecuta en primer plano, lo hace ideal para su uso en contenedores **docker**.

La parte más importante es que demos la especificación temporal (*flag* `-s`) y el comando a ejecutar. Podemos encontrar documentación para la especificación temporal [aquí](https://godoc.org/github.com/robfig/cron). Esta puede ser de 3 tipos: tipo *cron*, tiempos preconfigurados y por intervalos.

### Especificación tipo cron

Se trata de dar 5 o 6 valores, que indican respectivamente el segundo, el minuto, la hora, el día del mes, el mes, y -opcionalmente- el día de la semana.

Estos valores pueden tener intervalos, comodines e incrementos, justo como en el *cron* normal. Por ejemplo, para lanzar un comando en el segundo 0, cada 30 minutos, entre las 10 y las 20 horas, los días 1 y 15 del mes de todos los meses, usaríamos algo como esto:

```bash
gerard@sirius:~/workspace$ ./go-cron -s "0 */30 10-20 1,15 *" -- echo "hola"
2018/04/25 12:19:32 Running version: 6f160c2
2018/04/25 12:19:32 new cron: 0 */30 10-20 1,15 *
2018/04/25 12:19:32 Opening port 18080 for health checking
```

### Valores preconfigurados

Alternativamente, **go-cron** nos ofrece unos valores preconfigurados que simplifican la expresión, a costa de perder especificaciones más caprichosas. A saber:

* `@yearly` o `@annually` &rarr; Ejecuta cada año, concretamente el 1 de enero (equivale a `0 0 0 1 1 *`)
* `@monthly` &rarr; Ejecuta una vez al mes, en el día 1 (equivale a `0 0 0 1 * *`)
* `@weekly` &rarr; Ejecuta cada semana, a medianoche del domingo (equivale a `0 0 0 * * 0`)
* `@daily` o `@midnight` &rarr; Ejecuta una vez al día, a medianoche (equivale a `0 0 0 * * *`
* `@hourly` &rarr; Ejecuta cada hora, a su principio (equivale a `0 0 * * * *`)

Así pues, para ejecutar un *backup* diario, podríamos hacer algo como lo siguiente:

```bash
gerard@sirius:~/workspace$ ./go-cron -s "@daily" -- ./backup_database.sh
2018/04/25 12:27:45 Running version: 6f160c2
2018/04/25 12:27:45 new cron: @daily
2018/04/25 12:27:45 Opening port 18080 for health checking
```

### Especificación por intervalos

También podemos instruir a **go-cron** para que ejecute cada cierto tiempo, con el *keyword* `@every`. Esto nos dejaría una línea de comandos como esta:

```bash
gerard@sirius:~/workspace$ ./go-cron -s "@every 1m30s" -- ./send_keepalive.sh
2018/04/25 12:30:25 Running version: 6f160c2
2018/04/25 12:30:25 new cron: @every 1m30s
2018/04/25 12:30:25 Opening port 18080 for health checking
```

**AVISO**: La primera ejecución se hace cuando ha pasado el tiempo especificado tras levantar **go-cron**. Las siguientes lo hacen sin tener en cuenta el tiempo de ejecución del comando dado. En caso de ejecutar cada hora, y tardar el *script* 40 minutos, saltaría en siguiente en unos 20 minutos; en casos extremos, podríamos tener solapamiento de ejecuciones.

### El servicio de healthcheck

El *flag* `-p` sirve para indicar el puerto en el que vamos a contar con un *webservice* con información de lo que pasa en **go-cron**.

```bash
gerard@sirius:~/workspace$ ./go-cron -s "@every 10s" -- ./do_something.sh 
2018/04/25 12:38:32 Running version: 6f160c2
2018/04/25 12:38:32 new cron: @every 10s
2018/04/25 12:38:32 Opening port 18080 for health checking
```

```bash
gerard@sirius:~/workspace$ curl http://localhost:18080/
{
  "Running": {
    "9107": {
      "Exit_status": 0,
      "Stdout": "",
      "Stderr": "",
      "ExitTime": "",
      "Pid": 9107,
      "StartingTime": "2018-04-25T12:39:02+02:00"
    }
  },
  "Last": {
    "Exit_status": 0,
    "Stdout": "hello\n",
    "Stderr": "",
    "ExitTime": "2018-04-25T12:38:57+02:00",
    "Pid": 9096,
    "StartingTime": "2018-04-25T12:38:52+02:00"
  },
  "Schedule": "@every 10s"
}
gerard@sirius:~/workspace$ 
```

Se puede desactivar indicando puerto 0, pero igual le podéis encontrar una utilidad...
