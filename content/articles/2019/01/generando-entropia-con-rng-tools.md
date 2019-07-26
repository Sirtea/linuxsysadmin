---
title: "Generando entropía con rng-tools"
slug: "generando-entropia-con-rng-tools"
date: 2019-01-28
categories: ['Sistemas']
tags: ['gpg', 'entropía', 'rng-tools']
---

Cada vez que intento crear claves GPG me doy por vencido y paso de hacerlo. El motivo es que es un proceso que tarda una barbaridad, especialmente en los entornos virtuales por los que me suelo mover. Eso es porque el dispositivo `/dev/random` no recibe suficiente aleatoriedad sin ayuda.<!--more-->

Pero esto ha cambiado últimamente; he descubierto un servicio capaz de generar entropía suficiente para que el generador del sistema `/dev/random` se llene rápidamente. Se trata de **rng-tools** y su existencia ha simplificado la mía notablemente.

Normalmente utilizo el otro generador del sistema `/dev/urandom`, que genera números pseudoaleatorios en función de un algoritmo matemático. Esto es suficiente para mí, pero para algunas herramientas del sistema es insuficiente, y por ello utilizan números puramente aleatorios.

## El problema

Vamos a generar una clave GPG para un uso cualquiera; esto es ahora irrelevante. Lanzamos el comando adecuado y vemos la sugerencia:

```bash
gerard@shangrila:~/workspace$ gpg --gen-key
gpg (GnuPG) 2.1.18; Copyright (C) 2017 Free Software Foundation, Inc.
This is free software: you are free to change and redistribute it.
There is NO WARRANTY, to the extent permitted by law.

Note: Use "gpg --full-generate-key" for a full featured key generation dialog.

GnuPG needs to construct a user ID to identify your key.

Real name: Gerard Monells
Email address: gerard.monells@gmail.com
You selected this USER-ID:
    "Gerard Monells <gerard.monells@gmail.com>"

Change (N)ame, (E)mail, or (O)kay/(Q)uit? o
We need to generate a lot of random bytes. It is a good idea to perform
some other action (type on the keyboard, move the mouse, utilize the
disks) during the prime generation; this gives the random number
generator a better chance to gain enough entropy.
...
```

Al final, tras más de 1 hora esperando, nos cansamos de esperar y cancelamos la generación de la clave.

## La solución

Por defecto, `/dev/random` es muy lento, porque recoge entropía de los *drivers* de los dispositivos y de otras fuentes lentas. El binario **rngd** permite usar fuentes de entropía más rápidas, principalmente generadores de números aleatorios por *hardware*, presentes en los procesadores modernos, por ejemplo, los procesadores AMD, los Intel, e incluso los ARM de las *Raspberry pi*.

Aunque nuestro servidor virtual no tenga acceso a tales dispositivos, no son las únicas fuentes; nos vamos a beneficiar de una generación de números aleatorios mayor aunque nos los tengamos. Para ello, solo necesitamos tener instalado el paquete **rng-tools** y el binario `rngd` ejecutando.

```bash
gerard@shangrila:~/workspace$ sudo apt install rng-tools
...
gerard@shangrila:~/workspace$
```

Si no queréis ensuciar el sistema operativo, podéis ejecutarlo en un contenedor **docker**; como comparten *kernel*, el contenedor generará entropía para todo el que comparta el mismo *kernel*, incluído el sistema *host*.

En el caso de **docker**, solo hace falta recordar que el binario debe correr en *foreground* y que necesita ejecutar con el *flag* `--privileged`, para poder acceder a los recursos del *kernel* compartido con el resto de contenedores.

Aquí os dejo mi receta:

```bash
gerard@shangrila:~/workspace/rngtools$ cat Dockerfile
FROM alpine:3.8
RUN apk add --no-cache tini rng-tools
ENTRYPOINT ["/sbin/tini", "--"]
CMD ["/usr/sbin/rngd", "-f"]
gerard@shangrila:~/workspace/rngtools$
```

```bash
gerard@shangrila:~/workspace/rngtools$ docker build -t rngtools .
Sending build context to Docker daemon  2.048kB
...
Successfully built 0b89a6d118ca
Successfully tagged rngtools:latest
gerard@shangrila:~/workspace/rngtools$
```

Y lo ejecutamos cada vez que necesitemos más entropía:

```bash
gerard@shangrila:~/workspace/rngtools$ docker run -ti --rm --privileged rngtools
Failed to init entropy source 0: Hardware RNG Device

Failed to init entropy source 1: TPM RNG Device
```

Esto es normal, porque no tenemos dispositivos *hardware* especiales, pero aún así, nos podemos beneficiar de la entropía generada.

```bash
gerard@shangrila:~/workspace$ gpg --gen-key
gpg (GnuPG) 2.1.18; Copyright (C) 2017 Free Software Foundation, Inc.
This is free software: you are free to change and redistribute it.
There is NO WARRANTY, to the extent permitted by law.

Note: Use "gpg --full-generate-key" for a full featured key generation dialog.

GnuPG needs to construct a user ID to identify your key.

Real name: Gerard Monells
Email address: gerard.monells@gmail.com
You selected this USER-ID:
    "Gerard Monells <gerard.monells@gmail.com>"

Change (N)ame, (E)mail, or (O)kay/(Q)uit? o
We need to generate a lot of random bytes. It is a good idea to perform
some other action (type on the keyboard, move the mouse, utilize the
disks) during the prime generation; this gives the random number
generator a better chance to gain enough entropy.
We need to generate a lot of random bytes. It is a good idea to perform
some other action (type on the keyboard, move the mouse, utilize the
disks) during the prime generation; this gives the random number
generator a better chance to gain enough entropy.
gpg: key 14C7309FFCC0D402 marked as ultimately trusted
gpg: directory '/home/gerard/.gnupg/openpgp-revocs.d' created
gpg: revocation certificate stored as '/home/gerard/.gnupg/openpgp-revocs.d/2AD87663273458D451D2E68114C7309FFCC0D402.rev'
public and secret key created and signed.

pub   rsa3072 2019-01-10 [SC] [expires: 2021-01-09]
      2AD87663273458D451D2E68114C7309FFCC0D402
      2AD87663273458D451D2E68114C7309FFCC0D402
uid                      Gerard Monells <gerard.monells@gmail.com>
sub   rsa3072 2019-01-10 [E] [expires: 2021-01-09]

gerard@shangrila:~/workspace$
```

Y con esto tenemos nuestra clave generada de forma rápida.
