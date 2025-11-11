import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from framework.framework import Framework
# Create framework for level0 without entering main loop
fw = Framework(levelnummer=0, auto_erzeuge_objekte=True, splash=False)
print('registered keys:', list(fw._tasten.keys()))
# Map keys to function names if bound
for k, fn in fw._tasten.items():
    print('key', k, '->', getattr(fn, '__name__', repr(fn)))
# inspect held
sp = fw.spielfeld
held = getattr(sp, 'held', None)
print('held object:', held, 'class=', held.__class__.__name__ if held else None)
if held:
    print('held has aktiviere_steuerung?', hasattr(held, 'aktiviere_steuerung'))
    try:
        print('held._student present?', hasattr(held, '_student'))
    except Exception:
        pass
# Quit pygame
import pygame
pygame.quit()
print('done')
