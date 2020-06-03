# Copyright (C) Intel Corp.  2014-2020.  All Rights Reserved.

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

performance_setup() {
        # Add the master to point at to the machine
        cat > /etc/salt/minion.d/master.conf << EOF
master: 192.168.1.1
master_finger: 1f:69:bc:a8:31:0f:c5:75:17:bc:4f:d6:9e:ab:35:fb:f1:11:19:52:ee:63:27:7f:e8:4b:b1:59:8d:d3:cb:82
EOF

        cat > /etc/salt/minion.d/grain.conf << EOF
grains:
  roles:
    - performance
EOF

        # Add our nfs mount to fstab
        echo 'otc-mesa-android.local:/srv/jenkins       /mnt/jenkins    nfs     _netdev,auto,async,comment=systemd.automount        0       0' >> /etc/fstab

        # Install libpng needed for synmark benchmark
        cd /tmp && wget "http://otc-mesa-android.jf.intel.com/userContent/benchmarks/linux/libpng12-0_1.2.54-6_amd64.deb"
        dpkg -i /tmp/libpng12-0_1.2.54-6_amd64.deb
        cd -
}

conformance_setup() {
        # Add the master to point at to the machine
        cat > /etc/salt/minion.d/master.conf << EOF
master: 192.168.1.1
master_finger: ba:42:e5:d8:e6:3f:ec:ff:a4:7b:c3:cd:24:74:2a:8b
hash_type: md5
EOF

        cat > /etc/salt/minion.d/grain.conf << EOF
grains:
  roles:
    - conformance
EOF

        # Add our nfs mount to fstab
        echo 'otc-mesa-ci.local:/srv/jenkins       /mnt/jenkins    nfs     _netdev,auto,async,comment=systemd.automount        0       0' >> /etc/fstab
        # Add fulsim_cache mount
        echo 'otc-mesa-ci.local:/mnt/space/fulsim_cache       /mnt/fulsim_cache    nfs     _netdev,auto,async,comment=systemd.automount        0       0' >> /etc/fstab
}

mkdir -p /etc/salt/minion.d/

# Options for roles are
# conformance : jenkins test nodes (deqp, piglit, cts, etc)
# performance : jenkins performance testing (trex, etc)
# builder     : jenkins build node
# jenkins     : Jenkins server
if [  $(grep ^otc-gfxperf- /etc/hostname) ]; then
        performance_setup
elif [ $(grep ^otc-gfxtest- /etc/hostname) ]; then
        conformance_setup
else
    echo "Unrecognized hostname. Exiting."
    exit 1
fi

echo 'startup_states: highstate' > /etc/salt/minion.d/startup.conf

# Enable DHCP on any existing and future ethernet interfaces
mkdir -p /etc/systemd/network

cat > "/etc/systemd/network/wired.network" << EOF
[Match]
Name=e*

[Network]
DHCP=yes
EOF

# setup resolve for systemd-resolved
# preserve existing resolv.conf so DNS can be resolved later in this script
mkdir -p /run/systemd/resolve/
mv /etc/resolv.conf /run/systemd/resolve/resolv.conf
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
# copy full grub.cfg to EFI partition to make booting on some systems more
# reliable
[ -d /boot/efi/EFI/debian ] && cp /boot/grub/grub.cfg /boot/efi/EFI/debian/grub.cfg

# Disable S3/suspend/hibernate
systemctl mask sleep.target suspend.target hibernate.target hybrid-sleep.target
sed -i 's|#HandleLidSwitch=suspend|HandleLidSwitch=ignore|' /etc/systemd/logind.conf

# make sure users can execute 'ping'...
chmod u+s /usr/bin/ping

# Enable and disable some services
systemctl enable systemd-networkd systemd-resolved avahi-daemon
systemctl disable networking

#re-enabling debian stable to get salt minion dependencies
echo "deb http://linux-ftp.jf.intel.com/pub/mirrors/debian stable main" >> /etc/apt/sources.list.d/debian_stable.list
proxy="http://proxy-jf.intel.com:911"
cat > /etc/apt/apt.conf.d/99proxy << EOF
Acquire::http::Proxy "http://proxy-jf.intel.com:911";
Acquire::http::Proxy::linux-ftp.jf.intel.com DIRECT;
EOF

apt update
# new dependency for salt modules
apt install python3-distro -y
# install saltstack repo versions of salt packages
mkdir -p /tmp/salt
wget http://otc-mesa-android.jf.intel.com/saltstack/salt-common.deb -O /tmp/salt/salt-common.deb
wget http://otc-mesa-android.jf.intel.com/saltstack/salt-minion.deb -O /tmp/salt/salt-minion.deb

dpkg -i /tmp/salt/salt-common.deb
apt install --fix-broken -y #in case salt deps aren't installed automatically
apt install dctrl-tools python3-systemd init-system-helpers -y #ensure salt-minion prereqs are installed
dpkg -i /tmp/salt/salt-minion.deb

systemctl enable salt-minion
unset proxy
