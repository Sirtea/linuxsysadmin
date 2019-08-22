---
title: "Programando tareas con timers en systemd"
slug: "programando-tareas-con-timers-en-systemd"
date: "2019-08-22"
categories: ['Operaciones']
tags: ['linux', 'systemd', 'timer']
---

Una de las funciones que prometía **systemd** cuando apareció era la de reemplazar las utilidades tipo **cron**. Esto era bueno porque iba a estandarizar un servicio que no lo estaba (aunque las diferentes distribuciones lo daban por hecho); esta idea se quedó en el tintero y es hora de sacarla.<!--more-->

Algunas voces indican que es más complejo crear tareas programadas para **systemd** que en **cron**, pero supongo que eso es debido a la familiaridad que todos tenemos con este último. La realidad es que solo necesitamos 3 cosas:

* Un *script* o binario que tengamos que ejecutar
* Una *unit* de **systemd** definiendo el servicio que el *timer* lanzará
* Una *unit* de **systemd** definiendo el *timer* y su periodicidad

Así pues, hoy voy a mostrar como se puede hacer para que **systemd** y sus *timers* ejecuten tareas por nosotros, creando un *script* que se vaya ejecutando cada cierto tiempo. Como añadido, lo vamos a hacer en modo usuario, para no necesitar permisos de *root*.

## Escenario inicial

Disponemos de un *script* que supuestamente va a hacer un *backup* de nuestros ficheros sensibles. Para ser ordenados, vamos a poner este *script* en la carpeta `~/bin/` y vamos a crear una carpeta `~/log/` para alojar el fichero de trazas.

```bash
gerard@eden:~$ tree
.
├── bin
│   └── backup.sh
└── log

2 directories, 1 file
gerard@eden:~$ 
```

Realmente, lo que hace el *script* no nos importa tanto como el hecho de que se ejecuta cuando toque; de momento vamos a hacer que deje en el *log* la fecha y hora en la que ejecutó, solo para poder comprobar que funciona. Asumiremos que no hay nada de lo que hacer *backup*.

```bash
gerard@eden:~$ cat bin/backup.sh 
#!/bin/bash

date +"%FT%T%z" >> /home/gerard/log/backup.log
gerard@eden:~$ 
```

## El servicio systemd

El *timer* se limita a levantar un servicio cada cierto tiempo, de acuerdo con sus directivas de configuración. Por lo tanto necesitamos asegurar que el servicio existe y ejecuta sin problemas.

**WARNING**: Se espera que este servicio acabe y no se quede residente, para evitar solapamientos futuros con otras invocaciones.

Creamos la estructura de carpetas en donde debemos dejar nuestras *units*:

```bash
gerard@eden:~$ mkdir -vp ~/.config/systemd/user
mkdir: se ha creado el directorio '/home/gerard/.config'
mkdir: se ha creado el directorio '/home/gerard/.config/systemd'
mkdir: se ha creado el directorio '/home/gerard/.config/systemd/user'
gerard@eden:~$ 
```

Y creamos una *unit* de tipo servicio. Es importante indicar que es de tipo *oneshot* para que **systemd** vea normal que acabe y no lo reinicie.

```bash
gerard@eden:~$ cat .config/systemd/user/backup.service 
[Unit]
Description=Backup script

[Service]
Type=oneshot
ExecStart=/home/gerard/bin/backup.sh
gerard@eden:~$ 
```

Recargamos los servicios en **systemd** y probamos que nuestro servicio funciona bien cuando se hace el respectivo `start`.

```bash
gerard@eden:~$ systemctl --user daemon-reload
gerard@eden:~$ 
```

```bash
gerard@eden:~$ systemctl --user start backup.service
gerard@eden:~$ 
```

**TRUCO**: El servicio **no se debe activar** (no hay que hacer el `systemctl enable`); esto es porque no se debe levantar solo, sino a petición del *timer*.

Podemos ver que se ha creado el fichero de *log* y, si lo revisamos, veremos que la hora actual en el *log*.

```bash
gerard@eden:~$ tree
.
├── bin
│   └── backup.sh
└── log
    └── backup.log

2 directories, 2 files
gerard@eden:~$ 
```

## El timer systemd

Nuevamente necesitaremos especificar un fichero tipo *unit* de **systemd**, pero esta vez necesitamos que tenga la extensión `.timer`. Para información sobre su sintaxis, podemos consultar la documentación:

* <https://www.freedesktop.org/software/systemd/man/systemd.timer.html>
* <https://www.freedesktop.org/software/systemd/man/systemd.time.html>

El *timer* puede funcionar de dos modos distintos: por intervalos de tiempo (por ejemplo, cada 30 minutos) y por momentos concretos (por ejemplo, cada lunes a las 08:00).

**TRUCO**: En todo momento podemos ver los *timers* activos con el comando `systemctl --user list-timers`. Esto nos dará una idea de cuando se ejecutó por última vez, cuando será la próxima vez y cuánto falta para una nueva ejecución.

