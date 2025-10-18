"""
The automations service entry file, ran by the user systemd.service on its
ExecStart (see setup.sh).
"""

from core.controller import Controller
from core.communication_server import CommunicationServer


def run_service():
    controller = Controller()
    communication_server = CommunicationServer(controller)
    communication_server.run()  # blocking


if __name__ == "__main__":
    run_service()
