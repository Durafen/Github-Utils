class CostTracker:
    """Utility for tracking and formatting AI cost information"""
    
    def __init__(self):
        self.total_cost = 0
        self.total_tokens = 0
    
    
    def get_total_cost_info(self):
        """Get total cost information as dict"""
        return {
            'estimated_cost': self.total_cost,
            'total_tokens': self.total_tokens
        }
    
    def format_cost_info(self, cost_info):
        """Format cost information for display"""
        if not cost_info or cost_info.get('estimated_cost', 0) == 0:
            return ""
        
        cost = cost_info['estimated_cost']
        tokens = cost_info.get('total_tokens', 0)
        
        if cost < 0.001:
            return f"($<0.001, {tokens} tokens)"
        else:
            return f"(${cost:.3f}, {tokens} tokens)"
    
    def reset(self):
        """Reset cost tracking"""
        self.total_cost = 0
        self.total_tokens = 0