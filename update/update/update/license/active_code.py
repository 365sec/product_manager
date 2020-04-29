import os
import hashlib

def get_cpu_code():
    try:
        md = hashlib.md5()
        sid = os.popen("dmidecode -t 4 | grep ID |sort -u |awk -F': ' '{print $2}'").read().strip()
        md.update(sid)
        return md.hexdigest()
    except:
        return ""

print get_cpu_code()