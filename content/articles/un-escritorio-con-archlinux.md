Title: Un escritorio con Archlinux
Slug: un-escritorio-con-archlinux
Date: 2016-07-25 08:00
Category: Miscelánea
Tags: linux, archlinux, escritorio, xfce



En [otro articulo]({filename}/articles/un-escritorio-minimo-con-debian.md) vimos como instalar **Archlinux**. Como tantas otras distribuciones nos vale para servidor y como distribución de escritorio. Sin embargo, debido a su filosofía como *rolling release*, puede asustarnos un poco como servidor; aunque tener un escritorio "a la última" es un caramelo que muy pocos podemos rechazar.

Vamos a instalar un escritorio basado en **XFCE**, que es bueno, bonito y barato. Me encanta personalmente porque no usa muchos recursos, responde rápido y tiene muchas herramientas de configuración, a diferencia de otros, por ejemplo **LXDE**.

Empezaremos instalando la capa gráfica. Esto se consigue mediante el paquete **xorg**.

```bash
[root@archlinux ~]# pacman -S xorg
...
[root@archlinux ~]#
```

Alternativamente, podemos instalar solamente el servidor gráfico y los *drivers* necesarios. Esto es especialmente importante en **Archlinux** porque los paquetes se actualizan muy a menudo, y por lo tanto, tener paquetes que no vamos a usar solo incrementa el tiempo del *update*.

```bash
[root@archlinux ~]# pacman -S xorg-server xf86-input-mouse xf86-input-keyboard xf86-input-synaptics xf86-video-vesa
resolviendo dependencias…
:: Existen 4 proveedores disponibles para libgl:
:: Repositorio extra
   1) mesa-libgl  2) nvidia-304xx-libgl  3) nvidia-340xx-libgl  4) nvidia-libgl

Introduzca un número (por omisión=1):
:: Existen 2 proveedores disponibles para xf86-input-driver:
:: Repositorio extra
   1) xf86-input-evdev  2) xf86-input-libinput

Introduzca un número (por omisión=1):
buscando conflictos entre paquetes…
advertencia: bucle de dependencias detectado:
advertencia: harfbuzz será instalado antes que su dependencia freetype2

Paquetes (62) damageproto-1.2.1-3  elfutils-0.166-1  fixesproto-5.0-3  fontconfig-2.12.0-1  fontsproto-2.1.3-1  freetype2-2.6.3-1
              graphite-1:1.3.8-1  harfbuzz-1.2.7-1  inputproto-2.3.2-1  kbproto-1.0.7-1  libdrm-2.4.68-1  libepoxy-1.3.1-1
              libevdev-1.5.2-1  libfontenc-1.1.3-1  libomxil-bellagio-0.9.3-1  libpciaccess-0.13.4-1  libpng-1.6.23-1
              libtxc_dxtn-1.0.1-6  libunwind-1.1-3  libx11-1.6.3-1  libxau-1.0.8-2  libxcb-1.12-1  libxdamage-1.1.4-2
              libxdmcp-1.1.2-1  libxext-1.3.3-1  libxfixes-5.0.2-1  libxfont-1.5.1-1  libxi-1.7.6-1  libxkbfile-1.0.9-1
              libxml2-2.9.4+0+gbdec218-2  libxshmfence-1.2-1  libxtst-1.2.2-1  libxxf86vm-1.1.4-1  llvm-libs-3.8.0-1
              mesa-11.2.2-1  mesa-libgl-11.2.2-1  mtdev-1.1.5-1  pixman-0.34.0-1  recordproto-1.14.2-2  wayland-1.11.0-1
              xcb-proto-1.12-2  xextproto-7.3.0-1  xf86-input-evdev-2.10.3-1  xf86vidmodeproto-2.3.1-3  xkeyboard-config-2.18-1
              xorg-bdftopcf-1.0.5-1  xorg-font-util-1.3.1-1  xorg-font-utils-7.6-4  xorg-fonts-alias-1.0.3-1
              xorg-fonts-encodings-1.0.4-4  xorg-fonts-misc-1.0.3-4  xorg-mkfontdir-1.0.7-2  xorg-mkfontscale-1.1.2-1
              xorg-server-common-1.18.3-2  xorg-setxkbmap-1.3.1-1  xorg-xkbcomp-1.3.1-1  xproto-7.0.29-1
              xf86-input-keyboard-1.8.1-2  xf86-input-mouse-1.9.1-2  xf86-input-synaptics-1.8.99.1-1  xf86-video-vesa-2.3.4-2
              xorg-server-1.18.3-2

Tamaño total de la descarga:     37,78 MiB
Tamaño total de la instalación:  150,38 MiB

:: ¿Continuar con la instalación? [S/n] s
...
[root@archlinux ~]#
```

