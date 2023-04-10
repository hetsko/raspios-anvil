#!/bin/bash

#
# Mount a partition of a block device or image file to a temporary mountpoint.
# Prints the path to the mount point to stdout. The partiton is specified by
# its order in the partition table.
#
# Note: Block devices usually offer their paritions as separate devices in /dev
#       so its not hard to mount them manually. This script is intended
#       primarily for image files, which would require loop devices and such.
#
# Usage:
#   ./mount_part.sh BLOCKDEVICE_OR_IMAGE PARTITION_NUMBER
#

#
# Tip - View the partition table:
#   partx --show /path/to/image
#
# Tip - Clean up afterwards:
#   umount /path/to/image
#

files=(
  # Wifi
  "/etc/wpa_supplicant/wpa_supplicant.conf"

  # SSH server
  "/etc/ssh/ssh_host_*_key"
  "/etc/ssh/ssh_host_*_key.pub"
  # Hostname
  "/etc/hostname"
  "/etc/hosts"
  # User
  "/etc/passwd"
  "/etc/shadow"
  "/etc/fstab"

  # Other non-system, e.g. /home
  "/home/"
)

# Exit on first error
set -e

# Check privileges and arguments
[ "$EUID" -ne 0 ] && echo "This script requires root privileges (mount)" && exit 1

if ! (partx --show "$1" > /dev/null); then
  >&2 echo "Error argument 1: Expected disk image file or block device"
  exit 1
fi

partitions_total=$(partx --show --noheadings "$1" | wc --lines)
if ! ([ "$2" -gt 0 ] && [ "$2" -le $partitions_total ]); then
  >&2 echo "Error argument 2: Expected a partition number in range 1-$partitions_total"
  >&2 echo "Use \"partx --show $1\" to list existing partitions"
  exit 1
fi

# Already moutned warning
mounted_total=$(mount | grep --count --word-regexp "$1" || true)
if [ "$mounted_total" -gt 0 ]; then
  >&2 echo "Warning: Target $1 is already mounted $mounted_total times, proceeding anyways"
fi

# Calculate offset
size_1st=$(partx --bytes --show --noheadings --output SIZE "$1" | head -n 1)
sectors_1st=$(partx --show --noheadings --output SECTORS "$1" | head -n 1)
SECTOR_SIZE=$(( $size_1st / $sectors_1st ))

offset_sectors=$(partx --show --noheadings --output START "$1" | sed "$2"'q;d')
OFFSET_BYTES=$(( $SECTOR_SIZE * $offset_sectors ))

# Create tempdir and mount
TEMPDIR="$(mktemp --directory)"
mount -o loop,offset=$OFFSET_BYTES "$1" "$TEMPDIR"
echo $TEMPDIR
>&2 echo ""
>&2 echo "To clean up:"
>&2 echo "    umount $1"
