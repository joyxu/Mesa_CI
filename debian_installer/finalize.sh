# Copyright (C) Intel Corp.  2014.  All Rights Reserved.

# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:

# The above copyright notice and this permission notice (including the
# next paragraph) shall be included in all copies or substantial
# portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE COPYRIGHT OWNER(S) AND/OR ITS SUPPLIERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

#  **********************************************************************/
#  * Authors:
#  *   Dylan Baker <dylanx.c.baker@intel.com>
#  **********************************************************************/

mkdir -p /etc/salt/minion.d/

# Add the master to point at to the machine
cat > /etc/salt/minion.d/master.conf << EOF
master: 192.168.1.1
master_finger: ba:42:e5:d8:e6:3f:ec:ff:a4:7b:c3:cd:24:74:2a:8b
hash_type: md5
EOF

# Options for roles are
# conformance : jenkins test nodes (deqp, piglit, cts, etc)
# performance : jenkins performance testing (trex, etc)
# builder     : jenkins build node
# jenkins     : Jenkins server
cat > /etc/salt/minion.d/grain.conf << EOF
grains:
  roles:
    - conformance
EOF

echo 'startup_states: highstate' > /etc/salt/minion.d/startup.conf

# Add our nfs mount to fstab
echo 'otc-mesa-ci.local:/srv/jenkins       /mnt/jenkins    nfs     _netdev,auto,async,comment=systemd.automount        0       0' >> /etc/fstab

# Create a systemd .network file for the network interfac
name=$(ip addr show scope link up | grep -v DOWN | grep UP | awk '{print $2}' | sed 's@:@@')

mkdir -p /etc/systemd/network

cat > "/etc/systemd/network/${name}.network" << EOF
[Match]
Name=${name}

[Network]
DHCP=yes
EOF

# python-tornado in testing is >=5, which is incompatible with salt-minion
proxy="http://proxy.jf.intel.com:911"
cat > /etc/apt/apt.conf.d/99proxy << EOF
Acquire::http::Proxy "http://proxy.jf.intel.com:911";
Acquire::http::Proxy::linux-ftp.jf.intel.com DIRECT;
EOF
apt install gpg -y
https_proxy=$proxy wget https://repo.saltstack.com/apt/debian/9/amd64/latest/SALTSTACK-GPG-KEY.pub
apt-key add SALTSTACK-GPG-KEY.pub
# use 2017.7 repo because latest repo is 'too new' with salt on the master
echo "deb http://repo.saltstack.com/apt/debian/9/amd64/2017.7 stretch main" > /etc/apt/sources.list.d/saltstack.list
http_proxy=$proxy wget http://ftp.cz.debian.org/debian/pool/main/p/python-tornado/python-tornado_4.4.3-1_amd64.deb
apt update
apt install gdebi-core -y
gdebi -n python-tornado_4.4.3-1_amd64.deb
apt install salt-minion salt-common -y
rm -f python-tornado_4.4.3-1_amd64.deb SALTSTACK-GPG-KEY.pub
unset proxy

# setup resolve for systemd-resolved
rm /etc/resolv.conf
ln -s /run/systemd/resolve/resolv.conf /etc/resolv.conf

# Remove interfaces to keep debian's interfaces from coming up as well as systemd
rm /etc/network/interfaces

# Copy the loader from ${EFI}/debian/grubx64.efi to ${EFI}/boot/bootx64.efi
# This is a work-around for broken EFI implementations.
mkdir -p /boot/efi/EFI/boot/
cp /boot/efi/EFI/debian/grubx64.efi /boot/efi/EFI/boot/bootx64.efi

# linux-image-amd64 does not generate an initrd in all cases, for some reason.
update-initramfs -c -k $(apt show linux-image-amd64 2>/dev/null| grep Depends| awk -F'image-' '{print $2}')
update-grub

# Enable and disable some services
systemctl enable systemd-networkd systemd-resolved avahi-daemon salt-minion
systemctl disable networking
