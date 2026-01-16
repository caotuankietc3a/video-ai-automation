import asyncio
from typing import List, Dict, Any, Optional
from .browser_automation import browser_automation
from .gemini_client import GeminiClient
from ..data.config_manager import config_manager

class VEO3Flow:
    def __init__(self):
        self.gemini_client = GeminiClient()
        self.flow_url = "https://labs.google/fx/tools/flow"
    
    async def generate_video_via_browser(self, prompt: str, project_config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        try:
            await browser_automation.start()
            
            project_link = project_config.get("project_link", "")
            if project_link:
                await browser_automation.navigate(project_link)
                await asyncio.sleep(3)
                await browser_automation.login_to_google()
                await asyncio.sleep(2)
            else:
                await browser_automation.navigate(self.flow_url)
                await asyncio.sleep(2)
                
                create_with_flow_selector = 'button:has-text("Create with Flow")'
                await browser_automation.wait_for_selector(create_with_flow_selector, timeout=60000)
                await browser_automation.click(create_with_flow_selector)
                await asyncio.sleep(2)
                
                await browser_automation.login_to_google()
                await asyncio.sleep(3)
                
                new_project_selector = 'button:has-text("New project")'
                await browser_automation.wait_for_selector(new_project_selector, timeout=10000)
                await browser_automation.click(new_project_selector)
                await asyncio.sleep(2)
                
                current_url = await browser_automation.get_current_url()
                if current_url and "/project/" in current_url:
                    project_id = current_url.split("/project/")[-1].split("?")[0]
                    project_link = f"https://labs.google/fx/tools/flow/project/{project_id}"
                    project_config["project_link"] = project_link
                    from ..data.project_manager import project_manager
                    project_file = project_config.get("file", "")
                    if project_file:
                        project_manager.update_project(project_file, {"project_link": project_link})
            
            prompt_input_selector = 'textarea[placeholder*="Generate a video"]'
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
            
            has_add_to_scene = await browser_automation.evaluate("""
                () => {
                    const html = document.documentElement.outerHTML;
                    return html.includes('Add to scene') || html.includes('add to scene');
                }
            """)
            
            if not has_add_to_scene:
                max_wait = 60
                waited = 0
                while not has_add_to_scene and waited < max_wait:
                    await asyncio.sleep(2)
                    waited += 2
                    has_add_to_scene = await browser_automation.evaluate("""
                        () => {
                            const html = document.documentElement.outerHTML;
                            return html.includes('Add to scene') || html.includes('add to scene');
                        }
                    """)
            
            video_url = await browser_automation.evaluate("""
                () => {
                    const video = document.querySelector('video, [data-video], .video-result');
                    return video ? video.src || video.getAttribute('src') : null;
                }
            """)
            
            return {
                "video_url": video_url,
                "success": has_add_to_scene,
                "project_link": project_config.get("project_link", "")
            }
            
        except Exception as e:
            print(f"Error in browser automation: {e}")
            return {
                "video_url": None,
                "success": False,
                "error": str(e),
                "project_link": project_config.get("project_link", "")
            }
    
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
    
    async def retry_video(self, prompt: str, project_config: Dict[str, Any], use_browser: bool = True) -> Dict[str, Any]:
        scene_id = f"scene_retry"
        try:
            if use_browser:
                video_result = await self.generate_video_via_browser(prompt, project_config)
                if isinstance(video_result, dict):
                    video_url = video_result.get("video_url")
                    success = video_result.get("success", False)
                    project_link = video_result.get("project_link", "")
                    
                    if project_link and not project_config.get("project_link"):
                        project_config["project_link"] = project_link
                        from ..data.project_manager import project_manager
                        project_file = project_config.get("file", "")
                        if project_file:
                            project_manager.update_project(project_file, {"project_link": project_link})
                    
                    return {
                        "scene_id": scene_id,
                        "prompt": prompt,
                        "status": "SUCCESSFUL" if success and video_url else "FAILED",
                        "video_url": video_url,
                        "video_path": None,
                        "project_link": project_link
                    }
                else:
                    return {
                        "scene_id": scene_id,
                        "prompt": prompt,
                        "status": "FAILED",
                        "video_url": None,
                        "video_path": None
                    }
            else:
                video_url = await self.generate_video_via_api(prompt, project_config)
                return {
                    "scene_id": scene_id,
                    "prompt": prompt,
                    "status": "SUCCESSFUL" if video_url else "FAILED",
                    "video_url": video_url,
                    "video_path": None
                }
        except Exception as e:
            return {
                "scene_id": scene_id,
                "prompt": prompt,
                "status": "FAILED",
                "error": str(e),
                "video_url": None,
                "video_path": None
            }
    
    async def generate_videos(self, prompts: List[str], project_config: Dict[str, Any], use_browser: bool = True) -> List[Dict[str, Any]]:
        results = []
        
        for i, prompt in enumerate(prompts):
            scene_id = f"scene_{i+1}"
            try:
                if use_browser:
                    video_result = await self.generate_video_via_browser(prompt, project_config)
                    if isinstance(video_result, dict):
                        video_url = video_result.get("video_url")
                        success = video_result.get("success", False)
                        project_link = video_result.get("project_link", "")
                        
                        if project_link and not project_config.get("project_link"):
                            project_config["project_link"] = project_link
                            from ..data.project_manager import project_manager
                            project_file = project_config.get("file", "")
                            if project_file:
                                project_manager.update_project(project_file, {"project_link": project_link})
                        
                        results.append({
                            "scene_id": scene_id,
                            "prompt": prompt,
                            "status": "SUCCESSFUL" if success and video_url else "FAILED",
                            "video_url": video_url,
                            "video_path": None,
                            "project_link": project_link
                        })
                    else:
                        results.append({
                            "scene_id": scene_id,
                            "prompt": prompt,
                            "status": "FAILED",
                            "video_url": None,
                            "video_path": None
                        })
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

