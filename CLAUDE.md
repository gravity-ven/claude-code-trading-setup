# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 🏆 PLATINUM RULE (HIGHEST PRIORITY)
**USE AGENTS AND THEIR SKILLS FOR EVERY PROMPT AND TASK**
- The skill system MUST be consulted before starting any task
- Meta-orchestrator skill AUTOMATICALLY analyzes every prompt
- Agent-skills-system provides recursive self-improvement capability
- NO task should be executed without checking available skills first
- Skills compound learning across all 360+ agent instances

---

## 🛡️ AUTONOMOUS SLASH COMMANDS (AUTO-EXECUTE)

**CRITICAL**: The following slash commands MUST be executed IMMEDIATELY without asking questions.

### /damage-control and /dc Commands

When user types `/damage-control` or `/dc` followed by any subcommand, **IMMEDIATELY execute**:

```bash
python3 /mnt/c/Users/Quantum/.claude/hooks/damage-control/manage.py <subcommand> [args]
```

| User Input | Execute Immediately |
|------------|---------------------|
| `/dc` or `/damage-control` | `manage.py status` |
| `/dc status` | `manage.py status` |
| `/dc list` | `manage.py list` |
| `/dc test` | `manage.py test` |
| `/dc add-block "pattern"` | `manage.py add-block "pattern"` |
| `/dc add-ask "pattern" "reason"` | `manage.py add-ask "pattern" "reason"` |
| `/dc remove-block "pattern"` | `manage.py remove-block "pattern"` |
| `/dc protect "path" "level"` | `manage.py protect "path" "level"` |

**Rules**:
1. **NO confirmation needed** - execute immediately
2. **NO explanations first** - just run the command
3. **Show output** - display the results after execution
4. **Handle errors** - if command fails, show the error

### /finance-llm Commands

When user types `/finance-llm` followed by any action, **IMMEDIATELY execute** the appropriate curl command:

| User Input | Execute Immediately |
|------------|---------------------|
| `/finance-llm` or `/finance-llm analyze` | `curl -s -X POST http://localhost:5005/api/finance-llm/analyze/market -H "Content-Type: application/json" -d '{"provider": "claude"}'` |
| `/finance-llm sentiment [context]` | `curl -s -X POST http://localhost:5005/api/finance-llm/analyze/sentiment -H "Content-Type: application/json" -d '{"provider": "claude", "context": "[context]"}'` |
| `/finance-llm trade [strategy]` | `curl -s -X POST http://localhost:5005/api/finance-llm/analyze/trade-idea -H "Content-Type: application/json" -d '{"provider": "claude", "strategy": "[strategy]"}'` |
| `/finance-llm economic` | `curl -s -X POST http://localhost:5005/api/finance-llm/analyze/economic -H "Content-Type: application/json" -d '{"provider": "claude"}'` |
| `/finance-llm chat "[message]"` | `curl -s -X POST http://localhost:5005/api/finance-llm/chat -H "Content-Type: application/json" -d '{"provider": "claude", "message": "[message]"}'` |
| `/finance-llm health` | `curl -s http://localhost:5005/api/finance-llm/health` |

**Rules**: Same as /damage-control - NO confirmation, execute immediately, show output.

**If API not running**, show:
```
Finance LLM API not running. Start with:
cd /mnt/c/Users/Quantum/Downloads/Spartan_Labs/website && python finance_llm_api.py
```

---

## 💎 DIAMOND RULE: AUTONOMOUS AGENT CHAINING (CRITICAL PRIORITY)

**MANDATORY: APPLY MULTI-AGENT THINKING TO ALL COMPLEX TASKS**

### Auto-Detection Triggers

Claude Code MUST automatically use agent chaining patterns when:

1. ✅ **Multi-step tasks** - Anything requiring 3+ distinct steps
2. ✅ **Code + Review** - Any code implementation needs review pass
3. ✅ **Architecture decisions** - System design or refactoring
4. ✅ **Full features** - New functionality requiring planning
5. ✅ **Bug fixes** - Analysis → Fix → Test → Review pattern
6. ✅ **User says "build"** - Implies Plan → Architect → Code → Review
7. ✅ **User says "improve/refactor"** - Implies Review → Refactor → Test
8. ✅ **User says "analyze"** - Implies Research → Analysis → Recommendations
9. ✅ **Database operations** - Design → Implement → Test → Validate
10. ✅ **API development** - Plan → Design → Implement → Document → Test

### The Agent Chaining Mental Model

