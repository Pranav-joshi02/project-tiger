import os
import argparse
import time
import requests
import csv
from pathlib import Path
from PIL import Image
from io import BytesIO
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def download_image(url: str, save_path: Path, session: requests.Session) -> bool:
    try:
        response = session.get(url, timeout=10)
        response.raise_for_status()
        
        # Verify it's a valid image
        img = Image.open(BytesIO(response.content))
        img.verify()
        
        # Optionally check size, let's say minimum 100x100
        img = Image.open(BytesIO(response.content))
        if img.size[0] < 100 or img.size[1] < 100:
            logger.debug(f"Image too small: {img.size}")
            return False
            
        with open(save_path, 'wb') as f:
            f.write(response.content)
        return True
    except Exception as e:
        logger.debug(f"Failed to download {url}: {e}")
        return False

def fetch_inaturalist(species_name: str, count: int, output_dir: Path, session: requests.Session, dry_run: bool, metadata_csv: csv.writer):
    logger.info(f"Fetching {count} {species_name} from iNaturalist...")
    url = f"https://api.inaturalist.org/v1/observations?taxon_name={requests.utils.quote(species_name)}&photos=true&per_page=100&quality_grade=research"
    
    downloaded = 0
    page = 1
    
    while downloaded < count:
        try:
            page_url = f"{url}&page={page}"
            response = session.get(page_url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            results = data.get('results', [])
            if not results:
                break
                
            for obs in results:
                if downloaded >= count:
                    break
                
                for photo in obs.get('photos', []):
                    if downloaded >= count:
                        break
                    
                    img_url = photo.get('url', '').replace('square', 'medium')
                    if not img_url:
                        continue
                        
                    filename = f"inat_{obs['id']}_{photo['id']}.jpg"
                    save_path = output_dir / filename
                    
                    if save_path.exists():
                        logger.debug(f"Skipping existing file {filename}")
                        continue
                        
                    if dry_run:
                        logger.info(f"[Dry Run] Would download {img_url} to {save_path}")
                        downloaded += 1
                        metadata_csv.writerow([filename, img_url, 'iNaturalist', photo.get('license_code', 'unknown')])
                    else:
                        if download_image(img_url, save_path, session):
                            downloaded += 1
                            metadata_csv.writerow([filename, img_url, 'iNaturalist', photo.get('license_code', 'unknown')])
                            if downloaded % 10 == 0:
                                logger.info(f"Downloaded {downloaded}/{count} {species_name} images...")
                            time.sleep(0.5) # Rate limiting
            
            page += 1
        except Exception as e:
            logger.error(f"Error fetching from iNaturalist: {e}")
            break

def fetch_gbif(scientific_name: str, count: int, output_dir: Path, session: requests.Session, dry_run: bool, metadata_csv: csv.writer):
    logger.info(f"Fetching {count} {scientific_name} from GBIF...")
    url = f"https://api.gbif.org/v1/occurrence/search?scientificName={requests.utils.quote(scientific_name)}&mediaType=StillImage&limit=100"
    
    downloaded = 0
    offset = 0
    
    while downloaded < count:
        try:
            page_url = f"{url}&offset={offset}"
            response = session.get(page_url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            results = data.get('results', [])
            if not results:
                break
                
            for obs in results:
                if downloaded >= count:
                    break
                
                for media in obs.get('media', []):
                    if downloaded >= count:
                        break
                    
                    if media.get('type') != 'StillImage':
                        continue
                        
                    img_url = media.get('identifier', '')
                    if not img_url:
                        continue
                        
                    filename = f"gbif_{obs['key']}.jpg"
                    save_path = output_dir / filename
                    
                    if save_path.exists():
                        logger.debug(f"Skipping existing file {filename}")
                        continue
                        
                    if dry_run:
                        logger.info(f"[Dry Run] Would download {img_url} to {save_path}")
                        downloaded += 1
                        metadata_csv.writerow([filename, img_url, 'GBIF', media.get('license', 'unknown')])
                    else:
                        if download_image(img_url, save_path, session):
                            downloaded += 1
                            metadata_csv.writerow([filename, img_url, 'GBIF', media.get('license', 'unknown')])
                            if downloaded % 10 == 0:
                                logger.info(f"Downloaded {downloaded}/{count} {scientific_name} images...")
                            time.sleep(0.5) # Rate limiting
            
            offset += 100
        except Exception as e:
            logger.error(f"Error fetching from GBIF: {e}")
            break

def main():
    parser = argparse.ArgumentParser(description="Download training data for Project Tiger species.")
    parser.add_argument("--species", type=str, choices=['deer', 'bear', 'both'], default='both', help="Species to download")
    parser.add_argument("--count", type=int, default=100, help="Number of images per species")
    parser.add_argument("--output-dir", type=str, default="datasets/pench_species/images/raw", help="Output directory")
    parser.add_argument("--dry-run", action="store_true", help="Perform a dry run without downloading")
    
    args = parser.parse_args()
    
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    
    species_map = {
        'deer': ('Axis axis', 'spotted_deer'),
        'bear': ('Melursus ursinus', 'sloth_bear')
    }
    
    targets = []
    if args.species in ['deer', 'both']:
        targets.append(species_map['deer'])
    if args.species in ['bear', 'both']:
        targets.append(species_map['bear'])
        
    session = requests.Session()
    session.headers.update({'User-Agent': 'ProjectTigerDatasetBuilder/1.0'})
    
    for scientific_name, folder_name in targets:
        species_dir = out_dir / folder_name
        species_dir.mkdir(parents=True, exist_ok=True)
        
        metadata_path = species_dir / "metadata.csv"
        mode = 'a' if metadata_path.exists() else 'w'
        
        with open(metadata_path, mode, newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            if mode == 'w':
                writer.writerow(['filename', 'url', 'source', 'license'])
                
            # Split count between iNaturalist and GBIF
            half_count = args.count // 2
            
            fetch_inaturalist(scientific_name, half_count, species_dir, session, args.dry_run, writer)
            fetch_gbif(scientific_name, args.count - half_count, species_dir, session, args.dry_run, writer)
            
    logger.info("Dataset download completed.")

if __name__ == '__main__':
    main()
