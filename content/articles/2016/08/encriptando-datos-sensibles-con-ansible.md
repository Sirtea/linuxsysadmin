---
title: "Encriptando datos sensibles con Ansible"
slug: "encriptando-datos-sensibles-con-ansible"
date: 2016-08-15
categories: ['Operaciones']
tags: ['ansible', 'vault', 'encriptación', 'inventario']
---

Si usamos **ansible** para configurar otras máquinas tenemos pleno poder para acceder a otras, sea mediante claves SSH o por accesos remotos normales. En este último caso, conviene aplicar un poco de seguridad para evitar que un posible intruso acceda libremente. Para esto podemos encriptar la información sensible con **ansible-vault**.<!--more-->

Para hacer una demostración simple, vamos a partir de [un artículo anterior]({{< relref "/articles/2016/06/controlando-contenedores-docker-con-ansible.md" >}}), por comodidad. En este artículo pusimos todos los datos de conexión a las máquinas controladas en el fichero de inventario *hosts*, que hoy vamos a trocear y a encriptar las partes sensibles.

Partimos de un modelo en el que un **master** con las herramientas de **ansible** controla s un grupo de **slaves**, que solo ofrecen acceso SSH. El uso de **docker** es opcional, pero muy conveniente por la rapidez en montar el entorno.

```bash
gerard@sirius:~$ docker ps
CONTAINER ID        IMAGE               COMMAND               CREATED             STATUS              PORTS               NAMES
c2de340b9dac        master              "/bin/sh"             17 seconds ago      Up 16 seconds                           ansible
e6f0d2569207        slave               "/usr/sbin/sshd -D"   17 minutes ago      Up 16 minutes                           slave2
497357df848c        slave               "/usr/sbin/sshd -D"   17 minutes ago      Up 17 minutes                           slave1
gerard@sirius:~$ 
```

Todo el tutorial se va a hacer desde la máquina **master**.

## Estado inicial

Siguiendo el artículo mencionado, disponemos de un fichero de inventario *hosts* que declara todos los servidores y grupos que tenemos, conjuntamente con sus datos de conexión.

```bash
~ # cat hosts 
[slaves:vars]
ansible_user = ansible
ansible_ssh_pass = s3cr3t
ansible_become = true
ansible_become_method = sudo
ansible_become_user = root
ansible_become_pass = s3cr3t

[slaves]
slave1
slave2
~ # 
```

Podemos ver que funciona como debe.

```bash
~ # ansible -i hosts -m ping slaves
slave1 | SUCCESS => {
    "changed": false, 
    "ping": "pong"
}
slave2 | SUCCESS => {
    "changed": false, 
    "ping": "pong"
}
~ # 
```

## Separando el inventario en dos partes

Como solo queremos encriptar los datos de conexión, vamos a partir el inventario en dos ficheros, dentro de su carpeta. **ansible** va a recibir esa carpeta como inventario y va a juntar ambas partes para sacar la visión global.

```bash
~ # tree inventory/
inventory/
├── hosts
└── vault

0 directories, 2 files
~ # 
```

La idea es tener una parte visible con los grupos y los servidores que los componen, y otra parte secreta con los datos a ocultar. Así quedaría la partición:

```bash
~ # cat inventory/hosts 
[slaves]
slave1
slave2
~ # cat inventory/vault 
[slaves:vars]
ansible_user = ansible
ansible_ssh_pass = s3cr3t
ansible_become = true
ansible_become_method = sudo
ansible_become_user = root
ansible_become_pass = s3cr3t
~ # 
```

Tras indicar a **ansible** que queremos utilizar esta nueva carpeta como inventario, vemos que sigue funcionando de manera adecuada.

```bash
~ # ansible -i inventory/ -m ping slaves
slave2 | SUCCESS => {
    "changed": false, 
    "ping": "pong"
}
slave1 | SUCCESS => {
    "changed": false, 
    "ping": "pong"
}
~ # 
```

## Encriptando el fichero secreto

Para conseguir esto, se va a utilizar el comando **ansible-vault**, al que se le pide que encripte el fichero secreto. Es una encriptación simétrica que encripta y desencripta con la misma contraseña.

```bash
~ # ansible-vault encrypt inventory/vault 
New Vault password: 
Confirm New Vault password: 
Encryption successful
~ # 
```

Podemos ver que el fichero ha quedado modificado, de forma que ya ni se puede curiosear:

