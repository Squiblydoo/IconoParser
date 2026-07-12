#pragma description "Iconoclasts .lvl level file (ARR1.0 format)"
#pragma array_limit 0

// ═══════════════════════════════════════════════════════════════════════════
// File layout summary
//
// Two reference levels cross-analysed:
//   blocky/1+.lvl  – 53×35 tiles (848×560px), 1028 game objects, 1030 array items
//   strait/6+.lvl  – 54×35 tiles (864×560px),   12 game objects,   14 array items
//
// Offsets below are for blocky/1+.lvl.
//
// Offset 0x00   : 8-byte magic + u16 version
// Offset 0x0a   : Array 0  – Object parallax/sprite data (id=17, parallax≈4.50)
// Offset 0x406e : Array 1  – Object sprite width table
// Offset 0x80d2 : Array 2  – Object sprite height table
// Offset 0xc136 : Array 3  – Object X pixel positions + room width header
// Offset 0x1019a: Array 4  – Object Y pixel positions + room height header
// Offset 0x141fe: Array 5  – Background descriptor string + sprite slots
// Offset 0x18262: Array 6  – Empty (count=0)
// Offset 0x18266: Array 7  – World size descriptor (count=1)
// Offset 0x1827a: Array 8  – Empty (count=0)
// Offset 0x1827e: Array 9  – Row/layer descriptor table (count=100)
// Offset 0x188c2: World data section – PART A: sparse tile grid (16-byte fixed records)
//                                       PART B: game object columnar property stream
//                                               (variable-length, starts ~rec 1963)
//
// Array item count = game_object_count + 2  (header item[0] + footer item[-1])
// Each array: u32 count + count × 16-byte records.
// ═══════════════════════════════════════════════════════════════════════════


// ─── Record types ──────────────────────────────────────────────────────────

// Item[0] (header) of arrays 0–2.
// Exact semantics of arrays 0–2 not fully confirmed; likely per-object sprite
// atlas offsets and parallax scroll parameters.
//   field[3] as f32: parallax scroll factor (0.0 when unused).
//     Observed: 4.503 (far), 2.125 (mid), 1.75 (near) from float interpretation.
//   Arrays 0–2 items[1+] (BgSpriteRec): all field[1]=0, field[3]=0 in observed data.
struct ParallaxLayerDesc {
    u32 active;           // always 1
    u32 has_factor;       // 1 when parallax_factor is valid, 0 otherwise
    u32 pad;              // always 0
    float parallax_factor;  // scroll multiplier; higher = further away
};

// Item[0] (header) of arrays 3–4.
//
// Array 3 header: field[2] = room WIDTH in tiles
//   (blocky: 53 tiles = 848px, strait: 54 tiles = 864px)
// Array 4 header: field[2] = room HEIGHT in tiles
//   (both levels: 35 tiles = 560px)
//
// Multiply tile count × 16 to get pixel dimensions.
struct ObjectLayerDesc {
    u32 active;           // always 1
    u32 pad;              // always 0
    u32 room_dim_tiles;   // room width (arr3) or height (arr4) in tiles
    u32 pad2;             // always 0
};

// Per-object record used in items[1+] of arrays 0–4.
//
// ARRAYS 3 AND 4 (confirmed, cross-verified against strait/6+.lvl room layout):
//   Array 3 items[1+]: field[1]=active(0/1), field[2]=X pixel position
//   Array 4 items[1+]: field[1]=Y active flag(0/1), field[2]=Y pixel position (often 0)
//   Object count = array count − 2 (subtract header + footer)
//   Object index n → item index n+1
//
// ARRAYS 0–2 (partially confirmed):
//   field[1]=0, field[2]=unknown (atlas offset?), field[3]=0 in all observed data
//
// NOTE: H-flip/V-flip confirmed via GL trace; encoding location not yet resolved.
struct BgSpriteRec {
    u32 active;   // 1 = slot in use, 0 = empty
    u32 y_flag;   // arr3/arr4: 0=header/footer slot, 1=active object; arr0-2: always 0
    u32 x_pos;    // arr3: X pixel position of object; arr4: Y pixel position (often 0)
    u32 unk3;     // always 0 in all observed data
};


// ─── Array 5: background descriptor string ─────────────────────────────────
//
// Item[0] is a variable-length chunk header.  The string starts at byte 12
// of item[0] and continues sequentially across the following records.
//
// String format: comma-separated "id+x_scroll+tile_flag" entries, one per
// background layer (6 layers → 6 entries).
//   id:         background layer type ID (observed range 1–18+)
//   x_scroll:   initial horizontal scroll offset in pixels
//   tile_flag:  0 = scale texture to fill quad height
//               3 = tile texture vertically (ground/tree strips)
//
// Example (blocky/1+.lvl): "17+0+3,3+0+0,18+0+0,2+0+0,16+0+3,1+0+0,"
//   → layer ids 17,3,18,2,16,1 map to arrays 0,1,2,3,4,5 respectively.
//
// After the string the remaining slots (items ~4 to count-1) appear unused.
struct BgDescStringHeader {
    u32 type;                   // always 1
    u32 num_cont_recs;          // continuation records carrying string bytes (observed: 2)
    u32 string_length;          // byte length including null terminator
    char str_data[string_length]; // sequential read spanning record boundaries
    // Pad to the next 16-byte record boundary after the 12-byte header+string
    if ((12 + string_length) % 16 != 0)
        u8 align_pad[16 - ((12 + string_length) % 16)];
};

