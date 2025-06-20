# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a GitHub utilities repository focused on building tools for monitoring and analyzing GitHub repositories. The main project is a **GitHub News Summary App** that tracks repository changes and generates AI-powered summaries.

## Architecture

The project follows a modular design with clear separation of concerns:

### Core Components
- **GitHubFetcher**: Uses GitHub CLI (`gh api`) for data retrieval instead of direct API calls
- **SummaryGenerator**: Integrates with Claude CLI for AI summarization
- **ConfigManager**: Handles JSON-based configuration and state persistence
- **Display**: Terminal output formatting and user interface

### Data Flow
1. Load repository list from `config.json`
2. Check last processed state from `state.json` 
3. Fetch new commits/releases since last check using GitHub CLI
4. Generate summaries via Claude CLI with structured prompts
5. Display results and update state for next run

## Key Design Decisions

**GitHub CLI Over Direct API**: Uses `gh api` commands instead of requests library for:
- No rate limiting concerns (5,000/hour vs 60/hour)
- Automatic authentication handling
- Richer commit data (signatures, verification, parent commits)
- Zero external Python dependencies

**Incremental Processing**: Tracks last processed commit SHA per repository to avoid reprocessing data.

**State Persistence**: JSON-based state management for resuming across runs.

## Implementation Details

The main implementation plan is documented in `github-news-checker-init.md` which contains:
- Complete class structure and method signatures
- Configuration file formats
- Test strategy and manual testing checklist
- MVP implementation priorities

## Dependencies

- **GitHub CLI**: Must be installed and authenticated (`gh auth login`)
- **Claude CLI**: Required for AI summarization functionality
- **Python Standard Library**: No external Python packages required

## Development Workflow

This is currently a planning/design repository. The actual implementation should follow the detailed plan in `github-news-checker-init.md`.

When implementing:
1. Start with MVP focusing on single repository (ccusage)
2. Implement core GitHub CLI integration first
3. Add basic Claude CLI integration
4. Expand to multiple repositories via config.json
5. Enhance terminal output and error handling