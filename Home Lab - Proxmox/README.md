# Promox Setup Steps
https://www.youtube.com/watch?v=GoZaMgEgrHw&t=899s

## Rename the "Node"
```bash
hostnamectl set-hostname NEW-HOSTNAME

# Update Hosts file change pve to the new name
nano /etc/hosts

reboot
```

## Install the 'unstable' updates

```bash
# SSH to your proxmox server or use the shell from the web gui
# Add the following line to the /etc/apt/sources.list
nano /etc/apt/sources.list

# Add the non production sources
deb http://download.proxmox.com/debian bullseye pve-no-subscription
```

Now we need to inactivate the pve-enterprise in /etc/apt/sources.list.d/pve-enterprise.list
```bash
# comment out this line
deb https://enterprise.proxmox.com/debianpve buster pve-enterprise
```
Now update & upgrade
```bash
apt-get update && apt-get upgrade -y && reboot
```
## Storage

Removing LVM

Goto Datacentre and select Storage and the click on local-lvm and select remove.  In a terminal (shell or ssh shell) enter the following commands:
```bash
lvremove /dev/pve/data
# select Yes
lvresize -l +100%FREE /dev/pve/root
resize2fs /dev/mapper/pve-root
```

Then goto Datacenter --> Storage --> Select Local and then edit.  Select the Content to be all the items to be available on this storage.

## PCI Passthrough
Update Grub - nano /etc/default/grub
```bash
# Comment out this line: GRUB_CMDLINE_LINUX_DEFAULT="quiet" and replace with the following:
GRUB_CMDLINE_LINUX_DEFAULT="quiet amd_iommu=on"
```

Now save and exit and update grub
```bash
update-grub
```

Now edit the etc/modules file
```bash
# add these 4 lines
vfio
vfio_iommu_type1
vfio_pci
vfio_virqfd
```

Now reboot
```bash
dmesg |grep -e DMAR -e IOMMU -e AMD-Vi
lsmod | grep vfio
```
https://www.thomas-krenn.com/en/wiki/Enable_Proxmox_PCIe_Passthrough

## Mounting a New Drive
https://nubcakes.net/index.php/2019/03/05/how-to-add-storage-to-proxmox/  

Follow these steps
Format and partition
We’ll use parted instead of fdisk although they have equal capabilities.Parted can be used in scripting and supports disks bigger than 2TB.

check existence in the system and install parted:
```bash
apt policy parted
```
```bash
apt install parted
```
Create a new partition table of type GPT,a newer and better standard than the older MBR:
```bash
parted /dev/sdb mklabel gpt
```
Make a primary partition for filesystem ext4 utilizing 100% of the disk:
```bash
parted -a opt /dev/sdb mkpart primary ext4 0% 100%
```
Create the ext4 filesystem on the newly created partition sdb1 with a volume label we want.Giving a label to a partition is the recommended method since when adding or removing drives the device name sdb1 could change.
```bash
mkfs.ext4 -L storageprox /dev/sdb1
```
```bash
lsblk -fs
```
Create a folder inside mnt/ that will host the data of the new disk:
```bash
mkdir -p /mnt/data
```
Edit fstab file and enter a line with the mount options:
```bash
nano /etc/fstab

# Add to FSTAB
LABEL=storageprox /mnt/data ext4 defaults 0 2
```
mount the new drive:
```bash
mount -a
```

https://www.youtube.com/watch?v=ATuUBocesmA


## Windows VirtIO Drivers
https://pve.proxmox.com/wiki/Windows_VirtIO_Drivers


## HD Passthrough to VM
Follow the mounting steps

Run the following command:
```bash
ls -n /dev/disk/by-id/
```

