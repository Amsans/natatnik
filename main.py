import tkinter as tk
from tkinter import ttk, filedialog, messagebox, font
import os
import json
import re
try:
    import win32clipboard
    import win32con
    WINDOWS_CLIPBOARD_AVAILABLE = True
except ImportError:
    WINDOWS_CLIPBOARD_AVAILABLE = False

class TextEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("Natatnik")
        self.root.geometry("1000x700")  # Increased window size

        # Default font size
        self.default_font_size = 14  # Increased from 11

        # Set dark theme
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.configure_dark_theme()

        # Create notebook for tabs
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Add bindings for tab management
        self.notebook.bind("<Double-Button-1>", self.on_notebook_double_click)

        # Dictionary to keep track of open files
        self.tabs = {}
        self.current_file = None

        # Create menu
        self.create_menu()

        # Create first tab
        self.create_new_tab()

    def configure_dark_theme(self):
        # Configure dark theme colors
        bg_color = "#000000"
        fg_color = "#FFFFFF"
        select_bg = "#000000"

        self.root.configure(bg=bg_color)

        self.style.configure('TNotebook', background=bg_color)
        self.style.configure('TNotebook.Tab', background=bg_color, foreground=fg_color, padding=[10, 2])
        self.style.map('TNotebook.Tab', background=[('selected', select_bg)], foreground=[('selected', fg_color)])

        self.style.configure('TFrame', background=bg_color)
        self.style.configure('TButton', background=bg_color, foreground=fg_color)
        self.style.configure('TLabel', background=bg_color, foreground=fg_color)

        # Text widget colors will be set when creating each tab

    def create_menu(self):
        menubar = tk.Menu(self.root, bg="#000000", fg="#e0e0e0", activebackground="#000000", activeforeground="#e0e0e0")
        self.root.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0, bg="#000000", fg="#e0e0e0", activebackground="#000000", activeforeground="#e0e0e0")
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New", command=self.create_new_tab)
        file_menu.add_command(label="Open", command=self.open_file)
        file_menu.add_command(label="Save", command=self.save_file)
        file_menu.add_command(label="Save As", command=self.save_file_as)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

        # Edit menu
        edit_menu = tk.Menu(menubar, tearoff=0, bg="#000000", fg="#e0e0e0", activebackground="#4a4a4a", activeforeground="#e0e0e0")
        menubar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Cut", command=self.cut)
        edit_menu.add_command(label="Copy", command=self.copy)
        edit_menu.add_command(label="Paste", command=self.paste)

        # Format menu
        format_menu = tk.Menu(menubar, tearoff=0, bg="#000000", fg="#e0e0e0", activebackground="#4a4a4a", activeforeground="#e0e0e0")
        menubar.add_cascade(label="Format", menu=format_menu)
        format_menu.add_command(label="Bold", command=self.toggle_bold)
        format_menu.add_command(label="Italic", command=self.toggle_italic)
        format_menu.add_command(label="Underline", command=self.toggle_underline)

    def create_new_tab(self, filename=None):
        # Create a frame for the tab
        tab_frame = ttk.Frame(self.notebook)

        # Create formatting toolbar first
        toolbar = ttk.Frame(tab_frame)
        toolbar.pack(side=tk.TOP, fill=tk.X)

        # Create text widget with scrollbar
        text_frame = ttk.Frame(tab_frame)
        text_frame.pack(fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        text_widget = tk.Text(text_frame, yscrollcommand=scrollbar.set, wrap=tk.WORD, 
                             bg="#000000", fg="#e0e0e0", insertbackground="#e0e0e0",
                             selectbackground="#4a4a4a", selectforeground="#e0e0e0",
                             font=("Consolas", self.default_font_size))
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=text_widget.yview)

        # Bold button
        bold_button = ttk.Button(toolbar, text="B", width=2, command=self.toggle_bold)
        bold_button.pack(side=tk.LEFT, padx=2, pady=2)

        # Italic button
        italic_button = ttk.Button(toolbar, text="I", width=2, command=self.toggle_italic)
        italic_button.pack(side=tk.LEFT, padx=2, pady=2)

        # Underline button
        underline_button = ttk.Button(toolbar, text="U", width=2, command=self.toggle_underline)
        underline_button.pack(side=tk.LEFT, padx=2, pady=2)

        # Font size buttons
        font_size_frame = ttk.Frame(toolbar)
        font_size_frame.pack(side=tk.LEFT, padx=10, pady=2)

        decrease_font_button = ttk.Button(font_size_frame, text="A-", width=2, command=self.decrease_font_size)
        decrease_font_button.pack(side=tk.LEFT, padx=2)

        increase_font_button = ttk.Button(font_size_frame, text="A+", width=2, command=self.increase_font_size)
        increase_font_button.pack(side=tk.LEFT, padx=2)

        # Configure text tags for formatting
        text_widget.tag_configure("bold", font=("Consolas", self.default_font_size, "bold"))
        text_widget.tag_configure("italic", font=("Consolas", self.default_font_size, "italic"))
        text_widget.tag_configure("underline", underline=1)

        # Add tab to notebook
        tab_name = os.path.basename(filename) if filename else "Untitled"
        self.notebook.add(tab_frame, text=tab_name)

        # Store tab information
        tab_info = {
            "text_widget": text_widget,
            "filename": filename,
            "frame": tab_frame
        }

        tab_id = len(self.tabs)
        self.tabs[tab_id] = tab_info

        # Select the new tab
        self.notebook.select(len(self.tabs) - 1)
        self.current_file = tab_id

        return tab_id

    def get_current_text_widget(self):
        if self.current_file is not None:
            return self.tabs[self.current_file]["text_widget"]
        return None

    def open_file(self):
        filename = filedialog.askopenfilename(
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        if filename:
            # Check if file is already open
            for tab_id, tab_info in self.tabs.items():
                if tab_info["filename"] == filename:
                    self.notebook.select(tab_id)
                    self.current_file = tab_id
                    return

            # Create new tab with file content
            try:
                with open(filename, "r") as file:
                    content = file.read()

                tab_id = self.create_new_tab(filename)
                text_widget = self.tabs[tab_id]["text_widget"]
                text_widget.delete(1.0, tk.END)
                text_widget.insert(tk.END, content)
                self.current_file = tab_id
            except Exception as e:
                messagebox.showerror("Error", f"Could not open file: {str(e)}")

    def save_file(self):
        if self.current_file is None:
            return

        tab_info = self.tabs[self.current_file]
        filename = tab_info["filename"]

        if not filename:
            return self.save_file_as()

        try:
            content = tab_info["text_widget"].get(1.0, tk.END)
            with open(filename, "w") as file:
                file.write(content)
            return True
        except Exception as e:
            messagebox.showerror("Error", f"Could not save file: {str(e)}")
            return False

    def save_file_as(self):
        if self.current_file is None:
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
        )

        if not filename:
            return False

        tab_info = self.tabs[self.current_file]
        tab_info["filename"] = filename

        # Update tab name
        tab_index = self.notebook.index(self.notebook.select())
        self.notebook.tab(tab_index, text=os.path.basename(filename))

        return self.save_file()

    def cut(self):
        text_widget = self.get_current_text_widget()
        if text_widget:
            if text_widget.tag_ranges(tk.SEL):
                self.copy()
                text_widget.delete(tk.SEL_FIRST, tk.SEL_LAST)

    def set_clipboard_html(self, text, is_bold=False, is_italic=False, is_underline=False):
        """Set HTML content to the clipboard for MS Word compatibility"""
        if not WINDOWS_CLIPBOARD_AVAILABLE:
            return False

        # Create HTML content
        html = "<html><body>"

        # Apply formatting
        if is_bold or is_italic or is_underline:
            html += "<span style=\""
            if is_bold:
                html += "font-weight: bold; "
            if is_italic:
                html += "font-style: italic; "
            if is_underline:
                html += "text-decoration: underline; "
            html += "\">"

        # Add the text content, escaping HTML special characters
        html += text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

        # Close formatting tags
        if is_bold or is_italic or is_underline:
            html += "</span>"

        html += "</body></html>"

        # Prepare the HTML clipboard format header
        # This is the format that MS Word expects
        header = (
            "Version:0.9\r\n"
            "StartHTML:00000000\r\n"
            "EndHTML:00000000\r\n"
            "StartFragment:00000000\r\n"
            "EndFragment:00000000\r\n"
        )

        # Insert fragment markers
        html_with_markers = html.replace("<body>", "<body><!--StartFragment-->").replace("</body>", "<!--EndFragment--></body>")

        # Calculate offsets
        start_html = len(header)
        start_fragment = start_html + html_with_markers.find("<!--StartFragment-->") + len("<!--StartFragment-->")
        end_fragment = start_html + html_with_markers.find("<!--EndFragment-->")
        end_html = start_html + len(html_with_markers)

        # Update header with calculated offsets
        header = header.replace("StartHTML:00000000", f"StartHTML:{start_html:08d}")
        header = header.replace("EndHTML:00000000", f"EndHTML:{end_html:08d}")
        header = header.replace("StartFragment:00000000", f"StartFragment:{start_fragment:08d}")
        header = header.replace("EndFragment:00000000", f"EndFragment:{end_fragment:08d}")

        # Combine header and HTML
        clipboard_data = header + html_with_markers

        try:
            # Open clipboard and set HTML format
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()

            # Set both plain text and HTML formats
            win32clipboard.SetClipboardData(win32con.CF_TEXT, text.encode('utf-8'))
            win32clipboard.SetClipboardData(win32con.CF_UNICODETEXT, text)

            # Set HTML format
            html_format = win32clipboard.RegisterClipboardFormat("HTML Format")
            win32clipboard.SetClipboardData(html_format, clipboard_data.encode('utf-8'))

            return True
        except Exception as e:
            print(f"Error setting clipboard HTML: {e}")
            return False
        finally:
            try:
                win32clipboard.CloseClipboard()
            except:
                pass

    def copy(self):
        text_widget = self.get_current_text_widget()
        if text_widget:
            if text_widget.tag_ranges(tk.SEL):
                # Get the selected text
                selected_text = text_widget.get(tk.SEL_FIRST, tk.SEL_LAST)

                # Get the formatting tags applied to the selection
                start_index = text_widget.index(tk.SEL_FIRST)
                end_index = text_widget.index(tk.SEL_LAST)

                # Check for formatting
                is_bold = "bold" in text_widget.tag_names(start_index)
                is_italic = "italic" in text_widget.tag_names(start_index)
                is_underline = "underline" in text_widget.tag_names(start_index)

                # Create a dictionary to store formatting information
                formatting = {}

                # Store formatting in dictionary for internal use
                if is_bold:
                    formatting["bold"] = True
                if is_italic:
                    formatting["italic"] = True
                if is_underline:
                    formatting["underline"] = True

                # Try to set HTML format for MS Word compatibility first
                html_set = False
                if WINDOWS_CLIPBOARD_AVAILABLE:
                    html_set = self.set_clipboard_html(selected_text, is_bold, is_italic, is_underline)

                # If HTML format wasn't set or not available, use Tkinter's clipboard
                if not html_set:
                    # Create a formatted text representation for internal use
                    formatted_text = {
                        "text": selected_text,
                        "formatting": formatting
                    }

                    # Convert to string for clipboard
                    clipboard_data = json.dumps(formatted_text)

                    # Store in clipboard for internal use
                    self.root.clipboard_clear()
                    self.root.clipboard_append(clipboard_data)

    def paste(self):
        text_widget = self.get_current_text_widget()
        if text_widget:
            try:
                clipboard_data = self.root.clipboard_get()

                # Try to parse as JSON (formatted text)
                try:
                    formatted_text = json.loads(clipboard_data)

                    # Extract text and formatting
                    text = formatted_text.get("text", "")
                    formatting = formatted_text.get("formatting", {})

                    # Delete selected text if any
                    if text_widget.tag_ranges(tk.SEL):
                        text_widget.delete(tk.SEL_FIRST, tk.SEL_LAST)

                    # Insert the text
                    insert_pos = text_widget.index(tk.INSERT)
                    text_widget.insert(insert_pos, text)

                    # Calculate end position
                    end_pos = text_widget.index(f"{insert_pos}+{len(text)}c")

                    # Apply formatting
                    if formatting.get("bold"):
                        text_widget.tag_add("bold", insert_pos, end_pos)

                    if formatting.get("italic"):
                        text_widget.tag_add("italic", insert_pos, end_pos)

                    if formatting.get("underline"):
                        text_widget.tag_add("underline", insert_pos, end_pos)

                except (json.JSONDecodeError, ValueError, KeyError, AttributeError):
                    # Not a valid formatted text, treat as plain text
                    if text_widget.tag_ranges(tk.SEL):
                        text_widget.delete(tk.SEL_FIRST, tk.SEL_LAST)
                    text_widget.insert(tk.INSERT, clipboard_data)

            except Exception as e:
                # Clipboard access error or other exception
                pass

    def toggle_bold(self):
        text_widget = self.get_current_text_widget()
        if text_widget:
            if text_widget.tag_ranges(tk.SEL):
                # Check if selection already has bold tag
                has_bold = "bold" in text_widget.tag_names(tk.SEL_FIRST)

                if has_bold:
                    text_widget.tag_remove("bold", tk.SEL_FIRST, tk.SEL_LAST)
                else:
                    text_widget.tag_add("bold", tk.SEL_FIRST, tk.SEL_LAST)

    def toggle_italic(self):
        text_widget = self.get_current_text_widget()
        if text_widget:
            if text_widget.tag_ranges(tk.SEL):
                # Check if selection already has italic tag
                has_italic = "italic" in text_widget.tag_names(tk.SEL_FIRST)

                if has_italic:
                    text_widget.tag_remove("italic", tk.SEL_FIRST, tk.SEL_LAST)
                else:
                    text_widget.tag_add("italic", tk.SEL_FIRST, tk.SEL_LAST)

    def toggle_underline(self):
        text_widget = self.get_current_text_widget()
        if text_widget:
            if text_widget.tag_ranges(tk.SEL):
                # Check if selection already has underline tag
                has_underline = "underline" in text_widget.tag_names(tk.SEL_FIRST)

                if has_underline:
                    text_widget.tag_remove("underline", tk.SEL_FIRST, tk.SEL_LAST)
                else:
                    text_widget.tag_add("underline", tk.SEL_FIRST, tk.SEL_LAST)

    def increase_font_size(self):
        if self.default_font_size < 52:  # Set a reasonable upper limit
            self.default_font_size += 2
            self.update_font_sizes()

    def decrease_font_size(self):
        if self.default_font_size > 8:  # Set a reasonable lower limit
            self.default_font_size -= 2
            self.update_font_sizes()

    def update_font_sizes(self):
        # Update font sizes for all text widgets and tags
        for tab_id, tab_info in self.tabs.items():
            text_widget = tab_info["text_widget"]
            text_widget.configure(font=("Consolas", self.default_font_size))
            text_widget.tag_configure("bold", font=("Consolas", self.default_font_size, "bold"))
            text_widget.tag_configure("italic", font=("Consolas", self.default_font_size, "italic"))

    def on_notebook_double_click(self, event):
        # Get the tab that was clicked
        try:
            clicked_tab_index = self.notebook.index(f"@{event.x},{event.y}")

            # Find the tab ID from the index
            tab_id = None
            for tid, tab_info in self.tabs.items():
                if self.notebook.index(tab_info["frame"]) == clicked_tab_index:
                    tab_id = tid
                    break

            if tab_id is not None:
                # Close the tab
                self.close_tab(tab_id)
            else:
                # Click was in empty space or invalid area, create a new tab
                self.create_new_tab()
        except (ValueError, tk.TclError):
            # If index() raises an error (empty string or invalid format), create a new tab
            self.create_new_tab()

    def close_tab(self, tab_id):
        # Check if there are unsaved changes
        # For simplicity, we're not implementing this check now

        # Remove the tab
        self.notebook.forget(self.tabs[tab_id]["frame"])

        # Remove from tabs dictionary
        del self.tabs[tab_id]

        # If there are no more tabs, create a new one
        if not self.tabs:
            self.create_new_tab()
            return

        # Update current_file to the selected tab
        selected_tab_index = self.notebook.index(self.notebook.select())
        for tid, tab_info in self.tabs.items():
            if self.notebook.index(tab_info["frame"]) == selected_tab_index:
                self.current_file = tid
                break

def main():
    root = tk.Tk()
    app = TextEditor(root)
    root.mainloop()

if __name__ == "__main__":
    main()
