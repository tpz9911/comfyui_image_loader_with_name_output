import os
import json
from datetime import datetime
import torch
import numpy as np
from PIL import Image, ImageOps, ImageSequence
from PIL.PngImagePlugin import PngInfo
import folder_paths
import node_helpers
from server import PromptServer

# ==================== 1. 高度自定义命名加载节点 ====================
class CustomImageLoaderWithName:
    _COUNTER = {}

    @classmethod
    def INPUT_TYPES(cls):
        input_dir = folder_paths.get_input_directory()
        files = [f for f in os.listdir(input_dir) if os.path.isfile(os.path.join(input_dir, f))] if os.path.exists(input_dir) else []
        return {
            "required": {
                "image": (sorted(files), {"image_upload": True}),
                # 1. 子目录配置
                "subfolder": ("STRING", {
                    "default": "", 
                    "multiline": False, 
                    "placeholder": "例如: image/animal/ (可选，前后斜杠均兼容)"
                }),
                # 2. 自定义前缀
                "custom_prefix": ("STRING", {
                    "default": "", 
                    "multiline": False, 
                    "placeholder": "自定义前缀 (可选)"
                }),
                # 3. 序列化模式 (默认 5 位序号)
                "serial_type": ([
                    "sequence_5_digits (_00001)", 
                    "timestamp (_YYMMDD-hhmmss-ms)", 
                    "none"
                ], {"default": "sequence_5_digits (_00001)"}),
                # 4. 序列化字符串位置 (默认后缀)
                "serial_placement": ([
                    "suffix (在后缀区域)", 
                    "prefix (在前缀区域)"
                ], {"default": "suffix (在后缀区域)"}),
                # 5. 序列化字符串与自定义文本的相对先后 (默认自定义在前)
                "serial_order": ([
                    "custom_first (自定义在前)", 
                    "serial_first (序号在前)"
                ], {"default": "custom_first (自定义在前)"}),
                # 6. 自定义后缀
                "custom_suffix": ("STRING", {
                    "default": "", 
                    "multiline": False, 
                    "placeholder": "自定义后缀 (可选)"
                }),
                # 7. 连接符号 (默认下划线)
                "delimiter": ([
                    "_ (下划线)", 
                    "- (中划线)", 
                    "none (无连接符)"
                ], {"default": "_ (下划线)"}),
            }
        }

    # 输出端口定义：更新为 custom_filename 和 original_filename
    RETURN_TYPES = ("IMAGE", "MASK", "STRING", "STRING")
    RETURN_NAMES = ("image", "mask", "custom_filename", "original_filename")
    FUNCTION = "load_image"
    CATEGORY = "image"

    def load_image(self, image, subfolder="", custom_prefix="", serial_type="sequence_5_digits (_00001)", 
                   serial_placement="suffix (在后缀区域)", serial_order="custom_first (自定义在前)", 
                   custom_suffix="", delimiter="_ (下划线)"):
        # 1. 查找并加载图片
        image_path = folder_paths.get_annotated_filepath(image)
        img = node_helpers.pillow(Image.open, image_path)
        
        output_images = []
        output_masks = []
        w, h = None, None

        for i in ImageSequence.Iterator(img):
            i = ImageOps.exif_transpose(i)
            if i.mode == 'I':
                i = i.point(lambda i: i * (1 / 255))
            image_frame = i.convert("RGB")

            if len(output_images) == 0:
                w = image_frame.size[0]
                h = image_frame.size[1]
            
            if image_frame.size[0] != w or image_frame.size[1] != h:
                continue
            
            image_frame_np = np.array(image_frame).astype(np.float32) / 255.0
            image_frame_tensor = torch.from_numpy(image_frame_np)[None,]
            
            if 'A' in i.getbands():
                mask = np.array(i.getchannel('A')).astype(np.float32) / 255.0
                mask = 1.0 - torch.from_numpy(mask)
            else:
                mask = torch.zeros((h, w), dtype=torch.float32, device="cpu")

            output_images.append(image_frame_tensor)
            output_masks.append(mask.unsqueeze(0))

        if len(output_images) > 1:
            output_image = torch.cat(output_images, dim=0)
            output_mask = torch.cat(output_masks, dim=0)
        else:
            output_image = output_images[0]
            output_mask = output_masks[0]

        # 2. 剥离已知图片扩展名，提取纯原文件名（完整保护 00.00.53.449 这类含多个小数点的情况）
        clean_file_name = image.split(" [")[0]
        base_name = os.path.basename(clean_file_name)
        stem, _ = os.path.splitext(base_name)

        # 3. 计算序列化字符串
        serial_str = ""
        if "sequence_5_digits" in serial_type:
            current_count = self._COUNTER.get(stem, 0) + 1
            self._COUNTER[stem] = current_count
            serial_str = f"{current_count:05d}"
        elif "timestamp" in serial_type:
            now = datetime.now()
            ms = int(now.microsecond / 1000)
            serial_str = f"{now.strftime('%y%m%d-%H%M%S')}-{ms:03d}"

        # 4. 确定分隔符
        if "中划线" in delimiter:
            sep = "-"
        elif "下划线" in delimiter:
            sep = "_"
        else:
            sep = ""

        # 5. 组合前缀块与后缀块
        c_prefix = custom_prefix.strip()
        c_suffix = custom_suffix.strip()
        prefix_parts = []
        suffix_parts = []

        # 序列号归属于前缀还是后缀
        if "prefix" in serial_placement:
            if serial_str:
                if "serial_first" in serial_order:
                    prefix_parts = [serial_str, c_prefix] if c_prefix else [serial_str]
                else:
                    prefix_parts = [c_prefix, serial_str] if c_prefix else [serial_str]
            elif c_prefix:
                prefix_parts = [c_prefix]
            if c_suffix:
                suffix_parts = [c_suffix]
        else:  # 归属于后缀
            if c_prefix:
                prefix_parts = [c_prefix]
            if serial_str:
                if "serial_first" in serial_order:
                    suffix_parts = [serial_str, c_suffix] if c_suffix else [serial_str]
                else:
                    suffix_parts = [c_suffix, serial_str] if c_suffix else [serial_str]
            elif c_suffix:
                suffix_parts = [c_suffix]

        # 6. 将 [前缀块] + [原文件名] + [后缀块] 紧密组装，自动剔除空项避免连续多余下划线
        all_blocks = []
        all_blocks.extend([p for p in prefix_parts if p])
        all_blocks.append(stem)
        all_blocks.extend([s for s in suffix_parts if s])

        final_filename = sep.join(all_blocks)

        # 7. 防御性处理 subfolder 子目录（规范化斜杠并去掉首尾斜杠）
        clean_subfolder = subfolder.strip().replace("\\", "/").strip("/")

        if clean_subfolder:
            full_save_name = f"{clean_subfolder}/{final_filename}"
        else:
            full_save_name = final_filename

        # 返回：图像、遮罩、最终组装路径(带子目录)、纯原文件名
        return (output_image, output_mask, full_save_name, stem)

    @classmethod
    def IS_CHANGED(cls, image, subfolder="", custom_prefix="", serial_type="sequence_5_digits (_00001)", 
                   serial_placement="suffix (在后缀区域)", serial_order="custom_first (自定义在前)", 
                   custom_suffix="", delimiter="_ (下划线)"):
        # 只要启用了动态序列（序号或时间戳），每次点击 Queue 都强制刷新
        if "none" not in serial_type:
            return float("nan")
        image_path = folder_paths.get_annotated_filepath(image)
        return os.path.getmtime(image_path)

