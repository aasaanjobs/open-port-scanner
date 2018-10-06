from nmap import PortScanner

from gcloud import ComputeInstance


PORT_RANGE = "1-100"


class InstancePortScanner:
    def __init__(self, instance: ComputeInstance):
        self.instance = instance
        self.scanner = PortScanner()

    def print_info(self, msg):
        print("[Instance:{}] INFO {}".format(self.instance.name, msg))

    def print_err(self, msg):
        print("[Instance:{}] **ERROR** {}".format(self.instance.name, msg))

    def scan(self):
        results = self.scanner.scan(self.instance.external_ip, PORT_RANGE)
        self.print_info("Executed command: {}".format(self.scanner.command_line()))
        if not results["scan"].get(self.instance.external_ip):
            self.print_err("Failed to scan IP address.")
            return None
        tcp_results = []
        for port, result in results["scan"][self.instance.external_ip].get("tcp", {}).items():
            tcp_results.append({
                "port": port,
                "status": result.get("state")
            })
        return tcp_results
