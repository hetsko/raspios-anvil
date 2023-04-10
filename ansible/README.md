# Ansible playbooks - Alternative implementation of the project

[Ansible](https://docs.ansible.com/ansible/latest/) is an IT automation tool.
It is used to (remotely) configure systems, deploy applications.
It is a more convenient, more manageable and standardized alternative
to writing plain shell scripts. It also prints a nice colorful overview of tasks
that were executed during the run, whether any failed, etc.
The tasks are described in YAML files and Ansible implements
them in python under the hood.

In this case, it is used:

1. Locally, to manipulate and configure the images.
2. Remotely, to orchestrate OS reinstall over SSH connection.

## Setup Ansible

> **Security notice:** Running playbooks that modify the image files
> requires one to mount the images to the active filesystem,
> which can only be done with *root* privileges. There are reasons for that
> (can be exploited for privilege escalation).
>
> Thus, it is more convenient to use a Docker container.
> However, keep in mind that the container itself needs to run with extra
> privileges/capabilities to be able to mount. And with access to a loop device.
> While its capabilities are more limited than that of a root process on
> the host machine, you should still be more careful about what you execute in it.

- Docker container

        docker build . -t ansible
        docker run -it --rm -v /path/to/your/images:/opt/images ansible \
            --cap-add CAP_SYS_ADMIN --device $(losetup -f)

    The container will be launched with access to a specified work directory
    (`/path/to/your/images`), where the container manipulate the source images
    and create the new images.

    The container needs to be run with extra capability
    `--cap-add CAP_SYS_ADMIN` and access to one free loop device as returned
    by calling `$(losetup -f)`. This allows mounting the image files inside
    the container. See the security notice above.

- Manually (root privileges will be required to run some of the playbooks)

        python3 -m venv venv && . venv/bin/activate
        pip install -r requirements.txt
        ansible-galaxy collection install -r requirements.yml

    The tasks target a Debian-based system. Make sure that following linux
    packages are present: `parted`, `rsync`, `zip`, `unzip`.

        apt install parted rsync zip unzip

## Usage

Run a playbook with following command:

```
ansible-playbook img/image_ssh.yml -e img_src=/opt/images/raspios.img
```

> In case you do not use the Docker container, the command needs to be run
> with root privileges (`sudo`).

Feel free to inspect the playbooks files (*.yml) to gain some information
on how to use them. They are by definition quite human-readable
and self-documenting. Usually, there is a section with predefined **input variables**,

```yaml
vars:
    myvar: 'something'
    ...
```

which can be modified either directly in the file, or on runtime with
a command line option

```
... -e myvar='something'
```

or by passing a simple YAML file with values.

```
... -e @values.yml
```

```yaml
# Contents of "values.yml"
myvar: something
myothervar: something else
```


## Examples

See the examples below for basic usage. The playbooks always create new images,
the source images are retained. Previously created images with the same name
will be overwritten. It is recommended to work on a SSD drive if you can,
otherwise the process may get a bit slow.


- Create a SSH-ready image (ready for headless boot)

        ansible-playbook img/image_ssh.yml -e img_src=/opt/images/raspios.img

    > Default output (same dir): "/opt/images/image_ssh.img"

    To specify a custom output path use `-e img_dest=...`

        ansible-playbook img/image_ssh.yml -e img_src=/opt/images/raspios.img \
             -e img_dest=/opt/images/image_wifi.img

- Create a SSH-ready image and change the default password for user pi

        ansible-playbook img/image_ssh.yml -e img_src=/opt/images/raspios.img -e @passwd.yml

    ```yaml
    # Contents of "passwd.yml". Sensitive data - delete when finished!
    pi_password: myPassw0rd
    ```

- Create a SSH-ready image with WiFi configuration

        ansible-playbook img/image_ssh.yml -e img_src=/opt/images/raspios.img -e @wifi.yml

    ```yaml
    # Contents of "wifi.yml". Sensitive data - delete when finished!
    wifi_countrycode: GB
    wifi_ssid: MyNetwork
    wifi_psk: VerySecretPassw0rd
    ```


    Make sure to specify your correct [2-letter country code](https://en.wikipedia.org/wiki/List_of_ISO_3166_country_codes) (different countries use
    different WiFi bands).

- Create an image with two /root partitions (two OS installations)

        ansible-playbook img/image_2os.yml -e img_src=/opt/images/raspios.img

    > Default output (same dir): "/opt/images/image_2os.img"

    By default it duplicates the /root partition from the same image. To source
    the secondary partition from a different image (e.g. RaspiOS Lite), use

        ansible-playbook img/image_2os.yml -e img_src=/opt/images/raspios.img \
            -e img_p2_src=/opt/images/raspios_lite.img
