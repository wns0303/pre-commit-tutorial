# built-in
import argparse, os, pickle, time
from copy import deepcopy

# need to install
import cv2
from pynput import keyboard
from natsort import natsorted
from win32gui import GetWindowText, GetForegroundWindow

# local module
from _classes import Bbox, Anchor, Image, Zoom, Text, Filehandler, Util


tenkey = {
    "<96>": "0",
    "<97>": "1",
    "<98>": "2",
    "<99>": "3",
    "<100>": "4",
    "<101>": "5",
    "<102>": "6",
    "<103>": "7",
    "<104>": "8",
    "<105>": "9",
}


def on_keypress(key):
    global action, press_cnt, press_shift, pressed_digit, box_on, label_on, saved_bboxes
    current_window_name = GetWindowText(GetForegroundWindow())

    if current_window_name == WINDOW_NAME or current_window_name == ZOOM_WINDOW_NAME:
        key_char = str(key).replace("'", "")
        if key_char in tenkey:
            key_char = tenkey[key_char]

        box_on_mouse = current_img.find_mouse_overed_bbox(mouse_x, mouse_y)
        current_img.mouse_overed_bbox = box_on_mouse

        # 종료 (pynput 콜백에서 cv2 콜백을 건드릴 수가 없었음)
        if key == keyboard.Key.esc:
            action = "ESC"

        # 이미지 앞으로/뒤로 (pynput 콜백에서 cv2 콜백을 건드릴 수가 없었음)
        elif key == keyboard.Key.caps_lock or key == keyboard.Key.left:
            action = "PREVIOUS"

        elif key == keyboard.Key.shift_l:
            if press_shift == True:
                press_shift = False
            else:
                press_shift = True

        elif key == keyboard.Key.tab or key == keyboard.Key.right:
            action = "NEXT"

        # F12키 누르면 현재 이미지 이름을 텍스트 파일에 append
        elif key == keyboard.Key.f12:
            with open(LOG_PATH, "a") as log:
                img_path = current_img.path + "\n"
                log.write(img_path)

        # 숫자 두 번 눌러서 라벨 변경
        elif key_char.isdigit():
            press_cnt += 1
            pressed_digit += key_char

            if press_cnt == 2:
                press_cnt = 0
                action = pressed_digit
                pressed_digit = ""

        # 즉시 라벨 변경

        elif key_char == "f":
            pressed_digit = "04"
            action = pressed_digit
            pressed_digit = ""

        elif key_char == "g":
            pressed_digit = "00"
            action = pressed_digit
            pressed_digit = ""

        elif key_char == "v":
            pressed_digit = "99"
            action = pressed_digit
            pressed_digit = ""

        elif key_char == "b":
            pressed_digit = "01"
            action = pressed_digit
            pressed_digit = ""

        # 라벨 추가/제거
        elif key_char == "q":
            if box_on_mouse:
                box_on_mouse.add_label()

        elif key_char == "r":
            if box_on_mouse:
                saved_bboxes = deepcopy(current_img.bboxes)

                # 박스에 라벨이 하나뿐이면 박스 자체를 지움
                if box_on_mouse.label_cnt == 1:
                    pass
                    current_img.remove_bbox(box_on_mouse)

                else:
                    box_on_mouse.remove_label()

                box_on_mouse = current_img.find_mouse_overed_bbox(mouse_x, mouse_y)
                current_img.mouse_overed_bbox = box_on_mouse

        # 라벨 증가/감소
        elif key_char == "z":
            if box_on_mouse and box_on_mouse.labels:
                last_label = box_on_mouse.labels[-1] - 1
                box_on_mouse.change_label(max(0, last_label))

        elif key_char == "c":
            if box_on_mouse and box_on_mouse.labels:
                last_label = box_on_mouse.labels[-1] + 1
                box_on_mouse.change_label(min(CLASS_MAX_INDEX, last_label))

        # 라벨/텍스트 토글
        elif key_char == "k":
            box_on = not box_on

        elif key_char == "l":
            label_on = not label_on

        # 박스를 다음 이미지로 복사
        elif key_char == "[":
            if box_on_mouse:
                action = "COPY_SINGLEBOX"

        elif key_char == "]":
            action = "COPY_ALL"

        # 현재 이미지에서 모든 박스 제거
        elif key == keyboard.Key.delete:
            saved_bboxes = deepcopy(current_img.bboxes)
            current_img.remove_all_bbox()

        # 마지막으로 지운 박스 복구
        elif key == keyboard.Key.insert:
            current_img.bboxes = saved_bboxes

        # 줌 기능 on/off
        elif key == keyboard.Key.page_up:
            action = "ZOOM_ON"
            Zoom.is_activated = True

        elif key == keyboard.Key.page_down:
            action = "ZOOM_OFF"
            Zoom.is_activated = False

        # 글자 크기 증가/감소
        elif key_char == "+" or key_char == "=":
            Text.set_scale(Text.font_scale + 0.1)

        elif key_char == "-":
            Text.set_scale(Text.font_scale - 0.1)

        # 선 두께 증가/감소
        elif key_char == ".":
            Text.to_thick_line()
            current_img.clear_img()

        elif key_char == ",":
            Text.to_thin_line()
            current_img.clear_img()

        # 박스 위치 픽셀 단위 조정
        # west
        elif key_char == "a":
            if press_shift == True:
                action = "WEST+1"
                if box_on_mouse:
                    box_on_mouse.resize_delta(
                        -1, 0, 0, 0, current_img.width, current_img.height
                    )
            else:
                action = "WEST-1"
                if box_on_mouse:
                    box_on_mouse.resize_delta(
                        1, 0, 0, 0, current_img.width, current_img.height
                    )

        # north
        elif key_char == "w":
            if press_shift == True:
                action = "NORTH+1"
                if box_on_mouse:
                    box_on_mouse.resize_delta(
                        0, -1, 0, 0, current_img.width, current_img.height
                    )
            else:
                action = "NORTH-1"
                if box_on_mouse:
                    box_on_mouse.resize_delta(
                        0, 1, 0, 0, current_img.width, current_img.height
                    )

        # east
        elif key_char == "d":
            if press_shift == True:
                action = "EAST+1"
                if box_on_mouse:
                    box_on_mouse.resize_delta(
                        0, 0, 1, 0, current_img.width, current_img.height
                    )
            else:
                action = "EAST-1"
                if box_on_mouse:
                    box_on_mouse.resize_delta(
                        0, 0, -1, 0, current_img.width, current_img.height
                    )

        # south
        elif key_char == "s":
            if press_shift == True:
                action = "SOUTH+1"
                if box_on_mouse:
                    box_on_mouse.resize_delta(
                        0, 0, 0, 1, current_img.width, current_img.height
                    )
            else:
                action = "SOUTH-1"
                if box_on_mouse:
                    box_on_mouse.resize_delta(
                        0, 0, 0, -1, current_img.width, current_img.height
                    )