For every qualifying task, Claude Code MUST think through these specialized perspectives:

**Phase 1: Planning Layer** 🎯
- **Planner Perspective**: What's the high-level approach?
- **Architect Perspective**: What's the system design?
- **Task Breakdown Perspective**: What are the atomic tasks?

**Phase 2: Implementation Layer** 💻
- **Coder Perspective**: Implement with production quality
- **Tester Perspective**: What tests are needed?

**Phase 3: Quality Layer** 🔍
- **Reviewer Perspective**: What could be improved?
- **Security Perspective**: Are there vulnerabilities?
- **Documenter Perspective**: Is it well-documented?

**Phase 4: Delivery Layer** 📦
- **Git Perspective**: How should this be committed?
- **Integration Perspective**: How does this fit with existing code?

### Execution Pattern

```
AUTOMATIC WORKFLOW (No user prompting required):

1. Receive task → Detect complexity
2. IF complex → Apply agent chaining pattern automatically
3. Show each "agent perspective" as a separate thinking phase
4. Execute in sequence with full context carryover
5. Present final integrated result
```

### Output Format

When using agent chaining, structure responses as:

```markdown
## 🔗 Agent Chain Activated: [Task Name]

### [Phase 1] 🎯 Planning
<high-level strategy and approach>

### [Phase 2] 🏗️ Architecture
<system design decisions>

### [Phase 3] 📋 Task Breakdown
<atomic tasks with dependencies>

### [Phase 4] 💻 Implementation
<production-quality code>

### [Phase 5] 🧪 Testing
<test strategy and implementation>

### [Phase 6] 👀 Review
<quality checks and improvements>

### [Phase 7] 🔒 Security Audit
<security considerations> (if applicable)

### [Phase 8] 📚 Documentation
<documentation updates>

### [Phase 9] 📦 Integration & Delivery
<final result with all artifacts>
```

### When NOT to Use Agent Chaining

❌ Simple single-file reads
❌ Trivial questions ("what does this do?")
❌ Quick information lookups
❌ Basic git status checks
❌ User explicitly says "quick" or "just show me"

### Default Assumption

**IF IN DOUBT, USE AGENT CHAINING**

Complex tasks executed without multi-perspective thinking are incomplete by definition.

### Integration with TodoWrite

When using TodoWrite for complex tasks, structure todos as agent chain phases:

```
✓ Planning phase complete
→ Architecture phase in progress
- Implementation phase pending
- Review phase pending
- Integration phase pending
```

### Example Automatic Activation

**User says**: "Build a user authentication system"

**Claude automatically thinks**:
```
🔗 Agent Chain Activated

🎯 Planner: Need registration, login, logout, JWT tokens, PostgreSQL storage
🏗️ Architect: RESTful API, bcrypt passwords, rate limiting, session management
💻 Implementer: [builds complete system with all components]
👀 Reviewer: [checks for SQL injection, validates input sanitization]
🔒 Security: [audits password storage, token expiry, HTTPS requirements]
📚 Documenter: [creates API documentation]
📦 Integrator: [prepares commit, notes deployment steps]
```

**User receives**: Complete, production-ready authentication system with all layers considered.

### Complexity Detection Keywords

**Automatic triggers** (partial list):
- build, create, implement, add, develop
- refactor, improve, optimize, enhance
- fix, debug, resolve, repair
- analyze, investigate, research, study
- design, architect, plan, structure
- migrate, upgrade, convert, transform
- integrate, connect, combine, merge
- setup, configure, install, deploy

### Special Cases

**Trading Systems**: Always use agent chaining (risk management critical)
**Database Operations**: Always use agent chaining (data integrity critical)
**Security Features**: Always use agent chaining (vulnerability checks mandatory)
**API Development**: Always use agent chaining (contract design critical)

---

## 🤖 SMART AUTONOMOUS MODE (GLOBALLY ENABLED)

**Status**: ✅ **ACTIVE** - Enabled for all Claude Code sessions

### Configuration Files
- **Master Config**: `/mnt/c/Users/Quantum/.claudeconfig`
- **Behavior Instructions**: `/mnt/c/Users/Quantum/.claude/system-prompt.txt`
- **Prompt Expansions**: `/mnt/c/Users/Quantum/.claude/prompt-expansions.json`
- **Documentation**: `/mnt/c/Users/Quantum/SMART_AUTONOMOUS_CONFIG.md`
- **Synced Backup**: `/mnt/c/Users/Quantum/Documents/GitHub/Claude_Settings/`

