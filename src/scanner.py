# Python script to get IP address of all project vm instances

import os

import time
import googleapiclient.discovery
import sendgrid

from datetime import datetime
from sendgrid.helpers.mail import *

project = "aj-cloud-staging"
region = "asia-south1"


def get_instance_ip_address_list():
    print("\nAccessing google client API\n")
    compute = googleapiclient.discovery.build('compute', 'v1')

    print("Getting Addresses")
    request = compute.addresses().list(project=project, region=region)
    api_result = request.execute()
    return api_result


def execute_port_scan(api_result):
    if api_result is not None:
        ip_list = api_result['items']

        print_ip_metadata(ip_list)

        for item in ip_list:
            ip = item['address']
            command = "nmap -sV -p- " + ip + " -Pn"
            os.system('output="$(' + command + ')"; echo $output >> output.txt; echo "\n" >> output.txt')

        print("Completed scans of all IPs. Please find report in output.txt")
        return True
    else:
        print("IP addresses couldn't be retrieved... Error occurred")
        print(api_result)
        return False


def print_ip_metadata(ip_list):
    print("Addresses to be scanned:")
    for item in ip_list:
        ip = item['address']
        name = item['name']
        instance_id = item['id']
        print("Instance: " + name + "  -  IP Address: " + ip + "  -  ID: " + instance_id)


def send_report(file_contents):
    sg = sendgrid.SendGridAPIClient(apikey=os.environ.get('SENDGRID_API_KEY'))

    timestamp = time.time()
    time_now = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
    print("Time now: ", time_now)

    from_email = Email("port.scanner@aasaanjobs.com")
    to_email = Email("asad.khan@aasaanjobs.com")
    subject = "Open port scanner report - " + time_now
    mail_content = Content("text/plain", file_contents)
    mail_draft = Mail(from_email, subject, to_email, mail_content)
    response = sg.client.mail.send.post(request_body=mail_draft.get())

    print(response.status_code)
    print(response.body)
    print(response.headers)

    # Clear file contents
    os.system('echo "\n" > output.txt')


def get_output_content():
    with open("output.txt", "r") as output_file:
        file_content = output_file.read()
        print("File Content: ", file_content)
        return file_content


if __name__ == "__main__":
    api_response = get_instance_ip_address_list()
    scan_success = execute_port_scan(api_response)
    if scan_success:
        content = get_output_content()
        send_report(content)
    else:
        print("Scanning Failed!")
