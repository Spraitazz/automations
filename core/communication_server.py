"""
The communication server awaits for messages on the socket
(file) path defined in the AUTOMATIONS_SOCKET_PATH environment variable.

On receiving messages, in a thread it relays them to the controller,
awaiting for and returning the response.

The admissible messages are one of the following:

automations list
automations start {automation_name}
automations stop {automation_name}
"""

import os
import queue
import socket
import threading

from core.utils import init_default_logger
from core.controller import Controller


class CommunicationServer:

    admissible_commands = ["start", "stop"]

    def __init__(self, automation_controller: Controller):
        socket_path = os.environ.get("AUTOMATIONS_SOCKET_PATH", None)

        if socket_path is None:
            print(
                "AUTOMATIONS_SOCKET_PATH environment variable was not set by "
                "the systemd.service, did you forget to source ~/.bashrc after "
                "running ./setup.sh?"
            )
            exit(0)

        self.socket_path = socket_path
        self.automation_controller = automation_controller

        logger, logs_dir = init_default_logger("communication_server")
        self.logger = logger

    def run(self):
        """
        Start automations configured to run on startup and listen to messages
        sent by socket client, responding on receiving.
        """
        self.automation_controller.start_automations_on_startup()

        if os.path.exists(self.socket_path):
            os.remove(self.socket_path)

        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as server:
            server.bind(self.socket_path)
            server.listen(1)
            print(f"[controller] Listening on {self.socket_path}", flush=True)

            while True:
                conn, _ = server.accept()
                threading.Thread(
                    target=self.handle_client, args=(conn,), daemon=True
                ).start()

    def handle_client(self, conn: socket.socket):
        """
        Act on admissible messages received from the socket client.
        """

        with conn:
            # Spawn a thread to monitor the queue for stop notifications
            threading.Thread(
                target=self._send_notifications,
                args=(conn,),
                daemon=True,
            ).start()

            data = conn.recv(1024).decode().strip()
            self.logger.debug(f"[controller received]: {data}")
            commands = data.split(" ")

            if len(commands) == 1:
                if commands[0] == "list":
                    info = self.automation_controller.get_automations_info()
                    conn.sendall(info.encode())
                else:
                    conn.sendall(f'Command "{data}" is not admissible\n'.encode())

            elif len(commands) == 2:
                command = commands[0]

                if command not in self.admissible_commands:
                    conn.sendall(f'Command "{data}" is not admissible\n'.encode())
                    return

                automation_name = commands[1]

                if command == "start":
                    response = self.automation_controller.start_automation(
                        automation_name
                    )
                else:
                    response = self.automation_controller.stop_automation(
                        automation_name
                    )

                conn.sendall(response.encode())

    def _send_notifications(self, conn: socket.socket):
        """
        Continuously send messages from the shared queue to the client.
        """
        while True:
            try:
                msg = self.automation_controller.message_queue.get(timeout=1.0)
                conn.sendall(msg.encode())
            except queue.Empty:
                # No new messages — continue checking
                continue
            except (BrokenPipeError, ConnectionResetError):
                break