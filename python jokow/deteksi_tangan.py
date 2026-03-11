import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import pygame
import numpy as np
import os

# 1. Inisialisasi Audio (Pygame)
try:
    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
    print(f"DEBUG: Audio initialized: {pygame.mixer.get_init()}", flush=True)
except Exception as e:
    print(f"ERROR: Gagal inisialisasi audio: {e}", flush=True)

def load_sound(file_name):
    if os.path.exists(file_name):
        try:
            return pygame.mixer.Sound(file_name)
        except Exception as e:
            print(f"Gagal memuat {file_name}: {e}", flush=True)
    else:
        print(f"File tidak ditemukan: {file_name}", flush=True)
    return None

# Load lagu-lagu baru
suara_berjuang = load_sound('berjuang.mp3')
suara_selamat = load_sound('selamat.mp3')
suara_sukses = load_sound('sukses.mp3')
suara_hidup = load_sound('hidup.mp3')

print("DEBUG: Mengetes suara (anda harusnya mendengar bunyi singkat)...")
if suara_selamat:
    suara_selamat.play()
    pygame.time.delay(500) # kek i waktu diluk
    pygame.mixer.stop()

# Buka Kamera Dulu (Mencoba 0, 1, atau 2)
def find_camera():
    for index in [0, 1, 2]:
        print(f"DEBUG: Mencoba membuka kamera index {index}...", flush=True)
        temp_cap = cv2.VideoCapture(index)
        if temp_cap.isOpened():
            # Bmanasin mesen 
            for i in range(10):
                pygame.time.delay(200)
                success, _ = temp_cap.read()
                if success:
                    print(f"DEBUG: Kamera index {index} berhasil ditemukan dan siap.", flush=True)
                    return temp_cap
                print(f"DEBUG: Index {index} percobaan {i} gagal...", flush=True)
            temp_cap.release()
            pygame.time.delay(500) # Jeda sebelum index lainmassss
    return None

cap = find_camera()
if cap is None:
    print("ERROR: Tidak dapat menemukan kamera yang berfungsi. Pastikan kamera terhubung dan tidak sedang digunakan aplikasi lain.", flush=True)
    exit()

print("DEBUG: Inisialisasi MediaPipe...", flush=True)
base_options = python.BaseOptions(model_asset_path='hand_landmarker.task')
options = vision.HandLandmarkerOptions(base_options=base_options,
                                        num_hands=2,
                                        min_hand_detection_confidence=0.5,
                                        min_hand_presence_confidence=0.5,
                                        min_tracking_confidence=0.5)
detector = vision.HandLandmarker.create_from_options(options)
print("DEBUG: MediaPipe siap.", flush=True)

# Variabel untuk mencegah lagu diputar berulang-ulang
gestur_saat_ini = None 

def get_finger_status(hand_landmarks):
    jari = []
    
    # 1. Jempol (Landmark 4) 
    # Logika jempol lebih stabil menggunakan perbandingan X (untuk kiri/kanan) atau Y (untuk atas/bawah)
    # Di sini kita gunakan Y untuk "Jempol Up" dan X untuk deteksi genggam yang lebih baik
    if hand_landmarks[4].y < hand_landmarks[3].y:
        jari.append(1)
    else:
        jari.append(0)
        
    # 2. Jari lain (Telunjuk, Tengah, Manis, Kelingking)
    tips = [8, 12, 16, 20]
    pips = [6, 10, 14, 18]
    
    for tip, pip in zip(tips, pips):
        if hand_landmarks[tip].y < hand_landmarks[pip].y:
            jari.append(1) # Terbuka
        else:
            jari.append(0) # Tertutup
            
    return jari # Return format: [Jempol, Telunjuk, Tengah, Manis, Kelingking]

while cap.isOpened():
    success, img = cap.read()
    
    if not success:
        print("ERROR: Gagal membaca frame. Menutup.")
        break

    img = cv2.flip(img, 1) # Flip di awal agar koordinat sesuai tampilan cermin
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=img_rgb)
    
    detection_result = detector.detect(mp_image)

    if detection_result.hand_landmarks:
        for hand_landmarks in detection_result.hand_landmarks:
            # Gambar landmark
            h, w, _ = img.shape
            for landmark in hand_landmarks:
                cx, cy = int(landmark.x * w), int(landmark.y * h)
                cv2.circle(img, (cx, cy), 5, (0, 255, 0), cv2.FILLED)

            jari = get_finger_status(hand_landmarks)
            print(f"DEBUG Jari: {jari}", flush=True)

            gestur_terdeteksi = None
            
            # LOGIKA GESTUR
            if jari == [0, 0, 0, 0, 0]:
                gestur_terdeteksi = "Menggenggam"
            elif jari[1:] == [1, 0, 0, 1]: # Metal (Telunjuk & Kelingking UP)
                gestur_terdeteksi = "Metal"
            elif jari == [1, 0, 0, 0, 0]:
                gestur_terdeteksi = "Jempol"
            elif jari == [0, 1, 1, 0, 0] or (jari[1] == 1 and jari[2] == 1 and jari[3] == 0 and jari[4] == 0):
                gestur_terdeteksi = "2 Jari"

            # EKSEKUSI SUARA
            if gestur_terdeteksi != gestur_saat_ini:
                if gestur_terdeteksi:
                    print(f"DEBUG: Gestur Terdeteksi: {gestur_terdeteksi}", flush=True)
                    pygame.mixer.stop() 
                    
                    if gestur_terdeteksi == "Menggenggam" and suara_berjuang:
                        suara_berjuang.play()
                        print(">>> Lagu: Berjuang", flush=True)
                    elif gestur_terdeteksi == "Metal" and suara_selamat:
                        suara_selamat.play()
                        print(">>> Lagu: Selamat", flush=True)
                    elif gestur_terdeteksi == "Jempol" and suara_sukses:
                        suara_sukses.play()
                        print(">>> Lagu: Sukses", flush=True)
                    elif gestur_terdeteksi == "2 Jari" and suara_hidup:
                        suara_hidup.play()
                        print(">>> Lagu: Hidup", flush=True)
                else:
                    if gestur_saat_ini is not None:
                        print(f"DEBUG: Jemari {jari} tidak cocok dengan gestur apapun.", flush=True)
                
                gestur_saat_ini = gestur_terdeteksi
    else:
        # Jika tidak ada tangan, reset gestur agar bisa memicu suara lagi saat tangan muncul
        if gestur_saat_ini is not None:
            print("DEBUG: Tangan tidak terdeteksi (Reset).", flush=True)
            gestur_saat_ini = None

    cv2.imshow("Multi-Gesture Music Player", img)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
