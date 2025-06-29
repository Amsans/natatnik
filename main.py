import json
import os
import textwrap
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, font as tkfont, PhotoImage

from text_widget import TextWidget

LABEL_FONT = ("Arial", 20)
ICON_FONT = ("Arial", 12)

BG_COLOR = "#000000"
FG_COLOR = "#FFFFFF"
FG_ACTIVE = "#e0e0e0"
BG_ACTIVE = "#4a4a4a"
SELECT_BG = "#25254C"

SLIDER_TROUGH_COLOR = "#2a2a2a"
SLIDER_HANDLE_COLOR = "#e0e0e0"
SLIDER_ACTIVE_COLOR = "#25254C"


class TextEditor:
    def __init__(self, root: tk.Tk):
        self.open_tabs = None
        self.cursor_positions = None  # Store cursor positions for tabs
        self.font_size_display = None
        self.font_size_var = None
        self.untitled_counter = 0
        self.fixed_tab_index = 1
        self.show_special = False
        self.selected_tab_index = None
        self.root = root
        self.root.title("Natatnik")
        self.root.geometry("1000x700")
        self.root.iconbitmap("img/icon.ico")

        self.default_font_size = 28
        self.settings_dir = os.path.join(os.path.expanduser("~"), ".natatnik")
        self.settings_file = os.path.join(self.settings_dir, "settings.json")
        self.autosave_dir = os.path.join(self.settings_dir, "autosave")

        # Create settings directory if it doesn't exist
        os.makedirs(self.settings_dir, exist_ok=True)
        os.makedirs(self.autosave_dir, exist_ok=True)

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

        # Dictionary to keep track of open files
        self.tabs = {}
        self.current_file = None

        status_bar = ttk.Frame(self.main_frame)
        status_bar.pack(side="bottom", fill="both", padx=5, pady=5)

        self.status_label = ttk.Label(status_bar, text="Радкоў: 0", font=("Arial", 18))
        self.status_label.pack(side="left", fill="x", padx=5, pady=5, expand=1)

        # Add file path label
        self.file_path_label = ttk.Label(status_bar, text="", font=("Arial", 12))
        self.file_path_label.pack(side="left", padx=5)

        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill="both", expand=True, padx=5, pady=5)

        # Add bindings for tab management
        self.notebook.bind("<Double-Button-1>", self.on_notebook_double_click)

        # Create menu
        self.create_menu()

        # Setup autosave
        self.setup_autosave()
        self.create_fixed_tab()

        # Load previously opened tabs
        self.load_tabs()

        # If no tabs were loaded, create a new one
        if not self.tabs:
            self.create_new_tab()

        self.select_tab_and_set_cursor()

        self.count_display_lines()

    def select_tab_and_set_cursor(self):
        self.notebook.select(self.selected_tab_index)
        filename = self.tabs[self.selected_tab_index]["filename"]
        cursor_pos = self.cursor_positions.get(filename, "1.0")
        text_widget = self.get_current_text_widget()
        text_widget.focus_set()
        text_widget.mark_set(tk.INSERT, cursor_pos)
        text_widget.see(cursor_pos)

    def configure_dark_theme(self):
        self.root.configure(bg=BG_COLOR)
        self.style.configure('TNotebook', background=BG_COLOR)
        self.style.configure('TNotebook.Tab', background=BG_COLOR, foreground=FG_COLOR, padding=[10, 2], font=("Consolas", 20, "bold"))
        self.style.map('TNotebook.Tab', background=[('selected', SELECT_BG)], foreground=[('selected', FG_COLOR)])
        self.style.configure('TFrame', background=BG_COLOR)
        self.style.configure('TButton', background=BG_COLOR, foreground=FG_COLOR, font=("Arial", 15))
        self.style.configure('TLabel', background=BG_COLOR, foreground=FG_COLOR)
        self.style.configure('Fg.TFrame', background=SELECT_BG, foreground=BG_COLOR)
        # Configure TScale for the slider
        self.style.configure('Horizontal.TScale', background=BG_COLOR, troughcolor=SLIDER_TROUGH_COLOR, bordercolor=BG_COLOR)
        self.style.map('Horizontal.TScale', background=[('active', SLIDER_ACTIVE_COLOR), ('!disabled', SLIDER_HANDLE_COLOR)],
                       troughcolor=[('active', SLIDER_TROUGH_COLOR)])

    def create_menu(self):
        menubar = tk.Menu(self.root, bg=BG_COLOR, fg=FG_ACTIVE, activebackground=BG_COLOR, activeforeground=FG_ACTIVE)
        self.root.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0, bg=BG_COLOR, fg=FG_ACTIVE, activebackground=BG_ACTIVE, activeforeground=FG_ACTIVE, font=LABEL_FONT)
        menubar.add_cascade(label="Файл", menu=file_menu, font=LABEL_FONT)
        file_menu.add_command(label="Новы", command=self.create_new_tab)
        file_menu.add_command(label="Адкрыць", command=self.open_file)
        file_menu.add_command(label="Захаваць", command=self.save_file)
        file_menu.add_command(label="Захаваць як...", command=self.save_file_as)
        file_menu.add_separator()
        file_menu.add_command(label="Выхад", command=self.on_window_close)

        # Edit menu
        edit_menu = tk.Menu(menubar, tearoff=0, bg=BG_COLOR, fg=FG_ACTIVE, activebackground=BG_ACTIVE, activeforeground=FG_ACTIVE, font=LABEL_FONT)
        menubar.add_cascade(label="Праўка", menu=edit_menu, font=LABEL_FONT)
        edit_menu.add_command(label="Адмяніць", command=self.undo)
        edit_menu.add_command(label="Паўтарыць", command=self.redo)
        edit_menu.add_separator()
        edit_menu.add_command(label="Выразаць", command=self.cut)
        edit_menu.add_command(label="Капіраваць", command=self.copy)
        edit_menu.add_command(label="Уставіць", command=self.paste)

    def create_font_size_control(self):
        # Create a frame for font size control
        toolbar = ttk.Frame(self.main_frame)
        toolbar.pack(side="top", fill="x", padx=5, pady=5)

        # Label for the slider
        font_size_label = ttk.Label(toolbar, text="Шрыфт:", font=("Arial", 15))
        font_size_label.pack(side="left", padx=5)

        # Create a slider for font size
        self.font_size_var = tk.IntVar(value=self.default_font_size)
        font_size_slider = ttk.Scale(toolbar, from_=10, to=80,
                                     orient="horizontal", length=200,
                                     variable=self.font_size_var, command=self.on_font_size_change)
        font_size_slider.pack(side="left", padx=5)

        # Display current font size value
        self.font_size_display = ttk.Label(toolbar, text=str(self.font_size_var.get()), font=LABEL_FONT)
        self.font_size_display.pack(side="left", padx=5)

        # Undo/Redo button group
        undo_redo_frame = ttk.Frame(toolbar)
        undo_redo_frame.pack(side="left", padx=(40, 10))  # Padding to separate from next group
        undo_image = PhotoImage(file="img/undo.png")
        undo_button = tk.Button(undo_redo_frame, text="Адмяніць", image=undo_image, compound="top", bg=BG_COLOR, fg=FG_COLOR, activebackground=FG_COLOR,
                                activeforeground=BG_COLOR, font=ICON_FONT, command=self.undo)
        undo_button.image = undo_image
        undo_button.pack(side="left", padx=0)

        redo_image = PhotoImage(file="img/redo.png")
        redo_button = tk.Button(undo_redo_frame, text="Паўтарыць", image=redo_image, compound="top", bg=BG_COLOR, fg=FG_COLOR, activebackground=FG_COLOR,
                                activeforeground=BG_COLOR, font=ICON_FONT, command=self.redo)
        redo_button.image = redo_image
        redo_button.pack(side="left", padx=0)

        # Cut/Copy/Paste button group
        clipboard_frame = ttk.Frame(toolbar)
        clipboard_frame.pack(side="left", padx=(0, 10))

        cut_image = PhotoImage(file="img/cut.png")
        cut_button = tk.Button(clipboard_frame, text="Выразаць", image=cut_image, compound="top", bg=BG_COLOR, fg=FG_COLOR, activebackground=FG_COLOR,
                               activeforeground=BG_COLOR, font=ICON_FONT, command=self.cut)
        cut_button.image = cut_image
        cut_button.pack(side="left", padx=0)

        copy_image = PhotoImage(file="img/copy.png")
        copy_button = tk.Button(clipboard_frame, text="Капіраваць", image=copy_image, compound="top", bg=BG_COLOR, fg=FG_COLOR, activebackground=FG_COLOR,
                                activeforeground=BG_COLOR, font=ICON_FONT, command=self.copy)
        copy_button.image = copy_image
        copy_button.pack(side="left", padx=0)

        paste_image = PhotoImage(file="img/paste.png")
        paste_button = tk.Button(clipboard_frame, text="Уставіць", image=paste_image, compound="top", bg=BG_COLOR, fg=FG_COLOR, activebackground=FG_COLOR,
                                 activeforeground=BG_COLOR, font=ICON_FONT, command=self.paste)
        paste_button.image = paste_image
        paste_button.pack(side="left", padx=0)

        spec_chars_image = PhotoImage(file="img/paragraph.png")
        spec_chars_button = tk.Button(toolbar, text="Спец. знакі", image=spec_chars_image, compound="top", bg=BG_COLOR, fg=FG_COLOR, activebackground=FG_COLOR,
                                      activeforeground=BG_COLOR, font=ICON_FONT, command=self.toggle_spec_chars)
        spec_chars_button.image = spec_chars_image
        spec_chars_button.pack(side="left", padx=(0, 10))

    def create_fixed_tab(self):
        fixed_frame = ttk.Frame(self.notebook)
        self.notebook.add(fixed_frame, text="+")
        self.fixed_tab_index = self.notebook.index("end") - 1
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)

    def on_tab_changed(self, event: tk.Event):
        selected_index = self.notebook.index("current")
        if selected_index == self.fixed_tab_index:
            self.create_new_tab()
            if self.tabs:
                self.notebook.select(len(self.tabs) - 1)
        else:
            # Update the file path label and selected tab index
            tab_id = None
            for tid, tab_info in self.tabs.items():
                if self.notebook.index(tab_info["frame"]) == selected_index:
                    tab_id = tid
                    break
            if tab_id is not None:
                self.current_file = tab_id
                file_path = self.tabs[tab_id]["filename"]
                self.tabs[tab_id]["file_path_label"].config(text=file_path)
                self.selected_tab_index = tab_id
                self.select_tab_and_set_cursor()
            self.count_display_lines()

    def create_new_tab(self, filename=None, content=None, cursor_pos=None):
        content_frame = ttk.Frame(self.notebook)
        toolbar = ttk.Frame(content_frame)
        toolbar.pack(side="top", fill="x")

        tab_id = len(self.tabs)
        close_button = ttk.Button(toolbar, text="Закрыць", command=lambda: self.close_tab(tab_id))
        close_button.pack(side="right", padx=3)

        text_frame = ttk.Frame(content_frame)
        text_frame.pack(fill="both", expand=True)
        scrollbar = ttk.Scrollbar(text_frame)
        scrollbar.pack(side="right", fill="y")
        text_widget = TextWidget(text_frame, yscrollcommand=scrollbar.set, wrap="word",
                                 bg="#000000", fg="#FFFFFF", insertbackground="#e0e0e0",
                                 selectbackground="#4a4a4a", selectforeground="#FFFFFF",
                                 font=("Times New Roman", self.default_font_size, "bold"), spec_chars=self.show_special)
        text_widget.pack(side="left", fill="both", expand=True)
        text_widget.bind("<KeyRelease>", self.on_text_change)
        scrollbar.config(command=text_widget.yview)
        if filename:
            tab_name = os.path.basename(filename)[:-4]
        else:
            tab_name = f"Новы{self.untitled_counter}"
            filename = os.path.join(self.autosave_dir, f"{tab_name}.txt")
            self.untitled_counter += 1
        self.notebook.insert(self.fixed_tab_index, content_frame, text=tab_name)
        tab_info = {
            "text_widget": text_widget,
            "filename": filename,
            "frame": content_frame,
            "autosave_filename": filename if not os.path.exists(filename) else None,
            "file_path_label": self.file_path_label
        }
        self.tabs[tab_id] = tab_info
        if content:
            text_widget.delete(1.0, tk.END)
            text_widget.insert(tk.END, content)
        if cursor_pos:
            text_widget.focus_set()
            text_widget.mark_set(tk.INSERT, cursor_pos)
        self.notebook.select(tab_id)
        self.current_file = tab_id
        # Update file path label for the new tab
        self.file_path_label.config(text=filename)
        self.count_display_lines()

        # Update fixed tab index since tab list changed
        self.fixed_tab_index = self.notebook.index("end") - 1
        self.save_settings()
        return tab_id

    def toggle_spec_chars(self):
        self.show_special = not self.show_special
        text_widget = self.get_current_text_widget()
        text_widget.toggle_spec_chars(self.show_special)

    def get_current_text_widget(self) -> TextWidget | None:
        if self.current_file is not None:
            return self.tabs[self.current_file]["text_widget"]
        return None

    def count_display_lines(self):
        tab_id = self.notebook.index(self.notebook.select())
        text_widget = self.tabs[tab_id]["text_widget"]
        text_widget.update_idletasks()

        text_font = tkfont.Font(font=text_widget['font'])
        widget_width_px = text_widget.winfo_width()
        avg_char_width = text_font.measure("n")
        chars_per_line = max(widget_width_px // avg_char_width, 1)
        full_text = text_widget.get("1.0", "end-1c")
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
                    tab_info["file_path_label"].config(text=filename)
                    self.save_settings()
                    return

            # Create new tab with file content
            try:
                with open(filename, "r", encoding="utf-8") as file:
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
            content = tab_info["text_widget"].get("1.0", "end-1c")
            with open(filename, "w", encoding="utf-8") as file:
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
            try:
                os.remove(old_filename)
            except OSError as e:
                print(e)
                pass
        tab_info["filename"] = filename
        tab_info["autosave_filename"] = None  # No longer an autosave file

        # Update tab name and file path label
        tab_index = self.notebook.index(self.notebook.select())
        self.notebook.tab(tab_index, text=os.path.basename(filename))
        tab_info["file_path_label"].config(text=filename)
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

    def undo(self):
        text_widget = self.get_current_text_widget()
        if text_widget:
            try:
                text_widget.undo()
                self.count_display_lines()
            except tk.TclError:
                # No more undo actions available; ignore
                pass

    def redo(self):
        text_widget = self.get_current_text_widget()
        if text_widget:
            try:
                text_widget.redo()
                self.count_display_lines()
            except tk.TclError:
                # No more redo actions available; ignore
                pass

    def load_settings(self):
        # Load settings from file
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding="utf-8") as f:
                    settings = json.load(f)
                    self.default_font_size = settings.get('font_size', self.default_font_size)
                    self.untitled_counter = settings.get('untitled_counter', 1)
                    self.open_tabs = settings.get('open_tabs', [])
                    self.cursor_positions = settings.get('cursor_positions', {})
                    self.selected_tab_index = settings.get('selected_tab_index', None)
                    self.show_special = settings.get('show_special', False)
        except Exception as e:
            print(f"Error loading settings: {e}")
            self.open_tabs = []
            self.cursor_positions = {}
            self.selected_tab_index = None

    def save_settings(self):
        # Save settings to file, including open tabs and selected tab index
        try:
            # Get current open tabs in order
            open_tabs = []
            cursor_positions = {}
            for i in range(self.notebook.index("end") - 1):
                tab_id = None
                for tid, tab_info in self.tabs.items():
                    if self.notebook.index(tab_info["frame"]) == i:
                        tab_id = tid
                        break
                if tab_id is not None:
                    filename = self.tabs[tab_id]["filename"]
                    open_tabs.append(filename)
                    cursor_positions[filename] = self.tabs[tab_id]["text_widget"].index(tk.INSERT)
            settings = {
                'font_size': self.default_font_size,
                'untitled_counter': self.untitled_counter,
                'open_tabs': open_tabs,
                'cursor_positions': cursor_positions,
                'selected_tab_index': self.notebook.index("current"),
                'show_special': self.show_special
            }
            with open(self.settings_file, 'w', encoding="utf-8") as f:
                json.dump(settings, f, indent=2)
        except Exception as e:
            print(f"Error saving settings: {e}")

    # noinspection PyTypeChecker
    def setup_autosave(self):
        # Set up autosave to run every 30 seconds
        self.autosave()
        self.root.after(30000, self.setup_autosave)
        self.root.protocol("WM_DELETE_WINDOW", self.on_window_close)

    def on_window_close(self):
        self.autosave()
        self.save_settings()
        self.root.destroy()

    def autosave(self):
        # Save all tabs
        for tab_id, tab_info in self.tabs.items():
            self.autosave_tab(tab_id)

    def autosave_tab(self, tab_id):
        tab_info = self.tabs[tab_id]
        filename = tab_info["filename"]

        # Get content without trailing newline
        content = tab_info["text_widget"].get("1.0", "end-1c")

        # Save to file
        try:
            with open(filename, 'w', encoding="utf-8") as f:
                f.write(content)
        except Exception as e:
            print(f"Error autosaving tab {tab_id}: {e}")

    def load_tabs(self):
        # Load tabs from settings.json
        try:
            tab_ids = {}
            # Load open tabs from settings
            for filename in self.open_tabs:
                if os.path.exists(filename):
                    try:
                        with open(filename, 'r', encoding="utf-8") as f:
                            content = f.read()
                        cursor_pos = self.cursor_positions.get(filename, "1.0")
                        tab_id = self.create_new_tab(filename, content, cursor_pos)
                        tab_ids[filename] = tab_id
                    except Exception as e:
                        print(f"Error loading tab {filename}: {e}")
            autosave_files = [f for f in os.listdir(self.autosave_dir) if f.endswith('.txt')]
            for filename in autosave_files:
                full_path = os.path.join(self.autosave_dir, filename)
                if full_path not in self.open_tabs:
                    try:
                        with open(full_path, 'r', encoding="utf-8") as f:
                            content = f.read()
                        cursor_pos = self.cursor_positions.get(full_path, "1.0")
                        tab_id = self.create_new_tab(full_path, content, cursor_pos)
                        tab_ids[full_path] = tab_id
                    except Exception as e:
                        print(f"Error loading tab {filename}: {e}")

            # Update untitled_counter based on autosave files
            highest_num = 0
            for filename in autosave_files:
                if filename.startswith('Новы'):
                    try:
                        num = int(filename[4:-4])  # Extract number from "Новы{num}.txt"
                        highest_num = max(highest_num, num)
                    except ValueError:
                        pass
            self.untitled_counter = max(self.untitled_counter or 1, highest_num + 1)

            # Select the saved tab index, if valid
            if self.selected_tab_index is not None and self.tabs:
                # Ensure the index is valid (not exceeding the number of tabs, excluding the fixed "+" tab)
                max_index = self.notebook.index("end") - 2  # Subtract 1 for 0-based indexing and 1 for fixed tab
                if 0 <= self.selected_tab_index <= max_index:
                    tab_id = None
                    for tid, tab_info in self.tabs.items():
                        if self.notebook.index(tab_info["frame"]) == self.selected_tab_index:
                            tab_id = tid
                            break
                    if tab_id is not None:
                        self.notebook.select(self.selected_tab_index)
                        self.current_file = tab_id
                        self.tabs[tab_id]["file_path_label"].config(text=self.tabs[tab_id]["filename"])
                        self.count_display_lines()
                        self.get_current_text_widget().toggle_spec_chars(self.show_special)
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
        for tab_id, tab_info in self.tabs.items():
            text_widget = tab_info["text_widget"]
            text_widget.configure(font=("Times New Roman", self.default_font_size, "bold"))

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
        except (ValueError, tk.TclError) as err:
            print(err)

    def close_tab(self, tab_id):
        # Check if there are unsaved changes
        tab_info = self.tabs[tab_id]
        filename = tab_info["filename"]
        if self.autosave_dir in filename:
            response = messagebox.askyesnocancel("Захаваць?", "Захаваць файл перад закрыццём?")
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
            self.selected_tab_index = self.notebook.index("current")
            self.save_settings()
        self.fixed_tab_index = self.notebook.index("end") - 1
        return True

def _onKeyRelease(event):
    ctrl = (event.state & 0x4) != 0
    if event.keycode == 88 and ctrl and event.keysym.lower() != "x":
        event.widget.event_generate("<<Cut>>")

    if event.keycode == 86 and ctrl and event.keysym.lower() != "v":
        event.widget.event_generate("<<Paste>>")

    if event.keycode == 67 and ctrl and event.keysym.lower() != "c":
        event.widget.event_generate("<<Copy>>")


def main():
    root = tk.Tk()
    TextEditor(root)
    root.state('zoomed')
    root.bind_all("<Key>", _onKeyRelease, "+")
    root.mainloop()


if __name__ == "__main__":
    main()
