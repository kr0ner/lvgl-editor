# LVGL Layout Editor

A comprehensive graphical editor for creating LVGL layouts on PC with ESPHome-compatible YAML output.

## Features

### Core Functionality
- **Visual Layout Editor**: Drag-and-drop interface for placing and arranging LVGL widgets
- **ESPHome Compatibility**: Generate ESPHome-compatible YAML configurations
- **Multi-Page Support**: Create and manage multiple pages with navigation
- **Widget Library**: Comprehensive library of LVGL widgets with search and categorization
- **Property Editing**: Visual property editor for widget styling and behavior
- **Project Management**: Save/load projects in JSON format

### Widgets Supported
- **Basic Widgets**: Label, Button, Image, Line
- **Input Widgets**: Button, Switch, Checkbox, Slider, Roller, Dropdown, Textarea, Keyboard
- **Display Widgets**: Label, Image, LED, Bar, Arc, Meter, Chart
- **Container Widgets**: Panel, Tabview, Window, Message Box

### Advanced Features
- **Actions & Triggers**: Configure widget interactions and automations
- **Style Management**: Comprehensive styling options (colors, fonts, padding, borders)
- **Layout Systems**: Support for Flex and Grid layouts
- **Image Support**: Import and manage images for use in layouts
- **Color Management**: Color picker and theme support
- **Export Options**: YAML export, project summary generation
- **Interactive Preview**: Navigate between pages in the editor

## Installation

### Prerequisites
- Python 3.12 or newer
- Tkinter (usually included with Python)

### Setup
1. Clone or download the project
2. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install pyyaml pillow
   ```

## Usage

### Starting the Editor
```bash
python main.py
```

### Basic Workflow
1. **Create Project**: Start with a new project or load an existing one
2. **Configure Display**: Set display dimensions and properties
3. **Add Widgets**: Drag widgets from the library to the canvas
4. **Edit Properties**: Use the property panel to customize widget appearance and behavior
5. **Add Pages**: Create multiple pages and set up navigation
6. **Configure Actions**: Set up button clicks and other interactions
7. **Export**: Generate ESPHome YAML configuration

### Demo
Run the demo script to see example output:
```bash
python demo.py
```

This generates:
- `demo_output.yaml` - ESPHome configuration
- `demo_project.json` - Project file for the editor
- `demo_summary.md` - Human-readable project summary

## Project Structure

```
├── main.py              # Main application entry point
├── widgets.py           # Widget classes and factory
├── canvas_editor.py     # Visual canvas editor
├── property_panel.py    # Widget property editor
├── widget_library.py    # Widget selection palette
├── yaml_generator.py    # ESPHome YAML generation
├── page_manager.py      # Multi-page management
├── demo.py             # Demo script and examples
└── README.md           # This file
```

## File Formats

### Project Files (.json)
```json
{
  "version": "1.0",
  "display_config": {
    "width": 320,
    "height": 240,
    "color_depth": 16
  },
  "pages": {
    "main_page": {
      "id": "main_page",
      "name": "Main Page",
      "layout": "NONE"
    }
  },
  "widgets": {
    "main_page": [
      {
        "widget_type": "label",
        "id": "my_label",
        "text": "Hello World",
        "x": 10,
        "y": 10
      }
    ]
  }
}
```

### ESPHome Output
The editor generates complete ESPHome configurations including:
- Display driver setup (customizable for your hardware)
- LVGL component configuration
- Widget definitions with styling
- Page navigation setup
- Automation triggers for interactions

## Widget Configuration

### Common Properties
- **Position**: x, y coordinates
- **Size**: width, height (supports SIZE_CONTENT)
- **Styling**: colors, fonts, borders, padding
- **Alignment**: text and widget alignment options

### Widget-Specific Properties
Each widget type has specific properties:
- **Label**: text content, font, color, alignment
- **Button**: text, toggle state, checkable
- **Slider**: min/max values, current value
- **Image**: source file path
- **Switch**: state (on/off)

### Actions and Triggers
Configure widget interactions:
```yaml
button:
  id: my_button
  text: "Click Me"
  on_click:
    then:
      - logger.log: "Button was clicked"
      - lvgl.page.show: settings_page
```

## ESPHome Integration

### Basic ESPHome Configuration
```yaml
# Add to your ESPHome configuration
esphome:
  name: your-device
  platform: ESP32

# Include the generated LVGL configuration
<<: !include lvgl_config.yaml
```

### Hardware Setup
Customize the display driver section for your specific hardware:
```yaml
display:
  - platform: ili9xxx  # Change for your display
    model: ili9341      # Change for your model
    cs_pin: GPIO5       # Customize pins
    dc_pin: GPIO2
    reset_pin: GPIO4
    # ... other hardware-specific settings
```

## Development

### Architecture
The editor uses a modular architecture:
- **MVC Pattern**: Separation of data models, views, and controllers
- **Event-Driven**: Loose coupling through callbacks and events
- **Plugin Architecture**: Easy to extend with new widgets

### Adding New Widgets
1. Add widget class to `widgets.py`
2. Update widget metadata in `LVGL_WIDGETS`
3. Add property controls to `property_panel.py`
4. Update YAML generation in `yaml_generator.py`

### Contributing
- Follow PEP 8 style guidelines
- Add docstrings to all functions and classes
- Include unit tests for new features
- Update documentation for changes

## Troubleshooting

### Common Issues
1. **Import Errors**: Ensure all dependencies are installed
2. **Display Issues**: Check Tkinter installation
3. **YAML Errors**: Validate generated YAML with ESPHome

### Known Limitations
- Hardware-specific display configuration needs manual customization
- Some advanced LVGL features not yet supported
- Limited undo/redo functionality

## License

This project is open source. Please check the license file for details.

## Resources

- [ESPHome LVGL Documentation](https://esphome.io/components/display/lvgl.html)
- [LVGL Documentation](https://docs.lvgl.io/)
- [ESPHome Documentation](https://esphome.io/)

## Support

For issues, questions, or contributions, please refer to the project repository or documentation.
