---
title: "Recetas interesantes con Systemd"
slug: "recetas-interesantes-con-systemd"
date: "2021-10-27"
categories: ['Sistemas']
tags: ['debian', 'systemd', 'jaula', 'overlayfs', 'squashfs']
---

No es un secreto que me encanta utilizar **systemd**; aunque hay una buena
parte de la comunidad que lo detesta, siempre encuentro la manera de hacer
lo que yo necesito. Y es que las funcionalidades que ofrece son muchas y
la documentación es excelente. Vamos a ver algunas recetas útiles.<!--more-->

## Orden de montado de sistemas de ficheros

A veces es importante el orden en el que se montan los sistemas de ficheros;
con el fichero `/etc/fstab` el orden era que marcaban las líneas del fichero.
Con **systemd**, esto cambia; se intenta paralelizar todas las tareas posibles,
lo que puede resultar en un caos impresionante.

Tomemos como ejemplo [un artículo anterior][1]. La última parte del artículo
sugiere que podemos montar las jaulas mezclando una capa de cambios con una
capa base, que a su vez puede ser un punto de montaje **squashfs**. Dejo
un ejemplo aquí:

```bash
gerard@alcatraz:/srv$ tree
.
├── debian-nginx.sqsh
├── jails
│   └── nginx1
└── overlay
    └── nginx1
        ├── lowerdir
        ├── upperdir
        │   ├── etc
        │   │   └── nginx
        │   │       └── sites-enabled
        │   │           ├── default
        │   │           └── web
        │   └── var
        │       └── www
        │           └── html
        │               ├── index.html
        │               └── index.nginx-debian.html
        └── workdir

13 directories, 5 files
gerard@alcatraz:/srv$
```

```bash
gerard@alcatraz:/srv$ cat /etc/fstab
...
/srv/debian-nginx.sqsh /srv/overlay/nginx1/lowerdir squashfs loop 0 0
overlay /srv/jails/nginx1 overlay noauto,x-systemd.automount,lowerdir=/srv/overlay/nginx1/lowerdir,upperdir=/srv/overlay/nginx1/upperdir,workdir=/srv/overlay/nginx1/workdir 0 0
...
gerard@alcatraz:/srv$
```

```bash
gerard@alcatraz:/srv$ cat /etc/systemd/system/nginx1.service
[Service]
RootDirectory=/srv/jails/nginx1
ExecStart=/usr/sbin/nginx -g "daemon off;"

[Install]
WantedBy=multi-user.target
gerard@alcatraz:/srv$
```

Todo funciona muy bien si montamos los puntos manualmente, pero falla al
reiniciar la máquina; solo nos queda una jaula con la capa superior. El
motivo es simple: el montaje del sistema de ficheros **overlayfs** se hace
antes que el montaje del sistema de ficheros **squashfs**.

Esto causa que la capa conjunta sea el resultado de juntar una carpeta de
cambios con una carpeta vacía. Por suerte, podemos cambiar este comportamiento
añadiendo dependencias entre ellos para que se monten en un orden concreto.

La solución pasa por entender como funciona **systemd** en relación al fichero
`/etc/fstab`: hay un binario `systemd-fstab-generator` que genera una *unit*
por cada línea del fichero. Por ejemplo, pongo la línea del `/etc/fstab` que
monta la carpeta raíz y su *unit* generada:

```bash
gerard@alcatraz:~$ cat /etc/fstab
...
UUID=3723d7aa-ca4d-4959-ade2-80d7b2d0bb5e /               ext4    errors=remount-ro 0       1
...
gerard@alcatraz:~$
```

```bash
gerard@alcatraz:~$ cat /run/systemd/generator/-.mount
# Automatically generated by systemd-fstab-generator

[Unit]
Documentation=man:fstab(5) man:systemd-fstab-generator(8)
SourcePath=/etc/fstab
After=blockdev@dev-disk-by\x2duuid-3723d7aa\x2dca4d\x2d4959\x2dade2\x2d80d7b2d0bb5e.target

[Mount]
Where=/
What=/dev/disk/by-uuid/3723d7aa-ca4d-4959-ade2-80d7b2d0bb5e
Type=ext4
Options=errors=remount-ro
gerard@alcatraz:~$
```