// After BgDescStringHeader the remaining items are sprite records (all zero).
// num_string_recs = ceil((12 + string_length) / 16); remaining = count - num_string_recs.


// ─── Array 7: world size descriptor ─────────────────────────────────────────
//
// Single record.  Observed: u32s = (0, 100, 0, 1).
// u32[1]=100 matches the count of array 9 (row descriptor count).
struct WorldSizeDesc {
    u32 pad;              // always 0
    u32 row_count;        // matches array 9 count (100 in blocky/1+.lvl)
    u32 pad2;             // always 0
    u32 always_one;       // always 1
};


// ─── Array 9: row/layer descriptor table ────────────────────────────────────
//
// count = 100 = row_count from array 7.
//
// item[0]: global world parameters
//   u32[0]=0, u32[1]=world_width (1030 in blocky), u32[2]=1, u32[3]=0
//   world_width matches the item count of each background layer array.
//
// item[1]: first active-row descriptor
//   u32[0]=N (varies per level; blocky=1, concernb/21+.lvl=14)
//   u32[1]=0, u32[2]=1, u32[3]=0
//   Exact semantics of u32[0] not yet confirmed; likely relates to which
//   row(s) hold tile data in the world section tile grid.
//
// items[2..count-1]: mostly (0xFFFFFF,0,1,0) or (0,0,1,0) = unused.
struct Array9HeaderRec {
    u32 pad;              // always 0
    u32 world_width;      // sprite slots per layer AND tile grid column count
    u32 always_one;       // always 1
    u32 pad2;             // always 0
};

struct Array9Rec {
    u32 field0;     // item[1]: row selector N; items[2+]: 0 or 0xFFFFFF
    u32 field1;     // usually 0
    u32 always_one; // always 1
    u32 field3;     // always 0
};


// ─── World section tile record ──────────────────────────────────────────────
//
// Immediately follows array 9 with NO leading count field.
// The world section has two distinct parts:
//
// PART A: Tile grid (16-byte fixed records)
//   Each record is one of four types identified by head (u32[0]):
//
//   (0xFFFFFF, 0, 1, 0)           → EMPTY: no tile at this grid slot
//   (0xC0C0C0, 0, 1, 0)           → SPECIAL: unknown marker; 1 per level
//   (0xFFFFFF, 0, world_width, 1) → ROW HEADER: marks start of a tile row;
//                                   followed by world_width-1 tile records
//   (0x000000, tile_type, 0, 1)   → TILE: occupied cell; tile_type = game tile ID
//
//   Tile type IDs observed in blocky/1+.lvl:
//     0(ground?), 1, 3, 5-7, 14-18, 21, 24-27, 32, 34, 38-39, 62-63,
//     70-71, 77-78, 84, 95, 100.
//
// PART B: Game object columnar property stream (variable-length; starts ~1963 records in)
//
//   This is the SAME generic engine serialization format used in dialog (.dia) files.
//   rawParser.py documents it: two-u32 header (type_id=1, value_type=2) precedes each
//   string entry; null entries use (type_id=1, value_type=6) in 8 bytes only.
//
//   Entry formats:
//     String entry:  [u32=1][u32=2][u32=byte_len][ASCII string + \0]  total: 12+len bytes
//     Null entry:    [u32=1][u32=6]                                   total: 8 bytes
//
//   Section structure:
//     Transition record: u32s = (0, N, 0, world_width)
//     Null header × 2:   u32s = (1, 0, 0, 0)
//     Column 1 (type):   object_count string/null entries
//     Integer column:    16-byte records (0, 1, 0, value) × (object_count + 4)
//                        values 0–3 = likely render Z-order within layer
//     Column 2 (layer):  object_count string/null entries
//     ... more columns ...
//
//   CONFIRMED column semantics (verified against strait/6+.lvl room geometry):
//
//     Col 1 — Object type code (string):
//       "a"  = collision area / hitbox
//       "1"  = trigger / event object / foreground entity
//       "7"  = background anchor sprite (layer=back)
//       "10" = far-background sprite (layer=far)
//
//     Integer column (between col1 and col2) — render Z-order within layer (0–3)
//
//     Col 2 — Render layer (string):
//       "collisions" = physics collision layer (no rendering)
//       "front"      = main foreground layer
//       "back"       = near-background layer
//       "far"        = far-background layer
//       "overlay"    = UI/overlay layer (blocky only)
//
//     Col 3 — Object parameters (string, format varies by type):
//       ""                          = no parameters
//       "W,H,0,0"                   = trigger zone: W=width px, H=height px
//                                     e.g. "400,46,0,0" confirmed in strait/6+.lvl
//       "5,X,Y,Z,Name,flag,..."     = NPC spawner descriptor
//                                     e.g. "5,0,0,0,Fitzroy,1"
//                                     e.g. "5,0,0,0,Leticia,2,-1,0,0,Look Down"
//       "1,Region Name,id,W,H"      = scene/region descriptor
//                                     e.g. "1,Blockrock Region,blockrock,4,1"
//       "5,N,x1,x2,0"              = camera bounds (col 34 in blocky)
//                                     e.g. "5,3,225,500,0"
//
//     Col 4 — Script target (string):
//       ""              = no script
//       "-event_name"   = event/cutscene to trigger, e.g. "-fitzroy_fight"
//       "target_name"   = script jump target
//
//     Blocky/1+.lvl has 47 string columns total; strait/6+.lvl has 4.
//
// The hexpat struct below covers only PART A (tile grid).
// PART B requires a byte-level variable-length parser.
// Use lvlLayout.py (in repo root) to extract and visualize game objects.
struct WorldTileRec {
    u32 head;            // 0xFFFFFF=empty/row-hdr, 0xC0C0C0=special, 0=tile
    u32 tile_type;       // tile type ID when head=0; world_width in row-hdr; 0 otherwise
    u32 width_or_flags;  // world_width in row-hdr record; 0 for empty/tile
    u32 row_flag;        // 1 in row-hdr and tile records; 0 in empty/special
};


