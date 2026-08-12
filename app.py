import streamlit as st
import pandas as pd
import plotly.express as px
from sklearn.ensemble import RandomForestRegressor

st.set_page_config(page_title="Steam Oyun Analiz Panosu", page_icon="🎮", layout="wide")

st.title("🎮 Steam Oyun Veri Analiz Panosu")
st.write("Bu panel üzerinden Steam oyunlarının fiyat, indirim ve başarı tahmin analizlerini inceleyebilirsiniz.")

@st.cache_data
def load_data():
    df = pd.read_csv("steam_top_1495_games.csv") 
    return df

try:
    df = load_data()
    
    # 1. Metrik Kartları (Üst Bilgi Paneli)
    st.subheader("📊 Genel İstatistikler")
    col1, col2, col3 = st.columns(3)
    
    col1.metric("Toplam Oyun Sayısı", len(df))
    col2.metric("Ücretsiz Oyun Sayısı", int(df['is_free'].sum()))
    col3.metric("Ortalama Fiyat ($)", f"${df['price_usd'].mean():.2f}")

    st.markdown("---")

    # 2. Sol Menü Filtreleri
    st.sidebar.header("🔍 Filtreler")
    
    max_price = float(df['price_usd'].max())
    selected_price = st.sidebar.slider("Maksimum Fiyat ($)", 0.0, max_price, max_price)
    show_free_only = st.sidebar.checkbox("Sadece Ücretsiz Oyunları Göster")
    
    filtered_df = df[df['price_usd'] <= selected_price]
    if show_free_only:
        filtered_df = filtered_df[filtered_df['is_free'] == True]

    # 3. İki Sütunlu Grafik Alanı
    left_col, right_col = st.columns(2)

    with left_col:
        st.subheader("💰 En Pahalı 10 Oyun")
        top_expensive = filtered_df.nlargest(10, 'price_usd')
        fig_price = px.bar(
            top_expensive, 
            x='price_usd', 
            y='name', 
            orientation='h',
            labels={'price_usd': 'Fiyat ($)', 'name': 'Oyun Adı'},
            color='price_usd',
            color_continuous_scale='Viridis'
        )
        fig_price.update_layout(yaxis={'categoryorder': 'total ascending'})
        st.plotly_chart(fig_price, use_container_width=True)

    with right_col:
        st.subheader("🔥 En Yüksek İndirim Oranları (%)")
        top_discount = filtered_df.nlargest(10, 'discount_pct')
        fig_discount = px.bar(
            top_discount, 
            x='name', 
            y='discount_pct',
            labels={'discount_pct': 'İndirim (%)', 'name': 'Oyun Adı'},
            color='discount_pct',
            color_continuous_scale='Reds'
        )
        st.plotly_chart(fig_discount, use_container_width=True)

    # 4. Veri Tablosu
    st.markdown("---")
    st.subheader("📋 Filtrelenmiş Oyun Listesi")
    st.dataframe(filtered_df[['name', 'price_usd', 'discount_pct', 'is_free', 'release_date']], use_container_width=True)

    # 5. Oyun Arama Bölümü
    st.markdown("---")
    st.subheader("🎯 Oyun Arama & İndirim Yakalayıcı")
    search_query = st.text_input("Merak ettiğiniz bir oyunun adını yazın:", "")
    if search_query:
        results = df[df['name'].str.contains(search_query, case=False, na=False)]
        if not results.empty:
            st.write(f"**'{search_query}'** araması için {len(results)} sonuç bulundu:")
            st.dataframe(results[['name', 'price_usd', 'discount_pct', 'release_date']], use_container_width=True)
        else:
            st.warning("Aradığınız kriterlere uygun oyun bulunamadı.")

    # 6. Yapay Zeka ile Başarı Tahmini
    st.markdown("---")
    st.subheader("🤖 Yapay Zeka ile Oyun Başarısı / Oyuncu Etkileşimi Tahmini")
    st.write("Yayınlamayı planladığınız oyunun parametrelerini girerek tahmini inceleme/oyuncu etkileşim sayısını öngörün.")

    # Kullanıcı Girdileri
    p_col1, p_col2, p_col3 = st.columns(3)
    input_price = p_col1.number_input("Planlanan Fiyat ($):", min_value=0.0, max_value=200.0, value=19.99)
    input_discount = p_col2.slider("Planlanan İndirim Oranı (%):", 0, 90, 0)
    input_is_free = p_col3.selectbox("Oyun Ücretsiz mi olmalı?", [False, True])

    # Hedef Sütun Tespiti ve Model Eğitimi
    target_col = None
    for col in df.columns:
        if 'review' in col.lower() and pd.api.types.is_numeric_dtype(df[col]):
            target_col = col
            break

    if target_col:
        X = df[['price_usd', 'discount_pct', 'is_free']].copy()
        y = df[target_col]
        
        model = RandomForestRegressor(n_estimators=100, random_state=42)
        model.fit(X, y)

        if st.button("🔮 Oyuncu Etkileşimini Tahmin Et"):
            input_data = pd.DataFrame({
                'price_usd': [input_price],
                'discount_pct': [input_discount],
                'is_free': [input_is_free]
            })
            prediction = model.predict(input_data)[0]
            st.success(f"🎉 Tahmini Oyuncu İnceleme/Etkileşim Sayısı: **{int(prediction):,}**")
            st.info("💡 Not: Bu tahmin, Random Forest algoritması kullanılarak geçmiş Steam verileri üzerindeki eğilimlere göre hesaplanmıştır.")
    else:
        st.warning("⚠️ Verisetinde inceleme/oyuncu sayısını temsil eden sayısal bir sütun otomatik tespit edilemedi.")

except Exception as e:
    st.error(f"Hata oluştu: {e}")