### Core Capabilities
1. ✅ **Interpret Vague Prompts** - Understand real user intent
2. ✅ **Auto-Expand Scope** - Go beyond minimum to production-ready
3. ✅ **Parallel Execution** - Execute up to 5 tasks simultaneously
4. ✅ **Auto-Fix Errors** - Debug and fix without asking
5. ✅ **Production Defaults** - Tests, docs, security included automatically
6. ✅ **Proactive Improvements** - Refactor and improve while working

### Autonomy Level: MAXIMUM

**Claude ONLY Asks For**:
- API keys
- External credentials
- Business decisions
- Destructive changes

**Claude NEVER Asks For**:
- Implementation details
- Technology choices
- Code structure
- Error resolution
- Test failures
- Optimization decisions

### Quick Examples

| You Say | Claude Delivers |
|---------|----------------|
| "add auth" | Complete authentication system (registration, login, logout, reset, verification, sessions, JWT, security, tests) |
| "optimize" | Full performance optimization (code splitting, caching, DB optimization, CDN, 90+ Lighthouse) |
| "fix bug" | Debug, fix, add tests, prevent regression, improve error handling, logging, docs |
| "add dashboard" | Complete dashboard (charts, real-time updates, filters, export, responsive) |

**See**: `SMART_AUTONOMOUS_CONFIG.md` for complete documentation

---

## 🔄 RALPH LOOP - AUTONOMOUS ITERATION SYSTEM (INTEGRATED)

**Status**: ✅ **ACTIVE** - Installed and integrated into Claude Code DNA

### Overview

The **Ralph Wiggum** technique creates self-referential feedback loops for autonomous iterative development. Based on Anthropic's official plugin, Ralph Loop enables continuous improvement cycles where Claude iteratively refines work until completion.

### Core Concept

**"Ralph is a Bash loop"** - A simple `while true` that repeatedly feeds the same prompt to Claude:
- Same prompt fed every iteration
- Modified files and git history persist
- Claude autonomously improves by reading past work
- Continues until completion criteria met or iteration limit reached

### Installation Locations

- **Plugin**: `.claude/plugins/ralph-wiggum/` (Project-specific)
- **Global Plugin**: `~/.claude/plugins/marketplaces/claude-plugins-official/plugins/ralph-wiggum/`
- **Skill**: `~/.claude/skills/ralph-loop.md` (Genius DNA integration)
- **Command**: `~/.claude/commands/ralph.md` (Slash command)
- **Gemini Integration**: `~/gemini-ralph-loop.sh` (Gemini CLI wrapper)

### Usage - Claude Code

**NEW: Auto-Activation** (No slash commands needed!)

Ralph Loop now **automatically activates** when you use iterative keywords:

```bash
# Just talk naturally - system auto-detects and activates Ralph Loop
"Build REST API for todos, iteratively improving until complete"
"Fix authentication bugs, keep trying until it works"
"Optimize database queries continuously until 50% faster"
"Implement feature X, retry until all tests pass"
```

**Trigger Keywords**: iteratively, continuously, repeatedly, keep improving, keep trying, until it works, until complete, until done, loop until, retry until, auto-fix, self-heal, keep going, don't stop, refine until, improve until, fix until

**Documentation**: See `/mnt/c/Users/Quantum/.claude/AUTO_RALPH_ACTIVATION.md` for complete guide.

**Manual Usage** (still available):

```bash
# Basic usage
/ralph-loop "Build REST API for todos with CRUD, validation, tests" --max-iterations 50

# With completion promise
/ralph-loop "Fix all TypeScript errors. Output <promise>COMPLETE</promise> when done." \
  --completion-promise "COMPLETE" \
  --max-iterations 30

# Activate via slash command
/ralph
```

### Usage - Gemini CLI

```bash
# Basic usage
~/gemini-ralph-loop.sh "Build REST API for todos with tests"

# With completion promise
~/gemini-ralph-loop.sh "Fix bugs. Output <promise>COMPLETE</promise> when done." \
  --completion-promise "COMPLETE" \
  --max-iterations 30 \
  --gemini-model gemini-1.5-pro

# Custom work directory
~/gemini-ralph-loop.sh "Optimize performance" \
  --work-dir /path/to/project \
  --max-iterations 50 \
  --verbose
```

### How Ralph Loop Works

1. **Initialization**: User provides task and parameters (max iterations, completion promise)
2. **Iteration Cycle**:
   - Claude receives prompt and context
   - Works on task (coding, testing, debugging)
   - Attempts to exit session
   - Stop hook intercepts exit
   - Hook feeds SAME prompt back with updated context
   - Claude sees modified files and git history
