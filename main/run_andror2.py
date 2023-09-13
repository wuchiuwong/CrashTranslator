from env.emulator import EmuRunner
from env.state_info import StateInfo
from env.scorer import Scorer
from gpt3.gpt3_scorer import GPT3Scorer
from strategy.random_strategy import RandomExplore
from strategy.q_learning import QLearningExplore
import subprocess
import logging
import os
import json
from trace_process.trace_preprocess import preprocess_trace
from ella.ella_caller import EllaCaller
from trigger_check.checker import APITriggerChecker
import re
import time
from main.clean_adb import do_clean
from step_generation.gen_steps import StepGenerator

def get_app_info(app_idx, dataset_dir="../Data/EasyData", debug=False):
    app_dict = {}
    for app_name in os.listdir(dataset_dir + "/apps"):
        app_dict.setdefault(int(app_name.split(".")[0]), app_name)
    tgt_app = app_dict[app_idx]
    app_dir = dataset_dir + "/data/" + tgt_app.replace(".apk", "")
    if not os.path.exists(app_dir):
        os.mkdir(app_dir)
    entry_json = json.load(open(dataset_dir + "/activity.txt", "r"))
    app_pkg = entry_json[tgt_app]["app_pkg"]
    app_acti = entry_json[tgt_app]["app_acti"][0]
    all_actis = entry_json[tgt_app]["all_actis"]
    trace_path = dataset_dir + "/traces/" + tgt_app.replace(".apk", ".txt")
    trace_info = preprocess_trace(trace_path, app_pkg, all_actis)
    ori_apk_path = dataset_dir + "/apps/" + tgt_app
    ella_caller = EllaCaller(ori_apk_path)
    api_checker = APITriggerChecker(trace_info, app_pkg, ella_caller)
    # scorer = Scorer(trace_info)
    # dst_acti = target_map[tgt_app.replace(".apk", "")]

    input_path = dataset_dir + "/input/" + tgt_app.replace(".apk", ".json")
    if os.path.exists(input_path):
        input_cont = json.load(open(input_path, "r"))
    else:
        input_cont = {}

    if len(trace_info["trace_actis"]) > 0:
        dst_acti = trace_info["trace_actis"][0].split(".")[-1]
        logging.info("dst activity: case find in trace: " + dst_acti)
    elif len(trace_info["trace_eles"]["class"]) > 0:
        # trace_eles_class = list(trace_info["trace_eles"]["class"])
        # dst_acti = trace_eles_class[0].split(".")[-1].split("$")[0]
        # logging.info("dst activity: case use first class: " + dst_acti)
        trace_eles_class = list(trace_info["trace_eles"]["class"])
        print(trace_eles_class)
        if "$" in trace_eles_class[0]:
            dst_acti = trace_eles_class[0].split(".")[-1].split("$")[0]
        else:
            dst_acti1 = trace_eles_class[0].split(".")[-1][0]
            if dst_acti1.istitle():
                dst_acti = trace_eles_class[0].split(".")[-1]
            else:
                dst_acti = trace_eles_class[0].split(".")[-2]
        logging.info("dst activity: case use first class: " + dst_acti)
    else:
        dst_acti = "unknown"
        logging.info("dst activity: case unknown: " + dst_acti)
    # dst_acti = trace_info["trace_actis"][0]
    all_pages = get_activity_names(all_actis)
    scorer = GPT3Scorer(dst_acti, api_checker, all_pages, trace_info)
    # scorer = GPT3Scorer(dst_acti, api_checker, all_pages, trace_info, use_page=0)
    # scorer = GPT3Scorer(dst_acti, api_checker, all_pages, trace_info, use_widget=0)

    data_dir = app_dir
    action_output = data_dir + "/action_history.txt"
    if not os.path.exists(data_dir):
        os.mkdir(data_dir)
    uninstall_cmd = "adb shell pm uninstall " + app_pkg
    os.system(uninstall_cmd)
    install_cmd = "adb install -g " + ella_caller.out_apk
    os.system(install_cmd)
    if app_idx in [23]:
        need_rotate = True
    else:
        need_rotate = False
    # app_info = {"app_pkg": app_pkg, "app_acti": app_acti, "scorer": scorer, "trace_info": trace_info, "reset": True,
    #             "data_dir": data_dir, "all_actis": all_actis, "api_checker": api_checker, "input_cont": input_cont,
    #             "need_rotate": need_rotate, "ella_caller": ella_caller, "action_output": action_output}
    app_info = {"app_pkg": app_pkg, "app_acti": app_acti, "scorer": scorer, "trace_info": trace_info, "reset": True,
                "data_dir": data_dir, "all_actis": all_actis, "api_checker": api_checker, "input_cont": input_cont,
                "need_rotate": need_rotate, "ella_caller": ella_caller, "action_output": action_output, "use_page": 0}
    # app_info = {"app_pkg": app_pkg, "app_acti": app_acti, "scorer": scorer, "trace_info": trace_info, "reset": True,
    #             "data_dir": data_dir, "all_actis": all_actis, "api_checker": api_checker, "input_cont": input_cont,
    #             "need_rotate": need_rotate, "ella_caller": ella_caller, "action_output": action_output, "use_widget": 0}
    if debug:
        for k, v in trace_info.items():
            print(k)
            print(v)
    if app_idx in [129, 164]:
        app_info["reset"] = False
    if app_idx in [164]:
        app_info.setdefault("relaunch", True)
    if app_pkg == "com.fsck.k9.debug":
        print("%%% push com.fsck.k9.debug")
        app_info["reset"] = False
        push_cmd = "adb -s emulator-5554 root | adb -s emulator-5554 remount | adb  -s emulator-5554 push ../Data/Temp/app_data/com.fsck.k9.debug/ /data/data/"
        os.system(push_cmd)
    return app_info


