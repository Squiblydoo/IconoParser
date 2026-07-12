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

 namespace animations {
    struct data {
        u32 data1;
        u32 type;
        if (type == 02) {
            u32 len;
            u8 section[len];
        }
    };
    
    struct anim {
        u32 size;
        data unknown[size];
    };

}

 namespace unknown_struct {
    struct data {
        u32 data1;
        u32 type;
        if (type == 02) {
            u32 len;
            u8 section[len];
        }
    };
    
    struct unknown {
        u32 size;
        data unknown[size];
    };
}


struct arr_hdr_t {
    u64 magic_number;
    u16 version_minor;
    
   // u32 step1;
    levelpart::level_contents level[1];
    unknown_struct::unknown unk[6];
    animations::anim animation[1];
    unknown_struct::unknown unk2[7];
};

arr_hdr_t hdr @ 0x00;