```bash
~ # cat inventory/hosts 
[slaves]
slave1
slave2
~ # cat inventory/vault 
$ANSIBLE_VAULT;1.1;AES256
37306639633165383030626335356261333436646539373962623937653137666430366330313663
3666396533313031633236383964323235376262386337360a303037366336666135363266616363
63656431623363343639663331613262643032393034623337383134306635313235623463316466
3161613332306136310a663261346565386634663938656136363939653061373035346332616164
62353865313265306132366166653263623964306536633163393764306166366236666362323165
39353835346263646134383037386465656131356130376165646331623438336336363462383066
34353062396364393239333563336466653637343030326262323338313065623864393131343165
35313134666566663636636237376563316436666437316632613630396565643539623661323436
30383261333230613130666465626137656463326238626163656465316632303638373334623137
61653537396535346266623462396165333731326462646534343833346165333034613037663033
64613763363635333030393464646139373339333436343861313462666537636461303238326433
30346333303336643663623563613465393661626565636630383931643863343430613335373234
3336
~ # 
```

Cuando usemos fichero encriptados, **ansible** es capaz de desencriptarlos según se necesite. Solo hace falta indicarle la forma en la que queremos darle la contraseña, por ejemplo, por el terminal.

```bash
~ # ansible -i inventory/ -m ping slaves --ask-vault-pass
Vault password: 
slave1 | SUCCESS => {
    "changed": false, 
    "ping": "pong"
}
slave2 | SUCCESS => {
    "changed": false, 
    "ping": "pong"
}
~ # 
```

Otra forma, menos segura pero mas conveniente, es tener la contraseña en un fichero, y dejar que **ansible** la lea de ese fichero. Esto es útil especialmente en *scripts*, en donde suministrar una contraseña por el terminal no es factible.

```bash
~ # cat .vault-passfile 
supersecret
~ # ansible -i inventory/ -m ping slaves --vault-password-file=.vault-passfile
slave1 | SUCCESS => {
    "changed": false, 
    "ping": "pong"
}
slave2 | SUCCESS => {
    "changed": false, 
    "ping": "pong"
}
~ # 
```

Es importante recalcar que solo se puede indicar una contraseña para nuestros *vaults*, sea por el terminal o por un fichero. Eso significa que todas las contraseñas usadas en un mismo comando deben ser las mismas.

## Limpiando nuestras líneas de comandos

Si el fichero de la *password* es siempre el mismo, nuestros comandos van a ser largos y repetitivos. La gracia es que podemos ocultar los parámetros permanentes en el fichero de configuración de **ansible**.

```bash
~ # cat .ansible.cfg 
[defaults]
host_key_checking = False
vault_password_file = .vault-passfile
~ # 
```

De esta forma, podemos omitirlo:

```bash
~ # ansible -i inventory/ -m ping slaves
slave1 | SUCCESS => {
    "changed": false, 
    "ping": "pong"
}
slave2 | SUCCESS => {
    "changed": false, 
    "ping": "pong"
}
~ # 
```

De hecho, este parámetro también afecta a otras herramientas, como por ejemplo el mismo comando **ansible-vault**, por ejemplo, para inspeccionar el fichero encriptado.

```bash
~ # cat inventory/vault 
$ANSIBLE_VAULT;1.1;AES256
30313636313462346536346262333462633131633666653238313239333330343036346263653962
3862623363393436656334636361303263336333363431610a346666653539643065383765613466
64626437633565323866316466636166623432313630323362393961383663356233626263386530
3539353266343237310a396536326337313232663466333361316666376364323634623638353865
66323636336137303863643736636666353631613230633231386434373266343764343730653238
38643462636330663864626237366631346439303739323030306336396266366666303262363735
30303034333532336532306432643265653963646132393939386561326539646566613961393963
62363633626135376532336137373631383839393231356265653932333639343762353937356439
64346465323263623830306436636134613561646232663664306262383136646265383834306336
62646537666135393032306338313166316631303134363363633833663862663933366436613461
35343039646430393235383238653733343465653863363835303537383437613933306137636161
37643432373531613565633431636461666661343561393764376239313637663362333136363237
3131
~ # ansible-vault view inventory/vault
[slaves:vars]
ansible_user = ansible
ansible_ssh_pass = s3cr3t
ansible_become = true
ansible_become_method = sudo
ansible_become_user = root
ansible_become_pass = s3cr3t
~ # 
```

De hecho, también sirve para encriptar, de forma que si lo hubiésemos puesto al principio, ni siquiera tendríamos que usarla para esa función. Para ir mas lejos, podríamos haber generado la *password* de forma aleatorio y/o automatizada.

```bash
~ # cat aaaa 
lorem ipsum
~ # ansible-vault encrypt aaaa 
Encryption successful
~ # cat aaaa 
$ANSIBLE_VAULT;1.1;AES256
38666531306261623531363836623436333061326536323066386139643630323336336565626663
6238383334333666376338363366353066333763393330340a353365343234646430393236356464
62346166356430346564343539313436346661656335343733623836663563633630346138636661
3838633536383934360a343232306237373864616237386164376136323737373739623062306562
3964
~ # 
```

Y con esto nos quedan los ficheros sensibles un poco mas protegidos, aunque no tenemos porque encriptarlos todos.
