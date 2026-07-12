namespace levelpart {
    struct data {
        u64 data1;
        u64 data2;
    };
    
    struct level_contents {
        u32 size;
        data level[size];
    };
    
}


namespace small_sec {
    struct small_unk{
        u8 size;
        u8 size2;
        u16 size3;
        u64 sec[size2];
    };
}

namespace unknown {
    struct unk_chunk {
        u32 head;
        u32 type;
        u32 section_size;
        if (type == 00) {
            u32 dunno;
        }
        if (type == 2) {
            u8 section[section_size];
        }     
    };
    
    struct unk_data {
        u64 data1;
        u64 data2;
    };
    
    struct data {
        u32 size;
        unk_chunk chunks[2];
        unk_data data[size - 2];
    };
}

namespace new_unknown {
    struct chunks {
        u32 head;
        u32 type;
        u32 section_size;
        if (type == 00) {
            u32 dunno;
        }
        if (type == 2) {
            u8 section[section_size];
        }     
    };
    
    struct unk_data {
        u32 size;
        chunks dunno[2];
        chunks unk[size - 2];
    };
}

namespace hr {
    struct chunks {
        u32 head;
        u32 type;
        u32 section_size;
        if (type == 00) {
            u32 dunno;
        }
        if (type == 2) {
            u8 section[section_size];
        }     
    };
    
    struct unk_data {
        u32 size;
        chunks dunno[2];
        chunks unk[size - 2];
    };
}

namespace sm {
    struct chunks {
        u32 head;
        u32 type;
        if (type == 00) {
            u32 section_size;
            u32 dunno;
        }
        if (type == 2) {
            u32 section_size;
            u8 section[section_size];
        }
        
    };
    
    struct unk_data {
        u32 size;
        chunks dunno[2];
        chunks unk[size - 2];
    };
}

struct arr_hdr_t {
    u64 magic_number;
    u16 version_minor;
    
   // u32 step1;
    levelpart::level_contents level[5];
    unknown::data unknown[1];
    levelpart::level_contents level2[2];
    new_unknown::unk_data unknown2[1];
    levelpart::level_contents level3[1];
    hr::unk_data hr_s[1];
    sm::unk_data sm[2];
};

arr_hdr_t hdr @ 0x00;
