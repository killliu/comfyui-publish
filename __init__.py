import json
import os
import server
import folder_paths
import nodes

from aiohttp import web
from .assist import is_chinese
from .api import API, WorkflowResultEnum
from .ws import Connector
from .klLoger import klLoger
from translate import Translator

def get_node(data):
    try:
        for node in data['data']['workflow']['nodes']:
            if node.get('type') == "klPublisher":
                return node
    except Exception:
        raise ValueError("node not found")
    raise ValueError("node not found")

@server.PromptServer.instance.routes.post("/check")
async def check(request):
    _ = await request.json()
    userInfo = {"userInfo":API().fresh_userInfo()}
    return web.Response(status=200, text=json.dumps(userInfo))

@server.PromptServer.instance.routes.post("/login")
async def login(request):
    data = await request.json()
    result = await API().login(data)
    if API().userInfo != None:
        Connector().Connect()
    if result == None:
        return web.Response(status=200, text=json.dumps({"su":""}))
    else:
        return web.Response(status=200, text=json.dumps({"message": result}))

@server.PromptServer.instance.routes.post("/add_workflow")
async def add_workflow(request):
    data = await request.json()
    resultType, msg = await API().add_workflow(data)
    result = {
        "resultType": resultType.value,
        "message": msg
    }
    if resultType == WorkflowResultEnum.UpdateID:
        if msg == "":
            result["resultType"] = WorkflowResultEnum.Failed
            result["message"] = "workflow's id error from server"
    return web.Response(status=200, text=json.dumps(result))

class klImage(nodes.LoadImage):
    @classmethod
    def INPUT_TYPES(s):
        input_dir = folder_paths.get_input_directory()
        files = [f for f in os.listdir(input_dir) if os.path.isfile(os.path.join(input_dir, f))]
        return {
            "required": {
                "title": ("STRING", { "multiline": False, "default": "" }),
                "describe": ("STRING", { "multiline": True, "default": "" }),
                "image": (sorted(files), {"image_upload": True}),
            }
        }
    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "load_capture"
    CATEGORY = "killliu"
    def load_capture(self, title, describe, image):
        return super().load_image(folder_paths.get_annotated_filepath(image))

class klText:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "title": ("STRING", { "multiline": False, "default": "" }),
                "describe": ("STRING", { "multiline": True, "default": "" }),
                "prompt": ("STRING", {"multiline": True, "default": "" }), 
            }
        }
    RETURN_TYPES = ("STRING",)
    FUNCTION = "encode"
    CATEGORY = "killliu"
    def encode(self, title, describe, prompt):
        if is_chinese(prompt):
            text = Translator(to_lang="en", from_lang="zh").translate(prompt)
            klLoger().log(f">>>>>>>>>>>>>>>>>>>>>>>>>>>> {describe} translated: {text}")
            return text,
        return prompt,

class klText1:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "title": ("STRING", { "multiline": False, "default": "" }),
                "describe": ("STRING", { "multiline": True, "default": "" }),
                "prompt": ("STRING", {"multiline": False, "default": "" }), 
            }
        }
    RETURN_TYPES = ("STRING",)
    FUNCTION = "encode"
    CATEGORY = "killliu"
    DESCRIPTION = ("Text with one line")
    def encode(self, title, describe, prompt):
        if is_chinese(prompt):
            text = Translator(to_lang="en", from_lang="zh").translate(prompt)
            klLoger().log(f">>>>>>>>>>>>>>>>>>>>>>>>>>>> {describe} translated: {text}")
            return text,
        return prompt,

class klInt:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "title": ("STRING", { "multiline": False, "default": "" }),
                "describe": ("STRING", { "multiline": True, "default": "" }),
                "int_value": ("INT", { "default": 0, "min": -9223372036854775808, "max": 9223372036854775807, "step": 1 }),
            }
        }
    RETURN_TYPES = ("INT",)
    FUNCTION = "encode"
    CATEGORY = "killliu"
    def encode(self, title, describe, int_value):
        return int_value,

class klSimpleMath:
    def __init__(self):
        pass
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "a": ("INT", {"default": 0, "min": -0xffffffffffffffff, "max": 0xffffffffffffffff, "step": 1}),
                "b": ("INT", {"default": 0, "min": -0xffffffffffffffff, "max": 0xffffffffffffffff, "step": 1}),
                "operation": (["add", "subtract", "multiply", "divide_float", "divide", "modulo", "power"],),
            },
        }
    RETURN_TYPES = ("INT", "FLOAT",)
    FUNCTION = "math_operation"
    CATEGORY = "killliu"
    def math_operation(self, a, b, operation):
        if operation == "add":
            result = a + b
            return result, float(result)
        elif operation == "subtract":
            result = a - b
            return result, float(result)
        elif operation == "multiply":
            result = a * b
            return result, float(result)
        elif operation == "divide_float":
            if b == 0:
                return 0, float('inf') 
            return int(float(a) / float(b)), float(a) / float(b)
        elif operation == "divide":
            if b == 0:
                return 0,
            return a // b, float(a) / float(b)
        elif operation == "modulo":
            if b == 0:
                return 0, float('inf')
            return a % b, float(a) / float(b)
        elif operation == "power":
            result = a ** b
            return result, float(result)