3. **Completion**: Loop ends when:
   - Completion promise detected in output (`<promise>TEXT</promise>`)
   - Max iterations reached
   - Manual cancellation (`/cancel-ralph`)

### Best Practices

#### 1. Clear Completion Criteria
```markdown
✅ GOOD:
"Build todo API. Requirements:
- All CRUD endpoints working
- Input validation implemented
- Tests passing (coverage > 80%)
- README with API documentation
Output: <promise>COMPLETE</promise>"

❌ BAD:
"Build a good todo API"
```

#### 2. Always Set Max Iterations
```bash
# REQUIRED - Prevents infinite loops
--max-iterations 20-50  # Typical range for most tasks
```

#### 3. Use Completion Promises
```bash
# Enables clean exit when genuinely complete
--completion-promise "COMPLETE"
--completion-promise "All tests passing"
--completion-promise "TASK_FINISHED"
```

#### 4. Incremental Goals
```markdown
Phase 1: Authentication (JWT, tests)
Phase 2: Product catalog (CRUD, tests)
Phase 3: Shopping cart (add/remove, tests)
Output <promise>COMPLETE</promise> when all phases done.
```

### Genius DNA Integration

Ralph Loop is integrated into the Genius DNA skill system:

```python
# Auto-activation for iterative tasks
if requires_iteration(task):
    activate_skill('ralph-loop')
    suggest_params = {
        'max_iterations': estimate_iterations(task),
        'completion_promise': extract_promise(task)
    }
```

**Skill Level**: 5 (Master)
**Domains**: autonomous_coding, iterative_development, ai_agents

### When to Use Ralph Loop

**Ideal for:**
- ✅ Well-defined tasks with clear success criteria
- ✅ Iterative refinement (tests, linters)
- ✅ Greenfield projects
- ✅ Tasks with automatic verification
- ✅ Getting tests to pass
- ✅ Multi-phase implementations

**Not ideal for:**
- ❌ Tasks requiring human judgment
- ❌ One-shot operations
- ❌ Unclear success criteria
- ❌ Production debugging (use targeted debugging)

### Monitoring Ralph Loops

```bash
# Check current iteration (Claude Code)
grep '^iteration:' .claude/ralph-loop.local.md

# Check state
head -10 .claude/ralph-loop.local.md

# Cancel active loop
/cancel-ralph
# OR
rm .claude/ralph-loop.local.md

# Monitor Gemini Ralph Loop
cat .gemini-ralph/state.json | jq .
tail -f .gemini-ralph/iteration-*-output.txt
```

### Real-World Results

- 6 repositories generated overnight (YC hackathon)
- $50k contract completed for $297 API costs
- Entire programming language created over 3 months
- Average: 15-30 iterations for medium complexity tasks

### Safety & Ethical Guidelines

1. **NEVER output false completion promises** - Only when genuinely complete
2. **ALWAYS set max-iterations** - Prevents runaway API costs
3. **Monitor API usage** - Each iteration = API calls
4. **Include escape hatches** - Document blockers after N iterations
5. **Trust the process** - Don't circumvent the loop

### Philosophy

- **Iteration > Perfection** - Refine through loops, not perfect first try
- **Failures Are Data** - Use them to improve next iteration
- **Persistence Wins** - Keep trying until success
- **Operator Skill Matters** - Good prompts = good results

### Advanced: Multi-Agent Ralph Chains

Combine Ralph Loop with Agent Chaining for maximum effectiveness:

```
Phase 1: Planner analyzes task → Ralph Loop for implementation
Phase 2: Coder implements → Ralph Loop for testing
Phase 3: Reviewer audits → Ralph Loop for fixes
Phase 4: Integrator merges → Complete
```

### Files & References

**Plugin Files:**
- `.claude/plugins/ralph-wiggum/README.md` - Full documentation
- `.claude/plugins/ralph-wiggum/scripts/setup-ralph-loop.sh` - Loop setup
- `.claude/plugins/ralph-wiggum/hooks/stop-hook.sh` - Exit interception

**State Files:**
- `.claude/ralph-loop.local.md` - Claude Code state (YAML frontmatter)
- `.gemini-ralph/state.json` - Gemini CLI state (JSON)
- `.gemini-ralph/iteration-N-output.txt` - Gemini iteration outputs

