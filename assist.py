import io
import json
import os
import re
import time
import uuid
import base58
import base64
import datetime
import GPUtil
import requests

from PIL import Image
from hashlib import md5, sha256
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from comfy.cli_args import parser

def get_comfyui_uri():
    comfyui_args = parser.parse_args()
    return f'{comfyui_args.listen}:{comfyui_args.port}'

def get_root_uri():
    script_directory = os.path.dirname(os.path.abspath(__file__))
    absolute_path = os.path.abspath(f'{script_directory}../../../')
    if not absolute_path.endswith(os.sep):
        absolute_path += os.sep
    return absolute_path

def get_time():
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

def get_IpInfo():
    response = requests.get('https://ip.cn/api/index?type=0', timeout=3)
    ip_data = response.json()
    if response.status_code == 200:
        return ip_data
    else:
        return None

def get_mechine_info():
    mac = uuid.UUID(int=uuid.getnode()).hex[-12:]
    mac = ":".join([mac[e:e+2] for e in range(0, 12, 2)])
    ip = ""
    position = ""
    info = get_IpInfo()
    if info:
        ip = info.get('ip')
        position = info.get('address')
    return {
        "gpu": GPUtil.getGPUs()[0].name,
        "mac": mac,
        "ip": ip,
        "position": position
    }

def verify_image_exists(path):
    if os.path.exists(path):
        valid_extensions = {".jpg", ".jpeg", ".png", ".webp"}
        ext = os.path.splitext(path)[1].lower()
        if ext in valid_extensions:
            return True
    return False

def json_to_file(filename, jsondata, isStr=False, path='workflows/'):
    base_url = os.path.join(get_root_uri(), 'custom_nodes/comfyui-publish/', path)
    if not os.path.exists(base_url):
        os.makedirs(base_url)
    if isStr:
        str_data = str(jsondata)
        with open(os.path.join(base_url, filename), 'w') as f:
            f.write(str_data)
    else:
        with open(os.path.join(base_url, filename), 'w') as f:
            json.dump(jsondata, f)

# example: "xx_%date:yyyy-MM-dd%" >>>>> xx_2024-08-15
def format_date(str):
    now = datetime.datetime.now()
    custom_formats = {
        "yyyy": "%Y",
        "yy": "%y",
        "MM": "%m",
        "dd": "%d",
        "HH": "%H",
        "mm": "%M",
        "ss": "%S",
    }
    date_formats = re.findall(r"%date:(.*?)%", str)
    for date_format in date_formats:
        original_format = date_format
        for custom_format, strftime_format in custom_formats.items():
            date_format = date_format.replace(custom_format, strftime_format)
        formatted_date = now.strftime(date_format)
        str = str.replace(f"%date:{original_format}%", formatted_date)
    return str

def _EVP_BytesToKey(password, salt, key_len=32, iv_len=16):
    dtot = b''
    d = b''
    while len(dtot) < key_len + iv_len:
        d = md5(d + password + salt).digest()
        dtot += d
    return dtot[:key_len], dtot[key_len:key_len + iv_len]

def encrypt(text):
    salt = os.urandom(8)
    key, iv = _EVP_BytesToKey(b'KILLLIU_CRYPTSTR', salt)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    padded_text = pad(text.encode('utf-8'), AES.block_size)
    encrypted_bytes = cipher.encrypt(padded_text)
    encrypted_data = b'Salted__' + salt + encrypted_bytes
    encrypted_base64 = base64.b64encode(encrypted_data).decode('utf-8')
    return encrypted_base64

def encrypt_sha256(text):
    key = sha256('killliu_key'.encode('utf-8')).digest()[:16]  # 固定16字节密钥
    iv = sha256('killliu_iv'.encode('utf-8')).digest()[:16]    # 固定16字节IV
    cipher = AES.new(key, AES.MODE_CBC, iv)
    padded_text = pad(text.encode('utf-8'), AES.block_size)
    encrypted_bytes = cipher.encrypt(padded_text)
    hash_bytes = sha256(encrypted_bytes).digest()
    encrypted_base58 = base58.b58encode(hash_bytes).decode('utf-8')
    return encrypted_base58

# 按指定高度等比缩放
def get_adapter_size(width, height, target_height, max_width) -> tuple[int, int]:
    aspect_ratio = width / height
    new_width = int(target_height * aspect_ratio)
    if not max_width:
            max_width = target_height
    if new_width > max_width:
        new_width = max_width
        target_height = int(max_width / aspect_ratio)
    return new_width, target_height

def resize_image(img:Image, max_side:int):
    w, h = get_adapter_size(img.size[0], img.size[1], max_side, max_side)
    resized_img = img.resize((w, h), Image.Resampling.LANCZOS)
    return resized_img

def img_path_2_byte_arr(img_path:str, max_side:int):
    try:
        with open(img_path, 'rb') as f:
            img = Image.open(f)
            img_256 = resize_image(img, max_side)
            img_byte_arr = io.BytesIO()
            img_256.save(img_byte_arr, format='webp')
            img_byte_arr.seek(0)
            return img_byte_arr
    except Exception as e:
        raise SystemError(f'{img_path} handle error:{e}')

def img_path_2_base64(img_path: str) -> io.BytesIO:
    try:
        with Image.open(img_path) as img:
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='webp')
            img_byte_arr.seek(0)
            img_base64 = base64.b64encode(img_byte_arr.getvalue()).decode('utf-8')
            return img_base64
    except (OSError, IOError) as _:
        return None
