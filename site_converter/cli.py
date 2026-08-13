import sys
import asyncio
import argparse
import logging

from .parser import SiteParser

# CLI için temiz ve profesyonel bir log formatı
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

async def run_async(url: str, output_dir: str):
    # Asenkron motoru başlat
    parser = SiteParser(output_dir=output_dir)
    await parser.process_site(url)

def main():
    parser = argparse.ArgumentParser(
        description="Site Converter — Make Any Website Work Offline",
        epilog="Created by İbrahim Emir Akman | github.com/iemirakman"
    )
    
    # Zorunlu URL argümanı
    parser.add_argument(
        "url", 
        help="Çevrimdışı kaydedilecek web sitesinin tam adresi (örn: https://example.com)"
    )
    
    # Opsiyonel çıkış klasörü parametresi (-o veya --output)
    parser.add_argument(
        "-o", "--output", 
        default="offline_site", 
        help="Dosyaların kaydedileceği klasör (varsayılan: offline_site)"
    )
    
    args = parser.parse_args()

    # Basit güvenlik kontrolü
    if not args.url.startswith("http"):
        logger.error("[HATA] URL 'http://' veya 'https://' ile başlamalıdır.")
        sys.exit(1)

    logger.info(f"🚀 Başlatılıyor: {args.url}")
    logger.info(f"📂 Hedef Klasör: {args.output}\n" + "-"*40)
    
    try:
        # Asenkron döngüyü CLI'dan güvenle tetikle
        asyncio.run(run_async(args.url, args.output))
    except KeyboardInterrupt:
        logger.warning("\n[!] İşlem kullanıcı tarafından iptal edildi.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n[!] Beklenmeyen kritik bir hata oluştu: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()