---
title: "Un entorno productivo basado en Docker Swarm (I)"
slug: "un-entorno-productivo-basado-en-docker-swarm"
date: "2019-09-16"
categories: ['Sistemas']
tags: ['linux', 'entorno', 'docker', 'swarm']
series: "Un entorno productivo basado en Docker Swarm"
---

Hace tiempo trabajé en una compañía que tenía un entorno productivo basado en **docker**.
Fueron de los primeros en adoptar **docker** y no utilizaban ninguna tecnología
de *clusterización*. Los contenedores se ponían en alguna máquina con capacidad adecuada;
los balanceadores y las bases de datos tenían máquinas dedicadas.<!--more-->

La idea no estaba mal y se administraba el entorno mediante *playbooks* de **ansible**.
Mirando atrás con cierta nostalgia, y viendo como ha evolucionado la tecnología de
contenedores, se me ocurrió la idea de recrear algo parecido basado en **docker swarm**.

En este artículo pretendo mostrar como utilizar **docker swarm** para alojar un
entorno clásico web, desde la infraestructura (máquinas y *firewall*) hasta los servicios
que en ellos vamos a desplegar (aplicaciones y bases de datos). Para no alargar el
artículo, voy a crear un subconjunto mínimo desde el que se puede ir creciendo:

* Una red privada con sus servidores y su *gateway*
* Un *cluster* de **docker swarm** que gestione los servicios
* Los servicios que se ejecutan en el *swarm*
    * El balanceador de carga
    * El *cluster* de base de datos
    * Las diferentes aplicaciones a desplegar

**NOTA**: Para virtualizar todas estas máquinas se va a utilizar **Oracle VirtualBox**
porque es lo que tengo a mano, pero es bastante fácil adaptarlo para utilizar cualquier
otro proveedor de máquinas virtuales, local o *cloud*. Solo hay que saber como crear
servidores y como se comunican entre sí.

En cuanto a tecnologías utilizadas, van a ser las que venimos viendo en el *blog*, que son
aquellas con las que me siento cómodo; esto no quita que podáis adaptar lo aprendido a
vuestras preferencias particulares. También he decidido que todos los servicios van a ser
gestionados por **docker swarm**, restringiendo la administración desde un solo punto
(que puede ser cualquiera de los *managers* del *swarm*), y añadiendo una capa de autoreparación.

Para ser un poco más concretos, vamos a utilizar las siguientes tecnologías:

* Infraestructura basada en **debian buster**, que es la actual versión estable
* *Gateway* hecho con **shorewall** y **dnsmasq**, con funciones de *firewall*
* Un *cluster* tipo *replica set* de **mongodb**, con autenticación habilitada
* Balanceadores **traefik** con una IP flotante, compartida mediante **keepalived**
* Aplicaciones de ejemplo escritas en **python** y ejecutadas en **gunicorn**

**NOTA**: Todas estas partes se comunican mediante protocolos estándares; eso las
hace fácilmente reemplazables por otras tecnologías, según vuestras preferencias
particulares; me comprometo a utilizar nombres de servicios genéricos donde sea factible.
