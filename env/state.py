# from env.parse_layout import parse_layout
from env.parse_layout2 import parse_layout
import logging
from env.state_util import check_is_confirm_button
import re


class State:
    def __init__(self, state_id: int, screen_info: dict, new_state=False, need_rotate=False):
        self.state_id = state_id
        self.new_state = new_state
        self.need_rotate = need_rotate
        self.activity = screen_info["activity"]
        self.xml_path = screen_info["xml_path"]
        self.img_path = screen_info["img_path"]
        # self.all_views, self.clickable_views = parse_layout(self.xml_path)
        self.all_views, self.clickable_views, self.page_type, self.widget_group = parse_layout(self.xml_path)
        self.actions = dict()
        self.name2action = dict()
        self.action_groups = []
        self.init_action()
        self.action_count = len(self.actions.keys())

    def get_view_count(self):
        return len(self.all_views.keys())

    def get_state_hash(self):
        state_symbol = self.activity
        # if len(self.all_views.keys()) <= 10:
        if len(self.actions.keys()) > 2 and self.actions[1]["type"] == "system_rotate":
            temp_action_count = self.action_count - 1
        else:
            temp_action_count = self.action_count
        if (temp_action_count <= 4 and len(self.all_views.keys()) < 25) or self.action_count <= 2:
            for view_key, view in self.all_views.items():
                if view["text"] != None and view["text"].lower() != "none" and "edittext" not in view["class"].lower():
                    state_symbol += view_key + view["text"]
                else:
                    state_symbol += view_key
            # print(self.state_id, ":", state_symbol)
        else:
            all_key = set()
            for view_key in self.all_views.keys():
                if "listview" in view_key.lower() or "recyclerview" in view_key.lower():
                    clean_view_key = re.sub(r"\[\d+]", "[*]", view_key)
                    all_key.add(clean_view_key)
                else:
                    all_key.add(view_key)
            state_symbol = self.activity + "".join(all_key)
        hash_symbol = hash(state_symbol)
        return hash_symbol

    def init_action(self):
        # first action is back!
        back_action = {"refer_name": "system back", "is_scroll": False, "xpath": "", "type": "system_back",
                       "content": "", "class": "system_back", "bounds": [[175, 1785], [305, 1915]]}
        self.actions.setdefault(0, back_action)
        # second action is need rotate, if crash need
        if self.need_rotate:
            rotate_action = {"refer_name": "system rotate", "is_scroll": False, "xpath": "", "type": "system_rotate",
                             "content": "", "class": "system_back", "bounds": [[0, 0], [0, 0]]}
            self.actions.setdefault(1, rotate_action)

        has_edittext = False
        for view_xpath, view_info in self.clickable_views.items():
            if "edittext" in view_info["class"].lower():
                has_edittext = True
                break
        find_fill_info = False
        exclude_widget = ["client certificate", "advanced options", "download", "flip cycle interval", "voice search",
                          "clear recent list", "language"]
        edittext_view_infos = []
        for container_type, containers in self.widget_group.items():
            for container_id, widgets in containers.items():
                cur_action_names = set()
                for view_xpath in widgets:
                    view_info = self.clickable_views[view_xpath]
                    cur_action_name = self.get_action_name(view_info["refer_name"])
                    exclude_link = "http://" in view_info["text"] or "https://" in view_info["text"]
                    too_long = len(view_info["text"].split(" ")) > 10
                    # cur_action_names.add(cur_action_name)
                    # todo: set scroll
                    if view_info["clickable"] and cur_action_name.lower() not in exclude_widget and "edittext" not in \
                            view_info["class"].lower() and not exclude_link and not too_long:
                        cur_action_id = self.new_action(view_info, "click")
                        cur_action_names.add(cur_action_name)
                    if view_info["long_clickable"] and "edittext" not in view_info["class"].lower() and not too_long:
                        cur_action_id = self.new_action(view_info, "long_click")
                        cur_action_names.add(cur_action_name)
                    # todo: set editText input content
                    if "edittext" in view_info["class"].lower():
                        # cur_action_id = self.new_action(view_info, "input")
                        # block EditText, only when can't find fill button can fill
                        edittext_view_infos.append(view_info)
                    # todo: confirm button (fill all info and click ok)
                    if has_edittext and check_is_confirm_button(view_info):
                        cur_action_id = self.new_action(view_info, "fill_info")
                        cur_action_names.add(cur_action_name)
                        find_fill_info = True
                cur_container = {"container_type": container_type, "action_names": cur_action_names}
                self.action_groups.append(cur_container)
        if has_edittext and not find_fill_info:
            for view_info in edittext_view_infos:
                cur_action_id = self.new_action(view_info, "input")
        for action_id, info in self.actions.items():
            self.log_action(action_id, info)
        # for t in self.action_group:
        #     print(t)
        # print(self.name2action)

        # for view_xpath, view_info in self.clickable_views.items():
        #     cur_action_name = self.get_action_name(view_info["refer_name"])
        #     # todo: set scroll
        #     if view_info["clickable"] and "edittext" not in view_info["class"].lower():
        #         action_info = self.init_action_info(view_info)
        #         cur_action_id = len(self.actions.keys())
        #         action_info["type"] = "click"
        #         self.actions.setdefault(cur_action_id, action_info)
        #     if view_info["long_clickable"] and "edittext" not in view_info["class"].lower():
        #         action_info = self.init_action_info(view_info)
        #         cur_action_id = len(self.actions.keys())
        #         action_info["type"] = "long_click"
        #         self.actions.setdefault(cur_action_id, action_info)
        #     # todo: set editText input content
        #     # block EditText
        #     # if "edittext" in view_info["class"].lower():
        #     #     action_info = self.init_action_info(view_info)
        #     #     cur_action_id = len(self.actions.keys())
        #     #     action_info["type"] = "input"
        #     #     action_info["content"] = "HelloWorld"
        #     #     self.actions.setdefault(cur_action_id, action_info)
        #     # todo: confirm button (fill all info and click ok)
        #     if has_edittext and check_is_confirm_button(view_info):
        #         action_info = self.init_action_info(view_info)
        #         cur_action_id = len(self.actions.keys())
        #         action_info["type"] = "fill_info"
        #         self.actions.setdefault(cur_action_id, action_info)
        # for action_id, info in self.actions.items():
        #     self.log_action(action_id, info)

    def init_action_info(self, view_info: dict):
        # todo: delete this old method
        action_info = {"refer_name": view_info["refer_name"], "is_scroll": False, "xpath": view_info["xpath"],
                       "type": "", "content": "", "class": view_info["class"].split(".")[-1],
                       "bounds": view_info["bounds"], "action_name": self.get_action_name(view_info["refer_name"])}
        return action_info

    def new_action(self, view_info: dict, action_type: str):
        action_info = {"refer_name": view_info["refer_name"], "is_scroll": False, "xpath": view_info["xpath"],
                       "type": action_type, "content": "", "class": view_info["class"].split(".")[-1],
                       "bounds": view_info["bounds"], "action_name": self.get_action_name(view_info["refer_name"])}
        if action_type == "input":
            action_info["content"] = "HelloWorld!"
        cur_action_id = len(self.actions.keys())
        # action_info["type"] = "fill_info"
        self.actions.setdefault(cur_action_id, action_info)
        cur_action_name = self.get_action_name(view_info["refer_name"])
        if cur_action_name not in self.name2action.keys():
            self.name2action.setdefault(cur_action_name, [])
        self.name2action[cur_action_name].append(cur_action_id)
        return cur_action_id

    def log_action(self, action_id, action_info):
        if self.new_state:
            logging.info("\tfind [" + str(action_id) + "] " + action_info["type"] + ": " + action_info[
                "refer_name"] + " (" + action_info["class"] + ", " + str(action_info["bounds"]) + ")")

    def get_state_detail(self):
        return self.action_groups, self.name2action

    def get_state_detail_old(self):
        view_name_map = dict()
        view_names = []
        for action_id, action_info in self.actions.items():
            ori_refer_name = action_info["refer_name"]
            clean_name = re.sub("[^a-z0-9]", " ", ori_refer_name.lower())
            clean_name = re.sub("\s+", " ", clean_name).strip()
            clean_name2 = re.sub("[^a-z]", "", ori_refer_name.lower())
            if len(clean_name2) <= 1 or len(clean_name.split()) == 0 or clean_name == "none":
                view_name = "other"
            elif len(clean_name.split()) > 4:
                name_token = clean_name.split()
                view_name = " ".join(name_token[:4]) + " ..."
            else:
                view_name = clean_name
            if view_name not in view_name_map.keys():
                view_name_map.setdefault(view_name, [action_id])
                view_names.append(view_name)
            else:
                view_name_map[view_name].append(action_id)
        return view_names, view_name_map

    def get_action_name(self, ori_refer_name: str):
        ori_refer_name = ori_refer_name.replace("<unknown>", "")
        clean_name = re.sub("[^a-z0-9]", " ", ori_refer_name.lower())
        clean_name = re.sub("\s+", " ", clean_name).strip()
        clean_name2 = re.sub("[^a-z]", "", ori_refer_name.lower())
        if len(clean_name2) <= 1 or len(clean_name.split()) == 0 or clean_name == "none":
            action_name = "other"
        elif len(clean_name.split()) > 4:
            name_token = clean_name.split()
            action_name = " ".join(name_token[:4]) + " ..."
        else:
            action_name = clean_name
        if len(action_name.strip()) > 0:
            return action_name.strip()
        else:
            return "other"

    def get_refer_names(self):
        # todo: delete this old method
        view_name_map = dict()
        refer_names = []
        for action_id, action_info in self.actions.items():
            ori_refer_name = action_info["refer_name"]
            clean_name = re.sub("[^a-z0-9]", " ", ori_refer_name.lower())
            clean_name = re.sub("\s+", " ", clean_name).strip()
            clean_name2 = re.sub("[^a-z]", "", ori_refer_name.lower())
            if len(clean_name2) <= 1 or len(clean_name.split()) == 0 or clean_name == "none":
                view_name = "other"
            elif len(clean_name.split()) > 4:
                name_token = clean_name.split()
                view_name = " ".join(name_token[:4]) + " ..."
            else:
                view_name = clean_name
            if view_name not in view_name_map.keys():
                view_name_map.setdefault(view_name, [action_id])
                refer_names.append(view_name)
            else:
                view_name_map[view_name].append(action_id)
        return refer_names, view_name_map


