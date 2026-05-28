#!/usr/bin/env python3
"""
yt-dlp Web GUI — Hosted on Render / Local Web
Requires: pip install streamlit yt-dlp
"""

import streamlit as st
import subprocess
import os
import shutil
import sys

# ── Setup Page Config ────────────────────────────────────────────────────────
st.set_page_config(
    page_title="yt-dlp Web GUI",
    page_icon="⬇",
    layout="centered"
)

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
    return "yt-dlp"  # On Linux/Render, if installed via pip, it runs as 'yt-dlp'

YTDLP = find_ytdlp()

# ── UI Layout ───────────────────────────────────────────────────────────────
st.title("⬇ yt-dlp Web GUI")

# Check binary status
if YTDLP and (shutil.which(YTDLP) or os.path.exists(YTDLP)):
    st.success(f"✓ yt-dlp พร้อมใช้งาน")
else:
    st.error("✗ ไม่พบ yt-dlp — โปรดตรวจสอบระบบการติดตั้ง")

st.markdown("---")

# URL Input
url_input = st.text_input("Video / Playlist URL", placeholder="วางลิงก์วิดีโอหรือเพลย์ลิสต์ที่นี่...")

st.markdown("---")

# Download Type Selection
st.markdown("### Download Type")
download_type = st.radio(
    "เลือกประเภทการดาวน์โหลด",
    ["🎬 Video", "🎵 Audio only", "📋 Playlist"],
    horizontal=True,
    label_visibility="collapsed"
)

# Option Frames based on Selection
quality_val = "bestvideo+bestaudio/best"
merge_format = "Auto"
audio_fmt = "mp3"
audio_q = "0"
pl_start = ""
pl_end = ""

if "Video" in download_type:
    st.markdown("#### Quality")
    col1, col2 = st.columns([2, 1])
    with col1:
        q_opts = {
            "Best available": "bestvideo+bestaudio/best",
            "Max 1080p": "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
            "Max 720p": "bestvideo[height<=720]+bestaudio/best[height<=720]",
            "Max 480p": "bestvideo[height<=480]+bestaudio/best[height<=480]",
            "Smallest file": "worstvideo+worstaudio/worst"
        }
        quality_label = st.selectbox("เลือกความละเอียด", list(q_opts.keys()))
        quality_val = q_opts[quality_label]
    with col2:
        merge_format = st.selectbox("Container", ["Auto", "mp4", "mkv", "webm"])

elif "Audio" in download_type:
    st.markdown("#### Audio format")
    col1, col2 = st.columns(2)
    with col1:
        audio_fmt = st.selectbox("Format", ["mp3", "m4a", "opus", "flac", "wav"])
    with col2:
        audio_q_label = st.selectbox("Quality", ["0 (best)", "3", "5", "9 (smallest)"])
        audio_q = audio_q_label.split()[0]

elif "Playlist" in download_type:
    st.markdown("#### Playlist range (optional)")
    col1, col2 = st.columns(2)
    with col1:
        pl_start = st.text_input("From #", placeholder="1")
    with col2:
        pl_end = st.text_input("To #", placeholder="10")

st.markdown("---")

# Toggles / Options
st.markdown("### Options")
subs_var = st.checkbox("📝 Embed subtitles (auto-generated)", value=False)
thumb_var = st.checkbox("🖼 Embed thumbnail", value=False)
meta_var = st.checkbox("🏷 Add metadata", value=True)

st.markdown("---")

