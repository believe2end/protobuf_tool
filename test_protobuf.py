import os
import sys
import binascii
from google.protobuf.json_format import MessageToDict

def proto2py(probuf_dir="./protobuf_msgs"):
    protoc_dir = os.path.join("protoc-3.19.4-win64", "bin", "protoc.exe")
    for f in os.listdir(probuf_dir):
        if not f.endswith(".proto"):
            continue
        cmd = f"{protoc_dir} --python_out=./ {probuf_dir}/{f}"
        print(cmd)
        os.system(cmd)

def import_lib(probuf_dir="./protobuf_msgs"):
    import importlib
    # 获取当前目录下的所有文件
    sys.path.append(probuf_dir)
    files = os.listdir(probuf_dir)
    # 遍历文件列表
    all_module_files = []
    for file in files:
        # 如果文件是以.py结尾的模块文件
        if file.endswith('.py'):
            # 去掉文件扩展名
            module_name = file[:-3]
            # 动态import模块
            module = importlib.import_module(module_name)
            all_module_files.append(module)
    return all_module_files

proto2py()
all_module_files = import_lib()


def get_modules(object_name):
    # 获取对象所有方法和属性
    attr_all = []
    for method in dir(object_name):
        attr = getattr(object_name, method)
        if callable(attr):
            attr_all.append(attr())
    return attr_all

def get_all_modules():
    all_modules = []
    for m in all_module_files:
        all_modules.extend(get_modules(m))
    result = {}
    for m in all_modules:
        result[m.DESCRIPTOR.name] = m
    return result

def get_all_attr_value(message):
    # 访问消息中的字段
    result = []
    for field_descriptor in message.DESCRIPTOR.fields:
        field_name = field_descriptor.name
        field_value = getattr(message, field_name)
        result.append( (field_name,field_value) )
    return result

def set_attr(message, kv=[]):
    for field_name,value  in kv:
        if isinstance(getattr(message, field_name), bool):
            value = True if value.upper() == "TRUE" else False
        elif isinstance(getattr(message, field_name), int):
            value = int(value)
        setattr(message, field_name, value)

def get_serialized_data(message):
    serialized_data = message.SerializeToString()
    sstring = binascii.hexlify(serialized_data).decode('utf-8').upper()
    return sstring

def parse_serialized_data(message, hex_string):
    # 将十六进制字符串转换为字节流
    byte_stream = bytes.fromhex(hex_string.replace(" ", ""))
    # 解析数据
    message.ParseFromString(byte_stream)
    return MessageToDict(message)

def input_module_attr(message):
    for field_descriptor in message.DESCRIPTOR.fields:
        field_name = field_descriptor.name
        value = input(f"{field_name}: ")
        if isinstance(getattr(message, field_name), int):
            value = int(value)
        setattr(message, field_name, value)
        field_value = getattr(message, field_name)
        print(f"{message.DESCRIPTOR.name} {field_name}:  {field_value}")

    serialized_data = message.SerializeToString()
    sstring = binascii.hexlify(serialized_data).decode('utf-8').upper()
    print(message.__class__.__name__, ":", sstring, MessageToDict(message))

from PySide6 import QtWidgets
class MyWidget(QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle("ProtoBufTool")
        self.all_modules = get_all_modules()
        self.setup_ui()
    def setup_ui(self):
        def add_lable_input(name, layout, label, input):
            label_n = QtWidgets.QLabel(label)
            attr_le = QtWidgets.QLineEdit(str(input))
            layout.addWidget(label_n)
            layout.addWidget(attr_le)
            self.item_layout[f"{name}@{label}"] = attr_le
        self.main_layout = QtWidgets.QVBoxLayout()
        self.item_layout = {}

        for n, m in self.all_modules.items():
            item_layout = QtWidgets.QHBoxLayout()
            label_n = QtWidgets.QLabel(n)
            label_n.setStyleSheet("background-color: lightgreen;")
            item_layout.addWidget(label_n)
            for attr, attv in get_all_attr_value(m):
                add_lable_input(n, item_layout, attr, attv)
            parse_lineedit = QtWidgets.QLineEdit()
            parse_lineedit.setStyleSheet("background-color: lightgreen;")
            self.item_layout[f"{n}@parseline"] = parse_lineedit
            parse_button = QtWidgets.QPushButton("解析")
            parse_button.setObjectName(f"parse@{n}")
            parse_button.clicked.connect(self.on_button_excute)
            gen_button = QtWidgets.QPushButton("生成")
            gen_button.setObjectName(f"gen@{n}")
            gen_button.clicked.connect(self.on_button_excute)
            item_layout.addWidget(parse_lineedit)
            item_layout.addWidget(parse_button)
            item_layout.addWidget(gen_button)
            item_container = QtWidgets.QWidget()
            item_container.setLayout(item_layout)
            self.main_layout.addWidget(item_container)
        self.setLayout(self.main_layout)
    def on_button_excute(self):
        sender_button = self.sender()
        print(sender_button.objectName())
        bname = sender_button.objectName()
        if bname.startswith('gen'):
            self.action_set(bname.split('@')[-1])
        if bname.startswith('parse'):
            self.action_parse(bname.split('@')[-1])

    def action_set(self, name):
        for k, v in self.item_layout.items():
            if not k.startswith(name):
                continue
            if 'parseline' in k:
                continue
            attr = k.split('@')[-1]
            print(name, "|", attr, "|", v.text())
            set_attr(self.all_modules[name], [(attr, v.text())])
        try:
            sstr = get_serialized_data(self.all_modules[name])
            self.item_layout[f'{name}@parseline'].setText(sstr)
            self.item_layout[f'{name}@parseline'].setStyleSheet("background-color: Lightgreen;")
            print(sstr)
        except Exception as e:
            self.item_layout[f'{name}@parseline'].setStyleSheet("background-color: LightCoral;")
            print(e)
    def action_parse(self, name):
        sstr = self.item_layout[f'{name}@parseline'].text()
        try:
            result = parse_serialized_data(self.all_modules[name], sstr)
            self.item_layout[f'{name}@parseline'].setStyleSheet("background-color: Lightgreen;")
        except Exception as e:
            self.item_layout[f'{name}@parseline'].setStyleSheet("background-color: LightCoral;")
            print(e)
            return
        print(result)
        for k, v in result.items():
            self.item_layout[f"{name}@{k}"].setText(str(v))

def ui():
    import sys
    app = QtWidgets.QApplication(sys.argv)
    window = MyWidget()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    ui()
