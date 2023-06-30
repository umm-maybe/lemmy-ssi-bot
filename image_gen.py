from diffusers import StableDiffusionPipeline, StableDiffusionImg2ImgPipeline
from PIL import Image
import torch
from datetime import datetime

def dummy(images, **kwargs):
    return images, False

text_to_image = StableDiffusionPipeline.from_pretrained("Mitsua/mitsua-diffusion-cc0" , torch_dtype=torch.float16)
text_to_image.to("cuda")
text_to_image.enable_xformers_memory_efficient_attention()
text_to_image.safety_checker = dummy

def generate_image(prompt):
    image_data = text_to_image(prompt).images[0]
    now = datetime.now()
    nowstr = now.strftime("%Y%m%d%H%M%S")
    image_path = f"{nowstr}.png"
    image_data.save(image_path)
    return image_path
