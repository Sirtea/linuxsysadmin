---
title: "Construyendo imágenes Docker de forma correcta"
slug: "construyendo-imagenes-docker-de-forma-correcta"
date: "2022-04-05"
categories: ['Seguridad']
tags: ['docker', 'dockerfile', 'hadolint', 'trivy']
---

Muchas veces nos ponemos a escribir nuestros ficheros `Dockerfile` sin prestar mucha atención a lo
que salga, siempre que funcione. Es una forma correcta de ver las cosas, pero suele ser un error;
verificar unos pocos puntos antes de dar el fichero por bueno nos puede ahorrar problemas futuros
y no requiere mucho tiempo.<!--more-->

Para hacerlo todavía más fácilmente, la comunidad nos brinda de algunas herramientas que nos
simplifican enormemente la tarea, ya de por sí bastante simple y corta. Hablamos de:

* **Hadolint** &rarr; [https://github.com/hadolint/hadolint][1]
* **Trivy** &rarr; [https://github.com/aquasecurity/trivy][2]

Se trata de dos herramientas que son un analizador de sintaxis (**hadolint**) y otra que se encarga
de buscar vulnerabilidades en la imagen, tanto presentes en la imagen como inducidas por posibles
errores nuestros (**trivy**).

## Instalando las herramientas

Esta parte no entraña ninguna dificultad; podemos utilizar las imágenes **Docker** oficiales para
no tener que pensar demasiado: [hadolint/hadolint][3] y [aquasec/trivy][4].

Alternativamente, podemos descargar los binarios precompilados y dejarlos en algún lugar en el
*path* de nuestro usuario o del sistema. Vamos a optar por esta última opción porque, al ser
binarios únicos, es muy fácil de hacer.

Descargamos la última versión disponible de [hadolint][5] y [trivy][6] y la colocamos, por ejemplo,
en `~/bin/`. En el caso de **hadolint** se trata del binario directamente, al que hay que renombrar
y dar permisos de ejecución; en el caso de **trivy** se trata de un fichero comprimido con el
binario dentro.

```bash
gerard@sandbox:~$ tree
.
└── bin
    ├── hadolint
    └── trivy

1 directory, 2 files
gerard@sandbox:~$ hadolint --version
Haskell Dockerfile Linter 2.10.0
gerard@sandbox:~$ trivy --version
Version: 0.25.0
gerard@sandbox:~$
```

## Un ejemplo de uso con un caso real

Tenemos un proyecto escrito en **python**, aunque eso es lo de menos. Creamos un `Dockerfile`
rápido, para salir del paso y ver que todo funciona como debe:

```bash
gerard@sandbox:~/myapi$ cat Dockerfile
FROM python
COPY requirements.txt /tmp/
RUN pip install -r /tmp/requirements.txt
COPY myapi/ /srv/myapi/
CMD ["gunicorn", "--bind=0.0.0.0:8080", "myapi:app"]
gerard@sandbox:~/myapi$
```

Este `Dockerfile` funciona, pero como veremos, no es la mejor versión del mismo. Pasaremos ambas
herramientas para ver lo que le falla.

### Hadolint

Esta herramienta nos va a sugerir algunas buenas prácticas, tanto a nivel de sintaxis del fichero
`Dockerfile`, como en el uso interno de algunos comandos que se utilizan en su construcción.

```bash
gerard@sandbox:~/myapi$ hadolint Dockerfile
Dockerfile:1 DL3006 warning: Always tag the version of an image explicitly
Dockerfile:3 DL3042 warning: Avoid use of cache directory with pip. Use `pip install --no-cache-dir <package>`
gerard@sandbox:~/myapi$
```

### Trivy

Esta otra herramienta nos va a dar la visión de las vulnerabilidades, tanto de la imagen base como
de las que podamos introducir nosotros. Vamos a empezar por las nuestras:

```bash
gerard@sandbox:~/myapi$ trivy fs --security-checks vuln,config .
2022-04-04T23:54:51.961+0200    INFO    Number of language-specific files: 0
2022-04-04T23:54:51.964+0200    INFO    Detected config files: 1

Dockerfile (dockerfile)
=======================
Tests: 23 (SUCCESSES: 21, FAILURES: 2, EXCEPTIONS: 0)
Failures: 2 (UNKNOWN: 0, LOW: 0, MEDIUM: 1, HIGH: 1, CRITICAL: 0)

+---------------------------+------------+--------------------+----------+------------------------------------------+
|           TYPE            | MISCONF ID |       CHECK        | SEVERITY |                 MESSAGE                  |
+---------------------------+------------+--------------------+----------+------------------------------------------+
| Dockerfile Security Check |   DS001    | ':latest' tag used |  MEDIUM  | Specify a tag in the 'FROM'              |
|                           |            |                    |          | statement for image 'python'             |
|                           |            |                    |          | -->avd.aquasec.com/appshield/ds001       |
+                           +------------+--------------------+----------+------------------------------------------+
|                           |   DS002    | root user          |   HIGH   | Specify at least 1 USER                  |
|                           |            |                    |          | command in Dockerfile with               |
|                           |            |                    |          | non-root user as argument                |
|                           |            |                    |          | -->avd.aquasec.com/appshield/ds002       |
+---------------------------+------------+--------------------+----------+------------------------------------------+
gerard@sandbox:~/myapi$
```

Ambas herramientas nos indican que deberíamos utilizar un *tag* en la directiva `FROM`. Sobre esto
no hay mucho que decir; tenemos varias opciones si combinamos la versión con la variante.

En este caso vamos a utilizar la versión 3.8 de **python**, simplemente porque es la versión que
se utilizó para hacer el desarrollo. En cuanto a la variante, disponemos de 3:

* `python:<version>` &rarr; Se trata de una imagen **debian** con varios compiladores preinstalados. Como no los necesitamos, descarto la imagen directamente.
* `python:<version>-slim` &rarr; Lo mismo que antes, pero sin los compiladores, que normalmente no se utilizan. Esta es una buena opción.
* `python:<version>-alpine` &rarr; Esta imagen tiene una base de **alpine linux**, más pequeña. En principio es un reemplazo adecuado para las otras dos, aunque tampoco incluye compiladores; es otra buena opción, si nos funciona.

Ahora toca ver las vulnerabilidades de las dos opciones, que se puede hacer con `trivy image`:

```bash
gerard@sandbox:~/myapi$ trivy image python:3.8-slim
2022-04-05T00:02:22.961+0200    INFO    Detected OS: debian
2022-04-05T00:02:22.964+0200    INFO    Detecting Debian vulnerabilities...
2022-04-05T00:02:23.010+0200    INFO    Number of language-specific files: 1
2022-04-05T00:02:23.012+0200    INFO    Detecting python-pkg vulnerabilities...

python:3.8-slim (debian 11.3)
=============================
Total: 75 (UNKNOWN: 0, LOW: 66, MEDIUM: 4, HIGH: 5, CRITICAL: 0)

+------------------+------------------+----------+-------------------+-------------------------+-----------------------------------------+
|     LIBRARY      | VULNERABILITY ID | SEVERITY | INSTALLED VERSION |      FIXED VERSION      |                  TITLE                  |
+------------------+------------------+----------+-------------------+-------------------------+-----------------------------------------+
| apt              | CVE-2011-3374    | LOW      | 2.2.4             |                         | It was found that apt-key in apt,       |
|                  |                  |          |                   |                         | all versions, do not correctly...       |
|                  |                  |          |                   |                         | -->avd.aquasec.com/nvd/cve-2011-3374    |
+------------------+------------------+          +-------------------+-------------------------+-----------------------------------------+
| bsdutils         | CVE-2022-0563    |          | 2.36.1-8+deb11u1  |                         | util-linux: partial disclosure          |
|                  |                  |          |                   |                         | of arbitrary files in chfn              |
|                  |                  |          |                   |                         | and chsh when compiled...               |
|                  |                  |          |                   |                         | -->avd.aquasec.com/nvd/cve-2022-0563    |
+------------------+------------------+          +-------------------+-------------------------+-----------------------------------------+
...
Python (python-pkg)
===================
Total: 0 (UNKNOWN: 0, LOW: 0, MEDIUM: 0, HIGH: 0, CRITICAL: 0)

gerard@sandbox:~/myapi$
```

```bash
gerard@sandbox:~/myapi$ trivy image python:3.8-alpine
2022-04-05T00:03:59.507+0200    INFO    Detected OS: alpine
2022-04-05T00:03:59.510+0200    INFO    Detecting Alpine vulnerabilities...
2022-04-05T00:03:59.524+0200    INFO    Number of language-specific files: 1
2022-04-05T00:03:59.524+0200    INFO    Detecting python-pkg vulnerabilities...

python:3.8-alpine (alpine 3.15.3)
=================================
Total: 2 (UNKNOWN: 2, LOW: 0, MEDIUM: 0, HIGH: 0, CRITICAL: 0)

+------------+------------------+----------+-------------------+---------------+---------------------------------------+
|  LIBRARY   | VULNERABILITY ID | SEVERITY | INSTALLED VERSION | FIXED VERSION |                 TITLE                 |
+------------+------------------+----------+-------------------+---------------+---------------------------------------+
| busybox    | CVE-2022-28391   | UNKNOWN  | 1.34.1-r4         | 1.34.1-r5     | BusyBox through 1.35.0 allows         |
|            |                  |          |                   |               | remote attackers to execute           |
|            |                  |          |                   |               | arbitrary code if netstat...          |
|            |                  |          |                   |               | -->avd.aquasec.com/nvd/cve-2022-28391 |
+------------+                  +          +                   +               +                                       +
| ssl_client |                  |          |                   |               |                                       |
|            |                  |          |                   |               |                                       |
|            |                  |          |                   |               |                                       |
|            |                  |          |                   |               |                                       |
+------------+------------------+----------+-------------------+---------------+---------------------------------------+

Python (python-pkg)
===================
Total: 0 (UNKNOWN: 0, LOW: 0, MEDIUM: 0, HIGH: 0, CRITICAL: 0)

gerard@sandbox:~/myapi$
```

A la vista de los resultados vamos a utilizar la variante basada en **alpine linux**, simplemente
por el menor número de vulnerabilidades presentes.

### Subsanando los problemas

Hemos encontrado 3 posibles problemas:

* Una falta de *tag* en la imagen base, que podemos corregir fácilmente utilizando la imagen base `python:3.8-alpine`
* Un *flag* sugerido en el comando `pip`, que podemos añadir sin problemas
* Ejecución del servidor `gunicorn` con el usuario **root** que se utiliza por defecto; basta con utilizar otro usuario, por ejemplo, **nobody**.

Con estas simples directrices, nos quedaría un ejemplo más seguro con el siguiente `Dockerfile`:

```bash
gerard@sandbox:~/myapi$ cat Dockerfile
FROM python:3.8-alpine
COPY requirements.txt /tmp/
RUN pip install --no-cache-dir -r /tmp/requirements.txt
COPY myapi/ /srv/myapi/
USER nobody
CMD ["gunicorn", "--bind=0.0.0.0:8080", "myapi:app"]
gerard@sandbox:~/myapi$
```

Y con esto podemos versionar el fichero `Dockerfile`, que seguramente no vaya a ver más cambios
relevantes durante el resto de la vida del proyecto.

[1]: https://github.com/hadolint/hadolint
[2]: https://github.com/aquasecurity/trivy
[3]: https://hub.docker.com/r/hadolint/hadolint
[4]: https://hub.docker.com/r/aquasec/trivy/
[5]: https://github.com/hadolint/hadolint/releases/tag/v2.10.0
[6]: https://github.com/aquasecurity/trivy/releases/tag/v0.25.0
