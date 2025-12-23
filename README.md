# 📏 Gerçek Zamanlı Mesafe Ölçümü Projesi

Bu proje, kamera kullanarak iki nesne arasındaki mesafeyi ölçmek için iki farklı yöntem sunar. Hem laptop kamerası hem de telefon kamerası (IP Webcam) ile çalışabilir. Ölçüm sonuçları Excel dosyasına kaydedilir.

## 📁 Proje Yapısı

```
realtime_mesafe_ölcümü/
├── aruco_marker_olusturucu.py    # ArUco marker oluşturma aracı
├── aruco_mesafe_olcumu.py        # Yöntem 1: ArUco marker ile ölçüm
├── referans_nesne_mesafe_olcumu.py # Yöntem 2: Referans nesne ile ölçüm
├── requirements.txt              # Gerekli Python paketleri
├── README.md                     # Bu dosya
├── markers/                      # Oluşturulan ArUco markerlar (otomatik)
├── aruco_mesafe_olcumleri.xlsx   # ArUco ölçüm kayıtları (otomatik)
└── referans_mesafe_olcumleri.xlsx # Referans ölçüm kayıtları (otomatik)
```

## 🚀 Kurulum

### 1. Python Paketlerini Yükleyin

```bash
pip install -r requirements.txt
```

### 2. Gerekli Paketler

| Paket | Açıklama |
|-------|----------|
| `opencv-python` | Görüntü işleme ve kamera erişimi |
| `opencv-contrib-python` | ArUco marker desteği |
| `numpy` | Sayısal hesaplamalar |
| `pandas` | Excel okuma/yazma |
| `openpyxl` | Excel dosya formatı desteği |

---

# 🎯 YÖNTEM 1: ArUco Marker ile Mesafe Ölçümü

## Genel Bakış

ArUco markerlar, özel olarak tasarlanmış siyah-beyaz karelerdir. Bilgisayar görüşü sistemleri tarafından kolayca tespit edilebilir ve benzersiz ID'leri sayesinde tanınabilirler.

### ✅ Avantajları
- **Kamera hareketine dayanıklı**: Marker boyutu her zaman bilindiği için kamera hareket etse bile doğru ölçüm yapılır
- **Otomatik kalibrasyon**: Her frame'de piksel/cm oranı güncellenir
- **Yüksek doğruluk**: Marker köşeleri piksel düzeyinde tespit edilir

### ⚠️ Dezavantajları
- Marker yazdırılması ve yapıştırılması gerekir
- Markerlar görünür olmalı ve kapatılmamalı

---

## 📄 aruco_marker_olusturucu.py

Bu script, yazdırılabilir ArUco markerları oluşturur.

### Çalıştırma

```bash
python aruco_marker_olusturucu.py
```

### Fonksiyonlar

#### `aruco_marker_olustur(marker_id, marker_boyutu_cm, cozunurluk_piksel=200)`

Tek bir ArUco marker görüntüsü oluşturur.

**Parametreler:**
- `marker_id` (int): Marker'ın benzersiz kimlik numarası (0-249)
- `marker_boyutu_cm` (float): Marker'ın gerçek dünya boyutu (cm)
- `cozunurluk_piksel` (int): Çıktı görüntüsünün piksel boyutu

**Ne yapar:**
1. OpenCV'nin ArUco sözlüğünü kullanarak marker matrisi oluşturur
2. Beyaz kenarlık ekler (tespit doğruluğu için kritik)
3. PNG formatında görüntü döndürür

**Neden kullanıyoruz:**
- Markerlar benzersiz ID'lere sahip olduğu için hangi nesnenin hangisi olduğunu ayırt edebiliriz
- Boyutu bildiğimiz için piksel-cm dönüşümü yapabiliriz

```python
# Örnek: ID=5, 4cm boyutunda marker
marker = aruco_marker_olustur(5, 4.0)
```

#### `tum_markerlari_olustur(boyutlar_cm=[3, 4, 5], marker_sayisi=4)`

Farklı boyutlarda birden fazla marker oluşturur.

**Parametreler:**
- `boyutlar_cm` (list): Oluşturulacak marker boyutları
- `marker_sayisi` (int): Her boyut için kaç marker

**Ne yapar:**
1. Her boyut için belirtilen sayıda marker oluşturur
2. `markers/` klasörüne kaydeder
3. A4 boyutunda birleşik sayfa oluşturur

#### `birlesik_sayfa_olustur(markers_klasoru, boyutlar_cm, marker_sayisi)`