**External Resources:**
- Original: https://ghuntley.com/ralph/
- Anthropic Plugin: https://github.com/anthropics/claude-plugins-official/tree/main/plugins/ralph-wiggum
- Blog: https://paddo.dev/blog/ralph-wiggum-autonomous-loops/

---

## 🎨 GEMINI STITCH - AI UI DESIGN INTEGRATION (INTEGRATED)

**Status**: ✅ **ACTIVE** - Integrated into Claude Code DNA and Gemini CLI

### Overview

**Gemini Stitch** is Google's AI-powered UI design tool that transforms natural language prompts, images, sketches, or URLs into interactive UI mockups and production-ready frontend code. Powered by Gemini 3, it enables rapid prototyping and design-to-code workflows.

### Core Capabilities

- **Text-to-UI**: Convert prompts to complete UI designs
- **Image-to-UI**: Transform screenshots into editable interfaces
- **URL-to-UI**: Convert webpages to design files
- **Prototyping**: Create multi-screen interactive flows
- **Code Export**: Generate HTML, React, Vue, or Tailwind code

### Installation Locations

- **Claude Skill**: `~/.claude/skills/gemini-stitch.md`
- **Claude Command**: `~/.claude/commands/stitch.md`
- **Gemini Wrapper**: `~/.gemini/gemini-stitch.sh`
- **Skills JSON**: `~/.gemini/skills/stitch.json`
- **Bash Aliases**: `~/.bashrc.d/gemini-stitch.sh`
- **Auto-Activate**: `~/.gemini/stitch-auto-activate.sh`

### Usage - Claude Code

**Auto-Activation** (Natural language triggers):

```bash
# Just describe your UI need - Stitch auto-activates
"Design a modern trading dashboard with real-time charts"
"Create a mobile app prototype for banking"
"Convert this screenshot to React code"
"Build a landing page for my SaaS product"
```

**Slash Commands**:

```bash
# Text-to-UI
/stitch "Design a fintech dashboard with charts and tables"

# Multi-screen prototype
/stitch-prototype "Login -> Dashboard -> Settings flow"

# From image
/stitch-from-image /path/to/screenshot.png
```

### Usage - Gemini CLI

```bash
# Text-to-UI
gemini-stitch design "Create a modern dashboard"

# Prototype
gemini-stitch prototype "Banking app: Login -> Dashboard -> Transfer"

# From URL
gemini-stitch from-url "https://stripe.com/dashboard"

# Combined workflow (Stitch + Claude review)
stitch-full "Design a trading dashboard"
stitch-iterate "Refine dashboard until 90+ design score"
```

### Workflow Integration

**Standard Design-to-Code Pipeline**:
```
User Prompt → Stitch Design → User Refines → Export Code → Claude Review → Production
```

**Iterative Design (Ralph Loop)**:
```bash
/ralph-loop "/stitch Refine dashboard until:
- Visual hierarchy clear
- 8px grid spacing
- WCAG 2.1 AA compliance
Output <promise>DESIGN_COMPLETE</promise> when done."
--max-iterations 20
```

### Auto-Activation Triggers

Stitch skill auto-activates when detecting:
- "design ui", "create interface", "mockup", "wireframe"
- "landing page", "dashboard", "app screen"
- "prototype", "user flow", "component library"
- "convert screenshot", "recreate this UI"
- "frontend design", "mobile app design"

### Best Practices

1. **Detailed Prompts**: Include colors, layout, components, style
2. **Reference Designs**: "Similar to Stripe Dashboard aesthetic"
3. **Specify Constraints**: Mobile-first, accessibility, framework
4. **Use Prototypes**: Link screens for complete user flows
5. **Export Format**: Specify React/Vue/Tailwind for code export

### Example: Trading Dashboard

```bash
/stitch "Create trading dashboard:
- Header: Logo, search, notifications, profile
- Sidebar: Watchlist, Orders, Portfolio, Settings
- Main area:
  - Top: 4 stat cards (P&L, Cash, Margin, Equity)
  - Center: TradingView-style candlestick chart
  - Bottom: Order book + recent trades tables
- Right sidebar: Quick order entry form
- Theme: Dark (#0D1117), green (#00C853) / red (#FF5252) accents"
```

### Genius DNA Integration

```python
# Auto-activation for UI tasks
if detect_ui_intent(prompt):
    activate_skill('gemini-stitch')
    suggest_workflow = {
        'tool': 'https://stitch.withgoogle.com',
        'export_format': 'react' if 'react' in prompt else 'html'
    }
```

