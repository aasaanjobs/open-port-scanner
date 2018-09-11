#!/usr/bin/env python
#  Python script to get IP address of all project vm instances

import os

import time
import googleapiclient.discovery
import sendgrid
from jinja2 import Environment, FileSystemLoader
import nmap  # import nmap.py module

from datetime import datetime
from sendgrid.helpers.mail import *

project = "aj-cloud-staging"
region = "asia-south1"


def get_instance_ip_address_list():
    print("\nAccessing Google Cloud API")
    compute = googleapiclient.discovery.build('compute', 'v1')

    print("Getting IP Addresses ... \n")

    request = compute.addresses().list(project=project, region=region)
    api_result = request.execute()
    return api_result


def execute_port_scan(api_result):
    line_break = '-----------------------------------------------------------------'
    data = []

    items = api_result['items']
    print_ip_metadata(items)

    for instance in items:
        ip_address = instance['address']
        # Optimizing scan to check 10,000 ports since the ones above are rarely used
        port_range = '1-10000'

        scanner = nmap.PortScanner()  # instantiate nmap.PortScanner object
        scanner.scan(ip_address, port_range)
        print("Command: ", scanner.command_line())

        # Key = IP Address
        # Value = List of ports scanned
        ip_address_data = {}

        hosts_list = scanner.all_hosts()
        print("Host scanned: ", hosts_list)
        if len(hosts_list) <= 0:
            print("Host data is missing. "
                  "Host may be down / Scan may have failed or aborted.")
            continue

        for host in hosts_list:
            ip_address_data = {host: []}
            print(line_break)
            host_ = scanner[host]
            hostname = host_.hostname()
            print('Host : %s (%s)' % (host, hostname))

            for protocol in host_.all_protocols():
                print(line_break)
                protocol_ = host_[protocol]

                for port in protocol_:
                    state = protocol_[port]['state']
                    state_label = 'state: %s' % state

                    port_label = '%s:%s' % (protocol, port)

                    port_data = {port_label: state}
                    print(state_label + " state:" + port_label)
                    ip_address_data[host].append(port_data)

            print(line_break)

        data.append(ip_address_data)

    return data


def render_output(data):
    env = Environment(loader=FileSystemLoader('.'))
    template = env.get_template("sample_format.html")
    template_vars = {
        "title": "Port Scanner results",
        "data": data
    }
    return template.render(template_vars)


def print_ip_metadata(ip_list):
    print("Addresses to be scanned:")
    for item in ip_list:
        ip = item['address']
        name = item['name']
        instance_id = item['id']
        print("Instance: " + name + "  -  IP Address: " + ip + "  -  ID: " + instance_id)


def write_output(output_content):
    print(output_content)
    with open("output.html", "w+") as output_file:
        output_file.seek(0)
        output_file.write(output_content)
        print("Saved successfully in file: output.html")


def send_report(report_content):
    # TODO :: Set the value for SENDGRID_API_KEY
    sg = sendgrid.SendGridAPIClient(apikey=os.environ.get('SENDGRID_API_KEY'))

    timestamp = time.time()
    time_now = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
    print("Time now: ", time_now)

    from_email = Email("port.scanner@aasaanjobs.com")
    to_email = Email("asad.khan@aasaanjobs.com")
    subject = "Open port scanner report - " + time_now
    mail_content = Content("text/plain", report_content)
    mail_draft = Mail(from_email, subject, to_email, mail_content)
    response = sg.client.mail.send.post(request_body=mail_draft.get())

    print(response.status_code)
    print(response.body)
    print(response.headers)


if __name__ == "__main__":
    api_response = get_instance_ip_address_list()
    if api_response is None:
        print("Failed to get IP Addresses. Aborting scan")
        exit(1)

    scan_data = execute_port_scan(api_response)
    if len(scan_data) < 1:
        print("Port scanning failed. Exiting.")
        exit(1)

    scan_output = render_output(scan_data)
    write_output(scan_output)
    # send_report(scan_output)
