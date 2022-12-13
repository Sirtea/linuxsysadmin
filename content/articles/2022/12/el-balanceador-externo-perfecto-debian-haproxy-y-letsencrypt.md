---
title: "El balanceador externo perfecto: Debian, HAProxy y LetsEncrypt"
slug: "el-balanceador-externo-perfecto-debian-haproxy-y-letsencrypt"
date: "2022-12-13"
categories: ['Sistemas']
tags: ['debian', 'haproxy', 'letsencrypt', 'certificado', 'ssl']
---

Hace mucho tiempo que no reviso mi política de *hosting*. Tras la renovación
de alguno de mis servicios, decidí que era tiempo de recortar en gastos para
los más simples. Así pues, decidí moverme a un servicio de *hosting* de estos
que van por horas, con terminación SSL gratuita.<!--more-->

Y es que no es de recibo pagar un ojo de la cara por un certificado SSL si
nos vale con uno gratis renovable cada 3 meses; eso si, de forma automatizada,
porque no quiero tener que ir preocupándome de ello.

El combo es simple:

* Un servidor con un sistema operativo con el que nos sintamos cómodos. En mi caso, eso se traduce como **Debian** (concretamente **Debian Bullseye**, actual estable).
* Un balanceador por requisito de mi servicio. Nos vale cualquiera, pero me decanto por **HAProxy**; otras opciones incluirían **Nginx** o **Caddy**, pero voy a tirar por la solución 100% libre.
* Un certificado SSL generado por **Let's Encrypt** o una entidad similar. Como nunca había utilizado **Let's Encrypt**, me decanto por él; cosas de la curiosidad humana.

Hay muchos proveedores de VPS "por horas". Puedo mencionar algunos como
**DigitalOcean**, **Scaleway** o **Linode**. Sin embargo, en esta ocasión me
decanto por **Vultr** por sus instancias mínimas de 2,5 $ mensuales (en realidad
3,5 $, porque acabé abrazando la simplicidad de la dirección pública IPv4).

Esto no es un artículo de tutorial sobre este portal, así que vamos a asumir que
ya tenemos nuestro VPS aprovisionado y un registro DNS apuntando a su dirección
IP. Supongamos que el dominio es `www.example.com`.

Procedemos a instalar el **HAProxy** y el cliente de **Let's Encrypt** (que es
**certbot**). Hay muchos otros clientes, pero nos limitaremos a este por estar en
los repositorios oficiales.

```bash
root@balancer:~# apt install haproxy certbot
...
root@balancer:~#
```

El requisito imprescindible que vamos a imponer es que **no vamos a parar el
HAProxy bajo ninguna circunstancia**, para evitar *downtime* mientras se renueva
el certificado; solamente lo vamos a tocar para montarlo. De hecho, todo se
puede hacer con *reloads* de ahora en adelante.

## Generar el certificado

**WARNING**: Es un buen momento para asegurar que el puerto HTTP y HTTPS están
permitidos en nuestro firewall (tanto el del *hosting* como el del servidor).
En mi caso tenía instalado **ufw** y lo vi con `ufw status`. Me faltó ejecutar
un `ufw allow http` y `ufw allow https`.

La generación del certificado la vamos a hacer con el *HTTP challenge*, que
básicamente significa poner un fichero en nuestro servidor para que
**Let's Encrypt** pueda verificar que es de nuestra propiedad.

Sin embargo, **HAProxy** no es un servidor web. Necesitamos otro servidor web
al que se pueda llegar desde el exterior; por suerte, el mismo cliente de
**certbot** nos ofrece un servidor *standalone*. Como no podemos reemplazar el
**HAProxy**, solo necesitamos desviar una ruta concreta hacia el servidor
auxiliar (que levantaré en el puerto 8888).

```bash
root@balancer:~# cat /etc/haproxy/haproxy.cfg
...
frontend public
        bind :80
        use_backend letsencrypt if { path -m beg /.well-known/acme-challenge/ }
        ...
...
backend letsencrypt
        server letsencrypt 127.0.0.1:8888
...
root@balancer:~#
```

```bash
root@balancer:~# systemctl reload haproxy
root@balancer:~#
```

Ahora basta con la línea mágica (cambiad el dominio y el email):

```bash
root@balancer:~# certbot certonly --standalone -d <domain> --non-interactive --agree-tos --email <email> --http-01-port=8888
...
root@balancer:~#
```

En este momento, el servidor auxiliar se ha parado solo y tenemos los certificados
en `/etc/letsencrypt/live/<domain>/`. Específicamente nos interesan el `fullchain.pem`
y el `privkey.pem`, que en el caso de **HAProxy** deben ir juntos, por ejemplo,
en `/etc/haproxy/certs/`.

```bash
root@balancer:~# mkdir /etc/haproxy/certs
root@balancer:~#
```

```bash
root@balancer:~# cat /etc/letsencrypt/live/<domain>/{fullchain,privkey}.pem > /etc/haproxy/certs/<domain>.pem
root@balancer:~#
```

Vamos a poner la configuración relevante en el **HAProxy** para servir HTTPS:

```bash
root@balancer:~# cat /etc/haproxy/haproxy.cfg
...
frontend public
        bind :80
        bind :443 ssl crt /etc/haproxy/certs/<domain>.pem
        http-request redirect scheme https code 301 unless { ssl_fc }
        use_backend letsencrypt if { path -m beg /.well-known/acme-challenge/ }
...
root@balancer:~#
```