# 마우스 콜백
def on_mouse(event, x, y, flags, param):
    global current_img, prev_x, prev_y, mouse_x, mouse_y, is_anchor_activated, saved_bboxes

    mouse_x, mouse_y = x, y
    box_on_mouse = current_img.find_mouse_overed_bbox(x, y)
    current_img.mouse_overed_bbox = box_on_mouse

    if event == cv2.EVENT_LBUTTONDOWN:
        current_img.double_clicked_bbox = None

        if prev_x == -1 and prev_y == -1:
            prev_x = x
            prev_y = y

        else:
            xmin = min(x, prev_x)
            ymin = min(y, prev_y)
            xmax = max(x, prev_x)
            ymax = max(y, prev_y)

            img_w = current_img.width
            img_h = current_img.height
            cx, cy, w, h = Util.render_to_yolo(xmin, ymin, xmax, ymax, img_w, img_h)
            labels = [current_label]

            box = Bbox(labels, cx, cy, w, h, img_w, img_h)

            current_img.append_bbox(box)
            current_img.clear_img()
            current_img.draw_bboxes()
            current_img.draw_labels(label_text, notice_text)

            prev_x, prev_y = -1, -1

    # 줌 윈도우 업데이트
    if event == cv2.EVENT_MOUSEMOVE:
        if box_on_mouse and Zoom.is_activated:
            Zoom.is_window_visible = True
            zoom_window.update(current_img.img_original, box_on_mouse)
        else:
            zoom_window.deactivate()

    # 더블클릭 : 박스 선택
    if event == cv2.EVENT_RBUTTONDBLCLK:
        if box_on_mouse:
            current_img.double_clicked_bbox = box_on_mouse
            is_anchor_activated = True

    # 앵커 잡고 드래그 : 박스 크기 조절
    elif is_anchor_activated and event == cv2.EVENT_MOUSEMOVE and flags:
        if box_on_mouse and anchorbox.find_mouse_overed_anchor(mouse_x, mouse_y):
            anchor_name, anchor_center = anchorbox.find_mouse_overed_anchor(
                mouse_x, mouse_y
            )
            opposit_name, opposit_center = anchorbox.get_opposit_anchor(anchor_name)
            ox, oy = opposit_center

            xmin = min(mouse_x, ox)
            ymin = min(mouse_y, oy)
            xmax = max(mouse_x, ox)
            ymax = max(mouse_y, oy)

            box_on_mouse.resize(
                xmin, ymin, xmax, ymax, current_img.width, current_img.height
            )

    # 박스 바깥 영역 우클릭 : 선택 해제
    elif event == cv2.EVENT_RBUTTONDOWN and not box_on_mouse:
        is_anchor_activated = False


