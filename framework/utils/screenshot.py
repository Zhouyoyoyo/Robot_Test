import os
from datetime import datetime

def take_screenshot(driver, folder: str, prefix: str = "case") -> str:
    os.makedirs(folder, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    filename = f"{prefix}_{ts}_{os.getpid()}.png"
    path = os.path.join(folder, filename)
    driver.save_screenshot(path)
    return path
