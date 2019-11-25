---
title: "Con confianza: Una autoridad certificadora propia"
slug: "con-confianza-una-autoridad-certificadora-propia"
date: "2019-11-25"
categories: ['Operaciones']
tags: ['CA', 'ssl', 'https', 'certificado', 'openssl']
---

Es muy habitual tener varios entornos en donde ejecutar nuestras aplicaciones;
algunos son entornos productivos o copias exactas, pero muchos otros son entornos
de desarrollo y de pruebas que solo son accedidos por una minoría, normalmente
de nuestra misma empresa. Y si usan certificados SSL válidos, el coste se dispara.<!--more-->

En estos casos podemos recurrir a generar certificados autofirmados, en los que
solemos confiar cuando el navegador nos los presenta. Sin embargo, la arquitectura
basada en microservicios nos plantea nuevos desafíos, que convierten esta acción
de confianza en un problema:

1. Tenemos muchos dominios o subdominios, uno por microservicio y entorno.
2. Creamos y destruimos entornos con gran facilidad, y los cambios son frecuentes.
3. Necesitamos que otros servicios confíen en sus homólogos de forma automática.

Podemos simplificar todos ellos de forma fácil si generamos nuestros certificados
usando uno nuestro intermedio; de esta forma podemos generar los certificados
finales de forma rápida y automatizada. Esto simplifica las relaciones de confianza,
que quedan reducidas a una sola: confiar en el certificado intermedio.

Trabajando de esta forma, los certificados finales serán confiables sí también
lo es el certificado intermedio. De esto último se encargará una sola excepción
manual. Así tendremos a nuestra disposición una autoridad certificadora (CA)
de "estar por casa", simple, sencilla y efectiva. Y lo mejor: solo necesitamos
instalar un solo paquete, que seguramente ya tenemos instalado: **openssl**.

## Crear los certificados de la CA

Una CA no es otra cosa que una metodología de trabajo. La idea es que es una
fábrica para firmar certificados, basándonos en un certificado *master*. A su
vez, este certificado puede estar firmado por otro, y así sucesivamente.

**NOTA**: Para simplificar, vamos a asumir que solo tenemos un certificado *master*,
que vamos a tratar como nuestro certificado raíz o intermedio.

El primer paso para crear un certificado es generar una clave. Esta clave es
privada, y no debería ser accesible a nadie ajeno a nuestro intereses.

```bash
gerard@umbra:~/services/ca$ openssl genrsa -out ca.key 2048
Generating RSA private key, 2048 bit long modulus
...................................................+++++
.+++++
e is 65537 (0x010001)
gerard@umbra:~/services/ca$ 
```

**TRUCO**: Es interesante añadir el *flag* `-des3` para que la clave esté cifrada
con una contraseña. No lo he puesto para que la operación de firma no me la pida
y se pueda automatizar el proceso en un futuro.

Teniendo la clave, la podemos usar para generar un certificado autofirmado, que
va a ser nuestro certificado raíz. Este certificado es público, y lo deberemos
distribuir entre todos aquellos clientes que tengan que confiar en él.

```bash
gerard@umbra:~/services/ca$ openssl req -sha256 -x509 -days 3650 -key ca.key -out ca.crt -subj "/CN=LinuxSysadmin CA"
gerard@umbra:~/services/ca$ 
```

**NOTA**: El campo `CN` solo sirve para que el navegador lo ponga en la lista de
autoridades conocidas, y es el texto que va a aparecer en el nombre. Realmente se
puede poner lo que nos apetezca, y nada va a cambiar.

En este punto tenemos dos ficheros: un `ca.key` y un `ca.crt`.

Muchos navegadores modernos exigen como medida extra de seguridad que el dominio
de un sitio aparezca en dos lugares del certificado final: el campo `CN` y el
campo `subjectAltName`. Para ello necesitamos firmar los certificados con cierto
fichero de opciones que es siempre el mismo, excepto el dominio; vamos a utilizar
una especie de plantilla, que dejamos aquí para el futuro para que la operación
de firma la utilice:

```bash
gerard@umbra:~/services/ca$ cat v3.ext.tpl 
authorityKeyIdentifier=keyid,issuer
basicConstraints=CA:FALSE
keyUsage = digitalSignature, nonRepudiation, keyEncipherment, dataEncipherment
subjectAltName = @alt_names

[alt_names]
DNS.1 = %%DOMAIN%%
gerard@umbra:~/services/ca$ 
```

Con esto tenemos nuestra CA funcional, y no tendremos que tocarla hasta que
tengamos que cambiar el certificado raíz o la clave, ya sea porque han sido
comprometidos o porque ha caducado el certificado a los 10 años indicados.

## Creando un certificado

Esta operación se va a tener que hacer para cada certificado generado.

**TRUCO**: Para facilitar el *copy-paste* de comandos, todos ellos van a utilizar
una variable de entorno para indicar el dominio, que es fácil de cambiar y sirve
en varios puntos de los diferentes comandos usados.

```bash
gerard@umbra:~/services/ca$ export DOMAIN=web.local
gerard@umbra:~/services/ca$ 
```