Then find the ID of the drive or partition you want to pass through, as well as the VM ID that you want to pass the drive through too.
```bash
/sbin/qm set 500 -virtio2 /dev/disk/by-id/ata-TOSHIBA_MK2555GSX_59DFC0LST-part1`
```

Then in Proxmox GUI under the VM you have added the drive too, edit the drive and remove the "backup" checkbox to prevent the drive from being part of the backup process.

---

## Pi Hole Install (Recursive DNS)
https://github.com/pi-hole/pi-hole/#one-step-automated-install
```bash
curl -sSL https://install.pi-hole.net | bash
```

Reset the password to something else by typing
```bash
pihole -a -p <new password>
```
https://docs.pi-hole.net/guides/dns/unbound/

```bash
sudo apt install unbound
sudo nano /etc/unbound/unbound.conf.d/pi-hole.conf
```

#### Configure `unbound`

Highlights:

-   Listen only for queries from the local Pi-hole installation (on port 5335)
-   Listen for both UDP and TCP requests
-   Verify DNSSEC signatures, discarding BOGUS domains
-   Apply a few security and privacy tricks

`/etc/unbound/unbound.conf.d/pi-hole.conf`:
Sample File
```bash
server:
    # If no logfile is specified, syslog is used
    # logfile: "/var/log/unbound/unbound.log"
    verbosity: 0

    interface: 127.0.0.1
    port: 5335
    do-ip4: yes
    do-udp: yes
    do-tcp: yes

    # May be set to yes if you have IPv6 connectivity
    do-ip6: no

    # You want to leave this to no unless you have *native* IPv6. With 6to4 and
    # Terredo tunnels your web browser should favor IPv4 for the same reasons
    prefer-ip6: no

    # Use this only when you downloaded the list of primary root servers!
    # If you use the default dns-root-data package, unbound will find it automatically
    #root-hints: "/var/lib/unbound/root.hints"

    # Trust glue only if it is within the server's authority
    harden-glue: yes

    # Require DNSSEC data for trust-anchored zones, if such data is absent, the zone becomes BOGUS
    harden-dnssec-stripped: yes

    # Don't use Capitalization randomization as it known to cause DNSSEC issues sometimes
    # see https://discourse.pi-hole.net/t/unbound-stubby-or-dnscrypt-proxy/9378 for further details
    use-caps-for-id: no

    # Reduce EDNS reassembly buffer size.
    # IP fragmentation is unreliable on the Internet today, and can cause
    # transmission failures when large DNS messages are sent via UDP. Even
    # when fragmentation does work, it may not be secure; it is theoretically
    # possible to spoof parts of a fragmented DNS message, without easy
    # detection at the receiving end. Recently, there was an excellent study
    # >>> Defragmenting DNS - Determining the optimal maximum UDP response size for DNS <<<
    # by Axel Koolhaas, and Tjeerd Slokker (https://indico.dns-oarc.net/event/36/contributions/776/)
    # in collaboration with NLnet Labs explored DNS using real world data from the
    # the RIPE Atlas probes and the researchers suggested different values for
    # IPv4 and IPv6 and in different scenarios. They advise that servers should
    # be configured to limit DNS messages sent over UDP to a size that will not
    # trigger fragmentation on typical network links. DNS servers can switch
    # from UDP to TCP when a DNS response is too big to fit in this limited
    # buffer size. This value has also been suggested in DNS Flag Day 2020.
    edns-buffer-size: 1232

    # Perform prefetching of close to expired message cache entries
    # This only applies to domains that have been frequently queried
    prefetch: yes

    # One thread should be sufficient, can be increased on beefy machines. In reality for most users running on small networks or on a single machine, it should be unnecessary to seek performance enhancement by increasing num-threads above 1.
    num-threads: 1

    # Ensure kernel buffer is large enough to not lose messages in traffic spikes
    so-rcvbuf: 1m

    # Ensure privacy of local IP ranges
    private-address: 192.168.0.0/16
    private-address: 169.254.0.0/16
    private-address: 172.16.0.0/12
    private-address: 10.0.0.0/8
    private-address: fd00::/8
    private-address: fe80::/10

