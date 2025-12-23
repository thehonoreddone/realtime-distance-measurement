"""
ArUco Marker Oluşturucu
========================
Bu script, farklı boyutlarda ArUco markerları oluşturur ve yazdırılabilir PDF formatında kaydeder.
Oluşturulan markerları kesip nesnelerin üzerine yapıştırarak mesafe ölçümü yapabilirsiniz.

Kullanım:
    python aruco_marker_olusturucu.py
    
Markerlar 'markers' klasörüne kaydedilir.
"""

import cv2
import numpy as np
import os

def aruco_marker_olustur(marker_id, marker_boyutu_cm, cozunurluk_piksel=200):
    """
    Belirtilen ID ve boyutta ArUco marker oluşturur.
    
    Parametreler:
    -------------
    marker_id : int
        Marker'ın benzersiz ID numarası (0-249 arası)
    marker_boyutu_cm : float
        Marker'ın gerçek dünya boyutu (cm cinsinden)
    cozunurluk_piksel : int
        Marker görüntüsünün piksel cinsinden boyutu
        
    Döndürür:
    ---------
    numpy.ndarray
        Oluşturulan marker görüntüsü
    """
    # ArUco sözlüğünü seç (DICT_4X4_250: 4x4 grid, 250 benzersiz marker)
    aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_250)
    
    # Marker'ı oluştur
    marker_img = cv2.aruco.generateImageMarker(aruco_dict, marker_id, cozunurluk_piksel)
    
    # Beyaz kenarlık ekle (yazdırma ve algılama için önemli)
    kenarlik = 50
    marker_with_border = cv2.copyMakeBorder(
        marker_img,
        kenarlik, kenarlik, kenarlik, kenarlik,
        cv2.BORDER_CONSTANT,
        value=255
    )
    
    return marker_with_border


def tum_markerlari_olustur(boyutlar_cm=[3, 4, 5], marker_sayisi=4):
    """
    Belirtilen boyutlarda birden fazla marker oluşturur ve kaydeder.
    
    Parametreler:
    -------------
    boyutlar_cm : list
        Oluşturulacak marker boyutlarının listesi (cm)
    marker_sayisi : int
        Her boyut için oluşturulacak marker sayısı
    """
    # Markers klasörünü oluştur
    markers_klasoru = os.path.join(os.path.dirname(__file__), "markers")
    if not os.path.exists(markers_klasoru):
        os.makedirs(markers_klasoru)
    
    marker_id = 0
    
    for boyut in boyutlar_cm:
        print(f"\n{boyut} cm boyutunda markerlar oluşturuluyor...")
        
        for i in range(marker_sayisi):
            marker = aruco_marker_olustur(marker_id, boyut)
            
            # Dosya adı: marker_ID_BOYUTcm.png
            dosya_adi = f"marker_{marker_id}_{boyut}cm.png"
            dosya_yolu = os.path.join(markers_klasoru, dosya_adi)
            
            cv2.imwrite(dosya_yolu, marker)
            print(f"  Kaydedildi: {dosya_adi}")
            
            marker_id += 1
    
    # Tüm markerları tek bir sayfada gösteren birleşik görüntü oluştur
    birlesik_sayfa_olustur(markers_klasoru, boyutlar_cm, marker_sayisi)
    
    print(f"\n✓ Tüm markerlar '{markers_klasoru}' klasörüne kaydedildi!")
    print("\n--- ÖNEMLİ NOTLAR ---")
    print("1. Markerları yazdırırken gerçek boyutlarına dikkat edin")
    print("2. Yazdırma ayarlarında 'Gerçek Boyut' veya '%100' seçin")
    print("3. Yazdırdıktan sonra cetvel ile boyutları kontrol edin")
    print("4. Her marker dosya adında boyutu belirtilmiştir (örn: marker_0_3cm.png)")


