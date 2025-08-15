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
        
        # Initialize UI
        self.create_ui()
        self.create_menu()
        
        # Load default project
        self.new_project()
        
    def create_ui(self):
        """Create the main user interface"""
        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create paned windows for layout
        # Horizontal paned window (left sidebar | main content)
        h_paned = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        h_paned.pack(fill=tk.BOTH, expand=True)
        
        # Left sidebar frame
        left_frame = ttk.Frame(h_paned, width=300)
        h_paned.add(left_frame, weight=0)
        
        # Right content area (vertical split)
        right_paned = ttk.PanedWindow(h_paned, orient=tk.VERTICAL)
        h_paned.add(right_paned, weight=1)
        
        # Create widget library in left sidebar
        self.widget_library = WidgetLibrary(left_frame, self.on_widget_selected)
        
        # Create page manager in left sidebar  
        page_frame = ttk.LabelFrame(left_frame, text="Pages", padding=5)
        page_frame.pack(fill=tk.X, pady=5)
        self.page_manager = PageManager(page_frame, self.on_page_changed)
        
        # Display settings in left sidebar
        display_frame = ttk.LabelFrame(left_frame, text="Display Settings", padding=5)
        display_frame.pack(fill=tk.X, pady=5)
        self.create_display_settings(display_frame)
        
        # Canvas editor in top right
        canvas_frame = ttk.Frame(right_paned)
        right_paned.add(canvas_frame, weight=2)
        
        self.canvas_editor = CanvasEditor(
            canvas_frame, 
            self.display_config,
            self.on_widget_selected_canvas,
            self.on_widgets_changed
        )
        
        # Property panel in bottom right
        property_frame = ttk.Frame(right_paned, height=300)
        right_paned.add(property_frame, weight=1)
        
        self.property_panel = PropertyPanel(
            property_frame,
            self.on_property_changed
        )
        
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
            
    def on_widgets_changed(self):
        """Handle when widgets are modified"""
        # Could implement undo/redo here
        pass
        
    def on_page_changed(self, page_id: str, page_info: dict):
        """Handle page selection change"""
        if self.canvas_editor:
            self.canvas_editor.set_current_page(page_id)
        
    def update_display_config(self, key: str, value: str):
        """Update display configuration"""
        try:
            if key in ['width', 'height', 'color_depth']:
                self.display_config[key] = int(value)
            else:
                self.display_config[key] = value
            
            if key in ['width', 'height']:
                self.canvas_editor.update_display_size(self.display_config['width'], self.display_config['height'])
        except ValueError:
            pass  # Invalid input, ignore
            
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
        # TODO: Implement YAML import
        pass
        
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