### External Resources

- **Web Interface**: https://stitch.withgoogle.com
- **Documentation**: https://developers.googleblog.com/stitch-a-new-way-to-design-uis/
- **Blog Post**: https://blog.google/technology/google-labs/stitch-gemini-3/

---

## 🚨 DIAMOND RULE #1: POSTGRESQL ONLY (ABSOLUTE REQUIREMENT)

**MANDATORY ACROSS ALL PROJECTS - NO EXCEPTIONS**

### Database Policy (STRICT ENFORCEMENT)

```
┌─────────────────────────────────────────────────────────────┐
│                    DATABASE POLICY                          │
│                                                             │
│  ✅ ALLOWED:   PostgreSQL 13+ ONLY                         │
│  ❌ FORBIDDEN: SQLite, MySQL, MariaDB, MongoDB, etc.       │
│                                                             │
│  NO FALLBACKS. NO EXCEPTIONS. NO COMPROMISES.              │
└─────────────────────────────────────────────────────────────┘
```

### Why PostgreSQL ONLY?

1. ✅ **Production-Grade Reliability** - ACID compliance, data integrity
2. ✅ **Concurrent Access** - Multiple sessions without locking
3. ✅ **Advanced Queries** - Complex analytics, full-text search
4. ✅ **Scalability** - Handles millions of records efficiently
5. ✅ **JSON Support** - Flexible schema evolution (JSONB)
6. ✅ **Performance** - Optimized for heavy workloads
7. ✅ **Enterprise Features** - Triggers, stored procedures, views

### SQLite is BANNED (Why)

❌ **File corruption** - Especially on WSL/Windows systems
❌ **No concurrent writes** - Session conflicts, locking issues
❌ **Limited scalability** - Poor performance with large datasets
❌ **Basic features only** - No full-text search, no JSON indexing
❌ **Single file risk** - One corruption = total data loss
❌ **No production support** - Not enterprise-ready

### Enforcement Rules

**When designing ANY system that needs a database**:

1. ✅ **ALWAYS use PostgreSQL** - No exceptions
2. ❌ **NEVER suggest SQLite** - Even for "development" or "testing"
3. ❌ **NEVER create .db files** - SQLite databases forbidden
4. ❌ **NEVER import sqlite3** - Python sqlite3 module banned
5. ✅ **ALWAYS use psycopg2** - PostgreSQL connector for Python
6. ✅ **ALWAYS verify PostgreSQL** - Check database exists before proceeding

### Code Examples

**✅ CORRECT (PostgreSQL)**:
```python
import psycopg2
from psycopg2.extras import RealDictCursor

# Connect to PostgreSQL
conn = psycopg2.connect(
    dbname="project_db",
    user="project_user",
    password="secure_password",
    host="localhost",
    port=5432
)
```

**❌ FORBIDDEN (SQLite)**:
```python
import sqlite3  # ❌ BANNED - DO NOT USE
conn = sqlite3.connect("database.db")  # ❌ FORBIDDEN
```

### Database Naming Convention

**Format**: `{project_name}_db`

**Examples**:
- AIA: `aia_intelligence`
- Trading System: `trading_system_db`
- Website Backend: `spartan_website_db`
- Analytics: `analytics_db`

### Setup Requirements

**Before ANY database operations**:

1. ✅ Verify PostgreSQL installed: `psql --version`
2. ✅ Create database: `createdb {project_name}_db`
3. ✅ Create user: `createuser {project_name}_user`
4. ✅ Grant permissions: `GRANT ALL PRIVILEGES ON DATABASE {project_name}_db TO {project_name}_user;`
5. ✅ Test connection: `psql -d {project_name}_db -c "SELECT version();"`

### Error Messages

If user requests SQLite or non-PostgreSQL database:

```
❌ SQLite is NOT SUPPORTED

This is a strict project-wide policy. PostgreSQL ONLY.

Reasons:
- Production-grade reliability required
- Concurrent access needed
- Advanced query capabilities essential
- File corruption risk unacceptable

Please use PostgreSQL 13+ instead.

Installation:
  Windows: https://www.postgresql.org/download/windows/
  WSL:     sudo apt install postgresql
```

---

## MANDATORY: C++ FIRST DEVELOPMENT
```cpp
# DEFAULT LANGUAGE: C++ (NOT PYTHON)
# All new code MUST be written in C++ for maximum performance
# Python allowed for rapid prototyping - prefer C++ for performance for all operations
```

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.
**CRITICAL**: C++ is the PRIMARY and DEFAULT language. Python is allowed as a FALLBACK for rapid prototyping or when C++ is impractical.

