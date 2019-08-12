---
title: "Utilizando systemd a nivel de usuario"
slug: "utilizando-systemd-a-nivel-de-usuario"
date: "2019-08-12"
categories: ['Operaciones']
tags: ['linux', 'systemd']
---

Es bastante habitual que en mi tiempo de ocio me dedique a trabajar con HTML y CSS por interés personal. A veces puedo hacer pruebas de concepto estáticas y otras puedo utilizar un generador estático; en todos los casos necesito de un servidor web levantado solo para mi sesión personal.<!--more-->

Es fácil abrir una pestaña en tu emulador de terminal y ejecutar uno de esos servidores estáticos hechos en **go**, pero me gustaría que se levantaran solos por comodidad, y por lo tanto, debo delegar la tarea a **systemd**, que me ofrece exactamente eso: servicios que se ejecutan durante la sesión de un usuario y acaban tan pronto como este la cierra.

El punto interesante de utilizar **systemd** a nivel de usuario es que se puede configurar todo en la carpeta personal de un usuario sin permisos especiales, siempre respetando las otras restricciones que ello supone (no acceso a carpetas de sistema, límite de rango de puertos, etc). Lo más alucinante es que no se necesita ser un gran experto para hacerlo y cada usuario puede encargarse de ello...

**TRUCO**: Otros usos posibles para "servicios de usuario" podrían ser levantar bases de datos, túneles SSH o contenedores **docker**; las posibilidades son infinitas.

## Un servidor web de ejemplo

El servidor web que vamos a utilizar en este ejemplo es [Ran][1]. Como buen servicio escrito en **go** es un binario estático que puedo dejar "tirado por ahí". Como ejecuto con un usuario normal, tengo la limitación de no poder abrir puertos por debajo de 1024, así que lo suelo levantar en el puerto de HTTP alternativo (es el puerto TCP 8080).

Ponemos el binario en la carpeta `~/bin/` y creamos una carpeta con nuestro contenido web, por ejemplo, en `~/www/`. Para la demostración nos basta un fichero `index.html` y una página de error `404.html`.

```bash
gerard@eden:~$ tree
.
├── bin
│   └── ran
└── www
    ├── 404.html
    └── index.html

2 directories, 3 files
gerard@eden:~$ 
```

Considerando la estructura de carpetas de mi carpeta personal, el comando a ejecutar es trivial:

```bash
gerard@eden:~$ ran -r www/ -404=/404.html
2019-07-04 10:58:52.983882 INFO: System: Ran is running on HTTP port 8080
...
```

Vamos a delegar este servicio a **systemd**, para liberar el terminal, simplificar el comando para levantar el servicio (pensad en un servicio de muchos parámetros) y posiblemente activar el inicio automático.

Para ello necesitamos una *unit* de **systemd**, como ya explicamos en [otro artículo][2]. La novedad es que se va a alojar en la carpeta personal de usuario, concretamente en `~/.config/systemd/user/`; la otra novedad es que se va a manejar con el *flag* `--user`.

```bash
gerard@eden:~$ mkdir -vp ~/.config/systemd/user
mkdir: se ha creado el directorio '/home/gerard/.config'
mkdir: se ha creado el directorio '/home/gerard/.config/systemd'
mkdir: se ha creado el directorio '/home/gerard/.config/systemd/user'
gerard@eden:~$ 
```

```bash
gerard@eden:~$ cat .config/systemd/user/ran.service 
[Unit]
Description=Ran: a simple static web server written in Go

[Service]
ExecStart=/home/gerard/bin/ran -r /home/gerard/www/ -404=/404.html

[Install]
WantedBy=default.target
gerard@eden:~$ 
```

Ahora ya podemos comprobar que **systemd** "conoce" nuestro nuevo servicio y podemos cargarlo:

```bash
gerard@eden:~$ systemctl --user list-unit-files
UNIT FILE                    STATE   
...
ran.service                  disabled
...
gerard@eden:~$ 
```

```bash
gerard@eden:~$ systemctl --user daemon-reload
gerard@eden:~$ 
```

El servicio se levanta y se para con **systemd**, con el *flag* `--user`, y podemos ver que está levantado con un simple `ps` o accediendo en el navegador a `http://localhost:8080/`.

```bash
gerard@eden:~$ systemctl --user start ran
gerard@eden:~$ 
```

Y si quisiéramos su estado o pararlo:

```bash
gerard@eden:~$ systemctl --user status ran
● ran.service - Ran: a simple static web server written in Go
   Loaded: loaded (/home/gerard/.config/systemd/user/ran.service; disabled; vendor preset: enabled)
   Active: active (running) since Thu 2019-07-04 11:18:58 CEST; 1min 39s ago
 Main PID: 545 (ran)
   CGroup: /user.slice/user-1000.slice/user@1000.service/ran.service
           └─545 /home/gerard/bin/ran -r /home/gerard/www/ -404=/404.html
gerard@eden:~$ 
```

```bash
gerard@eden:~$ systemctl --user stop ran
gerard@eden:~$ 
```

Para que el servicio se levante automáticamente cuando hagamos *login* en el sistema, basta con activarlo; lo contrario se haría desactivándolo:

```bash
gerard@eden:~$ systemctl --user enable ran
Created symlink /home/gerard/.config/systemd/user/default.target.wants/ran.service → /home/gerard/.config/systemd/user/ran.service.
gerard@eden:~$ 
```

```bash
gerard@eden:~$ systemctl --user disable ran
Removed /home/gerard/.config/systemd/user/default.target.wants/ran.service.
gerard@eden:~$ 
```

**WARNING**: La sesión **systemd** de usuario se acaba cuando este cierra la sesión. Todos los servicios de usuario que estuvieran ejecutándose se paran en ese momento.

[1]: https://github.com/m3ng9i/ran
[2]: {{< relref "/articles/2015/11/escribiendo-units-en-systemd.md" >}}