```

## Installing Guacamole
After creating a light install of an ubuntu server or variant I install ssh & byobu and remote into the machine and run the script found here:
https://github.com/MysticRyuujin/guac-install

How to Run:
Download file directly from here: 
```bash
wget https://git.io/fxZq5 -O guac-install.sh
```

Make it executable:
```bash
chmod +x guac-install.sh
```

Run it as root:
Interactive (asks for passwords):
```bash
./guac-install.sh
```

Non-Interactive (values provided via cli):
```bash
./guac-install.sh --mysqlpwd password --guacpwd password --nomfa --installmysql
```

OR
```bash
./guac-install.sh -r password -gp password -o -i
```

---
## Docker Installation
Install docker.io and docker-compose
```bash
sudo apt install docker.io byobu docker-compose -y
```

#### Installing
* **SearXNG** https://github.com/searxng/searxng-docker
Follow the instructions for your own secure search engine.  Recommendations are to (a) edit the docker-compose.yml file for the proper ports to avoid collisions (b) update the searxng/settings.yml file with the ultrasecretkey of your choosing.  then run `docker-compose up` in the searxng-docker directory and test it all is working if so run with the daemon `sudo docker-compose up -d`
`
* **Hemidall**
```bash
sudo docker run -d \
  --name=heimdall \
  -e PUID=1000 \
  -e PGID=1000 \
  -e TZ=America/Edmonton \
  -p 8088:80 \
  -p 8443:443 \
  -v /home/nexxsys/docker/heimdall/config:/config \
  --restart unless-stopped \
  lscr.io/linuxserver/heimdall:latest
```
* **Bitwarden** https://bitwarden.com/help/install-on-premise-linux/ Just follow the instructions
* Portainer.io follow the instructions here https://docs.portainer.io/v/ce-2.9/start/install/server/docker/linux


Result:
```text
Proxmox (tiamat)
	-	http://10.0.0.232:8006
	-	root / kmMgYDTH5528 # @lderan5528
	-	server: nexxsys / Pyramid5528

Pi-Hole
	-	http://10.0.0.244
	-	L3n0v0
	-	Server: nexxsys / Pyramid5528

Hercules (docker server)
	-	http://10.0.0.117
	-	nexxsys / L3n0v0
	-	SearXNG http://10.0.0.125:8080 (Medusa)
	-	Heimdall http://10.0.0.117:8088
		-	https://10.0.0.117:8443
	- Portainer
		https://10.0.0.117:9443/#!/init/admin
		nexxsys / Pyramid5528

Guac (Hercules)
	http://10.0.0.117:8080/guacamole/#/
	- MySQL Root: Pyramid5528
	- MySQL User: L3n0v0
	guacadmin / Pyramid5528
	- Server nexxsys/Pyramid5528




Medusa (Searxng 8080 /Ansible)
10.0.0.125
nexxsys / Pyramid5528

Minecraft Server:
10.0.0.182

```

### Installing Searxng
I followed the step by steps here https://docs.searxng.org/admin/installation-searxng.html with no success, but then followed the docker steps and success: https://docs.searxng.org/admin/installation-docker.html

---
See here for changing IP:  [[How to make your IP static in Ubuntu]]
## Look Into This for SSH

For each user: they should generate (on their local machine) their keypair using `ssh-keygen -t rsa` (the `rsa` can be replaced with `dsa` or `rsa1` too, though those options are not recommended). Then they need to put the contents of their public key (`id_rsa.pub`) into `~/.ssh/authorized_keys` on the server being logged into  https://upcloud.com/resources/tutorials/use-ssh-keys-authentication/

https://www.dlford.io/pfsense-nat-how-to-home-lab-part-3/

https://bilk0h.com/posts/security-onion-proxmox-open-vswitch

---

Installing Wireguard
https://www.wireguard.com/install/

installing Photoprism
https://docs.photoprism.app/getting-started/docker-compose/
Nextcloud?

Let's Encrypt
https://letsencrypt.org/

---

### Adding an new network card/port
Once the card is installed you should see the device appear un the Node --> System --> Network list.
![[Pasted image 20220808153438.png]]

Create a Network Bridge for the PCI Card  
  
You need to create a Network Bridge for the NIC so it can work.  
  
1.Click on the Host in the Proxmox Webinterface  
  
