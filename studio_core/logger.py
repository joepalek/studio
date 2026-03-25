import datetime
import os
from typing import Literal


class Logger:
    """Standardized logging utility for Studio agents.
    Logs messages to console and a dedicated log file per agent.
    """
    LOG_DIR = "studio_logs"

    def __init__(self, agent_id: str, log_to_file: bool = True):
        self.agent_id = agent_id
        self.log_to_file = log_to_file
        self.log_filepath = None
        if self.log_to_file:
            os.makedirs(self.LOG_DIR, exist_ok=True)
            self.log_filepath = os.path.join(self.LOG_DIR, f"{self.agent_id}.log")
            with open(self.log_filepath, 'w') as f:
                f.write(
                    f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "
                    f"[LOGGER] [INFO] Log file initialized for {self.agent_id}\n"
                )

    def log(
        self,
        message: str,
        level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO",
    ):
        """Logs a message with a timestamp, agent ID, and level."""
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        formatted_message = f"[{timestamp}] [{self.agent_id}] [{level}] {message}"
        print(formatted_message)
        if self.log_to_file and self.log_filepath:
            try:
                with open(self.log_filepath, 'a') as f:
                    f.write(formatted_message + "\n")
            except Exception as e:
                print(
                    f"[{timestamp}] [LOGGER] [ERROR] "
                    f"Failed to write to log file {self.log_filepath}: {e}"
                )