if __name__ == '__main__':
    # screen_info = {}
    # open("../Data/AndroR2/data/129/state/state_8-0310-103451.xml")
    # open("../Data/MyData/data/7_7LPdWcaW-GrowTracker-Android-89/state/state_11-0310-152445.xml")
    open("../Data/MyData/data/9_ankidroid-Anki-Android-3370/state/state_5-0310-193249.xml")
    open("../Data/ReCDriod/data/2.markor_s/state/state_6-0310-200753.png")
    screen_info = {}
    screen_info.setdefault("activity", "fuck")
    screen_info.setdefault("xml_path",
                           "../Data/MyData/data/9_ankidroid-Anki-Android-3370/state/state_3-0313-220619.xml")
    screen_info.setdefault("img_path", "../Data/ReCDriod/data/2.markor_s/state/state_5-0310-200749.png")
    a1 = State(1, screen_info)
    a1.get_state_hash()
    # screen_info2 = {}
    # screen_info2.setdefault("activity", "fuck")
    # screen_info2.setdefault("xml_path", "../Data/ReCDriod/data/2.markor_s/state/state_6-0310-200753.xml")
    # screen_info2.setdefault("img_path", "../Data/ReCDriod/data/2.markor_s/state/state_6-0310-200753.png")
    # a2 = State(1, screen_info2)
    # print(a1.get_state_hash(), a1.get_view_count())
    # print(a2.get_state_hash(), a2.get_view_count())
