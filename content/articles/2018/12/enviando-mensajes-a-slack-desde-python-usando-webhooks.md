---
title: "Enviando mensajes a slack desde python usando webhooks"
slug: "enviando-mensajes-a-slack-desde-python-usando-webhooks"
date: 2018-12-10
categories: ['Desarrollo']
tags: ['python', 'slack', 'webhooks']
---

Cuando hablamos de equipos distribuidos por diferentes puntos geográficos, se necesitan herramientas de comunicación adecuadas; en nuestro equipo utilizamos **Slack**. Con el auge de palabras como **chatops** y otras tendencias, se hace muy interesante que nuestros sistemas puedan notificar mensajes en la misma herramienta que todo el equipo está mirando.<!--more-->

En el caso concreto de **Slack**, podemos encontrar muchos añadidos en forma de "Apps"; estas nos van a dar muchas herramientas de gran utilidad, y una de las que más me gusta es la de **webhooks**.

Los **webhooks** son URLs a las que podemos mandar mensajes con una forma concreta, para que acaben mostrándose en el canal conveniente de **Slack**, de una forma sencilla.

Seguramente ya existen librerías que hagan esa funcionalidad, pero en este artículo se va a mostrar la petición mediante el uso directo de HTTP, para ver lo sencillo que es y no ensuciar los entornos con librerías "no principales" para nuestro servicio.

El único requisito que necesitamos en **Slack** es el de activar la aplicación **Incoming webhooks**, que se puede encontrar siguiendo el panel de conversaciones, en el lateral izquierdo:

> Aplicaciones -> WebHooks entrantes -> Añadir configuración

El resultado es que nos va a dar una **URL de Webhook**, que es algo del estilo <https://hooks.slack.com/services/XXX/YYY/ZZZ>; no necesitamos nada más.

Para la parte de envío, solo se necesita hacer una petición POST al **webhook**, con un mensaje muy concreto. Más información [en la documentación](https://api.slack.com/incoming-webhooks).

El *script* no puede ser más sencillo; solo he usado la librería **requests** para aumentar la legibilidad del código, aunque la **httplib** también serviría y está en la librería estándar de **python**.

```bash
(.env) gerard@atlantis:~/workspace/slack_webhook$ cat requirements.txt
requests==2.20.1
(.env) gerard@atlantis:~/workspace/slack_webhook$
```

```bash
(.env) gerard@atlantis:~/workspace/slack_webhook$ cat send_slack_message.py
#!/usr/bin/env python3

import requests
import json

SLACK_WEBHOOK = 'https://hooks.slack.com/services/XXX/YYY/ZZZ'
SLACK_CHANNEL = '#notificaciones'
SLACK_USERNAME = 'Server Atlantis'

def send_slack_message(text):
    payload = {
        'channel': SLACK_CHANNEL,
        'username': SLACK_USERNAME,
        'text': text,
    }
    r = requests.post(SLACK_WEBHOOK, data=json.dumps(payload))

send_slack_message('Hello world')
(.env) gerard@atlantis:~/workspace/slack_webhook$
```

Solo hace falta que alguien o algo lance el *script*, que posiblemente acabará siendo parametrizado para un uso más útil... De momento lo haremos a mano, solo para verificar que funciona.

```bash
(.env) gerard@atlantis:~/workspace/slack_webhook$ ./send_slack_message.py
(.env) gerard@atlantis:~/workspace/slack_webhook$
```

Y con esto tenemos nuestro nuevo mensaje en el canal de grupo "#notificaciones", que es el que indicamos cuando creamos el **webhook**.

Personalmente utilizo esto para tener informes de funcionamiento periódicos en un **cron**, o alguna monitorización temporal especial para seguir algún *bug*.
