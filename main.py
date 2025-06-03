import json
import os
import textwrap
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, font as tkfont

LABEL_FONT = ("Arial", 20)


class TextEditor:
    def __init__(self, root: tk.Tk):
        self.font_size_display = None
        self.font_size_var = None
        self.untitled_counter = None
        self.fixed_tab_index = 1
        self.root = root
        self.root.title("Natatnik")
        self.root.geometry("1000x700")  # Increased window size
        self.root.iconbitmap("icon.ico")

        # Default font size
        self.default_font_size = 28  # Doubled from 14

        # Settings directory and file
        self.settings_dir = os.path.join(os.path.expanduser("~"), ".natatnik")
        self.settings_file = os.path.join(self.settings_dir, "settings.json")
        self.autosave_dir = os.path.join(self.settings_dir, "autosave")

        # Create settings directory if it doesn't exist
        os.makedirs(self.settings_dir, exist_ok=True)
        os.makedirs(self.autosave_dir, exist_ok=True)

        # Load settings
        self.load_settings()

        # Set dark theme
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.configure_dark_theme()

        # Create main frame
        self.main_frame = ttk.Frame(root)
        self.main_frame.pack(fill="both", expand=True)

        # Create font size control frame above tabs
        self.create_font_size_control()

        status_bar = ttk.Frame(self.main_frame)
        status_bar.pack(side="bottom", fill="both", padx=5, pady=5)

        self.status_label = ttk.Label(status_bar, text="Радкоў: 0", font=("Arial", 18))
        self.status_label.pack(side="left", fill="x", padx=5, pady=5, expand=1)

        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill="both", expand=True, padx=5, pady=5)

        # Add bindings for tab management
        self.notebook.bind("<Double-Button-1>", self.on_notebook_double_click)

        # Dictionary to keep track of open files
        self.tabs = {}
        self.current_file = None

        # Create menu
        self.create_menu()

        # Setup autosave
        self.setup_autosave()

        # Create + tab
        self.create_fixed_tab()

        # Load previously opened tabs
        self.load_tabs()

        # If no tabs were loaded, create a new one
        if not self.tabs:
            self.create_new_tab()

        self.count_display_lines()

    def configure_dark_theme(self):
        # Configure dark theme colors
        bg_color = "#000000"
        fg_color = "#FFFFFF"
        select_bg = "#000000"

        self.root.configure(bg=bg_color)

        self.style.configure('TNotebook', background=bg_color)
        self.style.configure('TNotebook.Tab', background=bg_color, foreground=fg_color, padding=[20, 4], font=("Consolas", 28, "bold"))
        self.style.map('TNotebook.Tab', background=[('selected', "#454545")], foreground=[('selected', fg_color)])

        self.style.configure('TFrame', background=bg_color)
        self.style.configure('TButton', background=bg_color, foreground=fg_color, font=("Arial", 15))
        self.style.configure('TLabel', background=bg_color, foreground=fg_color)

        # Text widget colors will be set when creating each tab

    def create_menu(self):
        menubar = tk.Menu(self.root, bg="#000000", fg="#e0e0e0", activebackground="#000000", activeforeground="#e0e0e0")
        self.root.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0, bg="#000000", fg="#e0e0e0", activebackground="#000000", activeforeground="#e0e0e0", font=LABEL_FONT)
        menubar.add_cascade(label="Файл", menu=file_menu, font=LABEL_FONT)
        file_menu.add_command(label="Новы", command=self.create_new_tab)
        file_menu.add_command(label="Адкрыць", command=self.open_file)
        file_menu.add_command(label="Захаваць", command=self.save_file)
        file_menu.add_command(label="Захаваць як...", command=self.save_file_as)
        file_menu.add_separator()
        file_menu.add_command(label="Выхад", command=self.root.quit)

        # Edit menu
        edit_menu = tk.Menu(menubar, tearoff=0, bg="#000000", fg="#e0e0e0", activebackground="#4a4a4a", activeforeground="#e0e0e0", font=LABEL_FONT)
        menubar.add_cascade(label="Праўка", menu=edit_menu, font=LABEL_FONT)
        edit_menu.add_command(label="Выразаць", command=self.cut)
        edit_menu.add_command(label="Капіраваць", command=self.copy)
        edit_menu.add_command(label="Уставіць", command=self.paste)

    def create_font_size_control(self):
        # Create a frame for font size control
        font_control_frame = ttk.Frame(self.main_frame)
        font_control_frame.pack(side="top", fill="x", padx=5, pady=5)

        # Label for the slider
        font_size_label = ttk.Label(font_control_frame, text="Шрыфт:", font=("Arial", 15))
        font_size_label.pack(side="left", padx=5)

        # Create a slider for font size
        self.font_size_var = tk.IntVar(value=self.default_font_size)
        font_size_slider = ttk.Scale(font_control_frame, from_=10, to=80,
                                     orient="horizontal", length=200,
                                     variable=self.font_size_var, command=self.on_font_size_change)
        font_size_slider.pack(side="left", padx=5)

        # Display current font size value
        self.font_size_display = ttk.Label(font_control_frame, text=str(self.font_size_var.get()), font=LABEL_FONT)
        self.font_size_display.pack(side="left", padx=5)

    def create_fixed_tab(self):
        fixed_frame = ttk.Frame(self.notebook)
        self.notebook.add(fixed_frame, text="+")  # Fixed tab as "+" or "Add"
        self.fixed_tab_index = self.notebook.index("end") - 1  # Always last
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)

    def on_tab_changed(self, event):
        selected_index = self.notebook.index("current")
        if selected_index == self.fixed_tab_index:
            self.create_new_tab()
            if self.tabs:
                self.notebook.select(len(self.tabs) - 1)

    def create_new_tab(self, filename=None, content=None):
        content_frame = ttk.Frame(self.notebook)
        toolbar = ttk.Frame(content_frame)
        toolbar.pack(side="top", fill="x")

        # Add close button
        tab_id = len(self.tabs)  # Get tab ID before adding to notebook
        close_button = ttk.Button(toolbar, text="Закрыць", command=lambda: self.close_tab(tab_id))
        close_button.pack(side="right")

        # Rest of the method...
        text_frame = ttk.Frame(content_frame)
        text_frame.pack(fill="both", expand=True)
        scrollbar = ttk.Scrollbar(text_frame)
        scrollbar.pack(side="right", fill="y")
        text_widget = tk.Text(text_frame, yscrollcommand=scrollbar.set, wrap="char",
                              bg="#000000", fg="#FFFFFF", insertbackground="#e0e0e0",
                              selectbackground="#4a4a4a", selectforeground="#FFFFFF",
                              font=("Consolas", self.default_font_size, "bold"))
        text_widget.pack(side="left", fill="both", expand=True)
        text_widget.bind("<KeyRelease>", self.on_text_change)
        scrollbar.config(command=text_widget.yview)

        if filename:
            tab_name = os.path.basename(filename)[:-4]
        else:
            tab_name = f"Новы{self.untitled_counter}"
            filename = os.path.join(self.autosave_dir, f"{tab_name}.txt")
            self.untitled_counter += 1

        # Insert tab just before the fixed "+" tab
        self.notebook.insert(self.fixed_tab_index, content_frame, text=tab_name)
        tab_info = {
            "text_widget": text_widget,
            "filename": filename,
            "frame": content_frame,
            "autosave_filename": filename if not os.path.exists(filename) else None
        }
        self.tabs[tab_id] = tab_info
        if content:
            text_widget.delete(1.0, tk.END)
            text_widget.insert(tk.END, content)

        self.notebook.select(tab_id)
        self.current_file = tab_id
        self.count_display_lines()

        # Update fixed tab index since tab list changed
        self.fixed_tab_index = self.notebook.index("end") - 1
        return tab_id

    def get_current_text_widget(self):
        if self.current_file is not None:
            return self.tabs[self.current_file]["text_widget"]
        return None

    def count_display_lines(self):
        tab_id = self.notebook.index(self.notebook.select())
        text_widget = self.tabs[tab_id]["text_widget"]
        # Update layout
        text_widget.update_idletasks()

        text_font = tkfont.Font(font=text_widget['font'])
        widget_width_px = text_widget.winfo_width()
        # Get average character width (approximation using space character)
        avg_char_width = text_font.measure("n")  # You can use " " or "n" as a good estimate
        # Characters per line that can fit in widget
        chars_per_line = max(widget_width_px // avg_char_width, 1)
        # Get all text content
        full_text = text_widget.get("1.0", "end-1c")  # remove trailing newline
        # Split into logical lines
        logical_lines = full_text.split("\n")

        # Estimate total visual lines using word wrap
        total_visual_lines = 0
        for line in logical_lines:
            wrapped = textwrap.wrap(line, width=chars_per_line) or [""]
            total_visual_lines += len(wrapped)

        lines_text = f"Радкоў: {total_visual_lines}"
        self.status_label.config(text=lines_text)

        return total_visual_lines

    def on_text_change(self, event=None):
        self.count_display_lines()

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
            return None

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
            return None

        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
        )

        if not filename:
            return False

        tab_info = self.tabs[self.current_file]

        # Check if this was an autosaved file
        old_filename = tab_info["filename"]
        if old_filename and os.path.dirname(old_filename) == self.autosave_dir:
            # This was an autosaved file, try to remove it
            try:
                os.remove(old_filename)
            except OSError as e:
                print(e)
                pass

        tab_info["filename"] = filename
        tab_info["autosave_filename"] = None  # No longer an autosave file

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
                self.count_display_lines()

    def copy(self):
        text_widget = self.get_current_text_widget()
        if text_widget:
            if text_widget.tag_ranges(tk.SEL):
                # Get the selected text
                selected_text = text_widget.get(tk.SEL_FIRST, tk.SEL_LAST)
                self.root.clipboard_clear()
                self.root.clipboard_append(selected_text)

    def paste(self):
        text_widget = self.get_current_text_widget()
        if text_widget:
            try:
                clipboard_data = self.root.clipboard_get()
                if text_widget.tag_ranges(tk.SEL):
                    text_widget.delete(tk.SEL_FIRST, tk.SEL_LAST)
                text_widget.insert(tk.INSERT, clipboard_data)
                self.count_display_lines()
            except tk.TclError:
                # Clipboard is empty or unavailable; ignore
                pass

    def load_settings(self):
        # Load settings from file
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    settings = json.load(f)
                    self.default_font_size = settings.get('font_size', self.default_font_size)
                    self.untitled_counter = settings.get('untitled_counter', 1)
        except Exception as e:
            print(f"Error loading settings: {e}")

    def save_settings(self):
        # Save settings to file
        try:
            settings = {
                'font_size': self.default_font_size,
                'untitled_counter': self.untitled_counter
            }
            with open(self.settings_file, 'w') as f:
                json.dump(settings, f)
        except Exception as e:
            print(f"Error saving settings: {e}")

    # noinspection PyTypeChecker
    def setup_autosave(self):
        # Set up autosave to run every 30 seconds
        self.autosave()
        self.root.after(30000, self.setup_autosave)
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def on_closing(self):
        self.autosave()
        self.root.destroy()

    def autosave(self):
        # Save all tabs
        for tab_id, tab_info in self.tabs.items():
            self.autosave_tab(tab_id)

    def autosave_tab(self, tab_id):
        tab_info = self.tabs[tab_id]
        filename = tab_info["filename"]

        # Get content
        content = tab_info["text_widget"].get(1.0, tk.END)

        # Save to file
        try:
            with open(filename, 'w') as f:
                f.write(content)
        except Exception as e:
            print(f"Error autosaving tab {tab_id}: {e}")

    def load_tabs(self):
        # Load tabs from autosave directory
        try:
            autosave_files = [f for f in os.listdir(self.autosave_dir) if f.endswith('.txt')]

            # Sort files to maintain order
            autosave_files.sort()

            # Extract the highest untitled number to set the counter
            highest_num = 0
            for filename in autosave_files:
                if filename.startswith('Новы'):
                    try:
                        num = int(filename[4:-4])  # Extract number from "Untitled{num}.txt"
                        highest_num = max(highest_num, num)
                    except ValueError:
                        pass

            self.untitled_counter = highest_num + 1

            # Load each file
            for filename in autosave_files:
                full_path = os.path.join(self.autosave_dir, filename)
                try:
                    with open(full_path, 'r') as f:
                        content = f.read()
                    self.create_new_tab(full_path, content)
                except Exception as e:
                    print(f"Error loading tab {filename}: {e}")
        except Exception as e:
            print(f"Error loading tabs: {e}")

    def on_font_size_change(self, value):
        try:
            new_size = int(float(value))
            self.default_font_size = new_size
            self.font_size_display.config(text=str(new_size))
            self.update_font_sizes()
            self.count_display_lines()
            self.save_settings()
        except ValueError:
            pass

    def update_font_sizes(self):
        # Update font sizes for all text widgets and tags
        for tab_id, tab_info in self.tabs.items():
            text_widget = tab_info["text_widget"]
            text_widget.configure(font=("Consolas", self.default_font_size, "bold"))

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
            # else:
            #     # Click was in empty space or invalid area, create a new tab
            #     self.create_new_tab()
        except (ValueError, tk.TclError ) as err:
            print(err)
            # If index() raises an error (empty string or invalid format), create a new tab
            # self.create_new_tab()

    def close_tab(self, tab_id):
        # Check if there are unsaved changes
        # For simplicity, we're not implementing this check now
        tab_info = self.tabs[tab_id]
        filename = tab_info["filename"]
        if self.autosave_dir in filename:
            response = messagebox.askyesnocancel("Question", "Захаваць файл перад закрыццём?")
            if response is None:
                return False
            elif response:
                if not self.save_file_as():
                    return False
            else:
                try:
                    os.remove(filename)
                except FileNotFoundError:
                    print(f'File {filename} not found.')

        # # Autosave the tab before closing
        # self.autosave_tab(tab_id)

        # Remove the tab
        self.notebook.forget(self.tabs[tab_id]["frame"])

        # Remove from tabs dictionary
        del self.tabs[tab_id]

        # If there are no more tabs, create a new one
        if not self.tabs:
            self.create_new_tab()
        else:
            tid = len(self.tabs) - 1
            self.notebook.select(tid)
            self.current_file = tid

        self.fixed_tab_index = self.notebook.index("end") - 1  # Always last
        return True


def main():
    root = tk.Tk()
    TextEditor(root)
    root.mainloop()


if __name__ == "__main__":
    main()
