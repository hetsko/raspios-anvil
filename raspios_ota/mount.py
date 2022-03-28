"""
Partition mounting utilities including two useful context managers:
    - mounted_context()
    - loop_context()
"""

import contextlib
import glob
import re

from ._commands import ExternalCommands


commands = ExternalCommands(['fdisk', 'partx', 'mount', 'umount', 'losetup'])


def mount_partition(image, n, mount_point='/mnt'):
    """Mount n-th partition from a specified raw image (*.img).

    Returns the mount point.
    """
    res = re.search(
        r'Units: sectors of [*\d\s]+ = (\d+) bytes',
        commands.fdisk('-l', '-o', 'Start', str(image)),
    )
    sector_size = int(res[1]) if res else 512

    offsets = [
        int(s)*sector_size for s
        in commands.partx('-sgo', 'START', str(image)).splitlines()
    ]
    commands.mount('-o', f'loop,offset={offsets[n]}', str(image), str(mount_point))
    return mount_point


def unmount_partition(mount_point='/mnt'):
    """Unmount a partition mounted at given mount point."""
    commands.umount(str(mount_point))


@contextlib.contextmanager
def mounted_context(image, n=0, mount_point='/mnt'):
    """Context manager. Mount n-th partition from a specified raw image (*.img)
    and then clean up by unmounting.

    Returns the mount point.
    """
    mount_partition(image, n, mount_point)
    try:
        yield mount_point
    finally:
        unmount_partition(mount_point)


@contextlib.contextmanager
def loop_context(image):
    """Context manager. Create loop for each partition in the specified raw
    image (*.img) and then clean up by releasing the loops.

    Returns a list of the loop devices pointing to each of the partitions.
    """
    loop = commands.losetup('--show', '-P', '-f', str(image)).strip()
    try:
        yield sorted(glob.glob(f'{loop}p*'))
    finally:
        commands.losetup('-d', loop)