def do_test(app_idx):
    os.system("adb logcat -c")
    log_out = open("../Data/Temp/log/log_out.txt", "wb")
    log_err = open("../Data/Temp/log/log_err.txt", "wb")
    log_proc = subprocess.Popen("adb logcat *:E", stdout=log_out, stderr=log_err, shell=True)
    app_info = get_app_info(app_idx, dataset_dir=dataset_dir)
    # app_info = {"app_pkg": "com.rigid.birthdroid", "app_acti": "com.rigid.birthdroid.BirthdroidActivity",
    #             "data_dir": "../Data/Test"}
    start_time = time.time()
    logging.info("Stage 1: init state info")
    state_info = StateInfo(app_info)
    app_info["scorer"].set_state_info(state_info)
    logging.info("Stage 2: init env")
    env = EmuRunner(app_info, state_info)
    logging.info("Stage 3: init strategy")
    # explore = RandomExplore(state_info, env)
    explore = QLearningExplore(state_info, env, app_info)
    time.sleep(2)
    logging.info("Stage 4: run testing")
    step = explore.explore()
    if step > 0:
        logging.info("try step: " + str(step))
        logging.info("reproducing time: " + str(time.time() - start_time))
        uninstall_cmd = "adb shell pm uninstall " + app_info["app_pkg"]
        os.system(uninstall_cmd)
        sg = StepGenerator(app_info["data_dir"])
        sg.gen_reproducing_steps()


def get_activity_names(all_actis):
    names = []
    for acti in all_actis:
        activity_name = acti.split(".")[-1]
        activity_name = re.sub(r'([a-z])([A-Z])', r'\1 \2', activity_name).lower()
        activity_name = re.sub(r"[^a-z0-9]", " ", activity_name)
        activity_name = re.sub(r"\s+", " ", activity_name).strip()
        activity_name = activity_name.replace("activity", "").replace("fragment", "").strip()
        names.append(activity_name)
    return names


if __name__ == '__main__':
    do_clean()
    dataset_dir = "../Data/AndroR2"
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(filename)s:%(lineno)s] %(message)s",
                        datefmt="%m-%d %H:%M:%S")
    do_test(271)
    # get_app_info(2, debug=True)
