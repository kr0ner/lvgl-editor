"""
Widget Library for LVGL Editor
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, List, Any, Callable
from widgets import LVGL_WIDGETS

class WidgetLibrary:
    """Widget library panel for selecting widgets to place"""
    
    def __init__(self, parent, selection_callback: Callable):
        self.parent = parent
        self.selection_callback = selection_callback
        
        # State
        self.selected_widget = None
        
        # Create UI
        self.create_ui()
        
    def create_ui(self):
        """Create the widget library UI"""
        # Main frame
        main_frame = ttk.LabelFrame(self.parent, text="Widget Library", padding=5)
        main_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        
        # Search frame
        search_frame = ttk.Frame(main_frame)
        search_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT)
        
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        search_entry.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(5, 0))
        self.search_var.trace('w', self.on_search_changed)
        
        # Widget categories notebook
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Create category tabs
        self.category_frames = {}
        self.widget_buttons = {}
        
        for category_name, widgets in LVGL_WIDGETS.items():
            self.create_category_tab(category_name, widgets)
            
    def create_category_tab(self, category_name: str, widgets: Dict[str, Dict]):
        """Create a tab for a widget category"""
        # Create scrollable frame
        tab_frame = ttk.Frame(self.notebook)
        self.notebook.add(tab_frame, text=category_name)
        
        # Canvas for scrolling
        canvas = tk.Canvas(tab_frame)
        scrollbar = ttk.Scrollbar(tab_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Store references
        self.category_frames[category_name] = scrollable_frame
        self.widget_buttons[category_name] = {}
        
        # Create widget buttons
        for widget_type, widget_info in widgets.items():
            self.create_widget_button(scrollable_frame, category_name, widget_type, widget_info)
            
        # Bind mousewheel
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind("<MouseWheel>", _on_mousewheel)
        
    def create_widget_button(self, parent, category: str, widget_type: str, widget_info: Dict):
        """Create a button for a widget type"""
        # Button frame
        button_frame = ttk.Frame(parent, relief='ridge', borderwidth=1)
        button_frame.pack(fill=tk.X, pady=2, padx=2)
        
        # Main button
        button = tk.Button(
            button_frame,
            text=f"{widget_info.get('icon', '◼')} {widget_info['name']}",
            font=('Arial', 10),
            anchor='w',
            bg='white',
            relief='flat',
            cursor='hand2',
            command=lambda: self.select_widget(widget_type)
        )
        button.pack(fill=tk.X, pady=2, padx=2)
        
        # Description label
        desc_label = ttk.Label(
            button_frame,
            text=widget_info.get('description', ''),
            font=('Arial', 8),
            foreground='gray'
        )
        desc_label.pack(fill=tk.X, padx=4, pady=(0, 2))
        
        # Store button reference
        self.widget_buttons[category][widget_type] = {
            'frame': button_frame,
            'button': button,
            'info': widget_info
        }
        
        # Bind hover effects
        def on_enter(event):
            if self.selected_widget != widget_type:
                button.config(bg='#e6f3ff')
                
        def on_leave(event):
            if self.selected_widget != widget_type:
                button.config(bg='white')
                
        button.bind("<Enter>", on_enter)
        button.bind("<Leave>", on_leave)
        
    def select_widget(self, widget_type: str):
        """Select a widget type"""
        # Clear previous selection
        if self.selected_widget:
            self.clear_selection()
            
        # Set new selection
        self.selected_widget = widget_type
        
        # Highlight selected button
        for category_buttons in self.widget_buttons.values():
            if widget_type in category_buttons:
                button = category_buttons[widget_type]['button']
                button.config(bg='#0078d4', fg='white')
                break
                
        # Notify callback
        self.selection_callback(widget_type)
        
    def clear_selection(self):
        """Clear widget selection"""
        if self.selected_widget:
            # Find and unhighlight the selected button
            for category_buttons in self.widget_buttons.values():
                if self.selected_widget in category_buttons:
                    button = category_buttons[self.selected_widget]['button']
                    button.config(bg='white', fg='black')
                    break
                    
        self.selected_widget = None
        
    def on_search_changed(self, *args):
        """Handle search text changes"""
        search_text = self.search_var.get().lower()
        
        for category_name, category_buttons in self.widget_buttons.items():
            for widget_type, button_info in category_buttons.items():
                widget_info = button_info['info']
                frame = button_info['frame']
                
                # Check if widget matches search
                matches = (
                    search_text in widget_type.lower() or
                    search_text in widget_info['name'].lower() or
                    search_text in widget_info.get('description', '').lower()
                )
                
                # Show/hide based on search
                if search_text == '' or matches:
                    frame.pack(fill=tk.X, pady=2, padx=2)
                else:
                    frame.pack_forget()
                    
    def get_widget_info(self, widget_type: str) -> Dict[str, Any]:
        """Get information about a widget type"""
        for category_widgets in LVGL_WIDGETS.values():
            if widget_type in category_widgets:
                return category_widgets[widget_type]
        return {}
        
    def get_selected_widget(self) -> str:
        """Get the currently selected widget type"""
        return self.selected_widget
