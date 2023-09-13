import os
import re
import json
import pandas as pd

trace_stopwords = ['java', 'exception', 'on', 'e', 'lang', 'android', 'invoke', 'runtime', 'at', 'run', 'os', 'method',
                   'handle', 'fatal', 'com', 'internal', 'pid', 'main', 'dispatch', 'process', 'app', 'message',
                   'thread', 'activity', 'zygote', 'reflect', 'caller', 'handler', 'args', 'native', 'looper', 'loop',
                   'and', 'init', 'perform', 'to', 'get', 'by', 'view', 'caused', 'a', 'more', 'null', 'pointer',
                   'callback', 'start', 'call', 'wrap', 'attempt', 'impl', 'unable', 'h', 'list', 'object', 'reference',
                   'state', 'create', 'virtual', 'widget', 'instrumentation', 'launch', 'org', 'adapter', 'item',
                   'click', 'manager', 'info', 'fragment', 'ui', 'for', 'component', 'do', 'util', 'window', 'illegal',
                   'action', 'helper', 'not', 'async', 'selected', 'policy', 'phone', 'input', 'abs', 'builder', 'menu',
                   'root', 'group', 'queue', 'layout', 'jni', 'event', 'sqlite', 'database', 'support', 'v', 'androidx',
                   'touch', 'task', 'stage', 'drawable', 'compat', 'pager', 'inflate', 'kt', 'delegate', 'integer', 'k',
                   'fsck', 'vdc', 'camera', 'class', 'acra', 'open', 'fretboard', 'account', 'base', 'linear',
                   'presenter']


def preprocess_trace(trace_path: str, full_app_pkg: str, all_actis: list):
    # trace_path = "traces/r/21.txt"
    app_pkg = ".".join(full_app_pkg.split(".")[:2])
    trace = open(trace_path, "r", encoding="UTF-8").read()
    # trace_tokens = get_trace_tokens(trace, app_pkg)
    trace_eles = get_related_element(trace, app_pkg)
    trace_actis = get_trace_activities(trace, all_actis)
    trace_tokens = get_token_from_eles(trace, trace_eles, full_app_pkg)
    trace_info = {"trace": trace, "trace_tokens": trace_tokens, "trace_eles": trace_eles, "trace_actis": trace_actis}
    return trace_info


def get_trace_activities(trace: str, all_actis):
    trace_actis = set()
    for line in trace.split("\n"):
        for acti in all_actis:
            if acti in line:
                trace_actis.add(acti)
    return list(trace_actis)


def get_related_element(trace: str, app_pkg: str):
    # trace = trace.replace("\t", " ").replace("\n", " ")
    trace = re.sub("[^a-zA-Z0-9.()$<>]", " ", trace)
    split_app_pkg = app_pkg.split(".")
    if len(split_app_pkg) >= 3:
        short_app_pkg = ".".join(split_app_pkg[:1])
    else:
        short_app_pkg = app_pkg
    trace_eles = trace.split(" ")
    temp_class = []
    related_eles = {"class": [], "api": set(), "all": set()}
    for element in trace_eles:
        # if app_pkg in element and element != app_pkg:
        if len(element.strip()) < 3:
            continue
        if element[-1] == ".":
            element = element[:-1]
        if (app_pkg in element or short_app_pkg in element) and element != app_pkg:
            related_eles["all"].add(element)
            if "(" in element:
                method = element.split("(")[0]
                related_eles["api"].add(method)
                class_of_method = ".".join(method.split(".")[:-1])
                # related_eles["class"].add(class_of_method)
                if class_of_method not in temp_class:
                    temp_class.append(class_of_method)
            else:
                if element not in temp_class:
                    temp_class.append(element)
            # if "activity." in element.lower():
            #     acti_name = element.split("ctivity.")[0] + "ctivity"
            #     related_eles["class"].add(acti_name)
    temp_class2 = []
    print("temp_class", temp_class)
    for idx, class1 in enumerate(temp_class):
        skip_flag = False
        for class2 in temp_class:
            if class1 != class2 and class1 in class2 and class1.count(".") < class2.count("."):
                skip_flag = True
                break
        if skip_flag:
            continue
        # related_eles["class"].append(class1)
        if "activity" in class1.lower() or "fragment" in class1.lower():
            temp_class2.append([class1, idx - 100])
        else:
            temp_class2.append([class1, idx])
    temp_class2.sort(key=lambda x: x[1])
    for t in temp_class2:
        related_eles["class"].append(t[0])
    # print(related_eles)
    return related_eles


