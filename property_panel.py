"""
Property Panel for editing widget properties
"""

import tkinter as tk
from tkinter import ttk, colorchooser, filedialog
from typing import Dict, List, Any, Optional, Callable
from widgets import LVGLWidget, ALIGN_OPTIONS, COLORS, FONT_OPTIONS

class PropertyPanel:
    """Panel for editing widget properties"""
    
    def __init__(self, parent, change_callback: Callable):
        self.parent = parent
        self.change_callback = change_callback
        self.current_widget = None
        
        # Property variables
        self.property_vars = {}
        
        # Create UI
        self.create_ui()
        
    def create_ui(self):
        """Create the property panel UI"""
        # Main scrollable frame
        main_frame = ttk.Frame(self.parent)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.title_label = ttk.Label(title_frame, text="Properties", font=('Arial', 12, 'bold'))
        self.title_label.pack(side=tk.LEFT)
        
        # Scrollable content
        canvas = tk.Canvas(main_frame)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Bind mousewheel
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind("<MouseWheel>", _on_mousewheel)
        
        # Initial empty state
        self.show_empty_state()
        
    def show_empty_state(self):
        """Show empty state when no widget is selected"""
        self.clear_properties()
        ttk.Label(self.scrollable_frame, text="No widget selected", 
                 foreground="gray").pack(pady=20)
                 
    def clear_properties(self):
        """Clear all property controls"""
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self.property_vars.clear()
        
    def set_widget(self, widget: Optional[LVGLWidget]):
        """Set the widget to edit"""
        self.current_widget = widget
        
        if widget is None:
            self.show_empty_state()
            return
            
        self.title_label.config(text=f"Properties - {widget.widget_type.title()}")
        self.create_property_controls()
        
    def create_property_controls(self):
        """Create property controls for the current widget"""
        self.clear_properties()
        
        if not self.current_widget:
            return
            
        # Basic properties section
        self.create_section("Basic", [
            ('id', 'ID', 'string'),
            ('x', 'X Position', 'int'),
            ('y', 'Y Position', 'int'),
            ('width', 'Width', 'size'),
            ('height', 'Height', 'size'),
            ('align', 'Alignment', 'align'),
        ])
        
        # Style properties section
        self.create_section("Appearance", [
            ('bg_color', 'Background Color', 'color'),
            ('bg_opa', 'Background Opacity', 'opacity'),
            ('border_width', 'Border Width', 'int'),
            ('border_color', 'Border Color', 'color'),
            ('border_opa', 'Border Opacity', 'opacity'),
            ('radius', 'Corner Radius', 'int'),
        ])
        
        # Padding section
        self.create_section("Padding", [
            ('pad_all', 'All Sides', 'int'),
            ('pad_top', 'Top', 'int'),
            ('pad_bottom', 'Bottom', 'int'),
            ('pad_left', 'Left', 'int'),
            ('pad_right', 'Right', 'int'),
        ])
        
        # Flags section
        self.create_section("Behavior", [
            ('hidden', 'Hidden', 'bool'),
            ('clickable', 'Clickable', 'bool'),
            ('checkable', 'Checkable', 'bool'),
            ('scrollable', 'Scrollable', 'bool'),
        ])
        
        # State section
        self.create_section("State", [
            ('checked', 'Checked', 'bool'),
            ('disabled', 'Disabled', 'bool'),
        ])
        
        # Widget-specific properties
        self.create_widget_specific_properties()
        
        # Actions section
        self.create_actions_section()
        
    def create_section(self, title: str, properties: List[tuple]):
        """Create a property section"""
        # Section frame
        section_frame = ttk.LabelFrame(self.scrollable_frame, text=title, padding=5)
        section_frame.pack(fill=tk.X, pady=5)
        
        # Create property controls
        for prop_name, display_name, prop_type in properties:
            self.create_property_control(section_frame, prop_name, display_name, prop_type)
            
    def create_property_control(self, parent, prop_name: str, display_name: str, prop_type: str):
        """Create a single property control"""
        if not hasattr(self.current_widget, prop_name):
            return
            
        # Property frame
        prop_frame = ttk.Frame(parent)
        prop_frame.pack(fill=tk.X, pady=2)
        
        # Label
        ttk.Label(prop_frame, text=f"{display_name}:", width=15).pack(side=tk.LEFT, anchor='w')
        
        # Get current value
        current_value = getattr(self.current_widget, prop_name)
        
        # Create appropriate control based on type
        if prop_type == 'string':
            var = tk.StringVar(value=str(current_value))
            entry = ttk.Entry(prop_frame, textvariable=var)
            entry.pack(side=tk.RIGHT, fill=tk.X, expand=True)
            var.trace('w', lambda *args: self.on_property_changed(prop_name, var.get()))
            
        elif prop_type == 'int':
            var = tk.StringVar(value=str(current_value))
            entry = ttk.Entry(prop_frame, textvariable=var, width=10)
            entry.pack(side=tk.RIGHT)
            var.trace('w', lambda *args: self.on_int_property_changed(prop_name, var.get()))
            
        elif prop_type == 'size':
            var = tk.StringVar(value=str(current_value))
            frame = ttk.Frame(prop_frame)
            frame.pack(side=tk.RIGHT, fill=tk.X, expand=True)
            
            entry = ttk.Entry(frame, textvariable=var, width=10)
            entry.pack(side=tk.LEFT)
            
            if prop_name in ['width', 'height']:
                ttk.Button(frame, text="Auto", width=6,
                          command=lambda: self.set_size_auto(prop_name, var)).pack(side=tk.LEFT, padx=(5, 0))
                          
            var.trace('w', lambda *args: self.on_size_property_changed(prop_name, var.get()))
            
        elif prop_type == 'color':
            var = tk.StringVar(value=str(current_value))
            frame = ttk.Frame(prop_frame)
            frame.pack(side=tk.RIGHT, fill=tk.X, expand=True)
            
            entry = ttk.Entry(frame, textvariable=var, width=10)
            entry.pack(side=tk.LEFT)
            
            color_button = ttk.Button(frame, text="...", width=3,
                                    command=lambda: self.choose_color(var))
            color_button.pack(side=tk.LEFT, padx=(2, 0))
            
            var.trace('w', lambda *args: self.on_property_changed(prop_name, var.get()))
            
        elif prop_type == 'opacity':
            var = tk.StringVar(value=str(current_value))
            frame = ttk.Frame(prop_frame)
            frame.pack(side=tk.RIGHT, fill=tk.X, expand=True)
            
            combo = ttk.Combobox(frame, textvariable=var, width=10,
                               values=['TRANSP', 'COVER', '0%', '25%', '50%', '75%', '100%'])
            combo.pack(side=tk.LEFT)
            var.trace('w', lambda *args: self.on_property_changed(prop_name, var.get()))
            
        elif prop_type == 'align':
            var = tk.StringVar(value=str(current_value))
            combo = ttk.Combobox(prop_frame, textvariable=var, values=ALIGN_OPTIONS, width=15)
            combo.pack(side=tk.RIGHT)
            var.trace('w', lambda *args: self.on_property_changed(prop_name, var.get()))
            
        elif prop_type == 'bool':
            var = tk.BooleanVar(value=bool(current_value))
            check = ttk.Checkbutton(prop_frame, variable=var,
                                  command=lambda: self.on_property_changed(prop_name, var.get()))
            check.pack(side=tk.RIGHT)
            
        elif prop_type == 'font':
            var = tk.StringVar(value=str(current_value))
            combo = ttk.Combobox(prop_frame, textvariable=var, values=FONT_OPTIONS, width=15)
            combo.pack(side=tk.RIGHT)
            var.trace('w', lambda *args: self.on_property_changed(prop_name, var.get()))
            
        elif prop_type == 'list':
            var = tk.StringVar(value=', '.join(current_value) if isinstance(current_value, list) else str(current_value))
            entry = ttk.Entry(prop_frame, textvariable=var)
            entry.pack(side=tk.RIGHT, fill=tk.X, expand=True)
            var.trace('w', lambda *args: self.on_list_property_changed(prop_name, var.get()))
            
        elif prop_type == 'file':
            var = tk.StringVar(value=str(current_value))
            frame = ttk.Frame(prop_frame)
            frame.pack(side=tk.RIGHT, fill=tk.X, expand=True)
            
            entry = ttk.Entry(frame, textvariable=var)
            entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
            
            browse_button = ttk.Button(frame, text="Browse...", width=10,
                                     command=lambda: self.choose_file(var))
            browse_button.pack(side=tk.LEFT, padx=(2, 0))
            
            var.trace('w', lambda *args: self.on_property_changed(prop_name, var.get()))
            
        else:
            # Default to string for unknown types
            var = tk.StringVar(value=str(current_value))
            entry = ttk.Entry(prop_frame, textvariable=var)
            entry.pack(side=tk.RIGHT, fill=tk.X, expand=True)
            var.trace('w', lambda *args: self.on_property_changed(prop_name, var.get()))
            
        # Store variable reference
        self.property_vars[prop_name] = var
        
    def create_widget_specific_properties(self):
        """Create widget-specific property controls"""
        if not self.current_widget:
            return
            
        widget_type = self.current_widget.widget_type
        
        if widget_type == 'label':
            self.create_section("Text", [
                ('text', 'Text', 'string'),
                ('text_color', 'Text Color', 'color'),
                ('text_font', 'Font', 'font'),
                ('text_align', 'Text Align', 'string'),
                ('long_mode', 'Long Mode', 'string'),
                ('recolor', 'Enable Recolor', 'bool'),
            ])
            
        elif widget_type == 'image':
            self.create_section("Image", [
                ('src', 'Source', 'file'),
                ('angle', 'Rotation Angle', 'int'),
                ('zoom', 'Zoom Factor', 'string'),
                ('antialias', 'Anti-alias', 'bool'),
                ('offset_x', 'X Offset', 'int'),
                ('offset_y', 'Y Offset', 'int'),
            ])
            
        elif widget_type in ['arc', 'bar', 'slider']:
            self.create_section("Value", [
                ('value', 'Current Value', 'int'),
                ('min_value', 'Minimum Value', 'int'),
                ('max_value', 'Maximum Value', 'int'),
            ])
            
            if widget_type == 'arc':
                self.create_section("Arc Settings", [
                    ('start_angle', 'Start Angle', 'int'),
                    ('end_angle', 'End Angle', 'int'),
                    ('adjustable', 'User Adjustable', 'bool'),
                    ('arc_color', 'Arc Color', 'color'),
                    ('arc_width', 'Arc Width', 'int'),
                    ('arc_rounded', 'Rounded Ends', 'bool'),
                ])
                
        elif widget_type == 'checkbox':
            self.create_section("Checkbox", [
                ('text', 'Label Text', 'string'),
            ])
            
        elif widget_type == 'dropdown':
            self.create_section("Dropdown", [
                ('options', 'Options', 'list'),
                ('selected_index', 'Selected Index', 'int'),
                ('dir', 'Direction', 'string'),
            ])
            
        elif widget_type == 'textarea':
            self.create_section("Text Input", [
                ('text', 'Text', 'string'),
                ('placeholder_text', 'Placeholder', 'string'),
                ('one_line', 'Single Line', 'bool'),
                ('password_mode', 'Password Mode', 'bool'),
                ('max_length', 'Max Length', 'int'),
                ('accepted_chars', 'Accepted Chars', 'string'),
            ])
            
        elif widget_type == 'spinbox':
            self.create_section("Spinbox", [
                ('value', 'Current Value', 'string'),
                ('range_from', 'Range From', 'string'),
                ('range_to', 'Range To', 'string'),
                ('step', 'Step', 'string'),
                ('digits', 'Digits', 'int'),
                ('decimal_places', 'Decimal Places', 'int'),
                ('rollover', 'Rollover', 'bool'),
            ])
            
        elif widget_type == 'led':
            self.create_section("LED", [
                ('color', 'LED Color', 'color'),
                ('brightness', 'Brightness', 'opacity'),
            ])
            
        elif widget_type == 'qrcode':
            self.create_section("QR Code", [
                ('text', 'Text/URL', 'string'),
                ('size', 'Size', 'int'),
                ('light_color', 'Light Color', 'color'),
                ('dark_color', 'Dark Color', 'color'),
            ])
            
    def create_actions_section(self):
        """Create actions section for triggers and automations"""
        section_frame = ttk.LabelFrame(self.scrollable_frame, text="Actions & Triggers", padding=5)
        section_frame.pack(fill=tk.X, pady=5)
        
        # Common triggers
        triggers = [
            'on_click', 'on_press', 'on_release', 'on_long_press',
            'on_value', 'on_change', 'on_focus', 'on_defocus'
        ]
        
        for trigger in triggers:
            self.create_action_control(section_frame, trigger)
            
    def create_action_control(self, parent, action_name: str):
        """Create an action control"""
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X, pady=1)
        
        # Checkbox to enable/disable action
        enabled_var = tk.BooleanVar(value=action_name in self.current_widget.actions)
        check = ttk.Checkbutton(frame, text=action_name, variable=enabled_var,
                               command=lambda: self.toggle_action(action_name, enabled_var.get()))
        check.pack(side=tk.LEFT)
        
        # Button to edit action
        if action_name in self.current_widget.actions:
            ttk.Button(frame, text="Edit", width=6,
                      command=lambda: self.edit_action(action_name)).pack(side=tk.RIGHT)
                      
    def toggle_action(self, action_name: str, enabled: bool):
        """Toggle an action on/off"""
        if enabled:
            if action_name not in self.current_widget.actions:
                self.current_widget.actions[action_name] = {
                    'then': [{'logger.log': f'{action_name} triggered'}]
                }
        else:
            if action_name in self.current_widget.actions:
                del self.current_widget.actions[action_name]
                
        self.change_callback(self.current_widget, 'actions', self.current_widget.actions)
        self.create_actions_section()  # Refresh the actions section
        
    def edit_action(self, action_name: str):
        """Edit an action's configuration"""
        if action_name not in self.current_widget.actions:
            return
            
        # Create action editor dialog
        dialog = ActionEditorDialog(self.parent, action_name, self.current_widget.actions[action_name])
        if dialog.result:
            self.current_widget.actions[action_name] = dialog.result
            self.change_callback(self.current_widget, 'actions', self.current_widget.actions)
            
    # Property change handlers
    def on_property_changed(self, prop_name: str, value: Any):
        """Handle property change"""
        if self.current_widget:
            setattr(self.current_widget, prop_name, value)
            self.change_callback(self.current_widget, prop_name, value)
            
    def on_int_property_changed(self, prop_name: str, value: str):
        """Handle integer property change"""
        try:
            int_value = int(value) if value else 0
            self.on_property_changed(prop_name, int_value)
        except ValueError:
            pass  # Invalid input, ignore
            
    def on_size_property_changed(self, prop_name: str, value: str):
        """Handle size property change"""
        if value == "SIZE_CONTENT" or value == "":
            self.on_property_changed(prop_name, "SIZE_CONTENT")
        else:
            try:
                int_value = int(value)
                self.on_property_changed(prop_name, int_value)
            except ValueError:
                pass  # Invalid input, ignore
                
    def on_list_property_changed(self, prop_name: str, value: str):
        """Handle list property change"""
        if value:
            list_value = [item.strip() for item in value.split(',')]
            self.on_property_changed(prop_name, list_value)
        else:
            self.on_property_changed(prop_name, [])
            
    def set_size_auto(self, prop_name: str, var: tk.StringVar):
        """Set size to auto (SIZE_CONTENT)"""
        var.set("SIZE_CONTENT")
        
    def choose_color(self, var: tk.StringVar):
        """Open color chooser dialog"""
        current_color = var.get()
        
        # Convert LVGL color to RGB
        if current_color.startswith('0x'):
            try:
                hex_color = current_color[2:]
                rgb_color = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            except:
                rgb_color = (255, 255, 255)
        else:
            rgb_color = (255, 255, 255)
            
        color = colorchooser.askcolor(color=rgb_color)
        if color[1]:  # User selected a color
            # Convert to LVGL format
            hex_color = color[1].lstrip('#')
            lvgl_color = f"0x{hex_color.upper()}"
            var.set(lvgl_color)
            
    def choose_file(self, var: tk.StringVar):
        """Open file chooser dialog"""
        filename = filedialog.askopenfilename(
            title="Select Image File",
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg *.bmp *.gif"),
                ("All files", "*.*")
            ]
        )
        if filename:
            # Use just the filename without path
            import os
            var.set(os.path.basename(filename))


