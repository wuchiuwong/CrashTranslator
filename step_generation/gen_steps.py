import re
import shutil
import cv2
import pickle
import os
import numpy as np


class StepGenerator:
    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        self.action_history = open(data_dir + "/action_history.txt", "r").readlines()
        self.info_dict = pickle.load(open(data_dir + "/state_info.pkl", "rb"))
        self.output_dir = data_dir + "/step"
        if not os.path.exists(self.output_dir):
            os.mkdir(self.output_dir)
        else:
            shutil.rmtree(self.output_dir)
            if not os.path.exists(self.output_dir):
                os.mkdir(self.output_dir)
        self.full_dir = self.output_dir + "/full"
        if not os.path.exists(self.full_dir):
            os.mkdir(self.full_dir)
        self.simplify_dir = self.output_dir + "/simplify"
        if not os.path.exists(self.simplify_dir):
            os.mkdir(self.simplify_dir)
        self.states = self.info_dict["states"]
        self.stg = self.info_dict["stg"]
        self.stg_parents = self.info_dict["stg_parents"]
        self.action_to_state = self.info_dict["action_to_state"]
        self.actions_belong_states = self.info_dict["actions_belong_states"]

    def get_action_block(self):
        symbol_block = []
        cur_symbol_block = []
        for line_idx, line in enumerate(self.action_history):
            if "###" in line:
                cur_symbol_block.append(line.strip())
            if "Restart" in line or len(line.strip()) == 0 or line_idx == (len(self.action_history) - 1):
                if len(cur_symbol_block) != 0:
                    symbol_block.append(cur_symbol_block.copy())
                cur_symbol_block.clear()
        use_symbol_block = symbol_block[-1]
        if len(use_symbol_block) <= 1 and len(symbol_block) > 1:
            use_symbol_block = symbol_block[-2]
        return use_symbol_block

    def output_all_action(self, max_step=15):
        # old: output all history
        # step_idx = 1
        # action_block = self.get_action_block()
        # action_freq = {}
        # for action_symbol in action_block:
        #     state_id = int(action_symbol.split("###")[0])
        #     action_id = int(action_symbol.split("###")[1])
        #     if action_symbol not in action_freq.keys():
        #         action_freq.setdefault(action_symbol, 0)
        #     if action_freq[action_symbol] <= 2:
        #         action_freq[action_symbol] += 1
        #         self.output_step(step_idx, state_id, action_id, self.full_dir)
        #         step_idx += 1
        # new: output latest 15
        step_idx = 0
        action_block = self.get_action_block()
        if len(action_block) >= max_step:
            action_block = action_block[-max_step:]
        full_actions = []
        first_action_symbol = action_block[0]
        first_state = int(first_action_symbol.split("###")[0])
        if first_state != 0:
            # self.get_path_recursion(0, first_state, path_arr)
            path_arr = self.get_path(0, first_state)
            for pos in range(len(path_arr) - 1):
                before_state = path_arr[pos]
                after_state = path_arr[pos + 1]
                candi_actions = list(self.action_to_state[after_state][before_state])
                use_action = str(before_state) + "###" + str(candi_actions[0])
                for action_id in candi_actions:
                    cur_symbol = str(before_state) + "###" + str(action_id)
                    if cur_symbol in action_block:
                        use_action = cur_symbol
                        break
                full_actions.append(use_action)
        full_actions.extend(action_block)
        for action_symbol in full_actions:
            step_idx += 1
            state_id = int(action_symbol.strip().split("###")[0])
            action_id = int(action_symbol.strip().split("###")[1])
            self.output_step(step_idx, state_id, action_id, self.full_dir)

    def gen_reproducing_steps(self):
        self.output_all_action()
        self.output_simplify_action()

    def output_simplify_action(self):
        step_idx = 0
        action_block = self.get_action_block()
        last_action = action_block[-1]
        last_state = int(last_action.split("###")[0])
        # path_arr = []
        # self.get_path_recursion(0, last_state, path_arr)
        simplify_actions = []
        if last_state != 0:
            path_arr = self.get_path(0, last_state)
            for pos in range(len(path_arr) - 1):
                before_state = path_arr[pos]
                after_state = path_arr[pos + 1]
                candi_actions = list(self.action_to_state[after_state][before_state])
                use_action = str(before_state) + "###" + str(candi_actions[0])
                for action_id in candi_actions:
                    cur_symbol = str(before_state) + "###" + str(action_id)
                    if cur_symbol in action_block:
                        use_action = cur_symbol
                        break
                simplify_actions.append(use_action)
        simplify_actions.append(last_action)
        for action_symbol in simplify_actions:
            step_idx += 1
            state_id = int(action_symbol.strip().split("###")[0])
            action_id = int(action_symbol.strip().split("###")[1])
            self.output_step(step_idx, state_id, action_id, self.simplify_dir)

    def output_step(self, step_idx: int, state_id: int, action_id: int, output_dir: str):
        if state_id not in self.states.keys():
            print("fail to find state", state_id, "in the state dict:", self.states.keys())
            return
        cur_state = self.states[state_id]
        cur_img_path = cur_state["img_path"]
        if not os.path.exists(cur_img_path):
            print("fail to find img for", state_id, ":", cur_img_path)
            return
        cur_all_action = cur_state["actions"]
        if action_id not in cur_all_action.keys():
            print("fail to find action", state_id, "in state", state_id, ":", cur_all_action.keys())
            return
        cur_action = cur_all_action[action_id]
        cur_save_path = self.get_save_path(step_idx, cur_action, output_dir)
        self.show_step_img(cur_img_path, cur_action["bounds"], cur_save_path)

    def get_save_path(self, step_idx: int, action: dict, output_dir: str):
        ori_action_name = action['refer_name']
        action_name = re.sub("[^a-zA-Z0-9 ]", "", ori_action_name)
        # todo: click/input/fill info
        if action["type"] == "system_back":
            action_str = "click back"
        elif action["type"] == "system_rotate":
            action_str = "rotate"
        elif action["type"] == "click":
            action_str = "click " + action_name
        elif action["type"] == "long_click":
            action_str = "long click " + action_name
        elif action["type"] == "input":
            action_str = "input " + action_name
        elif action["type"] == "fill_info":
            action_str = "fill all input box on the screen and click " + action_name
        else:
            action_str = action_name
        step_str = str(step_idx) + "_" + action_str + ".png"
        return output_dir + "/" + step_str

    def show_step_img(self, img_path: str, action_bounds: list, save_path: str):
        try:
            state_img = cv2.imread(img_path)
            state_img = cv2.rectangle(state_img, (action_bounds[0][0], action_bounds[0][1]),
                                      (action_bounds[1][0], action_bounds[1][1]), (0, 0, 255), 5)
            cv2.imwrite(save_path, state_img)
        except Exception as e:
            print(e)
            empty_img = np.zeros((1920, 1080, 3), np.uint8)
            # empty_img.fill(0)
            cv2.imshow('img', empty_img)
            state_img = cv2.rectangle(empty_img, (action_bounds[0][0], action_bounds[0][1]),
                                      (action_bounds[1][0], action_bounds[1][1]), (0, 0, 255), 5)
            cv2.imwrite(save_path, state_img)

    def get_path(self, src_state, dst_state):
        path_arr = []
        if src_state not in self.states.keys() or dst_state not in self.states.keys() or self.stg[src_state][
            dst_state] > 100:
            return []
        self.get_path_recursion(src_state, dst_state, path_arr)
        return path_arr

    def get_path_recursion(self, src_idx, dst_idx, path_arr):
        if src_idx != dst_idx:
            self.get_path_recursion(src_idx, self.stg_parents[src_idx][dst_idx], path_arr)
        path_arr.append(dst_idx)


