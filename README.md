# raspios-anvil

> [Work in progress...]

RaspiOS anvil is here to unofficially help you bend the official
[Raspberry Pi OS images 32bit/64bit](https://www.raspberrypi.com/software/operating-systems/) to your will.

More specifically, it is a commandline/python
utility that can for example configure the image for a network-ready
(**ssh-ready**) first boot, which is very useful if you use your Pi headless.
No need to go looking for a spare keyboard+screen just for the first boot.
While this in itself can be achieved e.g. simply by copying the "ssh" and "wpa_supplicant.conf" files to "/boot" by hand after burning the image
(google: headless raspberrypi boot), there are many additional features and
applications to this tool may also come in handy.

Targets `python>=3.7`. Main features:

- prepare a customized RaspiOS image (and write it to SD card now or anytime later)
- enable SSH by default and...
- ...set a unique and secure password for the default user (instead of `raspberry`)
- configure WiFi credentials for a wireless Pi
- add or modify additional configs or data

To create the image, download an image of your choice from
[here](https://downloads.raspberrypi.org/raspios_lite_armhf/images/),
unzip the archive and run the script.
```bash
unzip 2021-10-30-raspios-bullseye-armhf-lite.zip
mv 2021-10-30-raspios-bullseye-armhf-lite.img my_img.img
sudo python -m raspios_ota my_img.img  # Modifies the image in place
```
> Root privilege is required to **mount** partitions from the image and modify the
> files inside.

The script is interactive and prompts you for the relevant info (new password,
WiFi credentials). The image is then ready to be installed on a microSD card
with an imaging tool of your choice
([RPi Imager](https://www.raspberrypi.com/software/),
[Rufus](https://rufus.ie/), `dd` command)
same as the original Raspberry Pi OS images.

## Experimental features/ideas: Remote OS upgrade

The images created with this procedure need to be burned manually to the SD
card and then insert the card back to the Pi. Often removing the card is not
so straightforward e.g. when the Pi is well hidden in a box somewhere which
needs to be disassembled. This is ok for "install once, do not bother further"
approach, but may become a nuisance in case of the need to update to a new
RaspiOS version, migrating to 64bit, or trying out a completely different OS.

Alternative options utilizing a boot from
USB drive, NFS server or a second OS partition can be exploited to sidestep
these mechanical hurdles. A reliable guide/utility for these procedures, which
may lead even to a completely remote OS re-install, is the next step for this
project.