class ActionEditorDialog:
    """Dialog for editing widget actions"""
    
    def __init__(self, parent, action_name: str, action_config: Dict):
        self.action_name = action_name
        self.action_config = action_config.copy()
        self.result = None
        
        # Create dialog
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(f"Edit {action_name}")
        self.dialog.geometry("400x300")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self.create_ui()
        
        # Center dialog
        self.dialog.geometry("+%d+%d" % (
            parent.winfo_rootx() + 50,
            parent.winfo_rooty() + 50
        ))
        
    def create_ui(self):
        """Create dialog UI"""
        # Main frame
        main_frame = ttk.Frame(self.dialog, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        ttk.Label(main_frame, text=f"Configure {self.action_name}", 
                 font=('Arial', 12, 'bold')).pack(pady=(0, 10))
        
        # Action type selection
        type_frame = ttk.Frame(main_frame)
        type_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(type_frame, text="Action Type:").pack(side=tk.LEFT)
        
        self.action_type = tk.StringVar(value="logger.log")
        type_combo = ttk.Combobox(type_frame, textvariable=self.action_type, 
                                values=[
                                    "logger.log", "light.toggle", "light.turn_on", "light.turn_off",
                                    "switch.toggle", "switch.turn_on", "switch.turn_off",
                                    "lvgl.widget.update", "lvgl.page.show", "homeassistant.service"
                                ])
        type_combo.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(10, 0))
        
        # Parameters frame
        params_frame = ttk.LabelFrame(main_frame, text="Parameters", padding=5)
        params_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Simple text area for now - could be enhanced with structured editing
        self.params_text = tk.Text(params_frame, height=8)
        self.params_text.pack(fill=tk.BOTH, expand=True)
        
        # Load current configuration
        if 'then' in self.action_config and self.action_config['then']:
            import yaml
            try:
                yaml_text = yaml.dump(self.action_config['then'], default_flow_style=False)
                self.params_text.insert('1.0', yaml_text)
            except:
                pass
                
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(button_frame, text="Cancel", 
                  command=self.cancel).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="OK", 
                  command=self.ok).pack(side=tk.RIGHT)
                  
    def ok(self):
        """Accept changes"""
        try:
            import yaml
            yaml_text = self.params_text.get('1.0', tk.END).strip()
            if yaml_text:
                self.result = {
                    'then': yaml.safe_load(yaml_text)
                }
            else:
                self.result = {
                    'then': [{'logger.log': f'{self.action_name} triggered'}]
                }
        except Exception as e:
            tk.messagebox.showerror("Error", f"Invalid YAML: {str(e)}")
            return
            
        self.dialog.destroy()
        
    def cancel(self):
        """Cancel changes"""
        self.result = None
        self.dialog.destroy()
