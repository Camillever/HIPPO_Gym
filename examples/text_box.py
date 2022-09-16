import base64
import logging

from hippogym import HippoGym, create_queues
from hippogym.event_handler import EventsQueues
from hippogym.ui_elements import (
    InfoPanel,
    TextBox,
    ControlPanel,
    GameWindow,
    image_sliders,
    standard_controls,
)
from hippogym.recorder.recorder import Recorder

images = [
    "logo_vertical.png",
    "icon_dark.png",
    "words_horizontal.png",
    "logo_horizontal.png",
    "icon_light.png",
    "words_vertical.png",
]

logging.basicConfig(level=20)


def main():
    index = 0
    toggle_sliders = True
    toggle_info = True
    queues = create_queues()
    out_q = queues[EventsQueues.OUTPUT]

    info_panel = InfoPanel(queues[EventsQueues.INFO_PANEL], out_q=out_q)

    text_box = TextBox(
        queues[EventsQueues.TEXTBOX],
        out_q=out_q,
        text="Hello World!",
        buttons=["save", "run", "clear"],
    )

    game_window = GameWindow(
        in_q=queues[EventsQueues.WINDOW],
        out_q=out_q,
        image=get_image(images[index // len(images)]),
        width=300,
        height=300,
    )

    json_recorder = Recorder(mode="json", clean_path=True)
    pickle_recorder = Recorder(mode="pickle")

    hippo = HippoGym(
        queues=queues,
        ui_elements=[info_panel, text_box, game_window],
        recorders=[json_recorder, pickle_recorder],
    )
    control_panel = ControlPanel(
        queues[EventsQueues.CONTROL_PANEL],
        out_q=out_q,
        hippo=hippo,
        buttons=standard_controls,
    )
    hippo.ui_elements.append(control_panel)

    hippo.standby()
    hippo.send()

    while True:
        for item in hippo.poll():
            button = item.get("BUTTONPRESSED", None)
            if button == "save":
                text_box.request()
                text = text_box.get_text()
                print(text)
                json_recorder.record({"text": text})
                pickle_recorder.record({"text": text})
            action = item.get("ACTION", None)
            if action == "right":
                index += 1
                game_window.update(image=get_image(images[index % len(images)]))
                control_panel.send()
            elif action == "left":
                index -= 1
                game_window.update(image=get_image(images[index % len(images)]))
            elif action == "up":
                if toggle_sliders:
                    control_panel.update(sliders=image_sliders)
                else:
                    control_panel.update(sliders=[])
                toggle_sliders = not toggle_sliders
            elif action == "down":
                if toggle_info:
                    info_panel.update(
                        text="Hello world!",
                        items=[1],
                        key_value={"hi": "there", "dear": "human"},
                    )
                else:
                    info_panel.update(text="", items=[], key_value={})
                toggle_info = not toggle_info
            elif action == "fire":
                text_box.send()


def tryme(hg):
    print(hg)
    print("hello, this worked")


def get_image(filename):
    with open(f"img/{filename}", "rb") as infile:
        frame = base64.b64encode(infile.read()).decode("utf-8")
    return frame


if __name__ == "__main__":
    main()