# ── build command ─────────────────────────────────────────────────────
# ── ค้นหาฟังก์ชันนี้ใน app.py เดิมของคุณ แล้ววางทับเฉพาะฟังก์ชันนี้ ────────────────
    def build_cmd(self, url=None): # หรือ build_cmd(url, d_type) ตามเวอร์ชันที่คุณใช้อยู่
        u = url or self.url_var.get().strip()
        if not u:
            return None, "Please enter a URL"

        t = self.type_var.get() if hasattr(self, 'type_var') else download_type
        cmd = [YTDLP]

        # 🌟 [BYPASS] เพิ่ม Parameter เพื่อหลบเลี่ยงระบบตรวจจับบอทของ YouTube
        cmd += [
            "--impersonate", "chrome",                           # ปลอมตัวเป็น Browser Chrome ของมนุษย์
            "--extractor-args", "youtube:player-client=ios,android", # บังคับใช้ระบบของ iOS/Android ในการดึงข้อมูลเพื่อเลี่ยง Error 429
            "--no-check-certificates",                           # ข้ามการตรวจสอบใบรับรองในกรณีเน็ตเวิร์กของเซิร์ฟเวอร์มีปัญหา
        ]

        if "Video" in t or t == "video":
            q_val = self.quality_var.get() if hasattr(self, 'quality_var') else quality_val
            cmd += ["-f", q_val]
            c = self.container_var.get() if hasattr(self, 'container_var') else merge_format
            if c and c != "Auto":
                cmd += ["--merge-output-format", c]
        elif "Audio" in t or t == "audio":
            fmt = self.audio_fmt_var.get() if hasattr(self, 'audio_fmt_var') else audio_fmt
            q = self.audio_q_var.get().split()[0] if hasattr(self, 'audio_q_var') else audio_q
            cmd += ["-x", "--audio-format", fmt, "--audio-quality", q]
        elif "Playlist" in t or t == "playlist":
            s = self.pl_start.get().strip() if hasattr(self, 'pl_start') else pl_start.strip()
            e = self.pl_end.get().strip() if hasattr(self, 'pl_end') else pl_end.strip()
            if s: cmd += ["--playlist-start", s]
            if e: cmd += ["--playlist-end",   e]
            cmd += ["-f", "bestvideo+bestaudio/best"]

        # ดึงค่า Toggles จากหน้าแอปมาประกอบคำสั่งตามเดิม
        v_subs = self.subs_var.get() if hasattr(self, 'subs_var') else subs_var
        v_thumb = self.thumb_var.get() if hasattr(self, 'thumb_var') else thumb_var
        v_meta = self.meta_var.get() if hasattr(self, 'meta_var') else meta_var

        if v_subs:  cmd += ["--write-auto-sub", "--embed-subs", "--sub-lang", "en"]
        if v_thumb: cmd += ["--embed-thumbnail"]
        if v_meta:  cmd += ["--add-metadata"]

        # ตั้งโฟลเดอร์สำหรับดาวน์โหลดชั่วคราวบน Render
        output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "downloads")
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        cmd += ["-o", os.path.join(output_dir, "%(title)s.%(ext)s")]
        cmd.append(u)
        
        return cmd, output_dir
# Action Buttons
st.markdown("### Actions")
col_list, col_dl = st.columns([1, 2])

# Log Output Area
log_area = st.empty()

if col_list.button("🔍 List formats", use_container_width=True):
    if not url_input.strip():
        st.warning("⚠ Please enter a URL first.")
    else:
        st.info("Fetching available formats...")
        cmd = [YTDLP, "-F", url_input.strip()]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        st.code(proc.stdout)

if col_dl.button("⬇ DOWNLOAD", type="primary", use_container_width=True):
    if not url_input.strip():
        st.warning("⚠ Please enter a URL first.")
    else:
        cmd, out_dir = build_cmd(url_input.strip(), download_type)
        
        # ล้างไฟล์เก่าในโฟลเดอร์ downloads ก่อนเพื่อไม่ให้ตีกัน
        if os.path.exists(out_dir):
            shutil.rmtree(out_dir)
        os.makedirs(out_dir)

        st.info("▶ เริ่มกระบวนการดาวน์โหลดบนเซิร์ฟเวอร์...")
        
        # รันคำสั่งบรรทัดคำสั่งและแสดง Log สดๆ บนหน้าเว็บ
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        log_content = ""
        while True:
            line = proc.stdout.readline()
            if not line:
                break
            log_content += line
            log_area.code(log_content) # อัปเดต log บนหน้าเว็บสดๆ
            
        proc.wait()
        
        if proc.returncode == 0:
            st.success("✅ เซิร์ฟเวอร์ดาวน์โหลดเสร็จเรียบร้อยเสร็จแล้ว!")
            
            # ค้นหาไฟล์ที่โหลดเสร็จในโฟลเดอร์ downloads เพื่อส่งให้ผู้ใช้กดดาวน์โหลดลงคอมตัวเอง
            downloaded_files = os.listdir(out_dir)
            if downloaded_files:
                for file_name in downloaded_files:
                    file_path = os.path.join(out_dir, file_name)
                    with open(file_path, "rb") as f:
                        st.download_button(
                            label=f"💾 คลิกเพื่อบันทึกไฟล์: {file_name}",
                            data=f,
                            file_name=file_name,
                            use_container_width=True
                        )
            else:
                st.error("ไม่พบไฟล์ที่ดาวน์โหลดสำเร็จในระบบ")
        else:
            st.error(f"✗ เกิดข้อผิดพลาดในการดาวน์โหลด (Exit code: {proc.returncode})")
