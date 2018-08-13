Title: Verificando contraseñas manualmente en Linux
Slug: verificando-contrasenas-manualmente-en-linux
Date: 2018-08-20 10:00
Category: Seguridad
Tags: password, shadow



El otro día recibí una petición inusual; un usuario no se acordaba de su contraseña y quería que se la descifrara de los ficheros de sistema. Como eso no es factible, y tras mi negativa, él me dijo que no sabía si era una de una lista, lo que comprobé.

Las contraseñas en **Linux** no se guardan; lo que se guarda es un *hash* de las mismas en el fichero `/etc/shadow`, y para verificarlas solo hay que hacer el mismo procedimiento de *hash*, para luego comparar los resultados.

## Un ejemplo

El usuario **zeus** ha perdido su contraseña y por lo tanto no puede acceder a **olympus**. Como administrador, puedo ver lo que hay en `/etc/shadow`:

```bash
root@olympus:~# grep zeus /etc/shadow
zeus:$6$jq62gTbU$kYZgWuKLuNTX0Ur.UWiuBJuIYltW3hc7EdI2/4RpldwUoLlRl9IdXgJb6B3kxEoAxWolDwXDCqOnz8SN0CKkJ1:17739:0:99999:7:::
root@olympus:~#
```

Los campos se separan por `:`; el primer campo es el usuario y el segundo, el *hash* de su password. Este *hash* tiene la forma `$id$salt$hashed`, y cada parte significa algo:

* `6` &rarr; es algoritmo usado para el *hash*, donde "6" significa **SHA-512**.
* `jq62gTbU` &rarr; el algoritmo **SHA-512** requiere de un *salt* para combinar con la contraseña antes del *hash*, por seguridad.
* `kYZgWuKLuNTX0Ur.UWiuBJuIYltW3hc7EdI2/4RpldwUoLlRl9IdXgJb6B3kxEoAxWolDwXDCqOnz8SN0CKkJ1` &rarr; este es el *hash* propiamente dicho.

**NOTA**: Más información [aquí](https://www.cyberciti.biz/faq/understanding-etcshadow-file/).

Sabiendo el algoritmo y el *salt*, podemos hacer el *hash* de cualquier contraseña. En caso de que el *hash* sea el mismo que tenemos guardado, **Linux** asume la contraseña como válida. Es importante recalcar que dos *salt* distintos darían dos *hash* distintos.

Podemos probar con la contraseña `temporal`:

```python
>>> import crypt
>>> crypt.crypt('temporal', '$6$jq62gTbU')
'$6$jq62gTbU$Zr/CBQAIKhWu1wCIE/jP0okICiaCQrw.eUBl4f9fQjgyCcLzkGB0dqfE8sM4tB1YG/DtLtaompXqvIrpPlErn1'
>>>
```

No nos cuadra con el ejemplo, con lo que contraseña sería rechazada. Probemos ahora con `supersecret`:

```python
>>> import crypt
>>> crypt.crypt('supersecret', '$6$jq62gTbU')
'$6$jq62gTbU$kYZgWuKLuNTX0Ur.UWiuBJuIYltW3hc7EdI2/4RpldwUoLlRl9IdXgJb6B3kxEoAxWolDwXDCqOnz8SN0CKkJ1'
>>>
```

Esto es exactamente lo mismo que sacamos del fichero `/etc/shadow`, con lo que la contraseña sería aceptada. Ahora le podemos comunicar a **zeus** que puede entrar a **olympus** usando la contraseña `supersecret`.

## Probando contraseñas por fuerza bruta

Si podemos hacer una función que nos permita validar una contraseña dada, podemos enchufar un montón de entradas. Tirando de **python**, esto no tiene mucha dificultad:

```bash
root@olympus:~# cat test_passwords.py
#!/usr/bin/env python3

import crypt

class PasswordCracker:
    def __init__(self, shadow):
        self.shadow = shadow
        self.salt = shadow[:shadow.rfind('$')]
    def verify(self, password):
        hash = crypt.crypt(password, self.salt)
        return hash == self.shadow

shadow = '$6$jq62gTbU$kYZgWuKLuNTX0Ur.UWiuBJuIYltW3hc7EdI2/4RpldwUoLlRl9IdXgJb6B3kxEoAxWolDwXDCqOnz8SN0CKkJ1'
possible = ['temporal', 'baspassword', 'secret', 'supersecret']
pc = PasswordCracker(shadow)
for password in possible:
    if pc.verify(password):
        print('Password "%s" is valid' % password)
root@olympus:~#
```

Y una ejecución nos probaría toda la lista:

```bash
root@olympus:~# ./test_passwords.py
Password "supersecret" is valid
root@olympus:~#
```

**AVISO**: Probar varias contraseñas no lleva mucho tiempo, pero si intentáis un generador de contraseñas posibles, puede ser muy costoso en tiempo.
