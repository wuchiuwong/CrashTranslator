import pymongo
import pandas as pd
import re
from nltk.stem import SnowballStemmer
from tqdm import tqdm
import datetime

snowball_stemmer = SnowballStemmer("english")

verbs = ['select', 'choose', 'swipe', 'press', 'type', 'enter', 'open', "insert", "rotate", 'tap', 'click', 'go', 'write', 'input']
verb_counter = {}
step_symbols = ["-", ">"]

verb_prefix = set([w[:2] for w in verbs])
stem_verbs = set([snowball_stemmer.stem(w) for w in verbs])
in_verb_res = {}

res = {'_id': [], "title": [], "body": [], "created_at": [], "close_day": [], "issue_page": [], "repo_page": [],
       "release_page": [], "has_trace": [], "has_step": []}


def export():
    myclient = pymongo.MongoClient()
    dblist = myclient.list_database_names()
    # dblist = myclient.database_names()
    db = myclient.issues
    all_issues = db.issues
    find_count = 0
    all_issue_list = []
    for issue in all_issues.find():
        find_count += 1
        all_issue_list.append(issue)
    print("all report count", len(all_issue_list))
    close_stat = {"all": [], "has_step": [], "has_trace": [], 0: [], 1: [], 10: [], 11: []}
    filter_count1 = 0
    for issue in tqdm(all_issue_list):
        # print(issue)
        # break
        issue_body = str(issue["body"])
        issue_body = re.sub(r"[^\x00-\x7f]", " ", issue_body)
        issue_body = issue_body.lower()
        issue_body = str(issue["body"])
        issue_body = re.sub(r"[^\x00-\x7f]", " ", issue_body)
        issue_year = int(issue["created_at"].split("-")[0])
        create_date = datetime.datetime.strptime(issue["created_at"].split("T")[0], "%Y-%m-%d").date()
        if isinstance(issue["closed_at"], str):
            close_date = datetime.datetime.strptime(issue["closed_at"].split("T")[0], "%Y-%m-%d").date()
            close_day = (close_date - create_date).days
        else:
            close_day = 9999
        has_verb = False
        clean_body_lines = []
        if not check_is_crash(issue_body):
            continue
        has_trace = check_has_trace(issue_body)
        for body_line in issue_body.split("\n"):
            clean_body_line = re.sub(r"[^a-z0-9:]", " ", body_line.lower())
            if len(clean_body_line.strip()) == 0:
                continue
            first_word = clean_body_line.strip().split()[0]
            if first_word == "java" or first_word == "at" or ":" in first_word:
                continue
            is_stacktrace = re.match(r".*?\.java:\d+.*?", body_line)
            if is_stacktrace:
                continue
            has_time = re.match(r".*?\d{2}:\d{2}:\d{2}.*?", body_line)
            if has_time:
                continue
            has_file1 = re.match(r".*?/[a-zA-Z0-9]{2,10}/[a-zA-Z0-9]{2,10}\.[a-zA-Z0-9]{2,10}.*?", body_line)
            has_file2 = re.match(r".*?\\[a-zA-Z0-9]{2,10}\\[a-zA-Z0-9]{2,10}\.[a-zA-Z0-9]{2,10}.*?", body_line)
            if has_file1 or has_file2:
                continue
            has_digit = re.match(r".*?\(\s?\d{3,10}\).*?", body_line)
            if has_digit:
                continue
            clean_body_line2 = re.sub(r"\"", " ", body_line.lower())
            clean_body_line2 = re.sub(r"\'", " ", clean_body_line2)
            clean_body_lines.append(clean_body_line2)
        clean_issue_body = "\n".join(clean_body_lines[:20])
        # if not ("crash" in clean_issue_body or "stop" in clean_issue_body):
        #     continue
        filter_count1 += 1
        for word in clean_issue_body.lower().split():
            if len(word) < 2 or word[:2] not in verb_prefix:
                continue
            if word in in_verb_res.keys():
                if in_verb_res[word]:
                    if word not in verb_counter.keys():
                        verb_counter.setdefault(word, 1)
                    else:
                        verb_counter[word] += 1
                    has_verb = True
                    break
            else:
                stem_word = snowball_stemmer.stem(word)
                if stem_word in stem_verbs:
                    has_verb = True
                    in_verb_res.setdefault(word, True)
                    if word not in verb_counter.keys():
                        verb_counter.setdefault(word, 1)
                    else:
                        verb_counter[word] += 1
                    break
                else:
                    in_verb_res.setdefault(word, False)
        # if not has_verb:
        #     continue
        has_step_symbol1 = False
        for step_symbol in step_symbols:
            if step_symbol in clean_issue_body:
                has_step_symbol1 = True
                break
        if re.match("[^0-9]1\.[^0-9]", " " + clean_issue_body):
            has_step_symbol2 = True
        else:
            has_step_symbol2 = False
        has_step = has_verb and (has_step_symbol1 or has_step_symbol2)
        # if not (has_step_symbol1 or has_step_symbol2):
        #     continue
        res["_id"].append(issue["_id"])
        res["title"].append(issue["title"])
        res["created_at"].append(str(issue["created_at"]).split("T")[0])
        res["close_day"].append(close_day)
        # res["body"].append(clean_issue_body)
        issue_body2 = re.sub(r"[^a-z0-9:A-Z\s\n():]", " ", issue_body)
        res["body"].append(issue_body2)
        issue_page = "https://github.com/" + issue["url"].split(".com/repos/")[1]
        res["issue_page"].append('=HYPERLINK("' + issue_page + '", "show")')
        repo_page = "/".join(issue_page.split("/")[:-2])
        res["repo_page"].append('=HYPERLINK("' + repo_page + '", "show")')
        release_page = repo_page + "/releases"
        res["release_page"].append('=HYPERLINK("' + release_page + '", "show")')
        if has_trace:
            res["has_trace"].append(1)
        else:
            res["has_trace"].append(0)
        if has_step:
            res["has_step"].append(1)
        else:
            res["has_step"].append(0)
        type_symbol = 0
        close_stat["all"].append(close_day)
        if has_trace:
            close_stat["has_trace"].append(close_day)
            type_symbol += 10
        if has_step:
            close_stat["has_step"].append(close_day)
            type_symbol += 1
        close_stat[type_symbol].append(close_day)
    print(filter_count1)
    print(verb_counter)
    report_type_map = {0: "without trace and step", 1: "has step but without trace", 10: "has trace but without step",
                       11: "has trace and step"}
    for report_type, close_days in close_stat.items():
        if report_type in report_type_map.keys():
            show_type = report_type_map[report_type]
        else:
            show_type = report_type
        print(show_type, len(close_days), str(round(100 * len(close_days) / filter_count1, 2)) + "%",
              get_avg(close_days))
    df = pd.DataFrame(res)
    df.to_excel("find_crash_issue_0322.xlsx", index=False)

    # sample_df = df.sample(200)
    # sample_df.to_excel("find_crash_issue_200.xlsx", index=False)
    # sample_df2 = df.sample(1000)
    # sample_df2.to_excel("find_crash_issue_1000.xlsx", index=False)


def check_is_crash(issue_body: str):
    for line in issue_body.split("\n"):
        if "#" not in line and ("crash" in line or "stop" in line or "exception" in line):
            return True
    return False


def check_has_trace(issue_body: str):
    trace_line_count = 0
    for body_line in issue_body.split("\n"):
        is_stacktrace = re.match(r".*?\.java:\d+.*?", body_line)
        if is_stacktrace:
            trace_line_count += 1
        if trace_line_count >= 5:
            return True
    return False


def get_avg(ori_close_day):
    filt_close_day = [i for i in ori_close_day if i < 5000]
    return round(sum(filt_close_day) / len(filt_close_day), 2)


if __name__ == '__main__':
    export()
