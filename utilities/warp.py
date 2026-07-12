#!/usr/bin/env python3
"""
warp.py — Quick save-file level warp + flag editor for Iconoclasts.

Usage:
    python3 warp.py list                          # list all areas and rooms
    python3 warp.py warp <area> [<room>]          # teleport (default room: 1+)
    python3 warp.py warp <area> [<room>] --save N # target save slot (1/2/3, default: active)
    python3 warp.py flag <key> <value>            # set a save-file flag
    python3 warp.py flag relaxed 1                # enable Relaxed Mode (no damage)
    python3 warp.py flag forcenight 1             # force night-time graphics
    python3 warp.py flag difficulty 1             # harder mode
    python3 warp.py show                          # show current location + key flags

Areas: blocky city concern concernb descent desert house isi midway mountain strait tower wood
"""

import os, struct, shutil, sys, argparse

SAVE_ROOT = os.path.expanduser('~/.local/share/Steam/steamapps/common/Iconoclasts/data')
LVL_ROOT  = os.path.join(SAVE_ROOT, 'lvl')

# Approximate world-grid centre for each area (for mapx/mapy).
# Derived from observed save data and minimap coordinates.
AREA_CENTER = {
    'house':    (57, 36),
    'strait':   (60, 30),
    'isi':      (46, 24),
    'blocky':   (59, 36),
    'city':     (53, 26),
    'concern':  (57, 50),
    'concernb': (51, 52),
    'descent':  (40, 53),
    'desert':   (52, 49),
    'midway':   (45, 50),
    'mountain': (47, 46),
    'tower':    (51, 48),
    'wood':     (36, 50),
}

KNOWN_EXACT = {
    ('house',  '1+'): (57, 36),
    ('isi',    '4+'): (43, 21),
    ('isi',   '22+'): (50, 27),
    ('strait', '2+'): (59, 30),
}

FLAG_HELP = {
    'relaxed':    'Relaxed Mode — player takes no damage (0=off, 1=on)',
    'difficulty': 'Difficulty (0=normal, 1=hard)',
    'forcenight': 'Force night-time visuals (0=off, 1=on)',
    'night':      'Night flag (set by game; editing may affect lighting)',
    'consistentchallenge': 'Consistent challenge mode (0=off, 1=on)',
}


# ── MAP1.0 parser/serialiser ──────────────────────────────────────────────────

def parse_map10(data: bytes):
    if data[:6] != b'MAP1.0':
        raise ValueError(f'Not a MAP1.0 file (magic={data[:6]!r})')
    pos = 6
    count = struct.unpack_from('<I', data, pos)[0]; pos += 4
    entries = []
    for _ in range(count):
        klen = struct.unpack_from('<I', data, pos)[0]; pos += 4
        key  = data[pos:pos+klen].rstrip(b'\x00').decode('latin-1'); pos += klen
        vtype = struct.unpack_from('<I', data, pos)[0]; pos += 4
        if vtype == 1:
            val = struct.unpack_from('<d', data, pos)[0]; pos += 8
        elif vtype == 2:
            slen = struct.unpack_from('<I', data, pos)[0]; pos += 4
            val  = data[pos:pos+slen].rstrip(b'\x00').decode('latin-1'); pos += slen
        else:
            raise ValueError(f'Unknown vtype {vtype} for key {key!r}')
        entries.append([key, vtype, val])
    return entries


def serialise_map10(entries) -> bytes:
    out = bytearray(b'MAP1.0')
    out += struct.pack('<I', len(entries))
    for key, vtype, val in entries:
        key_b = (key + '\x00').encode('latin-1')
        out += struct.pack('<I', len(key_b))
        out += key_b
        out += struct.pack('<I', vtype)
        if vtype == 1:
            out += struct.pack('<d', float(val))
        elif vtype == 2:
            val_b = (str(val) + '\x00').encode('latin-1')
            out += struct.pack('<I', len(val_b))
            out += val_b
    return bytes(out)


# ── Helpers ───────────────────────────────────────────────────────────────────

def get_save_path(slot: int) -> str:
    name = 'point' if slot == 0 else f'save{slot}'
    return os.path.join(SAVE_ROOT, name)


def load_save(path: str):
    with open(path, 'rb') as f:
        return parse_map10(f.read())


def write_save(path: str, entries):
    bak = path + '.warp.bak'
    if not os.path.exists(bak):
        shutil.copy2(path, bak)
        print(f'  Backup: {bak}')
    data = serialise_map10(entries)
    with open(path, 'wb') as f:
        f.write(data)


def get_entry(entries, key):
    for e in entries:
        if e[0] == key:
            return e
    return None


def set_entry(entries, key, vtype, val):
    for e in entries:
        if e[0] == key:
            e[1] = vtype
            e[2] = val
            return
    entries.append([key, vtype, val])


def active_slot() -> int:
    """Return the last-used save slot (1/2/3), or 1 as default."""
    try:
        entries = load_save(get_save_path(0))
        e = get_entry(entries, 'lastsaveslot')
        if e:
            return max(1, min(3, int(float(e[2]))))
    except Exception:
        pass
    return 1


def list_rooms(area: str):
    d = os.path.join(LVL_ROOT, area)
    if not os.path.isdir(d):
        return []
    rooms = [f.replace('.lvl', '') for f in os.listdir(d) if f.endswith('.lvl')]
    rooms.sort(key=lambda x: (len(x), x))
    return rooms