Sabiendo esto, podemos atacar el problema de dos formas distintas:

* Podemos eliminar (o comentar) la línea en el `/etc/fstab` para que no genere
  la *unit*, que gestionaremos nosotros; podemos coger la autogenerada como
  punto de partida. A partir de aquí, pondremos las directivas que queramos.
* Otra opción, consiste en indicar las directivas que queremos que se autogeneren
  en las opciones de montaje en el `/etc/fstab`, prefijadas por `x-systemd.`.

Optamos por este último, por su simplicidad. En este caso, la directiva a añadir
es `x-systemd.requires-mounts-for` y esto nos va a generar una *unit* que contenga
nuestros requisitos en el orden del montaje.

```bash
gerard@alcatraz:~$ cat /etc/fstab
...
/srv/debian-nginx.sqsh /srv/overlay/nginx1/lowerdir squashfs loop 0 0
overlay /srv/jails/nginx1 overlay noauto,x-systemd.automount,lowerdir=/srv/overlay/nginx1/lowerdir,upperdir=/srv/overlay/nginx1/upperdir,workdir=/srv/overlay/nginx1/workdir,x-systemd.requires-mounts-for=/srv/overlay/nginx1/lowerdir 0 0
...
gerard@alcatraz:~$
```

```bash
gerard@alcatraz:~$ cat /run/systemd/generator/srv-jails-nginx1.mount
# Automatically generated by systemd-fstab-generator

[Unit]
Documentation=man:fstab(5) man:systemd-fstab-generator(8)
SourcePath=/etc/fstab
RequiresMountsFor=/srv/overlay/nginx1/lowerdir

[Mount]
Where=/srv/jails/nginx1
What=overlay
Type=overlay
Options=noauto,x-systemd.automount,lowerdir=/srv/overlay/nginx1/lowerdir,upperdir=/srv/overlay/nginx1/upperdir,workdir=/srv/overlay/nginx1/workdir,x-systemd.requires-mounts-for=/srv/overlay/nginx1/lowerdir
gerard@alcatraz:~$
```

Reiniciamos la máquina y vemos que la jaula se ha montado correctamente y que
el servicio funciona como esperábamos (y como funcionaba antes del reinicio).

## Levantando servicios dentro de una jaula

Cuando trabajamos con jaulas, debemos ejecutar los binarios entrando en la
misma, normalmente utilizando el comando `chroot`. Si queremos que este
ejecutable levante un servicio, y lo queremos hacer cómodamente mediante
el proceso inicial de nuestro sistema operativo, la cosa suele complicarse.

Por suerte, **systemd** simplifica las cosas de forma notable. Aunque el
proceso **systemd** está en el sistema operativo principal, y por lo tanto
también sus *units*, ejecutar dentro de un **chroot** es tan fácil como
indicar la directiva `RootDirectory`.

Veamos un ejemplo, aprovechando el ejemplo anterior:

```bash
gerard@alcatraz:~$ cat /etc/systemd/system/nginx1.service
[Service]
RootDirectory=/srv/jails/nginx1
ExecStart=/usr/sbin/nginx -g "daemon off;"

[Install]
WantedBy=multi-user.target
gerard@alcatraz:~$
```

En este caso se va a ejecutar el binario `/usr/sbin/nginx`, con el entendido
de que es la ruta una vez ya estamos enjaulados en `/srv/jails/nginx1`. Por
lo tanto, ejecutaremos el binario real `/srv/jails/nginx1/usr/sbin/nginx`,
aunque este no lo sepa...

## Configurando servicios mediante variables de entorno

