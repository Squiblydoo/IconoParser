// Iconoclasts Cutscene File Format (.arr cutscene variant)
// Reverse-engineered by Squiblydoo with assistance from IconoParser analysis.
//
// FILE STRUCTURE OVERVIEW
// =======================
// Header magic:  u64 + u16  (10 bytes total: 0x415252312E300F000000)
// Followed by 15 sections in order:
//
//   Section  0  [markers]     - Frame count markers; always [id=1, data=0] pairs (u64,u64)
//   Section  1  [time]        - Tick number when this event fires
//   Section  2  [duration]    - Tween / lerp duration (0 = instant; non-zero on 'pos' cmds)
//   Section  3  [unknown_3]   - Always 0; purpose unknown
//   Section  4  [unknown_4]   - Always 0; purpose unknown
//   Section  5  [command]     - The action type string:
//                               set_time, zero, lock, unlock, skip, noskip, end,
//                               edit_robin, edit_robin2, edit_demo,
//                               pos, edit_scroll, toggle_scroll,
//                               play_track, sound,
//                               make_text, message,
//                               create_effect, edit_effect, hash
//   Section  6  [target_id]   - Object / slot identifier:
//                               '0'=Robin; '1'/'2'/'3'...=NPC index;
//                               'scroll','robin','demo' for pos;
//                               'HUD','Text','placements' for effects/text
//   Section  7  [param_1]     - Primary parameter:
//                               • edit_robin / edit_demo: animation key=value string
//                                 Keys: #X (instant X), X (dest X), #Y, Y, #Direction,
//                                       Animation, !Animation (transition), #NextAnim,
//                                       #AnimStart, #AnimEnd, #MoveX, #SpeedX, #MoveTime,
//                                       #MultiY, #Shake, #ForceX, #ForceY, #GoX, #OffY,
//                                       #Life, #Death, AnimFrame, Width, Height, Filter,
//                                       #Opacity, #SubOpacity
//                               • pos scroll/robin: startX
//                               • pos demo: NPC index (integer)
//                               • play_track: track state (e.g. '1' = play)
//                               • sound: volume
//                               • create_effect / edit_effect: sub-id or '0'
//   Section  8  [param_2]     - Secondary parameter:
//                               • pos scroll/robin: startY
//                               • pos demo: startX
//                               • play_track: additional flag
//   Section  9  [param_3]     - Tertiary parameter:
//                               • pos scroll/robin: endX
//                               • pos demo: startY
//                               • make_text: text string ID (integer)
//                               • create_effect: effect properties key=value string
//   Section 10  [param_4]     - Quaternary parameter:
//                               • pos scroll/robin: endY
//                               • pos demo: endX
//   Section 11  [param_5]     - Fifth parameter:
//                               • pos demo: endY
//                               • rarely used otherwise
//   Sections 12–14 [param_6–8] - Sixth through eighth parameters; always empty in
//                                all examined files.
//
// ENTRY ENCODING
// ==============
// Each section begins with a u32 size (= number of frames in the cutscene).
// Each entry has:
//   u32  id       (always 1)
//   u32  type     (2 = has data payload; 6 = empty / no payload)
//   if type == 2:
//     u32  data_len
//     u8   data[data_len]   (UTF-8 string, often null-terminated or \r-padded)
//
// COORDINATES
// ===========
// World coordinate system: X increases rightward, Y increases downward.
// Game viewport: 1280 × 720 world units.
// scroll_x  = left edge of the camera viewport.
// Sprite X=896, Y=592 → near center-left of a 1280-wide screen.
//
// 'pos' COMMAND VARIANTS
// ======================
//   pos scroll   [6]='scroll'  [7]=startX  [8]=startY  [9]=endX  [10]=endY
//   pos robin    [6]='robin'   [7]=startX  [8]=startY  [9]=endX  [10]=endY
//   pos demo     [6]='demo'    [7]=NPC_idx [8]=startX  [9]=startY [10]=endX [11]=endY
//
// ANIMATION STRING KEY PREFIXES
// ==============================
//   #   Immediate / force  (e.g. #X,896 = teleport to X 896 instantly)
//   !   Transition         (e.g. !Animation,Walk = begin Walk anim sequence)
//   (none) Destination / state (e.g. X,1998 = move toward; Animation,Idle = set state)

namespace levelpart {
    struct data {
        u64 id;      // always 1
        u64 value;   // always 0
    };

    struct markers {
        u32 frame_count;
        data frame[frame_count];
    };
}

namespace timedata {
    struct entry {
        u32 id;
        u32 type;
        if (type == 0x02) {
            u32 len;
            u8  value[len];  // string: tick number (e.g. "1", "100", "99999")
        }
    };

    struct section {
        u32 frame_count;
        entry time[frame_count];
    };
}

namespace param {
    // Generic section for sections 2–14: each entry is a string payload or empty.
    struct entry {
        u32 id;
        u32 type;
        if (type == 0x02) {
            u32 len;
            u8  value[len];  // UTF-8 string; content depends on section role
        }
        // type == 0x06 means empty (no payload)
    };

    struct section {
        u32 frame_count;
        entry data[frame_count];
    };
}

struct cutscene_t {
    u64 magic;          // 0x4152523 12E300F00 ("ARR1.0" variant)
    u16 version;

    // Section 0: frame markers
    levelpart::markers   markers;

    // Sections 1–6 (before animation): time, duration, unknowns, command, target_id
    param::section       time_section;       // [1] fire tick
    param::section       duration_section;   // [2] tween duration
    param::section       unknown_3;          // [3] always 0
    param::section       unknown_4;          // [4] always 0
    param::section       command_section;    // [5] action type string
    param::section       target_id_section;  // [6] target / object id

    // Section 7: primary parameter (animation string, startX, demo index, etc.)
    param::section       param_1;

    // Sections 8–14: secondary through eighth parameters
    param::section       param_2;
    param::section       param_3;
    param::section       param_4;
    param::section       param_5;
    param::section       param_6;   // always empty in examined files
    param::section       param_7;   // always empty in examined files
    param::section       param_8;   // always empty in examined files
};

cutscene_t cutscene @ 0x00;
