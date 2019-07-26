---
title: "Escribiendo bots para Telegram"
slug: "escribiendo-bots-para-telegram"
date: 2016-08-08
categories: ['Desarrollo']
tags: ['telegram', 'bots', 'python']
---

Aunque no está muy extendido, **Telegram** es un magnífico cliente de mensajería instantánea. Tiene varios puntos a favor, como por ejemplo seguridad, rapidez y su condición de *libre*. Lo que no se conoce tanto es que dispone de una *API* para crear *bots* que pueden responder automáticamente a sus usuarios.<!--more-->

La variedad de usos que se dan mediante estos *bots* es muy variada. Personalmente he visto juegos, asistentes virtuales e incluso lo he usado para tener a mano las alarmas de un entorno de producción.

## El token

Nuestro *bot* es un ente propio, que tiene un *token* de autenticación, de forma que solamente el que posea el *token* pude responder como si fuera el *bot*.

Para conseguir el *token* tenemos que iniciar una conversación con **@BotFather**, que es el *bot* que gobierna al resto. La interfaz es muy simple, y vale la pena de explorar; de momento me limito a resumir los comandos necesarios:

1. Iniciamos una conversación con **BotFather** mediante el comando */start*.
2. Le indicamos que queremos un nuevo *bot* mediante el comando */newbot*.
3. Le damos un nombre y un *username*, tal como nos lo pide.
4. El último paso es anotar el *token* que nos ofrece **BotFather**.

Esto es todo lo que necesitamos para empezar a responder mensajes. Las conversaciones con el *bot* se pueden iniciar buscando al *bot* por su nombre o su *username*. Obviamente, no tenemos nada todavía que responda a los *chats* que se hagan a este nuevo *bot*.

Hay dos formas de responder a este *bot*:

* Lo podemos configurar para que llame directamente a un *endpoint* protegido con *HTTPS* (requiere un certificado válido no autofirmado).
* Podemos tener un programa preguntando por nuevos mensajes periódicamente.

Como no tengo un servidor *HTTPS* con certificado adecuado, vamos a ir por la segunda opción.

## El script de respuesta

Vamos a escribir el *script* en **python** por su simplicidad y facilidad. Realmente se podría hacer con cualquier lenguaje, ya que se trata de hacer peticiones web a la *API* e interpretarlas.

Empezaremos por instalar una librería que nos va a facilitar bastante entender las peticiones y crear las respuestas. Lo vamos a hacer en un *virtualenv* por limpieza.

```bash
gerard@sirius:~/projects/telebot$ virtualenv env
New python executable in /home/gerard/projects/telebot/env/bin/python
Installing setuptools, pip, wheel...done.
gerard@sirius:~/projects/telebot$ . env/bin/activate
(env) gerard@sirius:~/projects/telebot$ pip install python-telegram-bot
Collecting python-telegram-bot
  Downloading python_telegram_bot-4.3.3-py2.py3-none-any.whl (122kB)
    100% |████████████████████████████████| 122kB 471kB/s 
Collecting certifi (from python-telegram-bot)
  Downloading certifi-2016.2.28-py2.py3-none-any.whl (366kB)
    100% |████████████████████████████████| 368kB 514kB/s 
Collecting urllib3>=1.10 (from python-telegram-bot)
  Downloading urllib3-1.16-py2.py3-none-any.whl (98kB)
    100% |████████████████████████████████| 102kB 901kB/s 
Collecting future>=0.15.2 (from python-telegram-bot)
Installing collected packages: certifi, urllib3, future, python-telegram-bot
Successfully installed certifi-2016.2.28 future-0.15.2 python-telegram-bot-4.3.3 urllib3-1.16
(env) gerard@sirius:~/projects/telebot$ 
```

Realmente no hay mucho misterio; siguiendo la documentación se saca rápidamente un *script*, al que llamaremos *run.py*.

```python
#!/usr/bin/env python

import telegram

bot = telegram.Bot(token='190363978:AAG0bHpIbidczVYUPhW9UwrwG3n5s54XSlE')
print bot.getMe()

def process_update(update):
    request, response = update.message.text, 'unknown'
    if request.upper().startswith('UPPER '):
        response = request[6:].upper()
    params = {
        'chat_id': update.message.chat_id,
        'text': '*Response*: ' + response,
        'parse_mode': 'Markdown',
    }
    bot.sendMessage(**params)

last_update = None
while True:
    if last_update is None:
        updates = bot.getUpdates(timeout=10)
    else:
        updates = bot.getUpdates(offset=last_update+1, timeout=10)
    for update in updates:
        process_update(update)
        last_update = update.update_id
```

El *script* es relativamente fácil de entender, así que solo os dejo algunas reflexiones:

* El *token* usado en *telegram.Bot()* es el que nos dio el **BotFather** (ha sido destruido, así que no penséis en vandalizar).
* Los *update_id* son secuenciales; sin embargo, varias lecturas a la *API* nos vuelven a traer todos los mensajes. La forma de que no nos los vuelva a dar es especificando un parámetro *offset* (aunque en la primera iteración no lo tenemos).
* Se ha decidido por procesar cada *update* en una función aparte, ya que cada *bot* hará algo diferente con ellos.
* Este *bot* de prueba solo va a devolvernos el mensaje que le pasemos en mayúsculas, y solo si este empieza por "UPPER". El resto devuelve "unknown".
* Las respuestas pueden contener lenguaje *wiki*, en este caso, **markdown**; pueden también definir teclados a medida con las respuestas posibles.
* Las respuestas conocen a su receptor mediante el campo *chat_id*. Este campo se puede ver como un indicador de sesión, si vuestro *bot* mantiene el estado de un "jugador" concreto.

La verdad es que es bastante simple la interfaz de la *API*.  Con un poco de imaginación y una base de datos, es muy posible hacer un juego conversacional, sea con campos en la base de datos, o mediante una máquina de estados simple. Me quedo con esa idea para el futuro.
