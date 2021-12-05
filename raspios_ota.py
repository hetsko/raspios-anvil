#!/bin/python3

"""
Configure a RaspiOS image for remote access (ssh) out of the box.
Image changes include:
  - enable ssh
  - set new password for the pi user
  - [TODO] configure ssh public key login (if required)
  - configure WiFi credentials (if required)

SECURITY: The custom image may contain sensitive data that should be kept
          secret. Namely: the derived WiFi network key in plaintext. The
          password for the pi user is safely stored in hashed form.

Original image is required. Visit one of
  - https://downloads.raspberrypi.org/raspios_lite_armhf/ (headless)
  - https://downloads.raspberrypi.org/raspios_armhf/ (with gui libs)
"""

import contextlib
import argparse
import getpass
import os
import re
import glob
from subprocess import run
from pathlib import Path
import subprocess


# [WIFI -> select a country code]
# Different contries (e.g. Europe vs. USA) differ in allocation of (5GHz) WiFi channels.
# https://en.wikipedia.org/wiki/List_of_ISO_3166_country_codes
WIFI_COUNTRY_CODE = 'CZ'


def mount_partition(image, n, mount_point='/mnt'):
    disk_info = run(
        ['fdisk', '-l', '-o', 'Start', str(image)],
        check=True, capture_output=True, text=True
    ).stdout.splitlines()
    sector_size = int(re.search(r'= (\d+) bytes', disk_info[1]).group(1))
    offsets = [int(s)*sector_size for s in disk_info[disk_info.index('')+2:]]
    run(
        ['mount', '-o', f'loop,offset={offsets[n]}', str(image), str(mount_point)],
        check=True
    )
    return mount_point


def unmount_partition(mount_point='/mnt'):
    run(['umount', str(mount_point)], check=True)


@contextlib.contextmanager
def mounted_context(image, n=0, mount_point='/mnt'):
    """Temporarily mount n-th partition from a specified raw image (*.img)."""
    mount_partition(image, n, mount_point)
    try:
        yield mount_point
    finally:
        unmount_partition(mount_point)


@contextlib.contextmanager
def loop_context(image):
    """Temporarily create loop for partitions in the specified image (*.img)."""
    loop = run(
        ['losetup', '--show', '-P', '-f', str(image)],
        check=True, capture_output=True, text=True
    ).stdout.strip()
    try:
        yield sorted(glob.glob(f'{loop}p*'))
    finally:
        run(['losetup', '-d', loop], check=True)


def _configure_ssh(root):
    """[Boot partition] Enable shh server."""
    (Path(root) / 'ssh').touch()


def _configure_wifi(root, ssid, passwd):
    """[Boot partition] Configure wifi network credentials."""
    wpa_text = run(
        ['wpa_passphrase', ssid, passwd],
        check=True, capture_output=True, text=True
    ).stdout
    with (Path(root) / 'wpa_supplicant.conf').open('w') as wpa_file:
        lines = [
            f'country={WIFI_COUNTRY_CODE}\n'
            'ctrl_interface=/var/run/wpa_supplicant\n'
        ]
        lines += [
            l for l in wpa_text.splitlines(keepends=True)
            if not re.match(r'\s*#', l)
        ]
        wpa_file.writelines(lines)


def _configure_user_pass(root, user, passwd):
    """[File system] Modify /etc/shadow to change initial password for given user."""
    hashed = run(
        ['openssl', 'passwd', '-6', str(passwd)],
        check=True, capture_output=True, text=True
    ).stdout.strip()
    shadow_file = (Path(root) / 'etc/shadow')
    shadow_file.write_text(
        re.sub(f'{user}:[^:]*:(.*\\n)', f'{user}:{hashed}:\\1',
               shadow_file.read_text(), count=1)
    )


def _configure_nfs_root_fs(root, nfs_root_address):
    """[Boot partition] Configure remote root filesystem over NFS."""
    (Path(root) / 'cmdline.txt').write_text(' '.join([
        'console=serial0,115200',
        'console=tty1',
        'root=/dev/nfs',
        'rootfstype=nfs',
        f'nfsroot={nfs_root_address}',
        'ip=dhcp',
    ]) + '\n')


def prepare_image(image, pi_pass, wifi_ssid=None, wifi_pass=None):
    """Modify several fundamental settings in the raspios image:
        - enable ssh
        - change default password
        - (optional) set wifi credentials
    Note, that the image file is modified IN PLACE.

    :image str: Path to the raspios image file.
    :pi_pass str: New default password for the pi user.
    :wifi_ssid str: (Optional) SSID of the wifi network to connect to.
    :wifi_pass str: (Optional) Password for access to the wifi network.

    Returns path to the image that was modified.
    """
    with mounted_context(image, 0) as path:
        _configure_ssh(path)
        if wifi_ssid and wifi_pass:
            _configure_wifi(path, wifi_ssid, wifi_pass)
        elif bool(wifi_ssid) != bool(wifi_pass):
            raise ValueError('Specify both wifi_ssid and wifi_pass (or neither)')
    with mounted_context(image, 1) as path:
        _configure_user_pass(path, 'pi', pi_pass)
    return image


def copy_boot_for_nfs(image, new_image, nfs_root, progress=True):
    """Create a separate image file containing only the /boot partition and
    configure boot options for remote root file system via NFS.

    Purpose: This image can be used to overwrite /dev/mmcblk0p1 (i.e. /boot)
    on a running raspberry. After a reboot, the raspberry will stop using its
    SD card file system in favor of the remote NFS root enabling OS reinstall.

    :image str: Path to the image used as a source for the /boot partition.
    :nfs_root str: Address of the root file system on the NFS server,
                   e.g. "192.168.0.1:/srv/raspios-root".

    Returns path to the new image with the /boot partition.
    """

    with loop_context(image) as partitions:
        subprocess.run(
            ['dd', f'if={partitions[0]}', f'of={new_image}']
            + (['status=progress'] if progress else [])
        )
    with mounted_context(image, 0) as path:
        _configure_nfs_root_fs(path, nfs_root)
    return new_image


