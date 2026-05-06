import json
import tkinter as tk
from tkinter import ttk, messagebox, filedialog


class JSONFormatterApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title('Local JSON Formatter')
        self.root.geometry('1200x700')
        self.root.minsize(900, 550)

        self.indent_var = tk.StringVar(value='4')
        self.sort_keys_var = tk.BooleanVar(value=False)
        self.status_var = tk.StringVar(value='Ready')

        self._build_ui()

    def _build_ui(self) -> None:
        top = ttk.Frame(self.root, padding=10)
        top.pack(fill='x')

        ttk.Button(top, text='Format JSON', command=self.format_json).pack(side='left', padx=(0, 8))
        ttk.Button(top, text='Minify JSON', command=self.minify_json).pack(side='left', padx=(0, 8))
        ttk.Button(top, text='Validate', command=self.validate_json).pack(side='left', padx=(0, 8))
        ttk.Button(top, text='Clear', command=self.clear_all).pack(side='left', padx=(0, 8))
        ttk.Button(top, text='Load File', command=self.load_file).pack(side='left', padx=(0, 8))
        ttk.Button(top, text='Save Output', command=self.save_output).pack(side='left', padx=(0, 8))
        ttk.Button(top, text='Copy Output', command=self.copy_output).pack(side='left', padx=(0, 8))

        ttk.Label(top, text='Indent:').pack(side='left', padx=(18, 6))
        indent_box = ttk.Combobox(top, textvariable=self.indent_var, values=['2', '4', '8'], width=5, state='readonly')
        indent_box.pack(side='left')

        ttk.Checkbutton(top, text='Sort keys', variable=self.sort_keys_var).pack(side='left', padx=(18, 0))

        paned = ttk.Panedwindow(self.root, orient='horizontal')
        paned.pack(fill='both', expand=True, padx=10, pady=(0, 10))

        left_frame = ttk.Labelframe(paned, text='Input JSON', padding=8)
        right_frame = ttk.Labelframe(paned, text='Formatted Output', padding=8)
        paned.add(left_frame, weight=1)
        paned.add(right_frame, weight=1)

        self.input_text = self._add_text_with_scrollbars(left_frame)
        self.output_text = self._add_text_with_scrollbars(right_frame)

        status = ttk.Label(self.root, textvariable=self.status_var, relief='sunken', anchor='w', padding=(10, 6))
        status.pack(fill='x', side='bottom')

    def _add_text_with_scrollbars(self, parent: ttk.Labelframe) -> tk.Text:
        container = ttk.Frame(parent)
        container.pack(fill='both', expand=True)

        text_widget = tk.Text(container, wrap='none', undo=True, font=('Consolas', 11))
        y_scroll = ttk.Scrollbar(container, orient='vertical', command=text_widget.yview)
        x_scroll = ttk.Scrollbar(container, orient='horizontal', command=text_widget.xview)
        text_widget.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)

        text_widget.grid(row=0, column=0, sticky='nsew')
        y_scroll.grid(row=0, column=1, sticky='ns')
        x_scroll.grid(row=1, column=0, sticky='ew')

        container.rowconfigure(0, weight=1)
        container.columnconfigure(0, weight=1)
        return text_widget

    def _get_input(self) -> str:
        return self.input_text.get('1.0', 'end').strip()

    def _set_output(self, text: str) -> None:
        self.output_text.delete('1.0', 'end')
        self.output_text.insert('1.0', text)

    def _parse_json(self):
        raw = self._get_input()
        if not raw:
            raise ValueError('Input is empty.')
        return json.loads(raw)

    def format_json(self) -> None:
        try:
            parsed = self._parse_json()
            indent = int(self.indent_var.get())
            result = json.dumps(parsed, indent=indent, sort_keys=self.sort_keys_var.get(), ensure_ascii=False)
            self._set_output(result)
            self.status_var.set('JSON formatted successfully.')
        except Exception as exc:
            self.status_var.set('Invalid JSON.')
            messagebox.showerror('Format Error', f'Could not format JSON.\n\n{exc}')

    def minify_json(self) -> None:
        try:
            parsed = self._parse_json()
            result = json.dumps(parsed, separators=(',', ':'), ensure_ascii=False)
            self._set_output(result)
            self.status_var.set('JSON minified successfully.')
        except Exception as exc:
            self.status_var.set('Invalid JSON.')
            messagebox.showerror('Minify Error', f'Could not minify JSON.\n\n{exc}')

    def validate_json(self) -> None:
        try:
            self._parse_json()
            self.status_var.set('JSON is valid.')
            messagebox.showinfo('Validation Result', 'JSON is valid.')
        except Exception as exc:
            self.status_var.set('JSON is invalid.')
            messagebox.showerror('Validation Result', f'JSON is invalid.\n\n{exc}')

    def clear_all(self) -> None:
        self.input_text.delete('1.0', 'end')
        self.output_text.delete('1.0', 'end')
        self.status_var.set('Cleared.')

    def load_file(self) -> None:
        path = filedialog.askopenfilename(
            title='Open JSON file',
            filetypes=[('JSON files', '*.json'), ('Text files', '*.txt'), ('All files', '*.*')],
        )
        if not path:
            return
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            self.input_text.delete('1.0', 'end')
            self.input_text.insert('1.0', content)
            self.status_var.set(f'Loaded file: {path}')
        except Exception as exc:
            messagebox.showerror('Load Error', f'Could not load file.\n\n{exc}')

    def save_output(self) -> None:
        content = self.output_text.get('1.0', 'end').strip()
        if not content:
            messagebox.showwarning('Save Output', 'There is no output to save.')
            return

        path = filedialog.asksaveasfilename(
            title='Save formatted JSON',
            defaultextension='.json',
            filetypes=[('JSON files', '*.json'), ('Text files', '*.txt'), ('All files', '*.*')],
        )
        if not path:
            return
        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            self.status_var.set(f'Saved output: {path}')
        except Exception as exc:
            messagebox.showerror('Save Error', f'Could not save file.\n\n{exc}')

    def copy_output(self) -> None:
        content = self.output_text.get('1.0', 'end').strip()
        if not content:
            messagebox.showwarning('Copy Output', 'There is no output to copy.')
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(content)
        self.status_var.set('Output copied to clipboard.')


if __name__ == '__main__':
    root = tk.Tk()
    try:
        style = ttk.Style()
        if 'vista' in style.theme_names():
            style.theme_use('vista')
    except Exception:
        pass
    app = JSONFormatterApp(root)
    root.mainloop()