```bash
root@balancer:~# systemctl reload haproxy
root@balancer:~#
```

Y con esto ya tenemos HTTPS.

## Renovar el certificado

Otra cosa que nos dejó la ejecución de **certbot** es la configuración de
los parámetros con los que lo ejecutamos:

```bash
root@balancer:~# cat /etc/letsencrypt/renewal/<domain>.conf
# renew_before_expiry = 30 days
version = 1.12.0
archive_dir = /etc/letsencrypt/archive/<domain>
cert = /etc/letsencrypt/live/<domain>/cert.pem
privkey = /etc/letsencrypt/live/<domain>/privkey.pem
chain = /etc/letsencrypt/live/<domain>/chain.pem
fullchain = /etc/letsencrypt/live/<domain>/fullchain.pem

# Options used in the renewal process
[renewalparams]
account = <secret>
http01_port = 8888
authenticator = standalone
server = https://acme-v02.api.letsencrypt.org/directory
root@balancer:~#
```

Esto nos permite ejecutar el comando `certbot renew` sin añadir nada nuevo
(podemos evitar ejecutar cambios con el *flag* `--dry-run`).

```bash
root@balancer:~# certbot renew --dry-run
...
Cert not due for renewal, but simulating renewal for dry run
...
Congratulations, all simulated renewals succeeded:
  /etc/letsencrypt/live/<domain>/fullchain.pem (success)
...
root@balancer:~#
```

Hay que tener en cuenta algunos detalles:

* El cliente **certbot** no actualiza los servidores hasta que no faltan 30 días para su renovación, así que no habríamos cambiado nada. Eso significa que podemos ejecutar la renovación tan a menudo como queramos.
* La renovación funcionó, aunque nos quedaría juntar el certificado en `/etc/haproxy/certs/` y hacer un `systemctl reload haproxy` para que se apliquen.
* El comando de renovación levanta el servidor *standalone* para la renovación, pero lo para inmediatamente después; eso significa que no necesitamos "mantener vivo" dicho servidor con un servicio de sistema operativo.

Para no tener que ejecutar nada manualmente, **certbot** nos ofrece los *hooks*
que son comandos que se ejecutan durante la renovación, sea antes, después o si
hay cambios de certificados. Se pueden dar como parámetros a la ejecución de
`certbot renew`, o ser *scripts* en las carpetas adecuadas:

```bash
root@balancer:~# tree /etc/letsencrypt/renewal-hooks/
/etc/letsencrypt/renewal-hooks/
├── deploy
├── post
└── pre

3 directories, 0 files
root@balancer:~#
```

Dejamos un *script* en la carpeta `deploy`, que es la que contiene los *hooks* que
se ejecutan **si algún certificado se renueva**. Usamos los mismos comandos que antes:

```bash
root@balancer:~# cat /etc/letsencrypt/renewal-hooks/deploy/haproxy
#!/bin/bash

SITE="<domain>"

cat /etc/letsencrypt/live/${SITE}/{fullchain,privkey}.pem > /etc/haproxy/certs/${SITE}.pem
systemctl reload haproxy
root@balancer:~#
```

```bash
root@balancer:~# chmod 755 /etc/letsencrypt/renewal-hooks/deploy/haproxy
root@balancer:~#
```

La renovación corre a cargo de un *timer* de **systemd**, que lo hace 2 veces al
día (recordad que solo renovará si al certificado le quedan 30 días o menos para
caducar, así que es seguro). Este *timer* quedó creado al instalar el paquete
**certbot**; nuevamente, no tenemos nada que hacer.

```bash
root@balancer:~# cat /usr/lib/systemd/system/certbot.timer
...
OnCalendar=*-*-* 00,12:00:00
...
root@balancer:~#
```

```bash
root@balancer:~# cat /usr/lib/systemd/system/certbot.service
...
ExecStart=/usr/bin/certbot -q renew
...
root@balancer:~#
```

## Verificando nuestro setup SSL

Si vamos a `www.example.com` (nuestro dominio) podemos ver el candado al
lado de la barra de direcciones. No tiene colores, porque el certificado
de **Let's Encrypt** es básico, pero veremos que la conexión es segura
y el certificado es confiable.

Para más nota, podemos analizar nuestro sitio en [Qualys SSL Labs][1].
Un análisis en este momento nos va a dar directamente la nota "A".
Podemos conseguir una nota "A+" fácilmente añadiendo la cabecera HSTS
(Strict-Transport-Security).

```bash
root@balancer:~# cat /etc/haproxy/haproxy.cfg
...
frontend public
        bind :80
        bind :443 ssl crt /etc/haproxy/certs/<domain>.pem alpn h2,http/1.1
        http-request redirect scheme https code 301 unless { ssl_fc }
        http-response set-header Strict-Transport-Security max-age=63072000
        use_backend letsencrypt if { path -m beg /.well-known/acme-challenge/ }
...
root@balancer:~#
```

```bash
root@balancer:~# systemctl reload haproxy
root@balancer:~#
```

La configuración del **HAProxy** solo añade una línea más (la del
`http-response set-header`); aunque por convicción personal modifico
otra (la del `bind :443 ssl`), para que el balanceador acepte HTTP/2.

[1]: https://www.ssllabs.com/ssltest/
