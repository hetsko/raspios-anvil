#!/bin/bash

# Check privileges and arguments
[ "$EUID" -ne 0 ] && echo "This script requires root privileges (mount)" && exit 1

get_part_num() {
    grep -w '/' /etc/fstab | sed 's/.*PARTUUID=[^-]\+-\([0-9]\{2\}\).*/\1/'
}

set_part_num() {
    sed -i 's/\(root=PARTUUID=[^-]\+\)-[0-9]\{2\}/\1-'$1'/' /boot/cmdline.txt
}

if ! ( [ "$1" == "2" ] || [ "$1" == "3" ] ); then
  >&2 echo "Usage: $0 2"
  >&2 echo "  or:  $0 3"
  exit 1
fi

if [ "$(get_part_num)" == "0$1" ]; then
  echo "Already on partition 0$1"
  cat /boot/cmdline.txt
else
  set_part_num "0$1"
  echo "Switched to partition 0$1, reboot to continue"
  cat /boot/cmdline.txt
fi

fi
