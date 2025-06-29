import subprocess
import json
import re
from .debug_logger import DebugLogger


def check_test_mode(prompt, verbose=False):
    """Check if we're in test mode and return mock response if available"""
    try:
        import os
        import sys
        test_mode = os.environ.get('GH_UTILS_TEST_MODE')
        
        if verbose:
            print(f"🤖 ClaudeCLI: TEST_MODE={test_mode}")
        
        if test_mode == '1':
            # Import from test framework
            test_framework_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'test_framework')
            
            if verbose:
                print(f"🤖 ClaudeCLI: test_framework_path={test_framework_path}")
                print(f"🤖 ClaudeCLI: path_exists={os.path.exists(test_framework_path)}")
            
            if os.path.exists(test_framework_path) and test_framework_path not in sys.path:
                sys.path.append(test_framework_path)
            
            from ai_mocking import AIMockingManager
            mock_result = AIMockingManager.get_test_mode_response(prompt)
            
            if verbose:
                print(f"🤖 ClaudeCLI: mock_result={bool(mock_result)}")
            
            if mock_result:
                if verbose:
                    print(f"🤖 ClaudeCLI: Returning mock response")
                return mock_result
                
    except Exception as e:
        if verbose:
            print(f"🤖 ClaudeCLI: Exception in test mode: {e}")
        # If anything fails with test mode, continue with normal operation
        pass
    
    return None


