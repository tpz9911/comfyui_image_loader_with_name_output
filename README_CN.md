## comfyui_image_loader_with_name_output

[English](README.md) | **简体中文**

### 简介

**以原文件名保存图像的完美方案：在 ComfyUI 中加载图像并提取原始文件名，支持多级子目录、自定义前后缀、时间戳及序号，配合专用保存节点实现零多余字符的精准文件保存与覆盖保护。**

### 1. 解决的痛点
在使用 ComfyUI 官方的图像加载与保存节点时，常面临以下痛点：
* **无法继承原文件名**：官方保存节点通常只能手动指定固定文本前缀，处理完的图片无法直接沿用原图文件名。
* **强制添加流水号**：官方 `Save Image` 节点强制在文件名末尾追加类似 `_00001_` 的序号，无法输出纯净的原始文件名。
* **多次生图容易丢失或混乱**：如果手动固定文件名，反复执行时难以灵活控制是“覆盖更新”、“按次递增”还是“记录生成时刻”。
* **目录整理繁琐**：想把不同批次结果规整到不同子文件夹中，配置不够直观。

本插件包含两个无缝配合的节点：
* **`Load Image (with Filename Output)`**：像官方节点一样方便地弹窗选图、支持图片预览，同时提取出原始文件名，并按你的规则自由拼装包含子目录、前后缀、序号或时间戳的完整路径。
* **`Save Image (Exact Name)`**：严格按传入的完整名称写盘，绝不强制追加 `_00001_`，同时具备同名文件覆盖安全预警与自动时间戳兜底机制，还能继续把图像向后传递以便做效果对比。

### 2. 节点使用方法

#### 第零步：安装

解压至 `custom_nodes` 目录。

由于 ComfyUI 的发行版本较多（如 Portable 便携整合包、ComfyUI Desktop 官方桌面客户端、Git 手动源码部署等），不同用户的安装路径可能各不相同。**安装的核心操作就是将本节点放入你的 `custom_nodes` 文件夹中。**

1. **定位你的 `custom_nodes` 文件夹**：
   * **方法一（最推荐）**：启动 ComfyUI 后，在界面菜单或设置（⚙️ 齿轮图标）中找到 **“Open Custom Nodes Folder”（打开自定义节点目录）**，点击可直接呼出该目录。
   * **方法二（常见默认路径参考）**：
     * **便携版 (Portable)**：`ComfyUI_windows_portable/ComfyUI/custom_nodes/`
     * **桌面版 (Desktop)**：通常在 `%LOCALAPPDATA%\Comfy-Desktop\...` 或系统的 `AppData/Local` 中寻找包含 `custom_nodes` 的子目录。
     * **源码/独立部署版**：位于你克隆/下载的 `ComfyUI` 代码根目录下的 `custom_nodes/`。

2. **解压文件**：
   * 将 `comfyui_image_loader_with_name_output.zip` 压缩包解压到 `custom_nodes` 目录下。

3. **检查目录结构（重要）**：
   请确保解压后的文件直接位于该文件夹根层，**避免出现两层同名文件夹嵌套**（例如错误的 `.../custom_nodes/comfyui_image_loader_with_name_output/comfyui_image_loader_with_name_output/...`）：

   ```plaintext
   custom_nodes/
      └── comfyui_image_loader_with_name_output/
         ├── __init__.py
         └── file_loader_node.py
   ```

4. **重启 ComfyUI**：
   * 完全退出并重启 ComfyUI。
   * 刷新浏览器或桌面客户端界面。

5. **验证安装**：
   在画布空白处双击或右键，搜索能找到以下两个节点即可正常使用：
   * **`Load Image (with Filename Output)`**（分类：`image`）
   * **`Save Image (Exact Name)`**（分类：`image`）

#### 第一步：配置加载节点 `Load Image (with Filename Output)`
将节点加入画布并选择你的输入图片，下方提供直观的命名控制项：

| 选项名称 | 说明与建议 |
| :--- | :--- |
| **`subfolder`** | **输出子目录**（可选）。例如填写 `portraits/animal/`。无论首尾是否输入斜杠，插件都会自动清洗为规范路径。 |
| **`custom_prefix`** | **自定义前缀**（可选）。会放置在原始文件名前面。 |
| **`serial_type`** | **序列化类型**。可选：`五位递增序号 (_00001)`（默认）、`毫秒级时间戳` 或 `无 (none)`。 |
| **`serial_placement`**| **序号所处区域**。选择将序列号放在原始文件名的 `前缀区域` 还是 `后缀区域`（默认）。 |
| **`serial_order`** | **排列次序**。当同时存在自定义文字和序号时，决定哪一个排在前面（默认自定义在前）。 |
| **`custom_suffix`** | **自定义后缀**（可选）。会放置在原始文件名后面。 |
| **`delimiter`** | **连接符**。各项文本之间的分隔符号，支持 `_（下划线）`（默认）、`-（中划线）` 或 `无`。 |

**端口输出说明**：
* `image` / `mask`：图像张量与遮罩，直接连接你的生图或重绘流程。
* `custom_filename`：**核心端口**。已经拼装好子目录、前后缀、序号的最终名称，直接连至保存节点。
* `original_filename`：纯净的原文件名（不含任何前后缀与子目录），方便用于打标、提示词或日志记录。

#### 第二步：配置保存节点 `Save Image (Exact Name)`
替换掉官方的 `Save Image` 节点，置于工作流末尾：
1. 将经过模型处理的最终图像连接到节点的 **`images`** 输入槽。
2. 将加载节点的 **`custom_filename`** 连接到保存节点的 **`filename`** 输入槽。
3. **格式与同名策略选择**：
   * **`format`**：支持 `png`（默认，完整保留生图工作流元数据）、`jpeg`、`webp`。
   * **`on_duplicate`**（重名策略）：
     * `auto_append_timestamp`（默认推荐）：若磁盘已存在同名文件，自动追加当前时间后缀防丢失。
     * `warn_and_overwrite`：直接覆盖原文件，并在 ComfyUI 页面右上角弹窗提醒。
     * `stop_and_error`：遇到同名立刻中断运行并报错。
4. **图像对比扩展**：节点右侧带有 **`image`** 输出引脚，可直接连接 `Image Compare` 等对比节点，保存与效果比对两不误。
