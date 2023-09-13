from env.state import State
from env.util import get_state_sim, check_img_same
import os
import shutil
import time
import logging
import pickle

class StateInfo():
    def __init__(self, app_info: dict):
        self.app_info = app_info
        self.data_dir = app_info["data_dir"]
        self.pkl_path = app_info["data_dir"] + "/state_info.pkl"
        self.app_pkg = app_info["app_pkg"]
        self.scorer = app_info["scorer"]
        self.need_rotate = app_info["need_rotate"]
        # states and actions
        self.states = dict()
        self.actions_belong_states = dict()
        self.visit_activities = set()
        # stg
        self.stg = []
        self.stg_parents = []
        self.dis_dict = {}
        self.state_transitions = dict()
        self.action_transitions = dict()
        self.action_to_state = dict()
        self.state_count = -1
        self.inf = 114514

    def add_state(self, screen_info: dict):
        assign_state_id = len(self.states.keys())
        state_dir = self.data_dir + "/state"
        if not os.path.exists(state_dir):
            os.mkdir(state_dir)
        time_str = time.strftime("%m%d-%H%M%S", time.localtime())
        state_path = state_dir + "/state_" + str(assign_state_id) + "-" + time_str
        img_path = state_path + ".png"
        shutil.copy(screen_info["img_path"], img_path)
        xml_path = state_path + ".xml"
        shutil.copy(screen_info["xml_path"], xml_path)
        screen_info["img_path"] = img_path
        screen_info["xml_path"] = xml_path
        new_state = State(assign_state_id, screen_info, new_state=True, need_rotate=self.need_rotate)
        self.states.setdefault(assign_state_id, new_state)
        self.actions_belong_states.setdefault(assign_state_id, new_state.actions)
        self.visit_activities.add(screen_info["activity"])
        logging.info("save new state to: " + state_path)
        # todo: update stg
        self.save_pkl()
        return assign_state_id

    def get_state_idx(self, screen_info: dict, sim_thres=0.7):
        # state_type:
        #   9999: not the activity in app
        #   0: state already found
        #   1: state new find (activity already found)
        #   2: state new find (activity new find)
        #   todo: state type that related to crash
        temp_state = State(-1, screen_info)
        temp_state_hash = temp_state.get_state_hash()
        temp_img_path = screen_info["img_path"]
        if self.app_pkg != screen_info["package"]:
            logging.info("reach a state out of app")
            return 9999, -1
        if "FileBrowserActivity" in screen_info["activity"] or "AnyMemoDownloaderActivity" in screen_info["activity"]:
            logging.info("reach a state out of app")
            return 9999, -1
        max_sim = -1
        max_state = -1
        for state_id, state_obj in self.states.items():
            if temp_state.get_view_count() > 10:
                if temp_state_hash == state_obj.get_state_hash():
                    return state_id, 0
            else:
                state_img_path = state_obj.img_path
                is_img_same = check_img_same(temp_img_path, state_img_path)
                if is_img_same and temp_state_hash == state_obj.get_state_hash():
                    return state_id, 0
            cur_sim = get_state_sim(temp_state, state_obj)
            if cur_sim > max_sim:
                max_sim = cur_sim
                max_state = state_id
        if max_sim > sim_thres:
            return max_state, 0
        # Find a new state!
        if screen_info["activity"] in self.visit_activities:
            new_state_type = 1
        else:
            new_state_type = 2
        new_state_id = self.add_state(screen_info)
        return new_state_id, new_state_type

    def get_state_action(self, state_id: int, action_id: int):
        if state_id not in self.actions_belong_states.keys():
            return
        if action_id not in self.actions_belong_states[state_id].keys():
            return
        return self.actions_belong_states[state_id][action_id]

    def get_available_actions(self, state_id: int):
        if state_id not in self.actions_belong_states.keys():
            return []
        return list(self.actions_belong_states[state_id].keys())

    def get_action_transition(self, src_state: int, action_id: int):
        if src_state not in self.action_transitions.keys():
            return None
        if action_id not in self.action_transitions[src_state].keys():
            return None
        return self.action_transitions[src_state][action_id]

    def update_transition(self, src_state: int, action_id: int, dst_state: int, cover=False):
        if src_state not in self.state_transitions.keys():
            self.state_transitions.setdefault(src_state, {})
            self.action_transitions.setdefault(src_state, {})
        if dst_state not in self.state_transitions[src_state].keys():
            self.state_transitions[src_state].setdefault(dst_state, set())
        if dst_state not in self.action_to_state.keys():
            self.action_to_state.setdefault(dst_state, dict())
        if src_state not in self.action_to_state[dst_state].keys():
            self.action_to_state[dst_state].setdefault(src_state, set())
        self.state_transitions[src_state][dst_state].add(action_id)
        self.action_to_state[dst_state][src_state].add(action_id)
        tgt_action = self.get_state_action(src_state, action_id)
        if action_id not in self.action_transitions[src_state].keys():
            self.action_transitions[src_state].setdefault(action_id, dst_state)
            logging.info("update transition: " + tgt_action["refer_name"] + " " + str(src_state) + "->" + str(dst_state))
        else:
            old_state = self.action_transitions[src_state][action_id]
            if old_state != dst_state:
                logging.info("### state conflict, in state " + str(src_state))
                logging.info("### tgt_action: " + tgt_action["type"] + " " + tgt_action["refer_name"] + " (" + \
                             tgt_action["class"] + ", " + str(tgt_action["bounds"]) + ")")
                logging.info("### old: " + str(old_state) + ", new: " + str(dst_state))
                if cover:
                    self.action_transitions[src_state][action_id] = dst_state
                    logging.info("### cover: " + str(old_state) + "->" + str(dst_state))
        self.update_stg()

    def update_stg(self):
        self.state_count = len(self.states.keys())
        self.stg = [[self.inf for _ in range(self.state_count)] for _ in range(self.state_count)]
        self.stg_parents = [[i for _ in range(self.state_count)] for i in range(self.state_count)]
        for i in range(self.state_count):
            self.stg[i][i] = 0
        for src_state in self.state_transitions.keys():
            for dst_state in self.state_transitions[src_state].keys():
                if dst_state in self.states.keys():
                    self.stg[src_state][dst_state] = 1
        for k in range(self.state_count):
            for i in range(self.state_count):
                for j in range(self.state_count):
                    if self.stg[i][k] + self.stg[k][j] < self.stg[i][j]:
                        self.stg[i][j] = self.stg[i][k] + self.stg[k][j]
                        self.stg_parents[i][j] = self.stg_parents[k][j]
        self.dis_dict = {}
        for i in range(self.state_count):
            self.dis_dict.setdefault(i, {})
            for j in range(self.state_count):
                self.dis_dict[i].setdefault(j, self.stg[i][j])

    def get_action_to_state(self, dst_state):
        if dst_state not in self.action_to_state.keys():
            return {}
        return self.action_to_state[dst_state]

    def save_pkl(self):
        temp_state_info = dict()
        temp_state = dict()
        for state_key, t_state in self.states.items():
            cur_state = {}
            cur_state.setdefault("activity", t_state.activity)
            cur_state.setdefault("xml_path", t_state.xml_path)
            cur_state.setdefault("img_path", t_state.img_path)
            cur_state.setdefault("actions", t_state.actions)
            cur_state.setdefault("name2action", t_state.name2action)
            temp_state.setdefault(state_key, cur_state)
        temp_state_info.setdefault("states", temp_state)
        temp_state_info.setdefault("actions_belong_states", self.actions_belong_states.copy())
        temp_state_info.setdefault("stg", self.stg.copy())
        temp_state_info.setdefault("stg_parents", self.stg_parents.copy())
        temp_state_info.setdefault("state_transitions", self.state_transitions.copy())
        temp_state_info.setdefault("action_transitions", self.action_transitions.copy())
        temp_state_info.setdefault("action_to_state", self.action_to_state.copy())
        pkl_file = open(self.pkl_path, "wb")
        pickle.dump(temp_state_info, pkl_file)


if __name__ == '__main__':
    app_info = {"data_dir": "../Data/Test", "app_pkg": "test"}
    state_info = StateInfo(app_info)
    screen_info = {"activity": "aaa", "img_path": "../Data/Temp/cur_screen.png",
                   "xml_path": "../Data/Temp/cur_screen.xml"}
    print(state_info.get_state_idx(screen_info))
    print(state_info.get_available_actions(0))
