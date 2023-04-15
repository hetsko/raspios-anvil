# Cheat-sheat for image tasks

> Most of the commands here require root access, so prepend `sudo ...`
> or login as root `sudo su`.

## 1 Flashing a block device (SD card, USB drive)

**Warning:** No safety checks are done, whatsoever. It is completely possible
to accidentally overwrite the active system drive, so take care (or use `rpi-imager`).

### Uncompressed image

- Source = raw image `rpios.img`
- Target = SD card `/dev/mmcblk0`

```bash
dd if=rpios.img.xz of=/dev/mmcblk0 bs=4M status=progress
```

### Compressed image

- Source = compressed image `rpios.img.xz`
- Target = SD card `/dev/mmcblk0`

```bash
dd if=rpios.img.xz bs=4M | xzcat - | dd of=/dev/mmcblk0 bs=4M status=progress
```

> Assuming `.xz` compression, but this can change in the future. If that is the
> case, replace `xzcat` with an appropriate decompressing utility that reads
> from stdin and writes to stdout. For example, `funzip` works for older RPi OS
> compressed as `.zip`.

## 2 Inserting a 2nd system partition

**Motivation:** Having two system partitions is very useful (or even required)
when doing exotic tasks such as "OS re-install" or "drive partitioning" when
neither removing the SD card, nor booting from USB is an option. Only around
3GB of reserved storage space is required when the lite OS version is used.
This guide describes how to add a 2nd system partition to the official image.

### Augmenting an image file

The process requires one copy of a RPi OS image (Lite version is recommended)
that will be **modified in place**.

- `raspios-lite.img`

> If compressed, extract it by running `unxz raspios-lite.img.xz`.

Use the script `append_2nd.sh` to append a copy of the image's system partition
as a second partition. The first partition is padded with **1GiB** of free
space by default (this can be adjusted in the script file):

```bash
./append_2nd.sh raspios-lite.img
mv raspios-lite.img raspios-lite-lite.img
```

| No. | Partition                | Free space |
| --- | ------------------------ | ---------- |
| 1   | /boot                    |            |
| 2   | raspios lite (secondary) | ~1GiB      |
| 3   | raspios lite (primary)   | the rest   |

Alternatively, it is possible to specify a different source for the appended
partition. E.g. a regular image with graphical interface instead of lite:

```bash
./append_2nd.sh raspios-lite.img raspios-full.img
mv raspios-lite.img raspios-lite-full.img
```

| No. | Partition                 | Free space |
| --- | ------------------------- | ---------- |
| 1   | /boot                     |            |
| 2   | raspios lite (secondary)  | ~1GiB      |
| 3   | raspios desktop (primary) | the rest   |

Final touch: compress it.

```bash
xz -v raspios-lite-lite.img
```

## 3 First boot to a 2-partition system

In its initial state, the 2-partition image will successfully boot.into the
main system partition (no. 3) as if it was a normal image. However, during the
process new disk id is generated, which breaks the secondary partition.

Solve this by copying over updated `/etc/fstab` from the active partition
and changing the partition number.

```bash
replace_part_num() {
  sed -i 's/\(PARTUUID=[^-]\+\)-'$2'/\1-'$3'/' $1
}

mount /dev/mmcblk0p2 /mnt
cp /etc/fstab /mnt/etc/fstab
replace_part_num /mnt/etc/fstab "03" "02"
umount /mnt
```

Additionally, this can be executed automatically using the custom `firstrun.sh` script.

```bash
cp firstrun.sh /mnt
echo "systemd.run=/boot/firstrun.sh systemd.run_success_action=reboot systemd.unit=kernel-command-line.target" >> /mnt/cmdline.txt
```