if __name__ == '__main__':
    # info_dict = pickle.load(open("../Data/ReCDriod/data/19.Pix-Art-share_s/state_info.pkl", "rb"))
    # print(info_dict.keys())
    # print(info_dict['action_to_state'])
    # print(info_dict.keys())
    # for state_id, state_detail in info_dict["states"].items():
    #     print(state_id)
    #     for k, v in state_detail.items():
    #         print(k, v)
    #     break
    sg = StepGenerator("../Data/ReCDriod/data/24.obdreader_s")
    # sg = StepGenerator("../Data/MyData/data/4_ankidroid-Anki-Android-10584")
    sg.gen_reproducing_steps()
    # for i in range(len(sg.stg)):
    #     print(i, sg.stg[i])
    #     print(i, sg.stg_parents[i])
    # for i in range(9):
    #     path_arr = []
    #     sg.get_path_recursion(0, i, path_arr)
    #     print(i, path_arr)
    # sg.gen_reproducing_steps()
    # sg.output_simplify_action()
    # info_dict = pickle.load(open("../Data/AndroR2/data/129/state_info.pkl", "rb"))
    # info_dict["stg"][0][8] = 8
    # # print(info_dict["stg"])
    # info_dict["stg_parents"][0][8] = 7
    # pickle.dump(info_dict, open("../Data/AndroR2/data/129/state_info.pkl", "wb"))
