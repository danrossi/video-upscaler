
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
import re
from typing import Callable
import math

from rich.progress import Progress
from rich.logging import RichHandler

richHandler = RichHandler(show_path=True)

logger = logging.getLogger("videoupscaler")
#logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(message)s", 
    datefmt="[%X]",
    handlers=[
        richHandler
    ]
)


async def read_stream(stream, prefix, log: Logger, progress: Callable = None):
    try:
        while True:
            line = await stream.read(256)
            if not line:
                break
            line_str = line.decode("utf-8").strip()
            #log.info("frame" in line_str[:8])
            if "frame" in line_str[:8]:
                match = re.search(r"[-+]?[0-9]*\.?[0-9]+", line_str)
                if match:
                    float_value = float(match.group(0)) / 100

                    progress(float_value)
            else:
                #log.info("")
                log.info(f"{prefix}: {line_str}")
    except Exception as e:
            logger.error(e)  



async def run_command(cmd, log: Logger = None, verbose:bool = True):
     if (verbose):
        stdout=asyncio.subprocess.PIPE
        stderr=asyncio.subprocess.PIPE
     else:
        stdout=asyncio.subprocess.DEVNULL
        stderr=asyncio.subprocess.DEVNULL

     #print(*cmd)
 
     proc = await asyncio.create_subprocess_exec(*cmd, stdout=stdout, stderr=stderr)

     with Progress() as progress:
            
        task = progress.add_task("[red]Processing Upscale...", total=100)
            
        def upload_progress(perc) -> None:
            progress.update(task, completed=perc)


        if (verbose):
            await asyncio.gather(
                read_stream(proc.stdout, "FFMPEG_STDOUT", log, upload_progress),
                read_stream(proc.stderr, "FFMPEG_STDERR", log)
            )
            return_code = await proc.wait()
        else:
            return_code = await asyncio.gather(proc.wait())
        
        log.info(f'Stop Process, returned: {return_code}')

async def run_command_output(cmd, log: Logger = None):
     
    #print(*cmd)
 
    proc = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    stdout_bytes, stderr_bytes = await proc.communicate()

    await proc.wait() # Wait for the subprocess to complete
    stdout_text = stdout_bytes.decode('utf-8').strip()
    stderr_text = stderr_bytes.decode('utf-8').strip()

    return stdout_text, stderr_text

def replace_extension(filename, new_extension):
     file_path = Path(filename)
     return str(file_path.with_suffix(new_extension))



class VideoUpscaler:

    def __init__(self, src_dir:str, out_dir:str, model: ProcessorModelEnum, model_type: int, scale:int, noise_level:int, isHD: bool, is4K: bool, thread_count: int, max_height: int):
        self.src_dir = src_dir
        self.out_dir = out_dir

        if (platform.system() == "Windows"):
            self.video2x_path = os.path.join(os.environ.get('LOCALAPPDATA'), "Programs", "video2x")
            self.video2x_bin = os.path.join(self.video2x_path, "video2x")
            self.ffmpeg_bin = os.path.join(self.video2x_path, "ffmpeg","bin","ffmpeg")
            self.ffprobe_bin = os.path.join(self.video2x_path, "ffmpeg","bin","ffprobe")
        else:
            self.video2x_bin = "video2x"
            self.ffmpeg_bin = "ffmpeg"
            self.ffprobe_bin = "ffprobe"
            
        self.model = model
        self.model_type = modeltypesmap[model][model_type]
        self.scale = int(scale)
        self.noise_level = noise_level
        self.thread_count = thread_count
        self.max_height = int(max_height)
        self.setDimensions(isHD, is4K)

        logger.info(f"Starting Upscale {model.name} {self.model_type}")

    def setMaxScale(self, height, max_height):
        if (self.model == ProcessorModelEnum.realesrgan and max_height > 0):
            if ((height * self.scale) > max_height):
                self.scale = min(math.floor(max_height / height),4)
                logger.info(f"New Scale Set {self.scale}")

    def setDimensions(self, isHD, is4K):
        self.width = None

        if (self.model != ProcessorModelEnum.realesrgan):
            if (isHD):
                self.scale = None
                self.width = "1920"
                self.height = "1080"
            if (is4K):
                self.scale = None
                self.width = "3840"
                self.height = "2160"

                print(self.width)

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
            return ["-s", str(self.scale)]

    async def super_resolution(self, src_file, out_file):
        cmd = [
            self.video2x_bin,
            '-i',
            src_file,
            '-c',
            'hevc_nvenc',
            #'h264_nvenc',
            #'-a', 'vulkan',
            '--no-copy-streams']
        cmd += self.model_args()
        cmd += self.scale_args()
        cmd += [
            '-n', self.noise_level,    
            '--thread-count', str(self.thread_count),
            '-e',
            'preset=p7',
            '-e',
            'rc=vbr',
            '-e',
            'cq=19',
            '-e', 
            'tune=hq',
            '-o',
            out_file
            ]
        
        print(cmd)

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
            '-y',
            out_file
            ]

        await run_command(cmd, logger, True)
    
    async def get_video_dimensions(self, src_file):
        cmd = [
            self.ffprobe_bin,
            '-v', 
            'error',
            '-select_streams', 'v:0',
            '-show_entries', 'stream=width,height',
            '-of', 'csv=p=0:s=x', 
            src_file
            ]
        
        stdout, stderr = await run_command_output(cmd, logger)

        if 'x' in stdout:
            width_str, height_str = stdout.split('x')
            width = int(width_str)
            height = int(height_str)
            return width, height




    async def process_video(self):

        for root, dirs, files in os.walk(self.src_dir):
            for file in files:
                try:
                    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as temp_file:
                        src_file = os.path.join(root, file)
  
                        output_path = temp_file.name

                        dst_file = os.path.join(self.out_dir, replace_extension(file, ".mp4"))

                        if (self.max_height > 0):
                            try:
                                width, height = await self.get_video_dimensions(src_file)
                                self.setMaxScale(height, self.max_height)
                            except Exception as e:
                                logger.error(e)
                        #logger.debug(temp_file.name)
                        await self.super_resolution(src_file, output_path)
                        await self.mux_audio(src_file, output_path, dst_file)
                        #if os.path.exists(output_path):
                        #    os.remove(output_path)
                finally:
                    if os.path.exists(output_path):
                        temp_file.close()
                        os.remove(output_path)
                await asyncio.sleep(10)

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
    parser.add_argument('-n', '--noise_level', type=str, default=3)
    parser.add_argument('--tc', type=int, default=1)
    parser.add_argument('--mh', type=int, default=0)
    parser.add_argument('--hd', action='store_true')
    parser.add_argument('--fourk', action='store_true')
    args = parser.parse_args()

    try:
        videoscaler = VideoUpscaler(args.input, args.output, args.model, args.model_type, str(args.scale), str(args.noise_level), args.hd, args.fourk, args.tc, args.mh)
        videoscaler.run()
    except Exception as e:
        logger.error(e)


if __name__ == "__main__":
    main()