# 트랙바 콜백
def on_trackbar(idx):
    global current_img, img_index, mouse_x, mouse_y

    # 이전 이미지의 박스들 저장
    Filehandler.write_file(current_img.bboxes, current_img.annotaion_path)

    # 새 이미지 로드
    img_index = idx
    current_img_path = IMG_SEQUENCE[img_index]
    current_img = Image(current_img_path)

    print("Showing img {}/{}".format(img_index, SEQUENCE_LENGTH))

    box_on_mouse = current_img.find_mouse_overed_bbox(mouse_x, mouse_y)
    current_img.mouse_overed_bbox = box_on_mouse

    if box_on_mouse and Zoom.is_activated:
        Zoom.is_window_visible = True
        zoom_window.update(current_img.img_original, box_on_mouse)
    else:
        zoom_window.deactivate()

    current_img.draw_bboxes()
    current_img.draw_labels(label_text, notice_text)


def get_img_path(root_path):
    files = natsorted(os.listdir(root_path))
    img_path = []

    for file in files:
        file_path = os.path.join(root_path, file)
        f_name, f_ext = os.path.splitext(file)

        if f_ext in IMG_FORMAT:
            img_path.append(file_path)

    return img_path


# ================================================================ #


t_start = time.time()

parser = argparse.ArgumentParser(description="Open-source image labeling tool")
parser.add_argument(
    "-i", "--input_dir", default="./input", type=str, help="Path to input directory"
)
parser.add_argument(
    "--class_list",
    default="./data/argos_v6.2.txt",
    type=str,
    help="Class label (txt file)",
)
args = parser.parse_args()

# 색상 라벨일 때는 라벨 색을 색상 이름에 맞추기
if "color" in args.class_list:
    Util.color_flag = True

DELAY = 15  # 키보드 입력 딜레이

CLASS_NAMES_PATH = args.class_list
INPUT_PATH = args.input_dir

WINDOW_NAME = "OpenLabeling : Labeling Tool for LRD"
ZOOM_WINDOW_NAME = "Zoom window for Openlabeling"
TRACKBAR_IMG = "Image"

IMG_FORMAT = (".jpg", ".png", ".jpeg", ".PNG", ".JPG", "JPEG")

CLASS_MAX_INDEX = 9999

LOG_PATH = "./data/log.txt"

