from enum import Enum

class ProcessorModelEnum(Enum):
    realesrgan = 1
    libplacebo = 2
    realcugan = 3
    rife = 4
    lib2real = 5

    def __str__(self):
        return f"{str(self.value)} ({self.name})"

modeltypesmap = {
    ProcessorModelEnum.realesrgan : {
        1: "realesr-animevideov3",
        2: "realesrgan-plus-anime",
        3: "realesrgan-plus"
    },
    ProcessorModelEnum.libplacebo: {
        1: "anime4k-v4-a",
        2: "anime4k-v4-a+a",
        3: "anime4k-v4-b+b",
        4: "anime4k-v4-c+a",
        5: "anime4k-v4-b",
        6: "anime4k-v4-c",
        7: "anime4k-v4.1-gan"
    },
    ProcessorModelEnum.realcugan: {
        1: "models-nose", 
        2: "models-pro", 
        3: "models-se"
    },
    ProcessorModelEnum.rife: {
        1: "rife",
        2: "rife-HD", 
        3: "rife-UHD", 
        4: "rife-anime", 
        5: "rife-v2",
        6: "rife-v2.3", 
        7: "rife-v2.4", 
        8: "rife-v3.0",
        9: "rife-v3.1", 
        10: "rife-v4", 
        11: "rife-v4.6",
        12: "rife-v4.25", 
        13: "rife-v4.25-lite",
        14: "rife-v4.26"
    }
}

multi_models_typemap = {
    ProcessorModelEnum.lib2real : [
             {
                 "model": ProcessorModelEnum.libplacebo,
                 "type": modeltypesmap[ProcessorModelEnum.libplacebo][7],
                 "width": 960,
                 "height": 540,
                 "scale": 0,
                 "lossless": True
             },
             {
                 "model": ProcessorModelEnum.realesrgan,
                 "type": modeltypesmap[ProcessorModelEnum.realesrgan][1],
                 "scale": 4,
                 "width": 0,
                 "height": 0,
                 "lossless": False
             }
                 
        ]
}