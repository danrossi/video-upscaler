
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
from model_builder import ProcessorModelEnum, modeltypesmap, multi_models_typemap 
from enum_action import enum_action
import platform
import re
from typing import Callable
import math
import traceback
import shutil

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
        """"""
            #logger.error(e)  



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
            
       
        
        self.scale = int(scale)
        self.noise_level = noise_level
        self.thread_count = thread_count
        self.max_height = int(max_height)
        self.model = None
        self.models = None

        self.setModel(model, model_type)

        
        self.setDimensions(isHD, is4K)

        

    def setModel(self, model, model_type):
        if (model == ProcessorModelEnum.lib2real):
            self.models = multi_models_typemap[model]
            logger.info(f"Starting Upscale {self.models}")
        else:
            self.model = model
            self.model_type = modeltypesmap[model][model_type]
            logger.info(f"Starting Upscale {model.name} {self.model_type}")

    def setMaxScale(self, height, max_height):
        if (self.model is not None and self.model == ProcessorModelEnum.realesrgan and max_height > 0):
            if ((height * self.scale) > max_height):
                self.scale = min(math.floor(max_height / height),4)
                logger.info(f"New Scale Set {self.scale}")

    def setDimensions(self, isHD, is4K):
        self.width = 0
        self.height = 0

        if (self.model is not None and self.model != ProcessorModelEnum.realesrgan):
            if (isHD):
                self.scale = 0
                self.width = 1920
                self.height = 1080
            elif (is4K):
                self.scale = 0
                self.width = 3840
                self.height = 2160

    def model_args(self, model: ProcessorModelEnum, model_type: str):
        model_arg = ""
        if (model == ProcessorModelEnum.realesrgan):
            model_arg = "--realesrgan-model"
        elif (model == ProcessorModelEnum.libplacebo):
            model_arg = "libplacebo-shader"
        elif (model == ProcessorModelEnum.realcugan):
            model_arg = "--realcugan-model"
        elif (model == ProcessorModelEnum.rife):
            model_arg = "--rife-model"

        return ["-p", model.name, model_arg, model_type]

    def scale_args(self, scale: int, width: int, height: int):
        if (width > 0):
            return ["-w", str(width), "-h", str(height)]
        else:
            return ["-s", str(scale)]

    async def super_resolution(self, src_file: str, out_file: str, model: ProcessorModelEnum, model_type: str, scale: int, width: int, height: int, lossless: bool = False):
        cmd = [
            self.video2x_bin,
            '-i',
            src_file,
            '-c',
            'hevc_nvenc',
            #'h264_nvenc',
            #'-a', 'vulkan',
            '--no-copy-streams']
        cmd += self.model_args(model, model_type)
        cmd += self.scale_args(scale, width, height)
        cmd += [
            '-n', self.noise_level,    
            '--thread-count', str(self.thread_count)]
        
        if (lossless):
            cmd += ['-e',
                'preset=p7',
                '-e', 
                'tune=lossless']
        else:
            cmd += ['-e',
            'preset=p7',
            '-e', 
            'tune=hq']

        cmd += [
            '-e',
            'rc=vbr',
            '-e',
            'cq=19',
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
            '-y',
            out_file
            ]
        
        #print(cmd)

        await run_command(cmd, logger, True)
    
    async def pre_process(self, src_file, src_file_name, tmp_dir):
        tmp_src_file = os.path.join(tmp_dir, "transcoded_{0}".format(src_file_name))
        cmd = [
            self.ffmpeg_bin,
            '-i',
            src_file,
            '-c:v', 
            'libx265',
            '-x265-params',
            'lossless=1',
            '-an', 
            '-y',
            tmp_src_file
            ]
        
        #print(cmd)

        await run_command(cmd, logger, True)
        return tmp_src_file

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


    async def multi_model_pass(self, original_src_file, src_file, src_file_name, temp_dir, dst_file):
        
        next_src_file = src_file
        

        for model in self.models:
            logger.info(f"Process pass with model {model["model"].name}")
            dst_filename = "scaled_{0}_{1}".format(model["model"].name, src_file_name)
            next_dst_file = os.path.join(temp_dir, dst_filename)
            await self.super_resolution(next_src_file, next_dst_file, model["model"], model["type"], model["scale"], model["width"], model["height"], model["lossless"])
            next_src_file = next_dst_file
        
        await self.mux_audio(original_src_file, next_dst_file, dst_file)

    
    async def single_model_pass(self, original_src_file, src_file, src_file_name, temp_dir, dst_file):

        if (self.max_height > 0):
            try:
                width, height = await self.get_video_dimensions(src_file)
                self.setMaxScale(height, self.max_height)
            except Exception as e:
                logger.error(e)

        output_path = os.path.join(temp_dir, "scaled_" + src_file_name)
        await self.super_resolution(src_file, output_path, self.model, self.model_type, self.scale, self.width, self.height)
        await self.mux_audio(original_src_file, output_path, dst_file)


    async def process_video(self):

        for root, dirs, files in os.walk(self.src_dir):
            for file in files:
                try:
                    with tempfile.TemporaryDirectory(delete=False) as temp_dir:
                            logger.info(f"Creating Temp Directory {temp_dir}")

                            src_file_name = replace_extension(file, ".mp4")
                        

                            original_src_file = os.path.join(root, file)
                            dst_file = os.path.join(self.out_dir, src_file_name)
                            
                            if (os.path.splitext(file) != "mp4"):
                                src_file = await self.pre_process(original_src_file, src_file_name, temp_dir)

                                logger.info(f"Converted Source from {original_src_file} to {src_file}")
                            else:
                                src_file = original_src_file

                            logger.info(f"Processing Source {src_file}")

                            if (self.models):
                                await self.multi_model_pass(original_src_file, src_file, src_file_name, temp_dir, dst_file)
                            else:
                                await self.single_model_pass(original_src_file, src_file, src_file_name, temp_dir, dst_file)
                finally:
                    if os.path.exists(temp_dir):
                        shutil.rmtree(temp_dir)

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
        print(traceback.format_exc())


if __name__ == "__main__":
    main()
