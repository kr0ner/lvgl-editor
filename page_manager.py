"""
Page Manager for LVGL Editor
Handles multiple pages, navigation, and page-specific settings
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from typing import Dict, List, Optional, Callable
import uuid

class PageManager:
    """Manages multiple LVGL pages and navigation between them"""
    
    def __init__(self, parent: tk.Widget, on_page_changed: Optional[Callable] = None):
        self.parent = parent
        self.on_page_changed = on_page_changed
        
        # Page data
        self.pages = {}  # page_id -> page_info
        self.current_page = None
        self.page_widgets = {}  # page_id -> list of widgets
        
        # UI elements
        self.create_ui()
        
        # Create default page
        self.add_page("Main Page", is_default=True)
        
    def create_ui(self):
        """Create the page management UI"""
        
        # Main frame
        self.frame = ttk.Frame(self.parent)
        
        # Header
        header_frame = ttk.Frame(self.frame)
        header_frame.pack(fill=tk.X, padx=5, pady=2)
        
        ttk.Label(header_frame, text="Pages", font=('Arial', 10, 'bold')).pack(side=tk.LEFT)
        
        # Page buttons frame
        self.buttons_frame = ttk.Frame(header_frame)
        self.buttons_frame.pack(side=tk.RIGHT)
        
        ttk.Button(self.buttons_frame, text="+", width=3, command=self.add_page_dialog).pack(side=tk.LEFT, padx=2)
        ttk.Button(self.buttons_frame, text="⚙", width=3, command=self.edit_page_dialog).pack(side=tk.LEFT, padx=2)
        ttk.Button(self.buttons_frame, text="×", width=3, command=self.delete_page_dialog).pack(side=tk.LEFT, padx=2)
        
        # Page tabs
        self.notebook = ttk.Notebook(self.frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=2)
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)
        
        # Context menu for tabs
        self.create_context_menu()
        
    def create_context_menu(self):
        """Create context menu for page tabs"""
        self.context_menu = tk.Menu(self.parent, tearoff=0)
        self.context_menu.add_command(label="Rename Page", command=self.rename_page_dialog)
        self.context_menu.add_command(label="Duplicate Page", command=self.duplicate_page)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Page Settings", command=self.edit_page_dialog)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Delete Page", command=self.delete_page_dialog)
        
        # Bind right-click to tabs
        self.notebook.bind("<Button-3>", self.show_context_menu)
        
    def show_context_menu(self, event):
        """Show context menu for page tabs"""
        try:
            # Get the tab under cursor
            tab_id = self.notebook.tk.call(self.notebook._w, "identify", "tab", event.x, event.y)
            if tab_id != "":
                self.notebook.select(tab_id)
                self.context_menu.post(event.x_root, event.y_root)
        except tk.TclError:
            pass
            
    def add_page(self, name: str = None, is_default: bool = False) -> str:
        """Add a new page"""
        if name is None:
            name = f"Page {len(self.pages) + 1}"
            
        # Generate unique page ID
        page_id = f"page_{uuid.uuid4().hex[:8]}"
        if is_default:
            page_id = "main_page"
            
        # Create page info
        page_info = {
            'id': page_id,
            'name': name,
            'layout': 'NONE',
            'background_color': '#000000',
            'scrollable': False,
            'scroll_direction': 'BOTH',
            'is_default': is_default
        }
        
        self.pages[page_id] = page_info
        self.page_widgets[page_id] = []
        
        # Create tab
        tab_frame = ttk.Frame(self.notebook)
        self.notebook.add(tab_frame, text=name)
        
        # Add page content label (placeholder)
        content_label = ttk.Label(tab_frame, text=f"Page: {name}\nDrag widgets here from the widget library", 
                                 justify=tk.CENTER, foreground='gray')
        content_label.pack(expand=True)
        
        # Store tab info
        tab_frame.page_id = page_id
        
        # Select the new page
        self.notebook.select(tab_frame)
        self.current_page = page_id
        
        # Notify about page change
        if self.on_page_changed:
            self.on_page_changed(page_id, page_info)
            
        return page_id
        
    def add_page_dialog(self):
        """Show dialog to add a new page"""
        name = simpledialog.askstring("Add Page", "Enter page name:", initialvalue=f"Page {len(self.pages) + 1}")
        if name:
            self.add_page(name)
            
    def delete_page_dialog(self):
        """Show dialog to delete current page"""
        if len(self.pages) <= 1:
            messagebox.showwarning("Cannot Delete", "Cannot delete the last page.")
            return
            
        if self.current_page:
            page_info = self.pages[self.current_page]
            if page_info.get('is_default', False):
                result = messagebox.askyesno("Delete Default Page", 
                    "This is the default page. Are you sure you want to delete it?")
                if not result:
                    return
                    
            widget_count = len(self.page_widgets.get(self.current_page, []))
            if widget_count > 0:
                result = messagebox.askyesno("Delete Page", 
                    f"Page contains {widget_count} widgets. Delete anyway?")
                if not result:
                    return
                    
            self.delete_page(self.current_page)
            
    def delete_page(self, page_id: str):
        """Delete a page"""
        if page_id not in self.pages:
            return
            
        # Find and remove tab
        for i in range(self.notebook.index('end')):
            tab_frame = self.notebook.nametowidget(self.notebook.tabs()[i])
            if hasattr(tab_frame, 'page_id') and tab_frame.page_id == page_id:
                self.notebook.forget(i)
                break
                
        # Remove page data
        del self.pages[page_id]
        if page_id in self.page_widgets:
            del self.page_widgets[page_id]
            
        # Select another page
        if self.current_page == page_id:
            if self.pages:
                first_page_id = list(self.pages.keys())[0]
                self.switch_to_page(first_page_id)
            else:
                self.current_page = None
                
    def edit_page_dialog(self):
        """Show dialog to edit page settings"""
        if not self.current_page:
            return
            
        page_info = self.pages[self.current_page]
        
        # Create dialog
        dialog = tk.Toplevel(self.parent)
        dialog.title("Page Settings")
        dialog.geometry("400x300")
        dialog.transient(self.parent)
        dialog.grab_set()
        
        # Center dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")
        
        # Variables
        name_var = tk.StringVar(value=page_info['name'])
        layout_var = tk.StringVar(value=page_info.get('layout', 'NONE'))
        bg_color_var = tk.StringVar(value=page_info.get('background_color', '#000000'))
        scrollable_var = tk.BooleanVar(value=page_info.get('scrollable', False))
        scroll_dir_var = tk.StringVar(value=page_info.get('scroll_direction', 'BOTH'))
        
        # Layout
        row = 0
        
        # Name
        ttk.Label(dialog, text="Page Name:").grid(row=row, column=0, sticky=tk.W, padx=10, pady=5)
        ttk.Entry(dialog, textvariable=name_var, width=30).grid(row=row, column=1, padx=10, pady=5)
        row += 1
        
        # Layout
        ttk.Label(dialog, text="Layout:").grid(row=row, column=0, sticky=tk.W, padx=10, pady=5)
        layout_combo = ttk.Combobox(dialog, textvariable=layout_var, values=['NONE', 'FLEX', 'GRID'], 
                                   state='readonly', width=27)
        layout_combo.grid(row=row, column=1, padx=10, pady=5)
        row += 1
        
        # Background color
        ttk.Label(dialog, text="Background Color:").grid(row=row, column=0, sticky=tk.W, padx=10, pady=5)
        color_frame = ttk.Frame(dialog)
        color_frame.grid(row=row, column=1, padx=10, pady=5, sticky=tk.W)
        ttk.Entry(color_frame, textvariable=bg_color_var, width=20).pack(side=tk.LEFT)
        ttk.Button(color_frame, text="...", width=3, 
                  command=lambda: self.choose_color(bg_color_var)).pack(side=tk.LEFT, padx=5)
        row += 1
        
        # Scrollable
        ttk.Checkbutton(dialog, text="Enable Scrolling", variable=scrollable_var).grid(row=row, column=0, 
                                                                                       columnspan=2, sticky=tk.W, 
                                                                                       padx=10, pady=5)
        row += 1
        
        # Scroll direction
        ttk.Label(dialog, text="Scroll Direction:").grid(row=row, column=0, sticky=tk.W, padx=10, pady=5)
        scroll_combo = ttk.Combobox(dialog, textvariable=scroll_dir_var, 
                                   values=['BOTH', 'HORIZONTAL', 'VERTICAL'], 
                                   state='readonly', width=27)
        scroll_combo.grid(row=row, column=1, padx=10, pady=5)
        row += 1
        
        # Buttons
        button_frame = ttk.Frame(dialog)
        button_frame.grid(row=row, column=0, columnspan=2, pady=20)
        
        def save_settings():
            # Update page info
            page_info['name'] = name_var.get()
            page_info['layout'] = layout_var.get()
            page_info['background_color'] = bg_color_var.get()
            page_info['scrollable'] = scrollable_var.get()
            page_info['scroll_direction'] = scroll_dir_var.get()
            
            # Update tab text
            current_tab = self.notebook.select()
            self.notebook.tab(current_tab, text=name_var.get())
            
            # Notify about changes
            if self.on_page_changed:
                self.on_page_changed(self.current_page, page_info)
                
            dialog.destroy()
            
        ttk.Button(button_frame, text="Save", command=save_settings).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
        
    def choose_color(self, color_var: tk.StringVar):
        """Show color chooser dialog"""
        try:
            from tkinter import colorchooser
            color = colorchooser.askcolor(color=color_var.get())[1]
            if color:
                color_var.set(color)
        except ImportError:
            # Fallback if colorchooser not available
            color = simpledialog.askstring("Color", "Enter color (hex):", initialvalue=color_var.get())
            if color:
                color_var.set(color)
                
    def rename_page_dialog(self):
        """Show dialog to rename current page"""
        if not self.current_page:
            return
            
        current_name = self.pages[self.current_page]['name']
        new_name = simpledialog.askstring("Rename Page", "Enter new name:", initialvalue=current_name)
        
        if new_name and new_name != current_name:
            self.pages[self.current_page]['name'] = new_name
            
            # Update tab text
            current_tab = self.notebook.select()
            self.notebook.tab(current_tab, text=new_name)
            
    def duplicate_page(self):
        """Duplicate the current page"""
        if not self.current_page:
            return
            
        # Get current page data
        source_page = self.pages[self.current_page]
        source_widgets = self.page_widgets.get(self.current_page, [])
        
        # Create new page
        new_name = f"{source_page['name']} Copy"
        new_page_id = self.add_page(new_name)
        
        # Copy page settings
        new_page_info = self.pages[new_page_id]
        new_page_info.update({
            'layout': source_page.get('layout', 'NONE'),
            'background_color': source_page.get('background_color', '#000000'),
            'scrollable': source_page.get('scrollable', False),
            'scroll_direction': source_page.get('scroll_direction', 'BOTH'),
            'is_default': False  # Copy is never default
        })
        
        # Copy widgets (deep copy)
        import copy
        self.page_widgets[new_page_id] = copy.deepcopy(source_widgets)
        
        # Generate new IDs for copied widgets
        def update_widget_ids(widget_data):
            if 'id' in widget_data:
                widget_data['id'] = f"{widget_data['id']}_copy_{uuid.uuid4().hex[:4]}"
            if 'children' in widget_data:
                for child in widget_data['children']:
                    update_widget_ids(child)
                    
        for widget in self.page_widgets[new_page_id]:
            update_widget_ids(widget)
            
    def on_tab_changed(self, event):
        """Handle tab change event"""
        selected_tab = self.notebook.select()
        if selected_tab:
            tab_frame = self.notebook.nametowidget(selected_tab)
            if hasattr(tab_frame, 'page_id'):
                page_id = tab_frame.page_id
                if page_id != self.current_page:
                    self.switch_to_page(page_id)
                    
    def switch_to_page(self, page_id: str):
        """Switch to a specific page"""
        if page_id not in self.pages:
            return
            
        self.current_page = page_id
        
        # Find and select corresponding tab
        for i in range(self.notebook.index('end')):
            tab_frame = self.notebook.nametowidget(self.notebook.tabs()[i])
            if hasattr(tab_frame, 'page_id') and tab_frame.page_id == page_id:
                self.notebook.select(i)
                break
                
        # Notify about page change
        if self.on_page_changed:
            self.on_page_changed(page_id, self.pages[page_id])
            
    def get_current_page_id(self) -> Optional[str]:
        """Get the current page ID"""
        return self.current_page
        
    def get_current_page_info(self) -> Optional[Dict]:
        """Get the current page info"""
        if self.current_page:
            return self.pages[self.current_page]
        return None
        
    def get_page_widgets(self, page_id: str) -> List[Dict]:
        """Get widgets for a specific page"""
        return self.page_widgets.get(page_id, [])
        
    def set_page_widgets(self, page_id: str, widgets: List[Dict]):
        """Set widgets for a specific page"""
        if page_id in self.pages:
            self.page_widgets[page_id] = widgets
            
    def get_all_pages(self) -> Dict:
        """Get all pages data"""
        return self.pages.copy()
        
    def get_all_widgets_data(self) -> Dict[str, List[Dict]]:
        """Get all widgets data for all pages"""
        return self.page_widgets.copy()
        
    def load_project_data(self, pages_data: Dict, widgets_data: Dict[str, List[Dict]]):
        """Load project data (pages and widgets)"""
        
        # Clear existing pages
        for i in range(self.notebook.index('end')):
            self.notebook.forget(0)
            
        self.pages.clear()
        self.page_widgets.clear()
        self.current_page = None
        
        # Load pages
        if not pages_data:
            # Create default page if no pages data
            self.add_page("Main Page", is_default=True)
            return
            
        first_page = True
        for page_id, page_info in pages_data.items():
            self.pages[page_id] = page_info
            self.page_widgets[page_id] = widgets_data.get(page_id, [])
            
            # Create tab
            tab_frame = ttk.Frame(self.notebook)
            self.notebook.add(tab_frame, text=page_info['name'])
            
            # Add page content label
            widget_count = len(self.page_widgets[page_id])
            content_text = f"Page: {page_info['name']}\n{widget_count} widgets"
            content_label = ttk.Label(tab_frame, text=content_text, justify=tk.CENTER, foreground='gray')
            content_label.pack(expand=True)
            
            # Store tab info
            tab_frame.page_id = page_id
            
            # Select first page
            if first_page:
                self.notebook.select(tab_frame)
                self.current_page = page_id
                first_page = False
                
        # Notify about page change
        if self.current_page and self.on_page_changed:
            self.on_page_changed(self.current_page, self.pages[self.current_page])
            
    def create_page_navigation_buttons(self, parent_frame: tk.Widget, canvas_editor) -> ttk.Frame:
        """Create navigation buttons for interactive page switching"""
        
        nav_frame = ttk.LabelFrame(parent_frame, text="Page Navigation", padding=5)
        
        # Previous/Next buttons
        button_frame = ttk.Frame(nav_frame)
        button_frame.pack(fill=tk.X, pady=2)
        
        ttk.Button(button_frame, text="◀ Previous", 
                  command=lambda: self.navigate_previous()).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="Next ▶", 
                  command=lambda: self.navigate_next()).pack(side=tk.RIGHT, padx=2)
                  
        # Page list
        self.nav_listbox = tk.Listbox(nav_frame, height=4)
        self.nav_listbox.pack(fill=tk.BOTH, expand=True, pady=2)
        self.nav_listbox.bind('<<ListboxSelect>>', self.on_nav_selection)
        
        # Update navigation list
        self.update_navigation_list()
        
        return nav_frame
        
    def update_navigation_list(self):
        """Update the navigation listbox"""
        if hasattr(self, 'nav_listbox'):
            self.nav_listbox.delete(0, tk.END)
            for page_id, page_info in self.pages.items():
                marker = "★ " if page_id == self.current_page else "   "
                self.nav_listbox.insert(tk.END, f"{marker}{page_info['name']}")
                
    def on_nav_selection(self, event):
        """Handle navigation listbox selection"""
        selection = self.nav_listbox.curselection()
        if selection:
            index = selection[0]
            page_ids = list(self.pages.keys())
            if 0 <= index < len(page_ids):
                self.switch_to_page(page_ids[index])
                
    def navigate_previous(self):
        """Navigate to previous page"""
        if not self.current_page:
            return
            
        page_ids = list(self.pages.keys())
        try:
            current_index = page_ids.index(self.current_page)
            prev_index = (current_index - 1) % len(page_ids)
            self.switch_to_page(page_ids[prev_index])
        except ValueError:
            pass
            
    def navigate_next(self):
        """Navigate to next page"""
        if not self.current_page:
            return
            
        page_ids = list(self.pages.keys())
        try:
            current_index = page_ids.index(self.current_page)
            next_index = (current_index + 1) % len(page_ids)
            self.switch_to_page(page_ids[next_index])
        except ValueError:
            pass
            
    def pack(self, **kwargs):
        """Pack the page manager frame"""
        self.frame.pack(**kwargs)
        
    def grid(self, **kwargs):
        """Grid the page manager frame"""
        self.frame.grid(**kwargs)