// ═══════════════════════════════════════════════════════════════════════════
// Top-level structures
// ═══════════════════════════════════════════════════════════════════════════

// Generic fixed-count array of BgSpriteRec (used as tail of each layer array)
// defined inline per array below to keep sizes explicit.

struct ParallaxLayerArray {
    u32           count;         // always 1030 in blocky/*.lvl
    ParallaxLayerDesc desc;      // item[0]: layer descriptor
    BgSpriteRec   sprites[count - 1]; // items[1..count-1]: sprite placements
};

struct ObjectLayerArray {
    u32              count;        // game_object_count + 2  (header + footer)
    ObjectLayerDesc  desc;         // item[0]: room dimension header
    BgSpriteRec      objects[count - 1]; // items[1..count-1]: per-object records
    //   For array 3: objects[n].x_pos = X pixel position of object n
    //   For array 4: objects[n].y_flag = 1 (active), objects[n].x_pos = Y pixel position
    //   items[count-1] (last) = footer sentinel; field[1]=14 or similar
};

struct Array5 {
    u32  count;               // always 1030 in blocky/*.lvl
    // Item[0] inlined: variable-length background descriptor string header
    u32  bg_type;             // always 1
    u32  bg_num_cont_recs;    // continuation records carrying string bytes
    u32  bg_string_length;    // byte length including null terminator
    char bg_str_data[bg_string_length];
    // Alignment padding up to next 16-byte boundary + all remaining unused
    // sprite slots are absorbed into one flat block.
    // Total items bytes = count*16; consumed so far = 12 + bg_string_length.
    u8   rest[(count * 16) - 12 - bg_string_length];
};

struct Array7 {
    u32 count;                   // usually 1; 0 in some levels
    if (count > 0)
        WorldSizeDesc desc;
};

struct Array9 {
    u32 count;                   // usually 100; 0 in small/sprite levels
    if (count > 0)
        Array9HeaderRec header;
    if (count > 1)
        Array9Rec rows[count - 1];
};

struct LvlFile {
    // ── File header ──────────────────────────────────────────────────────
    // magic byte[6] = "ARR1.0"; byte[7] varies by file sub-type:
    //   0x0D (\r) = standard level file
    //   0x0F     = boss arena variant (e.g. ashboss)
    // version always 0 in all observed files.
    u8  magic[8];
    u16 version;

    // ── Background layer arrays (6 layers × 1030 records each) ───────────
    // Layer order matches the descriptor string in array 5 item[0]:
    //   arrays[0..2] = parallax sprite layers (drawn furthest→nearest)
    //   arrays[3..4] = tile/ground layers
    //   array[5]     = string descriptor + unused slots
    ParallaxLayerArray parallax_layers[3]; // arrays 0–2: sprite atlas + parallax data
    ObjectLayerArray   object_layers[2];   // arrays 3–4: per-object X and Y positions
    Array5             bg_string_array;    // array 5: background descriptor string

    // ── Metadata arrays ───────────────────────────────────────────────────
    u32 empty_arr6_count;       // always 0  (array 6)
    Array7 world_size_arr7;     // array 7: world size descriptor
    u32 empty_arr8_count;       // always 0  (array 8)
    Array9 row_desc_arr9;       // array 9: row descriptor table (100 records)

    // ── World data section ────────────────────────────────────────────────
    // Starts immediately here (at cursor $) with NO leading count field.
    // Contains PART A (tile grid, 16-byte WorldTileRec records) +
    //          PART B (game object columnar property stream, variable-length).
    // Part B is not expressible as fixed-size records — inspect manually in
    // the hex view from this address onward.
    // PART B starts around record 1960-1963 in blocky/1+.lvl (~offset 0x20342).
};

LvlFile lvl @ 0x00;
