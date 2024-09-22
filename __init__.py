import json
import os
import server
import folder_paths
import nodes

from aiohttp import web
from .api import API, WorkflowResultEnum
from .ws import Connector

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
                "describe": ("STRING", { "multiline": False, "default": "" }),
                "image": (sorted(files), {"image_upload": True}),
            }
        }
    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "load_capture"
    CATEGORY = "killliu"
    def load_capture(self, describe, image):
        return super().load_image(folder_paths.get_annotated_filepath(image))

class klText:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "describe": ("STRING", { "multiline": False, "default": "" }),
                "prompt": ("STRING", {"multiline": True, "default": "" }), 
            }
        }
    RETURN_TYPES = ("STRING",)
    FUNCTION = "encode"
    CATEGORY = "killliu"
    def encode(self, describe, prompt):
        return prompt,
    
class klText1:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "describe": ("STRING", { "multiline": False, "default": "" }),
                "prompt": ("STRING", {"multiline": False, "default": "" }), 
            }
        }
    RETURN_TYPES = ("STRING",)
    FUNCTION = "encode"
    CATEGORY = "killliu"
    DESCRIPTION = ("Text with one line")
    def encode(self, describe, prompt):
        return prompt,

class klInt:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "describe": ("STRING", { "multiline": False, "default": "" }),
                "int_value": ("INT", { "default": 0, "min": -9223372036854775808, "max": 9223372036854775807, "step": 1 }),
            }
        }
    RETURN_TYPES = ("INT",)
    FUNCTION = "encode"
    CATEGORY = "killliu"
    def encode(self, describe, int_value):
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

class klBool:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "describe": ("STRING", { "multiline": False, "default": "" }),
                "bool_value": ("BOOLEAN", {"default": False}),
            }
        }
    RETURN_TYPES = ("BOOLEAN",)
    FUNCTION = "encode"
    CATEGORY = "killliu"
    def encode(self, describe, bool_value):
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
    "klSize": klSize,
    "klBool": klBool,
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "klPublisher": "publish",
    "klImage": "image loader",
    "klText": "text",
    "klText1": "text oneline",
    "klInt": "int",
    "klSize": "size",
    "klBool": "boolean",
}

Connector().Connect()
