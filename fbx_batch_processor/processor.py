"""Core FBX processing functionality."""
import os
import json
import logging
from typing import Optional

import bpy
from mathutils import Matrix

logger = logging.getLogger(__name__)

class FBXProcessor:
    """Process FBX files with texture assignment and transform normalization."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the processor with optional config.
        
        Args:
            config_path: Path to config file with texture patterns
        """
        self.texture_patterns = {
            'diffuse': '_BC',
            'normal': '_N',
            'opacity': '_O',
        }
        self.export_settings = {
            'embed_textures': False,
            'bake_space_transform': True,
            'use_selection': False,
            'apply_scale_options': 'FBX_SCALE_ALL',
        }
        
        if config_path and os.path.exists(config_path):
            self._load_config(config_path)
    
    def _load_config(self, config_path: str) -> None:
        """Load configuration from JSON file.
        
        Args:
            config_path: Path to config file
        """
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                if 'texture_patterns' in config:
                    self.texture_patterns.update(config['texture_patterns'])
                if 'export_settings' in config:
                    self.export_settings.update(config['export_settings'])
        except Exception as e:
            logger.warning(f"Failed to load config: {e}")
    
    def process_fbx(self, fbx_path: str, output_dir: str) -> bool:
        """Process a single FBX file.
        
        Args:
            fbx_path: Path to input FBX file
            output_dir: Directory to save processed files
            
        Returns:
            bool: True if processing was successful
        """
        try:
            # Clear existing scene
            bpy.ops.wm.read_factory_settings(use_empty=True)
            
            # Import FBX
            self._import_fbx(fbx_path)
            
            # Process materials and textures
            self._process_materials(fbx_path)
            
            # Reset transforms
            self._reset_transforms()
            
            # Export FBX
            output_path = os.path.join(output_dir, os.path.basename(fbx_path))
            self._export_fbx(output_path)
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing {fbx_path}: {e}")
            return False
    
    def _import_fbx(self, filepath: str) -> None:
        """Import FBX file into Blender."""
        bpy.ops.import_scene.fbx(filepath=filepath)
    
    def _export_fbx(self, filepath: str) -> None:
        """Export FBX file from Blender."""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        bpy.ops.export_scene.fbx(
            filepath=filepath,
            use_selection=self.export_settings['use_selection'],
            apply_scale_options=self.export_settings['apply_scale_options'],
            path_mode='COPY',
            embed_textures=self.export_settings['embed_textures'],
            bake_space_transform=self.export_settings['bake_space_transform']
        )
    
    def _process_materials(self, fbx_path: str) -> None:
        """Process materials and assign textures based on naming patterns."""
        base_name = os.path.splitext(os.path.basename(fbx_path))[0]
        texture_dir = os.path.dirname(fbx_path)
        
        for obj in bpy.data.objects:
            if not obj.type == 'MESH' or not obj.data.materials:
                continue
                
            for mat in obj.data.materials:
                if not mat:
                    continue
                    
                self._assign_textures(mat, base_name, texture_dir)
    
    def _assign_textures(self, material, base_name: str, texture_dir: str) -> None:
        """Assign textures to material based on naming patterns.
        
        Args:
            material: The Blender material to assign textures to
            base_name: Base name of the FBX file (without extension)
            texture_dir: Directory containing the texture files
        """
        material_name = material.name.replace('.', '_')
        logger.debug(f"Processing material: {material_name}")
        
        # First collect all texture files in the directory
        try:
            texture_files = [f for f in os.listdir(texture_dir) 
                           if f.lower().endswith(('.png', '.jpg', '.jpeg', '.tga', '.tif', '.tiff'))]
            logger.debug(f"Found {len(texture_files)} texture files in {texture_dir}")
        except Exception as e:
            logger.warning(f"Could not list texture directory: {e}")
            return
        
        # Process each texture type separately
        for tex_type, suffix in self.texture_patterns.items():
            # Try different naming patterns in order of specificity
            patterns = []
            patterns.extend([
                f"T_{base_name}_{material_name}{suffix}",  # T_ModelName_MaterialName_Suffix
                f"T_{base_name}{suffix}",                  # T_ModelName_Suffix
                f"{material_name}{suffix}",                # MaterialName_Suffix
                f"{base_name}{suffix}"                     # ModelName_Suffix
            ])
            
            texture_path = None
            
            # Try each pattern until we find a match (case-insensitive)
            for pattern in patterns:
                pattern_lower = pattern.lower()
                for tex_file in texture_files:
                    # Get filename without extension and convert to lowercase for comparison
                    tex_name = os.path.splitext(tex_file)[0]
                    # Check for case-insensitive match with pattern
                    if tex_name.lower() == pattern_lower:
                        texture_path = os.path.join(texture_dir, tex_file)
                        logger.debug(f"Matched {tex_type} texture: {tex_file} with pattern '{pattern}'")
                        break
                if texture_path:
                    break
            
            if texture_path:
                self._assign_texture(material, texture_path, tex_type)
            else:
                logger.debug(f"No {tex_type} texture found for material {material_name} "
                           f"(tried patterns: {', '.join(patterns)})")
    
    @staticmethod
    def _find_texture(directory: str, pattern: str) -> Optional[str]:
        """Find texture file matching pattern in directory."""
        if not os.path.exists(directory):
            return None
            
        # Get all files in the directory
        try:
            files = os.listdir(directory)
        except Exception as e:
            logger.warning(f"Could not list directory {directory}: {e}")
            return None
        
        # Try exact match first (with or without extension)
        for filename in files:
            if filename == pattern or os.path.splitext(filename)[0] == pattern:
                path = os.path.join(directory, filename)
                if os.path.isfile(path):
                    return path
        
        # Try pattern with different extensions
        for ext in ['.png', '.jpg', '.jpeg', '.tga', '.tif', '.tiff']:
            # Try exact pattern match with extension
            target = f"{pattern}{ext}"
            if target in files:
                return os.path.join(directory, target)
                
        # Try case-insensitive match as last resort
        pattern_lower = pattern.lower()
        for filename in files:
            name, ext = os.path.splitext(filename)
            if ext.lower() in ['.png', '.jpg', '.jpeg', '.tga', '.tif', '.tiff']:
                if name.lower() == pattern_lower:
                    return os.path.join(directory, filename)
                    
        return None
    
    def _assign_texture(self, material, texture_path: str, tex_type: str) -> None:
        """Assign texture to material node.
        
        Args:
            material: Blender material to assign texture to
            texture_path: Path to the texture file
            tex_type: Type of texture ('diffuse', 'normal', 'opacity', etc.)
        """
        if not os.path.exists(texture_path):
            logger.warning(f"Texture file not found: {texture_path}")
            return
            
        # Enable nodes if not already
        material.use_nodes = True
        nodes = material.node_tree.nodes
        links = material.node_tree.links
        
        # Get or create Principled BSDF
        bsdf = nodes.get('Principled BSDF')
        if not bsdf:
            bsdf = nodes.new('ShaderNodeBsdfPrincipled')
            output = nodes.get('Material Output')
            if not output:
                output = nodes.new('ShaderNodeOutputMaterial')
            links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
        
        # Create texture node
        tex_node = nodes.new('ShaderNodeTexImage')
        try:
            # Try to load the texture
            tex_node.image = bpy.data.images.load(texture_path, check_existing=True)
            
            # Set color space based on texture type
            if tex_type == 'diffuse':
                tex_node.image.colorspace_settings.name = 'sRGB'
            else:
                tex_node.image.colorspace_settings.name = 'Non-Color'
            
            # Connect to appropriate input based on texture type
            if tex_type == 'diffuse':
                # For diffuse/albedo/color maps
                links.new(tex_node.outputs['Color'], bsdf.inputs['Base Color'])
                
            elif tex_type == 'normal':
                # For normal maps
                normal_map = nodes.new('ShaderNodeNormalMap')
                links.new(tex_node.outputs['Color'], normal_map.inputs['Color'])
                links.new(normal_map.outputs['Normal'], bsdf.inputs['Normal'])
                
            elif tex_type == 'opacity':
                # For opacity/alpha maps
                links.new(tex_node.outputs['Color'], bsdf.inputs['Alpha'])
                material.blend_method = 'BLEND'  # Enable transparency
                if hasattr(material, 'shadow_method'):
                    material.shadow_method = 'CLIP'  # For proper shadows with transparency (Blender 2.8+)
                material.show_transparent_back = False  # Don't show backfaces
                
            elif tex_type == 'roughness':
                # For roughness maps
                links.new(tex_node.outputs['Color'], bsdf.inputs['Roughness'])
                
            elif tex_type == 'metallic':
                # For metallic maps
                links.new(tex_node.outputs['Color'], bsdf.inputs['Metallic'])
                
            elif tex_type == 'ao' or tex_type == 'ambient_occlusion':
                # For ambient occlusion maps
                if 'Ambient Occlusion' in bsdf.inputs:
                    links.new(tex_node.outputs['Color'], bsdf.inputs['Ambient Occlusion'])
                    
            logger.info(f"Assigned {tex_type} texture: {os.path.basename(texture_path)}")
            
        except Exception as e:
            logger.error(f"Failed to load texture {texture_path}: {str(e)}")
            nodes.remove(tex_node)  # Clean up the node if texture loading fails
    
    def _reset_transforms(self) -> None:
        """Reset transforms of all mesh objects."""
        for obj in bpy.data.objects:
            if obj.type != 'MESH':
                continue
                
            # Apply all transforms
            matrix = obj.matrix_world.copy()
            obj.data.transform(matrix)
            
            # Reset transform
            obj.matrix_world = Matrix()
            
            # Apply scale and rotation
            bpy.context.view_layer.objects.active = obj
            bpy.ops.object.transform_apply(
                location=False,
                rotation=True,
                scale=True
            )