Tüm markerları tek bir yazdırılabilir sayfada birleştirir.

**Ne yapar:**
1. A4 boyutunda (300 DPI) boş sayfa oluşturur
2. Her marker'ı gerçek boyutuna ölçekler
3. Satır satır yerleştirir

**Neden kullanıyoruz:**
- Tek seferde tüm markerları yazdırabilmek için
- DPI hesabı yaparak gerçek boyutta çıktı almak için

---

## 📄 aruco_mesafe_olcumu.py

ArUco markerlar kullanarak gerçek zamanlı mesafe ölçümü yapar.

### Çalıştırma

```bash
python aruco_mesafe_olcumu.py
```

### Sınıf: `ArucoMesafeOlcucu`

Ana ölçüm sınıfı. Marker tespiti, mesafe hesaplama ve Excel kaydı yapar.

#### `__init__(self, marker_boyutu_cm=5.0)`

Sınıfı başlatır ve ArUco dedektörünü yapılandırır.

**Ne yapar:**
1. ArUco sözlüğünü yükler (`DICT_4X4_250`)
2. Dedektör parametrelerini optimize eder
3. Boş kayıt listesi oluşturur

**Neden DICT_4X4_250:**
- 4x4: Her marker 4x4 bit grid içerir (daha küçük markerlar için ideal)
- 250: 250 benzersiz marker ID'si (yeterince çok)
- Daha büyük grid'ler (6x6, 7x7) daha fazla ID sunar ama daha büyük marker gerektirir

```python
# ArUco dedektör parametreleri
self.detector_params.adaptiveThreshWinSizeMin = 3
self.detector_params.adaptiveThreshWinSizeMax = 23
self.detector_params.adaptiveThreshWinSizeStep = 10
```

**Bu parametreler ne yapar:**
- `adaptiveThreshWinSizeMin/Max`: Uyarlanabilir eşikleme pencere boyutu aralığı
- Farklı aydınlatma koşullarında marker tespitini iyileştirir
- Küçük ve büyük markerları tespit edebilmek için değişken pencere boyutu

#### `marker_merkezi_bul(self, koseleler)`

Marker'ın 4 köşe noktasından merkez noktasını hesaplar.

**Formül:**
```
merkez_x = (x1 + x2 + x3 + x4) / 4
merkez_y = (y1 + y2 + y3 + y4) / 4
```

**Neden kullanıyoruz:**
- Mesafe iki marker'ın merkez noktaları arasından ölçülür
- Köşeler perspektif nedeniyle kayabilir, merkez daha stabil

#### `marker_boyutu_piksel_hesapla(self, koseleler)`

Marker'ın piksel cinsinden kenar uzunluğunu hesaplar.

**Ne yapar:**
1. 4 kenarın uzunluğunu hesaplar (Öklid mesafesi)
2. Ortalamayı alır

**Neden 4 kenarın ortalaması:**
- Perspektif bozulması nedeniyle tüm kenarlar eşit görünmez
- Ortalama almak daha güvenilir sonuç verir

```python
kenar = np.linalg.norm(koseleler[0] - koseleler[1])
# linalg.norm: √((x2-x1)² + (y2-y1)²)
```

#### `piksel_cm_orani_guncelle(self, koseleler)`

Her frame'de piksel/cm oranını günceller.

**Formül:**
```
piksel_cm_orani = marker_piksel_boyutu / marker_gercek_boyutu_cm
```

**Neden her frame'de güncelliyoruz:**
- Kamera yaklaşır/uzaklaşırsa oran değişir
- Zoom değişirse oran değişir
- Böylece kamera hareketine dayanıklı olur

#### `iki_nokta_arasi_mesafe(self, nokta1, nokta2)`

Öklid mesafesi hesaplar.

**Formül:**
```
mesafe = √((x2-x1)² + (y2-y1)²)
```

**Neden Öklid mesafesi:**
- 2D düzlemde iki nokta arası en kısa mesafe
- Pitagor teoreminin uygulaması

#### `mesafe_cm_hesapla(self, merkez1, merkez2)`

Piksel mesafesini cm'ye çevirir.

**Formül:**
```
mesafe_cm = piksel_mesafe / piksel_cm_orani
```

**Örnek:**
- Marker boyutu: 5 cm
- Marker piksel boyutu: 100 px
- Piksel/cm oranı: 100/5 = 20 px/cm
- İki merkez arası: 200 px
- Gerçek mesafe: 200/20 = 10 cm

#### `frame_isle(self, frame)`

