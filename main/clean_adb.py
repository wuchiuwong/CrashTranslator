import os
import subprocess
import re

def do_clean():
    # os.remove("../Data/Temp/log/log_out.txt")
    # res = subprocess.Popen('ps aux | grep "adb logcat"', shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)
    # result = res.stdout.readlines()
    # for line in result:
    #     pid = str(line).split(" ")[1]
    #     print(pid)
    #     os.system("kill " + pid)
    # print("### clean process")
    try:
        port_query = subprocess.check_output('ps aux | grep "adb logcat"', shell=True)
        if len(port_query) > 20:
            port_query_str = re.sub(r"\s+", " ", str(port_query, 'utf-8'))
            pid = port_query_str.split(" ")[1]
            kill_cmd = "kill " + pid
            os.system(kill_cmd)
        else:
            print("not process listen 23745")
    except Exception as e:
        print(e)



if __name__ == '__main__':
    do_clean()