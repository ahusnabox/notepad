#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Notepad - Klon Notepad sederhana untuk Windows (dan OS lain)
Dibuat dengan Python + tkinter (bawaan Python, tanpa instalasi tambahan).

Cara menjalankan:
    python notepad.py

Fitur:
    - Berkas: Baru, Buka, Simpan, Simpan Sebagai, Keluar
    - Edit: Undo/Redo, Potong/Salin/Tempel, Pilih Semua, Hapus
    - Cari & Ganti
    - Sisipkan tanggal/waktu (F5)
    - Word wrap (rata kata)
    - Ganti font
    - Zoom in / Zoom out / reset
    - Status bar: posisi baris & kolom
    - Pintasan keyboard standar
    - Konfirmasi simpan jika ada perubahan belum disimpan
"""

import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, font as tkfont


class Notepad:
    def __init__(self, root):
        self.root = root
        self.filename = None          # path berkas yang sedang dibuka
        self.text_modified = False    # apakah ada perubahan belum disimpan

        # ----- Font default -----
        self.current_family = "Consolas"
        self.current_size = 12
        self.text_font = tkfont.Font(family=self.current_family, size=self.current_size)

        # ----- Area teks + scrollbar -----
        self.text_frame = tk.Frame(root)
        self.text_frame.pack(fill="both", expand=True)

        self.scroll_y = ttk.Scrollbar(self.text_frame, orient="vertical")
        self.scroll_y.pack(side="right", fill="y")

        self.text = tk.Text(
            self.text_frame,
            wrap="word",
            undo=True,
            maxundo=-1,
            font=self.text_font,
            yscrollcommand=self.scroll_y.set,
            relief="flat",
            padx=6,
            pady=4,
        )
        self.text.pack(fill="both", expand=True)
        self.scroll_y.config(command=self.text.yview)

        # ----- Status bar -----
        self.status = tk.Label(root, text="Baris 1, Kolom 1", anchor="e", padx=8)
        self.status.pack(side="bottom", fill="x")

        self.word_wrap = tk.BooleanVar(value=True)

        self._build_menu()
        self._bind_events()
        self._update_title()
        self._update_status()

    # ============================================================== MENU
    def _build_menu(self):
        menubar = tk.Menu(self.root)

        # --- Berkas ---
        m_file = tk.Menu(menubar, tearoff=0)
        m_file.add_command(label="Baru", accelerator="Ctrl+N", command=self.new_file)
        m_file.add_command(label="Buka...", accelerator="Ctrl+O", command=self.open_file)
        m_file.add_command(label="Simpan", accelerator="Ctrl+S", command=self.save_file)
        m_file.add_command(label="Simpan Sebagai...", accelerator="Ctrl+Shift+S",
                           command=self.save_file_as)
        m_file.add_separator()
        m_file.add_command(label="Keluar", accelerator="Ctrl+Q", command=self.on_exit)
        menubar.add_cascade(label="Berkas", menu=m_file)

        # --- Edit ---
        m_edit = tk.Menu(menubar, tearoff=0)
        m_edit.add_command(label="Urungkan", accelerator="Ctrl+Z", command=self.undo)
        m_edit.add_command(label="Ulangi", accelerator="Ctrl+Y", command=self.redo)
        m_edit.add_separator()
        m_edit.add_command(label="Potong", accelerator="Ctrl+X",
                           command=lambda: self.text.event_generate("<<Cut>>"))
        m_edit.add_command(label="Salin", accelerator="Ctrl+C",
                           command=lambda: self.text.event_generate("<<Copy>>"))
        m_edit.add_command(label="Tempel", accelerator="Ctrl+V",
                           command=lambda: self.text.event_generate("<<Paste>>"))
        m_edit.add_command(label="Hapus", accelerator="Del", command=self.delete_selection)
        m_edit.add_separator()
        m_edit.add_command(label="Cari & Ganti...", accelerator="Ctrl+F",
                           command=self.open_find_replace)
        m_edit.add_command(label="Sisipkan Tanggal/Waktu", accelerator="F5",
                           command=self.insert_datetime)
        m_edit.add_separator()
        m_edit.add_command(label="Pilih Semua", accelerator="Ctrl+A", command=self.select_all)
        menubar.add_cascade(label="Edit", menu=m_edit)

        # --- Format ---
        m_format = tk.Menu(menubar, tearoff=0)
        m_format.add_checkbutton(label="Word Wrap", onvalue=True, offvalue=False,
                                 variable=self.word_wrap, command=self.toggle_wrap)
        m_format.add_command(label="Font...", command=self.choose_font)
        menubar.add_cascade(label="Format", menu=m_format)

        # --- Tampilan ---
        m_view = tk.Menu(menubar, tearoff=0)
        m_view.add_command(label="Perbesar", accelerator="Ctrl++", command=self.zoom_in)
        m_view.add_command(label="Perkecil", accelerator="Ctrl+-", command=self.zoom_out)
        m_view.add_command(label="Reset Zoom", accelerator="Ctrl+0", command=self.zoom_reset)
        menubar.add_cascade(label="Tampilan", menu=m_view)

        # --- Bantuan ---
        m_help = tk.Menu(menubar, tearoff=0)
        m_help.add_command(label="Tentang", command=self.show_about)
        menubar.add_cascade(label="Bantuan", menu=m_help)

        self.root.config(menu=menubar)

    # ============================================================ BINDINGS
    def _bind_events(self):
        self.text.bind("<<Modified>>", self._on_modified)
        self.text.bind("<KeyRelease>", lambda e: self._update_status())
        self.text.bind("<ButtonRelease>", lambda e: self._update_status())

        b = self.root.bind_all
        b("<Control-n>", lambda e: self.new_file())
        b("<Control-o>", lambda e: self.open_file())
        b("<Control-s>", lambda e: self.save_file())
        b("<Control-S>", lambda e: self.save_file_as())   # Ctrl+Shift+S
        b("<Control-q>", lambda e: self.on_exit())
        b("<Control-f>", lambda e: self.open_find_replace())
        b("<Control-a>", lambda e: self.select_all())
        b("<Control-y>", lambda e: self.redo())
        b("<F5>", lambda e: self.insert_datetime())
        b("<Control-plus>", lambda e: self.zoom_in())
        b("<Control-equal>", lambda e: self.zoom_in())
        b("<Control-minus>", lambda e: self.zoom_out())
        b("<Control-0>", lambda e: self.zoom_reset())

        self.root.protocol("WM_DELETE_WINDOW", self.on_exit)

    # ====================================================== STATUS & TITLE
    def _on_modified(self, event=None):
        # event <<Modified>> butuh reset flag agar terpanggil lagi
        if self.text.edit_modified():
            self.text_modified = True
            self._update_title()
            self.text.edit_modified(False)

    def _update_title(self):
        name = os.path.basename(self.filename) if self.filename else "Tanpa Judul"
        mark = "*" if self.text_modified else ""
        self.root.title(f"{mark}{name} - Notepad")

    def _update_status(self):
        pos = self.text.index("insert")
        line, col = pos.split(".")
        self.status.config(text=f"Baris {line}, Kolom {int(col) + 1}")

    # ========================================================= FILE ACTIONS
    def _confirm_discard(self):
        """Tanya simpan jika ada perubahan. Return True jika boleh lanjut."""
        if not self.text_modified:
            return True
        res = messagebox.askyesnocancel(
            "Notepad",
            "Simpan perubahan pada dokumen ini?"
        )
        if res is None:          # Cancel
            return False
        if res:                  # Yes
            return self.save_file()
        return True              # No

    def new_file(self):
        if not self._confirm_discard():
            return
        self.text.delete("1.0", "end")
        self.filename = None
        self.text_modified = False
        self.text.edit_reset()
        self._update_title()
        self._update_status()

    def open_file(self):
        if not self._confirm_discard():
            return
        path = filedialog.askopenfilename(
            defaultextension=".txt",
            filetypes=[("Berkas Teks", "*.txt"), ("Semua Berkas", "*.*")],
        )
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
        except UnicodeDecodeError:
            with open(path, "r", encoding="latin-1") as f:
                content = f.read()
        except Exception as e:
            messagebox.showerror("Notepad", f"Gagal membuka berkas:\n{e}")
            return

        self.text.delete("1.0", "end")
        self.text.insert("1.0", content)
        self.filename = path
        self.text_modified = False
        self.text.edit_reset()
        self._update_title()
        self._update_status()

    def save_file(self):
        if self.filename is None:
            return self.save_file_as()
        return self._write_to(self.filename)

    def save_file_as(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Berkas Teks", "*.txt"), ("Semua Berkas", "*.*")],
        )
        if not path:
            return False
        if self._write_to(path):
            self.filename = path
            self._update_title()
            return True
        return False

    def _write_to(self, path):
        try:
            content = self.text.get("1.0", "end-1c")
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            self.text_modified = False
            self._update_title()
            return True
        except Exception as e:
            messagebox.showerror("Notepad", f"Gagal menyimpan berkas:\n{e}")
            return False

    def on_exit(self):
        if self._confirm_discard():
            self.root.destroy()

    # ========================================================= EDIT ACTIONS
    def undo(self):
        try:
            self.text.edit_undo()
        except tk.TclError:
            pass

    def redo(self):
        try:
            self.text.edit_redo()
        except tk.TclError:
            pass

    def delete_selection(self):
        if self.text.tag_ranges("sel"):
            self.text.delete("sel.first", "sel.last")

    def select_all(self):
        self.text.tag_add("sel", "1.0", "end-1c")
        return "break"

    def insert_datetime(self):
        from datetime import datetime
        now = datetime.now().strftime("%H:%M %d/%m/%Y")
        self.text.insert("insert", now)

    # ============================================================= FORMAT
    def toggle_wrap(self):
        self.text.config(wrap="word" if self.word_wrap.get() else "none")

    def choose_font(self):
        FontDialog(self.root, self)

    def apply_font(self, family, size):
        self.current_family = family
        self.current_size = size
        self.text_font.config(family=family, size=size)

    # ============================================================== ZOOM
    def zoom_in(self):
        self.current_size = min(self.current_size + 1, 72)
        self.text_font.config(size=self.current_size)

    def zoom_out(self):
        self.current_size = max(self.current_size - 1, 6)
        self.text_font.config(size=self.current_size)

    def zoom_reset(self):
        self.current_size = 12
        self.text_font.config(size=self.current_size)

    # ============================================================== ABOUT
    def show_about(self):
        messagebox.showinfo(
            "Tentang Notepad",
            "Notepad sederhana\nDibuat dengan Python + tkinter\n\n"
            "Pintasan:\n"
            "Ctrl+N Baru   Ctrl+O Buka   Ctrl+S Simpan\n"
            "Ctrl+F Cari & Ganti   F5 Tanggal/Waktu\n"
            "Ctrl++ / Ctrl+- Zoom"
        )

    # ========================================================= FIND & REPLACE
    def open_find_replace(self):
        FindReplaceDialog(self.root, self.text)


# ===================================================================== DIALOGS
class FindReplaceDialog(tk.Toplevel):
    """Jendela Cari & Ganti."""
    def __init__(self, parent, text_widget):
        super().__init__(parent)
        self.text = text_widget
        self.title("Cari & Ganti")
        self.resizable(False, False)
        self.transient(parent)
        self.last_index = "1.0"

        tk.Label(self, text="Cari:").grid(row=0, column=0, padx=6, pady=6, sticky="e")
        self.find_entry = tk.Entry(self, width=30)
        self.find_entry.grid(row=0, column=1, padx=6, pady=6)
        self.find_entry.focus_set()

        tk.Label(self, text="Ganti:").grid(row=1, column=0, padx=6, pady=6, sticky="e")
        self.replace_entry = tk.Entry(self, width=30)
        self.replace_entry.grid(row=1, column=1, padx=6, pady=6)

        self.case_var = tk.BooleanVar(value=False)
        tk.Checkbutton(self, text="Cocokkan huruf besar/kecil",
                       variable=self.case_var).grid(row=2, column=1, sticky="w", padx=6)

        btns = tk.Frame(self)
        btns.grid(row=0, column=2, rowspan=3, padx=6, pady=6)
        tk.Button(btns, text="Cari Berikutnya", width=14,
                  command=self.find_next).pack(pady=2)
        tk.Button(btns, text="Ganti", width=14, command=self.replace_one).pack(pady=2)
        tk.Button(btns, text="Ganti Semua", width=14,
                  command=self.replace_all).pack(pady=2)

        self.text.tag_config("found", background="yellow", foreground="black")
        self.protocol("WM_DELETE_WINDOW", self.close)

    def _clear_tags(self):
        self.text.tag_remove("found", "1.0", "end")

    def find_next(self):
        self._clear_tags()
        query = self.find_entry.get()
        if not query:
            return
        idx = self.text.search(query, self.last_index, nocase=not self.case_var.get(),
                               stopindex="end")
        if not idx:
            # ulang dari awal
            idx = self.text.search(query, "1.0", nocase=not self.case_var.get(),
                                   stopindex="end")
            if not idx:
                messagebox.showinfo("Cari", f"'{query}' tidak ditemukan.", parent=self)
                return
        end = f"{idx}+{len(query)}c"
        self.text.tag_add("found", idx, end)
        self.text.mark_set("insert", end)
        self.text.see(idx)
        self.last_index = end

    def replace_one(self):
        if self.text.tag_ranges("found"):
            start = self.text.index("found.first")
            end = self.text.index("found.last")
            self.text.delete(start, end)
            self.text.insert(start, self.replace_entry.get())
            self.last_index = f"{start}+{len(self.replace_entry.get())}c"
        self.find_next()

    def replace_all(self):
        query = self.find_entry.get()
        repl = self.replace_entry.get()
        if not query:
            return
        self._clear_tags()
        content = self.text.get("1.0", "end-1c")
        if self.case_var.get():
            count = content.count(query)
            new_content = content.replace(query, repl)
        else:
            import re
            pattern = re.compile(re.escape(query), re.IGNORECASE)
            count = len(pattern.findall(content))
            new_content = pattern.sub(repl.replace("\\", "\\\\"), content)
        if count:
            self.text.delete("1.0", "end")
            self.text.insert("1.0", new_content)
        messagebox.showinfo("Ganti Semua", f"{count} kemunculan diganti.", parent=self)

    def close(self):
        self._clear_tags()
        self.destroy()


class FontDialog(tk.Toplevel):
    """Jendela pemilihan font sederhana."""
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.title("Font")
        self.resizable(False, False)
        self.transient(parent)

        families = sorted(set(tkfont.families()))

        tk.Label(self, text="Font:").grid(row=0, column=0, padx=6, pady=4, sticky="w")
        tk.Label(self, text="Ukuran:").grid(row=0, column=1, padx=6, pady=4, sticky="w")

        self.family_var = tk.StringVar(value=app.current_family)
        self.family_box = ttk.Combobox(self, values=families,
                                       textvariable=self.family_var, width=28)
        self.family_box.grid(row=1, column=0, padx=6, pady=4)

        self.size_var = tk.IntVar(value=app.current_size)
        sizes = [8, 9, 10, 11, 12, 14, 16, 18, 20, 24, 28, 32, 36, 48, 72]
        self.size_box = ttk.Combobox(self, values=sizes,
                                     textvariable=self.size_var, width=6)
        self.size_box.grid(row=1, column=1, padx=6, pady=4)

        self.preview = tk.Label(self, text="Contoh teks AaBbCc 123",
                                width=36, height=2, relief="groove")
        self.preview.grid(row=2, column=0, columnspan=2, padx=6, pady=8)

        self.family_box.bind("<<ComboboxSelected>>", lambda e: self._update_preview())
        self.size_box.bind("<<ComboboxSelected>>", lambda e: self._update_preview())
        self._update_preview()

        tk.Button(self, text="Terapkan", width=12, command=self.apply).grid(
            row=3, column=0, columnspan=2, pady=6)

    def _update_preview(self):
        try:
            self.preview.config(font=(self.family_var.get(), self.size_var.get()))
        except tk.TclError:
            pass

    def apply(self):
        self.app.apply_font(self.family_var.get(), self.size_var.get())
        self.destroy()


def main():
    root = tk.Tk()
    root.geometry("900x600")
    Notepad(root)
    root.mainloop()


if __name__ == "__main__":
    main()