Para crear un certificado nuevo necesitamos una clave nueva. Esta clave se genera
una sola vez y se puede reutilizar hasta que decidamos revocarla por razones de
fuerza mayor, sean de seguridad o de pérdida de la misma. Así pues, si ya la
tenemos, podemos saltar este paso.

```bash
gerard@umbra:~/services/ca$ openssl genrsa -out ${DOMAIN}.key 2048
Generating RSA private key, 2048 bit long modulus
.....................................................................+++++
.................................+++++
e is 65537 (0x010001)
gerard@umbra:~/services/ca$ 
```

Teniendo la clave, necesitamos hacer una petición de firma (CSR). Esta será firmada
por el certificado raíz para generar el certificado final, y nuevamente podemos
reciclar el fichero tanto como queramos, incluso irlo firmando de nuevo cuando
el certificado generado caduque, sin cambiar el CSR.

```bash
gerard@umbra:~/services/ca$ openssl req -new -sha256 -out ${DOMAIN}.csr -key ${DOMAIN}.key -subj "/CN=${DOMAIN}"
gerard@umbra:~/services/ca$ 
```

**TRUCO**: El campo `CN` debe coincidir con el nombre de dominio, o será rechazado por
cualquiera que intente verificar el certificado mostrado, sea un navegador o una librería.

El firmado es el proceso en el que un CSR se convierte en un certificado correcto.
La firma es una operación caduca, que dura según se lo indiquemos en el parámetro
`-days`; transcurrido ese periodo, la validación fallará siempre, hasta que firmemos
otra vez el CSR (o una nuevo), creando un nuevo certificado en el proceso.

```bash
gerard@umbra:~/services/ca$ sed "s/%%DOMAIN%%/${DOMAIN}/" v3.ext.tpl > v3.ext
gerard@umbra:~/services/ca$ openssl x509 -sha256 -CA ca.crt -CAkey ca.key -req -in ${DOMAIN}.csr -days 365 -CAcreateserial -out ${DOMAIN}.crt -extfile v3.ext
Signature ok
subject=CN = web.local
Getting CA Private Key
gerard@umbra:~/services/ca$ rm v3.ext
gerard@umbra:~/services/ca$ 
```

**TRUCO**: Fijáos en el uso de `sed` para crear el fichero `v3.ext` a partir de
la plantilla que creamos en `v3.ext.tpl`. Luego lo usamos y lo limpiamos.

En este punto tenemos 3 ficheros: `web.local.key`, `web.local.csr` y `web.local.crt`.
Los conservaremos todos porque la clave y el CSR nos pueden servir en un futuro,
y la clave y el certificado se necesitan para su uso en los servicios SSL. No hace
falta ser muy conservador tampoco; los podemos volver a crear cuando queramos.

## Usando los certificados creados

Todos los servicios que necesiten certificados, necesitan también la clave. Hay
algunas variaciones en el formato de los ficheros de certificados; indico como
van en los dos servicios SSL más usados en este *blog*:

* **nginx** &rarr; La configuración de un dominio SSL utiliza ambos ficheros tal como los tenemos.
* **haproxy** &rarr; Los ficheros de certificados se concatenan en uno solo, juntando la clave y el certificado.

Una configuración de **nginx** para un sitio estático HTTPS podría ser la siguiente:

```bash
server {
    server_name web.local;

    listen 443 ssl;
    ssl_certificate /run/secrets/web.local.crt;
    ssl_certificate_key /run/secrets/web.local.key;

    root /srv/www;
    index index.html;
    error_page 404 /404.html;

    location /404.html {
        internal;
    }
}
```

**NOTA**: Para los que no lo sospechen, la configuración anterior se utiliza en
un contenedor **docker** usando [secretos y configuraciones][1].

Si hacemos una petición al dominio anterior, veremos que falla: el certificado
`web.local` falla la verificación sin más motivos ni errores que el fallo del
certificado *issuer*, que es el intermedio, del que no confía.

```bash
gerard@umbra:~/services/webserver$ curl https://web.local/
curl: (60) SSL certificate problem: unable to get local issuer certificate
More details here: https://curl.haxx.se/docs/sslcerts.html

curl performs SSL certificate verification by default, using a "bundle"
 of Certificate Authority (CA) public keys (CA certs). If the default
 bundle file isn't adequate, you can specify an alternate file
 using the --cacert option.
If this HTTPS server uses a certificate signed by a CA represented in
 the bundle, the certificate verification probably failed due to a
 problem with the certificate (it might be expired, or the name might
 not match the domain name in the URL).
If you'd like to turn off curl's verification of the certificate, use
 the -k (or --insecure) option.
gerard@umbra:~/services/webserver$ 
```

Vamos a ver algunos detalles, ignorando la verificación:

```bash
gerard@umbra:~/services/webserver$ curl -svk https://web.local/ 2>&1 | egrep "Host|CN=|h1"
*  subject: CN=web.local
*  issuer: CN=LinuxSysadmin CA
> Host: web.local
<h1>Hello world!</h1>
gerard@umbra:~/services/webserver$ 
```