Ana işleme fonksiyonu. Her video frame'i için çağrılır.

**İşlem adımları:**
1. Frame'i gri tonlamaya çevir (ArUco tespiti için gerekli)
2. Markerları tespit et
3. Her marker için:
   - Merkez noktasını bul
   - Piksel/cm oranını güncelle (ilk marker ile)
   - Görsel işaretler çiz
4. 2+ marker varsa mesafe hesapla
5. Bilgi paneli ekle

**Neden gri tonlama:**
- ArUco dedektörü tek kanallı görüntü bekler
- Renk bilgisi marker tespiti için gereksiz
- Daha hızlı işlem

```python
gri = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
koseler, idler, reddedilenler = self.detector.detectMarkers(gri)
```

**detectMarkers dönüş değerleri:**
- `koseler`: Her marker için 4 köşe noktası
- `idler`: Marker ID'leri
- `reddedilenler`: Tespit edilemeyen aday bölgeler (debug için)

#### `bilgi_paneli_ekle(self, frame, tespit_bilgisi, mesafe_cm)`

Ekrana bilgi paneli ekler.

**Ne yapar:**
1. Yarı saydam siyah dikdörtgen çizer
2. Marker boyutu, tespit sayısı, mesafe ve kayıt sayısını yazar
3. Kontrol tuşlarını gösterir

**Neden yarı saydam:**
- Arka plandaki görüntüyü tamamen kapatmaz
- `cv2.addWeighted` ile alpha blending yapar

```python
cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
# 0.7: overlay ağırlığı, 0.3: orijinal frame ağırlığı
```

#### `olcum_kaydet(self, mesafe_cm, marker_idleri)`

Ölçümü listeye ekler.

**Kaydedilen bilgiler:**
- Tarih ve saat
- Marker ID'leri
- Marker boyutu
- Ölçülen mesafe
- Piksel/cm oranı (debug için)

#### `excel_kaydet(self)`

Ölçümleri Excel'e yazar.

**Ne yapar:**
1. Mevcut dosya varsa oku
2. Yeni kayıtları ekle
3. Tekrar yaz

**Neden pandas kullanıyoruz:**
- Excel okuma/yazma için en kolay yol
- DataFrame yapısı tablo verileri için ideal
- `openpyxl` motoru modern Excel formatını destekler

### Fonksiyon: `kamera_sec()`

Kullanıcının kamera kaynağını seçmesini sağlar.

**Seçenekler:**
1. Laptop/USB kamera: `cap = cv2.VideoCapture(0)`
2. IP Webcam: `cap = cv2.VideoCapture("http://IP:PORT/video")`