def copy_root(image, progress=True):
    """Create a separate image containing only the root file system partition.

    Purpose: This image is to be mounted and served by the NFS server. Raspberry
    can use it as a temporary root fs instead of its SD card. A new copy ought
    to be created each time since the rapsberry will write changes to it.

    :image str: Path to the image used as a source for the root fs.

    Returns path to the new image with the root fs partition.
    """
    new_image = re.sub(r'^([^\.]*)(.*)?$', r'\1_nfsroot\2', image)
    with loop_context(image) as partitions:
        subprocess.run(
            ['dd', f'if={partitions[1]}', f'of={new_image}']
            + (['status=progress'] if progress else [])
        )
    return new_image


def _prompt_overwrite_check(file, exit_on_fail=True):
    """Check if file exists. If yes, prompt user for overwrite."""
    if Path(file).exists():
        reply = input(f'File "{file}" already exists, overwrite? [y/N]')
        if reply not in ('y', 'Y'):
            if exit_on_fail:
                exit('No overwrite, exiting...')
            else:
                return False
    return True


def _prompt_for_secrets():
    """Prompt user for the secrets (pi password, wifi credentials)."""
    pi_pass = getpass.getpass('New password for pi: ')
    if getpass.getpass('Again: ') != pi_pass:
        exit('Passwords do not match!')
    wifi_ssid = input('WiFi ssid (leave empty to skip): ')
    if wifi_ssid != '':
        wifi_pass = getpass.getpass('WiFi password: ')
        if getpass.getpass('Again: ') != wifi_pass:
            exit('Passwords do not match!')
    else:
        print('Skipping WiFi configuration')
        wifi_ssid = wifi_pass = None
    return pi_pass, wifi_ssid, wifi_pass


def _prompt_compress(image, keep_unzipped=None):
    """Compress the image and prompt to delete it afterwards."""
    print(f'Compressing {image}...')
    zip_file = re.sub(r'\.[^\.]*$', '', image) + '.zip'
    if _prompt_overwrite_check(zip_file, exit_on_fail=False):
        run(['zip', zip_file, image], check=True)
        print(f'Compressed, {zip_file}')

        if keep_unzipped is None:
            keep_unzipped = input('Keep the uncompressed copy? [y/N] ') not in ('y', 'Y')
        if not keep_unzipped:
            os.unlink(image)
    else:
        print(f'Skipped compressing {image}')


parser = argparse.ArgumentParser(description=(
    'Prepare a custom RaspiOS image by modifying the original one in-place.'
    ' You can look for original images here:'
    ' https://downloads.raspberrypi.org/raspios_lite_armhf/images/'
    ' Run the script again with the --nfs option to create copies of boot and'
    ' root partitions as separate images. Use these images to set up a raspberry'
    ' with remote root file system served by an NFS server.'
))
parser.add_argument(
    'image', help='path to the original raspios image (*.img)'
)
# parser.add_argument(
#     '-o', '--output',
#     help='save the modified image to this location instead of modifying it in place'
# )
parser.add_argument(
    '--nfs', help=(
        'alternative script use: specify address of the remote root file system'
        ' on an NFS server, e.g. "192.168.0.1:/srv/raspios-root". Script will'
        ' create two separate images (boot and root partition).'
    )
)
parser.add_argument(
    '--zip', action='store_true', help='compress the final modified image(s)'
)
parser.add_argument(
    '--keep-unzipped', action='store_true',
    help='use together with --zip, keep the uncompressed image(s) as well'
)
parser.add_argument(
    '--only-mount', dest='only_mount', type=int, default=None,
    help='do not modify, only mount one of the partitions with given index to /mnt'
)


if __name__ == '__main__':
    args = parser.parse_args()

    if os.geteuid() != 0:
        exit("Root privileges are required to run this script (try 'sudo').\nExiting.")

    if args.only_mount is not None:
        path = mount_partition(args.image, args.only_mount)
        print(f'Mounted "{args.image}" to "{path}". Unmount with:\n  sudo umount {path}')
        exit()

    elif args.nfs is None:
        image = args.image
        print(f'Configuring {image}')
        print('Success,', prepare_image(image, *_prompt_for_secrets()))
        if args.zip:
            _prompt_compress(image, keep_unzipped=args.keep_unzipped)

    else:
        original = args.image
        img_boot = re.sub(r'^([^\.]*)(.*)?$', r'\1_nfsboot\2', original)
        img_root = re.sub(r'^([^\.]*)(.*)?$', r'\1_nfsroot\2', original)
        _prompt_overwrite_check(img_boot)
        _prompt_overwrite_check(img_root)
        if not re.fullmatch(r'[\w\-\.]+:/[\w\-\./]*', args.nfs):
            reply = input(
                f'"{args.nfs}" does not seem to be a valid NFS path in format'
                + ' "host:/path/to/root". Continue anyway? [y/N]'
            )
            if reply not in ('y', 'Y'):
                exit('Invalid NFS path, exiting...')

        print(f'Extracting partitions from {original}')
        print('Success,', copy_boot_for_nfs(original, img_boot, args.nfs))
        print('Success,', copy_root(original, img_root))
        if args.zip:
            _prompt_compress(img_boot, keep_unzipped=args.keep_unzipped)
            _prompt_compress(img_root, keep_unzipped=args.keep_unzipped)
