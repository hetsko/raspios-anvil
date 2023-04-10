#!/bin/bash

# Secondary system partition, this file will be modified and becomes the output.
IMAGE_FILE=$1
# Primary system partition, use the same one or specify a different one.
IMAGE_APPEND=$2
# Extra space for secondary partition in MiB.
EXTRA_SPACE=1024


echo "INFO: Read partition table."
parse_parted_MiB() {
  row=$(parted -m $1 unit MiB print | grep "^$2:")
  echo $row | cut -d ':' -f $3 | sed 's/.\{3\}$//'
}
START_APPEND=$(parse_parted_MiB $IMAGE_APPEND 2 2)
SIZE_APPEND=$(parse_parted_MiB $IMAGE_APPEND 2 4)

echo "INFO: Pad the secondary system partition with "$EXTRA_SPACE"MiB of free space."
truncate -s "+"$EXTRA_SPACE"M" $IMAGE_FILE
parted $IMAGE_FILE resizepart 2 100%

echo "INFO: Append the primary system partition."
SIZE_PADDED=$(du --apparent-size -m $IMAGE_FILE | cut -f 1)
dd if=$IMAGE_APPEND bs=1M skip=$START_APPEND count=$SIZE_APPEND >> $IMAGE_FILE
parted $IMAGE_FILE mkpart primary $SIZE_PADDED"MiB" 100%

echo "INFO: Check and expand the filesystems."
LOOP=$(kpartx -l $IMAGE_FILE | tail -n 1 | sed 's|.*/dev/\(.*\)|\1|')
kpartx -va $IMAGE_FILE
e2fsck -y -f -v -C 0 /dev/mapper/${LOOP}p2 && resize2fs -p /dev/mapper/${LOOP}p2
e2fsck -y -f -v -C 0 /dev/mapper/${LOOP}p3 && resize2fs -p /dev/mapper/${LOOP}p3
kpartx -d /dev/$LOOP
