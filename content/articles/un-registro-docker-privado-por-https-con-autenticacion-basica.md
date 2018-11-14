Title: Un registro docker privado por HTTPS con autenticación básica
Slug: un-registro-docker-privado-por-https-con-autenticacion-basica
Date: 2018-11-19 10:00
Category: Sistemas
Tags: docker, registro, ssl, tls, autenticación, autenticacion basica



Cuando usamos integración continua o despliegues en varios servidores y usamos **docker**, se hace importante tener una fuente de imágenes de donde descargar las nuestras propias. Aquí entra en juego la confidencialidad, y es necesario pagar la capa privada de un registro, o podemos simplemente crear un registro nuestro propio.

Si el registro está abierto a nuestra red corporativa, somos vulnerables a ataques maliciosos por parte de empleados descontentos o traviesos. En estos casos se recomienda utilizar TLS para encriptar las comunicaciones y activar autenticación para que no nos puedan reescribir las imágenes.

Hacerlo no es muy complicado y solo vamos a tener que hacerlo una vez; vale la pena y así dejamos un punto de preocupación menos en nuestra infraestructura. Vamos a partir del siguiente escenario:

* Un servidor con **docker** dedicado al registro, con nombre `registry.test`
* Un servidor cliente, también con **docker** para simular los futuros clientes de nuestro registro, con nombre `node01.test`

**NOTA**: Es importante poner un dominio en nuestro servidor de registro, porque sino **docker** puede pensarse que se trata de un usuario de **DockerHub**; por ejemplo `registry/image` se puede referir a la URL "registry" o ir a **DockerHub** y hacer el *push* o *pull* con el usuario "registry".

## Activando TLS

Para activar TLS, solamente se necesita indicar el *path* en el contenedor en donde está el certificado, con las configuraciones o variables de entorno `REGISTRY_HTTP_TLS_KEY` y `REGISTRY_HTTP_TLS_CERTIFICATE`. Como la imagen no lleva certificados, y para facilitar su cambio, vamos a montar los certificados como volúmenes locales.

Como no tenemos dichos certificados, vamos a crearlos. Por economía voy a utilizar un certificado autofirmado, pero tal vez os interese utilizar uno firmado por una autoridad certificadora, como **VeriSign** u otras. En el caso del certificado autofirmado, necesitaremos un paso adicional en cada cliente, que ya veremos.

Creamos la carpeta de certificados (que luego montaremos), y generamos la clave y el certificado con los comandos habituales:

```bash
gerard@registry:~/registry$ mkdir certs
gerard@registry:~/registry$
```

```bash
gerard@registry:~/registry$ openssl req -newkey rsa:4096 -nodes -sha256 -keyout certs/domain.key -x509 -days 365 -out certs/domain.crt
...
Common Name (e.g. server FQDN or YOUR name) []:registry.test
...
gerard@registry:~/registry$
```

**NOTA**: El campo CN es importante; debe coincidir con el dominio HTTPS que se solicite o el certificado será rechazado.

Levantaremos con **docker-compose** por comodidad y para facilitar el levantamiento futuro del mismo; solo hemos cambiado el puerto de servicio al 443 y hemos indicado la clave y el certificado, en la ruta que montamos como volúmen. El resto es a gusto del consumidor.

```bash
gerard@registry:~/registry$ cat docker-compose.yml
version: '3'
services:
  registry:
    image: registry:2
    container_name: registry
    hostname: registry
    environment:
      REGISTRY_HTTP_ADDR: 0.0.0.0:443
      REGISTRY_HTTP_TLS_KEY: /certs/domain.key
      REGISTRY_HTTP_TLS_CERTIFICATE: /certs/domain.crt
    volumes:
      - data:/var/lib/registry
      - ./certs:/certs:ro
    ports:
      - "443:443"
    restart: always
volumes:
  data:
gerard@registry:~/registry$
```

En este punto, nuestra carpeta de *runtime* solo tiene 3 ficheros:

```bash
gerard@registry:~/registry$ tree
.
├── certs
│   ├── domain.crt
│   └── domain.key
└── docker-compose.yml

1 directory, 3 files
gerard@registry:~/registry$
```

Levantamos el servicio, y con esto tenemos el registro en funcionamiento, aunque sin autenticación por el momento.

```bash
gerard@registry:~/registry$ docker-compose up -d
Creating network "registry_default" with the default driver
Creating volume "registry_data" with default driver
Creating registry ... done
gerard@registry:~/registry$
```

### Trabajando con el cliente