class ClaudeCLIProvider:
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.debug_logger = DebugLogger(config_manager)
        claude_path = config_manager.get_claude_cli_path()
        self.claude_cmd = [claude_path, "--print", "--output-format", "stream-json", "--verbose"]
        
        # Integrated cost tracking
        self.total_cost = 0.0
        self.total_tokens = {'input': 0, 'output': 0}
    
    def generate_summary(self, prompt: str) -> dict:
        """Generate summary using Claude CLI"""
        # Check if we're in test mode first
        mock_result = check_test_mode(prompt, verbose=True)
        if mock_result:
            return mock_result
        
        print(f"🤖 ClaudeCLI: Making real AI call (test mode not detected)")
        summary = self._call_claude(prompt)
        
        # Estimate cost for Claude CLI (rough estimation)
        # Claude 3.5 Sonnet pricing: $3/MTok input, $15/MTok output
        input_tokens = len(prompt) // 4  # rough estimation: 4 chars per token
        output_tokens = len(summary) // 4
        input_cost = input_tokens * 3 / 1_000_000
        output_cost = output_tokens * 15 / 1_000_000
        total_cost = input_cost + output_cost
        
        cost_info = {
            'input_tokens': input_tokens,
            'output_tokens': output_tokens,
            'total_tokens': input_tokens + output_tokens,
            'estimated_cost': total_cost,
            'provider': 'Claude CLI (estimated)'
        }
        
        # Track usage
        self.track_usage(input_tokens, output_tokens)
        
        return {
            'summary': summary,
            'cost_info': cost_info
        }
    
    def track_usage(self, input_tokens, output_tokens):
        """Integrated cost tracking"""
        self.total_tokens['input'] += input_tokens
        self.total_tokens['output'] += output_tokens
        # Claude Sonnet 4 pricing: $3/$15 per MTok
        input_cost = input_tokens * 3 / 1_000_000
        output_cost = output_tokens * 15 / 1_000_000
        self.total_cost += input_cost + output_cost
    
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
    
    def get_total_cost_info(self):
        """Get total cost information as dict"""
        return {
            'estimated_cost': self.total_cost,
            'total_tokens': self.total_tokens['input'] + self.total_tokens['output']
        }
    
    def reset(self):
        """Reset cost tracking"""
        self.total_cost = 0.0
        self.total_tokens = {'input': 0, 'output': 0}
    
    def _call_claude(self, prompt):
        """Execute Claude CLI with subprocess using piped input"""
        try:
            cmd = self.claude_cmd
            self.debug_logger.debug(f"Executing Claude command: {' '.join(cmd)} [prompt_length={len(prompt)}]")
            self.debug_logger.debug(f"Using piped input (stdin) for prompt")
            self.debug_logger.debug(f"Claude CLI path exists: {subprocess.run(['ls', '-la', self.claude_cmd[0]], capture_output=True).returncode == 0}")
            self.debug_logger.debug("Starting Claude subprocess...")
            
            result = subprocess.run(
                cmd,
                input=prompt,
                capture_output=True,
                text=True,
                timeout=self.config_manager.get_ai_timeout()
            )
            
            self.debug_logger.debug(f"Claude subprocess completed with return code: {result.returncode}")
            self.debug_logger.debug(f"Claude stdout length: {len(result.stdout)}")
            self.debug_logger.debug(f"Claude stderr length: {len(result.stderr)}")
            
            if result.returncode != 0:
                self.debug_logger.debug(f"Claude stderr: {result.stderr[:200]}")
                return f"Error generating summary: {result.stderr}"
            
            return self._parse_stream_json_output(result.stdout)
        except subprocess.TimeoutExpired:
            self.debug_logger.debug(f"Claude CLI timed out after {self.config_manager.get_ai_timeout()}s")
            return "Summary generation timed out"
        except Exception as e:
            self.debug_logger.debug(f"Exception calling Claude: {str(e)}")
            return f"Error calling Claude: {str(e)}"
    
    def _parse_stream_json_output(self, raw_output):
        """Parse stream-json output from Claude CLI"""
        try:
            content_parts = []
            lines = raw_output.strip().split('\n')
            
            self.debug_logger.debug(f"Parsing {len(lines)} JSON lines from stream output")
            self.debug_logger.debug(f"Raw output preview: {raw_output[:500]}...")
            
            for line in lines:
                if not line.strip():
                    continue
                    
                try:
                    json_obj = json.loads(line)
                    
                    self.debug_logger.debug(f"JSON object keys: {list(json_obj.keys())}")
                    self.debug_logger.debug(f"JSON object: {json_obj}")
                    
                    if json_obj.get('type') == 'result' and 'result' in json_obj:
                        content_parts = [json_obj['result']]
                        self.debug_logger.debug(f"Found result: {json_obj['result'][:100]}...")
                        break
                    elif json_obj.get('type') == 'assistant' and 'message' in json_obj and not content_parts:
                        message = json_obj['message']
                        if 'content' in message and isinstance(message['content'], list):
                            for item in message['content']:
                                if isinstance(item, dict) and item.get('type') == 'text' and 'text' in item:
                                    content_parts.append(item['text'])
                                    self.debug_logger.debug(f"Found assistant content: {item['text'][:100]}...")
                    elif not content_parts and 'content' in json_obj:
                        if isinstance(json_obj['content'], list):
                            for item in json_obj['content']:
                                if isinstance(item, dict) and 'text' in item:
                                    content_parts.append(item['text'])
                                elif isinstance(item, str):
                                    content_parts.append(item)
                        elif isinstance(json_obj['content'], str):
                            content_parts.append(json_obj['content'])
                    elif not content_parts and 'text' in json_obj:
                        content_parts.append(json_obj['text'])
                    elif not content_parts and 'message' in json_obj and isinstance(json_obj['message'], str):
                        content_parts.append(json_obj['message'])
                        
                except json.JSONDecodeError as e:
                    self.debug_logger.debug(f"Failed to parse JSON line: {line[:100]}... Error: {e}")
                    content_parts.append(line)
            
            result = ''.join(content_parts).strip()
            result = self._strip_markdown(result)
            
            self.debug_logger.debug(f"Extracted {len(result)} characters from stream-json")
            
            return result if result else "No content received from Claude"
            
        except Exception as e:
            self.debug_logger.debug(f"Error parsing stream-json: {e}")
            return raw_output.strip() if raw_output.strip() else "Error parsing Claude response"
    
    def _strip_markdown(self, text):
        """Strip markdown formatting for terminal output"""
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
        text = re.sub(r'\*(.*?)\*', r'\1', text)
        text = re.sub(r'^#+\s*', '', text, flags=re.MULTILINE)
        text = re.sub(r'```[\s\S]*?```', '', text)
        text = re.sub(r'`(.*?)`', r'\1', text)
        # Remove empty lines and excessive whitespace
        text = re.sub(r'\n\s*\n', '\n', text)
        text = re.sub(r'^\s+|\s+$', '', text, flags=re.MULTILINE)
        return text