def all_areas():
    if not os.path.isdir(LVL_ROOT):
        return []
    return sorted(d for d in os.listdir(LVL_ROOT) if os.path.isdir(os.path.join(LVL_ROOT, d)))


# ── Commands ──────────────────────────────────────────────────────────────────

def cmd_list(_args):
    print('Available areas and rooms:')
    for area in all_areas():
        rooms = list_rooms(area)
        preview = ', '.join(rooms[:10])
        if len(rooms) > 10:
            preview += f', … ({len(rooms)} total)'
        print(f'  {area:<15} {preview}')


def cmd_show(_args):
    slot = active_slot()
    path = get_save_path(slot)
    print(f'Save slot: {slot}  ({path})')
    if not os.path.exists(path):
        print('  (file not found)')
        return
    entries = load_save(path)
    loc_keys = ('folder','file','mapx','mapy','position','facing','time')
    flag_keys = ('relaxed','difficulty','forcenight','night',
                 'consistentchallenge','consistentchallenge2','deaths','all_schematics')
    print('Location:')
    for k in loc_keys:
        e = get_entry(entries, k)
        if e:
            v = int(float(e[2])) if e[1]==1 and float(e[2])==int(float(e[2])) else e[2]
            print(f'  {k:<20} = {v}')
    print('Flags:')
    for k in flag_keys:
        e = get_entry(entries, k)
        if e:
            v = int(float(e[2])) if e[1]==1 and float(e[2])==int(float(e[2])) else e[2]
            desc = FLAG_HELP.get(k, '')
            print(f'  {k:<20} = {v:<8}  {desc}')


def cmd_warp(args):
    area = args.area.lower()
    room = args.room or '1+'

    # Validate area
    if area not in all_areas():
        print(f'Unknown area: {area!r}')
        print(f'Valid areas: {", ".join(all_areas())}')
        sys.exit(1)

    # Validate room
    rooms = list_rooms(area)
    if room not in rooms:
        print(f'Room {room!r} not found in {area}.')
        print(f'Available: {", ".join(rooms[:20])}{"…" if len(rooms)>20 else ""}')
        sys.exit(1)

    # Determine save file
    slot = args.save if args.save else active_slot()
    path = get_save_path(slot)
    if not os.path.exists(path):
        print(f'Save file not found: {path}')
        sys.exit(1)

    entries = load_save(path)

    # Compute mapx/mapy
    exact = KNOWN_EXACT.get((area, room))
    if exact:
        mx, my = exact
        coord_note = 'exact'
    else:
        mx, my = AREA_CENTER.get(area, (50, 30))
        coord_note = 'approximate'

    # Map path — use backslash (matches game's stored format)
    mapload = f'./data\\lvl\\{area}\\map.file'

    print(f'Warping save{slot} → {area}/{room}  (mapx={mx}, mapy={my} {coord_note})')
    print(f'  folder:   {area}')
    print(f'  file:     {room}')
    print(f'  mapload:  {mapload}')
    print(f'  position: 512,512')

    set_entry(entries, 'folder',   2, area)
    set_entry(entries, 'file',     2, room)
    set_entry(entries, 'mapload',  2, mapload)
    set_entry(entries, 'position', 2, '512,512')
    set_entry(entries, 'mapx',     1, float(mx))
    set_entry(entries, 'mapy',     1, float(my))
    set_entry(entries, 'facing',   1, 1.0)

    write_save(path, entries)
    print('Done. Load the save in-game to teleport.')


def cmd_flag(args):
    slot = active_slot()
    path = get_save_path(slot)
    if not os.path.exists(path):
        print(f'Save file not found: {path}')
        sys.exit(1)

    entries = load_save(path)
    key = args.key
    val_str = args.value

    # Try to detect type from existing entry, or infer from value
    e = get_entry(entries, key)
    if e:
        vtype = e[1]
    else:
        # Try float first
        try:
            float(val_str)
            vtype = 1
        except ValueError:
            vtype = 2

    if vtype == 1:
        val = float(val_str)
    else:
        val = val_str

    old_val = e[2] if e else '(not set)'
    set_entry(entries, key, vtype, val)
    write_save(path, entries)

    desc = FLAG_HELP.get(key, '')
    print(f'save{slot}: {key} = {old_val!r} → {val!r}  {desc}')


# ── Argument parsing ──────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(
        description='Iconoclasts save-file warp and flag editor',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__.split('Areas:')[0],
    )
    sub = ap.add_subparsers(dest='cmd')

    sub.add_parser('list', help='List all areas and rooms')
    sub.add_parser('show', help='Show current location and key flags')

    wp = sub.add_parser('warp', help='Teleport to an area/room')
    wp.add_argument('area', help='Target area (e.g. house, city, mountain)')
    wp.add_argument('room', nargs='?', default=None, help='Target room (default: 1+)')
    wp.add_argument('--save', type=int, choices=[1,2,3], default=None,
                    help='Save slot to edit (default: last used)')

    fl = sub.add_parser('flag', help='Set a save-file flag')
    fl.add_argument('key',   help='Flag name (e.g. relaxed, forcenight, difficulty)')
    fl.add_argument('value', help='New value')
    fl.add_argument('--save', type=int, choices=[1,2,3], default=None)

    args = ap.parse_args()
    if args.cmd == 'list':   cmd_list(args)
    elif args.cmd == 'show': cmd_show(args)
    elif args.cmd == 'warp': cmd_warp(args)
    elif args.cmd == 'flag': cmd_flag(args)
    else:
        ap.print_help()


if __name__ == '__main__':
    main()
