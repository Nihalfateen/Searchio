"""Heterogenous memory monitor for Python. It should work in all OS."""
import logging  # use for structured logging
import os  # to interact with the operating system
import threading  # to create a background thread
import time  # to add delays between memory checks and sleep intervals
from dataclasses import dataclass  # to create a simple configuration class

import psutil  # to monitor system and process information

logger = logging.getLogger(__name__)


@dataclass
class MemoryMonitorConfig:
    limit_mb: int #maximum allowed memory usage in MB (if exceeded, program crashes).
    interval_sec: float #time interval (in seconds) between memory usage checks.
    memory_updates: bool = True #whether to print memory usage updates to the console.


def start_memory_monitor(show_memory_updates: bool = False):
    """Initializes and starts a background thread to monitor memory usage.

    The thread is set as a "daemon" so it will exit automatically when the
    main program finishes.
    """

    memory_config = MemoryMonitorConfig(
        limit_mb=2000, interval_sec=0.5, memory_updates=show_memory_updates
    )
    monitor_thread = threading.Thread(
        target=memory_monitor_worker, args=(memory_config,), daemon=True
    )
    logger.info(
        f"[MemoryGuard] Monitoring started. Crashing if usage exceeds {memory_config.limit_mb} MB."
    )
    monitor_thread.start()


def memory_monitor_worker(memory_config: MemoryMonitorConfig):
    """The worker function that runs in the background.

    It periodically checks the current process's memory usage.
    """
    # Get the current process object
    current_process = psutil.Process(os.getpid())

    while True:
        try:
            # Get the resident set size (RSS) memory usage in bytes.
            # RSS is a good representation of the actual physical memory the process is using.
            rss_memory_bytes = current_process.memory_info().rss
            rss_memory_mb = rss_memory_bytes / (1024 * 1024)

            if memory_config.memory_updates:
                print(f"\r[MemoryGuard] Current usage: {rss_memory_mb:.2f} MB", end="")

            if rss_memory_mb > memory_config.limit_mb:
                logger.error(
                    f"\n\n[MemoryGuard] CRITICAL: Memory usage ({rss_memory_mb:.2f} MB) exceeded"
                    f" the limit of {memory_config.limit_mb} MB. Terminating program."
                )

                # Use os._exit(1) for an immediate, forceful exit.
                # This is more abrupt than sys.exit() and suitable for a "crash".
                os._exit(1)

        except psutil.NoSuchProcess:
            # The process might have already exited, so we can stop the thread.
            break
        except Exception as e:
            logger.error(f"\n[MemoryGuard] Error in memory monitor: {e}")
            break

        time.sleep(memory_config.interval_sec)
