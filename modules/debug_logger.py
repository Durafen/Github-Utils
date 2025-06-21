class DebugLogger:
    """Centralized debug logging utility"""
    
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self._debug_enabled = None
    
    def _is_debug_enabled(self):
        """Check if debug is enabled (cached for performance)"""
        if self._debug_enabled is None:
            self._debug_enabled = self.config_manager.get_boolean_setting('debug')
        return self._debug_enabled
    
    def debug(self, message):
        """Print debug message if debug mode is enabled"""
        if self._is_debug_enabled():
            print(f"DEBUG: {message}")
    
    def debug_api_call(self, endpoint, params=None):
        """Debug API call information"""
        if self._is_debug_enabled():
            if params:
                print(f"DEBUG: API call to {endpoint} with params: {params}")
            else:
                print(f"DEBUG: API call to {endpoint}")
    
    def debug_tokens(self, tokens_used, estimated_cost=None):
        """Debug token usage information"""
        if self._is_debug_enabled():
            if estimated_cost:
                print(f"DEBUG: Tokens used: {tokens_used}, Estimated cost: ${estimated_cost:.6f}")
            else:
                print(f"DEBUG: Tokens used: {tokens_used}")