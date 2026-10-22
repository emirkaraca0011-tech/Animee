import os
import shutil
import zipfile
import requests
import streamlit as st
from scenedetect import detect, ContentDetector, split_video_ffmpeg

st.title("🎬 Anime Twixtor 1:1 Klipler Ayırıcı")
st.write("YouTube linkini yapıştırın; Cobalt (Wuk) üzerinden indirilsin ve sahnelerine ayrılsın.")

url = st.text_input("YouTube Video Linki:")

if st.button("Videoyu İşle ve Böl"):
    if not url:
        st.warning("Lütfen geçerli bir YouTube linki girin.")
    else:
        with st.spinner("Video Cobalt üzerinden indiriliyor, sahnelerine ayrılıyor... Bekleyin."):
            work_dir = "temp_space"
            if os.path.exists(work_dir):
                shutil.rmtree(work_dir)
            os.makedirs(work_dir, exist_ok=True)
            
            input_file = os.path.join(work_dir, "input.mp4")

            try:
                # Alternatif Cobalt sunucusu (co.wuk.sh)
                cobalt_api_url = "https://co.wuk.sh/api/json"
                payload = {
                    "url": url,
                    "videoQuality": "max"
                }
                headers = {
                    "Accept": "application/json",
                    "Content-Type": "application/json"
                }

                response = requests.post(cobalt_api_url, json=payload, headers=headers)
                
                # Gelen yanıtın boş olup olmadığını ve JSON olup olmadığını kontrol edelim
                if not response.text:
                    st.error("Cobalt sunucusundan boş yanıt döndü.")
                    st.stop()
                    
                res_data = response.json()

                if res_data.get("status") in ["stream", "redirect", "success"]:
                    download_url = res_data.get("url")
                else:
                    st.error(f"Cobalt videoyu indiremedi: {res_data}")
                    st.stop()

                # İndirilen videoyu geçici klasöre kaydediyoruz
                video_res = requests.get(download_url, stream=True)
                with open(input_file, "wb") as f:
                    for chunk in video_res.iter_content(chunk_size=8192):
                        f.write(chunk)

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