**IP Webcam URL formatı:**
- Android: `http://192.168.x.x:8080/video`
- Uygulama: "IP Webcam" (Play Store'dan)

### Fonksiyon: `main()`

Ana program döngüsü.

**Akış:**
1. Marker boyutunu al
2. Kamera kaynağını seç
3. Kamerayı aç
4. Sonsuz döngüde:
   - Frame oku
   - Frame'i işle
   - Görüntüle
   - Tuş kontrolü yap
5. Çıkışta Excel'e kaydet

---

# 🎯 YÖNTEM 2: Referans Nesne ile Mesafe Ölçümü

## Genel Bakış

Bu yöntemde, uzunluğu bilinen herhangi bir nesne (cetvel, kalem, kağıt kenarı vb.) referans olarak kullanılır.

### ✅ Avantajları
- Marker yazdırmaya gerek yok
- Herhangi bir nesne referans olabilir
- Esnek kullanım

### ⚠️ Dezavantajları
- **KAMERA SABİT TUTULMALI**: Kalibrasyon sonrası kamera hareket ederse ölçümler hatalı olur
- Manuel nokta seçimi gerekir
- Kalibrasyon her kamera hareketi için tekrarlanmalı

---

## 📄 referans_nesne_mesafe_olcumu.py

Referans nesne kullanarak mesafe ölçümü yapar.

### Çalıştırma

```bash
python referans_nesne_mesafe_olcumu.py
```

### Sınıf: `ReferansNesneMesafeOlcucu`

Ana ölçüm sınıfı.

#### `__init__(self)`

Sınıfı başlatır.

**Değişkenler:**
- `kalibre_edildi`: Kalibrasyon durumu
- `piksel_cm_orani`: Hesaplanan oran
- `mod`: Mevcut çalışma modu ("bekleme", "kalibrasyon", "olcum")
- `secili_noktalar`: Kullanıcının tıkladığı noktalar

#### `fare_callback(self, event, x, y, flags, param)`

Fare tıklamalarını işler.

**Ne yapar:**
1. Sol tık algıla (`cv2.EVENT_LBUTTONDOWN`)
2. Moda göre işlem yap:
   - Kalibrasyon: Referans nesnenin iki ucunu kaydet
   - Ölçüm: Ölçülecek iki noktayı kaydet

**Neden callback:**
- OpenCV'nin fare olaylarını yakalaması için standart yöntem
- `cv2.setMouseCallback(pencere_adi, callback_fonksiyonu)`

```python
cv2.setMouseCallback(pencere_adi, olcucu.fare_callback)
```

#### `iki_nokta_arasi_mesafe_piksel(self, nokta1, nokta2)`

Öklid mesafesi hesaplar (ArUco yöntemiyle aynı).

#### `kalibrasyon_tamamla(self)`

Kalibrasyon noktalarından piksel/cm oranını hesaplar.

**Formül:**
```
piksel_cm_orani = referans_piksel_mesafe / referans_gercek_uzunluk
```

**Örnek:**
- Referans nesne: 10 cm cetvel
- Ekranda ölçülen piksel mesafe: 150 px
- Piksel/cm oranı: 150/10 = 15 px/cm

**⚠️ Kritik uyarı:**
Kamera hareket ederse bu oran geçersiz olur!

#### `kalibrasyon_baslat(self, referans_uzunluk_cm)`

Kalibrasyon modunu aktifleştirir.

**Ne yapar:**
1. Referans uzunluğu sakla
2. Önceki kalibrasyon noktalarını temizle
3. Modu "kalibrasyon" yap

#### `olcum_baslat(self)`

Ölçüm modunu başlatır.

**Kontrol:**
- Kalibrasyon yapılmamışsa uyarı ver
- Yapılmışsa "olcum" moduna geç

#### `mesafe_hesapla_ve_goster(self)`

Seçilen iki nokta arasındaki mesafeyi hesaplar.

**Formül:**
```
mesafe_cm = piksel_mesafe / piksel_cm_orani
```

#### `frame_isle(self, frame)`

Her frame'i işler ve görselleştirme yapar.

**Görsel öğeler:**
- Kalibrasyon noktaları: Sarı daireler (K1, K2)
- Kalibrasyon çizgisi: Sarı çizgi
- Ölçüm noktaları: Yeşil daireler (P1, P2)
- Ölçüm çizgisi: Kırmızı çizgi
- Mesafe değeri: Beyaz arka plan üzerinde kırmızı yazı

**Neden farklı renkler:**
- Kalibrasyon ve ölçüm noktalarını ayırt etmek için
- Sarı: Kalibrasyon (uyarı rengi)
- Yeşil: Seçim noktaları
- Kırmızı: Ölçüm sonucu (dikkat çekici)

#### `bilgi_paneli_ekle(self, frame)`

Durum bilgilerini gösterir.

**Özel özellik:**
- Kamera sabit tutulması uyarısı (sağ üst köşe, kırmızı)

```python
cv2.putText(frame, "! KAMERAYI HAREKET ETTIRMEYIN !", 
           (frame.shape[1] - 350, 30), 
           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
```

#### `olcum_kaydet(self)` ve `excel_kaydet(self)`

ArUco yöntemiyle benzer, ek olarak nokta koordinatlarını kaydeder.

---

# 📊 Excel Çıktı Formatları

## ArUco Ölçümleri (aruco_mesafe_olcumleri.xlsx)

| Sütun | Açıklama |
|-------|----------|
| tarih | Ölçüm tarihi |
| saat | Ölçüm saati |
| marker_1_id | İlk marker ID'si |
| marker_2_id | İkinci marker ID'si |
| marker_boyutu_cm | Kullanılan marker boyutu |
| mesafe_cm | Ölçülen mesafe |
| piksel_cm_orani | Hesaplanan oran (debug) |

## Referans Ölçümleri (referans_mesafe_olcumleri.xlsx)

| Sütun | Açıklama |
|-------|----------|
| tarih | Ölçüm tarihi |
| saat | Ölçüm saati |
| referans_uzunluk_cm | Kalibrasyon referansı |
| nokta1_x, nokta1_y | İlk nokta koordinatları |
| nokta2_x, nokta2_y | İkinci nokta koordinatları |
| mesafe_cm | Ölçülen mesafe |
| piksel_cm_orani | Hesaplanan oran |

---

# 🎮 Kontrol Tuşları

## ArUco Yöntemi
| Tuş | İşlev |
|-----|-------|
| `s` | Mevcut ölçümü kaydet |
| `r` | Kayıtları sıfırla |
| `q` | Çıkış (Excel'e kaydeder) |

## Referans Nesne Yöntemi
| Tuş | İşlev |
|-----|-------|
| `c` | Kalibrasyon modu |
| `n` | Yeni ölçüm modu |
| `s` | Mevcut ölçümü kaydet |
| `r` | Kayıtları sıfırla |
| `q` | Çıkış (Excel'e kaydeder) |

---

# 🔧 Teknik Detaylar

## Kullanılan OpenCV Fonksiyonları

| Fonksiyon | Kullanım Amacı |
|-----------|----------------|
| `cv2.VideoCapture()` | Kamera bağlantısı |
| `cv2.cvtColor()` | Renk dönüşümü |
| `cv2.aruco.getPredefinedDictionary()` | ArUco sözlüğü |
| `cv2.aruco.ArucoDetector()` | Marker dedektörü |
| `cv2.aruco.detectMarkers()` | Marker tespiti |
| `cv2.aruco.drawDetectedMarkers()` | Tespit görselleştirme |
| `cv2.circle()` | Nokta çizme |
| `cv2.line()` | Çizgi çizme |
| `cv2.putText()` | Metin yazma |
| `cv2.rectangle()` | Dikdörtgen çizme |
| `cv2.addWeighted()` | Alpha blending |
| `cv2.setMouseCallback()` | Fare olayları |

## NumPy Fonksiyonları

| Fonksiyon | Kullanım Amacı |
|-----------|----------------|
| `np.mean()` | Ortalama hesaplama |
| `np.linalg.norm()` | Öklid mesafesi |
| `np.ones()` | Boş görüntü oluşturma |

## Pandas Fonksiyonları

| Fonksiyon | Kullanım Amacı |
|-----------|----------------|
| `pd.DataFrame()` | Veri tablosu oluşturma |
| `pd.read_excel()` | Excel okuma |
| `df.to_excel()` | Excel yazma |
| `pd.concat()` | DataFrame birleştirme |

---

# 📝 Kullanım Önerileri

## ArUco Yöntemi İçin
1. Markerları düzgün yazdırın (boyutları cetvel ile kontrol edin)
2. Markerları nesnelerin üzerine düz yapıştırın
3. Markerların tamamı görünür olmalı
4. İyi aydınlatma sağlayın
5. Marker boyutunu programa doğru girin

## Referans Nesne Yöntemi İçin
1. **KAMERAYI SABİT TUTUN** (tripod kullanın)
2. Referans olarak düz kenarlı nesne kullanın (cetvel ideal)
3. Noktaları dikkatli seçin
4. Kamera hareket ederse tekrar kalibre edin
5. Referans ve ölçülecek nesneler aynı düzlemde olmalı

---

# ⚠️ Sınırlamalar

1. **2D Ölçüm**: Sadece kameraya paralel düzlemde doğru ölçüm yapar
2. **Perspektif**: Nesneler kameraya farklı mesafedeyse hata oluşur
3. **Lens Distorsiyonu**: Ucuz kameralarda kenar bölgelerinde hata olabilir
4. **Aydınlatma**: Yetersiz ışıkta marker tespiti zorlaşır

---

# 🐛 Sorun Giderme

| Sorun | Çözüm |
|-------|-------|
| Kamera açılmıyor | Kameranın bağlı olduğunu kontrol edin |
| IP Webcam bağlanmıyor | Aynı WiFi ağında olduğunuzdan emin olun |
| Marker tespit edilmiyor | Aydınlatmayı artırın, marker boyutunu kontrol edin |
| Ölçümler hatalı | Marker boyutunu doğru girdiğinizden emin olun |
| Excel kaydedilmiyor | openpyxl paketinin yüklü olduğunu kontrol edin |

---

# 📜 Lisans

Bu proje eğitim amaçlı oluşturulmuştur.

---

# 👨‍💻 Geliştirici Notları

Bu proje görüntü işleme dersinde mesafe ölçümü konusunu öğretmek için hazırlanmıştır. İki farklı yaklaşım sunarak öğrencilerin:

1. ArUco marker sistemini ve otomatik kalibrasyon kavramını
2. Manuel kalibrasyon ve piksel-cm dönüşümünü
3. Excel entegrasyonu ve veri kaydını
4. OpenCV ile gerçek zamanlı görüntü işlemeyi

öğrenmelerini hedeflemektedir.
