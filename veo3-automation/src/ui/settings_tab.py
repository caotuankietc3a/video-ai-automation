import customtkinter as ctk
from ..data.config_manager import config_manager

class SettingsTab(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.pack(fill="both", expand=True, padx=20, pady=20)
        self._setup_ui()
    
    def _setup_ui(self):
        title = ctk.CTkLabel(self, text="Cài đặt", font=ctk.CTkFont(size=20, weight="bold"))
        title.pack(pady=20)
        
        api_keys_frame = ctk.CTkFrame(self)
        api_keys_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(api_keys_frame, text="API Keys", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        gemini_frame = ctk.CTkFrame(api_keys_frame)
        gemini_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(gemini_frame, text="Gemini API Key:").pack(side="left", padx=5)
        self.gemini_key_entry = ctk.CTkEntry(gemini_frame, width=400, show="*")
        self.gemini_key_entry.insert(0, config_manager.get_api_key("gemini"))
        self.gemini_key_entry.pack(side="left", fill="x", expand=True, padx=5)
        
        openai_frame = ctk.CTkFrame(api_keys_frame)
        openai_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(openai_frame, text="OpenAI API Key:").pack(side="left", padx=5)
        self.openai_key_entry = ctk.CTkEntry(openai_frame, width=400, show="*")
        self.openai_key_entry.insert(0, config_manager.get_api_key("openai"))
        self.openai_key_entry.pack(side="left", fill="x", expand=True, padx=5)
        
        anthropic_frame = ctk.CTkFrame(api_keys_frame)
        anthropic_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(anthropic_frame, text="Anthropic API Key:").pack(side="left", padx=5)
        self.anthropic_key_entry = ctk.CTkEntry(anthropic_frame, width=400, show="*")
        self.anthropic_key_entry.insert(0, config_manager.get_api_key("anthropic"))
        self.anthropic_key_entry.pack(side="left", fill="x", expand=True, padx=5)
        
        save_btn = ctk.CTkButton(api_keys_frame, text="Lưu cấu hình", command=self._save_all)
        save_btn.pack(pady=20)

        cg_frame = ctk.CTkFrame(self)
        cg_frame.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(cg_frame, text="Content generation", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)

        use_browser_frame = ctk.CTkFrame(cg_frame)
        use_browser_frame.rowconfigure(0, weight=1)
        use_browser_frame.columnconfigure(1, weight=1)
        use_browser_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(
            use_browser_frame,
            text="Dùng Gemini Web (Chromium) cho VIDEO_TO_CONTENT:",
        ).grid(row=0, column=0, sticky="w", padx=5)
        self.use_browser_var = ctk.BooleanVar(
            value=bool(config_manager.get("content_generation.use_browser", True)),
        )
        use_browser_switch = ctk.CTkSwitch(
            use_browser_frame,
            text="",
            variable=self.use_browser_var,
        )
        use_browser_switch.grid(row=0, column=1, sticky="w")

        url_frame = ctk.CTkFrame(cg_frame)
        url_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(url_frame, text="URL Gemini/Flow:").pack(side="left", padx=5)
        self.cg_url_entry = ctk.CTkEntry(url_frame)
        self.cg_url_entry.insert(
            0,
            config_manager.get(
                "content_generation.url",
                "https://gemini.google.com/app",
            ),
        )
        self.cg_url_entry.pack(side="left", fill="x", expand=True, padx=5)
    
    def _save_all(self):
        config_manager.set_api_key("gemini", self.gemini_key_entry.get())
        config_manager.set_api_key("openai", self.openai_key_entry.get())
        config_manager.set_api_key("anthropic", self.anthropic_key_entry.get())
        config_manager.set("content_generation.use_browser", bool(self.use_browser_var.get()))
        config_manager.set("content_generation.url", self.cg_url_entry.get().strip())

