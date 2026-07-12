#pragma description "Iconoclasts MAP1.0 save/state file (point, save1, save2, save3)"
#pragma array_limit 0

// ═══════════════════════════════════════════════════════════════════════════
// File format: MAP1.0 key-value store
//
// Used for: point (live game state), save1/save2/save3 (save slots)
// Path: ~/.local/share/Steam/steamapps/common/Iconoclasts/data/
//
// Layout:
//   char[6]  magic        "MAP1.0"
//   u32      entry_count  number of entries (little-endian)
//   Entry[entry_count]    variable-length entries (see below)
//
// Entry layout:
//   u32  key_len     byte length of key including null terminator
//   char key[key_len]  null-terminated ASCII key string
//   u32  value_type  1 = double (f64), 2 = string
//   if value_type == 1:
//     double value   8-byte little-endian IEEE 754 float
//   if value_type == 2:
//     u32  string_len  byte length including null terminator
//     char value[string_len]  null-terminated ASCII string
//
// ─── Key naming conventions ────────────────────────────────────────────────
//
//   '-event_name'          Completed story event flag; value = progress/stage
//                          e.g. '-elrohome' = 1.0, '-splitup' = 2.0
//   'folder'               Current level folder (string), e.g. "house"
//   'file'                 Current level file (string), e.g. "1+"
//   'position'             Player position as "x,y" string
//   'status'               "hp,max_hp,level?,0,xp?,0,checkpoint_id"
//   'areacheck'            Running story checkpoint ID (matches status field 7)
//   'wrenchplus'           Wrench upgrade tier: 1.0, 2.0, or 3.0
//   'gotawrench'           Set once wrench first obtained (1.0)
//   'warps'                Comma-separated warp unlock flags (10 entries)
//   'folder_loot'          Total loot count collected in that area
//   'folder_map'           Explored map tiles as "x+y+flag,...," string
//   'tweak_own_N'          Tweak ownership data (double, usually 0 or level tier)
//   'tweak_equip_N'        Tweak equipped state (double, usually 0 or tier value)
//   'tweak_sales_N'        Shop row state: "tier,item_id_a,item_id_b,qty_bought,equipped"
//   'globalobjectsz1'      Global interactive object state vector (50 slots × 10 fields
//                          each, backslash-separated within, comma-separated between)
//                          Fields per slot: id, 39, x_px, y_px, folder, file, map_x, map_y, 0, 0
//                          id=0 means unused slot.
//   'collection'           Collectibles tally per category (comma-separated ints)
//   'bullets'              Bullet counts per slot (comma-separated ints)
//   'stackslot1..3'        Contra slot item IDs (double)
//   'stackcharge'          Current Contra charge amount
//   'ability1..3'          Robin ability slots (string, item name or empty)
//   'boulders+area+N+'     List of boulder positions that have been blown up (pixel coords)
//   'chest+area+N+x+y'     Chest collected flag (double, 1.0 = collected)
//   'N+roadblock'          Roadblock cleared flag (double, 1.0 = cleared)
//   'tremors'              Tremor system counter (double)
//   'night'                Day/night flag (0.0 = day, 1.0 = night)
//   'bgm_1..4'             Background music channel state
//   'time'                 Playtime as "HH:MM.SS," string
//
// ═══════════════════════════════════════════════════════════════════════════


// ─── Entry types ───────────────────────────────────────────────────────────

struct DoubleEntry {
    double value;    // 8-byte IEEE 754 little-endian; represents a numeric game flag
};

struct StringEntry {
    u32    string_len;        // byte length including null terminator
    char   value[string_len]; // null-terminated value string
};

struct Entry {
    u32  key_len;           // byte length of key string including null terminator
    char key[key_len];      // null-terminated key name
    u32  value_type;        // 1 = double, 2 = string
    if (value_type == 1) {
        DoubleEntry dval;
    } else if (value_type == 2) {
        StringEntry sval;
    }
};


// ─── Top-level structure ───────────────────────────────────────────────────

struct MAP10File {
    char magic[6];       // "MAP1.0"
    u32  entry_count;    // number of key-value entries
    Entry entries[entry_count];
};

MAP10File save @ 0x00;
