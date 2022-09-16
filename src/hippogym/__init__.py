""" HippoGym: A framework for human-in-the-loop experiments. """

import time
from logging import getLogger
from multiprocessing import Process, Queue
from typing import TYPE_CHECKING, Callable, Dict, List, Optional, Tuple


from hippogym.bucketer import bucketer
from hippogym.communicator import Communicator

from hippogym.queue_handler import check_queues

if TYPE_CHECKING:
    from hippogym.recorder.recorder import Recorder
    from hippogym.ui_elements import UIElement

LOGGER = getLogger(__name__)


class HippoGym:
    def __init__(
        self,
        queues: Dict[str, Queue],
        ui_elements: List["UIElement"],
        recorders: List["Recorder"],
    ) -> None:
        self.ui_elements = ui_elements
        self.recorders = recorders

        self._user_id: Optional[str] = None
        self.project_id: Optional[str] = None
        self.run = False
        self.stop = False

        self.queues = queues

        self.communicator = Process(
            target=Communicator,
            args=(self.queues,),
            kwargs={
                "address": "localhost",
                "port": 5000,
                "use_ssl": True,
                "force_ssl": False,
                "fullchain_path": "fullchain.pem",
                "privkey_path": "privkey.pem",
            },
            daemon=True,
        )
        self.communicator.start()

    @property
    def user_id(self) -> Optional[str]:
        return self._user_id

    @user_id.setter
    def user_id(self, new_user_id: Optional[str]):
        if new_user_id is not None:
            LOGGER.info("User connected: %s", new_user_id)
        else:
            LOGGER.info("User disconnected: %s", self._user_id)
        self._user_id = new_user_id

    def start(self) -> None:
        self.stop = False
        self.run = True

    def pause(self) -> None:
        self.run = False

    def end(self) -> None:
        self.run = False
        self.stop = True

    def disconnect(self) -> None:
        self.queues["out_q"].put_nowait("done")
        # self.__init__(False)  # TODO Need an alternative to this

    def group(self, num_groups: int) -> int:
        if self.user_id is None:
            raise TypeError("User must not be None in order to get user group.")
        return bucketer(self.user_id, num_groups)

    def poll(self) -> List[str]:
        return check_queues(
            [
                self.queues["keyboard_q"],
                self.queues["button_q"],
                self.queues["standard_q"],
            ]
        )

    def send(self) -> None:
        for ui_element in self.ui_elements:
            ui_element.send()

    def standby(self, function: Optional[Callable] = None) -> None:
        def _log_standby():
            LOGGER.debug("HippoGym in standby")

        time_printer = TimeActor(lambda: _log_standby(), 2)
        while self.user_id is None:
            time.sleep(0.01)
            time_printer.tick()

        if function:
            function(self)


class TimeActor:
    def __init__(self, func: Callable[[None], None], interval: float) -> None:
        self.start_time = time.time()
        self.last_tick = self.start_time
        self.interval = interval
        self.func = func

    def tick(self):
        now = time.time()
        delta = now - self.last_tick
        if delta >= self.interval:
            self.last_tick = time.time()
            self.func()


def create_queues() -> Dict[str, Queue]:
    keys = [
        "keyboard_q",
        "window_q",
        "button_q",
        "standard_q",
        "control_q",
        "textbox_q",
        "grid_q",
        "info_q",
        "out_q",
    ]
    return {key: Queue() for key in keys}
