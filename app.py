import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta

st.set_page_config(page_title="BIST YZ Terminali", layout="wide")
st.title("BIST Otomatik Tarama ve Sinyal Terminali")

# Sayfayı iki sekmeye ayırıyoruz
tab1, tab2 = st.tabs(["🎯 Tekil Hisse Sinyal Analizi", "🤖 Bilanço & Teknik Tarama Motoru"])

# Sayı formatlayıcı
def format_tl(value):
    if value is None or pd.isna(value): return "Veri Yok"
    if value >= 1e9: return f"{value / 1e9:.2f} Milyar TL"
    if value >= 1e6: return f"{value / 1e6:.2f} Milyon TL"
    return f"{value:,.2f} TL"

# ----------------- TAB 1: TEKİL HİSSE ANALİZİ -----------------
with tab1:
    st.subheader("Gelişmiş İndikatör Kombinasyonları")
    symbol = st.text_input("BIST Hisse Kodu (Örn: FROTO):", "FROTO").upper()
    ticker_symbol = f"{symbol}.IS"

    if st.button("Hisse Sinyallerini Getir"):
        with st.spinner("Matematiksel formüller ve indikatörler hesaplanıyor..."):
            stock = yf.Ticker(ticker_symbol)
            df = stock.history(period="1y")
            
            if not df.empty:
                current_price = df['Close'].iloc[-1]
                
                # 1. RSI
                df['RSI'] = ta.rsi(df['Close'], length=14)
                rsi = df['RSI'].iloc[-1]
                rsi_sig = "AL 🟢" if rsi < 35 else ("SAT 🔴" if rsi > 65 else "NÖTR ⚪")
                
                # 2. MACD
                macd = ta.macd(df['Close'])
                df['MACD'] = macd['MACD_12_26_9']
                df['MACD_Signal'] = macd['MACDs_12_26_9']
                macd_val = df['MACD'].iloc[-1]
                macd_sig = "AL 🟢" if macd_val > df['MACD_Signal'].iloc[-1] else "SAT 🔴"
                
                # 3. EMA (Üstel Hareketli Ortalama - 20)
                df['EMA_20'] = ta.ema(df['Close'], length=20)
                ema = df['EMA_20'].iloc[-1]
                ema_sig = "AL 🟢" if current_price > ema else "SAT 🔴"
                
                # 4. SMA (Basit Hareketli Ortalama - 50)
                df['SMA_50'] = ta.sma(df['Close'], length=50)
                sma = df['SMA_50'].iloc[-1]
                sma_sig = "AL 🟢" if current_price > sma else "SAT 🔴"
                
                # 5. WILLIAMS ALLIGATOR (Çene, Dişler, Dudaklar)
                # Formül: 13, 8 ve 5 periyotluk düzeltilmiş hareketli ortalamaların geleceğe kaydırılması
                df['Jaw'] = df['Close'].rolling(13).mean().shift(8)
                df['Teeth'] = df['Close'].rolling(8).mean().shift(5)
                df['Lips'] = df['Close'].rolling(5).mean().shift(3)
                
                jaw = df['Jaw'].iloc[-1]
                teeth = df['Teeth'].iloc[-1]
                lips = df['Lips'].iloc[-1]
                
                if lips > teeth and teeth > jaw:
                    gator_sig = "AL 🟢 (Timsah Uyanık/Yukarı)"
                elif jaw > teeth and teeth > lips:
                    gator_sig = "SAT 🔴 (Timsah Uyanık/Aşağı)"
                else:
                    gator_sig = "NÖTR ⚪ (Timsah Uyuyor)"

                # Sonuçları Göster
                st.write(f"### {symbol} - Güncel Fiyat: {current_price:.2f} TL")
                
                col1, col2, col3, col4, col5 = st.columns(5)
                col1.metric("1. RSI (14)", f"{rsi:.1f}", rsi_sig)
                col2.metric("2. MACD", f"{macd_val:.2f}", macd_sig)
                col3.metric("3. EMA (20)", f"{ema:.2f}", ema_sig)
                col4.metric("4. SMA (50)", f"{sma:.2f}", sma_sig)
                col5.metric("5. Williams Gator", "Timsah Durumu", gator_sig)
                
            else:
                st.error("Veri bulunamadı.")