Una vez tenemos el servidor gráfico, el siguiente paso es el escritorio que elijamos. Tras buscar el [el índice de grupos](https://www.archlinux.org/groups/), me decanté por **XFCE**, aunque hay para todos los gustos.

```bash
[root@archlinux ~]# pacman -S xfce4 xfce4-goodies
...
[root@archlinux ~]#
```

Si lo queréis un poco mas *minimal*, solo haría falta el paquete **xfce4**. Para ser breves, me limito a este solamente.

```bash
[root@archlinux ~]# pacman -S xfce4
:: Hay 17 miembros en el grupo xfce4:
:: Repositorio extra
   1) exo  2) garcon  3) gtk-xfce-engine  4) thunar  5) thunar-volman  6) tumbler  7) xfce4-appfinder  8) xfce4-mixer
   9) xfce4-panel  10) xfce4-power-manager  11) xfce4-session  12) xfce4-settings  13) xfce4-terminal  14) xfconf  15) xfdesktop
   16) xfwm4  17) xfwm4-themes

Introduzca una selección (por omisión=todos):
resolviendo dependencias…
buscando conflictos entre paquetes…

Paquetes (113) adwaita-icon-theme-3.20-2  alsa-lib-1.1.1-1  at-spi2-atk-2.20.1-2  at-spi2-core-2.20.2-1  atk-2.20.0-1
               avahi-0.6.32-2  cairo-1.14.6-1  cantarell-fonts-1:0.0.24-1  cdparanoia-10.2-5  colord-1.3.2-2
               compositeproto-0.4.2-3  dbus-glib-0.106-1  dconf-0.26.0-1  desktop-file-utils-0.22-2  gdk-pixbuf2-2.34.0-2
               glib-networking-2.48.2-1  gnome-icon-theme-3.12.0-3  gnome-icon-theme-symbolic-3.12.0-4
               gnome-themes-standard-3.20.2-1  gsettings-desktop-schemas-3.21.2-1  gstreamer0.10-0.10.36-4
               gstreamer0.10-base-0.10.36-3  gstreamer0.10-base-plugins-0.10.36-3  gtk-update-icon-cache-3.20.6-1  gtk2-2.24.30-2
               gtk3-3.20.6-1  hicolor-icon-theme-0.15-1  iso-codes-3.68-1  jasper-1.900.1-15  js17-17.0.0-3  json-glib-1.2.0-1
               lcms2-2.7-1  libcroco-0.6.11-1  libcups-2.1.4-1  libdaemon-0.14-3  libdatrie-0.2.10-1  libexif-0.6.21-2
               libgudev-230-1  libgusb-0.2.9-1  libice-1.0.9-1  libimobiledevice-1.2.0-3  libjpeg-turbo-1.5.0-1
               libkeybinder2-0.3.0-2  libnotify-0.7.6-2  libogg-1.3.2-1  libplist-1.12-4  libproxy-0.4.12-2  librsvg-2:2.40.16-1
               libsm-1.2.2-2  libsoup-2.54.1-1  libthai-0.1.24-1  libtheora-1.1.1-3  libtiff-4.0.6-2  libunique-1.1.6-6
               libusbmuxd-1.0.10-1  libvisual-0.4.0-6  libvorbis-1.3.5-1  libwnck-2.31.0-1  libxcomposite-0.4.4-2
               libxcursor-1.1.14-2  libxfce4ui-4.12.1-2  libxfce4util-4.12.1-1  libxft-2.3.2-1  libxinerama-1.1.3-2
               libxkbcommon-0.6.1-1  libxklavier-5.4-1  libxmu-1.1.2-1  libxrandr-1.5.0-1  libxrender-0.9.9-1  libxres-1.0.7-1
               libxt-1.1.5-1  libxv-1.0.10-1  nspr-4.12-1  orc-0.4.25-2  pango-1.40.1-1  perl-uri-1.71-1  polkit-0.113-4
               polkit-gnome-0.105-3  randrproto-1.5.0-1  renderproto-0.11.1-3  rest-0.8.0-1  shared-mime-info-1.6-2
               startup-notification-0.12-4  ttf-dejavu-2.35-1  upower-0.99.4-2  videoproto-2.3.3-1  vte-0.28.2-7
               vte-common-0.44.2-1  wayland-protocols-1.4-1  xcb-util-0.4.0-1  xineramaproto-1.2.1-3  xorg-iceauth-1.0.7-1
               xorg-xauth-1.0.9-1  xorg-xinit-1.3.4-4  xorg-xmodmap-1.0.9-1  xorg-xrdb-1.1.0-2  exo-0.10.7-2  garcon-0.4.0-1
               gtk-xfce-engine-2.10.1-1  thunar-1.6.10-3  thunar-volman-0.8.1-2  tumbler-0.1.31-1  xfce4-appfinder-4.12.0-4
               xfce4-mixer-4.11.0-3  xfce4-panel-4.12.0-2  xfce4-power-manager-1.4.4-2  xfce4-session-4.12.1-4
               xfce4-settings-4.12.0-4  xfce4-terminal-0.6.3-3  xfconf-4.12.0-4  xfdesktop-4.12.3-2  xfwm4-4.12.3-2
               xfwm4-themes-4.10.0-2

Tamaño total de la descarga:     65,79 MiB
Tamaño total de la instalación:  298,53 MiB

:: ¿Continuar con la instalación? [S/n] s
...
[root@archlinux ~]# 
```

Como pequeño inconveniente ante otras distribuciones, como **Debian**, los paquetes no tienen tantas dependencias, dejando al usuario elegir lo que pone o no.

Como requisito para tener algunas de las funcionalidades del escritorio, por ejemplo la papelera, es necesario instalar otros paquetes. En el caso concreto de la papelera, se necesita el paquete **gvfs**.

```bash
[root@archlinux ~]# pacman -S gvfs
resolviendo dependencias…
buscando conflictos entre paquetes…

Paquetes (10) fuse-2.9.6-1  gcr-3.20.0-1  libatasmart-0.19-3  libbluray-0.9.2-2  libcddb-1.3.2-4  libcdio-0.93-3
              libcdio-paranoia-10.2+0.93+1-2  libsecret-0.18.5-1  udisks2-2.1.7-1  gvfs-1.28.2-1

Tamaño total de la descarga:     3,84 MiB
Tamaño total de la instalación:  23,45 MiB

:: ¿Continuar con la instalación? [S/n] s
...
[root@archlinux ~]#
```

El siguiente paso es el gestor de entrada. Podemos entrar mediante un *login* texto, y escalar a gráficos con *startx*, pero es mas bonito y cómodo usar un gestor gráfico como **lightdm**. En caso de **Archlinux**, no depende de ninguna librería gráfica, y hay que decidirlo por nosotros mismos. Puesto que **XFCE** usa las librerías **GTK**, vamos a aprovecharnos de ello.

```bash
[root@archlinux ~]# pacman -S lightdm lightdm-gtk-greeter
resolviendo dependencias…
buscando conflictos entre paquetes…

Paquetes (2) lightdm-1:1.18.1-2  lightdm-gtk-greeter-1:2.0.1-3

Tamaño total de la descarga:    0,27 MiB
Tamaño total de la instalación:  2,68 MiB

:: ¿Continuar con la instalación? [S/n] s
...
[root@archlinux ~]#
```

Activamos el *login manager* para que salte automáticamente en cada *boot* de nuestro sistema, usando **systemd**.

```bash
[root@archlinux ~]# systemctl enable lightdm
Created symlink /etc/systemd/system/display-manager.service → /usr/lib/systemd/system/lightdm.service.
[root@archlinux ~]#
```

Y ya como detalles opcionales, vamos a habilitar el sonido y un gestor de redes, que nos van a hacer la vida mas fácil.

```bash
[root@archlinux ~]# pacman -S wicd wicd-gtk alsa-utils
resolviendo dependencias…
buscando conflictos entre paquetes…

Paquetes (22) ethtool-1:4.5-1  fftw-3.3.4-2  flac-1.3.1-3  libglade-2.6.4-5  libnl-3.2.27-1  libsamplerate-0.1.8-3
              libsndfile-1.0.26-1  net-tools-1.60.20130531git-1  pygobject2-devel-2.28.6-12  pygtk-2.24.0-6
              python-dbus-common-1.2.4-1  python2-2.7.11-3  python2-cairo-1.10.0-2  python2-dbus-1.2.4-1
              python2-gobject2-2.28.6-12  python2-urwid-1.3.1-2  rfkill-0.5-1  wireless_tools-30.pre9-1  wpa_supplicant-1:2.5-3
              alsa-utils-1.1.1-1  wicd-1.7.4-1  wicd-gtk-1.7.4-1

Tamaño total de la descarga:     19,58 MiB
Tamaño total de la instalación:  110,79 MiB

:: ¿Continuar con la instalación? [S/n] s
...
[root@archlinux ~]#
```

El paquete **wicd** usa un frontal para el escritorio, pero todas las operaciones delicadas se delegan a un *daemon* que funciona en segundo plano. De forma similar a **Redhat**, los servicios no se instalan preparados para arrancar, y hay que activarlos manualmente.

```bash
[root@archlinux ~]# systemctl enable wicd
Created symlink /etc/systemd/system/dbus-org.wicd.daemon.service → /usr/lib/systemd/system/wicd.service.
Created symlink /etc/systemd/system/multi-user.target.wants/wicd.service → /usr/lib/systemd/system/wicd.service.
[root@archlinux ~]#
```

El subsistema de sonido funciona solo, salvo por el hecho de que hay que inicializar el dispositivo, y guardar los niveles de audio, para que se puedan restablecer tras cada *reboot*.

```bash
[root@archlinux ~]# alsactl init
alsactl: sysfs_init:48: sysfs path '/sys' is invalid

Found hardware: "ICH" "Analog Devices AD1980" "AC97a:41445370" "0x1028" "0x0177"
Hardware is initialized using a generic method
[root@archlinux ~]# alsactl store
[root@archlinux ~]#
```

Como paso final, vamos a necesitar un usuario con el que trabajar habitualmente, sin privilegios y sin la capacidad de romper nada.

```bash
[root@archlinux ~]# useradd -m gerard
[root@archlinux ~]# passwd gerard
Introduzca la nueva contraseña de UNIX:
Vuelva a escribir la nueva contraseña de UNIX:
passwd: contraseña actualizada correctamente
[root@archlinux ~]#
```

Finalmente podemos reiniciar la máquina, y ver como nos queda de bonito.

```bash
[root@archlinux ~]# reboot
...
```

Si todo ha salido bien, nos queda un escritorio de esta apariencia, que tendremos que personalizar a nuestro gusto.

![Escritorio XFCE]({static}/images/escritorio-xfce-archlinux.jpg)

Y todo esto, con un consumo de recursos bastante escaso...

```bash
[gerard@archlinux ~]$ free -m
              total        used        free      shared  buff/cache   
available
Mem:            498          97         310           1          89         
379
Swap:           522           0         522
[gerard@archlinux ~]$ 
```
