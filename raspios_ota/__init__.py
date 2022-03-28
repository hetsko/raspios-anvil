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


from .prepare import prepare_image, copy_root, copy_boot_for_nfs
