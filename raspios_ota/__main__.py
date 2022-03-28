import argparse
import getpass
from pathlib import Path
import re
import os

from click import command

from .prepare import prepare_image, copy_boot_for_nfs, copy_root
from .mount import mount_partition
from ._commands import ExternalCommands


commands_nocap = ExternalCommands(['zip'], capture_output=False)


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
        commands_nocap.zip(zip_file, image)
        print(f'Compressed, {zip_file}')

        if keep_unzipped is None:
            keep_unzipped = input('Keep the uncompressed copy? [y/N] ') not in ('y', 'Y')
        if not keep_unzipped:
            Path(image).unlink()
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
