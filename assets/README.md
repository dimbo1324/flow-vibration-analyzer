# Assets

This directory contains static assets required for building and packaging IVA.

## iva_icon.ico

Application icon used by:
- PyInstaller when building `IVA.exe`
- Inno Setup when creating `IVA_Setup_1.0.0.exe`
- Windows taskbar and shortcut icons

The current `iva_icon.ico` is a minimal placeholder. Replace it with a
professionally designed icon (32x32, 48x48, 64x64, 256x256 multi-resolution ICO)
before the public release.

To regenerate the placeholder:
```
python -c "
from PIL import Image, ImageDraw
img = Image.new('RGBA', (32, 32), (26, 32, 44, 255))
draw = ImageDraw.Draw(img)
draw.rectangle([2,2,29,29], outline=(0, 191, 255, 255), width=1)
draw.text((10, 8), 'IV', fill=(0, 191, 255, 255))
draw.text((10, 18), 'A', fill=(0, 191, 255, 255))
img.save('assets/iva_icon.ico', format='ICO', sizes=[(32, 32)])
"
```
