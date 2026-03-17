import urllib.request
import urllib.error
from pathlib import Path
from .logging import status_message

def fetch_minecraft_asset(relative_path: str, extract_root: Path, version: str = "1.21.11") -> Path:
    target_path = extract_root / relative_path
    if target_path.exists():
        return target_path
    
    if not relative_path.startswith("assets/minecraft"):
        return target_path # we only download minecraft assets
        
    url = f"https://raw.githubusercontent.com/InventivetalentDev/minecraft-assets/{version}/{relative_path}"
    
    try:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(url, target_path)
        status_message("process", f"Downloaded missing asset: {relative_path}")
    except Exception as e:
        status_message("info", f"Could not download missing asset {relative_path}: {e}")
        if target_path.exists():
            target_path.unlink()
    
    return target_path
