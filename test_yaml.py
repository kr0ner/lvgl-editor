#!/usr/bin/env python3
"""
Quick test script to verify the yaml export functionality
"""

import json
from yaml_generator import YAMLGenerator

def test_yaml_export():
    """Test the YAML export with minimal data"""
    
    print("Testing YAML export...")
    
    # Minimal test data
    display_config = {
        'width': 320,
        'height': 240,
        'color_depth': 16
    }
    
    pages_data = {
        'main_page': {
            'id': 'main_page',
            'name': 'Main Page'
        }
    }
    
    widgets_data = {
        'main_page': [
            {
                'widget_type': 'label',
                'id': 'test_label',
                'text': 'Hello LVGL',
                'x': 10,
                'y': 10
            }
        ]
    }
    
    try:
        generator = YAMLGenerator()
        yaml_content = generator.generate_yaml(display_config, pages_data, widgets_data)
        
        print("✓ YAML generation successful!")
        print(f"Generated {len(yaml_content)} characters of YAML")
        
        # Save for inspection
        with open('test_output.yaml', 'w') as f:
            f.write(yaml_content)
        print("✓ Test YAML saved to test_output.yaml")
        
    except Exception as e:
        print(f"✗ YAML generation failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_yaml_export()