def get_trace_tokens(trace: str, app_pkg: str):
    clean_trace_tokens = []
    for trace_line in trace.split("\n"):
        if app_pkg not in trace_line:
            continue
        trace_tokens = split_to_tokens(trace_line)
        trace_tokens = [t for t in trace_tokens if t not in trace_stopwords]
        clean_trace_tokens.extend(trace_tokens)
    # clean_trace_tokens = set(clean_trace_tokens)
    # clean_trace = re.sub(r'[^a-z0-9]', r' ', trace.lower()).lower()
    # for token in clean_trace.split():
    #     clean_trace_tokens.add(token)
    return clean_trace_tokens


def split_to_tokens(in_str: str):
    new_str = re.sub(r'([a-z])([A-Z])', r'\1 \2', in_str).lower()
    new_str = re.sub("[^a-z]", " ", new_str)
    new_str = re.sub("\s+", " ", new_str).strip()
    tokens = new_str.split(" ")
    return set(tokens)


def get_trace_stopwords():
    file_freq = {}
    word_freq = {}
    for root, dirs, files in os.walk("traces/"):
        for name in files:
            trace_content = open(os.path.join(root, name), "r").read()
            trace_tokens = split_to_tokens(trace_content)
            for token in trace_tokens:
                if token not in word_freq.keys():
                    word_freq.setdefault(token, 1)
                else:
                    word_freq[token] += 1
            trace_tokens_set = set(trace_tokens)
            for token in trace_tokens_set:
                if token not in file_freq.keys():
                    file_freq.setdefault(token, 1)
                else:
                    file_freq[token] += 1
    sort_word_freq = sorted(word_freq.items(), key=lambda d: d[1], reverse=True)
    # print(sort_word_freq[:10])
    sort_file_freq = sorted(file_freq.items(), key=lambda d: d[1], reverse=True)
    stopwords = []
    for (word, freq) in sort_file_freq:
        if freq >= 7:
            stopwords.append(word)
    for (word, freq) in sort_word_freq[:100]:
        if word not in stopwords:
            stopwords.append(word)
    return stopwords


def get_token_from_eles(trace: str, trace_eles: dict, app_pkg: str):
    all_tokens = set()
    app_pkg_token = app_pkg.split(".")
    for line in trace.split("\n")[:2]:
        line_tokens = split_to_tokens(line)
        for token in line_tokens:
            if token not in trace_stopwords and token not in app_pkg_token and len(token) > 0:
                all_tokens.add(token)

    for ele_type, eles in trace_eles.items():
        for ele in eles:
            clean_ele = re.sub(r"[^a-zA-Z]", " ", ele.replace(app_pkg, "")).strip()
            if len(clean_ele) > 0:
                token_set1 = split_to_tokens(clean_ele)
                all_tokens = all_tokens.union(token_set1)
                # token_list2 = clean_ele.lower().strip().split(" ")
                # all_tokens = all_tokens.union(set(token_list2))
                for token in clean_ele.lower().strip().split(" "):
                    if len(token) > 0:
                        all_tokens.add(token)
    return all_tokens


def test_trace_analyse():
    res = {"app": [], "trace": [], "trace_tokens": [], "trace_eles": [], "trace_actis": []}
    trace_dir = "../Data/ReCDriod/traces/"
    app_file = open("../Data/ReCDriod/activity.txt", "r")
    app_info = json.load(app_file)
    for apk, info in app_info.items():
        trace_path = trace_dir + apk.replace(".apk", ".txt")
        app_pkg = info["app_pkg"]
        trace_info = preprocess_trace(trace_path, app_pkg, info["all_actis"])
        res["app"].append(apk)
        res["trace"].append(trace_info["trace"])
        res["trace_tokens"].append(trace_info["trace_tokens"])
        res["trace_eles"].append(trace_info["trace_eles"])
        res["trace_actis"].append(trace_info["trace_actis"])
    df = pd.DataFrame(res)
    df.to_csv("trace.csv", index=False)


if __name__ == '__main__':
    # get_trace_stopwords()
    # preprocess_trace("", "com.orpheusdroid.screenrecorder")
    # test_trace_analyse()
    # a = set(["a", "b", "c"])
    # b = set(["d", "b", "c"])
    # c = a.union(b)
    # print(c)
    # t = preprocess_trace("../Data/MyData/traces/3_ankidroid-Anki-Android-9914.txt", "com.ichi2.anki", [])
    # for k, v in t.items():
    #     print(k)
    #     print(v)
    a = [1, 5, 2, 3, 6, 4]
    a.sort(reverse=True)
    print(a)
