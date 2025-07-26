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
        1: { "type": "realesr-animevideov3", "max_scale": 4  },
        2: { "type": "realesrgan-plus-anime", "min_scale": 4 },
        3: { "type": "realesrgan-plus", "min_scale": 4 }
    },
    ProcessorModelEnum.libplacebo: {
        1: { "type": "anime4k-v4-a" },
        2: { "type": "anime4k-v4-a+a" },
        3: { "type": "anime4k-v4-b+b" },
        4: { "type": "anime4k-v4-c+a" },
        5: { "type": "anime4k-v4-b" },
        6: { "type": "anime4k-v4-c" },
        7: { "type": "anime4k-v4.1-gan" }
    },
    ProcessorModelEnum.realcugan: {
        1: { "type": "models-nose", "max_scale": 2, "max_noise_level": 0 }, 
        2: { "type": "models-pro", "max_scale": 3, "max_noise_level": 3  }, 
        3: { "type": "models-se", "max_noise_level": 3 }
    },
    ProcessorModelEnum.rife: {
        1: { "type": "rife-v4.6" },
        2: { "type": "rife-v4.25" }, 
        3: { "type": "rife-v4.25-lite" },
        4: { "type": "rife-v4.26" }
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