El funcionamiento en el cliente es el mismo de siempre; solo tenemos que preceder el nombre de la imagen por la URL del registro a utilizar. Para no crear mi propia imagen y emborronar el artículo, voy a descargar una cualquiera y a adueñármela:

```bash
gerard@node01:~$ docker pull alpine
Using default tag: latest
latest: Pulling from library/alpine
4fe2ade4980c: Pull complete
Digest: sha256:621c2f39f8133acb8e64023a94dbdf0d5ca81896102b9e57c0dc184cadaf5528
Status: Downloaded newer image for alpine:latest
gerard@node01:~$
```

```bash
gerard@node01:~$ docker tag alpine registry.test/alpine
gerard@node01:~$
```

En este momento tenemos las dos imágenes, aunque se puede ver por el *image id* que son las mismas.

```bash
gerard@node01:~$ docker images
REPOSITORY             TAG                 IMAGE ID            CREATED             SIZE
alpine                 latest              196d12cf6ab1        5 weeks ago         4.41MB
registry.test/alpine   latest              196d12cf6ab1        5 weeks ago         4.41MB
gerard@node01:~$
```

La subimos al registro con el correspondiente `docker pull` y listo:

```bash
gerard@node01:~$ docker push registry.test/alpine
The push refers to repository [registry.test/alpine]
Get https://registry.test/v2/: x509: certificate signed by unknown authority
gerard@node01:~$
```

**NOTA**: El *push* ha fallado, porque el certificado no es confiable, al no estar firmado por ninguna autoridad certificadora. Si queremos que se acepte este certificado, necesitamos un paso adicional, que es el que sigue:

Para que **docker** confíe en un certificado no confiable, debemos añadir dicho certificado a la ruta `/etc/docker/certs.d/<dominio>/ca.crt`. Este `ca.crt` no es otro que el certificado del registro (no la clave), que hemos llamado `domain.crt` en el servidor del registro.

```bash
gerard@node01:~$ sudo mkdir -p /etc/docker/certs.d/registry.test
gerard@node01:~$
```

```bash
gerard@node01:~$ sudo cat /etc/docker/certs.d/registry.test/ca.crt
-----BEGIN CERTIFICATE-----
...
-----END CERTIFICATE-----
gerard@node01:~$
```

No es necesario reiniciar nada. Relanzamos el `docker push` y ya debería funcionar.

```bash
gerard@node01:~$ docker push registry.test/alpine
The push refers to repository [registry.test/alpine]
df64d3292fd6: Pushed
latest: digest: sha256:02892826401a9d18f0ea01f8a2f35d328ef039db4e1edcc45c630314a0457d5b size: 528
gerard@node01:~$
```

Podemos verificar que el registro contiene la imagen consultando su propia API:

```
gerard@node01:~$ curl -k https://registry.test/v2/_catalog
{"repositories":["alpine"]}
gerard@node01:~$
```

Esto nos demuestra que el registro privado funciona según lo esperado.

## Habilitando la autenticación

Vamos a utilizar autenticación básica por su simplicidad, pero hay varios métodos posibles. Para ello vamos a utilizar la misma técnica: indicar autenticación básica mediante variables de entorno, indicando el *path* a un fichero de autenticación que vamos a montar como volúmen.

Generamos un fichero `htpasswd` estándar, que se puede crear mediante la misma imagen del registro:

```bash
gerard@registry:~/registry$ mkdir auth
gerard@registry:~/registry$
```

```bash
gerard@registry:~/registry$ docker run --entrypoint htpasswd --rm registry:2 -Bbn user p4ssw0rd > auth/htpasswd
gerard@registry:~/registry$
```

**TRUCO**: Es posible crear varios usuarios, pero no es muy útil; todos ellos van a poder ver las mismas imágenes y modificarlas a placer.

En este punto tenemos un fichero nuevo con los usuarios aceptados; si alguna vez tenemos que cambiarlos, como no forman parte de la imagen, basta con "dar el cambiazo".

```bash
gerard@registry:~/registry$ cat auth/htpasswd
user:$2y$05$M/IbI44MSrDFj9bcuFRPt.6tiit1r0V1.KCy2tf4hAzNuznqR9cXG
gerard@registry:~/registry$
```

El número de ficheros de *runtime* no ha incrementado casi nada:

```bash
gerard@registry:~/registry$ tree
.
├── auth
│   └── htpasswd
├── certs
│   ├── domain.crt
│   └── domain.key
└── docker-compose.yml

2 directories, 4 files
gerard@registry:~/registry$
```

Solo vamos a necesitar algunas modificaciones en el *docker-compose.yml* para añadir el volumen de autenticación y las variables de entorno que la activan.