Podemos comprobar que estamos solicitando el `Host: web.local`, y se nos presenta
el certificado de `CN=web.local`, que está firmado por el *issuer*, que es
el certificado `CN=LinuxSysadmin CA` (en el que no confiamos todavía). Por lo
demás, todo parece correcto.

## Confiando en el certificado de nuestra CA

Ahora nos urge indicar al cliente HTTPS indicar que debe confiar en el certificado
intermedio, que el el que llamamos `ca.crt`, y que deberemos distribuir adecuadamente.

### Usando curl

Las peticiones `curl` aceptan un parámetro indicando un certificado de confianza.
Podemos poner directamente el de `web.local` o el intermedio, que es el objetivo:

```bash
gerard@umbra:~/services$ curl -v --cacert ca/ca.crt https://web.local/
...
* Server certificate:
*  subject: CN=web.local
...
*  subjectAltName: host "web.local" matched cert's "web.local"
*  issuer: CN=LinuxSysadmin CA
*  SSL certificate verify ok.
...
<h1>Hello world!</h1>
...
gerard@umbra:~/services$ 
```

### Usando python

Si estamos protegiendo por HTTPS un servicio REST, la idea es que el consumidor
sea el que confíe en el certificado de la CA. Esto es dependiente de cada librería,
aunque voy a poner un ejemplo con **python-requests** que es la que utilizo casi
siempre, por su excelente documentación y facilidad de uso.

```bash
gerard@umbra:~/services$ python3
...
>>> import requests
>>> 
```

Si el certificado no está aceptado, obtenemos una excepción:

```bash
>>> r = requests.get('https://web.local/')
Traceback (most recent call last):
...
ssl.SSLError: [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed (_ssl.c:720)
...
requests.exceptions.SSLError: HTTPSConnectionPool(host='web.local', port=443): Max retries exceeded with url: / (Caused by SSLError(SSLError(1, '[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed (_ssl.c:720)'),))
>>> 
```

Podemos optar por ignorar el certificado completamente, pero no se recomienda:

```bash
>>> r = requests.get('https://web.local/', verify=False)
/home/gerard/services/env/lib/python3.5/site-packages/urllib3/connectionpool.py:1004: InsecureRequestWarning: Unverified HTTPS request is being made. Adding certificate verification is strongly advised. See: https://urllib3.readthedocs.io/en/latest/advanced-usage.html#ssl-warnings
  InsecureRequestWarning,
>>> r.text
'<h1>Hello world!</h1>\n'
>>> 
```

Si embargo, podemos indicar el certificado final o el intermedio en el parámetro
`verify`, lo que causa plena confianza con el certificado de la CA. Nuevamente
indico que necesitaremos tener el certificado (que no la clave), en un fichero local.

```bash
>>> r = requests.get('https://web.local/', verify='ca/ca.crt')
>>> r.text
'<h1>Hello world!</h1>\n'
>>> 
```

### Usando un navegador

Los navegadores tienen una forma peculiar de aceptar nuevas autoridades certificadoras.
Cada uno es un mundo, pero por lo general suelen tener un apartado de configuración,
en donde podemos importar certificados (en nuestro caso, el `ca.crt`).

En este ordenador, tengo **chromium**, y llego a esta configuración si voy a la URL
`chrome://settings/certificates`. Basta con ir a la pestaña "Authorities" y darle
al botón de "Import". Tras importar el certificado, aparece en la lista, en donde
lo podéis ver, examinar o eliminar cuando os convenga.

**NOTA**: El navegador guarda el certificado, con lo que no necesitamos repetir
este paso nunca más, a menos que cambiemos el certificado o lo hayamos borrado
del navegador en una acción manual (o reinstalemos el navegador).

De ahora en adelante (y hasta la eliminación), los certificados firmados por nuestra
CA, van a ser aceptados como seguros, sin ningún tipo de problema por parte de
**este navegador concreto**. Para el resto de navegadores, buscad en la web.

## Siguientes pasos

Nuestros certificados van a caducar pasado el tiempo de vigencia. Si se han seguido
los comandos indicados, el certificado de la CA va a caducar en 10 años (y va a haber
que redistribuirlo o importarlo en el navegador), y los certificados finales van a
caducar en 1 año. Eso significa que vamos a tener que volver a recrear el certificado
de la CA y refirmar un CSR para cada dominio (que puede ser el mismo) cada cierto tiempo.

Por supuesto, si añadimos más dominios a nuestro servidor web, *proxy* o balanceador,
vamos a tener que generar nuevos certificados, con sus claves y CSRs. Eso no entraña
ningúna dificultad y, como confiamos en el certificado de la CA que los firma, no va
a haber que añadir más excepciones al navegador ni a nuestro código consumidor.

Eso convierte en el paso intermedio de crear una CA en una herramienta cómoda; añade
un poco de complejidad a nuestro algoritmo de generación de certificados, pero a la
larga nos libera de muchos pasos relacionados con la confianza de los certificados.
Si tenemos una estrategia centralizada de distribución del certificado de la CA, los
usuarios de nuestra organización ni siquiera se van a enterar del engaño...

[1]: {{< relref "/articles/2019/06/distribuyendo-contenido-en-docker-swarm-configuraciones-y-secretos.md" >}}
