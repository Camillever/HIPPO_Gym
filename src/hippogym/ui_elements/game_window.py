import base64
import logging
from io import BytesIO
from queue import Queue
from typing import Optional

from PIL import Image

from hippogym.message_handlers.window import WindowMessageHandler


class GameWindow:
    def __init__(
        self,
        in_q: "Queue",
        out_q: "Queue",
        idx=0,
        width=700,
        height=600,
        mode="responsive",
        image=None,
        text=None,
    ) -> None:
        self.id = idx
        self.width = width
        self.height = height
        self.mode = mode
        self.frame = image
        self.text = text
        self.frame_id = 0
        self.pipe = out_q
        self.events: Queue = Queue(maxsize=10)
        self.message_handler = WindowMessageHandler(self, in_q)
        self.message_handler.start()

    def update(self, idx=None, width=None, height=None, mode=None, image=0, text=None):
        if idx is not None:
            self.id = idx
        if width:
            self.width = width
        if height:
            self.height = height
        if mode:
            self.mode = mode
        if width or height or mode:
            self.send_window_size()
        if text:
            self.text = text
            self.frame = None
        if image != 0:
            if type(image) != str:
                self.frame = self.convert_numpy_array_to_base64(image)
            else:
                self.frame = image
            self.text = None
        if text or image:
            self.send_frame()

    def send_window_size(self):
        message = {
            "GameWindow": {
                "id": self.id,
                "size": (self.width, self.height),
                "mode": self.mode,
            }
        }
        self.send(message)

    def send_frame(self):
        message = None
        if self.frame:
            message = {
                "GameWindow": {
                    "id": self.id,
                    "frame": self.frame,
                    "frameId": self.frame_id,
                }
            }
        elif self.text:
            message = {
                "GameWindow": {
                    "id": self.id,
                    "text": self.text,
                    "frameId": self.frame_id,
                }
            }
        if message:
            self.send(message)
            self.frame_id += 1

    def send(self, message=None):
        if not message:
            message = {
                "GameWindow": {
                    "idx": self.id,
                    "size": (self.width, self.height),
                    "mode": self.mode,
                    "frame": self.frame,
                    "frameId": self.frame_id,
                }
            }
        self.pipe.put_nowait(message)

    def hide(self):
        self.send({"GameWindow": None})

    def set_size(self, size):
        self.width = size[0]
        self.height = size[1]

    def add_event(self, event):
        if self.events.full():
            self.get_event()
        self.events.put(event)

    def get_event(self) -> Optional[str]:
        event = None
        if not self.events.empty():
            event = self.events.get()
        return event

    def clear_events(self) -> None:
        if not self.events.empty():
            self.events.get()

    # TODO: add functionality for RGBA array not just RGB
    def convert_numpy_array_to_base64(self, array):
        try:
            img = Image.fromarray(array)
            fp = BytesIO()
            img.save(fp, "JPEG")
            frame = base64.b64encode(fp.getvalue()).decode("utf-8")
            fp.close()
            return frame
        except Exception as e:
            logging.info("Failed to convert numpy array to Base64")
            logging.info(f"Numpy Array conversion error: {e}")
