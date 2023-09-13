import os
import re
import shutil
import subprocess
import socket
import logging
import json
import time


class EllaCaller:
    def __init__(self, ori_app_path: str):
        # self.cur_dir = "/".join(os.path.abspath(__file__).split("/")[:-1])
        # app_name = ori_app_path.split("/")[-1]
        # self.ella_res_dir = self.cur_dir + "/ella-out/" + self.cur_dir.replace("/", "_") + "_" + app_name
        # copy_dir = self.cur_dir + "/ella-out/res/" + app_name.replace(".apk", "")
        # if not os.path.exists(copy_dir):
        #     os.mkdir(copy_dir)
        # if not os.path.exists(self.ella_res_dir + "/instrumented.apk"):
        #     shutil.copy(ori_app_path, self.cur_dir + "/" + app_name)
        #     logging.info("perform ella init")
        #     os.system(self.cur_dir + "/ella.sh i " + self.cur_dir + "/" + app_name)
        #     os.remove(self.cur_dir + "/" + app_name)
        #     logging.info("ella init finish")
        #     time.sleep(2)
        #     if not os.path.exists(self.ella_res_dir + "/instrumented.apk"):
        #         shutil.copy(ori_app_path, self.ella_res_dir + "/instrumented.apk")
        #         shutil.copy(ori_app_path, copy_dir + "/" + app_name)
        #         empty_covid = open(copy_dir + "/" + "covids", "w")
        #     else:
        #         shutil.copy(self.ella_res_dir + "/instrumented.apk", copy_dir + "/" + app_name)
        #         shutil.copy(self.ella_res_dir + "/covids", copy_dir + "/" + "covids")
        app_name = ori_app_path.split("/")[-1]
        # copy_dir = "../ella-out/res/" + app_name.replace(".apk", "")
        # copy_dir = "../ella/ella-out/res/" + app_name.replace(".apk", "")
        # self.out_apk = copy_dir + "/" + app_name
        # self.stop_server()
        # self.covids_path = copy_dir + "/covids"
        # self.coverage_path = copy_dir + "/my_coverage.txt"
        copy_dir = "../ella/ella-out/res/" + app_name.replace(".apk", "")
        self.out_apk = ori_app_path
        self.stop_server()
        self.covids_path = ori_app_path.replace(".apk", "").replace("/apps/", "/covids/")
        if not os.path.exists(self.covids_path):
            print("not find!" + self.covids_path)
        self.coverage_path = ori_app_path.replace(".apk", "").replace("/apps/", "/data/") + "/my_coverage.txt"
        f = open(self.coverage_path, "w")
        f.close()
        self.server = MyEllaServer(self.coverage_path, self.covids_path)


    def get_coverage_path(self):
        return self.coverage_path

    def get_coverage(self):
        self.server.get_cov()

    def stop_server(self):
        # ubuntu
        try:
            port_query = subprocess.check_output("lsof -i:23745 | grep LISTEN", shell=True)
            if len(port_query) > 20:
                port_query_str = re.sub(r"\s+", " ", str(port_query, 'utf-8'))
                pid = port_query_str.split(" ")[1]
                kill_cmd = "kill " + pid
                os.system(kill_cmd)
            else:
                print("not process listen 23745")
        except Exception as e:
            print(e)
        # windows
        # try:
        #     port_query = subprocess.check_output('netstat -aon|findstr "23745"', shell=True)
        #     if len(port_query) > 20:
        #         port_query_str = re.sub(r"\s+", " ", str(port_query, 'utf-8')).strip()
        #         print(port_query_str)
        #         pid = port_query_str.split(" ")[-1]
        #         kill_cmd = 'taskkill /f /t /im "' + pid + '"'
        #         print(kill_cmd)
        #         os.system(kill_cmd)
        #     else:
        #         print("not process listen 23745")
        # except Exception as e:
        #     print(e)

    def close_connection(self):
        if self.server.conn != None:
            self.server.conn.close()
            self.server.conn = None

class MyEllaServer:
    def __init__(self, coverage_path: str, covids_path, port=23745):
        self.coverage_path = coverage_path
        cov_cont = open(covids_path, "r").read()
        if len(cov_cont.strip()) == 0:
            self.covids_path = None
        else:
            self.covids_path = covids_path
        self.m_socket = socket.socket()
        self.m_socket.bind(("0.0.0.0", port))
        self.m_socket.listen(3)
        self.conn = None
        self.addr = None
        logging.info("my ella server begin!")

    def get_cov(self):
        if self.covids_path is None:
            return
        try:
            if self.conn == None and os.path.exists(self.covids_path):
                print("waiting for accept")
                self.conn, self.addr = self.m_socket.accept()
            total_data = b''
            while True:
                data = self.conn.recv(1024)
                total_data += data
                if len(data) < 1024:
                    break
            data_str = str(total_data, encoding="utf-8").strip()
            if data_str.count('{"id":"') > 1:
                data_str = '{"id":"' + data_str.split('{"id":"')[-1].strip()
            data_json = json.loads(data_str)
            cov = data_json["cov"]
            logging.info("current coverage len:" + str(len(cov.split("\n"))))
            f = open(self.coverage_path, "w")
            f.write(cov)
            f.close()
        except Exception as e:
            print(e)

    # def restart_server(self):
    #     if self.conn != None:
    #         self.conn.close()
    #         self.conn = None


if __name__ == '__main__':
    # a = EllaCaller("../Data/ReCDriod/apps/1.newsblur_s.apk")
    # os.system("source ~/.bashrc")
    # os.system("echo $JAVA_HOME")
    # os.system("./ella.sh k & ./ella.sh s")
    # os.system("jarsigner")
    # print(subprocess.getoutput("java -version"))
    # os.system("bash ./test.jarsignersh")
    # stdout_output = open('testfile.txt', 'w')
    # subprocess.Popen("jarsigner", shell=True)
    # res = os.system("lsof -i:23745 | grep LISTEN")
    # try:
    #     port_query = subprocess.check_output("lsof -i:23745 | grep LISTEN", shell=True)
    #     if len(port_query) > 20:
    #         port_query_str = re.sub(r"\s+", " ", str(port_query, 'utf-8'))
    #         print(port_query_str)
    #         pid = port_query_str.split(" ")[1]
    #         kill_cmd = "kill " + pid
    #         os.system(kill_cmd)
    #     else:
    #         print("not process listen 23745")
    # except Exception as e:
    #     print(e)
    # app_dir = "/home/wongwuchiu/PycharmProjects/CrashHitter/Data/AndroR2/apps/"
    # for app in os.listdir(app_dir):
    #     _ = EllaCaller(app_dir + app)
    # m_socket = socket.socket()
    # m_socket.bind(("0.0.0.0", 23745))
    # m_socket.listen(3)
    # m_socket.accept()
    # port_query = subprocess.check_output('netstat -aon|findstr "23745"', shell=True)
    # if len(port_query) > 20:
    #     port_query_str = re.sub(r"\s+", " ", str(port_query, 'utf-8')).strip()
    #     print(port_query_str)
    #     pid = port_query_str.split(" ")[-1]
    #     kill_cmd = 'taskkill /f /t /im "' + pid + '"'
    #     print(kill_cmd)
    #     os.system(kill_cmd)
    # else:
    #     print("not process listen 23745")
    ori_app_path = "../Data/ReCDroid/apps/1.newsblur_s.apk"
    a = EllaCaller(ori_app_path)