```bash
gerard@eden:~$ systemctl --user list-timers
NEXT                          LEFT     LAST                          PASSED  UNIT         ACTIVATES
Fri 2019-07-05 00:00:05 CEST  10h left Thu 2019-07-04 13:20:00 CEST  58s ago backup.timer backup.service

1 timers listed.
Pass --all to see loaded but inactive timers, too.
gerard@eden:~$ 
```

### Ejecuciones por intervalos de tiempo

Si quisiéramos ejecutar nuestro *script* cada 10 segundos podríamos indicarlo mediante la directiva `OnUnitActiveSec`. Esto indicará que se ejecute si la *unit* está activada, y que lo haga cada tantos segundos como indiquemos en la directiva.

**TRUCO**: La directiva, igual que todas las temporales, asume que se trata de segundos, pero acepta otras formas, de acuerdo a la documentación. Por ejemplo podríamos poner algo como `1d5h10s`.

```bash
gerard@eden:~$ cat .config/systemd/user/backup.timer 
[Unit]
Description=Ejecutar backup cada 10 segundos

[Timer]
OnBootSec=60
OnUnitActiveSec=10
AccuracySec=1us
Unit=backup.service

[Install]
WantedBy=timers.target
gerard@eden:~$ 
```

Hay otras directivas, que hacen lo siguiente:

* `OnBootSec=60` &rarr; Evita que el *timer* ejecute hasta pasados 60 segundos desde el *boot* de la máquina. Esto es una decisión personal.
* `AccuracySec=1us` &rarr; La invocación de **systemd** puede retardarse tanto tiempo como indique este valor (por defecto 1 minuto), en favor de la economía de CPU. He bajado esto al máximo porque un minuto de precisión es poco si queremos 10 segundos...
* `Unit=backup.service` &rarr; Este es el servicio del que se va a hacer el `systemctl start`. Lo he puesto pero no es necesario; su valor por defecto es el mismo nombre del *timer* pero con extensión `.service`.

Escrita la *unit* pertinente, recargamos la configuración de **systemd**, activamos el timer para que se levante en cada sesión de usuario, y lo levantamos para la sesión actual.

```bash
gerard@eden:~$ systemctl --user daemon-reload
gerard@eden:~$ 
```

```bash
gerard@eden:~$ systemctl --user enable backup.timer
Created symlink /home/gerard/.config/systemd/user/timers.target.wants/backup.timer → /home/gerard/.config/systemd/user/backup.timer.
gerard@eden:~$ 
```

```bash
gerard@eden:~$ systemctl --user start backup.timer
gerard@eden:~$ 
```

Podemos ver el fichero de *logs* para comprobar como se va llenando cada 10 segundos.

### Ejecuciones por momentos concretos

Nadie hace un *backup* cada cierto tiempo; es mucho más habitual hacerlo a horas concretas. Por ello vamos a parar y deshabilitar el *timer* anterior y vamos a enfocar otra manera de lanzarlo.

En vez de utilizar la directiva `OnUnitActiveSec`, se puede indicar una especificación temporal con la directiva `OnCalendar`. La documentación indica el formato que se acepta; como queremos hacer un *backup* diario, vamos a poner `daily`, lo que equivale a `*-*-* 00:00:00` (medianoche).

```bash
gerard@eden:~$ cat .config/systemd/user/backup.timer 
[Unit]
Description=Ejecutar backup diario

[Timer]
Persistent=true
OnCalendar=daily
RandomizedDelaySec=10m

[Install]
WantedBy=timers.target
gerard@eden:~$ 
```

Otras decisiones de diseño, son:

* `Persistent=true` &rarr; Esto hace que **systemd** guarde el último *timestamp* de ejecución, y pueda saber si se ha saltado alguna ejecución, por ejemplo si la máquina estaba parada; en este caso la relanzaría inmediatamente.
* `RandomizedDelaySec=10m` &rarr; Para no ejecutar todas las tareas `daily` a la vez (y saturar el sistema), podemos indicar un tiempo aleatorio de retraso, siendo el máximo lo indicado, 10 minutos.

Siguiendo los pasos anteriores, recargamos la nueva *unit* en **systemd**, la activamos para que se levante en cada sesión nueva, y la levantamos para la sesión en curso.

```bash
gerard@eden:~$ systemctl --user daemon-reload
gerard@eden:~$ 
```

```bash
gerard@eden:~$ systemctl --user enable backup.timer
Created symlink /home/gerard/.config/systemd/user/timers.target.wants/backup.timer → /home/gerard/.config/systemd/user/backup.timer.
gerard@eden:~$ 
```

```bash
gerard@eden:~$ systemctl --user start backup.timer
gerard@eden:~$ 
```

Y solo faltaría esperar a medianoche para ver que se ha lanzado el *script*. Por supuesto, a fin de probar este artículo, cambié la especificación `daily` a `hourly`; así que esto funciona seguro.
