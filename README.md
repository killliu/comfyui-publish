# comfyui publisher


## comfyui websocket message types

- crystools.monitor
    ```json
    {
        "type": "crystools.monitor", 
        "data": { 
            "cpu_utilization": 13.6,
            "ram_total": 137189629952,
            "ram_used": 22640160768,
            "ram_used_percent": 16.5,
            "hdd_total": 1098540642304,
            "hdd_used": 736551907328,
            "hdd_used_percent": 67.0,
            "device_type": "cuda",
            "gpus": [{
                        "gpu_utilization": 21,
                        "gpu_temperature": 48,
                        "vram_total": 25757220864,
                        "vram_used": 2439340032,
                        "vram_used_percent": 9.470509434538348
                    }]
        }
    }
    ```
- progress
    ```json
    {
        "type": "progress",
        "data": {
            "value": 20,
            "max": 20,
            "prompt_id": "dbed14bc-92a6-4af4-a0fa-45c537285433",
            "node": "13"
        }
    }
    ```
- executed
    ```json
    {
        "type": "executed", 
        "data": {
            "node": "9",
            "display_node": "9",
            "output": {
                "images": [{
                    "filename": "Flux_00134_.png",
                    "subfolder": "Flux",
                    "type": "output"
                }]
            },
            "prompt_id": "45ba6caf-801e-4236-8855-c6822a80d778"
        }
    }
    ```
- execution_interrupted
- execution_start
    ```json
    {
        "type": "execution_start",
        "data": {
            "prompt_id": "7c01b1e6-5bc7-4506-ba19-9c174a92fe71",
            "timestamp": 1725179499806
        }
    }
    ```
- execution_cached
    ```json
    {
        "type": "execution_cached",
        "data": {
            "nodes": [],
            "prompt_id": "7c01b1e6-5bc7-4506-ba19-9c174a92fe71",
            "timestamp": 1725179499816
        }
    }
    ```
- status
    ```json
    {
        "type": "status",
        "data": {
            "status": {
                "exec_info": {"queue_remaining": 0}
            },
            "sid": "75bc2eef-d322-4982-ba30-be86a0209d26"
        }
    }
    ```
- executing
    ```json
    {
        "type": "executing",
        "data": {
            "node": "10",
            "display_node": "10",
            "prompt_id": "45ba6caf-801e-4236-8855-c6822a80d778"
        }
    }
    ```
- execution_success
    ```json
    {
        "type": "execution_success",
        "data": {
            "prompt_id": "7c01b1e6-5bc7-4506-ba19-9c174a92fe71",
            "timestamp": 1725179527456
        }
    }
    ```

## Segement opt

```python
def yoloworld_esam_image(self, image, yolo_world_model, esam_model, categories, confidence_threshold, iou_threshold, box_thickness, text_thickness, text_scale, with_segmentation, mask_combined, with_confidence, with_class_agnostic_nms, mask_extracted, mask_extracted_index):
    categories = process_categories(categories)
    processed_images = []
    processed_masks = []
    
    for img in image:
        img = np.clip(255. * img.cpu().numpy().squeeze(), 0, 255).astype(np.uint8)
        YOLO_WORLD_MODEL = yolo_world_model
        YOLO_WORLD_MODEL.set_classes(categories)
        results = YOLO_WORLD_MODEL.infer(img, confidence=confidence_threshold)
        detections = sv.Detections.from_inference(results)
        detections = detections.with_nms(
            class_agnostic=with_class_agnostic_nms,
            threshold=iou_threshold
        )

        # 创建空掩码矩阵以便占位
        combined_mask = np.zeros(img.shape[:2], dtype=np.uint8)
        if with_segmentation:
            # 检测框的掩码通过 ESAM 模型生成
            detections.mask = inference_with_boxes(
                image=img,
                xyxy=detections.xyxy,
                model=esam_model,
                device=DEVICE
            )
            
            # 初始化类别的空掩码列表，按 categories 顺序保存
            category_masks = [np.zeros(img.shape[:2], dtype=np.uint8) for _ in categories]
            
            # 检查每个检测到的目标
            for det_idx, det_category in enumerate(detections.class_id):
                if det_category < len(categories):
                    det_mask = detections.mask[det_idx]  # 取出该目标的分割掩码
                    category_masks[det_category] = det_mask  # 根据类别索引替换默认掩码
            
            # 如果需要合并所有掩码为一个
            if mask_combined:
                combined_mask = np.zeros(img.shape[:2], dtype=np.uint8)
                for mask in category_masks:
                    combined_mask = np.logical_or(combined_mask, mask).astype(np.uint8)
                masks_tensor = torch.tensor(combined_mask, dtype=torch.float32)
                processed_masks.append(masks_tensor)
            else:
                # 按类别顺序提取掩码
                if mask_extracted:
                    if mask_extracted_index < len(category_masks):
                        selected_mask = category_masks[mask_extracted_index]
                        masks_tensor = torch.tensor(selected_mask, dtype=torch.float32)
                    else:
                        masks_tensor = torch.zeros_like(torch.tensor(category_masks[0], dtype=torch.float32))
                else:
                    masks_tensor = torch.stack([torch.tensor(mask, dtype=torch.float32) for mask in category_masks], dim=0)
                processed_masks.append(masks_tensor)

        # 处理图像标注
        output_image = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        output_image = annotate_image(
            input_image=output_image,
            detections=detections,
            categories=categories,
            with_confidence=with_confidence,
            thickness=box_thickness,
            text_thickness=text_thickness,
            text_scale=text_scale,
        )
        output_image = cv2.cvtColor(output_image, cv2.COLOR_BGR2RGB)
        output_image = torch.from_numpy(output_image.astype(np.float32) / 255.0).unsqueeze(0)

        processed_images.append(output_image)

    new_ims = torch.cat(processed_images, dim=0)
    
    if processed_masks:
        new_masks = torch.stack(processed_masks, dim=0)
    else:
        new_masks = torch.empty(0)

    return new_ims, new_masks
```
