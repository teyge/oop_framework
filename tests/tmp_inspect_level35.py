from framework.spielfeld import Spielfeld

sp = Spielfeld('level/level35.json', None, auto_erzeuge_objekte=True)
print('Level:', sp.level.breite, 'x', sp.level.hoehe)
for y in range(sp.level.hoehe):
    row = ''
    for x in range(sp.level.breite):
        t = sp.level.tiles[y][x]
        row += t
    print(row)

# inspect some sample positions (where hero spawns?)
print('\nObjects at positions:')
for o in sp.objekte:
    try:
        print(type(o), getattr(o,'typ',None), getattr(o,'name',None), (getattr(o,'x',None), getattr(o,'y',None)))
    except Exception:
        pass

# test kann_betreten for all tiles
print('\nKann betreten map (True=can enter):')
for y in range(sp.level.hoehe):
    row = ''
    for x in range(sp.level.breite):
        # use a dummy obj e.g. None; function expects obj and coords
        ok = sp.kann_betreten(None, x, y)
        row += '1' if ok else '0'
    print(row)

# find hero location if any
h = sp.held
print('\nHeld:', h, getattr(h,'x',None), getattr(h,'y',None))

print('\nSample around hero:')
if h:
    for dy in (-1,0,1):
        for dx in (-1,0,1):
            tx, ty = h.x+dx, h.y+dy
            if 0 <= tx < sp.level.breite and 0 <= ty < sp.level.hoehe:
                print((tx,ty), sp.level.tiles[ty][tx], 'obj@', sp.gib_objekt_bei(tx,ty), 'passierbar?', sp.kann_betreten(h, tx, ty))

print('\nDone')
