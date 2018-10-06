import math
import multiprocessing
import os
from datetime import datetime
from typing import List

from jinja2 import Environment, FileSystemLoader
from sendgrid import sendgrid, Email
from sendgrid.helpers.mail import Content, Mail

from gcloud import GCloudProject, ComputeInstance, ComputeInstanceStatus
from port_scan import InstancePortScanner


def run_subprocess(instances: List[ComputeInstance], q: multiprocessing.Queue):
    for instance in instances:
        if instance.status != ComputeInstanceStatus.RUNNING:
            print("Instance {} (Project: {}) is not running.".format(instance.name, instance.project.name))
            continue
        try:
            result = InstancePortScanner(instance).scan()
            if not result:
                continue
            q.put({
                "instance": instance.serialize(),
                "port_results": result
            })
        except Exception as ex:
            print("Failed for Instance {} (Project: {}), reason: {}".format(instance.name, instance.project.name, ex))
            continue


def render_output(context):
    env = Environment(loader=FileSystemLoader('.'))
    template = env.get_template("templates/output_template.html")
    template_vars = {
        "title": "Port Scanner results",
        "data": context
    }
    return template.render(template_vars)


def send_report(html_content):
    sg = sendgrid.SendGridAPIClient(apikey=os.environ.get('SENDGRID_API_KEY'))
    subject = "Open Port Scanner Report - {}".format(datetime.now().strftime("%d %b, %Y"))
    from_email = Email("port.scanner@aasaanjobs.com")
    to_email = Email("sohel.tarir@aasaanjobs.com")
    mail_content = Content("text/html", html_content)
    mail_draft = Mail(from_email, subject, to_email, mail_content)
    response = sg.client.mail.send.post(request_body=mail_draft.get())
    print("Received response from sendgrid: {}".format(response))


def main():
    # Retrieve list of projects
    projects = GCloudProject.list()
    q = multiprocessing.Queue()
    total_instances = []
    for project in projects:
        if project.id not in ("aj-cloud-staging",):
            continue
        print("Fetching list of compute instances for project {}".format(project.name))
        total_instances += ComputeInstance.list(project)
    num_of_processes = multiprocessing.cpu_count()
    per_process_instances = math.ceil(len(total_instances) / num_of_processes)
    jobs = []
    for i in range(num_of_processes):
        start, end = per_process_instances * i, per_process_instances * (i + 1)
        process = multiprocessing.Process(
            target=run_subprocess,
            args=(total_instances[start: end], q)
        )
        jobs.append(process)

    for job in jobs:
        job.start()

    for job in jobs:
        job.join()
    data = []
    while not q.empty():
        data.append(q.get())

    # Send the report via email
    send_report(render_output(data))


if __name__ == "__main__":
    main()