```bash
gerard@registry:~/registry$ cat docker-compose.yml
version: '3'
services:
  registry:
    image: registry:2
    container_name: registry
    hostname: registry
    environment:
      REGISTRY_HTTP_ADDR: 0.0.0.0:443
      REGISTRY_HTTP_TLS_KEY: /certs/domain.key
      REGISTRY_HTTP_TLS_CERTIFICATE: /certs/domain.crt
      REGISTRY_AUTH: htpasswd
      REGISTRY_AUTH_HTPASSWD_REALM: LinuxSysadmin registry
      REGISTRY_AUTH_HTPASSWD_PATH: /auth/htpasswd
    volumes:
      - data:/var/lib/registry
      - ./certs:/certs:ro
      - ./auth:/auth:ro
    ports:
      - "443:443"
    restart: always
volumes:
  data:
gerard@registry:~/registry$
```

Vamos a levantar de nuevo el servicio para que apliquen los cambios:

```bash
gerard@registry:~/registry$ docker-compose up -d
Recreating registry ... done
gerard@registry:~/registry$
```

### Verificando la autenticación

El primer indicio de que algo falla es que no podemos consultar la API, ni descargar la imagen:

```bash
gerard@node01:~$ curl -k https://registry.test/v2/_catalog
{"errors":[{"code":"UNAUTHORIZED","message":"authentication required","detail":[{"Type":"registry","Class":"","Name":"catalog","Action":"*"}]}]}
gerard@node01:~$
```

```bash
gerard@node01:~$ docker pull registry.test/alpine
Using default tag: latest
Error response from daemon: Get https://registry.test/v2/alpine/manifests/latest: no basic auth credentials
gerard@node01:~$
```

En el caso de la API, podemos usar el *flag* que **curl** nos ofrece, que ya gestiona la parte de la autenicación básica:

```bash
gerard@node01:~$ curl -k -u user:p4ssw0rd https://registry.test/v2/_catalog
{"repositories":["alpine"]}
gerard@node01:~$
```

Para poder utilizar **docker**, vamos a necesitar hacer *login*. **Docker** ya nos ofrece esta facilidad.

```bash
gerard@node01:~$ docker login registry.test
Username: user
Password:
WARNING! Your password will be stored unencrypted in /home/gerard/.docker/config.json.
Configure a credential helper to remove this warning. See
https://docs.docker.com/engine/reference/commandline/login/#credentials-store

Login Succeeded
gerard@node01:~$
```

Una vez hecho el *login*, ya podemos hacer las operaciones de *push* y de *pull* al registro.

```bash
gerard@node01:~$ docker pull registry.test/alpine
Using default tag: latest
latest: Pulling from alpine
4fe2ade4980c: Pull complete
Digest: sha256:02892826401a9d18f0ea01f8a2f35d328ef039db4e1edcc45c630314a0457d5b
Status: Downloaded newer image for registry.test/alpine:latest
gerard@node01:~$
```

**NOTA**: El ejemplo parte de un servidor sin imágenes.

Solo nos falta ver que la imagen está disponible en el servidor local:

```bash
gerard@node01:~$ docker images
REPOSITORY             TAG                 IMAGE ID            CREATED             SIZE
registry.test/alpine   latest              196d12cf6ab1        5 weeks ago         4.41MB
gerard@node01:~$
```

Las credenciales se guardan en `~/.docker/config.json`, de una forma poco segura; es mejor ir haciendo *login* y *logout* entre operaciones. Alternativamente a las operationes de *login* y *logout*, podemos ir creando y eliminando este fichero según convenga.

```bash
gerard@node01:~$ cat .docker/config.json
{
        "auths": {
                "registry.test": {
                        "auth": "dXNlcjpwNHNzdzByZA=="
                }
        },
        "HttpHeaders": {
                "User-Agent": "Docker-Client/18.06.1-ce (linux)"
        }
}
gerard@node01:~$
```

Como ejemplo de la seguridad del fichero, solo hace falta ver que huele a una cadena en **base64**; descodificarla es trivial:

```bash
gerard@node01:~$ echo dXNlcjpwNHNzdzByZA== | base64 -d
user:p4ssw0rd
gerard@node01:~$
```

## Conclusiones

Tener un registro privado de **docker**, seguro y restringido, es relativamente fácil. Vale la pena dedicar un poco de esfuerzo al principio para que dicho servidor no sea la fuente de nuestras preocupaciones por su falta de seguridad o intrusiones futuras.

Estos pasos se hacen una sola vez por cada registro y no se tocan casi nunca, salvo renovación de certificados o de credenciales. Gracias a **docker-compose**, esto también es trivial...
