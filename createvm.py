# -*- coding: utf-8 -*-
"""
Created on Set  3 11:16:52 2017

yum install libcurl-devel

@author: enigmatyk
"""
import argparse
import re
import time
from ovirtsdk.api import API
from ovirtsdk.xml import params
import pymysql.cursors
import base64
from beautifultable import BeautifulTable
import sys

# Database connection
DBHOSTNAME = ""
DBUSER = ""
DBPWD = ""
DB = ""

# Main Vars
HOSTNAME = ''
IPADDR = ''
CLUSTER = ''
HOSTTYPE = ''
MEMORY = ''
CPU = ''

# Network Vars
NETMASK = '255.255.255.0'
GATEWAY = '10.0.0.0'
DNS1 = '10.0.0.0'
DNS2 = '10.0.0.0'
DOMAIN = 'domain.local'

# RHV connection
RHVURL = "https://RHEVM.domain.local/ovirt-engine/api"
RHVUSER = "admin@internal"
RHVPWD = ""
CA = "ca.pem"


# Basic functions and testing
def date_now():
    global date
    date = time.strftime("%Y-%m-%d")
    hour = time.strftime("%H:%M:%S")
    assert isinstance(date, object)
    return date


# Testing connection to manager
def manager_connection():
    try:
        api = API(url=RHVURL,
                  username=RHVUSER,
                  password=RHVPWD,
                  ca_file=CA)

        api.disconnect()

    except Exception as ex:
        print ("Can\'t connect to Manager: %s" % ex)
        sys.exit(1)


# Testing connection mysql
def mysql_connection():
    try:
        connection = pymysql.connect(host=DBHOSTNAME,
                                     user=DBUSER,
                                     password=DBPWD,
                                     db=DB,
                                     charset='utf8mb4',
                                     cursorclass=pymysql.cursors.DictCursor)

        connection.close()

    except Exception as mysql_err:
        print ("Can\'t connect to mysql server: %s" % mysql_err)
        sys.exit(1)

# Some obfuscation needed to generate string
def generator():
    # type: () -> object
    global decoded
    encoded = base64.b64encode(b'arg[\1]1x0x1')
    y = re.sub('\=', '', str(encoded))
    from strgen import StringGenerator as y
    secret = y("[\l\d]{8}.").render_list(1, unique=True)
    x = secret
    decoded = re.sub('[u\'\[\]]', '', str(x))
    return decoded


# Life is short, work hard, play harder
def take_some_time():
    print("\nPress the correct keys, take a break and grab a coffee.")
    sys.exit(1)


# Connecting to the database
connection = pymysql.connect(host=DBHOSTNAME,
                             user=DBUSER,
                             password=DBPWD,
                             db=DB,
                             charset='utf8mb4',
                             cursorclass=pymysql.cursors.DictCursor)


# Open cursor and query server
def check_if_exists():
    # global x
    try:
        with connection.cursor() as cursor:
            sql = "SELECT `Machine` FROM `Vmcreated` WHERE `Machine`=%s"
            cursor.execute(sql, (HOSTNAME,))
            x = cursor.fetchone()
            print(x)

        if x is None:
            print ('[INFO] Não existem Registos na BD')
            return
        else:
            a = raw_input("%s already exists on GPGS, do you want insert another record? yes/no : " % HOSTNAME)
            a = a.lower()
            if a == 'yes':
                return
            elif a == 'no':
                print("Script EXIT on confirmation")
                sys.exit(1)
            else:
                take_some_time()

    finally:
        pass


# Insert machine on database
def insert_gpgs():
    try:
        with connection.cursor() as cursor:
            sql = "INSERT INTO `zlinux_memory` ( Machine, Fingerprint, Memory, Date ) VALUES ( %s , %s , %s, %s )"
            cursor.execute(sql, (HOSTNAME, IPADDR, decoded, date))
            connection.commit()
    finally:
        # Don't forget to close a connection
        print ("The root password has generated and inserted on GPG's database for %s :" % HOSTNAME)
        connection.close()


