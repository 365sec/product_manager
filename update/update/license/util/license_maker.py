#ecoding:utf-8
from update import conf_list
import subprocess
import os

class LicenseMaker():

    def executable(self,command):
        try:
            proc = subprocess.Popen(command, shell=True)
            proc.communicate()
            return proc.returncode
        except:
            return False

    @staticmethod
    def read_device_code():
        '''
        仅由平台调用
        :return:
        '''
        licensereq_path = conf_list.vlicensereq
        licencereq_cmd = "%s" % (licensereq_path)
        proc = subprocess.Popen(licencereq_cmd, shell=True)
        proc.communicate()
        ret = proc.returncode
        result = str(ret).strip()
        if result and len(result) == 32:
            return result
        else:
            return False

    def license_maker(self,device_id):
        licensegen_path = conf_list.vlicensegen
        if len(str(device_id).strip()) !=32:
            return False,""
        licencegen_cmd = "%s -f %s" % (licensegen_path,device_id)
        ret = self.executable(licencegen_cmd)
        vlicenselic = conf_list.vlicenselic
        if os.path.exists(vlicenselic):
            return True,vlicenselic
        else:
            return False,""


    def license_reader(self,license_path):
        licenseget_path = conf_list.vlicenseget
        if not os.path.exists(license_path):
            return False,""
        licencegen_cmd = "%s -t %s" % (licenseget_path,license_path)
        ret = self.executable(licencegen_cmd)
        if str(ret).strip():
            return True,ret
        else:
            return False,""