# ==================== 2. 保存节点 ====================
class CustomSaveImageExactName:
    def __init__(self):
        self.output_dir = folder_paths.get_output_directory()
        self.type = "output"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE", ),
                "filename": ("STRING", {"default": "output", "multiline": False}),
                "format": (["png", "jpeg", "webp"], {"default": "png"}),
                "on_duplicate": ([
                    "auto_append_timestamp (自动补时间戳防覆盖)", 
                    "warn_and_overwrite (覆盖并发出提示)", 
                    "stop_and_error (停止运行并报错)"
                ], {"default": "auto_append_timestamp (自动补时间戳防覆盖)"}),
            },
            "hidden": {"prompt": "PROMPT", "extra_pnginfo": "EXTRA_PNGINFO"},
        }

    RETURN_TYPES = ("IMAGE", )
    RETURN_NAMES = ("image", )
    FUNCTION = "save_images"
    OUTPUT_NODE = True
    CATEGORY = "image"

    def save_images(self, images, filename="output", format="png", on_duplicate="auto_append_timestamp (自动补时间戳防覆盖)", prompt=None, extra_pnginfo=None):
        clean_path = filename.strip().replace("\\", "/").strip("/")
        
        # 拆分子目录和纯文件名主体
        subfolder = os.path.dirname(clean_path)
        base_name = os.path.basename(clean_path)

        # 仅当输入文本意外带有完全匹配的格式扩展名（如 .png）时才移除它，避免破坏包含圆点的文件名
        known_exts = ('.png', '.jpg', '.jpeg', '.webp')
        for ext_candidate in known_exts:
            if base_name.lower().endswith(ext_candidate):
                base_name = base_name[:-len(ext_candidate)]
                break

        full_output_folder = os.path.join(self.output_dir, subfolder)
        os.makedirs(full_output_folder, exist_ok=True)

        ext = "jpg" if format.lower() == "jpeg" else format.lower()
        results = []

        for batch_number, image in enumerate(images):
            name_stem = f"{base_name}_{batch_number:02d}" if len(images) > 1 else base_name
            target_filename = f"{name_stem}.{ext}"
            file_full_path = os.path.join(full_output_folder, target_filename)

            # 同名检测与处理策略
            if os.path.exists(file_full_path):
                if "auto_append_timestamp" in on_duplicate:
                    # 默认策略：追加精确到秒的时间戳 _YYMMDD_HHMMSS
                    time_suffix = datetime.now().strftime("%y%m%d_%H%M%S")
                    target_filename = f"{name_stem}_{time_suffix}.{ext}"
                    file_full_path = os.path.join(full_output_folder, target_filename)
                    print(f"\033[93m⚠️ [Save Exact Name] 同名文件已存在，已自动重命名为: {target_filename}\033[0m")

                elif "stop_and_error" in on_duplicate:
                    raise FileExistsError(f"目标文件已存在且策略设置为停止: {file_full_path}")

                else:
                    # warn_and_overwrite
                    warning_msg = f"已覆盖已有文件: {target_filename}"
                    print(f"\033[93m⚠️ [警告] {warning_msg}\033[0m")
                    try:
                        PromptServer.instance.send_sync("notification", {
                            "title": "Save Image 覆盖警告",
                            "message": warning_msg,
                            "type": "warning"
                        })
                    except Exception:
                        pass

            # 写入图像与元数据
            i = 255. * image.cpu().numpy()
            img = Image.fromarray(np.clip(i, 0, 255).astype(np.uint8))

            if ext == "png":
                metadata = PngInfo()
                if prompt is not None:
                    metadata.add_text("prompt", json.dumps(prompt))
                if extra_pnginfo is not None:
                    for x in extra_pnginfo:
                        metadata.add_text(x, json.dumps(extra_pnginfo[x]))
                img.save(file_full_path, pnginfo=metadata, compress_level=4)
            elif ext == "webp":
                img.save(file_full_path, quality=95, lossless=True)
            elif ext == "jpg":
                if img.mode != "RGB":
                    img = img.convert("RGB")
                img.save(file_full_path, quality=95)

            results.append({
                "filename": target_filename,
                "subfolder": subfolder,
                "type": self.type
            })

        return {"ui": {"images": results}, "result": (images, )}