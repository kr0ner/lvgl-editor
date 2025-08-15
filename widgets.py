"""
LVGL Widget definitions and properties
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Union
from enum import Enum

class WidgetType(Enum):
    """Enumeration of LVGL widget types"""
    LABEL = "label"
    BUTTON = "button"
    IMAGE = "image"
    ARC = "arc"
    BAR = "bar"
    SLIDER = "slider"
    SWITCH = "switch"
    CHECKBOX = "checkbox"
    DROPDOWN = "dropdown"
    ROLLER = "roller"
    TEXTAREA = "textarea"
    SPINBOX = "spinbox"
    METER = "meter"
    LED = "led"
    LINE = "line"
    OBJ = "obj"
    QRCODE = "qrcode"
    CANVAS = "canvas"
    BUTTONMATRIX = "buttonmatrix"
    KEYBOARD = "keyboard"
    SPINNER = "spinner"
    TABVIEW = "tabview"
    TILEVIEW = "tileview"
    ANIMIMG = "animimg"

@dataclass
class LVGLWidget:
    """Base class for LVGL widgets"""
    widget_type: str
    id: str = ""
    x: Union[int, str] = 0
    y: Union[int, str] = 0
    width: Union[int, str] = "SIZE_CONTENT"
    height: Union[int, str] = "SIZE_CONTENT"
    
    # Common style properties
    bg_color: str = "0xFFFFFF"
    bg_opa: str = "COVER"
    border_width: int = 0
    border_color: str = "0x000000"
    border_opa: str = "COVER"
    radius: int = 0
    pad_all: int = 0
    pad_top: int = 0
    pad_bottom: int = 0
    pad_left: int = 0
    pad_right: int = 0
    
    # Alignment
    align: str = "TOP_LEFT"
    
    # Flags
    hidden: bool = False
    clickable: bool = True
    checkable: bool = False
    scrollable: bool = True
    
    # State
    checked: bool = False
    disabled: bool = False
    
    # Layout
    layout_type: str = "NONE"
    
    # Children widgets
    children: List['LVGLWidget'] = field(default_factory=list)
    
    # Actions and triggers
    actions: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert widget to dictionary for YAML export"""
        result = {}
        
        # Add basic properties
        if self.id:
            result['id'] = self.id
        if self.x != 0:
            result['x'] = self.x
        if self.y != 0:
            result['y'] = self.y
        if self.width != "SIZE_CONTENT":
            result['width'] = self.width
        if self.height != "SIZE_CONTENT":
            result['height'] = self.height
            
        # Add styling properties
        if self.bg_color != "0xFFFFFF":
            result['bg_color'] = self.bg_color
        if self.bg_opa != "COVER":
            result['bg_opa'] = self.bg_opa
        if self.border_width > 0:
            result['border_width'] = self.border_width
            result['border_color'] = self.border_color
        if self.border_opa != "COVER":
            result['border_opa'] = self.border_opa
        if self.radius > 0:
            result['radius'] = self.radius
            
        # Add padding
        if self.pad_all > 0:
            result['pad_all'] = self.pad_all
        elif any([self.pad_top, self.pad_bottom, self.pad_left, self.pad_right]):
            if self.pad_top > 0:
                result['pad_top'] = self.pad_top
            if self.pad_bottom > 0:
                result['pad_bottom'] = self.pad_bottom
            if self.pad_left > 0:
                result['pad_left'] = self.pad_left
            if self.pad_right > 0:
                result['pad_right'] = self.pad_right
                
        # Add alignment
        if self.align != "TOP_LEFT":
            result['align'] = self.align
            
        # Add flags
        if self.hidden:
            result['hidden'] = self.hidden
        if not self.clickable:
            result['clickable'] = self.clickable
        if self.checkable:
            result['checkable'] = self.checkable
        if not self.scrollable:
            result['scrollable'] = self.scrollable
            
        # Add state
        if self.checked:
            result['state'] = {'checked': True}
        if self.disabled:
            if 'state' not in result:
                result['state'] = {}
            result['state']['disabled'] = True
            
        # Add layout
        if self.layout_type != "NONE":
            result['layout'] = {'type': self.layout_type}
            
        # Add children
        if self.children:
            result['widgets'] = [child.to_dict() for child in self.children]
            
        # Add actions
        if self.actions:
            result.update(self.actions)
            
        return result

@dataclass
class LabelWidget(LVGLWidget):
    """Label widget for displaying text"""
    text: str = "Label"
    text_color: str = "0x000000"
    text_font: str = "montserrat_14"
    text_align: str = "LEFT"
    long_mode: str = "WRAP"
    recolor: bool = False
    
    def __post_init__(self):
        self.widget_type = "label"
        
    def to_dict(self) -> Dict[str, Any]:
        result = super().to_dict()
        result['text'] = self.text
        if self.text_color != "0x000000":
            result['text_color'] = self.text_color
        if self.text_font != "montserrat_14":
            result['text_font'] = self.text_font
        if self.text_align != "LEFT":
            result['text_align'] = self.text_align
        if self.long_mode != "WRAP":
            result['long_mode'] = self.long_mode
        if self.recolor:
            result['recolor'] = self.recolor
        return result

