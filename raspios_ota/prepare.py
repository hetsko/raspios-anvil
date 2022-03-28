import re
from pathlib import Path

from ._commands import ExternalCommands
from .mount import mounted_context, loop_context


# [WIFI -> select a country code]
# Different contries (e.g. Europe vs. USA) differ in allocation of (5GHz) WiFi channels.
# https://en.wikipedia.org/wiki/List_of_ISO_3166_country_codes
WIFI_COUNTRY_CODE = 'CZ'

commands = ExternalCommands(['wpa_passphrase', 'openssl'])
commands_nocap = ExternalCommands(['dd'], capture_output=False)


def _configure_ssh(root):
    """[Boot partition] Enable ssh server."""
    (Path(root) / 'ssh').touch()


def _configure_wifi(root, ssid, passwd):
    """[Boot partition] Configure wifi network credentials."""
    with (Path(root) / 'wpa_supplicant.conf').open('w') as wpa_file:
        lines = [
            f'country={WIFI_COUNTRY_CODE}\n',
            'ctrl_interface=/var/run/wpa_supplicant\n',
            *commands.wpa_passphrase(ssid, passwd).splitlines(keepends=True),
        ]
        lines = [l for l in lines if not re.match(r'\s*#', l)]
        wpa_file.writelines(lines)


def _configure_user_passwd(root, user, passwd):
    """[File system] Modify /etc/shadow to change initial password for given user."""
    hashed = commands.openssl('passwd', '-6', str(passwd)).strip()
    shadow_file = (Path(root) / 'etc/shadow')
    shadow_file.write_text(
        re.sub(
            f'{user}:[^:]*:(.*\\n)', f'{user}:{hashed}:\\1',
            shadow_file.read_text(),
            count=1,
        )
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
        _configure_user_passwd(path, 'pi', pi_pass)
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
        commands_nocap.dd(
            f'if={partitions[0]}',
            f'of={new_image}',
            f'status={"progress" if progress else "none"}',
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
        commands_nocap.dd(
            f'if={partitions[1]}',
            f'of={new_image}',
            f'status={"progress" if progress else "none"}',
        )
    return new_image
