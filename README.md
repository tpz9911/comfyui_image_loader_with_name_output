## comfyui_image_loader_with_name_output

**English** | [简体中文](README_CN.md)

### Summary
**The definitive solution for retaining original filenames in ComfyUI: load images with visual previews, extract clean file stems, customize multi-level subfolders, prefixes, suffixes, sequence numbers, or timestamps, and save results cleanly without forced serial suffixes.**

### 1. Problems Solved
When using official ComfyUI load/save nodes, you may encounter several inconveniences:
* **Cannot Inherit Source Filenames**: Official save nodes require manual prefix inputs; output files cannot automatically retain original input filenames.
* **Forced Numbering Suffixes**: The default `Save Image` node forcefully appends counter numbers like `_00001_`, making it impossible to output clean, exact filenames.
* **Overwriting vs. Tracking Conflicts**: Manually fixing filenames makes it difficult to manage whether repeated runs should overwrite, increment cleanly, or record execution timestamps.
* **Cumbersome Subdirectory Routing**: Organizing outputs into structured folders is often rigid or unintuitive.

**Snapshot**

![Snapshot](/img/snapshot_01.png)

This suite provides two complementary nodes:
* **`Load Image (with Filename Output)`**: Retains the native upload dialog and visual preview while extracting the exact filename stem. It formats paths according to your custom subfolders, pre/suffixes, counters, and timestamps.
* **`Save Image (Exact Name)`**: Saves images strictly according to the incoming filename with zero unwanted suffixes, features overwrite warnings and timestamp fallbacks, preserves workflow metadata, and passes the image through for real-time visual comparison.

### 2. How to Use

#### Step 0: Installation

Extract into the `custom_nodes` Directory.

ComfyUI has various distribution and installation methods (e.g., Portable standalone packages, official ComfyUI Desktop client, manual Git clone, etc.), and folder paths vary between systems. **The only requirement is to place this custom node into your `custom_nodes` folder.**

1. **Locate your `custom_nodes` Folder**:
   * **Method 1 (Recommended)**: Inside ComfyUI, look in the menu or Settings (⚙️ gear icon) for **"Open Custom Nodes Folder"** to open the path directly in your file explorer.
   * **Method 2 (Common Paths for Reference)**:
     * **Portable package**: `ComfyUI_windows_portable/ComfyUI/custom_nodes/`
     * **Desktop client**: Typically located under `%LOCALAPPDATA%\Comfy-Desktop\...` or your system's `AppData/Local` directory.
     * **Git / Source install**: The `custom_nodes/` folder within your main `ComfyUI` repository directory.

2. **Extract the Files**:
   * Extract `comfyui_image_loader_with_name_output.zip` into your `custom_nodes` folder.

3. **Verify Directory Structure (Important)**:
   Ensure the scripts are directly inside the node folder **without accidental nested duplicate folders** (e.g., avoid `.../custom_nodes/comfyui_image_loader_with_name_output/comfyui_image_loader_with_name_output/...`):

   ```plaintext
   custom_nodes/
      └── comfyui_image_loader_with_name_output/
         ├── __init__.py
         └── file_loader_node.py
   ```

4. **Restart ComfyUI**:
   * Completely exit and restart ComfyUI.
   * Refresh your web browser or desktop UI.

5. **Verify Installation**:
   Double-click or right-click the canvas and search for the nodes:
   * **`Load Image (with Filename Output)`** (Category: `image`)
   * **`Save Image (Exact Name)`** (Category: `image`)

#### Step 1: Set Up `Load Image (with Filename Output)`
Add the node to your canvas, select your image, and tune the intuitive naming parameters:

| Parameter | Description & Recommendations |
| :--- | :--- |
| **`subfolder`** | **Output Directory** (Optional). E.g., `portraits/animal/`. Leading/trailing slashes are sanitized automatically. |
| **`custom_prefix`** | **Custom Prefix Text** (Optional). Placed ahead of the original filename. |
| **`serial_type`** | **Serialization Mode**. Choose between `5-digit counter (_00001)` (Default), `millisecond timestamp`, or `none`. |
| **`serial_placement`**| **Serial Position**. Place the counter/timestamp within the `suffix region` (Default) or `prefix region`. |
| **`serial_order`** | **Order Priority**. Determines whether the custom text or serial token comes first when both are present. |
| **`custom_suffix`** | **Custom Suffix Text** (Optional). Placed after the original filename. |
| **`delimiter`** | **Separator**. Delimiter between parts: `_ (Underscore)` (Default), `- (Hyphen)`, or `none`. |

**Output Ports**:
* `image` / `mask`: Standard image tensors and alpha masks for downstream pipelines.
* `custom_filename`: **Primary output**. The fully assembled path (subfolders + tokens + stem + serials) to connect directly into the save node.
* `original_filename`: The raw, clean file stem without extensions or extra tokens (ideal for prompts, captions, or logging).

#### Step 2: Set Up `Save Image (Exact Name)`
Replace the official `Save Image` node at the end of your workflow:
1. Connect the processed image to the **`images`** input.
2. Connect **`custom_filename`** from the loader node to the **`filename`** input.
3. **Configure File Format and Duplicate Strategy**:
   * **`format`**: Select `png` (Default, embeds full ComfyUI workflow metadata), `jpeg`, or `webp`.
   * **`on_duplicate`** (Collision Policy):
     * `auto_append_timestamp` (Default / Recommended): Appends a timestamp if the file already exists to prevent data loss.
     * `warn_and_overwrite`: Overwrites the file and pushes a notification toast in the ComfyUI web UI.
     * `stop_and_error`: Aborts the queue with an error when a duplicate is detected.
4. **Pass-through Comparison**: The **`image`** output port allows you to chain comparison nodes (such as `Image Compare` or preview tools) directly after saving.