Con el paradigma de **docker** en la esquina, muchos aplicativos empiezan
a permitir su configuración mediante variables de entorno y algunos lo llevan
fuera de esa tecnología concreta. Otros optan por dejarlo listo para un
futuro uso en **docker**, pero levantan la aplicación en local, usando el
proceso inicial del que disponen.

En estos casos, **systemd** también es una ayuda grande. Con las directivas
`Environment` y `EnvironmentFile` podemos dar esas variables, sea directamente
en la *unit* de **systemd**, o en un fichero tipo `source`.

Ilustremos esto con un ejemplo, por ejemplo una API escrita en **python**.
Disponemos de una aplicación, su fichero de requisitos y un fichero con los
secretos. Le ponemos su *virtualenv* y su *unit* de **systemd**:

```bash
gerard@medusa:/srv/showmysecrets$ tree -L 2
.
├── env
│   ├── bin
│   ├── include
│   ├── lib
│   ├── lib64 -> lib
│   ├── share
│   └── pyvenv.cfg
├── app.py
├── requirements.txt
└── secrets

6 directories, 4 files
gerard@medusa:/srv/showmysecrets$
```

```bash
gerard@medusa:/srv/showmysecrets$ cat app.py
import falcon
import os

class SecretsResource:
    def on_get(self, req, resp):
        resp.media = {
            'SECRET1': os.environ.get('SECRET1', 'undefined'),
            'SECRET2': os.environ.get('SECRET2', 'undefined'),
            'SECRET3': os.environ.get('SECRET3', 'undefined'),
        }

app = falcon.App()
app.add_route('/secrets', SecretsResource())
gerard@medusa:/srv/showmysecrets$
```

```bash
gerard@medusa:/srv/showmysecrets$ cat requirements.txt
falcon==3.0.1
gunicorn==20.1.0
gerard@medusa:/srv/showmysecrets$
```

```bash
gerard@medusa:/srv/showmysecrets$ cat secrets
SECRET1="secret1_v1"
SECRET2="secret2_v1"
gerard@medusa:/srv/showmysecrets$
```

```bash
gerard@medusa:/srv/showmysecrets$ cat /etc/systemd/system/showmysecrets.service
[Service]
DynamicUser=yes
WorkingDirectory=/srv/showmysecrets
Environment="SECRET3=secret3_v1"
EnvironmentFile=/srv/showmysecrets/secrets
ExecStart=/srv/showmysecrets/env/bin/gunicorn --bind :8080 app:app

[Install]
WantedBy=multi-user.target
gerard@medusa:/srv/showmysecrets$
```

**NOTA**: Nos hemos basado en [este otro artículo][2].

Tras el correspondiente `systemctl daemon-reload` y el `systemctl start showmysecrets`,
tenemos el servicio funcional, con el entendido de que las variables de entorno
proceden del fichero `secrets` (`SECRET1` y `SECRET2`) y de la misma *unit* de
**systemd** (`SECRET3`).

No es una sorpresa que la API nos devuelva los valores esperados:

```bash
gerard@medusa:/srv/showmysecrets$ curl -s http://localhost:8080/secrets | python3 -m json.tool
{
    "SECRET1": "secret1_v1",
    "SECRET2": "secret2_v1",
    "SECRET3": "secret3_v1"
}
gerard@medusa:/srv/showmysecrets$
```

**NOTA**: El fichero de secretos se lee cada vez que se (re)inicia el servicio.
Las variables de entorno que vienen de la *unit* de **systemd**, además, necesitan
aplicar un `systemctl daemon-reload` para que **systemd** recargue la *unit*.

Ambos métodos tienen sus ventajas e inconvenientes, especialmente la facilidad
de modificación de las variables (si el usuario pudiera escribir el fichero de
secretos) y la seguridad que nos ofrece tenerla en un sitio de sistema.

[1]: {{< relref "/articles/2021/06/una-vision-general-de-overlayfs.md" >}}
[2]: {{< relref "/articles/2019/12/desplegando-aplicaciones-python-con-gunicorn-y-systemd.md" >}}
