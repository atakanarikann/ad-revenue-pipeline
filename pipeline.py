import os
import sqlite3
from datetime import datetime

import pandas as pd


# --------------------------------------------------
# 1) Dosya yolları
# --------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATA_DIR = os.path.join(BASE_DIR, "data")
RAW_DIR = os.path.join(DATA_DIR, "raw")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")

IMPRESSION_PATH = os.path.join(RAW_DIR, "impressions.csv")
CLICKS_PATH = os.path.join(RAW_DIR, "clicks.csv")
REVENUE_PATH = os.path.join(RAW_DIR, "revenue.csv")

DB_PATH = os.path.join(BASE_DIR, "ads_analytics.db")


# --------------------------------------------------
# 2) Yardımcı fonksiyonlar
# --------------------------------------------------
def ensure_dirs():
    """Gerekli klasörleri oluştur."""
    os.makedirs(RAW_DIR, exist_ok=True)
    os.makedirs(REPORTS_DIR, exist_ok=True)


def load_data():
    """CSV dosyalarını Pandas DataFrame olarak yükle."""
    impressions = pd.read_csv(IMPRESSION_PATH)
    clicks = pd.read_csv(CLICKS_PATH)
    revenue = pd.read_csv(REVENUE_PATH)

    # Tarih kolonlarını date tipine çevir
    for df in (impressions, clicks, revenue):
        df["date"] = pd.to_datetime(df["date"])

    return impressions, clicks, revenue


def clean_and_join(impressions, clicks, revenue):
    """Veriyi temizle, join et ve metrikleri hesapla."""
    # Impressions + clicks join (date, campaign, country, device bazında)
    metrics = pd.merge(
        impressions,
        clicks,
        on=["date", "campaign_id", "country", "device"],
        how="left"
    )

    # Boş click değerlerini 0 yapalım
    metrics["clicks"] = metrics["clicks"].fillna(0)

    # CTR = clicks / impressions
    metrics["ctr"] = metrics["clicks"] / metrics["impressions"]

    # Revenue'i date + campaign bazında join edelim
    revenue_daily = revenue.groupby(
        ["date", "campaign_id", "currency"], as_index=False
    )["revenue"].sum()

    # Currency conversion (örnek kur değerleri – istersen gerçek kur da bağlarız)
    fx_rates = {
        "CAD": 1.0,   # base
        "USD": 1.35,  # örnek: 1 USD = 1.35 CAD
        "EUR": 1.45
    }

    revenue_daily["revenue_cad"] = revenue_daily.apply(
        lambda row: row["revenue"] * fx_rates.get(row["currency"], 1.0),
        axis=1
    )

    # campaign + date bazında toplu revenue
    revenue_agg = revenue_daily.groupby(
        ["date", "campaign_id"], as_index=False
    )["revenue_cad"].sum()

    # metrics ile revenue'u join edelim
    metrics = pd.merge(
        metrics,
        revenue_agg,
        on=["date", "campaign_id"],
        how="left"
    )

    metrics["revenue_cad"] = metrics["revenue_cad"].fillna(0)

    # RPM (revenue per 1000 impressions)
    metrics["rpm"] = metrics["revenue_cad"] / metrics["impressions"] * 1000

    return metrics


def aggregate_daily(metrics):
    """Günlük + kampanya bazında agregasyon."""
    daily = metrics.groupby(
        ["date", "campaign_id", "country"],
        as_index=False
    ).agg(
        impressions=("impressions", "sum"),
        clicks=("clicks", "sum"),
        revenue_cad=("revenue_cad", "sum")
    )

    daily["ctr"] = daily["clicks"] / daily["impressions"]
    daily["rpm"] = daily["revenue_cad"] / daily["impressions"] * 1000

    return daily


def save_to_sqlite(daily_df):
    """Sonuçları SQLite veritabanına yaz."""
    conn = sqlite3.connect(DB_PATH)
    try:
        daily_df.to_sql("daily_campaign_metrics", conn, if_exists="replace", index=False)
    finally:
        conn.close()


def save_report_csv(daily_df):
    """Reports klasörüne timestamp’li CSV kaydet."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = os.path.join(REPORTS_DIR, f"daily_campaign_metrics_{ts}.csv")
    daily_df.to_csv(out_path, index=False)
    print(f"Rapor oluşturuldu: {out_path}")


def run_pipeline():
    print("🔹 Klasörler kontrol ediliyor...")
    ensure_dirs()

    print("🔹 Veriler yükleniyor...")
    impressions, clicks, revenue = load_data()

    print("🔹 Veriler temizlenip birleştiriliyor...")
    metrics = clean_and_join(impressions, clicks, revenue)

    print("🔹 Günlük metrikler hesaplanıyor...")
    daily = aggregate_daily(metrics)

    print("🔹 SQLite veritabanına yazılıyor...")
    save_to_sqlite(daily)

    print("🔹 CSV rapor oluşturuluyor...")
    save_report_csv(daily)

    print("✅ Pipeline tamamlandı.")


if __name__ == "__main__":
    run_pipeline()
