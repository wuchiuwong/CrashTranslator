import random
from env.state_info import StateInfo
from env.emulator import EmuRunner
import time
import logging


class RandomExplore():
    def __init__(self, state_info: StateInfo, env: EmuRunner):
        self.state_info = state_info
        self.env = env
        self.state_visit_times = dict()
        self.action_q = dict()

    def explore(self):
        # self.env.reset(reset_all=True)
        self.env.reset()
        for step in range(1, 101):
            logging.info("##### Step " + str(step) + " #####")
            before_state, _ = self.env.get_cur_state()
            logging.info("Before state: " + str(before_state))
            self.update_visit_times(before_state)
            if before_state not in self.action_q.keys():
                self.init_action_q(before_state)
            choose_action = self.choose_action(before_state)
            logging.info("Choose action: " + str(choose_action))
            after_state, reward, done, info = self.env.step(choose_action)
            if after_state == before_state or after_state > 9000:
                self.update_action_q(before_state, choose_action, 999)
            else:
                self.update_action_q(before_state, choose_action, 1)
            if done:
                return step + 1
            if after_state > 9000:
                self.env.reset()
            time.sleep(0.5)
        return -1

    # def explore(self):
    #     self.env.reset(reset_all=True)
    #     for step in range(1, 101):
    #         logging.info("##### Step " + str(step) + " #####")
    #         before_state, _ = self.env.get_cur_state()
    #         logging.info("Before state: " + str(before_state))
    #         self.update_visit_times(before_state)
    #         if before_state not in self.action_q.keys():
    #             self.init_action_q(before_state)
    #         choose_idx, choose_action = self.choose_action(before_state)
    #         self.action_queue.add_action(choose_action)
    #         logging.info("Choose action: " + str(choose_idx))
    #         after_state, reward, done, info = self.env.step(choose_idx)
    #         self.update_bored_counter(reward)
    #         logging.info("Update aciton q: " + str(before_state) + "," + str(choose_idx))
    #         update_res = self.update_action_q(before_state, choose_idx, after_state, reward)
    #         if done:
    #             return step + 1
    #         if after_state > 9000:
    #             self.env.reset()
    #         time.sleep(0.5)
    #     return -1

    def update_visit_times(self, state_id: int):
        if state_id not in self.state_visit_times.keys():
            self.state_visit_times.setdefault(state_id, 1)
        else:
            self.state_visit_times[state_id] += 1

    def update_action_q(self, state_id: int, action_id: int, reward):
        if state_id not in self.action_q.keys() or action_id not in self.action_q[state_id].keys():
            return False
        # self.action_q[state_id][action_id] = reward
        self.action_q[state_id][action_id] += reward
        return True

    def init_action_q(self, state_id: int):
        available_actions = self.state_info.get_available_actions(state_id)
        cur_action_q = {a: 0 for a in available_actions}
        self.action_q.setdefault(state_id, cur_action_q)

    def choose_action(self, state_id: int):
        new_action = []
        visited_action = []
        for action_id, action_q in self.action_q[state_id].items():
            if action_q > 0:
                visited_action.append([action_id, action_q])
            else:
                new_action.append(action_id)
        if len(new_action) > 0:
            return random.choice(new_action)
        else:
            visited_action.sort(key=lambda x: x[1])
            visited_action = visited_action[:1]
            return random.choice(visited_action)[0]
