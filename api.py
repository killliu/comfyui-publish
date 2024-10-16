import json
import os
import aiohttp

from enum import Enum
from .assist import encrypt, get_mechine_info, get_root_uri, img_path_2_byte_arr, json_to_file
from .klLoger import klLoger

class WorkflowResultEnum(Enum):
    Failed = 1
    NeedLogin = 2
    UpdateID = 3
    Success = 4
    UpdateSuccess = 5

class API:
    _instance = None
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(API, cls).__new__(cls, *args, **kwargs)
        return cls._instance
    def __init__(self):
        if not hasattr(self, 'userInfo'):
            self.fresh_userInfo()

    def fresh_userInfo(self):
        fp = os.path.join(get_root_uri(), 'custom_nodes/comfyui-publish/', 'auth.json')
        if os.path.exists(fp):
            with open(fp, "r", encoding="utf-8") as f:
                auth_data = f.read()
            self.userInfo = json.loads(auth_data)
            if 'uid' not in self.userInfo or 'username' not in self.userInfo or 'nickname' not in self.userInfo or 'token' not in self.userInfo or 'APIUrl' not in self.userInfo:
                self.userInfo = None
            return self.userInfo
        else:
            self.userInfo = None
            return None

    def get_addr(self, data):
        outputs = data['prompt']['output']
        for key in outputs:
            if outputs[key]['class_type'] == "klPublisher":
                return outputs[key]['inputs']['APIUrl']
        return ''

    async def login(self, data) -> str|None:
        addr = self.get_addr(data)
        username = data['username']
        password = encrypt(data['password'])
        if addr == '':
            return "Set APIUrl first"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{addr}/api/login",
                    data={ "username": username, "password": password },
                    headers={ 'Content-Type': 'application/x-www-form-urlencoded' }
                ) as response:
                    result = await response.json()
            if 'failed' in result:
                return result['failed']
            
            headers = { 'Content-Type': 'application/x-www-form-urlencoded', "Authorization": f"Bearer {result['token']}" }
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{addr}/api/comfy_server", data={"server": json.dumps(get_mechine_info())}, headers=headers) as response:
                    server_result = await response.json()
            
            klLoger().error(f"\n\n>>>>>>>>>>>>>>>>> server_result: {server_result}\n\n")
            if 'failed' in server_result:
                return server_result['failed']
            self.userInfo = {
                'APIUrl': addr,
                'uid': result['uid'],
                'auth': result['auth'],
                'username': result['username'],
                'nickname': result['nickname'],
                'token': result['token'],
                'serverId': server_result['server']
            }
            json_to_file('auth.json', self.userInfo, False, "")
            return None
        except Exception as e:
            return f"An error occurred: {str(e)}"

    async def add_workflow(self, data):
        addr = ''
        cover_uri = ''
        node_data = None
        upload_cover = False
        workflow_nodes = data['data']['workflow']['nodes']
        klInputs = []
        fixedPower = True
        for node in workflow_nodes:
            node_type = node.get('type')
            if node_type == "klPublisher":
                id = int(node["widgets_values"][2])
                addr = node["widgets_values"][0]
                cover_uri = node["widgets_values"][7]
                upload_cover = node["widgets_values"][6]
                isI2I = node["widgets_values"][3] == "Image2Image"
                node_data = {
                    'id': id,
                    'sid': self.userInfo['serverId'],
                    'title': node["widgets_values"][1],
                    'desc': node["widgets_values"][4],
                    'power': int(node["widgets_values"][5]),
                    'is_i2i': isI2I,
                }
                if isI2I and id > 0 and id > 100000000:
                    return WorkflowResultEnum.Failed, "workflow id not correct"
                if not isI2I and id > 0 and id < 100000000:
                    return WorkflowResultEnum.Failed, "workflow id not correct"
            if node_type == "klImage" or node_type == "klText" or node_type == "klText1" or node_type == "klInt" or node_type == "klSeed" or node_type == "klBool":
                wv = node.get('widgets_values')
                value = wv[2]
                if node_type == "klBool":
                    value = "0" if wv[2] == False else "1"
                elif node_type == "klInt":
                    value = str(wv[2])
                klInputs.append({ 'id':node.get('id'), 'type':node.get('type'), 'title': wv[0], 'desc': wv[1], 'value': value })
            if node_type == "klSize":
                fixedPower = False
                wv = node.get('widgets_values')
                value = f'{wv[0]}|{wv[1]}'
                klInputs.append({ 'id':node.get('id'), 'type':node.get('type'), 'title': '', 'desc': '', 'value': value })
        node_data['fp'] = 1 if fixedPower else 0
        if len(klInputs) > 0:
            inputs = sorted(klInputs, key=lambda item: item['id'])
            node_data['inputs'] = json.dumps(inputs)
        if addr == "":
            return WorkflowResultEnum.Failed, "APIUrl is empty"
        if node_data['title'] == "" or node_data['desc'] == "":
            return WorkflowResultEnum.Failed, "Title or Describe is empty"
        async with aiohttp.ClientSession() as session:
            form_data = aiohttp.FormData()
            form_data.add_field('data', json.dumps(node_data))
            if upload_cover:
                img_path = os.path.join(get_root_uri(), 'input', cover_uri)
                form_data.add_field('file', img_path_2_byte_arr(img_path, 256), filename='cover.webp', content_type='image/webp')
            header = {"Authorization": f"Bearer {self.userInfo['token']}"}
            if node_data['id'] > 0:
                async with session.put(f'{addr}/api/ai_image_wf', data=form_data, headers=header) as response:
                    try:
                        resp = await response.json()
                        if 'failed' in resp:
                            if resp['failed'] == 'auth failed' or resp['failed'] == 'login again':
                                return WorkflowResultEnum.NeedLogin, ''
                            else:
                                return WorkflowResultEnum.Failed, resp['failed']
                        if 'success' in resp:
                            json_to_file(f'{resp["success"]}.json', {k: v for k, v in data['data']['output'].items() if v.get("class_type") != "klPublisher"})
                            return WorkflowResultEnum.UpdateSuccess, resp['success']
                    except Exception as e:
                        return WorkflowResultEnum.Failed, f'{e}'
            else:
                async with session.post(f'{addr}/api/ai_image_wf', data=form_data, headers=header) as response:
                    try:
                        resp = await response.json()
                        if 'failed' in resp:
                            if resp['failed'] == 'auth failed' or resp['failed'] == 'login again':
                                return WorkflowResultEnum.NeedLogin, ''
                            else:
                                return WorkflowResultEnum.Failed, resp['failed']
                        if 'success' in resp:
                            json_to_file(f'{resp["success"]}.json', {k: v for k, v in data['data']['output'].items() if v.get("class_type") != "klPublisher"})
                            return WorkflowResultEnum.UpdateID, resp['success']
                    except Exception as e:
                        return WorkflowResultEnum.Failed, f'{e}'
