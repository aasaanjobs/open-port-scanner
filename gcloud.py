import json
import shlex
import subprocess


class GCloudProject:
    cmd = "gcloud projects list --format json"

    def __init__(self, project_id, project_name):
        self.name = project_name
        self.id = project_id

    @classmethod
    def deserialize(cls, project: dict):
        return cls(project["projectId"], project["name"])

    @classmethod
    def list(cls):
        output = json.loads(subprocess.check_output(shlex.split(cls.cmd)))
        results = []
        for project in output:
            results.append(cls.deserialize(project))
        return results

    def __str__(self):
        return "<GCloud Project: {}>".format(self.name)

    def __repr__(self):
        return self.__str__()


class ComputeInstanceStatus:
    RUNNING = "RUNNING"
    TERMINATED = "TERMINATED"


class ComputeInstance:
    cmd = "gcloud compute instances list --format json --project {}"

    def __init__(self,
                 instance_id,
                 instance_name,
                 project: GCloudProject,
                 external_ip=None,
                 status=None
                 ):
        self.id = instance_id
        self.name = instance_name
        self.project = project
        self.external_ip = external_ip
        self.status = status

    @classmethod
    def deserialize(cls, instance: dict, project: GCloudProject):
        instance_obj = cls(instance["id"], instance["name"], status=instance["status"], project=project)
        if instance_obj.status == ComputeInstanceStatus.RUNNING and len(instance["networkInterfaces"]) and \
                len(instance["networkInterfaces"][0]["accessConfigs"]):
            instance_obj.external_ip = instance["networkInterfaces"][0]["accessConfigs"][0]["natIP"]
        return instance_obj

    def serialize(self):
        return {
            "id": self.id,
            "name": self.name,
            "project": self.project.name,
            "ip": self.external_ip
        }

    @classmethod
    def list(cls, project: GCloudProject):
        output = json.loads(subprocess.check_output(shlex.split(cls.cmd.format(project.id))))
        results = []
        for instance in output:
            results.append(cls.deserialize(instance, project))
        return results

    def __str__(self):
        return "<{}: {}>".format(self.__class__.__name__, self.name)

    def __repr__(self):
        return self.__str__()


def test():
    projects = GCloudProject.list()
    for p in projects:
        if p.id == "aj-cloud-staging":
            return ComputeInstance.list(p)
