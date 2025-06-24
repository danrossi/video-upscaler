'''
    Video Upscaler
    Automation tool for running all models tests
    Author: danrossi <electroteque@protonmail.com>
'''

import argparse
import logging
import asyncio
import os
from video_upscaler import VideoUpscaler
from model_builder import ProcessorModelEnum, modeltypesmap

logger = logging.getLogger("videoupscaler")
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

async def run_upscale(input, output, noise_level, model, model_type):
     

        model_type_name = modeltypesmap[model][model_type]

        out_dir = os.path.join(output, model.name, model_type_name)

        os.makedirs(out_dir, exist_ok=True)
        logger.info(f"Starting Upscale for {model.name} {model_type_name} in {out_dir}")
        videoscaler = VideoUpscaler(input, out_dir, model, model_type, str(4), str(noise_level), False, False)
        await videoscaler.rescale()

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', required=True)
    parser.add_argument('-o', '--output', required=True)
    parser.add_argument('-n', '--noise_level', type=int, default=3)
  
    args = parser.parse_args()

    try:
        logger.info("Starting Upscale")
        run_tests = []

        for model in ProcessorModelEnum:
            for type in modeltypesmap[model]:
                run_tests.append(run_upscale(args.input, args.output, args.noise_level, model, type))

        
        await asyncio.gather(*run_tests)
        
    except Exception as e:
        logger.error(e)
    



if __name__ == "__main__":
    asyncio.run(main())