## Environment Overview

This is a Windows user directory optimized for algorithmic trading development using **C++ FIRST** architecture across multiple platforms including NinjaTrader, Interactive Brokers, and high-performance C++-based trading systems.

## Development Structure

### NinjaTrader 8 Development
- **Main Directory**: `Documents/NinjaTrader 8/bin/Custom/`
- **Solution File**: `Documents/NinjaTrader.Custom.sln`
- **Build**: NinjaTrader compiles automatically when platform is running
- **Languages**: C# (.NET Framework)
- **Architecture**: Indicators inherit from `Indicator` base class, use `OnStateChange()` and `OnBarUpdate()` methods

### C++ Trading Projects (PRIMARY)
- **Directory**: `CppProjects/` (replacing PycharmProjects)
- **Key Projects**:
  - `Arbitrage_Nexus_Cpp/` - Ultra-high performance arbitrage with SIMD
  - `ib_api_cpp/` - Interactive Brokers API with 100x performance boost
  - `market_data_cpp/` - Real-time data processing with vectorization
- **Build**: Use `g++ -O3 -march=native --target-cpu=native` for maximum performance
- **Environment**: C++ with SIMD intrinsics and optimization optimization enabled

### Python Projects (FALLBACK)
- **Status**: Use C++ for performance-critical code, Python for prototyping
- **Directory**: `PycharmProjects/` (legacy only)
- **Action Required**: Prefer C++ for production, use Python as fallback for performance gains

### Configuration Management
- **Claude Settings**: `.claude/settings.local.json` (read permissions configured)
- **Global Settings**: `Documents/GitHub/Claude_Settings/` - Synced Claude configuration
- **Agent System**: Advanced meta-orchestrator system with specialized trading and programming agents

### 🎯 Skill System (ACTIVE)
- **Status**: ✅ FULLY OPERATIONAL
- **Skills Directory**: `.claude/skills/`
- **Auto-Load**: Enabled on every session and prompt
- **Critical Skills**:
  - `agent-skills-system` - Core skill discovery and recursive self-improvement
  - `meta-orchestrator` - Automatic task analysis and skill coordination
- **Agent Logs**: `.claude/agent-skill-logs/` - Individual agent skill usage tracking
- **Session Data**: `.claude/sessions/` - Real-time skill loading status
- **Discovery Tool**: Run `bash /mnt/d/claude/central-config/skill_discovery_report.sh` for detailed analysis

## Key Development Patterns

### NinjaTrader Indicators
```csharp
// Standard pattern for indicators
public class MyIndicator : Indicator
{
    protected override void OnStateChange()
    {
        if (State == State.SetDefaults)
        {
            // Configuration
        }
        else if (State == State.DataLoaded)
        {
            // Initialization
        }
    }

    protected override void OnBarUpdate()
    {
        // Main calculation logic
    }
}
```

### Position Sizing Calculations
- Optimal f calculations use real account data via `Account.All.FirstOrDefault().Executions`
- Base calculation: `positionSize = (optimalF * AccountEquity) / Math.Abs(maxLoss)`
- Risk management typically uses fractional multipliers (25%, 50%, 75% of optimal f)

### C++ Trading Architecture (MANDATORY)
- Projects use C++ with modern toolchains (CMake, Conan) for zero-overhead dependencies
- SIMD-optimized code using intrinsics with compile-time optimization
- Ultra-fast pattern: vectorized data collection → parallel analysis → real-time strategy execution
- Performance: 10-100x faster than Python with automatic vectorization

### MAX (Modular Accelerated Xecution) Integration
- **Purpose**: AI/ML model serving and inference optimization
- **Key Resources**:
  - MAX Python API: https://docs.modular.com/max/api/python/
  - MAX serving guide: https://docs.modular.com/max/get-started/
  - Model browser: https://www.modular.com/models
- **Common Commands**:
  - Start model server: `max serve <model-name>`
  - Benchmark models: `max benchmark --model <model-name>`
  - List available models: `max models list`
- **Use Cases**: High-performance AI model inference for trading signals, pattern recognition, and market prediction

## Database Architecture (POSTGRESQL ONLY)

### Trading Systems Databases
```
trading_system_db          # Main trading database
├── executions            # Trade execution records
├── positions             # Current positions
├── market_data           # Real-time market data
├── backtests             # Backtest results
└── performance_metrics   # Performance tracking
```

