import re
import os
from typing import Dict, List, Optional, Tuple


class CommentPreservingINIParser:
    """
    A custom INI parser that preserves all comments, formatting, and whitespace
    while allowing modifications to specific sections (primarily [repositories]).
    """
    
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.lines: List[str] = []
        self.repo_section_start: Optional[int] = None
        self.repo_section_end: Optional[int] = None
        self.repositories: Dict[str, str] = {}
        
    def parse_file(self) -> None:
        """Parse the INI file, preserving all formatting and identifying repository section."""
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
            
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.lines = f.readlines()
        except Exception as e:
            raise ValueError(f"Error reading config file: {e}")
            
        self._identify_repository_section()
        self._extract_current_repositories()
    
    def _identify_repository_section(self) -> None:
        """Find the start and end lines of the [repositories] section."""
        repo_section_found = False
        
        for i, line in enumerate(self.lines):
            stripped = line.strip()
            
            # Check for [repositories] section header
            if stripped.lower() == '[repositories]':
                self.repo_section_start = i
                repo_section_found = True
                continue
                
            # If we're in repositories section, look for next section or end of file
            if repo_section_found and stripped.startswith('[') and stripped.endswith(']'):
                # Found next section, repositories section ends here
                self.repo_section_end = i
                break
                
        # If no next section found, repositories section goes to end of file
        if repo_section_found and self.repo_section_end is None:
            self.repo_section_end = len(self.lines)
    
    def _extract_current_repositories(self) -> None:
        """Extract current repository entries from the [repositories] section."""
        if self.repo_section_start is None:
            return
            
        start = self.repo_section_start + 1  # Skip section header
        end = self.repo_section_end or len(self.lines)
        
        # Regex to match "name = url" pattern, handling inline comments
        repo_pattern = re.compile(r'^\s*([^=\s#]+)\s*=\s*([^#]+?)(?:\s*#.*)?$')
        
        for i in range(start, end):
            line = self.lines[i]
            match = repo_pattern.match(line)
            if match:
                name = match.group(1).strip()
                url = match.group(2).strip()
                self.repositories[name] = url
    
    def add_repository(self, name: str, url: str) -> None:
        """Add a repository to the configuration."""
        if not name or not url:
            raise ValueError("Repository name and URL cannot be empty")
            
        # Add to our internal repository dict
        self.repositories[name] = url
        
        # Ensure repositories section exists
        if self.repo_section_start is None:
            self._create_repositories_section()
        
        # Update the file lines
        self._update_repository_lines()
    
    def remove_repository(self, identifier: str) -> bool:
        """Remove a repository by name or URL. Returns True if removed, False if not found."""
        # Try to remove by name first
        if identifier in self.repositories:
            del self.repositories[identifier]
            self._update_repository_lines()
            return True
            
        # Try to remove by URL
        for name, url in list(self.repositories.items()):
            if url == identifier:
                del self.repositories[name]
                self._update_repository_lines()
                return True
                
        return False
    
    def _create_repositories_section(self) -> None:
        """Create a [repositories] section if it doesn't exist."""
        # Add section at the end of file with proper spacing
        if self.lines and not self.lines[-1].endswith('\n'):
            self.lines.append('\n')
        
        # Add blank line before section if file isn't empty
        if self.lines:
            self.lines.append('\n')
            
        self.lines.append('[repositories]\n')
        self.repo_section_start = len(self.lines) - 1
        self.repo_section_end = len(self.lines)
    
    def _update_repository_lines(self) -> None:
        """Update the repository lines in the file while preserving everything else."""
        if self.repo_section_start is None:
            return
            
        start = self.repo_section_start + 1  # Skip section header
        end = self.repo_section_end or len(self.lines)
        
        # Preserve comments and blank lines within the repositories section
        preserved_lines = []
        repo_pattern = re.compile(r'^\s*([^=\s#]+)\s*=\s*([^#]+?)(?:\s*#.*)?$')
        
        for i in range(start, end):
            line = self.lines[i]
            # If it's not a repository line (comment, blank line, etc.), preserve it
            if not repo_pattern.match(line):
                preserved_lines.append(line)
        
        # Build new repository section content
        new_repo_lines = []
        
        # Add preserved non-repository lines first
        new_repo_lines.extend(preserved_lines)
        
        # Add current repositories in sorted order for consistency
        for name in sorted(self.repositories.keys()):
            url = self.repositories[name]
            new_repo_lines.append(f"{name} = {url}\n")
        
        # Replace the repository section content
        self.lines[start:end] = new_repo_lines
        
        # Update section end pointer
        self.repo_section_end = self.repo_section_start + 1 + len(new_repo_lines)
    
    def save_file(self) -> None:
        """Save the file with all preserved comments and formatting."""
        try:
            # Create backup of original file
            backup_path = f"{self.config_path}.backup"
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as src:
                    with open(backup_path, 'w', encoding='utf-8') as dst:
                        dst.write(src.read())
            
            # Write the updated content
            with open(self.config_path, 'w', encoding='utf-8') as f:
                f.writelines(self.lines)
                
            # Remove backup if write was successful
            if os.path.exists(backup_path):
                os.remove(backup_path)
                
        except Exception as e:
            # Restore from backup if save failed
            backup_path = f"{self.config_path}.backup"
            if os.path.exists(backup_path):
                os.rename(backup_path, self.config_path)
            raise ValueError(f"Error saving config file: {e}")
    
    def get_repositories(self) -> Dict[str, str]:
        """Get current repositories dictionary."""
        return self.repositories.copy()