class klInt2String:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "int_value": ("INT", { "default": 0, "min": -9223372036854775808, "max": 9223372036854775807, "step": 1 }),
            }
        }
    RETURN_TYPES = ("STRING",)
    FUNCTION = "encode"
    CATEGORY = "killliu"
    def encode(self, int_value):
        return str(int_value),

class klSeed:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "title": ("STRING", { "multiline": False, "default": "" }),
                "describe": ("STRING", { "multiline": True, "default": "" }),
                "int_value": ("INT", { "default": 0, "min": -9223372036854775808, "max": 9223372036854775807, "step": 1 }),
            }
        }
    RETURN_TYPES = ("INT",)
    FUNCTION = "encode"
    CATEGORY = "killliu"
    def encode(self, title, describe, int_value):
        return int_value,

class klSize:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "width": ("INT", { "default": 768, "min": 256, "max": 2048, "step": 64 }),
                "height": ("INT", { "default": 1024, "min": 256, "max": 2048, "step": 64 }),
            }
        }
    RETURN_TYPES = ("INT","INT",)
    RETURN_NAMES = ("Width","Height",)
    FUNCTION = "encode"
    CATEGORY = "killliu"
    def encode(self, width, height):
        return width, height,

class klSizeAdapter:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "width": ("INT", { "default": 768, "min": 256, "max": 2048, "step": 64 }),
                "height": ("INT", { "default": 1024, "min": 256, "max": 2048, "step": 64 }),
                "invert": ("BOOLEAN", {"default": False}),
                "max_side": ("INT", { "default": 1024, "min": 256, "max": 2048, "step": 64 }),
            }
        }
    RETURN_TYPES = ("INT","INT","INT","INT","STRING",)
    RETURN_NAMES = ("width","height","adapter width", "adapter height", "adapter size")
    FUNCTION = "encode"
    CATEGORY = "killliu"
    def encode(self, width, height, invert, max_side):
        if invert == True:
            width, height = height, width
        aspect_ratio = width / height
        if width < height:
            if height > max_side:
                adp_height = max_side
                adp_width = int(max_side * aspect_ratio)
            else:
                return width, height, width, height, f"w:{str(width)},h:{str(height)}"
        else:
            if width > max_side:
                adp_width = max_side
                adp_height = int(max_side / aspect_ratio)
            else:
                return width, height, width, height, f"w:{str(width)},h:{str(height)}"
        return width, height, adp_width, adp_height, f"w:{str(adp_width)},h:{str(adp_height)}"

class klBool:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "title": ("STRING", { "multiline": False, "default": "" }),
                "describe": ("STRING", { "multiline": True, "default": "" }),
                "bool_value": ("BOOLEAN", {"default": False}),
            }
        }
    RETURN_TYPES = ("BOOLEAN",)
    FUNCTION = "encode"
    CATEGORY = "killliu"
    def encode(self, title, describe, bool_value):
        return bool_value,

class klPublisher:
    def __init__(self) -> None:
        pass
    @classmethod
    def INPUT_TYPES(s):
        input_dir = folder_paths.get_input_directory()
        files = [f for f in os.listdir(input_dir) if os.path.isfile(os.path.join(input_dir, f))]
        return {
            "required": {
                "APIUrl": ("STRING", { "multiline": False, "default": "", "placeholder": "" }),
                "Tittle": ("STRING", { "multiline": False, "default": "", "placeholder": "" }),
                "ID": ("INT", { "default": 0, "min": 0, "max": 999999, "step": 1, "display": "number" }),
                "Type": (["Image2Image", "Prompt2Image",], { "default": "Image2Image", }),
                "Describe": ("STRING", { "multiline": True, "default": "", "placeholder": "" }),
                "Power": ("INT", { "default": 10, "min": 0, "max": 999999, "step": 1, "display": "number" }),
                "UploadCover": ("BOOLEAN", {"default": False}),
                "image": (sorted(files), {"image_upload": True}),
            }
        }
    RETURN_TYPES = ()
    CATEGORY = "killliu"
    DESCRIPTION = ("Welcome to use kl publisher")

WEB_DIRECTORY = "./web"
NODE_CLASS_MAPPINGS = {
    "klPublisher": klPublisher,
    "klImage": klImage,
    "klText": klText,
    "klText1": klText1,
    "klInt": klInt,
    "klSimpleMath": klSimpleMath,
    "klInt2String": klInt2String,
    "klSeed": klSeed,
    "klSize": klSize,
    "klSizeAdapter": klSizeAdapter,
    "klBool": klBool,
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "klPublisher": "publish (http://localhost:9528)",
    "klImage": "image loader",
    "klText": "text",
    "klText1": "text 1line",
    "klInt": "int",
    "klSimpleMath": "simple math",
    "klInt2String": "int2string",
    "klSeed": "seed",
    "klSize": "size",
    "klSizeAdapter": "size adapter",
    "klBool": "boolean",
}

klLoger().enable(True, 0)

Connector().Connect()