@dataclass
class ButtonWidget(LVGLWidget):
    """Button widget"""
    
    def __post_init__(self):
        self.widget_type = "button"
        self.clickable = True

@dataclass
class ImageWidget(LVGLWidget):
    """Image widget for displaying images"""
    src: str = ""
    angle: float = 0.0
    zoom: float = 1.0
    antialias: bool = False
    pivot_x: Optional[int] = None
    pivot_y: Optional[int] = None
    offset_x: int = 0
    offset_y: int = 0
    
    def __post_init__(self):
        self.widget_type = "image"
        
    def to_dict(self) -> Dict[str, Any]:
        result = super().to_dict()
        if self.src:
            result['src'] = self.src
        if self.angle != 0.0:
            result['angle'] = self.angle
        if self.zoom != 1.0:
            result['zoom'] = self.zoom
        if self.antialias:
            result['antialias'] = self.antialias
        if self.pivot_x is not None:
            result['pivot_x'] = self.pivot_x
        if self.pivot_y is not None:
            result['pivot_y'] = self.pivot_y
        if self.offset_x != 0:
            result['offset_x'] = self.offset_x
        if self.offset_y != 0:
            result['offset_y'] = self.offset_y
        return result

@dataclass
class ArcWidget(LVGLWidget):
    """Arc widget for circular progress/input"""
    value: int = 0
    min_value: int = 0
    max_value: int = 100
    start_angle: int = 135
    end_angle: int = 45
    adjustable: bool = False
    arc_color: str = "0x808080"
    arc_width: int = 10
    arc_rounded: bool = True
    
    def __post_init__(self):
        self.widget_type = "arc"
        
    def to_dict(self) -> Dict[str, Any]:
        result = super().to_dict()
        result['value'] = self.value
        if self.min_value != 0:
            result['min_value'] = self.min_value
        if self.max_value != 100:
            result['max_value'] = self.max_value
        if self.start_angle != 135:
            result['start_angle'] = self.start_angle
        if self.end_angle != 45:
            result['end_angle'] = self.end_angle
        if self.adjustable:
            result['adjustable'] = self.adjustable
        if self.arc_color != "0x808080":
            result['arc_color'] = self.arc_color
        if self.arc_width != 10:
            result['arc_width'] = self.arc_width
        if not self.arc_rounded:
            result['arc_rounded'] = self.arc_rounded
        return result

@dataclass
class BarWidget(LVGLWidget):
    """Bar widget for progress display"""
    value: int = 0
    min_value: int = 0
    max_value: int = 100
    animated: bool = True
    mode: str = "NORMAL"
    
    def __post_init__(self):
        self.widget_type = "bar"
        
    def to_dict(self) -> Dict[str, Any]:
        result = super().to_dict()
        result['value'] = self.value
        if self.min_value != 0:
            result['min_value'] = self.min_value
        if self.max_value != 100:
            result['max_value'] = self.max_value
        if not self.animated:
            result['animated'] = self.animated
        if self.mode != "NORMAL":
            result['mode'] = self.mode
        return result

@dataclass
class SliderWidget(LVGLWidget):
    """Slider widget for value input"""
    value: int = 0
    min_value: int = 0
    max_value: int = 100
    animated: bool = True
    
    def __post_init__(self):
        self.widget_type = "slider"
        
    def to_dict(self) -> Dict[str, Any]:
        result = super().to_dict()
        result['value'] = self.value
        if self.min_value != 0:
            result['min_value'] = self.min_value
        if self.max_value != 100:
            result['max_value'] = self.max_value
        if not self.animated:
            result['animated'] = self.animated
        return result

@dataclass
class SwitchWidget(LVGLWidget):
    """Switch widget for boolean input"""
    
    def __post_init__(self):
        self.widget_type = "switch"
        self.checkable = True

@dataclass
class CheckboxWidget(LVGLWidget):
    """Checkbox widget"""
    text: str = "Checkbox"
    
    def __post_init__(self):
        self.widget_type = "checkbox"
        self.checkable = True
        
    def to_dict(self) -> Dict[str, Any]:
        result = super().to_dict()
        if self.text:
            result['text'] = self.text
        return result

