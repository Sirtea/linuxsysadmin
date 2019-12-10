---
title: "Protegiendo sistemas Linux con una autenticación de dos factores"
slug: "protegiendo-sistemas-linux-con-una-autenticacion-de-dos-factores"
date: 2019-01-22
categories: ['Seguridad']
tags: ['pam', 'two-factor', 'google', 'ssh']
---

El otro día tuve un auditor de seguridad imponiendo sus criterios arbitrarios; quería que cierto servidor seguro no fuera accesible si no era con una autenticación de 2 factores. Aunque personalmente no lo veo útil, me tocó ceder a sus exigencias y aquí he anotado como lo hice: con **libpam-google-authenticator**.<!--more-->

El reto no es para nada complejo; un sistema Linux moderno utiliza para autenticarse un sistema llamado **PAM** (*Pluggable Authentication Modules*) y solo es necesario añadir un módulo que haga el tipo de autenticación que más nos convenga.

Para una autenticación de 2 factores, **Google** nos lo pone fácil, usando una aplicación móvil generadora de *tokens* que su módulo **libpam-google-authenticator** acepta o no, dependiendo de las configuraciones reinantes.

Así sin más preámbulos, procedemos a instalar dicho paquete (esto se hizo en un sistema **Debian Stretch**, pero debería valer para cualquier **Debian**, **Ubuntu** o derivado):

```bash
gerard@secure:~$ sudo apt install libpam-google-authenticator
Leyendo lista de paquetes... Hecho
Creando árbol de dependencias
Leyendo la información de estado... Hecho
Se instalarán los siguientes paquetes adicionales:
  libqrencode3
Se instalarán los siguientes paquetes NUEVOS:
  libpam-google-authenticator libqrencode3
0 actualizados, 2 nuevos se instalarán, 0 para eliminar y 0 no actualizados.
Se necesita descargar 65,9 kB de archivos.
Se utilizarán 197 kB de espacio de disco adicional después de esta operación.
¿Desea continuar? [S/n] s
Des:1 http://ftp.es.debian.org/debian stretch/main amd64 libqrencode3 amd64 3.4.4-1+b2 [34,3 kB]
Des:2 http://ftp.es.debian.org/debian stretch/main amd64 libpam-google-authenticator amd64 20160607-2+b1 [31,6 kB]
Descargados 65,9 kB en 0s (254 kB/s)
Seleccionando el paquete libqrencode3:amd64 previamente no seleccionado.
(Leyendo la base de datos ... 21701 ficheros o directorios instalados actualmente.)
Preparando para desempaquetar .../libqrencode3_3.4.4-1+b2_amd64.deb ...
Desempaquetando libqrencode3:amd64 (3.4.4-1+b2) ...
Seleccionando el paquete libpam-google-authenticator previamente no seleccionado.
Preparando para desempaquetar .../libpam-google-authenticator_20160607-2+b1_amd64.deb ...
Desempaquetando libpam-google-authenticator (20160607-2+b1) ...
Configurando libqrencode3:amd64 (3.4.4-1+b2) ...
Procesando disparadores para libc-bin (2.24-11+deb9u3) ...
Configurando libpam-google-authenticator (20160607-2+b1) ...
gerard@secure:~$
```

## Configurando el servidor

Como ya he dicho antes, **PAM** es *pluggable*; esto significa que poco hay que hacer. Se "enchufa" a la cadena de autenticación, añadiendo una directiva nueva en el fichero relevante de la configuración de **PAM**.

Como nos interesa proteger todo aquello que requiera de autenticación, me ha parecido natural ponerlo en `/etc/pam.d/common-auth`, que es la configuración que todo el resto de subsistemas incluye. Para proteger -por ejemplo- solamente el subsistema de **sudo**, lo pondríamos en `/etc/pam.d/sudo`.

Añadimos la línea relevante al final del fichero y listo:

```bash
gerard@secure:~$ tail -1 /etc/pam.d/common-auth
auth required pam_google_authenticator.so nullok
gerard@secure:~$
```

**TRUCO**: El parámetro `nullok` permite que un usuario que no haya configurado la autenticación (ver más adelante), pueda seguir entrando sin ella, de la forma tradicional. Por supuesto, tras un periodo razonable, esta directiva se va a quitar, para obligar a todo el mundo a cumplir con las nuevas exigencias de seguridad.

Otro punto conflictivo es el **SSH**, al que hay que dar a entender que "hay dos peticiones de *login*" seguidas. Esto se hace mediante la directiva `ChallengeResponseAuthentication` en su configuración, que tendrá que recargar después.

```bash
gerard@secure:~$ grep -i ^challenge /etc/ssh/sshd_config
ChallengeResponseAuthentication yes
gerard@secure:~$
```

```bash
gerard@secure:~$ sudo service ssh reload
gerard@secure:~$
```

**AVISO**: Me pasé un buen rato sin que funcionara porque tenía dos veces la directiva, primero con "no" y luego con "yes"; eso no vale y solo debe quedar una sin comentar.

## Configurando un cliente

De hecho, este proceso debe repetirse para cada usuario "tradicional" que pretenda acceder al sistema. No es necesario para usuarios que no vayan a entrar, bloqueados o usuarios de servicio.

El procedimiento no puede ser más simple: ejecutamos el asistente.

```bash
gerard@secure:~$ google-authenticator
...
gerard@secure:~$
```

Este asistente nos va a hacer preguntas para regular el comportamiento del módulo (cosas como *tokens* por tiempo, reusabilidad de los códigos o un *rate limiting* de *logins* por tiempo). Es seguro responder que sí a todas las preguntas.

Finalmente nos va a mostrar un código QR y una clave, que no sirve para configurar la aplicación generadora de códigos (por ejemplo, [la suya](https://play.google.com/store/apps/details?id=com.google.android.apps.authenticator2&hl=es)). Podemos escanear el código o poner a mano la clave, con un nombre de cuenta descriptiva.

Es importante anotar los códigos de emergencia por si no tuviéramos el móvil a mano, aunque son de un solo uso. Esto nos va a crear un fichero `.google_authenticator` con los parámetros, las claves y los códigos de emergencia.

**TRUCO**: Si se os acaban los códigos de emergencia podéis añadirlos a mano en el mismo fichero.

En mi caso, como tengo demasiados servidores para administrar, tomé la decisión de configurar el generador en mi móvil **una única vez** y copiar el fichero `.google_authenticator` en todos los demás servidores, de forma que se rigen por el mismo generador. Solo os conviene saber que el fichero debe tener permisos `0600` o más restrictivos, o será rechazado al entrar.


```bash
gerard@secure:~$ chmod 600 .google_authenticator
gerard@secure:~$
```

Repetimos para todos los usuarios y ya lo tenemos.
