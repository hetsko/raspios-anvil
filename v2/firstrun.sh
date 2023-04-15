#!/bin/bash

set +e

if ! [ -f /usr/lib/raspberrypi-sys-mods/imager_custom ]; then
   echo 'Big bad'
   exit 1
fi

/usr/lib/raspberrypi-sys-mods/imager_custom set_hostname something
/usr/lib/raspberrypi-sys-mods/imager_custom enable_ssh
/usr/lib/userconf-pi/userconf 'pi' '$5$dV5IYu9p9k$0Emx5Y9mpYLTwk43z0QmqU7nqJxEevp7XUUxCTSf55.'
/usr/lib/raspberrypi-sys-mods/imager_custom set_wlan 'Kerberos' '9a7837a03fa21d29884982d409ee46a7dd6a1e67e201f70b9c2a1f6ca40ad48b' 'CZ'
/usr/lib/raspberrypi-sys-mods/imager_custom set_keymap 'us'
/usr/lib/raspberrypi-sys-mods/imager_custom set_timezone 'Europe/Prague'



get_active_part_uuid() {
  cat /boot/cmdline.txt | sed 's/.*root=PARTUUID=\([^-]\+-[0-9]\{2\}\).*/\1/'
}

replace_part_num() {
  sed -i 's/\(PARTUUID=[^-]\+\)-'$2'/\1-'$3'/' $1
}

DISK_UUID="$(get_active_part_uuid | cut -d '-' -f 1)"
PART_UUID_02="$DISK_UUID-02"
PART_UUID_03="$DISK_UUID-03"
DISK_DEVICE="/dev/$(lsblk -ndo PKNAME /dev/disk/by-partuuid/$PART_UUID_03)"

if [ "$(get_active_part_uuid)" == "$PART_UUID_03" ]; then
  # Fix /etc/fstab on partition 02
  TEMPDIR=$(mktemp --directory)
  mount "PARTUUID=$PART_UUID_02" $TEMPDIR
  cp /etc/fstab $TEMPDIR/etc/fstab
  replace_part_num $TEMPDIR/etc/fstab "03" "02"
  umount $TEMPDIR && rm -r $TEMPDIR

  # 1. Repeat firstrun.sh settings for partition 02
  replace_part_num /boot/cmdline.txt "03" "02"
  exit 0
else
  # Expand partition 03
  # ---- but this is probably not needed, since partition 3 is hopefully
  #      already expanded using the normal firstboot init script?
  # parted $DISK_DEVICE resizepart 3 100%
  # e2fsck -y -f -v -C 0 $PART_UUID_03
  # resize2fs -p $PART_UUID_03

  # 2. Return to partition 03 and let firstrun.sh be deleted
  replace_part_num /boot/cmdline.txt "02" "03"
fi

rm -f /boot/firstrun.sh
sed -i 's| systemd.run.*||g' /boot/cmdline.txt
exit 0

# Contents of cmdline.txt:
#
# console=serial0,115200 console=tty1 root=PARTUUID=e088fd39-02 rootfstype=ext4 fsck.repair=yes rootwait
#     quiet init=/usr/lib/raspberrypi-sys-mods/firstboot
#     systemd.run=/boot/firstrun.sh systemd.run_success_action=reboot systemd.unit=kernel-command-line.target
