
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

    def __init__(self, src_dir:str, out_dir:str):
       self.src_dir = src_dir
       self.out_dir = out_dir
       self.video2x_path = os.path.join(os.environ.get('LOCALAPPDATA'), "Programs", "video2x")
       self.video2x_bin = os.path.join(self.video2x_path, "video2x")
       self.ffmpeg_bin = os.path.join(self.video2x_path, "ffmpeg","bin","ffmpeg")

    
    async def super_resolution(self, src_file, out_file):
        cmd = [
            self.video2x_bin,
            '-i',
            src_file,
            '-c', 
            'h264_nvenc',
            '--no-copy-streams',
            '-p', 
            'libplacebo',
            '--libplacebo-shader', 
            'anime4k-v4-a+a',
            '-w', 
            '1920',
            '-h', 
            '1080',
            '-e',
            'preset=p7', 
            '-e', 
            'tune=hq',
            '-o',
            out_file
            ]

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
                        #print(os.path.join(root, file))
                        #rint(temp_file.name)
                        output_path = temp_file.name

                        dst_file = os.path.join(self.out_dir, replace_extension(file, ".mp4"))

                        logger.debug(temp_file.name)
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
    parser.add_argument('-i', '--input', default="")
    parser.add_argument('-o', '--output', default="")
   # parser.add_argument('-s', '--scale', default="2", required=False)
    args = parser.parse_args()

    try:
        #logger.info("Starting Stream {0} with token {1}".format(stream_name, token))
        videoscaler = VideoUpscaler(args.input, args.output)
        videoscaler.run()
        #logger.info(message)
    except Exception as e:
        logger.error(e)


if __name__ == "__main__":
    main()
