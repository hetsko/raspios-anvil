# Over-the-air RaspiOS
Also known as *stay-in-chair* RaspiOS, a simple commandline/python
utility that is here to help you configure
[Raspberry Pi OS](https://www.raspberrypi.com/software/operating-systems/#raspberry-pi-os-32-bit)
images for a network-ready (**ssh-ready**) **first boot** so
that there is no need to go looking for a spare keyboard and screen.
Simply burn the customized image to a microSD, power up the Pi and connect
via ssh straightaway. Requires `python>=3.7`.

Main features:
- enable SSH by default and...
- ...pre-set a unique and secure password for the default user (instead of `raspberry`)
- pre-configure WiFi credentials for wireless Pi-s

To create the image, download an image of your choice from
[here](https://downloads.raspberrypi.org/raspios_lite_armhf/images/),
unzip the archive and run the script.
```bash
unzip 2021-10-30-raspios-bullseye-armhf-lite.zip
mv 2021-10-30-raspios-bullseye-armhf-lite.img my_img.img
raspios_ota.py my_img.img  # Modifies the image in place
```
The script is interactive and prompts you for the relevant info (new password,
WiFi credentials). The image is then ready to be installed on a microSD card
with an imaging tool of your choice
([RPi Imager](https://www.raspberrypi.com/software/),
[Rufus](https://rufus.ie/), `dd` command)
same as the original Raspberry Pi OS images.


## Advanced features: Over-the-air OS reinstall
Be adventurous (from the comforts of your chair) and
conduct reliable **over-the-air OS upgrades** assited by an NFS server, which
can be hosted by a second Pi or any other linux machine in the same network.
The procedure has two main steps:
1. Configure the Pi to boot into a root file system hosted on the NFS server,
  thus releasing the SD card.
2. Since the SD card does not host the file system anymore, it can be safely
  unmounted and a new OS image can be installed. Finally, the Pi is rebooted.

Refer to ??? for a more detailed tutorial.

> *Reliable?* Well, a network-based approach always comes with certain
> risks which cannot be completely mitigated (connection loss, network security).
> Apart from that, the procedure itself is in theory quite sound and
> completly avoids dubious methods such as a live linux system attempting to
> overwrite its root file system.

**Q:** This idea sounds a bit overcomplicated.
- *Not really, it mostly comes down to creating the pre-configured images
  using this utility, running a few commands and twice rebooting the Pi.*

**Q:** But what good does this thing bring to the world?
- Use case 1: *Physically manupulating with the Pi and removing the SD card
  is not a reasonable option due to its remote/inaccessible location.*
- Use case 2: *Upgrading multiple Pi machines one-by-one can become a tedious
  task. This is represents an opportunity for automatization.*
- Use case 3: *It sounds fun.*