if __name__ == "__main__":
    print("Welcome to openlabeling.")

    with open(LOG_PATH, "a") as log:
        log_time = time.strftime("%Y-%m-%d", time.localtime(time.time()))
        log.write(log_time + "\n")

    # globals
    action = None

    current_label = 0
    press_cnt = 0
    press_shift = True
    pressed_digit = ""

    click_cnt = 0
    prev_x, prev_y = -1, -1
    mouse_x, mouse_y = -1, -1

    box_on = True
    label_on = True

    is_anchor_activated = False

    saved_bboxes = []

    IMG_SEQUENCE = get_img_path(INPUT_PATH)

    SEQUENCE_LENGTH = len(IMG_SEQUENCE) - 1

    keyboardListener = keyboard.Listener(on_press=on_keypress)
    keyboardListener.start()

    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_KEEPRATIO)
    cv2.resizeWindow(WINDOW_NAME, 1000, 700)
    cv2.setMouseCallback(WINDOW_NAME, on_mouse)
    cv2.createTrackbar(TRACKBAR_IMG, WINDOW_NAME, 0, SEQUENCE_LENGTH, on_trackbar)

    with open(CLASS_NAMES_PATH, "r") as f:
        named_class = list(Util.nonblank_lines(f))

    img_index = 0
    info_dict = dict()
    last_worked_folder = None
    if os.path.isfile("./data/information.pickle"):
        with open("./data/information.pickle", "rb") as f:
            info_dict = pickle.load(f)

            img_index = info_dict["img_index"]
            font_scale = info_dict["font_scale"]
            line_thickness = info_dict["line_thickness"]
            last_worked_folder = info_dict["folder_path"]

            Text.set_scale(font_scale)

    if img_index >= SEQUENCE_LENGTH or INPUT_PATH != last_worked_folder:
        img_index = 0

    t_end = time.time()
    print("loading : ", round(t_end - t_start, 3), "s", sep="")

    current_img_path = IMG_SEQUENCE[img_index]
    current_img = Image(current_img_path)

    notice_text = Text(
        classes=named_class,
        text="Selected label : {}".format(Util.get_class_label(0, named_class)),
    )
    label_text = Text(classes=named_class)

    zoom_window = Zoom(ZOOM_WINDOW_NAME)

    anchorbox = Anchor()

    current_img.draw_bboxes()
    current_img.draw_labels(label_text, notice_text)

    cv2.setTrackbarPos(TRACKBAR_IMG, WINDOW_NAME, img_index)

    while True:
        # 실시간으로 십자선과 클릭 시 따라오는 박스 그리기 (파일에 기록되지는 않고 눈에 보이기만 함)
        color = Util.generate_color(current_label)
        thickness = Text.line_thickness
        cv2.line(
            current_img.img,
            (mouse_x, 0),
            (mouse_x, current_img.height),
            color,
            thickness,
        )
        cv2.line(
            current_img.img,
            (0, mouse_y),
            (current_img.width, mouse_y),
            color,
            thickness,
        )
        cv2.rectangle(
            current_img.img, (prev_x, prev_y), (mouse_x, mouse_y), color, thickness
        )

        if is_anchor_activated:
            clickbox = current_img.double_clicked_bbox
            anchorbox.set_anchors(current_img, clickbox)
            anchorbox.display_anchor(current_img, mouse_x, mouse_y)

        cv2.imshow(WINDOW_NAME, current_img.img)
        _ = cv2.waitKey(DELAY)

        current_img.clear_img()

        if box_on:
            current_img.draw_bboxes()

        if label_on:
            current_img.draw_labels(label_text, notice_text)

        if action:
            box_on_mouse = current_img.find_mouse_overed_bbox(mouse_x, mouse_y)
            current_img.mouse_overed_bbox = box_on_mouse

            if box_on_mouse and Zoom.is_activated:
                Zoom.is_window_visible = True
                zoom_window.update(current_img.img_original, box_on_mouse)
            else:
                zoom_window.deactivate()

            # 라벨 변경
            if action.isdigit():
                current_label = int(action)

                if box_on_mouse:
                    box_on_mouse.change_label(current_label)

                notice_text.set_text(
                    "Selected label : {}".format(
                        Util.get_class_label(current_label, named_class, press_shift)
                    )
                )

            # 종료
            elif action == "ESC":
                break

            # 이전 이미지로
            elif action == "PREVIOUS":
                img_index = max(0, img_index - 1)
                cv2.setTrackbarPos(TRACKBAR_IMG, WINDOW_NAME, img_index)

            # 다음 이미지로
            elif action == "NEXT":
                img_index = min(SEQUENCE_LENGTH, img_index + 1)
                cv2.setTrackbarPos(TRACKBAR_IMG, WINDOW_NAME, img_index)

            # 박스 하나 복사
            elif action == "COPY_SINGLEBOX":
                if box_on_mouse and img_index < SEQUENCE_LENGTH:
                    copy_box = box_on_mouse

                    img_index += 1
                    cv2.setTrackbarPos(TRACKBAR_IMG, WINDOW_NAME, img_index)

                    current_img.append_bbox(copy_box)

            # 박스 전부 복사
            elif action == "COPY_ALL":
                if img_index < SEQUENCE_LENGTH:
                    copy_boxes = current_img.bboxes

                    img_index += 1
                    cv2.setTrackbarPos(TRACKBAR_IMG, WINDOW_NAME, img_index)

                    for box in copy_boxes:
                        current_img.append_bbox(box)

        # 반드시 루프 마지막에 둘 것
        action = None


# Esc로 루프 빠져나오면 파일 처리하고 종료
Filehandler.write_file(current_img.bboxes, current_img.annotaion_path)

if img_index == SEQUENCE_LENGTH:
    img_index = 0
info_dict["img_index"] = img_index
info_dict["font_scale"] = Text.font_scale
info_dict["line_thickness"] = Text.line_thickness
info_dict["folder_path"] = INPUT_PATH
Filehandler.save_progress(info_dict)


cv2.destroyAllWindows()
print("Bye!")
