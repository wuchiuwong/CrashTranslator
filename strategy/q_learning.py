import random
from env.state_info import StateInfo
from env.emulator import EmuRunner
import time
import logging
from strategy.action_recoder import ActionRecoder
import os

class QLearningExplore:
    def __init__(self, state_info: StateInfo, env: EmuRunner, app_info, lr=0.1, gamma=0.9):
        self.state_info = state_info
        self.env = env
        self.visit_actions = dict()
        self.action_q = dict()
        self.app_info = app_info
        self.scorer = app_info["scorer"]
        self.lr = lr
        self.gamma = gamma
        self.bored_counter = 0
        self.recoder = ActionRecoder(state_info, app_info["action_output"])

    def explore(self):
        # self.env.reset(reset_all=True)
        for step in range(1, 2001):
            logging.info("##### Step " + str(step) + " #####")
            before_state, _ = self.env.get_cur_state()
            logging.info("Before state: " + str(before_state))
            if before_state > 9000:
                logging.info("try relaunch")
                self.env.relaunch_app()
                before_state, _ = self.env.get_cur_state()
            if before_state not in self.action_q.keys():
                self.init_action_q(before_state)
            choose_idx, choose_action = self.choose_action(before_state)

            logging.info("Choose action: " + str(choose_idx))
            if choose_idx == -1:
                self.punish_action_to_stuck()
                self.recoder.add_restart_to_history()
                self.env.reset(force_restart=True)
                time.sleep(0.5)
                continue
            after_state, reward, done, info = self.env.step(choose_idx)
            self.recoder.update(before_state, after_state, choose_idx, reward)
            logging.info("Update aciton q: " + str(before_state) + "," + str(choose_idx))
            update_res = self.update_action_q(before_state, choose_idx, after_state, reward)
            if done == 2:
                return step
            elif done == 1:
                self.recoder.add_restart_to_history()
                self.env.reset(force_reset=True)
                os.system("adb logcat -c")
                f = open("../Data/Temp/log/log_out.txt", "w")
                time.sleep(0.5)
            if after_state > 9000:
                # print("do reset")
                # self.env.reset(force_restart=True)
                self.recoder.add_restart_to_history()
                self.env.reset()
                # print("reset done")
            # time.sleep(0.2)
            self.state_info.save_pkl()
        return -1

    def update_action_q(self, before_state: int, before_action_idx: int, after_state: int, reward):
        if before_state not in self.action_q.keys() or before_action_idx not in self.action_q[before_state].keys():
            return False
        if after_state not in self.action_q.keys() and after_state < 9000:
            self.init_action_q(after_state)
        if after_state < 9000:
            _, _, max_q_of_after = self.get_max_q_action(after_state)
        else:
            max_q_of_after = -9999
        before_score = self.action_q[before_state][before_action_idx]
        self.action_q[before_state][before_action_idx] = self.action_q[before_state][before_action_idx] + self.lr * (
                reward + self.gamma * max_q_of_after - self.action_q[before_state][before_action_idx])
        after_score = self.action_q[before_state][before_action_idx]
        logging.info("before_score: " + str(before_score) + ", after score: " + str(after_score))
        # q_value = self.ret_q_value(old_obs, a) + self.alfa * (reward + self.gamma * self.ret_max_q_value(obs) -
        #                                                       self.ret_q_value(old_obs, a))
        return True

    def init_action_q(self, state_id: int):
        available_actions = self.state_info.get_available_actions(state_id)
        cur_action_q = {}
        for action_id in available_actions:
            query_info = {}
            query_info.setdefault("state_id", state_id)
            query_info.setdefault("action_id", action_id)
            action = self.state_info.get_state_action(state_id, action_id)
            query_info.setdefault("action", action)
            action_refer_name = action["refer_name"]
            # action_class = action["class"]
            init_score = self.scorer.get_view_score(query_info)
            logging.info("init score [" + str(state_id) + ":" + str(action_id) + "] :" + action_refer_name + " " + str(
                init_score))
            cur_action_q.setdefault(action_id, init_score)
        self.action_q.setdefault(state_id, cur_action_q)
        self.visit_actions.setdefault(state_id, set())

    def choose_action(self, state_id: int):
        random_flag = random.random()
        action_prob = self.recoder.get_action_prob()
        if action_prob < 0:
            return -1, None
        elif random_flag < action_prob:
            # choose unvisited action
            unvisited_actions = self.recoder.get_unvisited_actions(state_id)
            if len(unvisited_actions) > 0:
                choose_idx = random.choice(list(unvisited_actions))
                choose_action = self.state_info.get_state_action(state_id, choose_idx)
            else:
                # all action has visited, still choose max q action
                choose_idx, choose_action, _ = self.get_max_q_action(state_id)
        else:
            # choose max q action
            choose_idx, choose_action, _ = self.get_max_q_action(state_id)
        self.visit_actions[state_id].add(choose_idx)
        return choose_idx, choose_action

    def get_max_q_action(self, state_id: int):
        sort_action_q = sorted(self.action_q[state_id].items(), key=lambda d: d[1], reverse=True)
        # return sort_action_q[0][0], sort_action_q[0][1]
        for i in range(len(sort_action_q)):
            choose_idx = sort_action_q[i][0]
            choose_action = self.state_info.get_state_action(state_id, choose_idx)
            if choose_action["type"] == "system_back":
                return choose_idx, choose_action, sort_action_q[0][1]
            else:
                choose_flag1 = len(sort_action_q) < 5
                choose_flag2 = len(sort_action_q) >= 5 and not self.recoder.check_action_in_recent(state_id, choose_idx)
                if choose_flag1 or choose_flag2:
                    return choose_idx, choose_action, sort_action_q[0][1]
        choose_idx = sort_action_q[0][0]
        return choose_idx, self.state_info.get_state_action(state_id, choose_idx), sort_action_q[0][1]

    def punish_action_to_stuck(self):
        logging.info("begin punish action to stuck" + str(self.recoder.stuck_states))
        # state_history = self.recoder.recent_state
        # state_stat = {s: state_history.count(s) for s in set(state_history)}
        # sort_state_stat = sorted(state_stat.items(), key=lambda s: -s[1])
        # for t in sort_state_stat[:1]:
        #     state_id = t[0]
        #     state_times = t[1]
        #     logging.info("state visit: " + str(state_id) + ":" + str(state_times))
        #     if state_id >= 2 and state_times >= 7:
        #         logging.info("stuck state: " + str(state_id))
        #         action_to_state = self.state_info.get_action_to_state(state_id)
        #         for src_state, actions in action_to_state.items():
        #             for a_id in actions:
        #                 logging.info("punish to state " + str(state_id) + ": " + str(src_state) + "/" + str(a_id))
        #                 update_res = self.update_action_q(src_state, a_id, state_id, -4)
        for stuck_state in self.recoder.stuck_states:
            logging.info("stuck state: " + str(stuck_state))
            action_to_state = self.state_info.get_action_to_state(stuck_state)
            for src_state, actions in action_to_state.items():
                for a_id in actions:
                    logging.info("punish to state " + str(stuck_state) + ": " + str(src_state) + "/" + str(a_id))
                    update_res = self.update_action_q(src_state, a_id, stuck_state, -4)
        self.recoder.stuck_states.clear()



if __name__ == '__main__':
    # print(1)
    print(sorted([3,5,1,4,2], key=lambda x:-x))