@dataclass
class DropdownWidget(LVGLWidget):
    """Dropdown widget for selection"""
    options: List[str] = field(default_factory=lambda: ["Option 1", "Option 2", "Option 3"])
    selected_index: int = 0
    dir: str = "BOTTOM"
    
    def __post_init__(self):
        self.widget_type = "dropdown"
        
    def to_dict(self) -> Dict[str, Any]:
        result = super().to_dict()
        result['options'] = self.options
        if self.selected_index > 0:
            result['selected_index'] = self.selected_index
        if self.dir != "BOTTOM":
            result['dir'] = self.dir
        return result

@dataclass
class TextareaWidget(LVGLWidget):
    """Textarea widget for text input"""
    text: str = ""
    placeholder_text: str = "Enter text..."
    one_line: bool = False
    password_mode: bool = False
    max_length: Optional[int] = None
    accepted_chars: str = ""
    
    def __post_init__(self):
        self.widget_type = "textarea"
        
    def to_dict(self) -> Dict[str, Any]:
        result = super().to_dict()
        if self.text:
            result['text'] = self.text
        if self.placeholder_text:
            result['placeholder_text'] = self.placeholder_text
        if self.one_line:
            result['one_line'] = self.one_line
        if self.password_mode:
            result['password_mode'] = self.password_mode
        if self.max_length:
            result['max_length'] = self.max_length
        if self.accepted_chars:
            result['accepted_chars'] = self.accepted_chars
        return result

@dataclass
class SpinboxWidget(LVGLWidget):
    """Spinbox widget for numeric input"""
    value: float = 0.0
    range_from: float = 0.0
    range_to: float = 100.0
    step: float = 1.0
    digits: int = 4
    decimal_places: int = 0
    rollover: bool = False
    
    def __post_init__(self):
        self.widget_type = "spinbox"
        
    def to_dict(self) -> Dict[str, Any]:
        result = super().to_dict()
        result['value'] = self.value
        if self.range_from != 0.0:
            result['range_from'] = self.range_from
        if self.range_to != 100.0:
            result['range_to'] = self.range_to
        if self.step != 1.0:
            result['step'] = self.step
        if self.digits != 4:
            result['digits'] = self.digits
        if self.decimal_places > 0:
            result['decimal_places'] = self.decimal_places
        if self.rollover:
            result['rollover'] = self.rollover
        return result

@dataclass
class LEDWidget(LVGLWidget):
    """LED widget for status indication"""
    color: str = "0xFF0000"
    brightness: str = "100%"
    
    def __post_init__(self):
        self.widget_type = "led"
        
    def to_dict(self) -> Dict[str, Any]:
        result = super().to_dict()
        result['color'] = self.color
        if self.brightness != "100%":
            result['brightness'] = self.brightness
        return result

@dataclass
class QRCodeWidget(LVGLWidget):
    """QR Code widget"""
    text: str = "https://esphome.io"
    size: int = 100
    light_color: str = "0xFFFFFF"
    dark_color: str = "0x000000"
    
    def __post_init__(self):
        self.widget_type = "qrcode"
        
    def to_dict(self) -> Dict[str, Any]:
        result = super().to_dict()
        result['text'] = self.text
        result['size'] = self.size
        if self.light_color != "0xFFFFFF":
            result['light_color'] = self.light_color
        if self.dark_color != "0x000000":
            result['dark_color'] = self.dark_color
        return result

# Widget factory function
def create_widget(widget_type: str, **kwargs) -> LVGLWidget:
    """Factory function to create widgets"""
    widget_classes = {
        'label': LabelWidget,
        'button': ButtonWidget,
        'image': ImageWidget,
        'arc': ArcWidget,
        'bar': BarWidget,
        'slider': SliderWidget,
        'switch': SwitchWidget,
        'checkbox': CheckboxWidget,
        'dropdown': DropdownWidget,
        'textarea': TextareaWidget,
        'spinbox': SpinboxWidget,
        'led': LEDWidget,
        'qrcode': QRCodeWidget,
    }
    
    if widget_type in widget_classes:
        return widget_classes[widget_type](widget_type=widget_type, **kwargs)
    else:
        # Default to base widget
        return LVGLWidget(widget_type=widget_type, **kwargs)

