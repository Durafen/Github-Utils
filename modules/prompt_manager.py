import os

class PromptManager:
    """Centralized prompt template management"""
    
    def __init__(self, template_name):
        self.template_name = template_name
        self.template = self._load_template()
    
    def _load_template(self):
        """Load prompt template from file"""
        prompt_file = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 
            'prompts', 
            f'{self.template_name}_prompt.txt'
        )
        try:
            with open(prompt_file, 'r') as f:
                return f.read().strip()
        except FileNotFoundError:
            raise FileNotFoundError(f"Prompt template not found: {prompt_file}")
    
    def build_prompt(self, **kwargs):
        """Build prompt by substituting template variables"""
        try:
            return self.template.format(**kwargs)
        except KeyError as e:
            raise ValueError(f"Missing template variable: {e}")