class OpenAIProvider:
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.debug_logger = DebugLogger(config_manager)
        self.api_key = config_manager.get_openai_api_key()
        self.model = config_manager.get_ai_model() or 'gpt-4o'
        self.timeout = config_manager.get_ai_timeout()
        
        # Integrated cost tracking
        self.total_cost = 0.0
        self.total_tokens = {'input': 0, 'output': 0}
        
        if not self.api_key:
            raise ValueError(
                "OpenAI API key not found. Please add to config.txt:\n"
                "[openai]\n"
                "api_key = sk-..."
            )
    
    def generate_summary(self, prompt: str) -> dict:
        """Generate summary using OpenAI API"""
        # Check if we're in test mode first
        mock_result = check_test_mode(prompt, verbose=False)
        if mock_result:
            return mock_result
        
        try:
            import openai
            
            self.debug_logger.debug(f"Using OpenAI model: {self.model}")
            self.debug_logger.debug(f"Prompt length: {len(prompt)} characters")
            self.debug_logger.debug(f"Timeout: {self.timeout} seconds")
            
            client = openai.OpenAI(api_key=self.api_key, timeout=self.timeout)
            
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that summarizes GitHub repository activity. Provide concise, terminal-friendly summaries without markdown formatting."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            result = response.choices[0].message.content.strip()
            
            # Calculate actual cost using real token usage
            cost_info = self._calculate_openai_cost(response, self.model)
            
            # Track usage
            self.track_usage(cost_info['input_tokens'], cost_info['output_tokens'])
            
            self.debug_logger.debug(f"OpenAI response length: {len(result)} characters")
            self.debug_logger.debug_tokens(cost_info['total_tokens'], cost_info['estimated_cost'])
            
            return {
                'summary': result if result else "No content received from OpenAI",
                'cost_info': cost_info
            }
            
        except ImportError:
            return {
                'summary': "Error: OpenAI library not installed. Run: pip install openai",
                'cost_info': {'estimated_cost': 0, 'provider': 'OpenAI (error)', 'total_tokens': 0}
            }
        except Exception as e:
            self.debug_logger.debug(f"OpenAI API error: {str(e)}")
            return {
                'summary': f"Error calling OpenAI API: {str(e)}",
                'cost_info': {'estimated_cost': 0, 'provider': 'OpenAI (error)', 'total_tokens': 0}
            }
    
    def track_usage(self, input_tokens, output_tokens):
        """Integrated cost tracking"""
        self.total_tokens['input'] += input_tokens
        self.total_tokens['output'] += output_tokens
        
        # Calculate cost based on model
        pricing = {
            'gpt-4o': {'input': 3.00, 'output': 10.00},
            'gpt-4o-mini': {'input': 0.15, 'output': 0.60},
            'gpt-4': {'input': 30.00, 'output': 60.00},
            'gpt-3.5-turbo': {'input': 0.50, 'output': 1.50}
        }
        model_pricing = pricing.get(self.model, pricing['gpt-4o-mini'])
        input_cost = input_tokens * model_pricing['input'] / 1_000_000
        output_cost = output_tokens * model_pricing['output'] / 1_000_000
        self.total_cost += input_cost + output_cost
    
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
    
    def get_total_cost_info(self):
        """Get total cost information as dict"""
        return {
            'estimated_cost': self.total_cost,
            'total_tokens': self.total_tokens['input'] + self.total_tokens['output']
        }
    
    def reset(self):
        """Reset cost tracking"""
        self.total_cost = 0.0
        self.total_tokens = {'input': 0, 'output': 0}
    
    def _calculate_openai_cost(self, response, model):
        """Calculate cost based on OpenAI pricing"""
        if not response.usage:
            return {'estimated_cost': 0, 'provider': 'OpenAI (no usage data)', 'total_tokens': 0}
        
        # OpenAI pricing (as of December 2024) - per 1M tokens
        pricing = {
            'gpt-4o': {'input': 3.00, 'output': 10.00},
            'gpt-4o-mini': {'input': 0.15, 'output': 0.60},
            'gpt-4': {'input': 30.00, 'output': 60.00},
            'gpt-3.5-turbo': {'input': 0.50, 'output': 1.50}
        }
        
        # Default to gpt-4o-mini pricing if model not found
        model_pricing = pricing.get(model, pricing['gpt-4o-mini'])
        
        input_cost = response.usage.prompt_tokens * model_pricing['input'] / 1_000_000
        output_cost = response.usage.completion_tokens * model_pricing['output'] / 1_000_000
        total_cost = input_cost + output_cost
        
        return {
            'input_tokens': response.usage.prompt_tokens,
            'output_tokens': response.usage.completion_tokens,
            'total_tokens': response.usage.total_tokens,
            'estimated_cost': total_cost,
            'provider': f'OpenAI {model}'
        }


def create_ai_provider(config_manager):
    """Factory function to create AI provider based on configuration"""
    provider_type = config_manager.get_ai_provider()
    
    if provider_type.lower() == 'openai':
        return OpenAIProvider(config_manager)
    else:
        return ClaudeCLIProvider(config_manager)