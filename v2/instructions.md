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
This guide describes how to add a 2nd system partition to the official image
or a freshly flashed SD card.

### Augmenting an image file

> The instructions for augmenting a flashed **SD card** are very similar.
> The main difference is that all `truncate` calls (padding the image with
> empty space) are to be skipped.

Start with the image of the secondary partition (RPi OS Lite is recommended),
here referred to as `rpios.img`.

```bash
# Secondary system partition, this file will be modified
IMAGE_FILE=rpios.img
# Primary system partition, use the same one or specify a different one.
IMAGE_APPEND=rpios.img
```

Inspect the partition tables.
  - verify there are two partitions (/boot and root)
  - write down START and SIZE of the appended partition (or rely on the examples)

```bash
parted $IMAGE_FILE unit MiB print
parted $IMAGE_APPEND unit MiB print

# Example: RPi OS Lite
START_APPEND=260
SIZE_APPEND=1644

# Example: RPi OS Full
START_APPEND=260
SIZE_APPEND=3932
```

> Some fancy shell to read it automatically:
> ```bash
> parse_parted_MiB() {
>   row=$(parted -m $1 unit MiB print | grep "^$2:")
>   echo $row | cut -d ':' -f $3 | sed 's/.\{3\}$//'
> }
> START_APPEND=$(parse_parted_MiB $IMAGE_APPEND 2 2)
> SIZE_APPEND=$(parse_parted_MiB $IMAGE_APPEND 2 4)
> ```

Pad the secondary system partition with 1GiB of free space.

```bash
truncate -s +1024M $IMAGE_FILE
parted $IMAGE_FILE resizepart 2 100%
```

Append the primary system partition.

```bash
SIZE_PADDED=$(du --apparent-size -m $IMAGE_FILE | cut -f 1)
dd if=$IMAGE_APPEND bs=1M skip=$START_APPEND count=$SIZE_APPEND >> $IMAGE_FILE
parted $IMAGE_FILE mkpart primary $SIZE_PADDED"MiB" 100%
```

Check and expand the filesystems (should only concern the first partition).

```bash
LOOP=$(kpartx -l $IMAGE_FILE | tail -n 1 | sed 's|.*/dev/\(.*\)|\1|')
kpartx -va $IMAGE_FILE
e2fsck -f /dev/mapper/${LOOP}p2 && resize2fs /dev/mapper/${LOOP}p2
e2fsck -f /dev/mapper/${LOOP}p3 && resize2fs /dev/mapper/${LOOP}p3
kpartx -d /dev/$LOOP
```


Final touch: compress it.

```bash
xz -v $IMAGE_FILE
```