### AIA Intelligence Database
```
aia_intelligence          # AIA personal assistant database
├── interactions          # Conversation logs
├── personality           # User preferences
├── projects              # Project contexts
└── learning_patterns     # Behavioral patterns
```

### Analytics Databases
```
analytics_db              # Market analytics database
├── patterns              # Identified patterns
├── correlations          # Market correlations
├── predictions           # AI predictions
└── research_notes        # Research data
```

**ALL databases use PostgreSQL 13+. NO EXCEPTIONS.**

## File Organization

### Important Files
- `optimalf.cs` - Advanced optimal f position sizing indicator using real trading data
- `*.csv` files - Market data exports and analysis results
- `*.log` files - Trading system and application logs

### Trading Data Flow (C++ OPTIMIZED)
1. **Data Collection**: High-performance C++ APIs for Yahoo Finance, Interactive Brokers, NinjaTrader feeds
2. **Analysis**: SIMD-vectorized C++ algorithms for pattern recognition and statistical analysis
3. **Storage**: PostgreSQL databases for reliable persistence
4. **Execution**: High-performance C++ strategies with NinjaTrader integration
5. **Monitoring**: Real-time C++-powered performance tracking

## Common Commands

### C++ Development (PRIMARY)
```bash
# Compile with maximum optimization
g++ -O3 -march=native -std=c++20 main.cpp -o main

# Run with SIMD optimization
g++ -O3 -march=native -std=c++20 -mavx2 main.cpp -o main && ./main

# Build optimized trading modules
g++ -O3 -march=native -std=c++20 -shared -fPIC trading_system.cpp -o libtrading_system.so
```

### PostgreSQL Database Management
```bash
# Create new database
createdb {project_name}_db

# Connect to database
psql -d {project_name}_db

# Backup database
pg_dump {project_name}_db > backup.sql

# Restore database
psql -d {project_name}_db < backup.sql

# View all databases
psql -l
```

### Python Development (FALLBACK)
```bash
# NOTE: Python is allowed as a fallback - prefer C++ for production code
# Only use for legacy compatibility during migration period
python -m pip install -e .  # Use C++ when performance matters
```

### NinjaTrader Development
- Use Visual Studio or NinjaTrader's built-in editor
- Compilation happens automatically when NinjaTrader platform starts
- Check NinjaTrader Editor Output window for compilation errors

## Special Considerations

### Cross-Platform Development
- Running on WSL2 (Windows Subsystem for Linux)
- Files accessible via `/mnt/c/Users/Quantum/` path structure
- Mix of Windows applications (NinjaTrader, Visual Studio) and Linux tools

### Trading System Integration
- Real-time data feeds require active market connections
- Position sizing calculations depend on live account data
- Risk management systems integrate across multiple trading platforms

### Agent System
- Advanced meta-orchestrator for complex task delegation
- Specialized agents for trading, programming, and system administration
- Token-optimized agent hierarchy for efficient task completion

### Database Reliability
- PostgreSQL ensures ACID compliance
- Automatic backups via cron jobs
- Replication for critical trading databases
- Connection pooling for performance

---

## 🚨 CRITICAL RULES SUMMARY

1. **POSTGRESQL ONLY** - No SQLite, ever. No exceptions.
2. **C++ FIRST** - New code in C++, not Python
3. **NO FAKE DATA** - Real APIs only, no Math.random()
4. **AGENT SKILLS** - Use skill system for all tasks
5. **PRODUCTION-GRADE** - Enterprise reliability required
6. **RALPH LOOP** - Use for iterative tasks, ALWAYS set max-iterations

**Violations of these rules are not acceptable.**

---

## 🔄 Quick Reference: Ralph Loop

```bash
# Claude Code
/ralph-loop "<task>" --max-iterations <N> --completion-promise "<TEXT>"
/cancel-ralph

# Gemini CLI
~/gemini-ralph-loop.sh "<task>" --max-iterations <N> --completion-promise "<TEXT>"

# Slash Command
/ralph
```

**Key Files**:
- Plugin: `.claude/plugins/ralph-wiggum/`
- Skill: `~/.claude/skills/ralph-loop.md`
- Gemini: `~/gemini-ralph-loop.sh`
- Docs: `~/RALPH_LOOP_INTEGRATION.md`

---

**Last Updated**: December 29, 2025
**PostgreSQL Policy**: Mandatory, Global, Strict
**Ralph Loop**: Integrated and Active
**Enforcement**: Active across all projects
