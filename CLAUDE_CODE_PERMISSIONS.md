# Claude Code Permissions and Capabilities

## Environment Information
- **Working Directory**: `C:\Users\adamc\OneDrive\Development\CLO System AI`
- **Platform**: Windows 10 (win32)
- **Git Repository**: Yes (main branch)
- **Date**: 2025-08-16

## File System Permissions

### Read Access
- ✅ **Read any file** in the project directory and subdirectories
- ✅ **List directories** with absolute paths
- ✅ **Search files** using glob patterns and grep
- ✅ **View file contents** including images, PDFs, and Jupyter notebooks
- ✅ **Access temporary files** and screenshots

### Write Access
- ✅ **Create new files** (though discouraged unless necessary)
- ✅ **Edit existing files** with precise string replacements
- ✅ **Multi-edit files** with multiple changes in one operation
- ✅ **Edit Jupyter notebooks** with cell-level modifications
- ✅ **Overwrite existing files** with Write tool

## Command Execution Permissions

### Bash Commands (Pre-approved)
- ✅ **Python execution**: `python:*`
- ✅ **Git operations**: `git add:*`, `git push:*`, `git checkout:*`, `git commit:*`, `git rm:*`
- ✅ **Docker commands**: `docker:*`
- ✅ **Package management**: `pip install:*`, `npm install:*`, `npm start`, `npm run build:*`, `npm test:*`
- ✅ **File operations**: `touch:*`, `find:*`, `grep:*`, `rm:*`, `rg:*`, `mkdir:*`, `mv:*`, `cat:*`
- ✅ **Development servers**: Various port configurations for npm start
- ✅ **TypeScript**: `npx tsc:*`, `npx eslint:*`
- ✅ **Virtual environments**: `venv\Scripts\activate:*`, activation scripts
- ✅ **System utilities**: `sed:*`, `curl:*`, `tasklist:*`, `taskkill:*`
- ✅ **Windows commands**: `cmd /c:*`, `call:*`, `set:*`, `timeout:*`, `dir:*`, `powershell:*`
- ✅ **Background execution**: Can run commands in background with monitoring

### Web Access
- ✅ **Web search** capability (US only)
- ✅ **Web fetch** from any URL with AI processing
- ✅ **MCP web tools** when available (preferred)

## Development Tools Access

### Code Analysis
- ✅ **Glob pattern matching** for file discovery
- ✅ **Grep/ripgrep** for code searching with regex
- ✅ **Multi-file searches** with parallel execution
- ✅ **Code diagnostics** via VS Code integration
- ✅ **Type checking** and linting capabilities

### Task Management
- ✅ **Todo list management** for tracking complex tasks
- ✅ **Multi-step task planning** and execution
- ✅ **Progress tracking** with status updates
- ✅ **Specialized agents** for complex operations

### Version Control
- ✅ **Git status, diff, log** operations
- ✅ **Branch management** and switching
- ✅ **Commit creation** with automated messages
- ✅ **Pull request creation** via GitHub CLI
- ✅ **Repository analysis** and history review

## Database and Infrastructure

### Docker Services
- ✅ **Start/stop containers** (PostgreSQL, Redis)
- ✅ **Container management** via docker-compose
- ✅ **Service health monitoring**

### Development Servers
- ✅ **Backend server startup** (Python FastAPI)
- ✅ **Frontend server startup** (React development)
- ✅ **Multiple port configurations**
- ✅ **Background service monitoring**

## Security and Compliance

### Security Restrictions
- ❌ **Malicious code creation** - Refused
- ❌ **Offensive security tools** - Not permitted
- ✅ **Defensive security analysis** - Allowed
- ✅ **Vulnerability documentation** - Permitted
- ✅ **Security best practices** - Encouraged

### Financial Data Handling
- ✅ **Read financial data** for analysis
- ✅ **Process CLO calculations** and models
- ✅ **Generate reports** and analytics
- ✅ **Handle sensitive data** with security awareness
- ❌ **Expose secrets** or credentials

## Current Project Context

### CLO System Permissions
- ✅ **Full system access** to CLO Management System
- ✅ **Database operations** via application layer
- ✅ **Asset management** and portfolio analytics
- ✅ **Waterfall calculations** and financial modeling
- ✅ **User authentication** system management
- ✅ **Real-time data** processing and WebSocket handling

### Testing and Validation
- ✅ **Run comprehensive tests** (1,100+ test suite)
- ✅ **Execute integration tests**
- ✅ **Performance validation**
- ✅ **Security assessment**
- ✅ **Code quality checks**

## Limitations and Constraints

### System Limitations
- ❌ **Cannot modify git config**
- ❌ **No interactive commands** (git rebase -i, git add -i)
- ❌ **Limited to 10-minute command timeout**
- ❌ **Cannot push to remote** unless explicitly requested

### Best Practices
- ✅ **Prefer editing** over creating new files
- ✅ **Follow existing code conventions**
- ✅ **Use absolute paths** for file operations
- ✅ **Batch tool calls** for performance
- ✅ **Proactive todo list usage**

## Environment Variables and Configuration

### Accessible Services
- **PostgreSQL**: `postgresql://postgres:adamchaz@127.0.0.1:5433/clo_dev`
- **Redis**: `redis://127.0.0.1:6379`
- **Frontend**: `http://localhost:3000`
- **Backend API**: `http://localhost:8000`
- **API Docs**: `http://localhost:8000/docs`

### Development Tools
- **Virtual Environment**: `backend\venv\Scripts\activate`
- **Docker Compose**: `infrastructure\docker\docker-compose.yml`
- **Package Management**: npm, pip, Docker
- **Code Quality**: ESLint, TypeScript, Ruff (if available)

---

*This document reflects Claude Code's current permissions and capabilities in the CLO Management System development environment as of 2025-08-16.*