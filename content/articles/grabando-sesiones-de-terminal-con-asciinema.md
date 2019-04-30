Title: Grabando sesiones de terminal con asciinema
Slug: grabando-sesiones-de-terminal-con-asciinema
Date: 2019-04-30 10:00
Category: Miscelánea
Tags: grabación, terminal, asciinema



Me defino como una persona de tecnología clásica, pero últimamente me ha dado una aire de modernillo y me he empezado a mirar el tema de los *podcasts*. Como amante del terminal necesitaba conocer alguna herramienta que me permitiera hacer *casts* de mi terminal y encontré uno interesante: es **asciinema**.

No tengo muy claro para qué lo voy a utilizar, ni siquiera si lo utilizaré, pero por el momento voy a dejar estas notas en este artículo para su uso futuro. Si alguien cree que le puede dar un uso interesante, soy todo oídos...

Lo primero es instalar la herramienta. Hay muchas maneras de instalar o usar la herramienta, tal como se indica en [su documentación](https://asciinema.org/docs/installation); desde paquetes para tu distribución favorita hasta un contenedor, pasando por una librería **python**. Voy a utilizar esta última por comodidad:

```bash
gerard@atlantis:~$ pip install asciinema
Collecting asciinema
  Using cached https://files.pythonhosted.org/packages/a7/71/771c859795e02c71c187546f34f7535487b97425bc1dad1e5f6ad2651357/asciinema-2.0.2.tar.gz
Building wheels for collected packages: asciinema
  Running setup.py bdist_wheel for asciinema ... error
  Complete output from command /home/gerard/workspace/asciinematest/env/bin/python3 -u -c "import setuptools, tokenize;__file__='/tmp/pip-build-l8bnaq6u/asciinema/setup.py';f=getattr(tokenize, 'open', open)(__file__);code=f.read().replace('\r\n', '\n');f.close();exec(compile(code, __file__, 'exec'))" bdist_wheel -d /tmp/tmpv_6mhrv_pip-wheel- --python-tag cp35:
  /usr/lib/python3.5/distutils/dist.py:261: UserWarning: Unknown distribution option: 'long_description_content_type'
    warnings.warn(msg)
  usage: -c [global_opts] cmd1 [cmd1_opts] [cmd2 [cmd2_opts] ...]
     or: -c --help [cmd1 cmd2 ...]
     or: -c --help-commands
     or: -c cmd --help
  
  error: invalid command 'bdist_wheel'
  
  ----------------------------------------
  Failed building wheel for asciinema
  Running setup.py clean for asciinema
Failed to build asciinema
Installing collected packages: asciinema
  Running setup.py install for asciinema ... done
Successfully installed asciinema-2.0.2
gerard@atlantis:~$ 
```

Su uso no es muy complejo, pero en caso de duda, nos ofrece ayuda si se invoca sin parámetros:

```bash
gerard@atlantis:~$ asciinema 
usage: asciinema [-h] [--version] {rec,play,cat,upload,auth} ...

Record and share your terminal sessions, the right way.

positional arguments:
  {rec,play,cat,upload,auth}
    rec                 Record terminal session
    play                Replay terminal session
    cat                 Print full output of terminal session
    upload              Upload locally saved terminal session to asciinema.org
    auth                Manage recordings on asciinema.org account

optional arguments:
  -h, --help            show this help message and exit
  --version             show program's version number and exit

example usage:
  Record terminal and upload it to asciinema.org:
    asciinema rec
  Record terminal to local file:
    asciinema rec demo.cast
  Record terminal and upload it to asciinema.org, specifying title:
    asciinema rec -t "My git tutorial"
  Record terminal to local file, limiting idle time to max 2.5 sec:
    asciinema rec -i 2.5 demo.cast
  Replay terminal recording from local file:
    asciinema play demo.cast
  Replay terminal recording hosted on asciinema.org:
    asciinema play https://asciinema.org/a/difqlgx86ym6emrmd8u62yqu8
  Print full output of recorded session:
    asciinema cat demo.cast

For help on a specific command run:
  asciinema <command> -h
gerard@atlantis:~$ 
```

La grabación de un fichero en local es muy simple; parámetros aparte, lo más simple quedaría así:

```
gerard@atlantis:~$ asciinema rec free_memory.cast
```

Esto nos abre una sesión de *shell* que será "grabada", aunque el fichero resultante es de texto plano y se puede modificar a mano con mucha paciencia. Por poner un ejemplo, voy a hacer un *cast* de un vaciado de cachés de la memoria del sistema operativo; concretamente, lanzo estos comandos (y comentarios):

```bash
# Veamos la memoria ocupada en nuestro sistema:
free -h
# Intentemos vaciar las cachés
echo 3 | sudo tee /proc/sys/vm/drop_caches
# Y veamos el resultado:
free -h
exit
```

Tras "salir" de esta sesión de terminal, volvemos a la sesión original, previo aviso de que nuestro *cast* ha quedado grabado en el fichero indicado.

```bash
asciinema: recording finished
asciinema: asciicast saved to free_memory.cast
gerard@atlantis:~$ 
```

Este es nuestro *cast*, y podemos reproducirlo, tanto localmente como en remoto si lo subimos a la nube. Como el comando es tan simple, le he añadido al ejemplo doble velocidad, con el *flag* `-s 2`.

```bash
gerard@atlantis:~$ asciinema play free_memory.cast -s 2
```

La página en donde se pueden subir los *casts* es <https://asciinema.org/> y podemos registrarnos en ella sin complicación ninguna. Una vez conectada la cuenta web con la herramienta de terminal mediante `asciinema auth`, podemos subir nuestro *cast*.

```bash
gerard@atlantis:~$ asciinema upload free_memory.cast 
View the recording at:

    https://asciinema.org/a/3vdnfBAL8simwMtcPx2zkhQbZ

gerard@atlantis:~$ 
```

En la página web se pueden editar algunos metadatos, como por ejemplo el título. Una vez hecho esto, la voy a hacer pública, para que todo el mundo pueda ver mi *cast*, en caso de saber su dirección. Me voy a "share" y puedo encontrar varias formas de compartir mi *cast*, como por ejemplo la dirección, un enlace, un enlace con imagen, o directamente incrustando un visor directamente; solo falta que distribuya el enlace o que lo añada a mi página para darlo a conocer al mundo.

Si a alguien le interesa el enlace, es <https://asciinema.org/a/241168>, pero yo considero que la mejor forma de distribuir el *cast* es con el visor incrustado, que necesita **javascript** para funcionar, pero se integra muy bien con mi *blog*.

<script id="asciicast-241168" src="https://asciinema.org/a/241168.js" async data-speed="4" data-rows="24"></script>
