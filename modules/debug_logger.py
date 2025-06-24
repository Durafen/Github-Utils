class DebugLogger:
    """Centralized debug logging utility"""
    
    def __init__(self, config_manager):
        self.config_manager = config_manager
    
    def _is_debug_enabled(self):
        """Check if debug is enabled"""
        return self.config_manager.get_boolean_setting('debug')
    
    def debug(self, message):
        """Print debug message if debug mode is enabled"""
        if self._is_debug_enabled():
            print(f"DEBUG: {message}")
    
    
    def debug_tokens(self, tokens_used, estimated_cost=None):
        """Debug token usage information"""
        if self._is_debug_enabled():
            if estimated_cost:
                print(f"DEBUG: Tokens used: {tokens_used}, Estimated cost: ${estimated_cost:.6f}")
            else:
                print(f"DEBUG: Tokens used: {tokens_used}")
    
    def debug_full_prompt(self, prompt, repo_name, prompt_type="summary"):
        """Save full prompt content to a debug file"""
        # Check for debug_prompt setting specifically, independent of general debug
        debug_prompt_enabled = self.config_manager.get_boolean_setting('debug_prompt', False)
        if self._is_debug_enabled() or debug_prompt_enabled:
            import os
            from datetime import datetime
            
            # Create debug directory if it doesn't exist
            debug_dir = "debug_prompts"
            if not os.path.exists(debug_dir):
                os.makedirs(debug_dir)
            
            # Generate filename with timestamp and repo name
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_repo_name = repo_name.replace("/", "_").replace(" ", "_")
            filename = f"{debug_dir}/{timestamp}_{safe_repo_name}_{prompt_type}_prompt.txt"
            
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(f"# Full AI Prompt for {repo_name}\n")
                    f.write(f"# Generated at: {datetime.now().isoformat()}\n")
                    f.write(f"# Prompt type: {prompt_type}\n")
                    f.write(f"# Prompt length: {len(prompt)} characters\n")
                    f.write("# " + "="*60 + "\n\n")
                    f.write(prompt)
                
                # Only print debug messages if general debug is enabled
                if self._is_debug_enabled():
                    print(f"DEBUG: Full prompt saved to {filename}")
                    print(f"DEBUG: Prompt length: {len(prompt)} characters")
            except Exception as e:
                print(f"DEBUG: Failed to save prompt to file: {e}")