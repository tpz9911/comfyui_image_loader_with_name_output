from .file_loader_node import CustomImageLoaderWithName, CustomSaveImageExactName

NODE_CLASS_MAPPINGS = {
    "PZ_CustomImageLoaderWithName": CustomImageLoaderWithName,
    "PZ_CustomSaveImageExactName": CustomSaveImageExactName
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PZ_CustomImageLoaderWithName": "Load Image (with Filename Output)",
    "PZ_CustomSaveImageExactName": "Save Image (Exact Name)"
}

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']