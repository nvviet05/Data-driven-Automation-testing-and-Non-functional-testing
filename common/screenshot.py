import os
import time


def save_screenshot(driver, output_dir: str, name_prefix: str) -> str:
    os.makedirs(output_dir, exist_ok=True)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename = f"{name_prefix}_{timestamp}.png"
    path = os.path.join(output_dir, filename)
    driver.save_screenshot(path)
    return path
