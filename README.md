# comfyui publisher


## comfyui websocket message types

- crystools.monitor
    ```json
    {
        'type': 'crystools.monitor', 
        'data': { 
            'cpu_utilization': 13.6,
            'ram_total': 137189629952,
            'ram_used': 22640160768,
            'ram_used_percent': 16.5,
            'hdd_total': 1098540642304,
            'hdd_used': 736551907328,
            'hdd_used_percent': 67.0,
            'device_type': 'cuda',
            'gpus': [{
                        'gpu_utilization': 21,
                        'gpu_temperature': 48,
                        'vram_total': 25757220864,
                        'vram_used': 2439340032,
                        'vram_used_percent': 9.470509434538348
                    }]
        }
    }
    ```
- progress
    ```json
    {
        'type': 'progress',
        'data': {
            'value': 20,
            'max': 20,
            'prompt_id': 'dbed14bc-92a6-4af4-a0fa-45c537285433',
            'node': '13'
        }
    }
    ```
- executed
    ```json
    {
        'type': 'executed', 
        'data': {
            'node': '9',
            'display_node': '9',
            'output': {
                'images': [{
                    'filename': 'Flux_00134_.png',
                    'subfolder': 'Flux',
                    'type': 'output'
                }]
            },
            'prompt_id': '45ba6caf-801e-4236-8855-c6822a80d778'
        }
    }
    ```
- execution_interrupted
- execution_start
    ```json
    {
        'type': 'execution_start',
        'data': {
            'prompt_id': '7c01b1e6-5bc7-4506-ba19-9c174a92fe71',
            'timestamp': 1725179499806
        }
    }
    ```
- execution_cached
    ```json
    {
        'type': 'execution_cached',
        'data': {
            'nodes': [],
            'prompt_id': '7c01b1e6-5bc7-4506-ba19-9c174a92fe71',
            'timestamp': 1725179499816
        }
    }
    ```
- status
    ```json
    {
        'type': 'status',
        'data': {
            'status': {
                'exec_info': {'queue_remaining': 0}
            },
            'sid': '75bc2eef-d322-4982-ba30-be86a0209d26'
        }
    }
    ```
- executing
    ```json
    {
        'type': 'executing',
        'data': {
            'node': '10',
            'display_node': '10',
            'prompt_id': '45ba6caf-801e-4236-8855-c6822a80d778'
        }
    }
    ```
- execution_success
    ```json
    {
        'type': 'execution_success',
        'data': {
            'prompt_id': '7c01b1e6-5bc7-4506-ba19-9c174a92fe71',
            'timestamp': 1725179527456
        }
    }
    ```
