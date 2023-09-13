import os
import openai
import json
import pandas as pd
import time
import re
from env.state_info import StateInfo, State
import logging
from env.util import check_crash, check_crash_strict
from trigger_check.checker import APITriggerChecker

from nltk.stem import SnowballStemmer

stemmer = SnowballStemmer("english")

# os.environ["http_proxy"] = "http://127.0.0.1:7890"
# os.environ["https_proxy"] = "http://127.0.0.1:7890"

# set your api key
openai.api_key = "sk-************************************************"
# set your fine-tune model
model_name = "curie:ft-personal-2023-MM-DD-hh-mm-ss"

class GPT3Scorer:
    def __init__(self, dst_acti: str, checker: APITriggerChecker, all_pages: list, trace_info: dict, use_page=1,
                 use_widget=1):
        self.state_action_score = {}
        self.state_info = None
        self.dst_acti = dst_acti
        self.checker = checker
        self.all_pages = all_pages
        self.trace_info = trace_info
        self.trace = trace_info["trace"]
        # self.need_rotate = trace_info["need_rotate"]
        self.use_page = use_page
        if use_page != 1:
            print("#" * 10, "Note", "#" * 10)
            print("use_page: ", self.use_page)
            print("#" * 26)
        self.use_widget = use_widget
        if use_widget != 1:
            print("#" * 10, "Note", "#" * 10)
            print("use_widget: ", self.use_widget)
            print("#" * 26)

    def set_state_info(self, state_info: StateInfo):
        self.state_info = state_info

    def init_state(self, state_id: int):
        if state_id < 0 and state_id > 100:
            logging.info("State " + str(state_id) + " maybe invalid, shoult not do init in GPT3!")
        if state_id in self.state_action_score.keys():
            logging.info("State " + str(state_id) + " has already init in GPT3!")
            return
        state = self.state_info.states[state_id]
        cur_action_score = self.do_score(state, self.dst_acti, self.use_page)
        self.state_action_score.setdefault(state_id, cur_action_score)
        logging.info("State " + str(state_id) + " success init in GPT3!")

    def get_view_score(self, query_info: dict):
        state_id = query_info["state_id"]
        action_id = query_info["action_id"]
        if state_id not in self.state_action_score.keys():
            logging.info("State " + str(state_id) + " has not init in GPT3!")
            if state_id >= 0 and state_id < 100:
                self.init_state(state_id)
            else:
                return -1
        if action_id not in self.state_action_score[state_id].keys():
            logging.info("GPT3 Error: action not find!: " + str(state_id) + "/" + str(action_id))
            return -1
        return self.state_action_score[state_id][action_id]

    def do_score_old(self, state: State, dst_acti):
        # todo: this is old prompt, delete this method
        src_acti = state.activity.split(".")[-1]
        refer_names, view_name_map = state.get_refer_names()
        prompt = self.gen_sort_prompt(refer_names, src_acti, dst_acti)
        gpt3_result = self.get_result(prompt)
        res_json = json.loads(gpt3_result)
        predict_str = res_json["choices"][0]["text"].strip()
        predict_str = predict_str.replace("END", "").strip()
        logging.info("GPT3 predict: " + predict_str)
        action_score = {}
        for _, action_ids in view_name_map.items():
            for action_id in action_ids:
                action_score.setdefault(action_id, 0)
        predicts = predict_str.split("\n")
        for rand_idx, predict in enumerate(predicts):
            if predict not in view_name_map.keys():
                logging.info("GPT3 Error: predict not find!: " + predict)
                refine_flag = False
                for t_view_name in view_name_map.keys():
                    if predict in t_view_name:
                        refine_flag = True
                        predict = t_view_name
                if not refine_flag:
                    continue
            action_ids = view_name_map[predict]
            init_score = 1 / (rand_idx + 2)
            logging.info("GPT3 rank " + str(rand_idx) + " : " + predict + ", id:" + str(action_ids))
            for action_id in action_ids:
                action_score[action_id] = init_score
        return action_score

    def do_score(self, state: State, dst_acti, use_page=1):
        src_acti = state.activity.split(".")[-1]
        action_groups, name2action = state.get_state_detail()
        # default action 0 is back, score is -0.1, will be explored at last
        action_score = {0: -0.1}
        if len(state.actions) >= 2 and state.actions[1]["type"] == "system_rotate":
            action_score.setdefault(1, 3)
        # if state.actions[1]
        # todo: init by heuristically
        for _, action_ids in name2action.items():
            for action_id in action_ids:
                heuristic_score = self.get_view_score_heuristically(state, action_id, self.use_widget)
                action_score.setdefault(action_id, heuristic_score)
        next_page_prompt = self.gen_next_page_prompt(src_acti, dst_acti)
        if use_page > 0:
            logging.info("GPT3 page prompt: " + next_page_prompt.split("\n")[0])
            gpt3_page_result = self.get_result(next_page_prompt)
            page_res_json = json.loads(gpt3_page_result)
            predict_page = page_res_json["choices"][0]["text"].replace(" END", "").strip()
            logging.info("GPT3 predict page: " + predict_page)
        else:
            time.sleep(1)
            predict_page = ""
        exclude_widgets = set()
        ask_times = min(5, len(name2action.keys()))
        for rank_idx in range(ask_times):
            if use_page > 0:
                next_widget_prompt = self.gen_next_widget_prompt(src_acti, dst_acti, predict_page, action_groups,
                                                                 exclude_widgets)
                logging.info("GPT3 widget prompt: " + next_widget_prompt.split("\n")[0])
                gpt3_widget_result = self.get_result(next_widget_prompt)
                widget_res_json = json.loads(gpt3_widget_result)
                predict_widget = widget_res_json["choices"][0]["text"].replace(" END", "").strip()
                logging.info("GPT3 predict widget: " + predict_widget)
                if predict_widget not in name2action.keys():
                    logging.info("GPT3 Error: predict not find!: " + predict_widget)
                    continue
                exclude_widgets.add(predict_widget)
                action_ids = name2action[predict_widget]
                # init_score = 1 / (rank_idx + 2)
                init_score = (1 / (rank_idx + 3)) * use_page
                logging.info("GPT3 rank " + str(rank_idx + 1) + " : " + predict_widget + ", id:" + str(action_ids))
                for action_id in action_ids:
                    action_score[action_id] += init_score
            else:
                time.sleep(1)
        # time.sleep(4)
        return action_score

    def get_result(self, prompt):
        # sort prompt: curie:ft-personal-2022-12-22-13-33-35
        # 2stage prompt: curie:ft-personal-2023-01-16-03-51-16
        res_str = openai.Completion.create(
            model="curie:ft-personal-2023-01-16-03-51-16",
            stop=[" END"],
            temperature=0,
            prompt=prompt)
        return str(res_str)

    def gen_next_page_prompt(self, src_acti, dst_acti):
        all_page_prompt = "There are " + str(len(self.all_pages)) + " pages in the app, named: " + ", ".join(
            self.all_pages) + ". "
        trans_prompt = "I want to go from the " + self.get_activity_name(src_acti) + " page to the " + \
                       self.get_activity_name(dst_acti) + " page. "
        next_prompt = "What is the next page? \n\n###\n\n"
        return all_page_prompt + trans_prompt + next_prompt

    def gen_next_widget_prompt(self, src_acti, dst_acti, next_page, action_groups, exclude_widgets):
        all_page_prompt = "There are " + str(len(self.all_pages)) + " pages in the app, named: " + \
                          ", ".join(self.all_pages) + ". "
        trans_prompt = "I want to go from the " + self.get_activity_name(src_acti) + " page to the " + \
                       self.get_activity_name(dst_acti) + " page. "
        next_prompt = "The next page may be the " + next_page + " page. "
        widget_on_screen = []
        normal_widgets = ""
        for group_info in action_groups:
            container_type = group_info["container_type"]
            action_names = group_info["action_names"]
            remain_names = action_names - exclude_widgets
            if container_type != "normal":
                widget_str = ", ".join(list(remain_names)) + " in a " + container_type + "; "
                widget_on_screen.append(widget_str)
            else:
                normal_widgets = ", ".join(list(remain_names)) + " on the screen. "
        widget_prompt = "Here are widgets I can click: " + "".join(widget_on_screen) + normal_widgets
        do_prompt = "What should I click? \n\n###\n\n"
        prompt = all_page_prompt + trans_prompt + next_prompt + widget_prompt + do_prompt
        return prompt

    def gen_sort_prompt(self, refer_names, src_acti, dst_acti):
        move_prompt = "From the " + self.get_activity_name(src_acti) + " page to the " + self.get_activity_name(
            dst_acti) + " page, "
        button_prompt = "I can click\n" + "\n".join(refer_names) + "\n"
        action_prompt = "Sort them \n\n###\n\n"
        prompt = move_prompt + button_prompt + action_prompt
        logging.info("GPT3 prompt: " + prompt.replace("\n", "// "))
        return prompt

    def get_activity_name(self, activity_name):
        activity_name = re.sub(r'([a-z])([A-Z])', r'\1 \2', activity_name).lower()
        activity_name = re.sub(r"[^a-z]", " ", activity_name)
        activity_name = re.sub(r"\s+", " ", activity_name).strip()
        activity_name = activity_name.replace("activity", "").replace("fragment", "").strip()
        return activity_name

    def get_state_score_heuristically(self, full_activity: str, state_type: int, action: dict, is_state_same: bool):
        # if full_activity in self.trace_eles["class"]:
        #     return 1000
        if action["type"] == "system_rotate":
            # rotate would be tried at first, but only one time
            return -1000
        trigger_res = self.checker.check_trigger_res()
        base_score = 0
        if trigger_res == 5:
            base_score = 20
        elif trigger_res == 4:
            base_score = 5
        elif trigger_res == 3:
            base_score = 5
        elif trigger_res == 2:
            base_score = 1
        # if check_crash():
        #     return 1000
        is_crash = check_crash_strict(self.trace)
        if is_crash == 2:
            return 1000
        if is_crash == 1:
            return -1000
        if is_state_same:
            return base_score - 2
        if action["type"] == "system_back" and state_type == 0:
            return base_score
        # todo: prefix activity of crash return 1
        if state_type == -1:
            return base_score - 100
        elif state_type == 0:
            return base_score - 2
        elif state_type == 1:
            return base_score + 10
        elif state_type == 2:
            return base_score + 20
        logging.info("Unexcept state type:" + str(state_type))
        return -100

    def get_view_score_heuristically(self, state: State, action_id: int, use_widget=1):
        # interest_words = {"new", "create", "add", "agree", "preference", "option", "next", "start", "study", "ok",
        #                   "setting", "attach", "enter", "show", "open", "more", "stats"}
        # interest_words = {"new", "create", "add", "agree", "preference", "options", "next", "start", "quiz", "ok",
        #                   "attach", "enter", "show", "more", "photo", "import"}
        interest_words = {"new", "create", "add", "agree", "options", "next", "send", "ok", "enter", "show",
                          "more", "photo", "study", "skip"}
        # not_interest_words = ["navigate up", "settings", "download", "preferences", "filter", "preview", "language", "icons"]
        not_interest_words = ["navigate up", "download", "preferences", "filter", "preview", "icons",
                              "open",  "genres", "settings", "message icons", "open", "download"]
        # not_interest_words = ["navigate up", "download", "preferences", "filter", "genres"]
        # not_interest_words = ["navigate up", "download", "preferences"]
        view_score = 0
        action = state.actions[action_id]
        refer_name = action["refer_name"]
        action_class = action["class"]
        action_type = action["type"]
        refer_name_tokens = self.split_to_tokens(refer_name)
        refer_name_tokens = set(refer_name_tokens)
        dst_tokens = set(self.get_activity_name(self.dst_acti).split())

        stem_trace_tokens = set()
        for token in self.trace_info["trace_tokens"]:
            stem_trace_tokens.add(stemmer.stem(token))
        stem_dst_tokens = set()
        for token in self.get_activity_name(self.dst_acti).split():
            stem_dst_tokens.add(stemmer.stem(token))
        stem_refer_name_tokens = set()
        for token in refer_name_tokens:
            stem_refer_name_tokens.add(stemmer.stem(token))

        if refer_name == "system back":
            return -0.1
        if refer_name == "system rotate":
            # rotate would be tried at first, but only one time
            return 3
        # if action_class == "EditText":
        #     return 0
        if action_type == "fill_info":
            view_score += 0.11
        if action_class == "EditText" and "search" in refer_name:
            view_score += 0.3
        # if action_class == "EditText":
        #     view_score += 0.3
        # not stem
        # inter_dst_len = len(refer_name_tokens.intersection(dst_tokens))
        # inter_token_len = len(refer_name_tokens.intersection(self.trace_info["trace_tokens"]))
        # stem
        inter_dst_len = len(stem_refer_name_tokens.intersection(stem_dst_tokens))
        inter_token_len = len(stem_refer_name_tokens.intersection(stem_trace_tokens))

        in_token_flag = "".join(self.split_to_tokens(refer_name)) in self.trace_info["trace_tokens"]
        widget_type_in_token = action_class.lower() in self.trace_info["trace_tokens"]
        if inter_dst_len > 0 and self.use_page > 0:
            # view_score += 0.35 * inter_dst_len * use_widget
            view_score += 0.35 * inter_dst_len * self.use_page
        elif refer_name in self.trace_info["trace_tokens"] and use_widget > 0:
            view_score += 0.25 * use_widget
        elif inter_token_len > 0 and use_widget > 0:
            view_score += 0.15 * inter_token_len * use_widget
        elif in_token_flag or widget_type_in_token and use_widget > 0:
            view_score += 0.15 * use_widget
        elif len(refer_name_tokens.intersection(interest_words)) > 0 and view_score == 0:
            view_score += 0.1
        elif action_type == "long_click" and "root" in refer_name:
            view_score += 0.1
        elif action_type == "long_click" and "hello" in refer_name.lower():
            view_score += 0.01
        elif refer_name in not_interest_words and state.state_id > 1:
            view_score -= 0.4
        return view_score

    def split_to_tokens(self, in_str: str):
        new_str = re.sub(r'([a-z])([A-Z])', r'\1 \2', in_str).lower()
        new_str = re.sub("[^a-z]", " ", new_str).strip()
        new_str = re.sub("\s+", " ", new_str)
        tokens = new_str.split(" ")
        return tokens


if __name__ == '__main__':
    pass
