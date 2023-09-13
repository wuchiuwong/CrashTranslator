from env.state_info import StateInfo
import math
import logging

class ActionRecoder:
    def __init__(self, state_info: StateInfo, action_output: str, action_len=5, state_len=20):
        self.state_info = state_info
        self.recent_action = []
        self.action_len = action_len
        self.recent_state = []
        self.state_len = state_len
        self.state_times = dict()
        self.action_times = dict()
        self.bored_counter = 0
        self.stuck_states = []
        self.action_history = []
        self.action_output = action_output

    def update(self, before_state: int, after_state: int, action_id: int, reward):
        # action = self.state_info.get_state_action(before_state, action_id)
        # action_symbol = self.get_action_symbol(action)
        action_symbol = self.get_action_symbol(before_state, action_id)
        self.action_history.append(action_symbol)
        self.recent_action.append(action_symbol)
        if len(self.recent_action) > self.action_len:
            self.recent_action.pop(0)
        self.recent_state.append(after_state)
        if len(self.recent_state) > self.state_len:
            self.recent_state.pop(0)
        if after_state not in self.state_times.keys():
            # find new state, reset bored counter
            self.state_times.setdefault(after_state, 1)
            self.bored_counter = 0
        else:
            self.state_times[after_state] += 1
            if reward < 0:
                self.bored_counter += 1
        if before_state not in self.action_times.keys():
            init_times = {a_key: 0 for a_key in self.state_info.get_available_actions(before_state)}
            self.action_times.setdefault(before_state, init_times)
        self.action_times[before_state][action_id] += 1
        action_file = open(self.action_output, "w")
        action_file.write("\n".join(self.action_history))

    def get_action_symbol(self, state_id, action_id):
        # old: by action name
        # refer_name = action["refer_name"]
        # action_class = action["class"]
        # return refer_name + "#" + action_class
        # new: by state id and action id
        return str(state_id) + "###" + str(action_id)

    def add_restart_to_history(self):
        self.action_history.append("@@@Restart")
        action_file = open(self.action_output, "w")
        action_file.write("\n".join(self.action_history))


    def check_action_in_recent(self, state_id: int, action_id: int):
        action = self.state_info.get_state_action(state_id, action_id)
        if action["refer_name"] == "system back":
            return False
        else:
            # action_symbol = self.get_action_symbol(action)
            action_symbol = self.get_action_symbol(state_id, action_id)
            return action_symbol in self.recent_action

    def check_state_in_recent(self, state_id: int):
        return state_id in self.recent_state

    def get_action_prob(self, fix_rate=False):
        if self.check_dead_end():
            self.recent_state.clear()
            logging.info("explore may be stuck: dead end")
            return -1
        if self.check_loop():
            self.recent_state.clear()
            logging.info("explore may be stuck: loop")
            return -1
        if fix_rate:
            return 0.1
        else:
            return 1 / (1 + math.exp(10 - self.bored_counter))


    def check_dead_end(self, no_progress_count=8):
        if len(self.recent_state) == 0:
            return False
        latest_state = self.recent_state[-1]
        counter = 0
        for i in range(len(self.recent_state)):
            idx = len(self.recent_state) - i - 1
            if self.recent_state[idx] != latest_state:
                break
            counter += 1
        if counter >= no_progress_count:
            self.stuck_states.append(latest_state)
            return True
        else:
            return False

    def check_loop(self, loop_thres=0.7):
        # old
        # if len(self.recent_state) != self.state_len:
        #     return False
        # repeat_count = 0
        # for s in set(self.recent_state):
        #     s_freq = self.recent_state.count(s)
        #     if s_freq > 2:
        #         repeat_count += s_freq
        # if repeat_count >= loop_thres * len(self.recent_state):
        #     return True
        # else:
        #     return False
        if len(self.recent_state) != self.state_len:
            return False
        repeat_count = 0
        state_history = self.recent_state
        state_stat = {s: state_history.count(s) for s in set(self.recent_state)}
        sort_state_stat = sorted(state_stat.items(), key=lambda s: -s[1])
        temp_stuck = []
        for t in sort_state_stat[:2]:
            state_id = t[0]
            state_times = t[1]
            if state_id >= 2 and state_times >= 5:
                repeat_count += state_times
                temp_stuck.append(state_id)
        if repeat_count >= loop_thres * len(self.recent_state):
            self.stuck_states = temp_stuck.copy()
            return True
        else:
            return False


    def get_unvisited_actions(self, state_id):
        unvisited_action = []
        min_time = 99999
        min_id = 0
        if state_id not in self.action_times.keys():
            return []
        for action_id, action_time in self.action_times[state_id].items():
            if action_time == 0:
                unvisited_action.append(action_id)
            if action_time < min_time:
                min_id = action_id
                min_time = action_time
        if len(unvisited_action) == 0:
            # all action has visit, return min time action
            # return [min_id]
            return []
        else:
            return unvisited_action


    # def add_action(self, action: dict):
    #     action_symbol = self.get_action_symbol(action)
    #     self.recent_action.append(action_symbol)
    #     if len(self.recent_action) > self.action_len:
    #         self.recent_action.pop(0)

    # def check_is_in(self, action):
    #     action_symbol = self.get_action_symbol(action)
    #     is_in = (action_symbol in self.recent_action)
    #     return is_in


if __name__ == '__main__':
    a = [[1, 2], [4, 3], [5, 1], [6, 4]]
    a.sort(key=lambda x:-x[1])
    print(a)
