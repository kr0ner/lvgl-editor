#!/usr/bin/env python3
"""
LVGL Layout Editor for ESPHome
A comprehensive graphical editor for creating LVGL layouts compatible with ESPHome
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, colorchooser
import yaml
import json
import os
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from PIL import Image, ImageTk
import copy

# Import our modules
from widgets import LVGLWidget, LVGL_WIDGETS
from canvas_editor import CanvasEditor
from property_panel import PropertyPanel
from widget_library import WidgetLibrary
from yaml_generator import YAMLGenerator
from page_manager import PageManager

class LVGLEditor:
    """Main LVGL Editor Application"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("LVGL Layout Editor for ESPHome")
        self.root.geometry("1400x900")
        
        # Application state
        self.current_project = None
        self.display_config = {
            'width': 320,
            'height': 240,
            'color_depth': 16,
            'buffer_size': '100%'
        }
        
        # UI Components
        self.canvas_editor = None
        self.property_panel = None
        self.widget_library = None
        self.page_manager = None
        self.yaml_generator = YAMLGenerator()
        
        # Device state for live preview
        self.device_state = {
            'current_page': 'main_page',
            'widget_states': {},
            'slider_values': {},
            'switch_states': {},
            'checkbox_states': {},
            'input_values': {},
            'drag_widget': None,
            'drag_start': None
        }
        
        # Image cache for device preview
        self.device_image_cache = {}
        
        # Initialize UI
        self.create_ui()
        self.create_menu()
        
        # Load default project
        self.new_project()
        
        # Initialize live preview
        self.update_live_preview()
        
    def create_ui(self):
        """Create the main user interface"""
        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create main horizontal paned window
        main_paned = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True)
        
        # Left panel (300px) - Project structure and widgets
        left_panel = ttk.Frame(main_paned, width=300)
        main_paned.add(left_panel, weight=0)
        
        # Center panel - Editor and preview
        center_panel = ttk.Frame(main_paned)
        main_paned.add(center_panel, weight=1)
        
        # Create left panel content
        self.create_left_panel(left_panel)
        
        # Create center panel with editor and integrated preview
        self.create_center_panel(center_panel)
        
    def create_left_panel(self, parent):
        """Create the left panel with project tree and widgets"""
        # Project tree view
        tree_frame = ttk.LabelFrame(parent, text="Project Structure", padding=5)
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        
        # Tree view with scrollbar
        tree_container = ttk.Frame(tree_frame)
        tree_container.pack(fill=tk.BOTH, expand=True)
        
        self.project_tree = ttk.Treeview(tree_container, show="tree headings", height=8)
        self.project_tree["columns"] = ("type", "properties")
        self.project_tree.heading("#0", text="Name", anchor=tk.W)
        self.project_tree.heading("type", text="Type", anchor=tk.W)
        self.project_tree.heading("properties", text="Size", anchor=tk.W)
        
        self.project_tree.column("#0", width=150, minwidth=100)
        self.project_tree.column("type", width=80, minwidth=60)
        self.project_tree.column("properties", width=70, minwidth=50)
        
        # Tree scrollbar
        tree_scroll = ttk.Scrollbar(tree_container, orient=tk.VERTICAL, command=self.project_tree.yview)
        self.project_tree.configure(yscrollcommand=tree_scroll.set)
        
        self.project_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind tree events
        self.project_tree.bind("<<TreeviewSelect>>", self.on_tree_select)
        self.project_tree.bind("<Double-1>", self.on_tree_double_click)
        
        # Page manager
        page_frame = ttk.LabelFrame(parent, text="Pages", padding=5)
        page_frame.pack(fill=tk.X, pady=5)
        self.page_manager = PageManager(page_frame, self.on_page_changed)
        
        # Display settings
        display_frame = ttk.LabelFrame(parent, text="Display Settings", padding=5)
        display_frame.pack(fill=tk.X, pady=5)
        self.create_display_settings(display_frame)
        
        # Widget library
        widget_frame = ttk.LabelFrame(parent, text="Widget Library", padding=5)
        widget_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        self.widget_library = WidgetLibrary(widget_frame, self.on_widget_selected)
        
    def create_center_panel(self, parent):
        """Create the center panel with editor and side-by-side live preview"""
        
        # Create horizontal paned window for editor and preview side-by-side
        center_paned = ttk.PanedWindow(parent, orient=tk.HORIZONTAL)
        center_paned.pack(fill=tk.BOTH, expand=True)
        
        # Left side: Editor and properties (60% width)
        editor_container = ttk.Frame(center_paned)
        center_paned.add(editor_container, weight=3)
        
        # Create vertical paned window for editor and properties
        editor_paned = ttk.PanedWindow(editor_container, orient=tk.VERTICAL)
        editor_paned.pack(fill=tk.BOTH, expand=True)
        
        # Canvas editor (top)
        canvas_frame = ttk.Frame(editor_paned)
        editor_paned.add(canvas_frame, weight=2)
        
        self.canvas_editor = CanvasEditor(
            canvas_frame, 
            self.display_config,
            self.on_widget_selected_canvas,
            self.on_widgets_changed
        )
        
        # Property panel (bottom)
        property_frame = ttk.Frame(editor_paned, height=250)
        editor_paned.add(property_frame, weight=0)
        
        self.property_panel = PropertyPanel(
            property_frame,
            self.on_property_changed
        )
        
        # Right side: Live Preview (40% width)
        preview_container = ttk.Frame(center_paned)
        center_paned.add(preview_container, weight=2)
        
        # Create the integrated live preview in the right panel
        self.create_live_preview(preview_container)
        
    def create_live_preview(self, parent):
        """Create integrated live preview that behaves like a real LVGL device"""
        
        # Main frame with title
        main_frame = ttk.LabelFrame(parent, text="Device Preview", padding=5)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Compact controls frame
        controls_frame = ttk.Frame(main_frame)
        controls_frame.pack(fill=tk.X, pady=(0, 5))
        
        # First row of controls
        controls_row1 = ttk.Frame(controls_frame)
        controls_row1.pack(fill=tk.X, pady=(0, 2))
        
        # Scale control
        ttk.Label(controls_row1, text="Scale:").pack(side=tk.LEFT)
        self.preview_scale_var = tk.DoubleVar(value=0.8)
        scale_spinbox = ttk.Spinbox(controls_row1, from_=0.3, to=2.0, increment=0.1,
                                   textvariable=self.preview_scale_var, width=5,
                                   command=self.update_preview_scale)
        scale_spinbox.pack(side=tk.LEFT, padx=(2, 8))
        
        # Device selection
        ttk.Label(controls_row1, text="Device:").pack(side=tk.LEFT)
        self.device_var = tk.StringVar(value="ESP32")
        device_combo = ttk.Combobox(controls_row1, textvariable=self.device_var, 
                                   values=["ESP32", "M5Stack", "T-Display"], 
                                   width=8, state='readonly')
        device_combo.pack(side=tk.LEFT, padx=(2, 0))
        
        # Second row of controls
        controls_row2 = ttk.Frame(controls_frame)
        controls_row2.pack(fill=tk.X, pady=(0, 2))
        
        # Current page indicator
        ttk.Label(controls_row2, text="Page:").pack(side=tk.LEFT)
        self.current_page_label = ttk.Label(controls_row2, text="main_page", 
                                           foreground="blue", font=("Arial", 8, "bold"))
        self.current_page_label.pack(side=tk.LEFT, padx=(2, 8))
        
        # Action buttons
        ttk.Button(controls_row2, text="Refresh", command=self.refresh_device_preview, 
                  width=7).pack(side=tk.LEFT, padx=(0, 2))
        ttk.Button(controls_row2, text="Reset", command=self.reset_device_state, 
                  width=6).pack(side=tk.LEFT, padx=(0, 0))
        
        # Device canvas container with scrollbars
        canvas_container = ttk.Frame(main_frame)
        canvas_container.pack(fill=tk.BOTH, expand=True)
        
        # Create canvas with device styling
        self.device_canvas = tk.Canvas(canvas_container, bg='#1a1a1a', highlightthickness=0)
        
        # Scrollbars for large previews
        v_scroll = ttk.Scrollbar(canvas_container, orient=tk.VERTICAL, command=self.device_canvas.yview)
        h_scroll = ttk.Scrollbar(canvas_container, orient=tk.HORIZONTAL, command=self.device_canvas.xview)
        
        self.device_canvas.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
        
        # Grid layout for canvas and scrollbars
        canvas_container.grid_rowconfigure(0, weight=1)
        canvas_container.grid_columnconfigure(0, weight=1)
        
        self.device_canvas.grid(row=0, column=0, sticky="nsew")
        v_scroll.grid(row=0, column=1, sticky="ns")
        h_scroll.grid(row=1, column=0, sticky="ew")
        
        # Bind events for device interaction
        self.device_canvas.bind("<Button-1>", self.on_device_click)
        self.device_canvas.bind("<B1-Motion>", self.on_device_drag)
        self.device_canvas.bind("<ButtonRelease-1>", self.on_device_release)
        self.device_canvas.bind("<Configure>", self.on_device_canvas_configure)
        
        # Initialize device preview
        self.update_device_preview()
        
    def create_display_settings(self, parent):
        """Create display configuration UI"""
        # Width
        ttk.Label(parent, text="Width:").grid(row=0, column=0, sticky=tk.W, pady=2)
        width_var = tk.StringVar(value=str(self.display_config['width']))
        width_entry = ttk.Entry(parent, textvariable=width_var, width=10)
        width_entry.grid(row=0, column=1, pady=2)
        width_var.trace('w', lambda *args: self.update_display_config('width', width_var.get()))
        
        # Height
        ttk.Label(parent, text="Height:").grid(row=1, column=0, sticky=tk.W, pady=2)
        height_var = tk.StringVar(value=str(self.display_config['height']))
        height_entry = ttk.Entry(parent, textvariable=height_var, width=10)
        height_entry.grid(row=1, column=1, pady=2)
        height_var.trace('w', lambda *args: self.update_display_config('height', height_var.get()))
        
        # Color depth
        ttk.Label(parent, text="Color Depth:").grid(row=2, column=0, sticky=tk.W, pady=2)
        depth_var = tk.StringVar(value=str(self.display_config['color_depth']))
        depth_combo = ttk.Combobox(parent, textvariable=depth_var, values=['16'], width=8)
        depth_combo.grid(row=2, column=1, pady=2)
        depth_var.trace('w', lambda *args: self.update_display_config('color_depth', depth_var.get()))
        
        # Buffer size
        ttk.Label(parent, text="Buffer Size:").grid(row=3, column=0, sticky=tk.W, pady=2)
        buffer_var = tk.StringVar(value=self.display_config['buffer_size'])
        buffer_combo = ttk.Combobox(parent, textvariable=buffer_var, values=['12%', '25%', '50%', '100%'], width=8)
        buffer_combo.grid(row=3, column=1, pady=2)
        buffer_var.trace('w', lambda *args: self.update_display_config('buffer_size', buffer_var.get()))
        
    def create_menu(self):
        """Create the application menu"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New Project", command=self.new_project, accelerator="Ctrl+N")
        file_menu.add_command(label="Open Project", command=self.open_project, accelerator="Ctrl+O")
        file_menu.add_command(label="Save Project", command=self.save_project, accelerator="Ctrl+S")
        file_menu.add_command(label="Save Project As...", command=self.save_project_as, accelerator="Ctrl+Shift+S")
        file_menu.add_separator()
        file_menu.add_command(label="Export YAML", command=self.export_yaml, accelerator="Ctrl+E")
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # Edit menu
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Undo", command=self.undo, accelerator="Ctrl+Z")
        edit_menu.add_command(label="Redo", command=self.redo, accelerator="Ctrl+Y")
        edit_menu.add_separator()
        edit_menu.add_command(label="Copy", command=self.copy_widget, accelerator="Ctrl+C")
        edit_menu.add_command(label="Paste", command=self.paste_widget, accelerator="Ctrl+V")
        edit_menu.add_command(label="Delete", command=self.delete_widget, accelerator="Delete")
        edit_menu.add_separator()
        edit_menu.add_command(label="Select All", command=self.select_all, accelerator="Ctrl+A")
        
        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Zoom In", command=self.zoom_in, accelerator="Ctrl++")
        view_menu.add_command(label="Zoom Out", command=self.zoom_out, accelerator="Ctrl+-")
        view_menu.add_command(label="Zoom to Fit", command=self.zoom_fit, accelerator="Ctrl+0")
        view_menu.add_separator()
        view_menu.add_command(label="Show Grid", command=self.toggle_grid)
        view_menu.add_command(label="Snap to Grid", command=self.toggle_snap)
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Align Left", command=lambda: self.align_widgets('left'))
        tools_menu.add_command(label="Align Center", command=lambda: self.align_widgets('center'))
        tools_menu.add_command(label="Align Right", command=lambda: self.align_widgets('right'))
        tools_menu.add_separator()
        tools_menu.add_command(label="Align Top", command=lambda: self.align_widgets('top'))
        tools_menu.add_command(label="Align Middle", command=lambda: self.align_widgets('middle'))
        tools_menu.add_command(label="Align Bottom", command=lambda: self.align_widgets('bottom'))
        tools_menu.add_separator()
        tools_menu.add_command(label="Distribute Horizontally", command=lambda: self.distribute_widgets('horizontal'))
        tools_menu.add_command(label="Distribute Vertically", command=lambda: self.distribute_widgets('vertical'))
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)
        help_menu.add_command(label="LVGL Documentation", command=self.open_lvgl_docs)
        
        # Bind keyboard shortcuts
        self.root.bind('<Control-n>', lambda e: self.new_project())
        self.root.bind('<Control-o>', lambda e: self.open_project())
        self.root.bind('<Control-s>', lambda e: self.save_project())
        self.root.bind('<Control-Shift-S>', lambda e: self.save_project_as())
        self.root.bind('<Control-e>', lambda e: self.export_yaml())
        self.root.bind('<Control-z>', lambda e: self.undo())
        self.root.bind('<Control-y>', lambda e: self.redo())
        self.root.bind('<Control-c>', lambda e: self.copy_widget())
        self.root.bind('<Control-v>', lambda e: self.paste_widget())
        self.root.bind('<Delete>', lambda e: self.delete_widget())
        self.root.bind('<Control-a>', lambda e: self.select_all())
        self.root.bind('<Control-plus>', lambda e: self.zoom_in())
        self.root.bind('<Control-minus>', lambda e: self.zoom_out())
        self.root.bind('<Control-0>', lambda e: self.zoom_fit())
        
    # Event handlers
    def on_widget_selected(self, widget_type: str):
        """Handle widget selection from library"""
        self.canvas_editor.start_placing_widget(widget_type)
        
    def on_widget_selected_canvas(self, widget: Optional[LVGLWidget]):
        """Handle widget selection from canvas"""
        self.property_panel.set_widget(widget)
        
    def on_property_changed(self, widget: LVGLWidget, property_name: str, value: Any):
        """Handle property changes"""
        if hasattr(widget, property_name):
            setattr(widget, property_name, value)
            self.canvas_editor.update_widget_display(widget)
            self.update_live_preview()
            
    def on_widgets_changed(self):
        """Handle when widgets are modified"""
        # Could implement undo/redo here
        self.update_live_preview()
        self.update_project_tree()
        
    def on_page_changed(self, page_id: str, page_info: dict):
        """Handle page selection change"""
        if self.canvas_editor:
            self.canvas_editor.set_current_page(page_id)
        self.device_state['current_page'] = page_id
        
        # Update current page label if it exists
        if hasattr(self, 'current_page_label'):
            self.current_page_label.config(text=page_id)
            
        self.update_live_preview()
        self.update_project_tree()
        
    def on_tree_select(self, event):
        """Handle tree selection"""
        selection = self.project_tree.selection()
        if selection:
            item = selection[0]
            item_data = self.project_tree.item(item)
            
            # Check if it's a widget
            if 'widget_' in item:
                # Find and select the widget
                widget_id = item_data['text']
                self.select_widget_by_id(widget_id)
            elif 'page_' in item:
                # Switch to page
                page_id = item_data['text']
                if hasattr(self, 'page_manager'):
                    self.page_manager.select_page(page_id)
                    
    def on_tree_double_click(self, event):
        """Handle tree double-click"""
        selection = self.project_tree.selection()
        if selection:
            item = selection[0]
            item_data = self.project_tree.item(item)
            
            if 'widget_' in item:
                # Edit widget properties - focus on the widget
                widget_id = item_data['text']
                self.select_widget_by_id(widget_id)
        
    def update_display_config(self, key: str, value: str):
        """Update display configuration"""
        try:
            if key in ['width', 'height', 'color_depth']:
                self.display_config[key] = int(value)
            else:
                self.display_config[key] = value
            
            if key in ['width', 'height']:
                self.canvas_editor.update_display_size(self.display_config['width'], self.display_config['height'])
                self.live_preview.set_display_config(self.display_config)
        except ValueError:
            pass  # Invalid input, ignore
            
    def update_live_preview(self):
        """Update the live preview with current data"""
        if hasattr(self, 'device_canvas') and hasattr(self, 'canvas_editor'):
            self.update_device_preview()
            
    def update_project_tree(self):
        """Update the project tree view"""
        if not hasattr(self, 'project_tree'):
            return
            
        # Clear existing items
        for item in self.project_tree.get_children():
            self.project_tree.delete(item)
            
        if not hasattr(self, 'canvas_editor') or not hasattr(self, 'page_manager') or not self.page_manager:
            return
            
        # Add display settings node
        display_node = self.project_tree.insert("", "end", "display", 
                                               text="Display", 
                                               values=("Config", f"{self.display_config['width']}x{self.display_config['height']}"))
        
        # Add pages
        pages_data = self.page_manager.get_all_pages()
        for page_id, page_info in pages_data.items():
            page_node = self.project_tree.insert("", "end", f"page_{page_id}",
                                                text=page_id,
                                                values=("Page", page_info.get('name', page_id)))
            
            # Add widgets for this page
            if self.canvas_editor:
                widgets = self.canvas_editor.get_widgets_for_page(page_id)
                for widget_data in widgets:
                    widget_id = widget_data.get('id', 'unknown')
                    widget_type = widget_data.get('widget_type', 'widget')
                    size_info = f"{widget_data.get('width', 0)}x{widget_data.get('height', 0)}"
                    
                    self.project_tree.insert(page_node, "end", f"widget_{widget_id}",
                                           text=widget_id,
                                           values=(widget_type, size_info))
                                       
        # Expand all nodes
        for item in self.project_tree.get_children():
            self.project_tree.item(item, open=True)
            
    def select_widget_by_id(self, widget_id: str):
        """Select a widget by its ID"""
        if hasattr(self, 'canvas_editor'):
            # Find widget in current page
            current_page = self.canvas_editor.current_page
            if current_page in self.canvas_editor.widgets:
                for widget in self.canvas_editor.widgets[current_page]:
                    if widget.id == widget_id:
                        self.canvas_editor.selected_widgets = [widget]
                        self.canvas_editor.draw_display()
                        self.property_panel.set_widget(widget)
                        break
                        
    # Device Preview Methods
    def update_preview_scale(self):
        """Update preview scale"""
        self.update_device_preview()
        
    def refresh_device_preview(self):
        """Refresh the device preview"""
        self.update_device_preview()
        
    def reset_device_state(self):
        """Reset device state to defaults"""
        self.device_state = {
            'current_page': self.device_state.get('current_page', 'main_page'),
            'widget_states': {},
            'slider_values': {},
            'switch_states': {},
            'checkbox_states': {},
            'input_values': {},
            'drag_widget': None,
            'drag_start': None
        }
        self.update_device_preview()
        
    def update_device_preview(self):
        """Update the device preview to look and behave like a real LVGL device"""
        if not hasattr(self, 'device_canvas') or not hasattr(self, 'preview_scale_var'):
            return
            
        try:
            self.device_canvas.delete("all")
            
            # Get current scale
            scale = self.preview_scale_var.get()
            width = int(self.display_config['width'] * scale)
            height = int(self.display_config['height'] * scale)
            
            # Device bezel/frame
            bezel_thickness = int(20 * scale)
            total_width = width + 2 * bezel_thickness
            total_height = height + 2 * bezel_thickness
            
            # Set canvas scroll region
            self.device_canvas.configure(scrollregion=(0, 0, total_width, total_height))
            
            # Draw device frame
            self.device_canvas.create_rectangle(
                0, 0, total_width, total_height,
                fill='#2d2d2d', outline='#404040', width=2,
                tags="device_frame"
            )
            
            # Draw screen area
            self.device_canvas.create_rectangle(
                bezel_thickness, bezel_thickness,
                bezel_thickness + width, bezel_thickness + height,
                fill='#000000', outline='#666666', width=1,
                tags="screen_area"
            )
            
            # Get current page data
            current_page = self.device_state['current_page']
            if hasattr(self, 'canvas_editor') and hasattr(self, 'page_manager') and self.page_manager and self.canvas_editor:
                pages_data = self.page_manager.get_all_pages()
                
                # Draw page background
                if current_page in pages_data:
                    page_info = pages_data[current_page]
                    bg_color = page_info.get('background_color', '#000000')
                    
                    self.device_canvas.create_rectangle(
                        bezel_thickness + 1, bezel_thickness + 1,
                        bezel_thickness + width - 1, bezel_thickness + height - 1,
                        fill=bg_color, outline='',
                        tags="page_background"
                    )
                
                # Draw widgets
                widgets = self.canvas_editor.get_widgets_for_page(current_page)
                for widget_data in widgets:
                    self.draw_device_widget(widget_data, bezel_thickness, scale)
                    
        except Exception as e:
            print(f"Error updating device preview: {e}")
            import traceback
            traceback.print_exc()
                
    def draw_device_widget(self, widget_data: dict, offset: int, scale: float):
        """Draw a widget on the device preview with full interactivity"""
        widget_type = widget_data.get('widget_type', 'label')
        widget_id = widget_data.get('id', 'unknown')
        
        # Calculate position and size with proper type conversion
        try:
            x_val = widget_data.get('x', 0)
            y_val = widget_data.get('y', 0)
            width_val = widget_data.get('width', 100)
            height_val = widget_data.get('height', 30)
            align = widget_data.get('align', None)
            
            # Handle SIZE_CONTENT and convert to numbers
            def convert_size_value(val, widget_data, is_width=True):
                if val == "SIZE_CONTENT":
                    # Calculate content-based size for different widget types
                    if widget_type == "label":
                        if is_width:
                            text = widget_data.get('text', 'Label')
                            return max(len(text) * 8, 50)  # Approximate text width
                        else:
                            return 20  # Single line text height
                    elif widget_type == "button":
                        if is_width:
                            text = widget_data.get('text', 'Button')
                            return max(len(text) * 10 + 20, 80)  # Button padding
                        else:
                            return 40  # Standard button height
                    elif widget_type == "image":
                        return 64  # Default image size for both width and height
                    else:
                        return 100 if is_width else 30  # Default sizes
                else:
                    return float(str(val))
            
            # Convert size values with SIZE_CONTENT handling
            width = int(convert_size_value(width_val, widget_data, True) * scale)
            height = int(convert_size_value(height_val, widget_data, False) * scale)
            
            # Ensure minimum sizes
            width = max(1, width)
            height = max(1, height)
            
            # Handle position calculation with alignment
            if align and align != "TOP_LEFT":
                # Calculate base position from alignment
                display_width = int(self.display_config['width'] * scale)
                display_height = int(self.display_config['height'] * scale)
                
                # Base positions for different alignments
                if align == "CENTER":
                    base_x = (display_width - width) // 2
                    base_y = (display_height - height) // 2
                elif align == "TOP_MID":
                    base_x = (display_width - width) // 2
                    base_y = 0
                elif align == "TOP_RIGHT":
                    base_x = display_width - width
                    base_y = 0
                elif align == "BOTTOM_LEFT":
                    base_x = 0
                    base_y = display_height - height
                elif align == "BOTTOM_MID":
                    base_x = (display_width - width) // 2
                    base_y = display_height - height
                elif align == "BOTTOM_RIGHT":
                    base_x = display_width - width
                    base_y = display_height - height
                elif align == "LEFT_MID":
                    base_x = 0
                    base_y = (display_height - height) // 2
                elif align == "RIGHT_MID":
                    base_x = display_width - width
                    base_y = (display_height - height) // 2
                else:  # TOP_LEFT or unknown
                    base_x = 0
                    base_y = 0
                
                # Add offsets
                x = offset + base_x + int(float(str(x_val)) * scale)
                y = offset + base_y + int(float(str(y_val)) * scale)
            else:
                # Absolute positioning
                x = offset + int(float(str(x_val)) * scale)
                y = offset + int(float(str(y_val)) * scale)
            
        except (ValueError, TypeError) as e:
            print(f"Error converting widget dimensions for {widget_id}: {e}")
            # Use safe defaults
            x = offset + 10
            y = offset + 10
            width = int(100 * scale)
            height = int(30 * scale)
        
        # Get widget state
        widget_state = self.device_state['widget_states'].get(widget_id, {})
        
        # Draw based on widget type
        if widget_type == 'button':
            self.draw_device_button(widget_data, x, y, width, height, widget_state)
        elif widget_type == 'slider':
            self.draw_device_slider(widget_data, x, y, width, height)
        elif widget_type == 'switch':
            self.draw_device_switch(widget_data, x, y, width, height)
        elif widget_type == 'checkbox':
            self.draw_device_checkbox(widget_data, x, y, width, height)
        elif widget_type == 'image':
            self.draw_device_image(widget_data, x, y, width, height)
        elif widget_type == 'label':
            self.draw_device_label(widget_data, x, y, width, height)
        elif widget_type == 'bar':
            self.draw_device_bar(widget_data, x, y, width, height)
        elif widget_type == 'arc':
            self.draw_device_arc(widget_data, x, y, width, height)
        elif widget_type == 'led':
            self.draw_device_led(widget_data, x, y, width, height)
        elif widget_type == 'dropdown':
            self.draw_device_dropdown(widget_data, x, y, width, height)
        elif widget_type == 'textarea':
            self.draw_device_textarea(widget_data, x, y, width, height)
        else:
            self.draw_device_generic(widget_data, x, y, width, height)
            
    def draw_device_button(self, widget_data: dict, x: int, y: int, width: int, height: int, state: dict):
        """Draw an interactive button on device preview"""
        widget_id = widget_data.get('id', 'button')
        text = widget_data.get('text', 'Button')
        bg_color = widget_data.get('bg_color', '#4CAF50')
        text_color = widget_data.get('text_color', '#FFFFFF')
        
        # Button state
        pressed = state.get('pressed', False)
        
        # Draw button with realistic appearance
        if pressed:
            # Pressed state - darker and slightly offset
            press_offset = 2
            button_color = self.darken_color(bg_color)
            self.device_canvas.create_rectangle(
                x + press_offset, y + press_offset, x + width, y + height,
                fill=button_color, outline='#FFFFFF', width=1,
                tags=f"device_widget_{widget_id}"
            )
        else:
            # Normal state with shadow
            self.device_canvas.create_rectangle(
                x + 2, y + 2, x + width + 2, y + height + 2,
                fill='#333333', outline='',
                tags=f"device_widget_{widget_id}"
            )
            self.device_canvas.create_rectangle(
                x, y, x + width, y + height,
                fill=bg_color, outline='#FFFFFF', width=1,
                tags=f"device_widget_{widget_id}"
            )
            
            # Highlight
            if height > 10:
                highlight_height = max(2, height // 4)
                self.device_canvas.create_rectangle(
                    x + 2, y + 2, x + width - 2, y + highlight_height,
                    fill='white', stipple='gray50',
                    tags=f"device_widget_{widget_id}"
                )
        
        # Button text
        font_size = max(8, int(12 * self.preview_scale_var.get()))
        text_y_offset = 2 if pressed else 0
        self.device_canvas.create_text(
            x + width//2, y + height//2 + text_y_offset, text=text,
            font=('Arial', font_size, 'bold'), fill=text_color,
            tags=f"device_widget_{widget_id}_clickable"
        )
        
    def draw_device_slider(self, widget_data: dict, x: int, y: int, width: int, height: int):
        """Draw an interactive slider on device preview"""
        widget_id = widget_data.get('id', 'slider')
        value = self.device_state['slider_values'].get(widget_id, widget_data.get('value', 50))
        min_val = widget_data.get('min_value', 0)
        max_val = widget_data.get('max_value', 100)
        
        # Track
        track_height = max(4, int(8 * self.preview_scale_var.get()))
        track_y = y + height // 2 - track_height // 2
        margin = max(8, int(12 * self.preview_scale_var.get()))
        
        # Track background
        self.device_canvas.create_rectangle(
            x + margin, track_y, x + width - margin, track_y + track_height,
            fill='#444444', outline='#666666', width=1,
            tags=f"device_widget_{widget_id}"
        )
        
        # Track progress
        progress_ratio = (value - min_val) / (max_val - min_val) if max_val > min_val else 0
        progress_width = progress_ratio * (width - 2 * margin)
        self.device_canvas.create_rectangle(
            x + margin, track_y, x + margin + progress_width, track_y + track_height,
            fill='#2196F3', outline='',
            tags=f"device_widget_{widget_id}"
        )
        
        # Knob
        knob_x = x + margin + progress_width
        knob_size = max(12, int(18 * self.preview_scale_var.get()))
        
        # Knob shadow
        self.device_canvas.create_oval(
            knob_x - knob_size//2 + 1, track_y + track_height//2 - knob_size//2 + 1,
            knob_x + knob_size//2 + 1, track_y + track_height//2 + knob_size//2 + 1,
            fill='#333333', outline='',
            tags=f"device_widget_{widget_id}"
        )
        
        # Knob
        self.device_canvas.create_oval(
            knob_x - knob_size//2, track_y + track_height//2 - knob_size//2,
            knob_x + knob_size//2, track_y + track_height//2 + knob_size//2,
            fill='white', outline='#2196F3', width=2,
            tags=f"device_widget_{widget_id}_draggable"
        )
        
        # Value display
        if height > 25:
            font_size = max(8, int(10 * self.preview_scale_var.get()))
            self.device_canvas.create_text(
                x + width//2, y + height - 8, text=f"{int(value)}",
                font=('Arial', font_size), fill='#FFFFFF',
                tags=f"device_widget_{widget_id}"
            )
            
    def draw_device_switch(self, widget_data: dict, x: int, y: int, width: int, height: int):
        """Draw an interactive switch on device preview"""
        widget_id = widget_data.get('id', 'switch')
        state = self.device_state['switch_states'].get(widget_id, widget_data.get('state', False))
        
        # Switch dimensions
        switch_width = min(width - 8, int(60 * self.preview_scale_var.get()))
        switch_height = min(height - 8, int(30 * self.preview_scale_var.get()))
        switch_x = x + (width - switch_width) // 2
        switch_y = y + (height - switch_height) // 2
        
        # Track color animation
        track_color = '#4CAF50' if state else '#666666'
        
        # Track
        self.device_canvas.create_oval(
            switch_x, switch_y, switch_x + switch_width, switch_y + switch_height,
            fill=track_color, outline='#FFFFFF', width=1,
            tags=f"device_widget_{widget_id}_clickable"
        )
        
        # Knob with animation
        knob_size = switch_height - 6
        knob_x = switch_x + switch_width - knob_size - 3 if state else switch_x + 3
        
        # Knob shadow
        self.device_canvas.create_oval(
            knob_x + 1, switch_y + 3 + 1, knob_x + knob_size + 1, switch_y + knob_size + 3 + 1,
            fill='#333333', outline='',
            tags=f"device_widget_{widget_id}"
        )
        
        # Knob
        self.device_canvas.create_oval(
            knob_x, switch_y + 3, knob_x + knob_size, switch_y + knob_size + 3,
            fill='white', outline='#DDDDDD', width=1,
            tags=f"device_widget_{widget_id}_clickable"
        )
        
    def draw_device_checkbox(self, widget_data: dict, x: int, y: int, width: int, height: int):
        """Draw an interactive checkbox on device preview"""
        widget_id = widget_data.get('id', 'checkbox')
        checked = self.device_state['checkbox_states'].get(widget_id, widget_data.get('checked', False))
        text = widget_data.get('text', 'Checkbox')
        
        # Checkbox dimensions
        check_size = min(width//3, height - 6, int(24 * self.preview_scale_var.get()))
        check_x = x + 4
        check_y = y + (height - check_size) // 2
        
        # Checkbox colors
        bg_color = '#2196F3' if checked else '#444444'
        border_color = '#2196F3' if checked else '#CCCCCC'
        
        # Checkbox shadow
        self.device_canvas.create_rectangle(
            check_x + 1, check_y + 1, check_x + check_size + 1, check_y + check_size + 1,
            fill='#333333', outline='',
            tags=f"device_widget_{widget_id}"
        )
        
        # Checkbox
        self.device_canvas.create_rectangle(
            check_x, check_y, check_x + check_size, check_y + check_size,
            fill=bg_color, outline=border_color, width=2,
            tags=f"device_widget_{widget_id}_clickable"
        )
        
        # Checkmark
        if checked and check_size > 10:
            check_points = [
                check_x + check_size * 0.2, check_y + check_size * 0.5,
                check_x + check_size * 0.45, check_y + check_size * 0.7,
                check_x + check_size * 0.8, check_y + check_size * 0.3
            ]
            self.device_canvas.create_line(
                check_points, fill='white', width=max(2, int(3 * self.preview_scale_var.get())),
                capstyle='round', joinstyle='round',
                tags=f"device_widget_{widget_id}"
            )
            
        # Label
        if text and width > check_size + 15:
            font_size = max(8, int(11 * self.preview_scale_var.get()))
            self.device_canvas.create_text(
                check_x + check_size + 10, y + height//2,
                text=text, font=('Arial', font_size), fill='#FFFFFF', anchor='w',
                tags=f"device_widget_{widget_id}"
            )
            
    def draw_device_image(self, widget_data: dict, x: int, y: int, width: int, height: int):
        """Draw image widget on device preview"""
        widget_id = widget_data.get('id', 'image')
        src = widget_data.get('src', '')
        
        # Try to load image
        if src:
            try:
                cache_key = f"{src}_{width}_{height}"
                if cache_key in self.device_image_cache:
                    photo = self.device_image_cache[cache_key]
                else:
                    image_path = self.find_image_path(src)
                    if image_path and os.path.exists(image_path):
                        pil_image = Image.open(image_path)
                        pil_image = pil_image.resize((max(1, width - 4), max(1, height - 4)), 
                                                   Image.Resampling.LANCZOS)
                        photo = ImageTk.PhotoImage(pil_image)
                        self.device_image_cache[cache_key] = photo
                    else:
                        photo = None
                        
                if photo:
                    self.device_canvas.create_rectangle(
                        x, y, x + width, y + height,
                        fill='#222222', outline='#555555', width=1,
                        tags=f"device_widget_{widget_id}"
                    )
                    self.device_canvas.create_image(
                        x + width//2, y + height//2, image=photo,
                        tags=f"device_widget_{widget_id}"
                    )
                    return
            except Exception as e:
                print(f"Error loading image {src}: {e}")
        
        # Placeholder
        self.device_canvas.create_rectangle(
            x, y, x + width, y + height,
            fill='#333333', outline='#666666', width=1,
            tags=f"device_widget_{widget_id}"
        )
        
    def draw_device_label(self, widget_data: dict, x: int, y: int, width: int, height: int):
        """Draw label widget on device preview"""
        text = widget_data.get('text', 'Label')
        text_color = widget_data.get('text_color', '#FFFFFF')
        font_size = max(8, int(12 * self.preview_scale_var.get()))
        self.device_canvas.create_text(
            x + width//2, y + height//2, text=text,
            font=('Arial', font_size), fill=text_color,
            tags=f"device_widget_{widget_data.get('id', 'label')}"
        )
        
    def draw_device_bar(self, widget_data: dict, x: int, y: int, width: int, height: int):
        """Draw progress bar on device preview"""
        value = widget_data.get('value', 50)
        progress_width = (value / 100) * (width - 6)
        
        self.device_canvas.create_rectangle(
            x + 2, y + 2, x + width - 2, y + height - 2,
            fill='#333333', outline='#666666', width=1,
            tags=f"device_widget_{widget_data.get('id', 'bar')}"
        )
        
        if progress_width > 0:
            self.device_canvas.create_rectangle(
                x + 3, y + 3, x + 3 + progress_width, y + height - 3,
                fill='#4CAF50', outline='',
                tags=f"device_widget_{widget_data.get('id', 'bar')}"
            )
            
    def draw_device_arc(self, widget_data: dict, x: int, y: int, width: int, height: int):
        """Draw arc widget on device preview"""
        value = widget_data.get('value', 25)
        extent = (value / 100) * 270
        margin = max(4, int(6 * self.preview_scale_var.get()))
        
        self.device_canvas.create_arc(
            x + margin, y + margin, x + width - margin, y + height - margin,
            start=135, extent=extent, outline='#2196F3',
            width=max(4, int(8 * self.preview_scale_var.get())), style='arc',
            tags=f"device_widget_{widget_data.get('id', 'arc')}"
        )
        
    def draw_device_led(self, widget_data: dict, x: int, y: int, width: int, height: int):
        """Draw LED widget on device preview"""
        state = widget_data.get('state', True)
        color = widget_data.get('color', '#FF0000') if state else '#330000'
        led_size = min(width - 8, height - 8)
        led_x = x + (width - led_size) // 2
        led_y = y + (height - led_size) // 2
        
        self.device_canvas.create_oval(
            led_x, led_y, led_x + led_size, led_y + led_size,
            fill=color, outline='#666666', width=1,
            tags=f"device_widget_{widget_data.get('id', 'led')}"
        )
        
    def draw_device_dropdown(self, widget_data: dict, x: int, y: int, width: int, height: int):
        """Draw dropdown widget on device preview"""
        text = widget_data.get('text', 'Select...')
        
        self.device_canvas.create_rectangle(
            x, y, x + width, y + height,
            fill='#444444', outline='#CCCCCC', width=1,
            tags=f"device_widget_{widget_data.get('id', 'dropdown')}_clickable"
        )
        
        font_size = max(8, int(10 * self.preview_scale_var.get()))
        self.device_canvas.create_text(
            x + 10, y + height//2, text=text,
            font=('Arial', font_size), fill='#FFFFFF', anchor='w',
            tags=f"device_widget_{widget_data.get('id', 'dropdown')}"
        )
        
    def draw_device_textarea(self, widget_data: dict, x: int, y: int, width: int, height: int):
        """Draw textarea widget on device preview"""
        text_content = widget_data.get('text', 'Enter text...')
        
        self.device_canvas.create_rectangle(
            x, y, x + width, y + height,
            fill='#333333', outline='#666666', width=1,
            tags=f"device_widget_{widget_data.get('id', 'textarea')}_clickable"
        )
        
        if text_content and height > 20:
            font_size = max(8, int(10 * self.preview_scale_var.get()))
            self.device_canvas.create_text(
                x + 8, y + 8, text=text_content[:50] + "..." if len(text_content) > 50 else text_content,
                font=('Arial', font_size), fill='#FFFFFF', anchor='nw',
                tags=f"device_widget_{widget_data.get('id', 'textarea')}"
            )
            
    def draw_device_generic(self, widget_data: dict, x: int, y: int, width: int, height: int):
        """Draw generic widget on device preview"""
        widget_type = widget_data.get('widget_type', 'widget')
        
        self.device_canvas.create_rectangle(
            x, y, x + width, y + height,
            fill='#424242', outline='#666666', width=1,
            tags=f"device_widget_{widget_data.get('id', 'widget')}"
        )
        
        if height > 20:
            font_size = max(8, int(10 * self.preview_scale_var.get()))
            self.device_canvas.create_text(
                x + width//2, y + height//2, text=widget_type.title(),
                font=('Arial', font_size), fill='#FFFFFF',
                tags=f"device_widget_{widget_data.get('id', 'widget')}"
            )
            
    # Device interaction handlers
    def on_device_click(self, event):
        """Handle device preview clicks"""
        canvas_x = self.device_canvas.canvasx(event.x)
        canvas_y = self.device_canvas.canvasy(event.y)
        
        item = self.device_canvas.find_closest(canvas_x, canvas_y)[0]
        tags = self.device_canvas.gettags(item)
        
        for tag in tags:
            if '_clickable' in tag:
                widget_id = tag.replace('device_widget_', '').replace('_clickable', '')
                self.handle_device_widget_click(widget_id, canvas_x, canvas_y)
                break
            elif '_draggable' in tag:
                widget_id = tag.replace('device_widget_', '').replace('_draggable', '')
                self.device_state['drag_widget'] = widget_id
                self.device_state['drag_start'] = (canvas_x, canvas_y)
                break
                
    def on_device_drag(self, event):
        """Handle device preview dragging"""
        if self.device_state['drag_widget']:
            canvas_x = self.device_canvas.canvasx(event.x)
            canvas_y = self.device_canvas.canvasy(event.y)
            self.handle_device_widget_drag(self.device_state['drag_widget'], canvas_x, canvas_y)
            
    def on_device_release(self, event):
        """Handle device preview release"""
        self.device_state['drag_widget'] = None
        self.device_state['drag_start'] = None
        
    def on_device_canvas_configure(self, event):
        """Handle device canvas resize"""
        pass
        
    def handle_device_widget_click(self, widget_id: str, x: float, y: float):
        """Handle widget clicks in device preview"""
        # Find widget data
        widget_data = self.find_widget_data_by_id(widget_id)
        if not widget_data:
            return
            
        widget_type = widget_data.get('widget_type')
        
        if widget_type == 'button':
            # Button press animation
            self.device_state['widget_states'][widget_id] = {'pressed': True}
            self.update_device_preview()
            
            # Release after 100ms
            self.root.after(100, lambda: self.release_button(widget_id))
            
            # Handle button actions
            self.handle_button_actions(widget_data)
            
        elif widget_type == 'switch':
            current_state = self.device_state['switch_states'].get(widget_id, widget_data.get('state', False))
            self.device_state['switch_states'][widget_id] = not current_state
            self.update_device_preview()
            
        elif widget_type == 'checkbox':
            current_state = self.device_state['checkbox_states'].get(widget_id, widget_data.get('checked', False))
            self.device_state['checkbox_states'][widget_id] = not current_state
            self.update_device_preview()
            
    def handle_device_widget_drag(self, widget_id: str, x: float, y: float):
        """Handle widget dragging in device preview"""
        widget_data = self.find_widget_data_by_id(widget_id)
        if not widget_data:
            return
            
        widget_type = widget_data.get('widget_type')
        
        if widget_type == 'slider':
            # Calculate new slider value
            scale = self.preview_scale_var.get()
            bezel_thickness = int(20 * scale)
            widget_x = bezel_thickness + int(widget_data.get('x', 0) * scale)
            widget_width = int(widget_data.get('width', 100) * scale)
            margin = max(8, int(12 * scale))
            
            relative_x = x - widget_x - margin
            track_width = widget_width - 2 * margin
            
            if 0 <= relative_x <= track_width:
                ratio = relative_x / track_width
                min_val = widget_data.get('min_value', 0)
                max_val = widget_data.get('max_value', 100)
                new_value = min_val + ratio * (max_val - min_val)
                
                self.device_state['slider_values'][widget_id] = new_value
                self.update_device_preview()
                
    def handle_button_actions(self, widget_data: dict):
        """Handle button actions like page navigation"""
        actions = widget_data.get('actions', {})
        if 'on_click' in actions and 'then' in actions['on_click']:
            for action in actions['on_click']['then']:
                if 'lvgl.page.show' in action:
                    target_page = action['lvgl.page.show']
                    self.navigate_to_page(target_page)
                    
    def navigate_to_page(self, page_id: str):
        """Navigate to a specific page in device preview"""
        if hasattr(self, 'page_manager'):
            pages_data = self.page_manager.get_all_pages()
            if page_id in pages_data:
                self.device_state['current_page'] = page_id
                self.current_page_label.config(text=page_id)
                self.update_device_preview()
                print(f"Navigated to page: {page_id}")
                
    def release_button(self, widget_id: str):
        """Release button press state"""
        if widget_id in self.device_state['widget_states']:
            del self.device_state['widget_states'][widget_id]
        self.update_device_preview()
        
    def find_widget_data_by_id(self, widget_id: str) -> Optional[dict]:
        """Find widget data by ID"""
        if hasattr(self, 'canvas_editor'):
            current_page = self.device_state['current_page']
            widgets = self.canvas_editor.get_widgets_for_page(current_page)
            for widget_data in widgets:
                if widget_data.get('id') == widget_id:
                    return widget_data
        return None
        
    def find_image_path(self, src: str) -> Optional[str]:
        """Find image file path"""
        if os.path.isabs(src) and os.path.exists(src):
            return src
            
        base_paths = [
            os.getcwd(),
            os.path.join(os.getcwd(), 'images'),
            os.path.join(os.getcwd(), 'assets'),
            os.path.dirname(os.path.abspath(__file__))
        ]
        
        for base_path in base_paths:
            test_path = os.path.join(base_path, src)
            if os.path.exists(test_path):
                return test_path
        return None
        
    def darken_color(self, color: str, factor: float = 0.7) -> str:
        """Darken a hex color"""
        try:
            if color.startswith('#'):
                color = color[1:]
            r, g, b = int(color[:2], 16), int(color[2:4], 16), int(color[4:6], 16)
            r, g, b = int(r * factor), int(g * factor), int(b * factor)
            return f"#{r:02x}{g:02x}{b:02x}"
        except:
            return '#333333'
            
    # File operations
    def new_project(self):
        """Create a new project"""
        self.current_project = None
        if self.canvas_editor:
            self.canvas_editor.clear_all()
        
    def open_project(self):
        """Open an existing project"""
        filename = filedialog.askopenfilename(
            title="Open LVGL Project",
            filetypes=[("LVGL Project", "*.lvgl"), ("YAML files", "*.yaml"), ("All files", "*.*")]
        )
        if filename:
            try:
                with open(filename, 'r') as f:
                    if filename.endswith('.yaml'):
                        # Import from ESPHome YAML
                        self.import_from_yaml(f.read())
                    else:
                        # Load LVGL project file
                        project_data = json.load(f)
                        self.load_project(project_data)
                self.current_project = filename
            except Exception as e:
                messagebox.showerror("Error", f"Failed to open project: {str(e)}")
                
    def save_project(self):
        """Save the current project"""
        if self.current_project:
            self.save_project_to_file(self.current_project)
        else:
            self.save_project_as()
            
    def save_project_as(self):
        """Save the project with a new name"""
        filename = filedialog.asksaveasfilename(
            title="Save LVGL Project",
            defaultextension=".lvgl",
            filetypes=[("LVGL Project", "*.lvgl"), ("All files", "*.*")]
        )
        if filename:
            self.save_project_to_file(filename)
            self.current_project = filename
            
    def save_project_to_file(self, filename: str):
        """Save project data to file"""
        try:
            project_data = {
                'display_config': self.display_config,
                'pages': self.page_manager.get_pages_data(),
                'widgets': self.canvas_editor.get_widgets_data()
            }
            
            with open(filename, 'w') as f:
                json.dump(project_data, f, indent=2)
                
            messagebox.showinfo("Success", "Project saved successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save project: {str(e)}")
            
    def export_yaml(self):
        """Export the current project as ESPHome YAML"""
        filename = filedialog.asksaveasfilename(
            title="Export ESPHome YAML",
            defaultextension=".yaml",
            filetypes=[("YAML files", "*.yaml"), ("All files", "*.*")]
        )
        if filename:
            try:
                yaml_content = self.yaml_generator.generate_yaml(
                    self.display_config,
                    self.page_manager.get_pages_data(),
                    self.canvas_editor.get_widgets_data()
                )
                
                with open(filename, 'w') as f:
                    f.write(yaml_content)
                    
                messagebox.showinfo("Success", "YAML exported successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export YAML: {str(e)}")
                
    # Edit operations
    def undo(self):
        """Undo the last operation"""
        # TODO: Implement undo/redo
        pass
        
    def redo(self):
        """Redo the last undone operation"""
        # TODO: Implement undo/redo
        pass
        
    def copy_widget(self):
        """Copy selected widgets"""
        self.canvas_editor.copy_selected()
        
    def paste_widget(self):
        """Paste copied widgets"""
        self.canvas_editor.paste()
        
    def delete_widget(self):
        """Delete selected widgets"""
        self.canvas_editor.delete_selected()
        
    def select_all(self):
        """Select all widgets"""
        self.canvas_editor.select_all()
        
    # View operations
    def zoom_in(self):
        """Zoom in on the canvas"""
        self.canvas_editor.zoom_in()
        
    def zoom_out(self):
        """Zoom out on the canvas"""
        self.canvas_editor.zoom_out()
        
    def zoom_fit(self):
        """Zoom to fit the display"""
        self.canvas_editor.zoom_fit()
        
    def toggle_grid(self):
        """Toggle grid visibility"""
        self.canvas_editor.toggle_grid()
        
    def toggle_snap(self):
        """Toggle snap to grid"""
        self.canvas_editor.toggle_snap()
        
    # Tool operations
    def align_widgets(self, alignment: str):
        """Align selected widgets"""
        self.canvas_editor.align_widgets(alignment)
        
    def distribute_widgets(self, direction: str):
        """Distribute selected widgets"""
        self.canvas_editor.distribute_widgets(direction)
        
    # Utility methods
    def load_project(self, project_data: dict):
        """Load project from data"""
        # Load display config
        if 'display_config' in project_data:
            self.display_config.update(project_data['display_config'])
            
        # Load pages
        if 'pages' in project_data:
            self.page_manager.load_pages(project_data['pages'])
            
        # Load widgets
        if 'widgets' in project_data:
            self.canvas_editor.load_widgets(project_data['widgets'])
            
    def import_from_yaml(self, yaml_content: str):
        """Import project from ESPHome YAML"""
        try:
            yaml_data = yaml.safe_load(yaml_content)
            
            # Extract LVGL configuration
            lvgl_config = yaml_data.get('lvgl', {})
            
            # Import display configuration
            if 'displays' in lvgl_config:
                display = lvgl_config['displays'][0] if lvgl_config['displays'] else {}
                if 'width' in display:
                    self.display_config['width'] = display['width']
                if 'height' in display:
                    self.display_config['height'] = display['height']
                if 'color_depth' in display:
                    self.display_config['color_depth'] = display['color_depth']
                    
            # Import pages
            pages_data = {}
            widgets_data = {}
            
            if 'pages' in lvgl_config:
                for page_config in lvgl_config['pages']:
                    page_id = page_config.get('id', 'page')
                    pages_data[page_id] = {
                        'name': page_config.get('id', page_id),
                        'background_color': page_config.get('bg_color', '#000000')
                    }
                    
                    # Extract widgets from page
                    page_widgets = []
                    if 'widgets' in page_config:
                        for widget_config in page_config['widgets']:
                            widget_data = self.convert_yaml_widget_to_data(widget_config)
                            if widget_data:
                                page_widgets.append(widget_data)
                                
                    widgets_data[page_id] = page_widgets
                    
            # Load the imported data
            if pages_data:
                self.page_manager.load_pages(pages_data)
            if widgets_data:
                self.canvas_editor.load_widgets(widgets_data)
                
            # Update UI
            self.update_project_tree()
            self.update_device_preview()
            
            messagebox.showinfo("Import Successful", "YAML file imported successfully!")
            
        except Exception as e:
            messagebox.showerror("Import Error", f"Failed to import YAML: {str(e)}")
            
    def convert_yaml_widget_to_data(self, yaml_widget: dict) -> Optional[dict]:
        """Convert YAML widget configuration to internal data format"""
        widget_type = yaml_widget.get('type', 'obj')
        
        # Map YAML widget types to internal types
        type_mapping = {
            'obj': 'label',
            'label': 'label',
            'btn': 'button',
            'slider': 'slider',
            'switch': 'switch',
            'checkbox': 'checkbox',
            'img': 'image',
            'bar': 'bar',
            'arc': 'arc',
            'led': 'led',
            'dropdown': 'dropdown',
            'textarea': 'textarea'
        }
        
        internal_type = type_mapping.get(widget_type, 'label')
        
        widget_data = {
            'id': yaml_widget.get('id', f"{internal_type}_1"),
            'widget_type': internal_type,
            'x': yaml_widget.get('x', 0),
            'y': yaml_widget.get('y', 0),
            'width': yaml_widget.get('width', 100),
            'height': yaml_widget.get('height', 30),
            'text': yaml_widget.get('text', ''),
            'bg_color': yaml_widget.get('bg_color', '#FFFFFF'),
            'text_color': yaml_widget.get('text_color', '#000000'),
        }
        
        # Widget-specific properties
        if internal_type == 'slider':
            widget_data.update({
                'min_value': yaml_widget.get('range_min', 0),
                'max_value': yaml_widget.get('range_max', 100),
                'value': yaml_widget.get('value', 50)
            })
        elif internal_type == 'image':
            widget_data['src'] = yaml_widget.get('src', '')
        elif internal_type == 'switch':
            widget_data['state'] = yaml_widget.get('state', False)
        elif internal_type == 'checkbox':
            widget_data['checked'] = yaml_widget.get('checked', False)
        elif internal_type == 'bar':
            widget_data.update({
                'min_value': yaml_widget.get('range_min', 0),
                'max_value': yaml_widget.get('range_max', 100),
                'value': yaml_widget.get('value', 50)
            })
        elif internal_type == 'arc':
            widget_data.update({
                'min_value': yaml_widget.get('range_min', 0),
                'max_value': yaml_widget.get('range_max', 100),
                'value': yaml_widget.get('value', 25)
            })
        elif internal_type == 'led':
            widget_data.update({
                'state': yaml_widget.get('state', True),
                'color': yaml_widget.get('color', '#FF0000')
            })
            
        return widget_data
        
    def show_about(self):
        """Show about dialog"""
        messagebox.showinfo(
            "About LVGL Editor",
            "LVGL Layout Editor for ESPHome\n\n"
            "A comprehensive tool for creating LVGL layouts\n"
            "compatible with ESPHome YAML configuration.\n\n"
            "Features:\n"
            "• Visual drag-and-drop interface\n"
            "• Complete widget library\n"
            "• Multi-page support\n"
            "• ESPHome YAML export\n"
            "• Interactive preview\n\n"
            "Version 1.0"
        )
        
    def open_lvgl_docs(self):
        """Open LVGL documentation"""
        import webbrowser
        webbrowser.open("https://esphome.io/components/lvgl/")
        
    def run(self):
        """Start the application"""
        self.root.mainloop()


if __name__ == "__main__":
    app = LVGLEditor()
    app.run()
