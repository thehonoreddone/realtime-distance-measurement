import cv2
import numpy as np
import pandas as pd
from datetime import datetime
import os
import math


class ReferansNesneMesafeOlcucu:
    
    def __init__(self):
        # Kalibrasyon değerleri
        self.kalibre_edildi = False
        self.piksel_cm_orani = None
        self.referans_uzunluk_cm = None
        
        # Nokta seçimi için değişkenler
        self.secili_noktalar = []
        self.kalibrasyon_noktalari = []
        self.mod = "bekleme"  # "bekleme", "kalibrasyon", "olcum"
        
        # Mevcut frame (fare callback için)
        self.mevcut_frame = None
        self.gosterim_frame = None
        
        # Ölçüm kayıtları
        self.olcum_kayitlari = []
        
        # Son ölçülen mesafe
        self.son_mesafe = None
        
        # Excel dosya yolu
        self.excel_dosyasi = os.path.join(
            os.path.dirname(__file__), 
            "referans_mesafe_olcumleri.xlsx"
        )
    
    def fare_callback(self, event, x, y, flags, param):

        if event == cv2.EVENT_LBUTTONDOWN:
            if self.mod == "kalibrasyon":
                # Kalibrasyon modunda nokta ekle
                if len(self.kalibrasyon_noktalari) < 2:
                    self.kalibrasyon_noktalari.append((x, y))
                    print(f"Kalibrasyon noktası {len(self.kalibrasyon_noktalari)}: ({x}, {y})")
                    
                    if len(self.kalibrasyon_noktalari) == 2:
                        self.kalibrasyon_tamamla()
                        
            elif self.mod == "olcum":
                # Ölçüm modunda nokta ekle
                if len(self.secili_noktalar) < 2:
                    self.secili_noktalar.append((x, y))
                    print(f"Ölçüm noktası {len(self.secili_noktalar)}: ({x}, {y})")
                    
                    if len(self.secili_noktalar) == 2:
                        self.mesafe_hesapla_ve_goster()
    
    def iki_nokta_arasi_mesafe_piksel(self, nokta1, nokta2):
        return math.sqrt((nokta2[0] - nokta1[0])**2 + (nokta2[1] - nokta1[1])**2)
    
    def kalibrasyon_tamamla(self):
        if len(self.kalibrasyon_noktalari) != 2:
            print("Kalibrasyon için 2 nokta gerekli!")
            return
        
        # Piksel cinsinden mesafe
        piksel_mesafe = self.iki_nokta_arasi_mesafe_piksel(
            self.kalibrasyon_noktalari[0],
            self.kalibrasyon_noktalari[1]
        )
        
        # Piksel/cm oranı = piksel_mesafe / gerçek_uzunluk
        self.piksel_cm_orani = piksel_mesafe / self.referans_uzunluk_cm
        self.kalibre_edildi = True
        
        print(f"\n KALİBRASYON TAMAMLANDI")
        print(f"  Referans uzunluk: {self.referans_uzunluk_cm} cm")
        print(f"  Piksel mesafe: {piksel_mesafe:.2f} piksel")
        print(f"  Piksel/cm oranı: {self.piksel_cm_orani:.4f}")
        
        self.mod = "bekleme"
    
    def kalibrasyon_baslat(self, referans_uzunluk_cm):
        self.referans_uzunluk_cm = referans_uzunluk_cm
        self.kalibrasyon_noktalari = []
        self.kalibre_edildi = False
        self.mod = "kalibrasyon"
        
        print(f"Referans nesne uzunluğu: {referans_uzunluk_cm} cm")
    
    def olcum_baslat(self):
        if not self.kalibre_edildi:
            print("Önce kalibrasyon yapılmalı!")
            return False
        
        self.secili_noktalar = []
        self.son_mesafe = None
        self.mod = "olcum"
        
        print(f"Ölçülecek iki noktaya tıklayın...")
        return True
    
    def mesafe_hesapla_ve_goster(self):
        if len(self.secili_noktalar) != 2:
            print("2 nokta seçilmeli!")
            return
        
        # Piksel cinsinden mesafe
        piksel_mesafe = self.iki_nokta_arasi_mesafe_piksel(
            self.secili_noktalar[0],
            self.secili_noktalar[1]
        )
        
        # CM cinsinden mesafe
        self.son_mesafe = piksel_mesafe / self.piksel_cm_orani
        
        print(f"\n ÖLÇÜM SONUCU: {self.son_mesafe:.2f} cm")
        print(f"  Piksel mesafe: {piksel_mesafe:.2f}")
        
        self.mod = "bekleme"
    
    def frame_isle(self, frame):
        self.mevcut_frame = frame.copy() # Kameradan alınan görüntü.
        gosterim = frame.copy() # Bir kopya üzerinde çizim yapılır (gosterim). Orijinal frame başka işlemler için saklanabilir.Bu görüntüye çember, yazı, çizgi, bilgi paneli vs. çizilecek.
        
        # Kalibrasyon noktalarını çiz
        if self.mod == "kalibrasyon":
            for i, nokta in enumerate(self.kalibrasyon_noktalari):
                cv2.circle(gosterim, nokta, 8, (0, 255, 255), -1)  # Sarı, nokta: cemberin merkezi. 8 piksele yarıçap, -1 ise çember doldurulmuş
                cv2.putText(gosterim, f"K{i+1}", 
                           (nokta[0] + 10, nokta[1] - 10), # yazıyı kaydırıyor sağa ve yukarı  
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2) # 0.6 → fontScale, 2 → thickness
            
            # Kalibrasyon çizgisi
            if len(self.kalibrasyon_noktalari) == 2:
                cv2.line(gosterim, 
                        self.kalibrasyon_noktalari[0],
                        self.kalibrasyon_noktalari[1],
                        (0, 255, 255), 2, cv2.LINE_AA) # Anti-Aliasing (pürüzsüz çizgi), 2 px kalınlık
                
                # Referans uzunluğu yaz
                orta = (
                    (self.kalibrasyon_noktalari[0][0] + self.kalibrasyon_noktalari[1][0]) // 2, # mesafe yazısının ortada gözükmesi için
                    (self.kalibrasyon_noktalari[0][1] + self.kalibrasyon_noktalari[1][1]) // 2 # iki noktanın ortasını bulur,
                )
                cv2.putText(gosterim, f"REF: {self.referans_uzunluk_cm} cm",
                           (orta[0] - 50, orta[1] - 15),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        
        # Ölçüm noktalarını çiz
        for i, nokta in enumerate(self.secili_noktalar):
            cv2.circle(gosterim, nokta, 8, (0, 255, 0), -1)  # Yeşil
            cv2.putText(gosterim, f"P{i+1}", 
                       (nokta[0] + 10, nokta[1] - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        # Ölçüm çizgisi ve mesafe
        if len(self.secili_noktalar) == 2 and self.son_mesafe is not None:
            cv2.line(gosterim, 
                    self.secili_noktalar[0],
                    self.secili_noktalar[1],
                    (0, 0, 255), 3, cv2.LINE_AA)
            
            # Mesafeyi yaz
            orta = (
                (self.secili_noktalar[0][0] + self.secili_noktalar[1][0]) // 2,
                (self.secili_noktalar[0][1] + self.secili_noktalar[1][1]) // 2
            )
            
            mesafe_text = f"{self.son_mesafe:.2f} cm"
            (text_w, text_h), _ = cv2.getTextSize(mesafe_text,  #mesafe yazısının arkasındaki beyaz kutu yukselik genislik alır oto ayarlanır.
                                                  cv2.FONT_HERSHEY_SIMPLEX,  
                                                  1, 2) # 1 → fontScale, 2 → thickness
            cv2.rectangle(gosterim, 
                         (orta[0] - text_w//2 - 10, orta[1] - text_h - 10), #Kutuyu yazının soluna kaydırır, # Kutuyu yukarı taşır
                         (orta[0] + text_w//2 + 10, orta[1] + 10),
                         (255, 255, 255), -1) # -1 dikdörtgeni doldur demek. 1 olursa sadece kenar. 2 olursa daha kalın kenar
            cv2.putText(gosterim, mesafe_text,
                       (orta[0] - text_w//2, orta[1]),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        
        # Bilgi paneli
        self.bilgi_paneli_ekle(gosterim)
        
        self.gosterim_frame = gosterim
        return gosterim
    
    def bilgi_paneli_ekle(self, frame):
        # Yarı saydam arka plan
        overlay = frame.copy() # üzerine çizilecek görüntü
        cv2.rectangle(overlay, (10, 10), (400, 180), (0, 0, 0), -1) # sol üst köşe,sağ alt köşe, siyah renk,dikdörtgen doldur.
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame) # Sonuç: %70 karanlık – %30 orijinal görüntü → yarı saydam panel.overlay %70,frame %30,gamma (ekstra parlaklık eklemez) 50 olsaydı görüntüyü ekstra aydınlatır.
        
        y = 35 # satır ayarlama,Bu ekrana yazılacak yazıların başlangıç yüksekliğidir.
        
        # Mod durumu
        mod_renk = {
            "bekleme": (200, 200, 200),
            "kalibrasyon": (0, 255, 255),
            "olcum": (0, 255, 0)
        }
        mod_text = {
            "bekleme": "Bekleme",
            "kalibrasyon": "KALİBRASYON - 2 nokta seçin",
            "olcum": "ÖLÇÜM - 2 nokta seçin"
        }
        cv2.putText(frame, f"Mod: {mod_text[self.mod]}", 
                   (20, y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, mod_renk[self.mod], 1) # Yazı ekranın solundan 20px içeride başlasın x koordinatı
        
        y += 25
        if self.kalibre_edildi:
            cv2.putText(frame, f"Kalibrasyon: TAMAM (1px = {1/self.piksel_cm_orani:.4f} cm)", 
                       (20, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        else:
            cv2.putText(frame, "Kalibrasyon: YAPILMADI", 
                       (20, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
        
        y += 25
        if self.son_mesafe is not None:
            cv2.putText(frame, f"Son Olcum: {self.son_mesafe:.2f} cm", 
                       (20, y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1)
        else:
            cv2.putText(frame, "Son Olcum: -", 
                       (20, y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)
        
        y += 25
        cv2.putText(frame, f"Kayit Sayisi: {len(self.olcum_kayitlari)}", 
                   (20, y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        
        y += 30
        cv2.putText(frame, "'c':Kalibrasyon 'n':Yeni Olcum", 
                   (20, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
        y += 20
        cv2.putText(frame, "'s':Kaydet 'r':Sifirla 'q':Cikis", 
                   (20, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
        
    
    def olcum_kaydet(self):
        if self.son_mesafe is None:
            print("Kaydedilecek ölçüm yok!")
            return None
        
        kayit = {
            "tarih": datetime.now().strftime("%Y-%m-%d"),
            "saat": datetime.now().strftime("%H:%M:%S"),
            "referans_uzunluk_cm": self.referans_uzunluk_cm,
            "nokta1_x": self.secili_noktalar[0][0] if len(self.secili_noktalar) > 0 else None,
            "nokta1_y": self.secili_noktalar[0][1] if len(self.secili_noktalar) > 0 else None,
            "nokta2_x": self.secili_noktalar[1][0] if len(self.secili_noktalar) > 1 else None,
            "nokta2_y": self.secili_noktalar[1][1] if len(self.secili_noktalar) > 1 else None,
            "mesafe_cm": round(self.son_mesafe, 2),
            "piksel_cm_orani": round(self.piksel_cm_orani, 4) if self.piksel_cm_orani else None
        }
        self.olcum_kayitlari.append(kayit)
        print(f"✓ Ölçüm kaydedildi: {self.son_mesafe:.2f} cm")
        return kayit
    
    def excel_kaydet(self):
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
        """Kaydedilmemiş ölçümleri ve seçimleri siler."""
        self.olcum_kayitlari = []
        self.secili_noktalar = []
        self.son_mesafe = None
        print("✓ Kayıtlar ve seçimler sıfırlandı")


def main():
    # Ölçücü oluştur
    olcucu = ReferansNesneMesafeOlcucu()
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("HATA: Kamera açılamadı!")
        return
    
    # Kamera özelliklerini ayarla
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    
    # Pencere oluştur ve fare callback'i ayarla
    pencere_adi = "Referans Nesne Mesafe Olcumu"
    cv2.namedWindow(pencere_adi)
    cv2.setMouseCallback(pencere_adi, olcucu.fare_callback)
    
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Kamera bağlantısı kesildi!")
            break
        
        # Frame'i işle
        gosterim = olcucu.frame_isle(frame)
        
        # Görüntüyü göster
        cv2.imshow(pencere_adi, gosterim)
        
        # Tuş kontrolü
        key = cv2.waitKey(1) & 0xFF
        
        if key == ord('q'):
            # Çıkışta Excel'e kaydet
            olcucu.excel_kaydet()
            break
            
        elif key == ord('c'):
            # Kalibrasyon modu
            print("\n--- KALİBRASYON ---")
            
            bilgi_frame = gosterim.copy()
            cv2.imshow(pencere_adi, bilgi_frame)
            cv2.waitKey(10)
            
            try:
                print(">>> Lütfen referans nesnenin uzunluğunu cm cinsinden girip ENTER'a basın <<<")
                uzunluk_str = input("Referans nesnenin uzunluğunu girin (cm): ")
                if uzunluk_str:
                    uzunluk = float(uzunluk_str)
                    if uzunluk > 0:
                        olcucu.kalibrasyon_baslat(uzunluk)
                    else:
                        print("Uzunluk pozitif olmalı!")
            except ValueError:
                print("Geçersiz değer!")
                
        elif key == ord('n'):
            # Yeni ölçüm
            olcucu.olcum_baslat()
            
        elif key == ord('s'):
            # Mevcut ölçümü kaydet
            olcucu.olcum_kaydet()
            
        elif key == ord('r'):
            # Kayıtları sıfırla
            olcucu.kayitlari_sifirla()
    
    # Temizlik
    cap.release()
    cv2.destroyAllWindows()
    print("\nProgram sonlandırıldı.")


if __name__ == "__main__":
    main()
