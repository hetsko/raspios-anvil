# Remote OS Upgrade

## Create the images
We will require 3 images in total, all prepared using the `raspios_anvil` script.
- the main (customized) image that will be installed on the SD card
- a copy of the boot partition configured for NFS root file system
- a copy of the root file system partition to be served by NFS
```bash
unzip 2021-10-30-raspios-bullseye-armhf-lite.zip
mv 2021-10-30-raspios-bullseye-armhf-lite.img myimg.img
# Configure and compress -> myimg.zip
sudo python3 -m raspios_anvil myimg.img --zip --keep-unzipped
# Extract partitions for NFS -> myimg_nfsboot.zip, myimg_nfsroot.zip
sudo python3 -m raspios_anvil --nfs myimg.img --zip
```
All of these images can be reused for multiple Pi machines, although it is
advisable to set aside a clean copy of the "myimg_nfsroot.img", duplicate it
for each of them and delete it afterwards. Each Pi is going to write its own
changes to it.

## Configure NFS server
Set up an NFS server to temporarily serve the Pi's root directory. The Pi in
the example uses a sticky ip `192.168.0.168`, change it as is appropriate.
A wildcard `*` can be used as well, but it will allow other
devices from the private network to access the Pi's NFS root directory.
```bash
# NFS SERVER
sudo apt install nfs-kernel-server

echo '/srv/rpi-root 192.168.0.168(rw,sync,no_subtree_check,no_root_squash)' >> /etc/exports
unzip myimg_nfsroot.zip
sudo mount myimg_nfsroot.img /srv/rpi-root
sudo exportfs -rv
```

Later, clean up by unmounting and removing a line from the "/etc/exports" file.
```bash
# NFS SERVER
sudo umount /srv/rpi-root && sudo nano /etc/exports && sudo exportfs -rv
rm myimg_nfsroot.img  # The image is now modified, won't be needed anymore
```

## Step 1 - Overwrite "/boot" and reboot to the NFS root
```bash
# RASPBERRY
sudo apt install unzip  # To get funzip

sudo umount /boot
ssh user@server 'dd if=myimg_nfsboot.zip' | funzip | sudo dd of=/dev/mmcblk0p1 status=progress
```
**[TODO]** Check integrity and reboot if successful.
```bash
# RASPBERRY
#sha256sum /dev/mmcblk0p1
sudo reboot
```

## Step 2 - Overwrite the whole SD card
```bash
# RASPBERRY
sudo apt install unzip  # To get funzip

sudo umount /dev/mmcblk0
ssh user@server 'dd if=myimg.zip' | funzip | sudo dd of=/dev/mmcblk0 status=progress
sudo reboot
```
**[TODO]** Check integrity and reboot if successful.
```bash
# RASPBERRY
#sha256sum /dev/mmcblk0
sudo reboot
```
And done. Pi should boot up to the freshly installed OS, connect to
network and be accessible over ssh.