# Available widgets configuration
LVGL_WIDGETS = {
    'Basic': {
        'label': {
            'name': 'Label',
            'icon': '🏷️',
            'description': 'Display text',
            'default_size': (100, 30)
        },
        'button': {
            'name': 'Button',
            'icon': '🔘',
            'description': 'Clickable button',
            'default_size': (80, 40)
        },
        'image': {
            'name': 'Image',
            'icon': '🖼️',
            'description': 'Display images',
            'default_size': (100, 100)
        },
        'obj': {
            'name': 'Object',
            'icon': '⬜',
            'description': 'Base container object',
            'default_size': (100, 100)
        }
    },
    'Input': {
        'slider': {
            'name': 'Slider',
            'icon': '🎚️',
            'description': 'Value slider',
            'default_size': (150, 20)
        },
        'arc': {
            'name': 'Arc',
            'icon': '🌙',
            'description': 'Circular progress/input',
            'default_size': (100, 100)
        },
        'switch': {
            'name': 'Switch',
            'icon': '🔄',
            'description': 'On/off switch',
            'default_size': (60, 30)
        },
        'checkbox': {
            'name': 'Checkbox',
            'icon': '☑️',
            'description': 'Checkbox with label',
            'default_size': (100, 30)
        },
        'dropdown': {
            'name': 'Dropdown',
            'icon': '📋',
            'description': 'Selection dropdown',
            'default_size': (120, 30)
        },
        'textarea': {
            'name': 'Text Area',
            'icon': '📝',
            'description': 'Text input area',
            'default_size': (150, 80)
        },
        'spinbox': {
            'name': 'Spinbox',
            'icon': '🔢',
            'description': 'Numeric input',
            'default_size': (100, 30)
        }
    },
    'Display': {
        'bar': {
            'name': 'Bar',
            'icon': '📊',
            'description': 'Progress bar',
            'default_size': (150, 20)
        },
        'led': {
            'name': 'LED',
            'icon': '💡',
            'description': 'Status LED',
            'default_size': (30, 30)
        },
        'qrcode': {
            'name': 'QR Code',
            'icon': '⬛',
            'description': 'QR code display',
            'default_size': (100, 100)
        },
        'meter': {
            'name': 'Meter',
            'icon': '⏲️',
            'description': 'Gauge meter',
            'default_size': (120, 120)
        }
    },
    'Container': {
        'tabview': {
            'name': 'Tab View',
            'icon': '📑',
            'description': 'Tabbed container',
            'default_size': (200, 150)
        },
        'tileview': {
            'name': 'Tile View',
            'icon': '🗂️',
            'description': 'Swipeable tiles',
            'default_size': (200, 150)
        }
    },
    'Special': {
        'keyboard': {
            'name': 'Keyboard',
            'icon': '⌨️',
            'description': 'On-screen keyboard',
            'default_size': (240, 120)
        },
        'buttonmatrix': {
            'name': 'Button Matrix',
            'icon': '🔳',
            'description': 'Matrix of buttons',
            'default_size': (180, 120)
        },
        'canvas': {
            'name': 'Canvas',
            'icon': '🎨',
            'description': 'Drawing canvas',
            'default_size': (200, 150)
        },
        'line': {
            'name': 'Line',
            'icon': '📏',
            'description': 'Line drawing',
            'default_size': (100, 2)
        },
        'animimg': {
            'name': 'Animated Image',
            'icon': '🎬',
            'description': 'Animated image frames',
            'default_size': (100, 100)
        },
        'spinner': {
            'name': 'Spinner',
            'icon': '🌀',
            'description': 'Loading spinner',
            'default_size': (50, 50)
        }
    }
}

# Alignment options
ALIGN_OPTIONS = [
    "TOP_LEFT", "TOP_MID", "TOP_RIGHT",
    "BOTTOM_LEFT", "BOTTOM_MID", "BOTTOM_RIGHT",
    "LEFT_MID", "CENTER", "RIGHT_MID",
    "OUT_TOP_LEFT", "OUT_TOP_MID", "OUT_TOP_RIGHT",
    "OUT_BOTTOM_LEFT", "OUT_BOTTOM_MID", "OUT_BOTTOM_RIGHT",
    "OUT_LEFT_TOP", "OUT_LEFT_MID", "OUT_LEFT_BOTTOM",
    "OUT_RIGHT_TOP", "OUT_RIGHT_MID", "OUT_RIGHT_BOTTOM"
]

# Color definitions
COLORS = {
    "White": "0xFFFFFF",
    "Black": "0x000000",
    "Red": "0xFF0000",
    "Green": "0x00FF00",
    "Blue": "0x0000FF",
    "Yellow": "0xFFFF00",
    "Cyan": "0x00FFFF",
    "Magenta": "0xFF00FF",
    "Gray": "0x808080",
    "Light Gray": "0xC0C0C0",
    "Dark Gray": "0x404040"
}

# Font options
FONT_OPTIONS = [
    "montserrat_8", "montserrat_10", "montserrat_12", "montserrat_14",
    "montserrat_16", "montserrat_18", "montserrat_20", "montserrat_22",
    "montserrat_24", "montserrat_26", "montserrat_28", "montserrat_30",
    "montserrat_32", "montserrat_34", "montserrat_36", "montserrat_38",
    "montserrat_40", "montserrat_42", "montserrat_44", "montserrat_46",
    "montserrat_48", "unscii_8", "unscii_16", "simsun_16_cjk",
    "dejavu_16_persian_hebrew"
]
