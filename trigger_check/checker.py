import os
from ella.ella_caller import EllaCaller
import logging
from trace_process.trace_preprocess import preprocess_trace
import json

class APITriggerChecker:
    def __init__(self, trace_info, app_pkg, ella_caller: EllaCaller):
        self.target_class = trace_info["trace_eles"]["class"]
        self.target_api = trace_info["trace_eles"]["api"]
        self.app_pkg = app_pkg
        self.ella_caller = ella_caller
        self.id2api = {}
        self.id_is_target = set()
        self.id_same_class = set()
        self.app_api = set()
        self.api_trigger_times = {}
        self.init_api_list()
        self.check_begin = 0

    def init_api_list(self):
        if os.path.exists(self.ella_caller.covids_path):
            cov_ids = open(self.ella_caller.covids_path, "r").readlines()
            for cid, cov_id_line in enumerate(cov_ids):
                part1 = cov_id_line.split(" ")[0][1:-1]
                part3 = cov_id_line.split(" ")[-1].split("(")[0]
                api_name = part1 + "." + part3
                self.id2api.setdefault(cid, api_name)
                if api_name in self.target_api:
                    self.id_is_target.add(cid)
                elif part1 in self.target_class:
                    self.id_same_class.add(cid)
                elif self.app_pkg in part1:
                    self.app_api.add(cid)
                self.api_trigger_times.setdefault(cid, 0)

    def check_trigger_res(self):
        # target_api_first: 5, target_api: 4, target_same_class: 3, new_api_app: 2, new_api: 1, normal: 0
        trigger_type = 0
        coverage_path = self.ella_caller.get_coverage_path()
        if len(coverage_path) == 0 or not os.path.exists(coverage_path):
            logging.info("coverage_path not exist: " + coverage_path)
            return trigger_type
        self.ella_caller.get_coverage()
        coverage_file = open(coverage_path, "r")
        coverage_data = coverage_file.readlines()
        coverage_file.close()
        coverage_len = len(coverage_data)
        logging.info("check coverage from line " + str(self.check_begin) + " to line " + str(len(coverage_data)))
        for coverage_id in coverage_data[self.check_begin:]:
            if not coverage_id.strip().isdigit():
                # logging.info("not digit: " + coverage_id)
                continue
            cid = int(coverage_id.strip())
            if cid not in self.api_trigger_times.keys():
                continue
            if cid in self.id_is_target:
                if self.api_trigger_times[cid] == 0:
                    logging.info("First trigger target api: " + self.id2api[cid])
                    trigger_type = 5
                else:
                    logging.info("Again trigger target api: " + self.id2api[cid])
                    trigger_type = 4
            if self.api_trigger_times[cid] == 0:
                if cid in self.id_same_class and trigger_type < 3:
                    trigger_type = 3
                if cid in self.app_api and trigger_type < 2:
                    trigger_type = 2
                if trigger_type < 1:
                    trigger_type = 1
            self.api_trigger_times[cid] += 1
        self.check_begin = coverage_len
        coverage_file.close()
        return trigger_type


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(filename)s:%(lineno)s] %(message)s",
                        datefmt=""
                                "%m-%d %H:%M:%S")
    dataset_dir = "../Data/ReCDriod"
    tgt_app = "1.newsblur_s.apk"
    entry_json = json.load(open("../Data/ReCDriod/activity.txt", "r"))
    app_pkg = entry_json[tgt_app]["app_pkg"]
    app_acti = entry_json[tgt_app]["app_acti"][0]
    all_actis = entry_json[tgt_app]["all_actis"]
    trace_path = dataset_dir + "/traces/" + tgt_app.replace(".apk", ".txt")
    trace_info = preprocess_trace(trace_path, app_pkg, all_actis)
    ori_apk_path = dataset_dir + "/apps/" + tgt_app
    ella_caller = EllaCaller(ori_apk_path)
    api_checker = APITriggerChecker(trace_info, app_pkg, ella_caller)
    api_checker.check_trigger_res()