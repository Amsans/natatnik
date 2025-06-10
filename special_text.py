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
        self.bind('<KeyRelease>', self.update_display)
        self.bind('<KeyPress>', self.handle_keypress)
        self.config(undo=True)  # Enable undo for better user experience

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
        """Prevent default insertion of special characters and handle manually."""
        if event.char in self.special_chars or event.keysym in ('Return', 'Tab', 'space'):
            self.handle_special_char(event)
            return "break"  # Prevent default behavior
        elif event.keysym in ('BackSpace', 'Delete'):
            return None
        return None

    def handle_special_char(self, event):
        """Insert special characters and their glyphs."""
        sel = self.tag_ranges(tk.SEL)
        if sel:
            self.delete(sel[0], sel[1])  # Delete selected text
        pos = self.index(tk.INSERT)
        char = '\n' if event.keysym == 'Return' else '\t' if event.keysym == 'Tab' else event.char
        if char in self.special_chars:
            if self.show_special:
                self.insert(pos, self.special_chars[char])  # Insert glyph
                self.tag_add("special", pos)
                self.display_chars[pos] = char  # Map glyph to original char
            else:
                self.insert(pos, char)  # Insert actual character

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
        self.show_special = show
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