
namespace dialog {
    struct dialogText {
        u32 dialog2;
        u32 dialog3;
        u32 size;
        u8 text [size];
    };
    
    struct dialog_contents {
        u32 dialogSize;
        dialogText c[dialogSize];
    };
    
}


struct arr_hdr_t {
    u64 magic_number;
    u16 version_minor;
    dialog::dialog_contents c[1000];
};



arr_hdr_t hdr @ 0x00;
