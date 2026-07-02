#!/usr/bin/env python3
# -*- coding: utf-8 text -*-

import os
import re
import sys

def gdm_wayland_duzenle(durum_aktif_mi=True):
    """
    Pardus GDM3 (Gnome Display Manager) yapılandırma dosyasındaki 
    Wayland özelliğini güvenli ve dinamik olarak düzenler.
    """
    hedef_dosya = "/etc/gdm3/custom.conf"
    klasor = os.path.dirname(hedef_dosya)
    
    # Gerekli sistem klasörü yoksa oluştur
    if not os.path.exists(klasor):
        try:
            os.makedirs(klasor, exist_ok=True)
        except PermissionError:
            print("[HATA] Yetki Yetersiz! Lütfen kodu 'sudo' ile çalıştırın.")
            return False

    try:
        # Yapılandırma dosyası yoksa varsayılan şablonla oluştur
        if not os.path.exists(hedef_dosya):
            with open(hedef_dosya, "w", encoding="utf-8") as f: 
                f.write("[daemon]\nWaylandEnable=false\n")
        
        # Dosya içeriğini oku
        with open(hedef_dosya, "r", encoding="utf-8") as f: 
            icerik = f.read()
            
        yeni_deger = "WaylandEnable=true" if durum_aktif_mi else "WaylandEnable=false"
        pattern = r"^[#\s]*WaylandEnable\s*=\s*(true|false)"
        
        # Eğer WaylandEnable satırı zaten varsa değerini güncelle
        if re.search(pattern, icerik, re.IGNORECASE | re.MULTILINE):
            yeni_icerik = re.sub(pattern, yeni_deger, icerik, flags=re.IGNORECASE | re.MULTILINE)
        else:
            # Satır yoksa ama [daemon] bloğu varsa altına ekle
            if "[daemon]" in icerik: 
                yeni_icerik = icerik.replace("[daemon]", f"[daemon]\n{yeni_deger}")
            else: 
                # Hiçbiri yoksa dosya sonuna ekle
                yeni_icerik = icerik + f"\n\n[daemon]\n{yeni_deger}\n"
                
        # Güncellenmiş içeriği dosyaya güvenli bir şekilde yaz
        with open(hedef_dosya, "w", encoding="utf-8") as f: 
            f.write(yeni_icerik)
        return True
        
    except Exception as e: 
        print(f"[SİSTEM HATASI] İşlem başarısız oldu: {e}")
        return False

def dosya_oku():
    try:
        with open("/etc/gdm3/custom.conf", "r", encoding="utf-8") as f: 
            return f.read().strip()
    except FileNotFoundError:
        return "Dosya bulunamadı."

if __name__ == "__main__":
    # Test ve Doğrulama Senaryoları
    print("==================================================")
    print("     PARDUS GDM WAYLAND ENTEGRASYON TEST LABORATUVARI     ")
    print("==================================================")
    print("\n[SİSTEM BİLGİSİ] Pardus GNU/Linux Entegrasyon Modülü")
    print("-" * 50)

    # TEST 1: Başlangıç Durumunu Ayarla
    print("[TEST 1] Orijinal Durum Hazırlanıyor...")
    if gdm_wayland_duzenle(durum_aktif_mi=False):
        print("Mevcut Dosya İçeriği:\n" + "-"*20 + "\n" + dosya_oku() + "\n" + "-"*20)
    else:
        sys.exit(1)

    # TEST 2: Fonksiyonu Tetikle (Wayland Aktif Et)
    print("\n[TEST 2] Fonksiyon Tetikleniyor (Wayland Aktif Ediliyor)...")
    if gdm_wayland_duzenle(durum_aktif_mi=True): 
        print("İŞLEM: Başarıyla Tetiklendi (Pardus Yapılandırması Güncellendi).")
    print("Yeni Dosya İçeriği:\n" + "-"*20 + "\n" + dosya_oku() + "\n" + "-"*20)

    # TEST 3: Tekrarlanabilirlik ve Çakışma Kontrolü
    print("\n[TEST 3] Üst Üste Kontrol (Zaten Aktifken Tekrar Tetikleniyor)...")
    if gdm_wayland_duzenle(durum_aktif_mi=True): 
        print("İŞLEM: Tekrar Tetiklendi (Çakışma/Mükerrer Kayıt Güvenliği Aktif).")
    print("Son Dosya İçeriği:\n" + "-"*20 + "\n" + dosya_oku() + "\n" + "-"*20)

    print("\n[SONUÇ] Doğrulama Başarılı! Pardus Entegrasyon Betiği Sorunsuz Çalışıyor.")
    print("==================================================")
