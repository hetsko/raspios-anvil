
# Experimental features/ideas

## OS upgrade over a USB cable

Since approx. RPi 3 (B) the Pis are capable of booting from a USB drive the same
way as they do from an SD card. In most cases the SD card does not even have
to be present (good for recovery from SD card failure). This approach can be leveraged to overwrite the full SD card contents (reinstall OS) without the
need to remove it from the Pi, just connect the USB drive. If using a

> TODO: The procedure.

## Remote OS upgrade via NFS

Be adventurous (from the comforts of your chair) and
conduct reliable **over-the-air OS upgrades** assited by an NFS server, which
can be hosted by a second Pi or any other linux machine in the same network.
All credit for the original idea to this
[stackexchange post](https://raspberrypi.stackexchange.com/questions/628/).
The procedure has two main steps:
1. Configure the Pi to boot into a root file system hosted on the NFS server,
  thus releasing the SD card.
2. Since the SD card does not host the file system anymore, it can be safely
  unmounted and a new OS image can be installed. Finally, the Pi is rebooted.

Refer to ??? for a more detailed tutorial.

> *Reliable?* Well, a network-based approach always comes with certain
> risks which cannot be completely mitigated (connection loss, network security).
> Apart from that, the procedure itself is quite sound in theory as it
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

## Remote OS upgrade via secondary OS partition
In theory, one could create an image with two identical /root partitions (two
OS). One primary to be used most of the time and one small secondary, which
would be used solely for the OS upgrades. Reboot to the secondary partition, overwrite the primary one with the new OS, configure it and reboot to new OS.

> TODO: The procedure.
