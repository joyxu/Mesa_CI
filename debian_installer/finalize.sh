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

echo 'startup_states: highstate' > /etc/salt/minion.d/startup.conf

# Update to Testing
cat > /etc/apt/sources.list <<EOF
deb http://linux-ftp.jf.intel.com/pub/mirrors/debian/ testing main
deb-src http://linux-ftp.jf.intel.com/pub/mirrors/debian/ testing main
EOF

# Add our nfs mount to fstab
echo 'otc-mesa-ci.local:/srv/jenkins       /mnt/jenkins    nfs     _netdev,auto,async,comment=systemd.automount        0       0' >> /etc/fstab

apt-get update -y
for _ in `seq 3`; do
    DEBIAN_FRONTEND=noninteractive \
    APT_LISTCHANGES_FRONTEND=mail \
        apt-get -o Dpkg::Options::="--force-confdef" \
        --force-yes -fuy dist-upgrade
done

# Debian testing has a bug that causes systemd to be uinstalled, but we want
# it.
DEBIAN_FRONTEND=noninteractive \
APT_LISTCHANGES_FRONTEND=mail \
    apt-get -o Dpkg::Options::="--force-confdef" \
    --force-yes -fuy install linux-image-amd64 systemd systemd-sysv

mkdir -p /etc/systemd/network
cat > /etc/systemd/network/eth0.network << EOF
[Match]
Name=eth0

[Network]
DHCP=yes
EOF

rm /etc/resolv.conf
ln -s /run/systemd/resolve/resolv.conf /etc/resolv.conf

# Enable and disable some services
systemctl enable systemd-networkd systemd-resolved avahi-daemon salt-minion
