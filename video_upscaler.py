
'''
    Video Upscaler
    Automation tool for video upscaling using video2x
    Author: danrossi <electroteque@protonmail.com>
'''

import argparse
import logging
import os
import asyncio
from logging import Logger
from asyncio import StreamReader
import tempfile
from pathlib import Path
from model_builder import ProcessorModelEnum, modeltypesmap
from enum_action import enum_action
import platform

logger = logging.getLogger("videoupscaler")
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


async def write_output(stdout: StreamReader, stderr, log) -> None:
    while line := await stdout.readline():
        log.info("%s", line.decode().rstrip())

async def run_command(cmd, log: Logger = None, verbose:bool = True):
     if (verbose):
        stdout=asyncio.subprocess.PIPE
        stderr=asyncio.subprocess.STDOUT
     else:
        stdout=asyncio.subprocess.DEVNULL
        stderr=asyncio.subprocess.DEVNULL

     
     proc = await asyncio.create_subprocess_exec(*cmd, stdout=stdout, stderr=stderr)

     if (verbose):
        stdout_task = asyncio.create_task(write_output(proc.stdout, proc.stderr, log))
        return_code, _ = await asyncio.gather(proc.wait(), stdout_task)
     else:
        return_code = await asyncio.gather(proc.wait())
    
     log.info(f'Stop Process, returned: {return_code}')

def replace_extension(filename, new_extension):
     file_path = Path(filename)
     return str(file_path.with_suffix(new_extension))

class VideoUpscaler:

    def __init__(self, src_dir:str, out_dir:str, model: ProcessorModelEnum, model_type: int, scale:int, noise_level:int, isHD: bool, is4K: bool):
        self.src_dir = src_dir
        self.out_dir = out_dir

        if (platform.system() == "Windows"):
            self.video2x_path = os.path.join(os.environ.get('LOCALAPPDATA'), "Programs", "video2x")
            self.video2x_bin = os.path.join(self.video2x_path, "video2x")
            self.ffmpeg_bin = os.path.join(self.video2x_path, "ffmpeg","bin","ffmpeg")
        else:
            self.video2x_bin = "video2x"
            self.ffmpeg_bin = "ffmpeg"
            
        self.model = model
        self.model_type = modeltypesmap[model][model_type]
        self.scale = scale
        self.noise_level = noise_level
        self.setDimensions(isHD, is4K)

    def setDimensions(self, isHD, is4K):
        self.width = None
        if (isHD):
            self.scale = None
            self.width = "1920"
            self.height = "1080"
        if (is4K):
            self.scale = None
            self.width = "3840"
            self.height = "2160"

    def model_args(self):
        model_arg = ""
        if (self.model == ProcessorModelEnum.realesrgan):
            model_arg = "--realesrgan-model"
        elif (self.model == ProcessorModelEnum.libplacebo):
            model_arg = "libplacebo-shader"
        elif (self.model == ProcessorModelEnum.realcugan):
            model_arg = "--realcugan-model"
        elif (self.model == ProcessorModelEnum.rife):
            model_arg = "--rife-model"

        return ["-p", self.model.name, model_arg, self.model_type]

    def scale_args(self):
        if (self.width):
            return ["-w", self.width, "-h", self.height]
        else:
            return ["-s", self.scale]

    async def super_resolution(self, src_file, out_file):
        cmd = [
            self.video2x_bin,
            '-i',
            src_file,
            '-c', 
            'h264_nvenc',
            '--no-copy-streams']
        cmd += self.model_args()
        cmd += self.scale_args()
        cmd += ['-n', self.noise_level,
            '-e',
            'preset=p7', 
            '-e', 
            'tune=hq',
            '-o',
            out_file
            ]
        
        #print(cmd)

        await run_command(cmd, logger, True)

    async def mux_audio(self, src_file, tmp_file, out_file):
        cmd = [
            self.ffmpeg_bin,
            '-i',
            tmp_file,
            '-i',
            src_file,
            '-c:v', 
            'copy',
            '-c:a',
            'aac',
            '-map', 
            '0:v:0', 
            '-map', 
            '1:a:0',
            out_file
            ]

        await run_command(cmd, logger, True)

    async def process_video(self):

        for root, dirs, files in os.walk(self.src_dir):
            for file in files:
                try:
                    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as temp_file:
                        src_file = os.path.join(root, file)
  
                        output_path = temp_file.name

                        dst_file = os.path.join(self.out_dir, replace_extension(file, ".mp4"))

                        #logger.debug(temp_file.name)
                        await self.super_resolution(src_file, output_path)
                        await self.mux_audio(src_file, output_path, dst_file)
                finally:
                    if os.path.exists(output_path):
                        os.remove(output_path)

    async def rescale(self):
        await self.process_video()
        
    def run(self):
        asyncio.run(self.rescale())
    
    

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', required=True)
    parser.add_argument('-o', '--output', required=True)
    #parser.add_argument('-m', '--model', type=int, default=1)
    parser.add_argument('-m', '--model', action=enum_action(ProcessorModelEnum), default=ProcessorModelEnum.realesrgan)
    parser.add_argument('-t', '--model_type', type=int, default=1)
    parser.add_argument('-s', '--scale', type=int, default=4)
    parser.add_argument('-n', '--noise_level', type=int, default=3)
    parser.add_argument('--hd', action='store_true')
    parser.add_argument('--fourk', action='store_true')
    args = parser.parse_args()

    try:
        logger.info("Starting Upscale")
        videoscaler = VideoUpscaler(args.input, args.output, args.model, args.model_type, args.scale, args.noise_level, args.hd, args.fourk)
        videoscaler.run()
    except Exception as e:
        logger.error(e)


if __name__ == "__main__":
    main()