# Import Main vars and args flow control
def main():
    global HOSTNAME
    global IPADDR
    global CLUSTER
    global HOSTTYPE
    global MEMORY
    global CPU
    global ENV
    parser = argparse.ArgumentParser(
        description="\nEXAMPLE: ./%(prog)s -m HOSTNAME -i 10.0.0.0 -r CLUSTER -t TYPE-prd -g 64 -c 4")
    parser.add_argument("-m", "--machine", help="machine hostname", type=str)
    parser.add_argument("-i", "--ipaddr", help="specify ip address", type=str)
    parser.add_argument("-r", "--resource", help="specify resource cluster", type=str)
    parser.add_argument("-t", "--type", help="specify host type (weblogic/dbservers/webservers)", type=str)
    parser.add_argument("-e", "--environment", help="specify the enviroment (DEV/QUA/PRD)", type=str)
    parser.add_argument("-g", "--gigabytes", help="specify memory in gigabytes (default 2G)", default=2, type=int)
    parser.add_argument("-c", "--cpu", help="specify the number of cpus (default 1)", type=int, default=1, )

    # First checks
    args = parser.parse_args()
    if args.machine is None:
        parser.print_help()
        sys.exit(1)
    elif args.type is None or args.ipaddr is None or args.resource is None or args.environment is None:
        parser.print_help()
        sys.exit(1)
    else:
        print(args)

    # Check the type, it's important because post-provisioning
    if args.type in ['weblogic', 'dbservers', 'webservers']:
        pass
    else:
        print ("Please specify the correct host type (weblogic/dbservers/webservers)")
        sys.exit(1)

    # Check the environment
    if args.environment in ['DEV', 'QUA', 'PRD']:
        pass
    else:
        print ("Please specify the correct environment (DEV/QUA/PRD)")
        sys.exit(1)


    # Set vars from options
    HOSTNAME = args.machine
    IPADDR = args.ipaddr
    CLUSTER = args.resource
    HOSTTYPE = args.type
    MEMORY = args.gigabytes
    CPU = args.cpu
    ENV = args.environment


def confirmation():
    table = BeautifulTable()
    table.left_border_char = ''
    table.column_headers = ["", "User Input"]
    table.append_row(["Hostname", HOSTNAME])
    table.append_row(["IP Address", IPADDR])
    table.append_row(["Cluster Resource", CLUSTER])
    table.append_row(["Memory", MEMORY * 1024 ])
    table.append_row(["CPU", CPU])
    table.append_row(["Environment", ENV])
    table.append_row(["HostType", HOSTTYPE])
    table.append_row(["Password", decoded])
    print ("\n")
    print(table)

    # We need to use raw on v2.7
    col1 = raw_input('\nAre you sure about creating VM? yes/no : ')
    col1 = col1.lower()
    if col1 == 'yes':
        vm_create()
    elif col1 == 'no':
        print("User abort operation...")
        sys.exit(1)
    else:
        take_some_time()
    return


# Creating virtual machine
def vm_create():
    global vm_name
    try:
        api = API(url=RHVURL,
                  username=RHVUSER,
                  password=RHVPWD,
                  ca_file=CA)

        # Adding VM Vars to Broker
        vm_name = HOSTNAME
        vm_memory = MEMORY * 1024 * 1024 * 1024
        vm_cluster = api.clusters.get(name=CLUSTER)
        vm_template = api.templates.get("rhel7.4_iso")
        vm_os = params.OperatingSystem(boot=[params.Boot(dev="hd")])
        cpuTopology = params.CpuTopology(cores=CPU, sockets=1)
        vm_cpu = params.CPU(topology=cpuTopology)

        vm_params = params.VM(name=vm_name,
                              memory=vm_memory,
                              cluster=vm_cluster,
                              template=vm_template,
                              cpu=vm_cpu,
                              os=vm_os)

        try:
            api.vms.add(vm=vm_params)
            print ("Virtual machine '%s' successfully created." % vm_name)
            return vm_name


        except Exception as ex:
            # Adding the argument if failed for specific reason
            print ("Creating virtual machine '%s' failed: %s" % (vm_name, ex))
            sys.exit(1)

            # Don't forget to close a connection
            # api.disconnect()
            # print ("ACABOU DE CRIAR")


    except Exception as ex:
        print ("Unexpected error: %s" % ex)


