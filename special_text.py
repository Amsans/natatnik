import tkinter as tk
from tkinter import font

class SpecialCharText(tk.Text):
    def __init__(self, master, spec_chars=False, **kwargs):
        super().__init__(master, **kwargs)
        self.special_chars = {
            ' ': '·',
            '\t': '→',
            '\n': '¶\n'
        }
        self.display_chars = {}  # Map original positions to displayed glyphs
        self.show_special = spec_chars
        self.undo_stack = []  # Stack for undo actions
        self.redo_stack = []  # Stack for redo actions
        self.bind('<KeyRelease>', self.update_display)
        self.bind('<KeyPress>', self.handle_keypress)
        self.config(undo=False)  # Disable built-in undo to use custom stack

        current_font = self.cget("font")
        if isinstance(current_font, str) and current_font.startswith("{"):
            self.normal_font = font.Font(self, font=current_font)
        else:
            self.normal_font = font.nametofont(current_font)

        self.gray_font = font.Font(
            self,
            family=self.normal_font.cget("family"),
            size=self.normal_font.cget("size"),
            weight=self.normal_font.cget("weight"),
            slant=self.normal_font.cget("slant"),
            underline=self.normal_font.cget("underline"),
            overstrike=self.normal_font.cget("overstrike")
        )

    def handle_keypress(self, event):
        """Handle keypresses and manage undo/redo for single characters."""
        if event.char in self.special_chars or event.keysym in ('Return', 'Tab', 'space'):
            self.handle_special_char(event)
            return "break"  # Prevent default behavior
        elif event.keysym in ('BackSpace', 'Delete'):
            self.handle_delete(event)
            return "break"
        elif event.char and event.char.isprintable():
            self.handle_insert(event)
            return "break"
        return None

    def handle_insert(self, event):
        """Handle insertion of a single character with undo support."""
        sel = self.tag_ranges(tk.SEL)
        pos = self.index(tk.INSERT)
        if sel:
            text = self.get(sel[0], sel[1])
            self.delete(sel[0], sel[1])
            self.undo_stack.append(('delete', sel[0], sel[1], text))
            self.redo_stack.clear()
        char = event.char
        self.insert(pos, char)
        self.undo_stack.append(('insert', pos, char))
        self.redo_stack.clear()
        self.update_display()

    def handle_delete(self, event):
        """Handle deletion of a single character with undo support."""
        sel = self.tag_ranges(tk.SEL)
        if sel:
            text = self.get(sel[0], sel[1])
            self.delete(sel[0], sel[1])
            self.undo_stack.append(('delete', sel[0], sel[1], text))
            self.redo_stack.clear()
        else:
            pos = self.index(tk.INSERT)
            if event.keysym == 'BackSpace':
                if pos != "1.0":
                    prev_pos = self.index(f"{pos} - 1 char")
                    char = self.get(prev_pos, pos)
                    self.delete(prev_pos, pos)
                    self.undo_stack.append(('delete', prev_pos, pos, char))
                    self.redo_stack.clear()
            elif event.keysym == 'Delete':
                end_pos = self.index(f"{pos} + 1 char")
                if self.compare(end_pos, "<=", "end-1c"):
                    char = self.get(pos, end_pos)
                    self.delete(pos, end_pos)
                    self.undo_stack.append(('delete', pos, end_pos, char))
                    self.redo_stack.clear()
        self.update_display()

    def handle_special_char(self, event):
        """Insert special characters and their glyphs with undo support."""
        sel = self.tag_ranges(tk.SEL)
        pos = self.index(tk.INSERT)
        if sel:
            text = self.get(sel[0], sel[1])
            self.delete(sel[0], sel[1])
            self.undo_stack.append(('delete', sel[0], sel[1], text))
            self.redo_stack.clear()
        char = '\n' if event.keysym == 'Return' else '\t' if event.keysym == 'Tab' else event.char
        if char in self.special_chars:
            if self.show_special:
                display_char = self.special_chars[char]
                self.insert(pos, display_char)
                self.tag_add("special", pos)
                self.display_chars[pos] = char
                self.undo_stack.append(('insert', pos, display_char, char))
            else:
                self.insert(pos, char)
                self.undo_stack.append(('insert', pos, char))
            self.redo_stack.clear()

    def update_display(self, event=None):
        """Update display to show special character glyphs if enabled."""
        if not self.show_special:
            return  # Skip update if special chars are not shown

        # Save cursor position and selection
        cursor_pos = self.index(tk.INSERT)
        sel = self.tag_ranges(tk.SEL)
        sel_start, sel_end = (self.index(sel[0]), self.index(sel[1])) if sel else (None, None)

        # Get all text
        content = self.get("1.0", tk.END)[:-1]  # Exclude trailing newline
        self.delete("1.0", tk.END)  # Clear text widget
        self.display_chars.clear()  # Clear mapping

        # Re-insert text with glyphs
        for i, char in enumerate(content, start=1):
            line, col = divmod(i-1, len(content.split('\n')[0]) + 1)
            pos = f"{line+1}.{col}"
            if char in self.special_chars:
                self.insert(pos, self.special_chars[char])
                self.tag_add("special", pos)
                self.display_chars[pos] = char
            else:
                self.insert(pos, char)
            # Handle newline explicitly
            if char == '\n' and i < len(content):
                self.insert(pos, '\n')

        # Apply gray color to special characters
        self.tag_configure("special", foreground="gray", font=self.gray_font)

        # Restore cursor and selection
        self.mark_set(tk.INSERT, cursor_pos)
        if sel_start and sel_end:
            self.tag_add(tk.SEL, sel_start, sel_end)

    def toggle_spec_chars(self, show):
        """Toggle special character display and update content."""
        self.show_special = show
        cursor_pos = self.index(tk.INSERT)
        content = self.get("1.0", tk.END)[:-1]
        if self.show_special:
            content = content.replace(' ', '·')
            content = content.replace('\t', '→')
            content = content.replace('\n', '¶\n')
        else:
            content = content.replace('·', ' ')
            content = content.replace('→', '\t')
            content = content.replace('¶', '')
        self.delete("1.0", tk.END)
        self.insert("1.0", content)

        self.mark_set(tk.INSERT, cursor_pos)
        self.see(cursor_pos)

    def undo(self):
        """Undo the last single-character action."""
        if not self.undo_stack:
            return
        action = self.undo_stack.pop()
        if action[0] == 'insert':
            pos, char = action[1], action[2]
            self.delete(pos, f"{pos}+{len(char)}c")
            self.redo_stack.append(('insert', pos, char))
        elif action[0] == 'delete':
            start, end, text = action[1], action[2], action[3]
            self.insert(start, text)
            self.redo_stack.append(('delete', start, end, text))
        self.update_display()

    def redo(self):
        """Redo the last undone single-character action."""
        if not self.redo_stack:
            return
        action = self.redo_stack.pop()
        if action[0] == 'insert':
            pos, char = action[1], action[2]
            self.insert(pos, char)
            self.undo_stack.append(('insert', pos, char))
        elif action[0] == 'delete':
            start, end, text = action[1], action[2], action[3]
            self.delete(start, end)
            self.undo_stack.append(('delete', start, end, text))
        self.update_display()
