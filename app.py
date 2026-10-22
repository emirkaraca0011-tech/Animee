import os
import shutil
import zipfile
import streamlit as st
from scenedetect import detect, ContentDetector, split_video_ffmpeg
import yt_dlp

st.title("🎬 Anime Twixtor 1:1 Klipler Ayırıcı")
st.write("YouTube linkini yapıştırın; video 1:1 kare yapılsın, sesi silinsin ve sahnelerine ayrılsın.")

url = st.text_input("YouTube Video Linki:")

if st.button("Videoyu İşle ve Böl"):
    if not url:
        st.warning("Lütfen geçerli bir YouTube linki girin.")
    else:
        with st.spinner("Video indiriliyor, sahnelerine ayrılıyor... Lütfen bekleyin."):
            work_dir = "temp_space"
            if os.path.exists(work_dir):
                shutil.rmtree(work_dir)
            os.makedirs(work_dir, exist_ok=True)
            
            input_file = os.path.join(work_dir, "input.mp4")

            try:
                ydl_opts = {
                    'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                    'outtmpl': input_file,
                    'quiet': True,
                    'no_warnings': True,
                    'extractor_args': {'youtube': {'player_client': ['android', 'web']}},
                }
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])

                # Sahne kesme, sessize alma (-an) ve 1:1 kare yapma
                scene_list = detect(input_file, ContentDetector(threshold=27.0))
                output_template = os.path.join(work_dir, "scene_$THREE_DIGIT_REG.mp4")
                
                split_video_ffmpeg(
                    input_file,
                    scene_list,
                    output_file_template=output_template,
                    ffmpeg_args='-vf "crop=ih:ih:(iw-ih)/2:0" -an -c:v libx264 -crf 18 -preset fast'
                )

                # Klipleri ZIP dosyası haline getirme
                zip_path = "anime_clips.zip"
                with zipfile.ZipFile(zip_path, 'w') as zipf:
                    for root, dirs, files in os.walk(work_dir):
                        for file in files:
                            if file.startswith("scene_"):
                                zipf.write(os.path.join(root, file), arcname=file)

                st.success(f"İşlem tamam! Toplam {len(scene_list)} sahne bölündü.")
                
                with open(zip_path, "rb") as fp:
                    st.download_button(
                        label="📥 Bölünmüş Klipleri İndir (ZIP)",
                        data=fp,
                        file_name="anime_clips.zip",
                        mime="application/zip"
                    )

            except Exception as e:
                st.error(f"Bir hata oluştu: {str(e)}")
            
            finally:
                if os.path.exists(work_dir):
                    shutil.rmtree(work_dir)
