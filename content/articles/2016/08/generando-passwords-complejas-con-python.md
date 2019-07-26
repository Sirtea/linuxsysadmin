---
title: "Generando passwords complejas con python"
slug: "generando-passwords-complejas-con-python"
date: 2016-08-22
categories: ['Operaciones']
tags: ['password', 'python', 'seguridad']
---

Todos hemos trabajado en empresas que tienen curiosas políticas de seguridad. La cosa es mas cierta en la generación de *passwords*, cuando te piden mayúsculas, minúsculas, dígitos y otros símbolos arcanos. Cuando los administradores tenemos que asignarlas a miles, ya no es divertido y tenemos que generarlas de forma automática.<!--more-->

Así pues, y harto de hacerlo, hice un *script* con **python** que me asegure que se cumple con todas las restricciones reinantes.

Supongamos que tenemos que generar *passwords* de 12 caracteres, con al menos una mayúscula, una minúscula, un dígito y un otro símbolo.

El truco es simple: vamos a poner un carácter de cada tipo de los requeridos, y el resto los vamos a poner del alfabeto completo. Luego solo hay que desordenar el conjunto. Para ello, hay algunas cosas que hay que saber en **python**:

* Tenemos métodos para desordenar *arrays*, pero no *strings*.
* Disponemos de un método para elegir un elemento de un *array* o un carácter de un *string*.
* Podemos juntar un *array* en un *string*, mediante un separador, posiblemente vacío.

Así pues, vamos a declarar el alfabeto como *strings*, la *password* como un *array* de caracteres y finalmente vamos a sacar la *password* como un *string*, juntando los caracteres sin un separador.

Crearemos un *script* llamado *password.py*, con el siguiente contenido:

```python
#!/usr/bin/env python

import random

length = 12

lowercase = 'abcdefghijklmnopqrstuvwxyz'
uppercase = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
digits = '0123456789'
other = '-+_.,:;()'
all_chars = lowercase + uppercase + digits + other

password = []
password.append(random.choice(lowercase))
password.append(random.choice(uppercase))
password.append(random.choice(digits))
password.append(random.choice(other))
for i in xrange(length-4):
    password.append(random.choice(all_chars))

random.shuffle(password)
print ''.join(password)
```

Tras darle permisos de ejecución, solo nos queda generar *passwords* hasta que quedemos satisfechos.

```bash
gerard@sirius:~$ ./password.py 
pyLq:4CmfU2+
gerard@sirius:~$ ./password.py 
(_vM7ag5mobU
gerard@sirius:~$ ./password.py 
4OKDa+afcEm4
gerard@sirius:~$ ./password.py 
w_.T8QjnB4UD
gerard@sirius:~$ ./password.py 
8VxHFb+.9z5e
gerard@sirius:~$ ./password.py 
vl6bSctxHd+c
gerard@sirius:~$ 
```
