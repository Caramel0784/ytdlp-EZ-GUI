#!/usr/bin/env python3
"""
yt-dlp GUI — just double-click to run!
Requires: pip install yt-dlp   (or place yt-dlp binary in same folder)
"""

import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext
import subprocess, threading, sys, os, shutil

# ── find yt-dlp binary ──────────────────────────────────────────────────────
def find_ytdlp():
    # 1. same folder as this script
    local = os.path.join(os.path.dirname(os.path.abspath(__file__)), "yt-dlp")
    if os.path.isfile(local):
        return local
    local_exe = local + ".exe"
    if os.path.isfile(local_exe):
        return local_exe
    # 2. system PATH
    found = shutil.which("yt-dlp")
    if found:
        return found
    # 3. pip-installed module fallback
    return None

YTDLP = find_ytdlp()

# ── colours ─────────────────────────────────────────────────────────────────
BG       = "#0f0f11"
SURFACE  = "#18181c"
SURFACE2 = "#222228"
BORDER   = "#2e2e38"
ACCENT   = "#7c6af7"
TEXT     = "#e8e8f0"
MUTED    = "#7a7a92"
GREEN    = "#34d399"
RED      = "#f87171"
YELLOW   = "#fbbf24"
MONO     = ("Consolas", 11) if sys.platform == "win32" else ("Monospace", 11)
SANS     = ("Segoe UI", 10) if sys.platform == "win32" else ("Sans", 10)
SANS_B   = ("Segoe UI Bold", 10) if sys.platform == "win32" else ("Sans Bold", 10)

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("yt-dlp GUI")
        self.configure(bg=BG)
        self.resizable(True, True)
        self.geometry("740x780")
        self.minsize(600, 600)

        self._build_ui()
        self._update_type()

    # ── UI builder ────────────────────────────────────────────────────────
    def _build_ui(self):
        pad = dict(padx=16, pady=6)

        # header
        hdr = tk.Frame(self, bg=BG)
        hdr.pack(fill="x", padx=16, pady=(18, 4))
        tk.Label(hdr, text="⬇  yt-dlp GUI", font=("Segoe UI Bold", 17) if sys.platform=="win32" else ("Sans Bold", 17),
                 bg=BG, fg=TEXT).pack(side="left")

        # binary status
        status_color = GREEN if YTDLP else RED
        status_text  = f"✓ found: {os.path.basename(YTDLP)}" if YTDLP else "✗ yt-dlp not found — install it first"
        tk.Label(hdr, text=status_text, font=MONO, bg=BG, fg=status_color).pack(side="right", padx=4)

        self._sep()

        # URL
        self._label("Video / Playlist URL")
        self.url_var = tk.StringVar()
        url_entry = tk.Entry(self, textvariable=self.url_var, font=SANS,
                             bg=SURFACE, fg=TEXT, insertbackground=TEXT,
                             relief="flat", highlightthickness=1,
                             highlightbackground=BORDER, highlightcolor=ACCENT)
        url_entry.pack(fill="x", **pad)

        self._sep()

        # type buttons
        self._label("Download type")
        type_row = tk.Frame(self, bg=BG)
        type_row.pack(fill="x", padx=16, pady=4)
        self.type_var = tk.StringVar(value="video")
        for val, label, icon in [("video","Video","🎬"), ("audio","Audio only","🎵"), ("playlist","Playlist","📋")]:
            b = tk.Button(type_row, text=f"{icon}  {label}", font=SANS_B,
                          bg=SURFACE2, fg=MUTED, activebackground=ACCENT, activeforeground=TEXT,
                          relief="flat", padx=18, pady=8, cursor="hand2",
                          command=lambda v=val: self._set_type(v))
            b.pack(side="left", expand=True, fill="x", padx=4)
            setattr(self, f"btn_{val}", b)

        self._sep()

        # video options frame
        self.video_frame = tk.Frame(self, bg=BG)
        self._label("Quality", parent=self.video_frame)
        vrow = tk.Frame(self.video_frame, bg=BG)
        vrow.pack(fill="x", padx=16, pady=4)

        self.quality_var = tk.StringVar(value="bestvideo+bestaudio/best")
        q_opts = [
            ("Best available",          "bestvideo+bestaudio/best"),
            ("Max 1080p",               "bestvideo[height<=1080]+bestaudio/best[height<=1080]"),
            ("Max 720p",                "bestvideo[height<=720]+bestaudio/best[height<=720]"),
            ("Max 480p",                "bestvideo[height<=480]+bestaudio/best[height<=480]"),
            ("Smallest file",           "worstvideo+worstaudio/worst"),
        ]
        q_cb = ttk.Combobox(vrow, textvariable=self.quality_var, values=[x[0] for x in q_opts],
                            state="readonly", width=28, font=SANS)
        q_cb.current(0)
        q_cb.pack(side="left")
        self._quality_map = {x[0]: x[1] for x in q_opts}
        self._quality_rmap = {x[1]: x[0] for x in q_opts}

        tk.Label(vrow, text="  Container:", bg=BG, fg=MUTED, font=SANS).pack(side="left")
        self.container_var = tk.StringVar(value="Auto")
        ttk.Combobox(vrow, textvariable=self.container_var,
                     values=["Auto", "mp4", "mkv", "webm"], state="readonly", width=8, font=SANS).pack(side="left", padx=4)

        # audio options frame
        self.audio_frame = tk.Frame(self, bg=BG)
        self._label("Audio format", parent=self.audio_frame)
        arow = tk.Frame(self.audio_frame, bg=BG)
        arow.pack(fill="x", padx=16, pady=4)
        self.audio_fmt_var = tk.StringVar(value="mp3")
        ttk.Combobox(arow, textvariable=self.audio_fmt_var,
                     values=["mp3","m4a","opus","flac","wav"], state="readonly", width=10, font=SANS).pack(side="left")
        tk.Label(arow, text="  Quality:", bg=BG, fg=MUTED, font=SANS).pack(side="left")
        self.audio_q_var = tk.StringVar(value="0")
        ttk.Combobox(arow, textvariable=self.audio_q_var,
                     values=["0 (best)","3","5","9 (smallest)"], state="readonly", width=12, font=SANS).pack(side="left", padx=4)

        # playlist options frame
        self.playlist_frame = tk.Frame(self, bg=BG)
        self._label("Playlist range (optional)", parent=self.playlist_frame)
        prow = tk.Frame(self.playlist_frame, bg=BG)
        prow.pack(fill="x", padx=16, pady=4)
        tk.Label(prow, text="From #", bg=BG, fg=MUTED, font=SANS).pack(side="left")
        self.pl_start = tk.Entry(prow, width=6, bg=SURFACE, fg=TEXT, insertbackground=TEXT,
                                  relief="flat", highlightthickness=1, highlightbackground=BORDER, font=SANS)
        self.pl_start.pack(side="left", padx=4)
        tk.Label(prow, text="  To #", bg=BG, fg=MUTED, font=SANS).pack(side="left")
        self.pl_end = tk.Entry(prow, width=6, bg=SURFACE, fg=TEXT, insertbackground=TEXT,
                                relief="flat", highlightthickness=1, highlightbackground=BORDER, font=SANS)
        self.pl_end.pack(side="left", padx=4)

        self._sep()

        # toggles
        self._label("Options")
        tog_frame = tk.Frame(self, bg=BG)
        tog_frame.pack(fill="x", padx=16, pady=2)

        self.subs_var  = tk.BooleanVar(value=False)
        self.thumb_var = tk.BooleanVar(value=False)
        self.meta_var  = tk.BooleanVar(value=True)

        for text, var in [
            ("📝  Embed subtitles (auto-generated)", self.subs_var),
            ("🖼  Embed thumbnail",                  self.thumb_var),
            ("🏷  Add metadata",                     self.meta_var),
        ]:
            cb = tk.Checkbutton(tog_frame, text=text, variable=var,
                                bg=BG, fg=TEXT, selectcolor=SURFACE2,
                                activebackground=BG, activeforeground=TEXT,
                                font=SANS, anchor="w", cursor="hand2")
            cb.pack(fill="x", pady=1)

        # output folder
        dir_row = tk.Frame(self, bg=BG)
        dir_row.pack(fill="x", padx=16, pady=6)
        self.dir_var = tk.StringVar()
        tk.Label(dir_row, text="📁  Save to:", bg=BG, fg=MUTED, font=SANS).pack(side="left")
        tk.Entry(dir_row, textvariable=self.dir_var, font=SANS,
                 bg=SURFACE, fg=TEXT, insertbackground=TEXT, relief="flat",
                 highlightthickness=1, highlightbackground=BORDER, highlightcolor=ACCENT,
                 width=38).pack(side="left", padx=6)
        tk.Button(dir_row, text="Browse…", font=SANS, bg=SURFACE2, fg=TEXT,
                  relief="flat", padx=8, cursor="hand2",
                  command=self._browse).pack(side="left")

        self._sep()

        # action buttons
        btn_row = tk.Frame(self, bg=BG)
        btn_row.pack(fill="x", padx=16, pady=6)

        tk.Button(btn_row, text="🔍  List formats", font=SANS_B,
                  bg=SURFACE2, fg=TEXT, activebackground=BORDER,
                  relief="flat", padx=16, pady=10, cursor="hand2",
                  command=self._list_formats).pack(side="left", padx=(0,8))

        tk.Button(btn_row, text="⬇  DOWNLOAD", font=("Segoe UI Bold",12) if sys.platform=="win32" else ("Sans Bold",12),
                  bg=ACCENT, fg="#fff", activebackground="#9b8df8",
                  relief="flat", padx=28, pady=10, cursor="hand2",
                  command=self._download).pack(side="left", expand=True, fill="x")

        tk.Button(btn_row, text="✕  Stop", font=SANS_B,
                  bg="#3a1a1a", fg=RED, activebackground="#4a2020",
                  relief="flat", padx=16, pady=10, cursor="hand2",
                  command=self._stop).pack(side="left", padx=(8,0))

        # log output
        self._label("Output")
        self.log = scrolledtext.ScrolledText(self, height=12, font=MONO,
                                             bg="#0a0a0e", fg="#a3e635",
                                             insertbackground=TEXT,
                                             relief="flat",
                                             highlightthickness=1,
                                             highlightbackground=BORDER)
        self.log.pack(fill="both", expand=True, padx=16, pady=(0,16))
        self.log.configure(state="disabled")

        self._proc = None
        self._update_type_buttons()

    # ── helpers ───────────────────────────────────────────────────────────
    def _sep(self):
        f = tk.Frame(self, bg=BORDER, height=1)
        f.pack(fill="x", padx=16, pady=8)

    def _label(self, text, parent=None):
        p = parent or self
        tk.Label(p, text=text.upper(), font=("Segoe UI",9) if sys.platform=="win32" else ("Sans",9),
                 bg=BG, fg=MUTED).pack(anchor="w", padx=16, pady=(4,0))

    def _browse(self):
        d = filedialog.askdirectory()
        if d:
            self.dir_var.set(d)

    def _set_type(self, val):
        self.type_var.set(val)
        self._update_type()

    def _update_type(self):
        t = self.type_var.get()
        self.video_frame.pack_forget()
        self.audio_frame.pack_forget()
        self.playlist_frame.pack_forget()
        if t == "video":
            self.video_frame.pack(fill="x", before=self._get_sep_after_type())
        elif t == "audio":
            self.audio_frame.pack(fill="x", before=self._get_sep_after_type())
        elif t == "playlist":
            self.playlist_frame.pack(fill="x", before=self._get_sep_after_type())
        self._update_type_buttons()

    def _update_type(self):
        t = self.type_var.get()
        for v in ["video","audio","playlist"]:
            btn = getattr(self, f"btn_{v}")
            if v == t:
                btn.configure(bg=ACCENT, fg="#fff")
            else:
                btn.configure(bg=SURFACE2, fg=MUTED)
        self.video_frame.pack_forget()
        self.audio_frame.pack_forget()
        self.playlist_frame.pack_forget()

        ref_widget = None
        for w in self.pack_slaves():
            if isinstance(w, tk.Frame) and w.cget("bg") == BORDER and w.cget("height") == 1:
                ref_widget = w
        
        if t == "video":    self.video_frame.pack(fill="x", after=ref_widget or self)
        elif t == "audio":  self.audio_frame.pack(fill="x", after=ref_widget or self)
        elif t == "playlist": self.playlist_frame.pack(fill="x", after=ref_widget or self)

    def _update_type_buttons(self):
        t = self.type_var.get()
        for v in ["video","audio","playlist"]:
            btn = getattr(self, f"btn_{v}")
            btn.configure(bg=ACCENT if v==t else SURFACE2, fg="#fff" if v==t else MUTED)

    def _get_sep_after_type(self):
        slaves = self.pack_slaves()
        for i, w in enumerate(slaves):
            if hasattr(w, '_is_type_row'):
                if i+1 < len(slaves):
                    return slaves[i+1]
        return None

    # ── build command ─────────────────────────────────────────────────────
    def _build_cmd(self, url=None):
        if YTDLP is None:
            return None, "yt-dlp not found"
        u = url or self.url_var.get().strip()
        if not u:
            return None, "Please enter a URL"

        t = self.type_var.get()
        cmd = [YTDLP]

        if t == "video":
            q_label = self.quality_var.get()
            q_val   = self._quality_map.get(q_label, "bestvideo+bestaudio/best")
            cmd += ["-f", q_val]
            c = self.container_var.get()
            if c and c != "Auto":
                cmd += ["--merge-output-format", c]
        elif t == "audio":
            fmt = self.audio_fmt_var.get()
            q   = self.audio_q_var.get().split()[0]
            cmd += ["-x", "--audio-format", fmt, "--audio-quality", q]
        elif t == "playlist":
            s = self.pl_start.get().strip()
            e = self.pl_end.get().strip()
            if s: cmd += ["--playlist-start", s]
            if e: cmd += ["--playlist-end",   e]
            cmd += ["-f", "bestvideo+bestaudio/best"]

        if self.subs_var.get():  cmd += ["--write-auto-sub", "--embed-subs", "--sub-lang", "en"]
        if self.thumb_var.get(): cmd += ["--embed-thumbnail"]
        if self.meta_var.get():  cmd += ["--add-metadata"]

        d = self.dir_var.get().strip()
        if d:
            cmd += ["-o", os.path.join(d, "%(title)s.%(ext)s")]

        cmd.append(u)
        return cmd, None

    # ── log helpers ───────────────────────────────────────────────────────
    def _log(self, text, color=None):
        self.log.configure(state="normal")
        if color:
            tag = f"col_{color.replace('#','')}"
            self.log.tag_configure(tag, foreground=color)
            self.log.insert("end", text + "\n", tag)
        else:
            self.log.insert("end", text + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def _clear_log(self):
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.configure(state="disabled")

    # ── actions ───────────────────────────────────────────────────────────
    def _list_formats(self):
        url = self.url_var.get().strip()
        if not url:
            self._log("⚠  Please enter a URL first.", RED)
            return
        if not YTDLP:
            self._log("✗  yt-dlp not found. See instructions below.", RED)
            return
        self._clear_log()
        self._log("Fetching available formats…", YELLOW)
        self._run_cmd([YTDLP, "-F", url])

    def _download(self):
        cmd, err = self._build_cmd()
        if err:
            self._log(f"⚠  {err}", RED)
            return
        self._clear_log()
        self._log("▶  " + " ".join(cmd), MUTED)
        self._log("─" * 60, BORDER)
        self._run_cmd(cmd)

    def _run_cmd(self, cmd):
        if self._proc and self._proc.poll() is None:
            self._log("Already running — click Stop first.", RED)
            return

        def worker():
            try:
                self._proc = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    cwd=os.path.dirname(os.path.abspath(__file__))
                )
                for line in self._proc.stdout:
                    line = line.rstrip()
                    if "[download]" in line and "%" in line:
                        self.after(0, self._log, line, GREEN)
                    elif "ERROR" in line or "error" in line:
                        self.after(0, self._log, line, RED)
                    elif "WARNING" in line:
                        self.after(0, self._log, line, YELLOW)
                    else:
                        self.after(0, self._log, line)
                self._proc.wait()
                rc = self._proc.returncode
                if rc == 0:
                    self.after(0, self._log, "\n✅  Done!", GREEN)
                else:
                    self.after(0, self._log, f"\n✗  Exited with code {rc}", RED)
            except Exception as ex:
                self.after(0, self._log, f"✗  {ex}", RED)

        threading.Thread(target=worker, daemon=True).start()

    def _stop(self):
        if self._proc and self._proc.poll() is None:
            self._proc.terminate()
            self._log("⏹  Stopped.", YELLOW)
        else:
            self._log("Nothing running.", MUTED)


# ── install helper message ───────────────────────────────────────────────────
if __name__ == "__main__":
    if YTDLP is None:
        print("=" * 60)
        print("yt-dlp not found!")
        print("Fix it with ONE of these:")
        print("  pip install yt-dlp")
        print("  — or —")
        print("  place yt-dlp binary in the same folder as this script")
        print("=" * 60)
    app = App()
    app.mainloop()
