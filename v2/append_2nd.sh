#!/bin/bash

usage()
{
>&2 echo "Usage: $0 TARGET_IMAGE [SRC_IMAGE]"
>&2 echo "Append a second system partition to a RaspberryPi OS image, modify in place."
>&2 echo "
Both arguments must be uncompressed RaspberryPi OS image files.
If SRC_IMAGE is given, its system partition will be used as a source for
the partition that is appended to IMAGE. Otherwise, the system partition
found in IMAGE is used."
}

# Exit on first error
set -e

# Extra space for secondary partition in MiB.
EXTRA_SPACE=1024

# Check privileges and arguments
[ "$EUID" -ne 0 ] && echo "This script requires root privileges (parted, mount)" && exit 1

if ! ([ "$?" == 1 ] || [ "$?" == 2 ]); then
  usage
  exit 1
fi

#   - Argument 1: Target to be modified.
IMAGE_FILE=$1
if ! ([ -f "$1" ] && partx --show "$1" > /dev/null); then
  >&2 echo "ERROR: Argument 1: Expected disk image file"
  >&2 echo ""
  usage
  exit 1
fi

#   - Argument 2: (Optional) Source for the appended primary system partition.
IMAGE_APPEND=$2
if [ -z "$2" ]; then
  IMAGE_APPEND=$IMAGE_FILE
elif ! ([ -f "$2" ] && partx --show "$2" > /dev/null); then
  >&2 echo "ERROR: Argument 2: Expected disk image file"
  >&2 echo ""
  usage
  exit 1
fi


#
# Main part
#

echo "INFO: Read partition table."
parse_parted_MiB() {
  row=$(parted -m $1 unit MiB print | grep "^$2:")
  echo $row | cut -d ':' -f $3 | sed 's/.\{3\}$//'
}
START_APPEND=$(parse_parted_MiB $IMAGE_APPEND 2 2)
SIZE_APPEND=$(parse_parted_MiB $IMAGE_APPEND 2 4)

echo ""
echo "INFO: Pad the secondary system partition with "$EXTRA_SPACE"MiB of free space."
truncate -s "+"$EXTRA_SPACE"M" $IMAGE_FILE
parted $IMAGE_FILE resizepart 2 100%

echo ""
echo "INFO: Append the primary system partition."
SIZE_PADDED=$(du --apparent-size -m $IMAGE_FILE | cut -f 1)
dd if=$IMAGE_APPEND bs=1M skip=$START_APPEND count=$SIZE_APPEND status=progress >> $IMAGE_FILE
parted $IMAGE_FILE mkpart primary $SIZE_PADDED"MiB" 100%

echo ""
echo "INFO: Check and expand the filesystems."
LOOP=$(kpartx -l $IMAGE_FILE | tail -n 1 | sed 's|.*/dev/\(.*\)|\1|')
kpartx -va $IMAGE_FILE
e2fsck -y -f -v -C 0 /dev/mapper/${LOOP}p2 > /dev/null
resize2fs -p /dev/mapper/${LOOP}p2 > /dev/null
e2fsck -y -f -v -C 0 /dev/mapper/${LOOP}p3 > /dev/null
resize2fs -p /dev/mapper/${LOOP}p3 > /dev/null
kpartx -vd /dev/$LOOP

echo ""
echo "INFO: Show partition table."
parted $1 unit MiB print

echo "INFO: All done."
