import base64

from hippogym import HippoGym
from hippogym.ui_elements.control_panel import ControlPanel, image_sliders

images = [
    "logo_vertical.png",
    "icon_dark.png",
    "words_horizontal.png",
    "logo_horizontal.png",
    "icon_light.png",
    "words_vertical.png",
]


def main():
    index = 0
    toggle_sliders = True
    toggle_info = True
    hippo = HippoGym()

    info_panel = hippo.get_info_panel()
    text_box = hippo.add_text_box()
    text_box.update(text="Hello Payas!", buttons=["save", "run", "clear"])
    game_window = hippo.get_game_window()
    game_window.update(
        image=get_image(images[index // len(images)]), width=300, height=300
    )

    control_panel = ControlPanel(hippo.out_q)
    hippo.set_control_panel(control_panel)

    json_recorder = hippo.add_recorder(mode="json", clean_path=True)
    pickle_recorder = hippo.add_recorder()
    hippo.standby()
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
                    info_panel.update(items=[1], kv={"hi": "there", "we": "square"})
                else:
                    info_panel.reset()
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
