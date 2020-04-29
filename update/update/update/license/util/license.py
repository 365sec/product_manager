import rc4

class License():
    def __init__(self,cpucode):
        self.secret_key= "365sec.com"+cpucode
        self.rc = rc4.rc4(self.secret_key)

    def encryption(self,fragment):
        return self.rc.encode(fragment)

    def  decipherment(self,fragment):
        return self.rc.decode(fragment)