# ----------------- TAB 2: OTOMATİK BİLANÇO VE SİNYAL TARAMASI -----------------
with tab2:
    st.subheader("Bilanço Filtresi & Sinyal Tarayıcı (BIST 30 Örneklem)")
    st.write("Bu modül, arka planda şirketlerin F/K oranı ve karlılık durumlarına (Bilançosuna) bakar. Sadece temel analizi güçlü olanları filtreler ve hedef fiyat ile teknik sinyallerini hesaplar.")
    
    if st.button("Taramayı Başlat"):
        # Hız için BIST'in sağlam şirketlerinden oluşan bir örneklem. 
        # (Gerçek kullanımda buraya tüm BIST kodları bir liste olarak eklenebilir)
        bist_listesi = ["THYAO", "TUPRS", "KCHOL", "SAHOL", "ASELS", "FROTO", "BIMAS", "EREGL", "AKBNK", "ISCTR"]
        
        filtreli_hisseler = []
        
        progress_bar = st.progress(0)
        
        for i, h_symbol in enumerate(bist_listesi):
            stock = yf.Ticker(f"{h_symbol}.IS")
            info = stock.info
            df = stock.history(period="1y")
            
            progress_bar.progress((i + 1) / len(bist_listesi))
            
            # TEMEL ANALİZ FİLTRELERİ (Bilanço Kontrolü)
            fk = info.get("trailingPE", 0)
            ozsermaye_karliligi = info.get("returnOnEquity", 0)
            
            # Kural: F/K'sı 0'dan büyük ve 15'ten küçük olanlar, Özsermaye karlılığı %15'ten büyük olanlar "İyi Bilanço" sayılır.
            if 0 < fk < 15 and (ozsermaye_karliligi is not None and ozsermaye_karliligi > 0.15):
                
                # Hedef Fiyat Hesaplama
                current_price = df['Close'].iloc[-1]
                hbk = current_price / fk
                ortalama_fiyat = df['Close'].mean()
                gecmis_fk_ortalama = ortalama_fiyat / hbk
                hedef_fiyat = hbk * (gecmis_fk_ortalama * 1.1)
                
                # Teknik Sinyal (MACD ve EMA 20 bazlı basit karar)
                df['EMA_20'] = ta.ema(df['Close'], length=20)
                macd = ta.macd(df['Close'])
                df['MACD'] = macd['MACD_12_26_9']
                df['MACD_Signal'] = macd['MACDs_12_26_9']
                
                if current_price > df['EMA_20'].iloc[-1] and df['MACD'].iloc[-1] > df['MACD_Signal'].iloc[-1]:
                    sinyal = "AL 🟢"
                else:
                    sinyal = "SAT / BEKLE 🔴"
                
                filtreli_hisseler.append({
                    "Hisse": h_symbol,
                    "Fiyat (TL)": round(current_price, 2),
                    "F/K Oranı": round(fk, 2),
                    "Özsermaye Karlılığı (%)": round(ozsermaye_karliligi * 100, 2),
                    "Tahmini Hedef Fiyat": round(hedef_fiyat, 2),
                    "Teknik Sinyal": sinyal
                })
        
        # Sonuçları Tablo Olarak Yazdır
        if filtreli_hisseler:
            st.success("Tarama Tamamlandı! Bilançosu sağlam ve kriterlere uyan şirketler aşağıdadır:")
            st.dataframe(pd.DataFrame(filtreli_hisseler), use_container_width=True)
        else:
            st.warning("Mevcut kriterlere uyan hisse bulunamadı.")
