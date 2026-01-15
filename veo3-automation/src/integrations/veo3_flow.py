import asyncio
from typing import List, Dict, Any, Optional
from .browser_automation import browser_automation
from .gemini_client import GeminiClient
from ..data.config_manager import config_manager

class VEO3Flow:
    def __init__(self):
        self.gemini_client = GeminiClient()
        self.flow_url = "https://labs.google/flow"
    
    async def generate_video_via_browser(self, prompt: str, project_config: Dict[str, Any]) -> Optional[str]:
        try:
            await browser_automation.start()
            await browser_automation.navigate(self.flow_url)
            
            await asyncio.sleep(2)
            
            prompt_input_selector = 'textarea[placeholder*="prompt"], textarea[placeholder*="Prompt"], input[type="text"]'
            await browser_automation.wait_for_selector(prompt_input_selector, timeout=10000)
            await browser_automation.fill(prompt_input_selector, prompt)
            
            await asyncio.sleep(1)
            
            generate_button_selector = 'button:has-text("Generate"), button:has-text("Create"), button[type="submit"]'
            await browser_automation.click(generate_button_selector)
            
            await asyncio.sleep(5)
            
            status_selector = '[data-status], .status, .generating'
            status = await browser_automation.get_text(status_selector)
            
            max_wait = 300
            waited = 0
            while "generating" in status.lower() or "processing" in status.lower():
                await asyncio.sleep(5)
                waited += 5
                if waited >= max_wait:
                    break
                status = await browser_automation.get_text(status_selector)
            
            video_selector = 'video, [data-video], .video-result'
            await browser_automation.wait_for_selector(video_selector, timeout=60000)
            
            video_url = await browser_automation.evaluate("""
                () => {
                    const video = document.querySelector('video, [data-video], .video-result');
                    return video ? video.src || video.getAttribute('src') : null;
                }
            """)
            
            return video_url
            
        except Exception as e:
            print(f"Error in browser automation: {e}")
            return None
    
    async def generate_video_via_api(self, prompt: str, project_config: Dict[str, Any]) -> Optional[str]:
        try:
            veo_prompt = f"""
            Generate a video with the following prompt:
            {prompt}
            
            Style: {project_config.get('style', '3d_Pixar')}
            Duration: {project_config.get('duration', 8)} seconds
            Aspect Ratio: {project_config.get('aspect_ratio', '16:9')}
            """
            
            response = await self.gemini_client.generate_text(veo_prompt)
            
            return response
            
        except Exception as e:
            print(f"Error in API generation: {e}")
            return None
    
    async def generate_videos(self, prompts: List[str], project_config: Dict[str, Any], use_browser: bool = True) -> List[Dict[str, Any]]:
        results = []
        
        for i, prompt in enumerate(prompts):
            scene_id = f"scene_{i+1}"
            try:
                if use_browser:
                    video_url = await self.generate_video_via_browser(prompt, project_config)
                else:
                    video_url = await self.generate_video_via_api(prompt, project_config)
                
                results.append({
                    "scene_id": scene_id,
                    "prompt": prompt,
                    "status": "SUCCESSFUL" if video_url else "FAILED",
                    "video_url": video_url,
                    "video_path": None
                })
                
            except Exception as e:
                results.append({
                    "scene_id": scene_id,
                    "prompt": prompt,
                    "status": "FAILED",
                    "error": str(e),
                    "video_url": None,
                    "video_path": None
                })
        
        return results

veo3_flow = VEO3Flow()