# function to encode the input data to init
def encode(s):
    return re.sub("\s+", "", base64.encodestring(s))

'''
# Prepare the cloud-init to input data
myscript = """\
manage_resolv_conf: true
"""
'''

# Append one file:
ssh_auth = """\
#cloud-config
users:
  - default
  - name: root
    ssh-authorized-keys:
      - ssh-rsa KEY root@machine.domain.local
""" #% encode("The content of the first file")

def pre_provision_vm():
    global vm
    try:
        api = API(url=RHVURL,
                  username=RHVUSER,
                  password=RHVPWD,
                  ca_file=CA)

        try:
            vm = api.vms.get(name=vm_name)
            while not api.vms.get(id=vm.id).status.state == 'down':
                print('Waiting for creating the disk...')
                time.sleep(10)

        except Exception as ex:
            print "Failed to retrieve VM: %s" % ex

        try:
            print "Starting and Provisioning the VM..."
            vm.start(
                action=params.Action(
                    use_cloud_init=True,
                    vm=params.VM(
                        initialization=params.Initialization(
                            user_name='root',
                            root_password='decoded',
                            host_name=vm_name,
                            domain=DOMAIN,
                            timezone='WEST',
                            cloud_init=params.CloudInit(
                                host=params.Host(address=vm_name + '.' + DOMAIN),
                                regenerate_ssh_keys=True,
                                network_configuration=params.NetworkConfiguration(
                                    nics=params.Nics(
                                        nic={params.NIC(
                                            name='eth0',
                                            boot_protocol='STATIC',
                                            on_boot=True,
                                            network=params.Network(
                                                ip=params.IP(
                                                    address=IPADDR,
                                                    netmask=NETMASK,
                                                    version='V4',
                                                    gateway='GATEWAY'
                                                )
                                            )
                                        )
                                        }
                                    )
                                )
                            ),
                            dns_servers='DNS1 + DNS2',
                            dns_search='domain.local',
                            custom_script = ssh_auth
                        )
                    )
                )
            )

            # Always remember to disconnect from the server:
            api.disconnect()

        except Exception as ex:
            print "Failed to start VM: %s" % ex

    except Exception as ex:
        print "Failed to start VM: %s" % ex


def env_provisioning():
    global tmpfile
    # Ready for multiple setup's at the same time
    list = [HOSTNAME]
    if ENV == "QUA":
        file_to_open = "hosts_qua"
    elif ENV == "DEV":
        file_to_open = "hosts_dev"
    else:
        file_to_open = "hosts_prd"

    inputfile = open(file_to_open, 'r').readlines()
    write_file = open(file_to_open, 'w')
    for line in inputfile:
        write_file.write(line)
        if HOSTTYPE in line:
            for item in list:
                new_line = "%s" % (item)
                write_file.write(new_line + "\n")
    write_file.close()

    # addvm
    tmpfile = 'tmp.yml'
    file = open(tmpfile, 'w')

    file.write('---' + '\n')
    file.write('hostname: ' + HOSTNAME + '\n')
    file.write('fqdn: ' + HOSTNAME + '.' + DOMAIN + '\n')
    file.write('ipaddr: ' + IPADDR + '\n')
    file.write('activationkey: LINUX_' + ENV + '_RHEL7' + '\n')

    file.close()

    # Falta a execução do ansible para terminar o aprovisionamento e fechar
    # ficheiros de configuração para fazer upload


if __name__ == '__main__':
    main()

# Functions
manager_connection()
mysql_connection()
generator()
date_now()
check_if_exists()
confirmation()
pre_provision_vm()
env_provisioning()
insert_gpgs()


