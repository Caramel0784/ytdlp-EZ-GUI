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
def build_cmd(url, d_type):
    if not url:
        return None, "Please enter a URL"

    cmd = [YTDLP]
    
    # กำหนดให้โหลดมาเก็บไว้ในโฟลเดอร์ downloads ของเซิร์ฟเวอร์ชั่วคราว เพื่อเตรียมให้กดโหลดผ่านเว็บ
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "downloads")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    out_template = os.path.join(output_dir, "%(title)s.%(ext)s")

    if "Video" in d_type:
        cmd += ["-f", quality_val]
        if merge_format and merge_format != "Auto":
            cmd += ["--merge-output-format", merge_format]
    elif "Audio" in d_type:
        cmd += ["-x", "--audio-format", audio_fmt, "--audio-quality", audio_q]
    elif "Playlist" in d_type:
        if pl_start.strip(): cmd += ["--playlist-start", pl_start.strip()]
        if pl_end.strip(): cmd += ["--playlist-end", pl_end.strip()]
        cmd += ["-f", "bestvideo+bestaudio/best"]

    if subs_var:  cmd += ["--write-auto-sub", "--embed-subs", "--sub-lang", "en"]
    if thumb_var: cmd += ["--embed-thumbnail"]
    if meta_var:  cmd += ["--add-metadata"]

    cmd += ["-o", out_template]
    cmd.append(url)
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
