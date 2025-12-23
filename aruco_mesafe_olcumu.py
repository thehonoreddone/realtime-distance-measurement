"""
ArUco Marker ile Mesafe Ölçümü
===============================
Bu uygulama ArUco markerları kullanarak iki nesne arasındaki mesafeyi ölçer.
Markerların gerçek boyutunu bilerek piksel-cm dönüşümü yapar.

Özellikler:
- Laptop kamerası veya IP webcam desteği
- Gerçek zamanlı mesafe ölçümü
- Excel'e otomatik kayıt
- Kamera hareketine dayanıklı (marker boyutu üzerinden sürekli kalibrasyon)

Kullanım:
    python aruco_mesafe_olcumu.py
    
Tuşlar:
    's' - Mevcut ölçümü Excel'e kaydet
    'r' - Kayıtları sıfırla
    'q' - Çıkış
"""

import cv2
import numpy as np
import pandas as pd
from datetime import datetime
import os
import math


class ArucoMesafeOlcucu:
    """
    ArUco marker tabanlı mesafe ölçüm sınıfı.
    
    Bu sınıf:
    1. Kamera görüntüsünden ArUco markerları tespit eder
    2. Marker boyutunu kullanarak piksel/cm oranını hesaplar
    3. İki marker arasındaki mesafeyi ölçer
    4. Sonuçları Excel'e kaydeder
    """
    
    def __init__(self, marker_boyutu_cm=5.0):
        """
        ArucoMesafeOlcucu sınıfını başlatır.
        
        Parametreler:
        -------------
        marker_boyutu_cm : float
            Kullanılan ArUco marker'ın kenar uzunluğu (cm)
            Bu değer piksel-cm dönüşümü için kritik öneme sahiptir.
        """
        self.marker_boyutu_cm = marker_boyutu_cm
        
        # ArUco sözlüğünü ve dedektörü oluştur
        # DICT_4X4_250: 4x4 grid yapısında, 250 benzersiz marker içerir
        self.aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_250)
        
        # Dedektör parametrelerini ayarla
        self.detector_params = cv2.aruco.DetectorParameters()
        # Daha iyi köşe tespiti için uyarlanabilir eşikleme
        self.detector_params.adaptiveThreshWinSizeMin = 3
        self.detector_params.adaptiveThreshWinSizeMax = 23
        self.detector_params.adaptiveThreshWinSizeStep = 10
        
        # ArUco dedektörünü oluştur
        self.detector = cv2.aruco.ArucoDetector(self.aruco_dict, self.detector_params)
        
        # Ölçüm kayıtları için liste
        self.olcum_kayitlari = []
        
        # Excel dosya yolu
        self.excel_dosyasi = os.path.join(
            os.path.dirname(__file__), 
            "aruco_mesafe_olcumleri.xlsx"
        )
        
        # Piksel/cm oranı (her frame'de güncellenir)
        self.piksel_cm_orani = None
        
    def marker_merkezi_bul(self, koseleler):
        """
        Marker'ın köşe noktalarından merkez noktasını hesaplar.
        
        Parametreler:
        -------------
        koseleler : numpy.ndarray
            Marker'ın 4 köşe noktasının koordinatları [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
            
        Döndürür:
        ---------
        tuple
            (merkez_x, merkez_y) koordinatları
        """
        # 4 köşenin ortalaması merkezi verir
        merkez_x = int(np.mean(koseleler[:, 0]))
        merkez_y = int(np.mean(koseleler[:, 1]))
        return (merkez_x, merkez_y)
    
    def marker_boyutu_piksel_hesapla(self, koseleler):
        """
        Marker'ın piksel cinsinden boyutunu hesaplar.
        Perspektif bozulmasını hesaba katmak için 4 kenarın ortalamasını alır.
        
        Parametreler:
        -------------
        koseleler : numpy.ndarray
            Marker'ın 4 köşe noktasının koordinatları
            
        Döndürür:
        ---------
        float
            Marker'ın piksel cinsinden ortalama kenar uzunluğu
        """
        # 4 kenarın uzunluklarını hesapla
        kenar1 = np.linalg.norm(koseleler[0] - koseleler[1])
        kenar2 = np.linalg.norm(koseleler[1] - koseleler[2])
        kenar3 = np.linalg.norm(koseleler[2] - koseleler[3])
        kenar4 = np.linalg.norm(koseleler[3] - koseleler[0])
        
        # Ortalama kenar uzunluğu
        return (kenar1 + kenar2 + kenar3 + kenar4) / 4
    
    def piksel_cm_orani_guncelle(self, koseleler):
        """
        Tespit edilen marker boyutuna göre piksel/cm oranını günceller.
        Bu sayede kamera hareketi veya zoom değişikliklerine uyum sağlanır.
        
        Parametreler:
        -------------
        koseleler : numpy.ndarray
            Marker'ın köşe koordinatları
        """
        marker_piksel = self.marker_boyutu_piksel_hesapla(koseleler)
        self.piksel_cm_orani = marker_piksel / self.marker_boyutu_cm
    
    def iki_nokta_arasi_mesafe(self, nokta1, nokta2):
        """
        İki nokta arasındaki Öklid mesafesini hesaplar.
        
        Parametreler:
        -------------
        nokta1, nokta2 : tuple
            (x, y) koordinatları
            
        Döndürür:
        ---------
        float
            Piksel cinsinden mesafe
        """
        return math.sqrt((nokta2[0] - nokta1[0])**2 + (nokta2[1] - nokta1[1])**2)
    
    def mesafe_cm_hesapla(self, merkez1, merkez2):
        """
        İki marker merkezi arasındaki mesafeyi cm cinsinden hesaplar.
        
        Parametreler:
        -------------
        merkez1, merkez2 : tuple
            Marker merkezlerinin (x, y) koordinatları
            
        Döndürür:
        ---------
        float veya None
            cm cinsinden mesafe, piksel/cm oranı yoksa None
        """
        if self.piksel_cm_orani is None:
            return None
            
        piksel_mesafe = self.iki_nokta_arasi_mesafe(merkez1, merkez2)
        cm_mesafe = piksel_mesafe / self.piksel_cm_orani
        return cm_mesafe
    
    def frame_isle(self, frame):
        """
        Bir video frame'ini işleyerek marker tespiti ve mesafe ölçümü yapar.
        
        Parametreler:
        -------------
        frame : numpy.ndarray
            BGR formatında video frame'i
            
        Döndürür:
        ---------
        tuple
            (işlenmiş_frame, mesafe_cm, tespit_bilgisi)
        """
        # Gri tonlamaya çevir (ArUco tespiti için gerekli)
        gri = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Markerları tespit et
        koseler, idler, reddedilenler = self.detector.detectMarkers(gri)
        
        tespit_bilgisi = {
            "marker_sayisi": 0,
            "marker_idleri": [],
            "merkezler": []
        }
        
        mesafe_cm = None
        
        if idler is not None and len(idler) > 0:
            tespit_bilgisi["marker_sayisi"] = len(idler)
            tespit_bilgisi["marker_idleri"] = idler.flatten().tolist()
            
            # Tespit edilen markerları çiz
            cv2.aruco.drawDetectedMarkers(frame, koseler, idler)
            
            merkezler = []
            
            for i, (kose, id_num) in enumerate(zip(koseler, idler)):
                kose = kose[0]  # (1, 4, 2) -> (4, 2)
                
                # İlk marker ile piksel/cm oranını güncelle
                if i == 0:
                    self.piksel_cm_orani_guncelle(kose)
                
                # Merkez noktasını bul
                merkez = self.marker_merkezi_bul(kose)
                merkezler.append((id_num[0], merkez))
                tespit_bilgisi["merkezler"].append(merkez)
                
                # Merkez noktasını çiz
                cv2.circle(frame, merkez, 7, (0, 255, 0), -1)
                
                # Marker ID'sini yaz
                cv2.putText(frame, f"ID: {id_num[0]}", 
                           (merkez[0] - 20, merkez[1] - 20),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)
            
            # En az 2 marker varsa mesafe hesapla
            if len(merkezler) >= 2:
                # İlk iki marker arasındaki mesafeyi hesapla
                id1, merkez1 = merkezler[0]
                id2, merkez2 = merkezler[1]
                
                mesafe_cm = self.mesafe_cm_hesapla(merkez1, merkez2)
                
                if mesafe_cm is not None:
                    # İki merkez arasına çizgi çiz
                    cv2.line(frame, merkez1, merkez2, (0, 0, 255), 3)
                    
                    # Mesafeyi çizginin ortasına yaz
                    orta_x = (merkez1[0] + merkez2[0]) // 2
                    orta_y = (merkez1[1] + merkez2[1]) // 2
                    
                    mesafe_text = f"{mesafe_cm:.2f} cm"
                    
                    # Arka plan dikdörtgeni
                    (text_w, text_h), _ = cv2.getTextSize(mesafe_text, 
                                                          cv2.FONT_HERSHEY_SIMPLEX, 
                                                          1, 2)
                    cv2.rectangle(frame, 
                                 (orta_x - text_w//2 - 10, orta_y - text_h - 10),
                                 (orta_x + text_w//2 + 10, orta_y + 10),
                                 (255, 255, 255), -1)
                    
                    cv2.putText(frame, mesafe_text,
                               (orta_x - text_w//2, orta_y),
                               cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        
        # Bilgi paneli ekle
        self.bilgi_paneli_ekle(frame, tespit_bilgisi, mesafe_cm)
        
        return frame, mesafe_cm, tespit_bilgisi
    
    def bilgi_paneli_ekle(self, frame, tespit_bilgisi, mesafe_cm):
        """
        Frame'e bilgi paneli ekler.
        
        Parametreler:
        -------------
        frame : numpy.ndarray
            Video frame'i
        tespit_bilgisi : dict
            Tespit edilen markerlar hakkında bilgi
        mesafe_cm : float veya None
            Ölçülen mesafe
        """
        # Yarı saydam arka plan
        overlay = frame.copy()
        cv2.rectangle(overlay, (10, 10), (350, 150), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
        
        # Bilgileri yaz
        y = 35
        cv2.putText(frame, f"Marker Boyutu: {self.marker_boyutu_cm} cm", 
                   (20, y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        
        y += 25
        cv2.putText(frame, f"Tespit: {tespit_bilgisi['marker_sayisi']} marker", 
                   (20, y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        
        y += 25
        if mesafe_cm is not None:
            cv2.putText(frame, f"Mesafe: {mesafe_cm:.2f} cm", 
                       (20, y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1)
        else:
            cv2.putText(frame, "Mesafe: 2 marker gerekli", 
                       (20, y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 1)
        
        y += 25
        cv2.putText(frame, f"Kayit Sayisi: {len(self.olcum_kayitlari)}", 
                   (20, y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        
        y += 25
        cv2.putText(frame, "'s':Kaydet 'r':Sifirla 'q':Cikis", 
                   (20, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
    
    def olcum_kaydet(self, mesafe_cm, marker_idleri):
        """
        Ölçümü listeye ekler.
        
        Parametreler:
        -------------
        mesafe_cm : float
            Ölçülen mesafe
        marker_idleri : list
            Kullanılan marker ID'leri
        """
        kayit = {
            "tarih": datetime.now().strftime("%Y-%m-%d"),
            "saat": datetime.now().strftime("%H:%M:%S"),
            "marker_1_id": marker_idleri[0] if len(marker_idleri) > 0 else None,
            "marker_2_id": marker_idleri[1] if len(marker_idleri) > 1 else None,
            "marker_boyutu_cm": self.marker_boyutu_cm,
            "mesafe_cm": round(mesafe_cm, 2),
            "piksel_cm_orani": round(self.piksel_cm_orani, 4) if self.piksel_cm_orani else None
        }
        self.olcum_kayitlari.append(kayit)
        print(f"✓ Ölçüm kaydedildi: {mesafe_cm:.2f} cm")
        return kayit
    
    def excel_kaydet(self):
        """
        Tüm ölçümleri Excel dosyasına kaydeder.
        Mevcut dosya varsa üzerine ekler.
        """
        if not self.olcum_kayitlari:
            print("⚠ Kaydedilecek ölçüm yok!")
            return
        
        yeni_df = pd.DataFrame(self.olcum_kayitlari)
        
        # Mevcut dosya varsa birleştir
        if os.path.exists(self.excel_dosyasi):
            try:
                mevcut_df = pd.read_excel(self.excel_dosyasi)
                df = pd.concat([mevcut_df, yeni_df], ignore_index=True)
            except:
                df = yeni_df
        else:
            df = yeni_df
        
        # Excel'e kaydet
        df.to_excel(self.excel_dosyasi, index=False, engine='openpyxl')
        print(f"✓ {len(self.olcum_kayitlari)} ölçüm Excel'e kaydedildi: {self.excel_dosyasi}")
        
        # Listeyi temizle
        self.olcum_kayitlari = []
    
    def kayitlari_sifirla(self):
        """Kaydedilmemiş ölçümleri siler."""
        self.olcum_kayitlari = []
        print("✓ Kayıtlar sıfırlandı")


def kamera_sec():
    """
    Kullanıcının kamera kaynağını seçmesini sağlar.
    
    Döndürür:
    ---------
    kamera_kaynak : int veya str
        Kamera indeksi veya IP webcam URL'i
    """
    print("\n=== KAMERA SEÇİMİ ===")
    print("1. Laptop/USB Kamera (varsayılan)")
    print("2. IP Webcam (telefon)")
    
    secim = input("\nSeçiminiz (1/2): ").strip()
    
    if secim == "2":
        print("\n--- IP WEBCAM AYARLARI ---")
        print("1. Telefonunuza 'IP Webcam' uygulamasını yükleyin")
        print("2. Uygulamayı açın ve 'Start Server' butonuna basın")
        print("3. Ekranda görünen IP adresini girin")
        print("   Örnek: 192.168.1.100:8080")
        
        ip = input("\nIP adresi (port dahil): ").strip()
        if ip:
            # IP Webcam URL formatı
            return f"http://{ip}/video"
        else:
            print("Geçersiz IP! Varsayılan kamera kullanılıyor...")
            return 0
    else:
        return 0


def main():
    """Ana program döngüsü."""
    print("=" * 50)
    print("   ARUCO MARKER İLE MESAFE ÖLÇÜMÜ")
    print("=" * 50)
    
    # Marker boyutunu al
    print("\nMarker boyutunu girin (yazdırdığınız marker'ın gerçek boyutu)")
    try:
        boyut = float(input("Marker boyutu (cm) [varsayılan: 5]: ") or "5")
    except ValueError:
        boyut = 5.0
    
    # Kamera seç
    kamera_kaynak = kamera_sec()
    
    # Ölçücü oluştur
    olcucu = ArucoMesafeOlcucu(marker_boyutu_cm=boyut)
    
    # Kamerayı başlat
    print("\nKamera başlatılıyor...")
    cap = cv2.VideoCapture(kamera_kaynak)
    
    if not cap.isOpened():
        print("HATA: Kamera açılamadı!")
        print("- Kameranın bağlı olduğundan emin olun")
        print("- IP Webcam kullanıyorsanız aynı ağda olduğunuzdan emin olun")
        return
    
    # Kamera özelliklerini ayarla
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    
    print("\n✓ Kamera başlatıldı!")
    print("\n--- KONTROLLER ---")
    print("'s' - Mevcut ölçümü kaydet")
    print("'r' - Kayıtları sıfırla")
    print("'q' - Çıkış (Excel'e kaydeder)")
    print("-" * 30)
    
    son_mesafe = None
    son_marker_idleri = []
    
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Kamera bağlantısı kesildi!")
            break
        
        # Frame'i işle
        islenmiş_frame, mesafe_cm, tespit = olcucu.frame_isle(frame)
        
        # Son geçerli ölçümü sakla
        if mesafe_cm is not None:
            son_mesafe = mesafe_cm
            son_marker_idleri = tespit["marker_idleri"]
        
        # Görüntüyü göster
        cv2.imshow("ArUco Mesafe Olcumu", islenmiş_frame)
        
        # Tuş kontrolü
        key = cv2.waitKey(1) & 0xFF
        
        if key == ord('q'):
            # Çıkışta Excel'e kaydet
            olcucu.excel_kaydet()
            break
        elif key == ord('s'):
            # Mevcut ölçümü kaydet
            if son_mesafe is not None:
                olcucu.olcum_kaydet(son_mesafe, son_marker_idleri)
            else:
                print("⚠ Kaydedilecek geçerli ölçüm yok!")
        elif key == ord('r'):
            # Kayıtları sıfırla
            olcucu.kayitlari_sifirla()
    
    # Temizlik
    cap.release()
    cv2.destroyAllWindows()
    print("\nProgram sonlandırıldı.")


if __name__ == "__main__":
    main()
