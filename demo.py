#!/usr/bin/env python3
"""
Demo script for LVGL Layout Editor
Creates a sample project and exports YAML
"""

import json
from yaml_generator import YAMLGenerator

def create_demo_project():
    """Create a sample LVGL project"""
    
    # Display configuration
    display_config = {
        'width': 320,
        'height': 240,
        'color_depth': 16,
        'buffer_size': '100%'
    }
    
    # Page configuration
    pages_data = {
        'main_page': {
            'id': 'main_page',
            'name': 'Main Page',
            'layout': 'NONE',
            'background_color': '#000000',
            'scrollable': False,
            'is_default': True
        },
        'settings_page': {
            'id': 'settings_page', 
            'name': 'Settings',
            'layout': 'FLEX',
            'background_color': '#1a1a1a',
            'scrollable': True,
            'is_default': False
        }
    }
    
    # Widget data
    widgets_data = {
        'main_page': [
            {
                'widget_type': 'label',
                'id': 'title_label',
                'text': 'LVGL Demo',
                'x': 10,
                'y': 10,
                'width': 300,
                'height': 30,
                'text_color': '#FFFFFF',
                'text_font': 'montserrat_18',
                'text_align': 'CENTER'
            },
            {
                'widget_type': 'button',
                'id': 'start_btn',
                'x': 50,
                'y': 60,
                'width': 100,
                'height': 40,
                'text': 'Start',
                'actions': {
                    'on_click': {
                        'then': [
                            {'logger.log': 'Start button clicked'},
                            {'lvgl.page.show': 'settings_page'}
                        ]
                    }
                }
            },
            {
                'widget_type': 'button',
                'id': 'settings_btn',
                'x': 170,
                'y': 60,
                'width': 100,
                'height': 40,
                'text': 'Settings',
                'actions': {
                    'on_click': {
                        'then': [
                            {'lvgl.page.show': 'settings_page'}
                        ]
                    }
                }
            },
            {
                'widget_type': 'slider',
                'id': 'volume_slider',
                'x': 50,
                'y': 120,
                'width': 220,
                'height': 20,
                'min_value': 0,
                'max_value': 100,
                'value': 50,
                'actions': {
                    'on_value_changed': {
                        'then': [
                            {'logger.log': 'Volume changed to ${volume_slider.value}'}
                        ]
                    }
                }
            },
            {
                'widget_type': 'label',
                'id': 'volume_label',
                'text': 'Volume: 50%',
                'x': 50,
                'y': 100,
                'width': 220,
                'height': 20,
                'text_color': '#CCCCCC'
            }
        ],
        'settings_page': [
            {
                'widget_type': 'label',
                'id': 'settings_title',
                'text': 'Settings',
                'x': 10,
                'y': 10,
                'width': 300,
                'height': 30,
                'text_color': '#FFFFFF',
                'text_font': 'montserrat_18',
                'text_align': 'CENTER'
            },
            {
                'widget_type': 'switch',
                'id': 'wifi_switch',
                'x': 50,
                'y': 60,
                'width': 60,
                'height': 30
            },
            {
                'widget_type': 'label',
                'id': 'wifi_label',
                'text': 'Wi-Fi',
                'x': 120,
                'y': 65,
                'width': 100,
                'height': 20,
                'text_color': '#FFFFFF'
            },
            {
                'widget_type': 'switch',
                'id': 'bluetooth_switch',
                'x': 50,
                'y': 100,
                'width': 60,
                'height': 30
            },
            {
                'widget_type': 'label',
                'id': 'bluetooth_label',
                'text': 'Bluetooth',
                'x': 120,
                'y': 105,
                'width': 100,
                'height': 20,
                'text_color': '#FFFFFF'
            },
            {
                'widget_type': 'button',
                'id': 'back_btn',
                'x': 50,
                'y': 180,
                'width': 80,
                'height': 30,
                'text': 'Back',
                'actions': {
                    'on_click': {
                        'then': [
                            {'lvgl.page.show': 'main_page'}
                        ]
                    }
                }
            }
        ]
    }
    
    return display_config, pages_data, widgets_data

def main():
    """Generate demo YAML configuration"""
    print("LVGL Layout Editor - Demo")
    print("=" * 40)
    
    # Create demo project
    display_config, pages_data, widgets_data = create_demo_project()
    
    # Generate YAML
    generator = YAMLGenerator()
    yaml_content = generator.generate_complete_config(display_config, pages_data, widgets_data)
    
    # Save to file
    output_file = 'demo_output.yaml'
    with open(output_file, 'w') as f:
        f.write(yaml_content)
    
    print(f"Demo YAML configuration saved to: {output_file}")
    print(f"Display: {display_config['width']}x{display_config['height']}")
    print(f"Pages: {len(pages_data)}")
    print(f"Total widgets: {sum(len(w) for w in widgets_data.values())}")
    
    # Generate project summary
    summary = generator.export_project_summary(display_config, pages_data, widgets_data)
    summary_file = 'demo_summary.md'
    with open(summary_file, 'w') as f:
        f.write(summary)
    
    print(f"Project summary saved to: {summary_file}")
    
    # Save project file for the editor
    project_data = {
        'version': '1.0',
        'display_config': display_config,
        'pages': pages_data,
        'widgets': widgets_data
    }
    
    project_file = 'demo_project.json'
    with open(project_file, 'w') as f:
        json.dump(project_data, f, indent=2)
    
    print(f"Project file saved to: {project_file}")
    print("\nYou can now:")
    print(f"1. Open {project_file} in the LVGL Layout Editor")
    print(f"2. Use {output_file} in your ESPHome configuration") 
    print(f"3. Review {summary_file} for project details")

if __name__ == '__main__':
    main()