[![1.png](https://forum.proxmox.com/data/attachments/19/19350-bad27b7807505539106d4c2a84cd2ae1.jpg "1.png")](https://forum.proxmox.com/attachments/1-png.19654/)  
  
2. First click on System and then click on Network  
[![2.png](https://forum.proxmox.com/data/attachments/19/19351-dd8eaf5082de518891ba4db3f4e3b763.jpg "2.png")](https://forum.proxmox.com/attachments/2-png.19655/)  
  
2.1 If the IOMMU migration was succsesfull you should see at least to Network devicese  
[![You should see multiply devices when IOMMU is enabled.png](https://forum.proxmox.com/data/attachments/19/19354-f41a5bb99e531db159ff2e0fab6d5854.jpg "You should see multiply devices when IOMMU is enabled.png")](https://forum.proxmox.com/attachments/you-should-see-multiply-devices-when-iommu-is-enabled-png.19658/)  
3. Navigate to the top corner  
First click on Create  
Secon click on Linux Bridge  
[![3.png](https://forum.proxmox.com/data/attachments/19/19352-c425a16577ea441522868214427a481d.jpg "3.png")](https://forum.proxmox.com/attachments/3-png.19656/)  
  
4. In the Setup window you shoul add atleast the  
-Name it need to be vmbr and a number  
-Add a IP Adress and a Subnetmask  
-In Bridge ports add the name of the Network Card  
[![Create Bridge.png](https://forum.proxmox.com/data/attachments/19/19353-c9fcc54bff85c71649111c4fb3750e80.jpg "Create Bridge.png")](https://forum.proxmox.com/attachments/create-bridge-png.19657/)  
  
5.After that you can add the Hardware in youre VM  
[![2020-09-04 22_28_49-pve - Proxmox Virtual Environment – Opera.png](https://forum.proxmox.com/data/attachments/19/19355-7da9157367f146cddb6cff84a36a8244.jpg "2020-09-04 22_28_49-pve - Proxmox Virtual Environment – Opera.png")](https://forum.proxmox.com/attachments/2020-09-04-22_28_49-pve-proxmox-virtual-environment-%E2%80%93-opera-png.19659/)  
  
On the pop up window you should see the new NICs  
[![2020-09-04 22_29_45-pve - Proxmox Virtual Environment – Opera.png](https://forum.proxmox.com/data/attachments/19/19356-6e1a7fdffa6923f7dadbd3861264e403.jpg "2020-09-04 22_29_45-pve - Proxmox Virtual Environment – Opera.png")](https://forum.proxmox.com/attachments/2020-09-04-22_29_45-pve-proxmox-virtual-environment-%E2%80%93-opera-png.19660/)  


qemu-guest-agent

---

## Setup RDP on Kali
-   **adduser tdh** _Add a user for remote login. Set a password and other info._{OPTIONAL if you already have a user}
-   **usermod -aG sudo tdh** _Get an updated list of installable packages_ (OPTIONAL if you already have a user)
-   **apt-get update** _Get an updated list of installable packages_
-   **apt-get install xrdp** _Install the RDP server_
-   **systemctl start xrdp** _Start the base XRDP server_
-   **systemctl start xrdp-sesman** _Start the XRDP session manager_

tbh = your username

You can enable XRDP to start automatically on boots with the following commands:
```bash
systemctl enable xrdp
systemctl enable xrdp-sesman
```

---

## Enable SSH on Kali Linux
RDP or access the Kali VM via the console. Run `kali-tweaks` in the terminal and select `Hardening-->SSH Client` apply and return to terminal.

##### Generating  Keys for Kali Linux SSH Server
Encryption keys must be needed to create a secure and encrypted session between computers and use securely. The following command is used to generate these keys in Kali Linux.

The first move the original keys form their default directory into a new directory, however, don’t delete them.
```bash
mkdir –p /etc/ssh/original_keys

mv /etc/ssh/ssh_host_* /etc/ssh/original_keys

cd /etc/ssh
```

Generate new keys
```bash
dpkg-reconfigure openssh-server
```

Start and Restart the Kali Linux SSH Server
```bash
service ssh start

service ssh restart
```
