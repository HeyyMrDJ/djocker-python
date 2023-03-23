"""Simple container runtime written in Python"""

import os


# Globals
btrfs_path = '/var/djocker'
pen_id = "TEST02"
ip_addr = "02"
mac = ":02"


def install():
    """Verify settings and set up prereqs"""
    with open("/proc/sys/net/ipv4/ip_forward", "r") as f:
        if f.read() != r"1\n":
            ip_foward = False

    if ip_foward is False:
        print("ERROR: IP Forwarding is not enabled")
        print("Please enable with \'sysctl -w net.ipv4.ip_forward=1\'")
        print("Actually I will enable for you")
        os.system('sudo sysctl -w net.ipv4.ip_forward=1')

    with open('/etc/hosts', 'a') as hosts_file:
        hosts_file.write('127.0.0.1 ' + os.uname()[1] + '\n')

    os.system('sudo ip link add bridge0 type bridge')
    os.system('sudo ip addr add 10.0.0.1/24 dev bridge0')
    os.system('sudo ip link set bridge0 up')

    os.system('sudo iptables -t nat -A POSTROUTING -o bridge0 -j MASQUERADE')

    os.system('fallocate -l 1G ~/btrfs.img')
    os.system('mkfs.btrfs ~/btrfs.img')
    os.system(f'sudo mkdir {btrfs_path}')
    os.system(f'sudo mount -o loop ~/btrfs.img {btrfs_path}')


def create(pen_id, ip_addr, mac, btrfs_path):
    """Create namespaces, and copy needed files and libraries over for chroot"""
    # Networking
    os.system(f"sudo ip link add dev veth0_{pen_id} type veth peer name veth1_{pen_id}")
    os.system(f"sudo ip link set dev veth0_{pen_id} up")
    os.system(f"sudo ip link set veth0_{pen_id} master bridge0")
    os.system(f"sudo ip netns add netns_{pen_id}")
    os.system(f"sudo ip link set veth1_{pen_id} netns netns_{pen_id}")
    os.system(f"sudo ip netns exec netns_{pen_id} ip link set dev lo up")
    os.system(f"sudo ip netns exec netns_{pen_id} ip link set veth1_{pen_id} address 02:42:ac:11:00{mac}")
    os.system(f"sudo ip netns exec netns_{pen_id} ip addr add 10.0.0.{ip_addr}/24 dev veth1_{pen_id}")
    os.system(f"sudo ip netns exec netns_{pen_id} ip link set dev veth1_{pen_id} up")
    os.system(f"sudo ip netns exec netns_{pen_id} ip route add default via 10.0.0.1")

    # Storage Snapshot
    os.system(f"sudo btrfs subvolume snapshot {btrfs_path}/ {btrfs_path}/{pen_id} > /dev/null")

    # Copy needed files and libraries
    os.system(f"sudo mkdir {btrfs_path}/{pen_id}/etc")
    os.system(f"sudo mkdir {btrfs_path}/{pen_id}/bin")
    os.system(f"sudo mkdir {btrfs_path}/{pen_id}/lib")
    os.system(f"sudo mkdir {btrfs_path}/{pen_id}/lib64")
    os.system(f"sudo cp /bin/sh {btrfs_path}/{pen_id}/bin/")
    os.system(f"sudo cp /bin/ls {btrfs_path}/{pen_id}/bin/")
    os.system(f"sudo cp /lib/x86_64-linux-gnu/libc.so.6 {btrfs_path}/{pen_id}/lib/")
    os.system(f"sudo cp /lib64/ld-linux-x86-64.so.2 {btrfs_path}/{pen_id}/lib64/")
    os.system(f"sudo cp /lib/x86_64-linux-gnu/libselinux.so.1 {btrfs_path}/{pen_id}/lib/")
    os.system(f"sudo cp /lib/x86_64-linux-gnu/libpcre2-8.so.0 {btrfs_path}/{pen_id}/lib/")
    os.system(f"sudo cp /lib/x86_64-linux-gnu/libpthread.so.0 {btrfs_path}/{pen_id}/lib/")
    os.system(f"sudo touch {btrfs_path}/{pen_id}/etc/resolv.conf")
    os.system(f"sudo chmod 777 {btrfs_path}/{pen_id}/etc/resolv.conf")

    with open(f"{btrfs_path}/{pen_id}/etc/resolv.conf", "w") as file:
        file.write("nameserver 8.8.8.8\n")


def exec_pen(pen_id):
    """Enter Namespace"""
    os.system(f'sudo ip netns exec netns_{pen_id} unshare \\\n'
              f'sudo chroot "{btrfs_path}/{pen_id}" /bin/sh')


def port_forward(dest_ip, dest_port, source_port):
    """Port forward to Pen"""
    os.system(f'sudo iptables -t nat -A PREROUTING -p tcp --dport {source_port} -j DNAT --to-destination {dest_ip}:{dest_port}')


install()
create(pen_id, ip_addr, mac, btrfs_path)
port_forward("10.0.0.2", "8080", "8081")
exec_pen("TEST02")
