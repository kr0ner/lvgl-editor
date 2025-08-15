"""
Canvas Editor for LVGL widgets
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, List, Any, Optional, Tuple, Callable
import copy
from widgets import LVGLWidget, create_widget, LVGL_WIDGETS

class CanvasEditor:
    """Canvas editor for visual widget editing"""
    
    def __init__(self, parent, display_config: Dict, selection_callback: Callable, change_callback: Callable):
        self.parent = parent
        self.display_config = display_config
        self.selection_callback = selection_callback
        self.change_callback = change_callback
        
        # State
        self.widgets = {}  # page_id -> List[LVGLWidget]
        self.current_page = "main_page"
        self.selected_widgets = []
        self.placing_widget = None
        self.zoom_level = 1.0
        self.grid_visible = True
        self.snap_to_grid = True
        self.grid_size = 10
        
        # Clipboard
        self.clipboard = []
        
        # Drag state
        self.drag_start = None
        self.drag_widgets = []
        
        # Create UI
        self.create_ui()
        
        # Initialize with empty page
        self.widgets[self.current_page] = []
        
    def create_ui(self):
        """Create the canvas UI"""
        # Main frame
        main_frame = ttk.Frame(self.parent)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Toolbar
        toolbar = ttk.Frame(main_frame)
        toolbar.pack(fill=tk.X, pady=(0, 5))
        
        # Zoom controls
        ttk.Label(toolbar, text="Zoom:").pack(side=tk.LEFT, padx=(0, 5))
        
        zoom_frame = ttk.Frame(toolbar)
        zoom_frame.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(zoom_frame, text="-", width=3, command=self.zoom_out).pack(side=tk.LEFT)
        self.zoom_label = ttk.Label(zoom_frame, text="100%", width=6)
        self.zoom_label.pack(side=tk.LEFT, padx=5)
        ttk.Button(zoom_frame, text="+", width=3, command=self.zoom_in).pack(side=tk.LEFT)
        ttk.Button(zoom_frame, text="Fit", width=4, command=self.zoom_fit).pack(side=tk.LEFT, padx=(5, 0))
        
        # Grid controls
        self.grid_var = tk.BooleanVar(value=self.grid_visible)
        ttk.Checkbutton(toolbar, text="Grid", variable=self.grid_var, command=self.toggle_grid).pack(side=tk.LEFT, padx=10)
        
        self.snap_var = tk.BooleanVar(value=self.snap_to_grid)
        ttk.Checkbutton(toolbar, text="Snap", variable=self.snap_var, command=self.toggle_snap).pack(side=tk.LEFT, padx=5)
        
        # Canvas frame with scrollbars
        canvas_frame = ttk.Frame(main_frame)
        canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create canvas with scrollbars
        self.canvas = tk.Canvas(canvas_frame, bg='#f0f0f0', highlightthickness=1, highlightbackground='#cccccc')
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        h_scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        
        self.canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Pack scrollbars and canvas
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Bind events
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_canvas_release)
        self.canvas.bind("<Button-3>", self.on_canvas_right_click)
        self.canvas.bind("<Control-a>", lambda e: self.select_all())
        self.canvas.bind("<Delete>", lambda e: self.delete_selected())
        self.canvas.bind("<Control-c>", lambda e: self.copy_selected())
        self.canvas.bind("<Control-v>", lambda e: self.paste())
        
        # Make canvas focusable
        self.canvas.focus_set()
        
        # Initial display setup
        self.update_canvas_size()
        self.draw_display()
        
    def update_canvas_size(self):
        """Update canvas size based on display config and zoom"""
        display_width = int(self.display_config['width'] * self.zoom_level)
        display_height = int(self.display_config['height'] * self.zoom_level)
        
        # Add margins
        margin = 50
        canvas_width = display_width + 2 * margin
        canvas_height = display_height + 2 * margin
        
        self.canvas.configure(scrollregion=(0, 0, canvas_width, canvas_height))
        
        # Store display area coordinates
        self.display_x = margin
        self.display_y = margin
        self.display_width = display_width
        self.display_height = display_height
        
    def draw_display(self):
        """Draw the display area and contents"""
        self.canvas.delete("all")
        
        # Draw display background
        self.canvas.create_rectangle(
            self.display_x, self.display_y,
            self.display_x + self.display_width, 
            self.display_y + self.display_height,
            fill='black', outline='gray', width=2, tags="display"
        )
        
        # Draw grid
        if self.grid_visible:
            self.draw_grid()
            
        # Draw widgets
        self.draw_widgets()
        
    def draw_grid(self):
        """Draw grid on the display"""
        grid_spacing = int(self.grid_size * self.zoom_level)
        
        # Vertical lines
        x = self.display_x
        while x <= self.display_x + self.display_width:
            self.canvas.create_line(
                x, self.display_y, x, self.display_y + self.display_height,
                fill='#333333', width=1, tags="grid"
            )
            x += grid_spacing
            
        # Horizontal lines
        y = self.display_y
        while y <= self.display_y + self.display_height:
            self.canvas.create_line(
                self.display_x, y, self.display_x + self.display_width, y,
                fill='#333333', width=1, tags="grid"
            )
            y += grid_spacing
            
    def draw_widgets(self):
        """Draw all widgets on the current page"""
        if self.current_page not in self.widgets:
            return
            
        for widget in self.widgets[self.current_page]:
            self.draw_widget(widget)
            
    def draw_widget(self, widget: LVGLWidget):
        """Draw a single widget"""
        # Calculate position and size
        x = self.display_x + (widget.x * self.zoom_level)
        y = self.display_y + (widget.y * self.zoom_level)
        
        # Get size from widget config or default
        widget_info = self.get_widget_info(widget.widget_type)
        default_width, default_height = widget_info.get('default_size', (100, 30))
        
        if isinstance(widget.width, str) and widget.width == "SIZE_CONTENT":
            width = default_width * self.zoom_level
        else:
            width = widget.width * self.zoom_level
            
        if isinstance(widget.height, str) and widget.height == "SIZE_CONTENT":
            height = default_height * self.zoom_level
        else:
            height = widget.height * self.zoom_level
            
        # Determine colors with widget-specific defaults
        widget_defaults = {
            'button': {'bg_color': '#4CAF50', 'border_color': '#2E7D32'},
            'label': {'bg_color': 'transparent', 'border_color': 'transparent'},
            'image': {'bg_color': '#F5F5F5', 'border_color': '#E0E0E0'},
            'slider': {'bg_color': 'transparent', 'border_color': 'transparent'},
            'switch': {'bg_color': 'transparent', 'border_color': 'transparent'},
            'checkbox': {'bg_color': 'transparent', 'border_color': 'transparent'},
            'arc': {'bg_color': 'transparent', 'border_color': 'transparent'},
            'bar': {'bg_color': '#EEEEEE', 'border_color': '#CCCCCC'},
            'dropdown': {'bg_color': 'white', 'border_color': '#CCCCCC'},
            'textarea': {'bg_color': 'white', 'border_color': '#CCCCCC'},
            'led': {'bg_color': 'transparent', 'border_color': 'transparent'},
        }
        
        defaults = widget_defaults.get(widget.widget_type, {'bg_color': '#424242', 'border_color': '#616161'})
        
        # Use widget color or default
        bg_color = widget.bg_color if widget.bg_color != '#000000' else defaults['bg_color']
        border_color = widget.border_color if widget.border_color != '#000000' else defaults['border_color']
        
        bg_color = self.parse_color(bg_color)
        border_color = self.parse_color(border_color)
        
        # Don't draw background for transparent widgets
        if bg_color != 'transparent':
            # Create widget rectangle
            outline_width = max(1, int(widget.border_width * self.zoom_level)) if border_color != 'transparent' else 0
            widget_id = self.canvas.create_rectangle(
                x, y, x + width, y + height,
                fill=bg_color, outline=border_color, width=outline_width,
                tags=f"widget_{widget.id}"
            )
        
        # Add widget-specific content
        self.draw_widget_content(widget, x, y, width, height)
        
        # Highlight if selected
        if widget in self.selected_widgets:
            self.canvas.create_rectangle(
                x - 2, y - 2, x + width + 2, y + height + 2,
                fill='', outline='blue', width=2, tags=f"selection_{widget.id}"
            )
            
            # Draw resize handles
            handle_size = 6
            handles = [
                (x - handle_size//2, y - handle_size//2),  # Top-left
                (x + width - handle_size//2, y - handle_size//2),  # Top-right
                (x - handle_size//2, y + height - handle_size//2),  # Bottom-left
                (x + width - handle_size//2, y + height - handle_size//2),  # Bottom-right
            ]
            
            for hx, hy in handles:
                self.canvas.create_rectangle(
                    hx, hy, hx + handle_size, hy + handle_size,
                    fill='blue', outline='blue', tags=f"handle_{widget.id}"
                )
                
    def draw_widget_content(self, widget: LVGLWidget, x: float, y: float, width: float, height: float):
        """Draw widget-specific content with realistic LVGL appearance"""
        text_size = max(8, int(12 * self.zoom_level))
        
        if widget.widget_type == "label":
            # Draw text with alignment
            text = getattr(widget, 'text', 'Label')
            text_color = self.parse_color(getattr(widget, 'text_color', '#FFFFFF'))
            align = getattr(widget, 'text_align', 'LEFT')
            
            # Calculate text position based on alignment
            if align == 'CENTER':
                text_x, anchor = x + width//2, 'center'
            elif align == 'RIGHT':
                text_x, anchor = x + width - 5, 'e'
            else:  # LEFT
                text_x, anchor = x + 5, 'w'
                
            self.canvas.create_text(
                text_x, y + height//2, text=text,
                font=('Arial', text_size), fill=text_color, anchor=anchor,
                tags=f"widget_{widget.id}"
            )
            
        elif widget.widget_type == "button":
            # Draw button with gradient-like effect
            button_text = getattr(widget, 'text', 'Button')
            
            # Button background with shadow effect
            shadow_offset = max(1, int(2 * self.zoom_level))
            self.canvas.create_rectangle(
                x + shadow_offset, y + shadow_offset, 
                x + width + shadow_offset, y + height + shadow_offset,
                fill='#666666', outline='', tags=f"widget_{widget.id}"
            )
            
            # Main button
            button_color = self.parse_color(getattr(widget, 'bg_color', '#4CAF50'))
            self.canvas.create_rectangle(
                x, y, x + width, y + height,
                fill=button_color, outline='#2E7D32', width=2,
                tags=f"widget_{widget.id}"
            )
            
            # Button highlight
            highlight_height = max(2, int(height * 0.3))
            self.canvas.create_rectangle(
                x + 2, y + 2, x + width - 2, y + highlight_height,
                fill='white', stipple='gray50', tags=f"widget_{widget.id}"
            )
            
            # Button text
            text_color = self.parse_color(getattr(widget, 'text_color', '#FFFFFF'))
            self.canvas.create_text(
                x + width//2, y + height//2, text=button_text,
                font=('Arial', text_size, 'bold'), fill=text_color,
                tags=f"widget_{widget.id}"
            )
            
        elif widget.widget_type == "image":
            # Try to load and display actual image if src is provided
            src = getattr(widget, 'src', '')
            if src and hasattr(self, 'load_image'):
                try:
                    # Try to load the actual image
                    pil_image = self.load_image(src, int(width), int(height))
                    if pil_image:
                        photo = tk.PhotoImage(pil_image)
                        self.canvas.create_image(
                            x + width//2, y + height//2, image=photo,
                            tags=f"widget_{widget.id}"
                        )
                        # Store reference to prevent garbage collection
                        self.canvas.photo_refs = getattr(self.canvas, 'photo_refs', [])
                        self.canvas.photo_refs.append(photo)
                        return
                except:
                    pass
            
            # Draw image placeholder with better styling
            self.canvas.create_rectangle(
                x + 2, y + 2, x + width - 2, y + height - 2,
                fill='#F0F0F0', outline='#CCCCCC', width=1,
                tags=f"widget_{widget.id}"
            )
            
            # Image icon
            icon_size = min(width, height) * 0.4
            icon_x, icon_y = x + width//2, y + height//2 - 5
            
            # Mountain shape
            self.canvas.create_polygon(
                icon_x - icon_size//2, icon_y + icon_size//4,
                icon_x - icon_size//4, icon_y - icon_size//4,
                icon_x, icon_y,
                icon_x + icon_size//4, icon_y - icon_size//4,
                icon_x + icon_size//2, icon_y + icon_size//4,
                fill='#666666', tags=f"widget_{widget.id}"
            )
            
            # Sun
            sun_size = icon_size // 6
            self.canvas.create_oval(
                icon_x + icon_size//4 - sun_size, icon_y - icon_size//3 - sun_size,
                icon_x + icon_size//4 + sun_size, icon_y - icon_size//3 + sun_size,
                fill='#FFD700', outline='', tags=f"widget_{widget.id}"
            )
            
            # File name if provided
            if src:
                self.canvas.create_text(
                    x + width//2, y + height - 8, text=src[:12] + '...' if len(src) > 12 else src,
                    font=('Arial', max(6, text_size - 2)), fill='#666666',
                    tags=f"widget_{widget.id}"
                )
            
        elif widget.widget_type == "slider":
            # Draw enhanced slider
            track_height = max(4, int(6 * self.zoom_level))
            track_y = y + height // 2 - track_height // 2
            margin = int(10 * self.zoom_level)
            
            # Track background
            self.canvas.create_rectangle(
                x + margin, track_y, x + width - margin, track_y + track_height,
                fill='#CCCCCC', outline='#999999', tags=f"widget_{widget.id}"
            )
            
            # Track progress
            value = getattr(widget, 'value', 50)
            max_val = getattr(widget, 'max_value', 100)
            min_val = getattr(widget, 'min_value', 0)
            progress_width = ((value - min_val) / (max_val - min_val)) * (width - 2 * margin)
            
            self.canvas.create_rectangle(
                x + margin, track_y, x + margin + progress_width, track_y + track_height,
                fill='#2196F3', outline='', tags=f"widget_{widget.id}"
            )
            
            # Knob
            knob_x = x + margin + progress_width
            knob_size = max(12, int(16 * self.zoom_level))
            
            # Knob shadow
            self.canvas.create_oval(
                knob_x - knob_size//2 + 2, track_y + track_height//2 - knob_size//2 + 2,
                knob_x + knob_size//2 + 2, track_y + track_height//2 + knob_size//2 + 2,
                fill='#666666', outline='', tags=f"widget_{widget.id}"
            )
            
            # Knob
            self.canvas.create_oval(
                knob_x - knob_size//2, track_y + track_height//2 - knob_size//2,
                knob_x + knob_size//2, track_y + track_height//2 + knob_size//2,
                fill='white', outline='#2196F3', width=2,
                tags=f"widget_{widget.id}"
            )
            
            # Value text
            self.canvas.create_text(
                x + width//2, y + height - 8, text=str(int(value)),
                font=('Arial', max(8, text_size - 2)), fill='#333333',
                tags=f"widget_{widget.id}"
            )
            
        elif widget.widget_type == "switch":
            # Draw iOS-style switch
            switch_width = min(width - 10, int(50 * self.zoom_level))
            switch_height = min(height - 10, int(25 * self.zoom_level))
            switch_x = x + (width - switch_width) // 2
            switch_y = y + (height - switch_height) // 2
            
            is_on = getattr(widget, 'state', False)
            
            # Switch track
            track_color = '#4CAF50' if is_on else '#CCCCCC'
            self.canvas.create_oval(
                switch_x, switch_y, switch_x + switch_width, switch_y + switch_height,
                fill=track_color, outline='#999999', tags=f"widget_{widget.id}"
            )
            
            # Switch knob
            knob_size = switch_height - 4
            knob_x = switch_x + switch_width - knob_size - 2 if is_on else switch_x + 2
            
            # Knob shadow
            self.canvas.create_oval(
                knob_x + 1, switch_y + 3, knob_x + knob_size + 1, switch_y + knob_size + 3,
                fill='#888888', outline='', tags=f"widget_{widget.id}"
            )
            
            # Knob
            self.canvas.create_oval(
                knob_x, switch_y + 2, knob_x + knob_size, switch_y + knob_size + 2,
                fill='white', outline='#DDDDDD', tags=f"widget_{widget.id}"
            )
            
        elif widget.widget_type == "checkbox":
            # Draw modern checkbox
            check_size = min(width - 10, height - 10, int(20 * self.zoom_level))
            check_x = x + 5
            check_y = y + (height - check_size) // 2
            
            is_checked = getattr(widget, 'checked', False)
            
            # Checkbox background
            bg_color = '#2196F3' if is_checked else 'white'
            border_color = '#2196F3' if is_checked else '#CCCCCC'
            
            self.canvas.create_rectangle(
                check_x, check_y, check_x + check_size, check_y + check_size,
                fill=bg_color, outline=border_color, width=2,
                tags=f"widget_{widget.id}"
            )
            
            # Checkmark
            if is_checked:
                # Draw checkmark path
                check_points = [
                    check_x + check_size * 0.2, check_y + check_size * 0.5,
                    check_x + check_size * 0.45, check_y + check_size * 0.7,
                    check_x + check_size * 0.8, check_y + check_size * 0.3
                ]
                self.canvas.create_line(
                    check_points, fill='white', width=max(2, int(3 * self.zoom_level)),
                    capstyle='round', joinstyle='round', tags=f"widget_{widget.id}"
                )
                
            # Label text
            text = getattr(widget, 'text', 'Checkbox')
            if text:
                self.canvas.create_text(
                    check_x + check_size + 8, y + height//2,
                    text=text, font=('Arial', text_size), fill='white', anchor='w',
                    tags=f"widget_{widget.id}"
                )
                
        elif widget.widget_type == "arc":
            # Draw arc/circular progress
            margin = max(3, int(5 * self.zoom_level))
            value = getattr(widget, 'value', 25)
            max_val = getattr(widget, 'max_value', 100)
            
            # Background arc
            self.canvas.create_oval(
                x + margin, y + margin, x + width - margin, y + height - margin,
                fill='', outline='#EEEEEE', width=max(3, int(6 * self.zoom_level)),
                tags=f"widget_{widget.id}"
            )
            
            # Progress arc
            extent = (value / max_val) * 270  # 270 degrees max
            if extent > 0:
                self.canvas.create_arc(
                    x + margin, y + margin, x + width - margin, y + height - margin,
                    start=135, extent=extent, outline='#2196F3', 
                    width=max(3, int(6 * self.zoom_level)), style='arc',
                    tags=f"widget_{widget.id}"
                )
                
            # Center value
            self.canvas.create_text(
                x + width//2, y + height//2, text=f"{int(value)}%",
                font=('Arial', text_size, 'bold'), fill='white',
                tags=f"widget_{widget.id}"
            )
            
        elif widget.widget_type == "bar":
            # Draw progress bar
            margin = max(2, int(3 * self.zoom_level))
            value = getattr(widget, 'value', 50)
            max_val = getattr(widget, 'max_value', 100)
            min_val = getattr(widget, 'min_value', 0)
            
            # Background
            self.canvas.create_rectangle(
                x + margin, y + margin, x + width - margin, y + height - margin,
                fill='#EEEEEE', outline='#CCCCCC', tags=f"widget_{widget.id}"
            )
            
            # Progress
            progress_width = ((value - min_val) / (max_val - min_val)) * (width - 2 * margin)
            if progress_width > 0:
                self.canvas.create_rectangle(
                    x + margin, y + margin, x + margin + progress_width, y + height - margin,
                    fill='#4CAF50', outline='', tags=f"widget_{widget.id}"
                )
                
            # Value text
            self.canvas.create_text(
                x + width//2, y + height//2, text=f"{int(value)}%",
                font=('Arial', text_size), fill='#333333',
                tags=f"widget_{widget.id}"
            )
            
        elif widget.widget_type == "dropdown":
            # Draw dropdown with arrow
            dropdown_text = getattr(widget, 'text', 'Select...')
            
            # Background
            self.canvas.create_rectangle(
                x, y, x + width, y + height,
                fill='white', outline='#CCCCCC', width=1,
                tags=f"widget_{widget.id}"
            )
            
            # Text
            self.canvas.create_text(
                x + 8, y + height//2, text=dropdown_text,
                font=('Arial', text_size), fill='#333333', anchor='w',
                tags=f"widget_{widget.id}"
            )
            
            # Dropdown arrow
            arrow_size = max(6, int(8 * self.zoom_level))
            arrow_x = x + width - arrow_size - 8
            arrow_y = y + height//2
            
            self.canvas.create_polygon(
                arrow_x, arrow_y - arrow_size//2,
                arrow_x + arrow_size, arrow_y - arrow_size//2,
                arrow_x + arrow_size//2, arrow_y + arrow_size//2,
                fill='#666666', tags=f"widget_{widget.id}"
            )
            
        elif widget.widget_type == "textarea":
            # Draw text area
            self.canvas.create_rectangle(
                x, y, x + width, y + height,
                fill='white', outline='#CCCCCC', width=1,
                tags=f"widget_{widget.id}"
            )
            
            # Placeholder text or content
            text_content = getattr(widget, 'text', 'Enter text...')
            lines = text_content.split('\n')[:max(1, int((height - 10) // (text_size + 2)))]
            
            for i, line in enumerate(lines):
                self.canvas.create_text(
                    x + 5, y + 5 + i * (text_size + 2),
                    text=line[:max(1, int((width - 10) // (text_size * 0.6)))],
                    font=('Arial', text_size), fill='#333333', anchor='nw',
                    tags=f"widget_{widget.id}"
                )
                
            # Cursor
            if len(lines) > 0:
                cursor_x = x + 5 + len(lines[-1]) * (text_size * 0.6)
                cursor_y = y + 5 + (len(lines) - 1) * (text_size + 2)
                self.canvas.create_line(
                    cursor_x, cursor_y, cursor_x, cursor_y + text_size,
                    fill='#333333', width=1, tags=f"widget_{widget.id}"
                )
                
        elif widget.widget_type == "led":
            # Draw LED indicator
            led_size = min(width - 10, height - 10)
            led_x = x + (width - led_size) // 2
            led_y = y + (height - led_size) // 2
            
            is_on = getattr(widget, 'state', True)
            led_color = getattr(widget, 'color', '#FF0000') if is_on else '#660000'
            
            # LED glow effect
            if is_on:
                glow_size = led_size + 6
                self.canvas.create_oval(
                    led_x - 3, led_y - 3, led_x + glow_size - 3, led_y + glow_size - 3,
                    fill=led_color, stipple='gray25', outline='',
                    tags=f"widget_{widget.id}"
                )
                
            # LED body
            self.canvas.create_oval(
                led_x, led_y, led_x + led_size, led_y + led_size,
                fill=led_color, outline='#333333', width=1,
                tags=f"widget_{widget.id}"
            )
            
            # LED highlight
            if is_on:
                highlight_size = led_size // 3
                self.canvas.create_oval(
                    led_x + led_size//4, led_y + led_size//4,
                    led_x + led_size//4 + highlight_size, led_y + led_size//4 + highlight_size,
                    fill='white', outline='', tags=f"widget_{widget.id}"
                )
                
        else:
            # Draw widget type name for unsupported widgets
            self.canvas.create_text(
                x + width//2, y + height//2, text=widget.widget_type.title(),
                font=('Arial', text_size), fill='white',
                tags=f"widget_{widget.id}"
            )
            
    def parse_color(self, color_str: str) -> str:
        """Parse LVGL color format to tkinter color"""
        if color_str.startswith('0x'):
            # Convert hex color
            hex_color = color_str[2:]
            if len(hex_color) == 6:
                return f"#{hex_color}"
            elif len(hex_color) == 3:
                # Convert RGB to RRGGBB
                return f"#{hex_color[0]*2}{hex_color[1]*2}{hex_color[2]*2}"
        elif color_str.startswith('#'):
            return color_str
        else:
            # Named colors
            color_map = {
                'red': '#FF0000', 'green': '#00FF00', 'blue': '#0000FF',
                'white': '#FFFFFF', 'black': '#000000', 'gray': '#808080',
                'yellow': '#FFFF00', 'cyan': '#00FFFF', 'magenta': '#FF00FF'
            }
            return color_map.get(color_str.lower(), '#FFFFFF')
            
    def load_image(self, src: str, width: int, height: int):
        """Load and resize image for display"""
        try:
            from PIL import Image, ImageTk
            import os
            
            # Try to find the image file
            image_path = src
            if not os.path.isabs(src):
                # Try relative to project directory
                base_paths = [
                    os.getcwd(),
                    os.path.join(os.getcwd(), 'images'),
                    os.path.join(os.getcwd(), 'assets'),
                    os.path.dirname(os.path.abspath(__file__))
                ]
                
                for base_path in base_paths:
                    test_path = os.path.join(base_path, src)
                    if os.path.exists(test_path):
                        image_path = test_path
                        break
                        
            if not os.path.exists(image_path):
                return None
                
            # Load and resize image
            pil_image = Image.open(image_path)
            pil_image = pil_image.resize((max(1, width - 4), max(1, height - 4)), Image.Resampling.LANCZOS)
            
            # Convert to PhotoImage
            return ImageTk.PhotoImage(pil_image)
            
        except Exception as e:
            print(f"Error loading image {src}: {e}")
            return None
        
    def get_widget_info(self, widget_type: str) -> Dict[str, Any]:
        """Get widget information from the widget library"""
        for category in LVGL_WIDGETS.values():
            if widget_type in category:
                return category[widget_type]
        return {'name': widget_type.title(), 'default_size': (100, 30)}
        
    # Event handlers
    def on_canvas_click(self, event):
        """Handle canvas click events"""
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        
        if self.placing_widget:
            # Place new widget
            self.place_widget(canvas_x, canvas_y)
        else:
            # Select widget(s)
            clicked_widget = self.get_widget_at_position(canvas_x, canvas_y)
            
            if not event.state & 0x4:  # Ctrl not pressed
                self.selected_widgets.clear()
                
            if clicked_widget:
                if clicked_widget not in self.selected_widgets:
                    self.selected_widgets.append(clicked_widget)
                self.selection_callback(clicked_widget)
                
                # Start drag
                self.drag_start = (canvas_x, canvas_y)
                self.drag_widgets = self.selected_widgets.copy()
            else:
                self.selection_callback(None)
                
        self.draw_display()
        
    def on_canvas_drag(self, event):
        """Handle canvas drag events"""
        if self.drag_start and self.drag_widgets:
            canvas_x = self.canvas.canvasx(event.x)
            canvas_y = self.canvas.canvasy(event.y)
            
            dx = (canvas_x - self.drag_start[0]) / self.zoom_level
            dy = (canvas_y - self.drag_start[1]) / self.zoom_level
            
            # Snap to grid if enabled
            if self.snap_to_grid:
                dx = round(dx / self.grid_size) * self.grid_size
                dy = round(dy / self.grid_size) * self.grid_size
                
            for widget in self.drag_widgets:
                new_x = max(0, widget.x + dx)
                new_y = max(0, widget.y + dy)
                
                # Keep within display bounds
                new_x = min(new_x, self.display_config['width'] - 50)
                new_y = min(new_y, self.display_config['height'] - 30)
                
                widget.x = new_x
                widget.y = new_y
                
            self.drag_start = (canvas_x, canvas_y)
            self.draw_display()
            
    def on_canvas_release(self, event):
        """Handle canvas release events"""
        if self.drag_start:
            self.drag_start = None
            self.drag_widgets = []
            self.change_callback()
            
    def on_canvas_right_click(self, event):
        """Handle right-click context menu"""
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        
        clicked_widget = self.get_widget_at_position(canvas_x, canvas_y)
        
        # Create context menu
        context_menu = tk.Menu(self.canvas, tearoff=0)
        
        if clicked_widget:
            context_menu.add_command(label=f"Edit {clicked_widget.widget_type}", 
                                   command=lambda: self.selection_callback(clicked_widget))
            context_menu.add_separator()
            context_menu.add_command(label="Copy", command=self.copy_selected)
            context_menu.add_command(label="Delete", command=self.delete_selected)
            context_menu.add_separator()
            context_menu.add_command(label="Bring to Front", 
                                   command=lambda: self.bring_to_front(clicked_widget))
            context_menu.add_command(label="Send to Back", 
                                   command=lambda: self.send_to_back(clicked_widget))
        else:
            context_menu.add_command(label="Paste", command=self.paste, 
                                   state='normal' if self.clipboard else 'disabled')
            
        try:
            context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            context_menu.grab_release()
            
    def get_widget_at_position(self, x: float, y: float) -> Optional[LVGLWidget]:
        """Get widget at canvas position"""
        if self.current_page not in self.widgets:
            return None
            
        # Check from front to back
        for widget in reversed(self.widgets[self.current_page]):
            widget_x = self.display_x + (widget.x * self.zoom_level)
            widget_y = self.display_y + (widget.y * self.zoom_level)
            
            widget_info = self.get_widget_info(widget.widget_type)
            default_width, default_height = widget_info.get('default_size', (100, 30))
            
            if isinstance(widget.width, str) and widget.width == "SIZE_CONTENT":
                width = default_width * self.zoom_level
            else:
                width = widget.width * self.zoom_level
                
            if isinstance(widget.height, str) and widget.height == "SIZE_CONTENT":
                height = default_height * self.zoom_level
            else:
                height = widget.height * self.zoom_level
                
            if (widget_x <= x <= widget_x + width and 
                widget_y <= y <= widget_y + height):
                return widget
                
        return None
        
    # Widget management
    def start_placing_widget(self, widget_type: str):
        """Start placing a new widget"""
        self.placing_widget = widget_type
        self.canvas.configure(cursor="crosshair")
        
    def place_widget(self, x: float, y: float):
        """Place a new widget at the specified position"""
        if not self.placing_widget:
            return
            
        # Convert canvas coordinates to display coordinates
        display_x = (x - self.display_x) / self.zoom_level
        display_y = (y - self.display_y) / self.zoom_level
        
        # Snap to grid if enabled
        if self.snap_to_grid:
            display_x = round(display_x / self.grid_size) * self.grid_size
            display_y = round(display_y / self.grid_size) * self.grid_size
            
        # Ensure within bounds
        display_x = max(0, min(display_x, self.display_config['width'] - 50))
        display_y = max(0, min(display_y, self.display_config['height'] - 30))
        
        # Create widget
        widget_id = f"{self.placing_widget}_{len(self.widgets.get(self.current_page, []))}"
        
        widget = create_widget(
            self.placing_widget,
            id=widget_id,
            x=int(display_x),
            y=int(display_y)
        )
        
        # Add to current page
        if self.current_page not in self.widgets:
            self.widgets[self.current_page] = []
        self.widgets[self.current_page].append(widget)
        
        # Select the new widget
        self.selected_widgets = [widget]
        self.selection_callback(widget)
        
        # Stop placing
        self.placing_widget = None
        self.canvas.configure(cursor="")
        
        self.change_callback()
        
    def update_widget_display(self, widget: LVGLWidget):
        """Update the display of a specific widget"""
        self.draw_display()
        
    def update_display_size(self, width: int, height: int):
        """Update display size"""
        self.display_config['width'] = width
        self.display_config['height'] = height
        self.update_canvas_size()
        self.draw_display()
        
    # Selection management
    def select_all(self):
        """Select all widgets on current page"""
        if self.current_page in self.widgets:
            self.selected_widgets = self.widgets[self.current_page].copy()
            if self.selected_widgets:
                self.selection_callback(self.selected_widgets[0])
            self.draw_display()
            
    def clear_selection(self):
        """Clear widget selection"""
        self.selected_widgets.clear()
        self.selection_callback(None)
        self.draw_display()
        
    # Clipboard operations
    def copy_selected(self):
        """Copy selected widgets to clipboard"""
        self.clipboard = [copy.deepcopy(widget) for widget in self.selected_widgets]
        
    def paste(self):
        """Paste widgets from clipboard"""
        if not self.clipboard:
            return
            
        if self.current_page not in self.widgets:
            self.widgets[self.current_page] = []
            
        # Paste with offset
        offset_x, offset_y = 20, 20
        new_widgets = []
        
        for widget in self.clipboard:
            new_widget = copy.deepcopy(widget)
            new_widget.id = f"{widget.widget_type}_{len(self.widgets[self.current_page])}"
            new_widget.x += offset_x
            new_widget.y += offset_y
            
            self.widgets[self.current_page].append(new_widget)
            new_widgets.append(new_widget)
            
        # Select pasted widgets
        self.selected_widgets = new_widgets
        if new_widgets:
            self.selection_callback(new_widgets[0])
            
        self.change_callback()
        self.draw_display()
        
    def delete_selected(self):
        """Delete selected widgets"""
        if self.current_page not in self.widgets:
            return
            
        for widget in self.selected_widgets:
            if widget in self.widgets[self.current_page]:
                self.widgets[self.current_page].remove(widget)
                
        self.selected_widgets.clear()
        self.selection_callback(None)
        self.change_callback()
        self.draw_display()
        
    # Z-order management
    def bring_to_front(self, widget: LVGLWidget):
        """Bring widget to front"""
        if self.current_page in self.widgets and widget in self.widgets[self.current_page]:
            self.widgets[self.current_page].remove(widget)
            self.widgets[self.current_page].append(widget)
            self.change_callback()
            self.draw_display()
            
    def send_to_back(self, widget: LVGLWidget):
        """Send widget to back"""
        if self.current_page in self.widgets and widget in self.widgets[self.current_page]:
            self.widgets[self.current_page].remove(widget)
            self.widgets[self.current_page].insert(0, widget)
            self.change_callback()
            self.draw_display()
            
    # View controls
    def zoom_in(self):
        """Zoom in on the canvas"""
        self.zoom_level = min(self.zoom_level * 1.2, 5.0)
        self.update_zoom_display()
        
    def zoom_out(self):
        """Zoom out on the canvas"""
        self.zoom_level = max(self.zoom_level / 1.2, 0.1)
        self.update_zoom_display()
        
    def zoom_fit(self):
        """Zoom to fit display in view"""
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        if canvas_width > 1 and canvas_height > 1:
            zoom_x = (canvas_width - 100) / self.display_config['width']
            zoom_y = (canvas_height - 100) / self.display_config['height']
            self.zoom_level = min(zoom_x, zoom_y, 2.0)
            self.update_zoom_display()
            
    def update_zoom_display(self):
        """Update zoom display and canvas"""
        self.zoom_label.config(text=f"{int(self.zoom_level * 100)}%")
        self.update_canvas_size()
        self.draw_display()
        
    def toggle_grid(self):
        """Toggle grid visibility"""
        self.grid_visible = self.grid_var.get()
        self.draw_display()
        
    def toggle_snap(self):
        """Toggle snap to grid"""
        self.snap_to_grid = self.snap_var.get()
        
    # Alignment tools
    def align_widgets(self, alignment: str):
        """Align selected widgets"""
        if len(self.selected_widgets) < 2:
            return
            
        if alignment == 'left':
            min_x = min(w.x for w in self.selected_widgets)
            for widget in self.selected_widgets:
                widget.x = min_x
        elif alignment == 'right':
            max_x = max(w.x + (w.width if isinstance(w.width, int) else 100) for w in self.selected_widgets)
            for widget in self.selected_widgets:
                widget.x = max_x - (widget.width if isinstance(widget.width, int) else 100)
        elif alignment == 'center':
            avg_x = sum(w.x + (w.width if isinstance(w.width, int) else 100) / 2 for w in self.selected_widgets) / len(self.selected_widgets)
            for widget in self.selected_widgets:
                widget.x = avg_x - (widget.width if isinstance(widget.width, int) else 100) / 2
        elif alignment == 'top':
            min_y = min(w.y for w in self.selected_widgets)
            for widget in self.selected_widgets:
                widget.y = min_y
        elif alignment == 'bottom':
            max_y = max(w.y + (w.height if isinstance(w.height, int) else 30) for w in self.selected_widgets)
            for widget in self.selected_widgets:
                widget.y = max_y - (widget.height if isinstance(widget.height, int) else 30)
        elif alignment == 'middle':
            avg_y = sum(w.y + (w.height if isinstance(w.height, int) else 30) / 2 for w in self.selected_widgets) / len(self.selected_widgets)
            for widget in self.selected_widgets:
                widget.y = avg_y - (widget.height if isinstance(widget.height, int) else 30) / 2
                
        self.change_callback()
        self.draw_display()
        
    def distribute_widgets(self, direction: str):
        """Distribute selected widgets evenly"""
        if len(self.selected_widgets) < 3:
            return
            
        if direction == 'horizontal':
            self.selected_widgets.sort(key=lambda w: w.x)
            total_width = self.selected_widgets[-1].x - self.selected_widgets[0].x
            spacing = total_width / (len(self.selected_widgets) - 1)
            
            for i, widget in enumerate(self.selected_widgets[1:-1], 1):
                widget.x = self.selected_widgets[0].x + i * spacing
                
        elif direction == 'vertical':
            self.selected_widgets.sort(key=lambda w: w.y)
            total_height = self.selected_widgets[-1].y - self.selected_widgets[0].y
            spacing = total_height / (len(self.selected_widgets) - 1)
            
            for i, widget in enumerate(self.selected_widgets[1:-1], 1):
                widget.y = self.selected_widgets[0].y + i * spacing
                
        self.change_callback()
        self.draw_display()
        
    # Page management
    def set_current_page(self, page_id: str):
        """Set the current page"""
        self.current_page = page_id
        if page_id not in self.widgets:
            self.widgets[page_id] = []
        self.selected_widgets.clear()
        self.selection_callback(None)
        self.draw_display()
        
    def clear_all(self):
        """Clear all widgets"""
        self.widgets.clear()
        self.selected_widgets.clear()
        self.selection_callback(None)
        
    def get_widgets_data(self) -> Dict[str, List[Dict]]:
        """Get all widgets data for saving"""
        result = {}
        for page_id, page_widgets in self.widgets.items():
            result[page_id] = [widget.to_dict() for widget in page_widgets]
        return result
        
    def get_widgets_for_page(self, page_id: str) -> List[Dict]:
        """Get widgets data for a specific page (for live preview)"""
        if page_id not in self.widgets:
            return []
        
        result = []
        for widget in self.widgets[page_id]:
            widget_data = widget.to_dict()
            # Add additional properties for preview
            widget_data.update({
                'widget_type': widget.widget_type,
                'id': widget.id,
                'x': widget.x,
                'y': widget.y,
                'width': widget.width,
                'height': widget.height
            })
            result.append(widget_data)
        return result
        
    def load_widgets(self, widgets_data: Dict[str, List[Dict]]):
        """Load widgets from data"""
        self.widgets.clear()
        for page_id, page_widgets in widgets_data.items():
            self.widgets[page_id] = []
            for widget_data in page_widgets:
                widget_type = widget_data.get('widget_type', 'obj')
                widget = create_widget(widget_type, **widget_data)
                self.widgets[page_id].append(widget)
        self.draw_display()
