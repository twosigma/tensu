# Copyright 2022 Two Sigma Open Source, LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# <http://www.apache.org/licenses/LICENSE-2.0>
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from multiprocessing import Process, Queue
from app.defaults import InternalDefaults
from app.sensu_go import SensuGoHelper
from datetime import datetime
from app.utils import Utils
import structlog
import queue


class ResourceHandler:
    """Handles the fetching of Sensu resources.

    ResourceHandler is used by the main loop to make requests within
    the context of a background Process. This ensures there is no
    delay on the main control loop when waiting for IO, or else
    the user experiences becomes choppy.

    API requests are made in a separate process and the results are
    put onto a shared Queue, which is processed by the main control
    loop.
    """

    def __init__(self, state: dict, sensu_go_helper: SensuGoHelper) -> None:
        """Initialize ResourceHandler.

        Inject state and SensuGoHelper as dependencies.
        """

        self.sensu_continue = None
        self.fetch_completed = True
        self.call_update = True
        self.items = []
        self.new_items = []
        self.viewable_items_count = 0
        self.next_update_time = Utils.current_milli_time()
        self.next_fetch_time = Utils.current_milli_time()
        self.last_updated = datetime.utcnow()
        self.state = state
        self.sensu_go_helper = sensu_go_helper
        self.spinner = ["⣾", "⣽", "⣻", "⢿", "⡿", "⣟", "⣯", "⣷"]
        self.spin_index = 0
        self.logger = structlog.get_logger(InternalDefaults.APPNAME)
        self.fetch_process = Process()
        self.q = Queue()

    def __spin(self):
        """Spin! the spinner.

        Returns a string.
        """

        self.spin_index += 1
        if self.spin_index > len(self.spinner) - 1:
            self.spin_index = 0
        return self.spinner[self.spin_index]

    def __is_allowed_to_update(self):
        """Regulates how often to start a new round of fetching.

        Returns True if update_interval_ms has elapsed.
        """

        return Utils.current_milli_time() >= self.next_update_time

    def __is_allowed_to_fetch(self):
        """Regulates how often to make an API request.

        Returns True of fetch_interval_ms has elapsed.
        """

        return Utils.current_milli_time() >= self.next_fetch_time

    def __items_updated(self):
        """Notifies the main loop that new items are available to be drawn."""

        self.viewable_items_count = len(self.items)
        self.last_updated = datetime.utcnow()
        self.callable(self.items)

    def __fetch(self, **kwargs):
        """Processes Responses from the backend API.

        The responses are waiting on the shared Queue.
        If we are allowed to start making requests again, then
        1. Check if there is anything on the Queue to br processed and process it.
        2. If there is a continuation from Sensu in the response,
           then make another request. Append results to new_items.
        3. If there is no continatuion, swap the old data (items) with the
           newly fetched data (new_items).
        """
        self.logger.debug(
            "ResourceHandler__fetch", fetch_interval_ms=self.state["fetch_interval_ms"]
        )
        if self.__is_allowed_to_fetch():
            try:
                err, result = self.q.get_nowait()  # Dont block
                if err:
                    raise Exception(err)
                items = result[0]
                self.sensu_continue = result[1]
                self.logger.debug(
                    "ResourceHandler.__fetch", items=len(items), fetched=True
                )
                self.fetch_status_callable(f"{self.__spin()} Received {len(items)}")
                if not self.sensu_continue:
                    self.fetch_completed = True
                    self.next_update_time = (
                        Utils.current_milli_time() + self.state["update_interval_ms"]
                    )
                    self.items = self.new_items
                else:
                    kwargs["sensu_continue"] = self.sensu_continue
                    self.__resource_fetch_request(**kwargs)  # Starts subprocess
                    self.fetch_completed = False

                self.new_items += items
                if not self.items:
                    self.items += items

                self.next_fetch_time = (
                    Utils.current_milli_time() + self.state["fetch_interval_ms"]
                )

                self.__items_updated()

            except queue.Empty:
                self.logger.debug("ResourceHandler.__fetch", skipped=True)
                self.fetch_status_callable(f"{self.__spin()} Waiting...")

    def __resource_fetch_request(self, **kwargs):
        """Make a Sensu API request in a separate Process.

        The response is stored in a shared Queue.
        """

        self.logger.debug("ResourceHandler.__resource_fetch_request", **kwargs)
        self.fetch_status_callable(f"{self.__spin()} Fetching...")
        self.fetch_process = Process(
            target=self.sensu_go_helper.multi_resource_fetch_request,
            args=(self.q,),
            kwargs=kwargs,
        )
        self.fetch_process.daemon = True
        self.fetch_process.start()

    def kill(self):
        """Immediately stops background request fetching.

        Continually wait for the background worker to terminate cleanly.
        Calling join(1) blocks for 1 second, waiting for fetch_process
        to end. kill() should be followed immeditaly by application shutdown.
        """
        while self.fetch_process.exitcode is None:
            self.logger.debug(
                "ResourceHandler.kill",
                terminated=False,
                waiting=True,
                fetch_process_exit_code=self.fetch_process.exitcode,
            )
            try:
                self.q.get_nowait()
                self.q.close()
            except Exception:
                self.logger.exception(
                    "Exception occured while waiting for fetch background process to"
                    " stop. Ignoring..."
                )
            self.fetch_process.join(1)
        self.logger.debug("ResourceHandler.kill", terminated=True, waiting=False)

    def reset(self):
        """Resets the class to an initial state."""

        self.logger.debug("ResourceHandler.reset")
        self.kill()
        self.q = Queue()
        self.items = []
        self.new_items = []
        self.fetch_completed = True
        self.sensu_continue = None
        self.next_update_time = Utils.current_milli_time()

    def force_call(self):
        """Force callable() on the next call of get_resource_items."""

        self.call_update = True

    def set_callable(self, callable):
        """Takes a function as an argument and sets that as the callable.

        The callable is what function is called when there is new data available.
        """

        self.callable = callable

    def set_fetch_status_callable(self, callable):
        """Takes a function as an argument and sets that as the fetch_status_callable.

        The fetch_status_callable is what function is called
        when we need to update a status message.
        """

        self.fetch_status_callable = callable

    def get_resource_items(self, **kwargs):
        """Requests items from Sensu API backend.

        If we are allowed to start making requests,
        and the last round of fetching is done:
        1. Reset some internal state
        2. Start a new round of fetching in a background process.

        If a fetch process is not completed:
        1. Continue to fetch more data.

        Otherwise: Wait...
        """

        if self.__is_allowed_to_update() and self.fetch_completed:
            self.new_items = []
            self.fetch_completed = False
            kwargs["sensu_continue"] = self.sensu_continue
            self.__resource_fetch_request(**kwargs)
            self.__fetch(**kwargs)
        elif not self.fetch_completed:
            self.__fetch(**kwargs)
        else:
            self.fetch_status_callable(f"{self.__spin()} Waiting...")
        if self.call_update:
            self.callable(self.items)
            self.call_update = False