def birlesik_sayfa_olustur(markers_klasoru, boyutlar_cm, marker_sayisi):
    """
    Tüm markerları tek bir A4 sayfasında birleştirir.
    Yazdırma için uygun format.
    """
    # A4 boyutu (300 DPI için yaklaşık piksel değerleri)
    a4_genislik = 2480
    a4_yukseklik = 3508
    
    # Beyaz A4 sayfa oluştur
    sayfa = np.ones((a4_yukseklik, a4_genislik), dtype=np.uint8) * 255
    
    # Her boyut için ayrı bir satır
    y_offset = 100
    
    for boyut_idx, boyut in enumerate(boyutlar_cm):
        # Boyut başlığı için alan bırak
        y_start = y_offset + boyut_idx * (a4_yukseklik // len(boyutlar_cm))
        
        x_offset = 100
        for i in range(marker_sayisi):
            marker_id = boyut_idx * marker_sayisi + i
            dosya_adi = f"marker_{marker_id}_{boyut}cm.png"
            dosya_yolu = os.path.join(markers_klasoru, dosya_adi)
            
            if os.path.exists(dosya_yolu):
                marker = cv2.imread(dosya_yolu, cv2.IMREAD_GRAYSCALE)
                
                # DPI hesabı: boyut cm -> piksel (300 DPI için)
                # 1 inch = 2.54 cm, 300 piksel/inch
                hedef_piksel = int(boyut * 300 / 2.54) + 100  # +100 kenarlık için
                
                # Marker'ı hedef boyuta yeniden boyutlandır
                marker_resized = cv2.resize(marker, (hedef_piksel, hedef_piksel))
                
                # Sayfaya yerleştir
                if x_offset + hedef_piksel < a4_genislik - 100:
                    if y_start + hedef_piksel < a4_yukseklik - 100:
                        sayfa[y_start:y_start+hedef_piksel, x_offset:x_offset+hedef_piksel] = marker_resized
                        x_offset += hedef_piksel + 50
    
    # Birleşik sayfayı kaydet
    birlesik_dosya = os.path.join(markers_klasoru, "tum_markerlar_A4.png")
    cv2.imwrite(birlesik_dosya, sayfa)
    print(f"\n✓ Birleşik A4 sayfa oluşturuldu: tum_markerlar_A4.png")


def ozel_marker_olustur():
    """
    Kullanıcının istediği boyut ve ID'de özel marker oluşturur.
    """
    print("\n=== ÖZEL ARUCO MARKER OLUŞTURUCU ===\n")
    
    try:
        marker_id = int(input("Marker ID (0-249): "))
        if marker_id < 0 or marker_id > 249:
            print("Hata: Marker ID 0-249 arasında olmalı!")
            return
            
        boyut = float(input("Marker boyutu (cm): "))
        if boyut <= 0:
            print("Hata: Boyut pozitif olmalı!")
            return
        
        marker = aruco_marker_olustur(marker_id, boyut, cozunurluk_piksel=400)
        
        markers_klasoru = os.path.join(os.path.dirname(__file__), "markers")
        if not os.path.exists(markers_klasoru):
            os.makedirs(markers_klasoru)
        
        dosya_adi = f"marker_{marker_id}_{boyut}cm.png"
        dosya_yolu = os.path.join(markers_klasoru, dosya_adi)
        
        cv2.imwrite(dosya_yolu, marker)
        print(f"\n✓ Marker kaydedildi: {dosya_yolu}")
        
    except ValueError:
        print("Hata: Geçersiz giriş!")


if __name__ == "__main__":
    print("=" * 50)
    print("      ARUCO MARKER OLUŞTURUCU")
    print("=" * 50)
    print("\nSeçenekler:")
    print("1. Standart marker seti oluştur (3cm, 4cm, 5cm)")
    print("2. Özel boyutta marker oluştur")
    
    secim = input("\nSeçiminiz (1/2): ").strip()
    
    if secim == "1":
        tum_markerlari_olustur(boyutlar_cm=[3, 4, 5], marker_sayisi=4)
    elif secim == "2":
        ozel_marker_olustur()
    else:
        print("Geçersiz seçim! Standart set oluşturuluyor...")
        tum_markerlari_olustur(boyutlar_cm=[3, 4, 5], marker_sayisi=4)
