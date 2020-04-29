#ecoding:utf-8
import traceback
from xml.dom import minidom

def mkxml(xmlpath,expire):
    doc = minidom.Document()
    config = doc.createElement("config")
    engine = doc.createElement("engine")
    engine.setAttribute("expire", expire)
    engine.setAttribute("cpuid", "")
    config.appendChild(engine)
    doc.appendChild(config)
    return  write_xml(xmlpath,doc)

def write_xml(path,xml_obj):
    try:
        with open(path, 'w') as fh:
            # 4.writexml()第一个参数是目标文件对象，第二个参数是根节点的缩进格式，第三个参数是其他子节点的缩进格式，
            # 第四个参数制定了换行格式，第五个参数制定了xml内容的编码。
            xml_obj.writexml(fh,addindent='   ',indent='',newl='\n',encoding="UTF-8")
            return True
    except Exception as err:
        msg = traceback.format_exc()
        print msg
        return False
        print('错误信息：{0}'.format(err))

if __name__=="__main__":
    mkxml("2020-12-25")