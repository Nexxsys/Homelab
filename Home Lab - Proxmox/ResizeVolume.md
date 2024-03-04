Steps:
Start with the VM screen in Proxmox.  Select Hardware --> Disk Action --> Resize (add the increment amount of GBs to the VM)

In the VM itself (boot it up and login) - in the terminal:
```bash
df -h
# see the current state
```
![[Pasted image 20220816232616.png]]
Notice above the size is 31 GB for dev/sda5  but we had increased the size in the Proxmox node to be 50 GB.  

```bash
sudo parted /dev/sda

resizepart 2
# enter yes for any warning saying /dev/sda2 is in use
# End?
100%
# repeat for resizepart 5
resizepart 5

# End?
100%

quit

# now enter the following command
sudo resize2fs /dev/sda5
#
```
![[Pasted image 20220816233055.png]]

https://forum.proxmox.com/threads/resize-disk-of-ubuntu-19-10-vm-on-proxmox.70352/

## Resizing Proxmox Volume with LVM
-   **parted** /dev/sdx
    -   print and Fix
    -   resizepart and choose correct partition and 100%FREE flag
-   **pvresize** /dev/sdx
-   **lvextend** -l +100%FREE /dev/mapper/pbs-root
-   **resize2fs** /dev/mapper/pbs-root
https://kb.vander.host/disk-management/how-to-enlarge-an-ext4-disk-on-an-ubuntu-proxmox-vm/
