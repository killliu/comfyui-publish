import asyncio
import collections
import json
import os
import threading
import uuid
import aiohttp
import websockets
import urllib.request
import urllib.parse

from enum import Enum
from .api import API
from .assist import get_comfyui_uri, get_root_uri, img_path_2_base64

RECONNECT_DELAY = 1
MAX_RECONNECT_DELAY = 3

class ConnectType(Enum):
    Comfyui = 1
    Server = 2

class Connector:
    _instance = None
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(Connector, cls).__new__(cls, *args, **kwargs)
        return cls._instance
    def __init__(self):
        self.uid = 0
        self.wid = 0
        self.free = True
        self.workflow = None
        self.client_id = str(uuid.uuid4())
        self.to_server_queue = collections.deque()
        self.comfyConn = None
        self.comfyTasks = None
        self.serverConn = None
        self.serverTasks = None

    async def _connect(self, connectType:ConnectType):
        reconnect_delay = RECONNECT_DELAY
        while True:
            try:
                if connectType == ConnectType.Comfyui:
                    async with websockets.connect(self.comfyUri) as ws:
                        self.comfyConn = ws
                        reconnect_delay = RECONNECT_DELAY
                        self.comfyTasks = [
                            asyncio.create_task(self._recevie_comfyui_msgs()),
                            asyncio.create_task(self._check_comfyui_alive()),
                        ]
                        await asyncio.gather(*self.comfyTasks)
                elif connectType == ConnectType.Server:
                    async with websockets.connect(self.serverUri, extra_headers=self.header) as ws:
                        self.serverConn = ws
                        self.to_server_queue.append({ 'key': 'bind', 'wid': self.wid , 'sid': API().userInfo['serverId'] })
                        reconnect_delay = RECONNECT_DELAY
                        self.serverTasks = [
                            asyncio.create_task(self._recevie_server_msgs()),
                            asyncio.create_task(self._c_t_s_msg())
                        ]
                        await asyncio.gather(*self.serverTasks)
            except websockets.ConnectionClosedError as e:
                # print(f'>>>>>>>>>>>>>>>>>>>>>>>>> {connectType} connection closed error: {e}')
                pass
            except websockets.ConnectionClosedOK as e:
                # print(f'>>>>>>>>>>>>>>>>>>>>>>>>> {connectType} connection closed ok error: {e}')
                pass
            except Exception as e:
                # print(f'>>>>>>>>>>>>>>>>>>>>>>>>> {connectType} connection error: {e}')
                pass
            finally: 
                await asyncio.sleep(reconnect_delay)
                reconnect_delay = min(reconnect_delay * 2, MAX_RECONNECT_DELAY)

    async def _recevie_comfyui_msgs(self):
        try:
            if self.comfyConn.open:
                async for message in self.comfyConn:
                    if type(message) != bytes:
                        await self._handle_comfyui_msg(json.loads(message))
        except json.JSONDecodeError as e:
            print(f'>>>>>>>>>>>>>>>>>>>>>>>>> comfyui msg json decode error: {e}')
            pass
        except Exception as e:
            print(f'>>>>>>>>>>>>>>>>>>>>>>>>> receive comfyui message error: {e}')
            pass
        finally:
            await asyncio.sleep(0.5)

    async def _check_comfyui_alive(self):
        while True:
            if self.comfyConn and self.comfyConn.open == True:
                await self.comfyConn.ping()
            await asyncio.sleep(1)

    async def _recevie_server_msgs(self):
        try:
            if self.serverConn.open:
                async for message in self.serverConn:
                    if type(message) != bytes:
                        msg_json = json.loads(message)
                        await self._handle_server_msg(msg_json)
        except json.JSONDecodeError as e:
            # print(f'>>>>>>>>>>>>>>>>>>>>>>>>> json decode error: {e}')
            pass
        except Exception as e:
            # print(f'>>>>>>>>>>>>>>>>>>>>>>>>> hand receive server message error: {e}')
            pass
        finally:
            await asyncio.sleep(0.5)

    async def _handle_comfyui_msg(self, msg_json):
        msg_type = msg_json['type']
        if not msg_type or msg_type == 'crystools.monitor':
            pass
        elif msg_type == "progress":
            progress = int(msg_json['data']['value'] / msg_json['data']['max'] * 100)
            self.to_server_queue.append({'key': 'progress', 'msg': f'{progress}'})
            pass
        elif msg_type == "executed":
            self.free = True
            self.to_server_queue.append({'key': 'progress', 'msg': '100'})
            pass
        elif msg_type == "execution_interrupted":
            self.to_server_queue.append({'key': 'interrupted'})
            pass

    async def _handle_server_msg(self, msg_json):
        if msg_json['key'] != "run":
            return
        self.wid = msg_json["wid"]
        filePath = os.path.join(get_root_uri(), 'custom_nodes', 'comfyui-publish', 'workflows', f'{str(self.wid)}.json')
        if os.path.exists(filePath) == False:
            self.to_server_queue.appendleft({ 'key':'err', 'msg': 'workflow not exist on comfy server' })
            return
        try:
            with open(filePath, encoding="utf-8") as f:
                workflow_data = f.read()
            self.uid = msg_json['uid']
            self.workflow = json.loads(workflow_data)
            # print(f">>>>>>>>>>>>>> loaded workflow --------: {workflow}")
            # print(f">>>>>>>>>>>>>> get server msg inputs: {msg_json['inputs']}")
            input_json = json.loads(msg_json['inputs'])
            for item in input_json:
                id = str(item['id'])
                if id not in self.workflow:
                    self.to_server_queue.appendleft({ 'key':'err', 'msg': 'workflow was changed, but not update to server' })
                    return
                it = item['type']
                if it == 'klText':
                    self.workflow[id]['inputs']['prompt'] = item['value']
                elif it == 'klInt':
                    self.workflow[id]['inputs']['int_value'] = item['value']
                elif it == 'klSize':
                    cur_size = str(item['value']).split('|')
                    self.workflow[id]['inputs']['width'] = cur_size[0]
                    self.workflow[id]['inputs']['height'] = cur_size[1]
                ###################################### TODO Other type ######################################
            await self.GenImages(self.workflow)
            pass
        except Exception as e:
            # print(f'>>>>>>>>>>>>>>>>>>>>>>>>> execute prompt error: {e}')
            pass

    async def _c_t_s_msg(self):
        bt = 0
        span = 0.05
        try:
            while True:
                bt = bt + span
                if self.serverConn and self.serverConn.open == True:
                    if len(self.to_server_queue) > 0:
                        data = self.to_server_queue.popleft()
                        data['uid'] = self.uid
                        # print(">>>>>>>>>>>>>>>>>>>>> s-> s: ", data)
                        await self.serverConn.send(json.dumps(data))
                    elif bt > 10:
                        bt = 0
                        # print(">>>>>>>>>>>>>>>>>>>>> s-> s >>>> heartbeat")
                        await self.serverConn.send(json.dumps({'key': 'hb', 'hb': self.free}))
                await asyncio.sleep(span)
        except Exception as e:
            pass

    #region ------------------------------------------ Gen Images ------------------------------------------

    async def _queue_prompt(self, prompt):
        try:
            uri = f"http://{get_comfyui_uri()}/prompt"
            data = {"prompt": prompt, "client_id": self.client_id}
            async with aiohttp.ClientSession() as session:
                async with session.post(uri, json=data) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        return result
                    else:
                        self.to_server_queue.appendleft({ 'key':'err', 'msg': e })
                        # print(f">>>>>>>>>>>>>>>>>> Failed to send prompt, status code: {resp.status}")
                        pass
        except aiohttp.ClientConnectionError as e:
            self.to_server_queue.appendleft({ 'key':'err', 'msg': e })
            # print(f">>>>>>>>>>>>>>>>> _queue_prompt failed: {e}")
        except Exception as e:
            self.to_server_queue.appendleft({ 'key':'err', 'msg': e })
            # print(f">>>>>>>>>>>> queue prompt error: {e}")
        return None

    def _get_history(self, prompt_id):
        with urllib.request.urlopen(f"http://{get_comfyui_uri()}/history/{prompt_id}") as response:
            return json.loads(response.read())

    async def GenImages(self, prompt):
        if self.free == False:
            self.to_server_queue.appendleft({ 'key':'err', 'msg': 'server is busy now' })
            return
        self.free = False

        pd = await self._queue_prompt(prompt)
        if pd == None:
            return
        self.prompt_id = pd['prompt_id']

        self.to_server_queue.append({ 'key':'success', 'msg': '' })

        while self.free == False:
            await asyncio.sleep(0.3)

        image_base64s = []
        names = []
        history = self._get_history(self.prompt_id)[self.prompt_id]
        for o in history['outputs']:
            for node_id in history['outputs']:
                node_output = history['outputs'][node_id]
                if 'images' in node_output:
                    for image in node_output['images']:
                        sp = os.path.join(get_root_uri(), 'output', image['subfolder'], image['filename'])
                        # print(">>>>>>>>>>>>>>>>>>>> save image path:", sp)
                        bs, err = img_path_2_base64(sp)
                        if err != "":
                            self.to_server_queue.appendleft({'key': 'err', 'msg': err})
                            pass
                        else:
                            image_base64s.append(bs)
                            names.append(image['filename'].split('.')[-2])
        self.to_server_queue.append({'key': 'images', 'images': image_base64s, 'names': names})

    #endregion

    def _thread(self, connectType:ConnectType):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self._connect(connectType))

    def Connect(self):
        if not API().userInfo or not API().userInfo["APIUrl"] or not API().userInfo['token']:
            return
        if self.serverConn:
            asyncio.run_coroutine_threadsafe(self.serverConn.close(), asyncio.get_event_loop())
        server_uri = API().userInfo["APIUrl"]
        if "http://" in server_uri:
            server_uri = server_uri.replace("http://", "ws://")
        if "https://" in server_uri:
            server_uri = server_uri.replace("https://", "wss://")
        self.serverUri = f'{server_uri}/api/ai_ws_img'
        self.header = {"Authorization": f"Bearer {API().userInfo['token']}"}
        threading.Thread(target=self._thread, args=(ConnectType.Server,), daemon=True).start()
        if self.comfyConn:
            asyncio.run_coroutine_threadsafe(self.comfyConn.close(), asyncio.get_event_loop())
        self.comfyUri = f"ws://{get_comfyui_uri()}/ws?clientId={self.client_id}"
        threading.Thread(target=self._thread, args=(ConnectType.Comfyui,), daemon=True).start()
