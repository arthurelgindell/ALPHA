# Browser Automation Setup for Claude Code

## Overview

This guide explains how to set up browser automation capabilities for Claude Code using MCP (Model Context Protocol). This enables Claude to interact with web interfaces, including local network devices like routers, NAS systems, and IoT dashboards.

---

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Claude Code    │────▶│   MCP Server     │────▶│    Browser      │
│  (CLI/API)      │     │  (WebSocket)     │     │  (Chrome/etc)   │
└─────────────────┘     └──────────────────┘     └─────────────────┘
        │                       │                        │
   Claude API              stdio/HTTP              Actual pages
   connection              transport              (local/remote)
```

---

## Option 1: Claude in Chrome Extension (Recommended for Interactive Use)

### Prerequisites
- Google Chrome browser
- Claude Code CLI installed
- Anthropic API key

### Installation Steps

#### Step 1: Install the Chrome Extension

1. Visit the Chrome Web Store
2. Search for "Claude in Chrome" or visit:
   ```
   https://chrome.google.com/webstore/detail/claude-in-chrome
   ```
3. Click "Add to Chrome"
4. Grant required permissions (tabs, activeTab, scripting)

#### Step 2: Configure MCP in Claude Code

Add to your Claude Code MCP configuration (`~/.claude/mcp.json` or project `.claude/.mcp.json`):

```json
{
  "mcpServers": {
    "claude-in-chrome": {
      "command": "npx",
      "args": ["-y", "@anthropic/claude-in-chrome-mcp"]
    }
  }
}
```

Or add via CLI:
```bash
claude mcp add claude-in-chrome npx -y @anthropic/claude-in-chrome-mcp
```

#### Step 3: Verify Installation

```bash
# List MCP servers
claude mcp list

# Should show claude-in-chrome with available tools
```

### Available Tools

| Tool | Purpose |
|------|---------|
| `tabs_context_mcp` | Get available browser tabs |
| `tabs_create_mcp` | Create new tab |
| `navigate` | Go to URL |
| `computer` | Screenshot, click, scroll, type |
| `read_page` | Get accessibility tree |
| `find` | Find elements by description |
| `form_input` | Fill form fields |
| `javascript_tool` | Execute JavaScript |
| `get_page_text` | Extract page text |

---

## Option 2: Playwright MCP (Headless/Automated)

For headless browser automation without needing a visible Chrome window.

### Installation

```bash
# Install Playwright MCP server
npm install -g @anthropic/mcp-server-playwright

# Or use npx (no install needed)
npx @anthropic/mcp-server-playwright
```

### Configuration

Add to MCP config:

```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": ["-y", "@anthropic/mcp-server-playwright"],
      "env": {
        "PLAYWRIGHT_BROWSERS_PATH": "/path/to/browsers"
      }
    }
  }
}
```

### Available Tools

| Tool | Purpose |
|------|---------|
| `browser_navigate` | Navigate to URL |
| `browser_screenshot` | Capture screenshot |
| `browser_click` | Click element |
| `browser_fill` | Fill input field |
| `browser_select` | Select dropdown option |
| `browser_evaluate` | Run JavaScript |
| `browser_get_content` | Get page content |

---

## Option 3: Puppeteer MCP (Alternative Headless)

### Installation

```bash
npm install -g @anthropic/mcp-server-puppeteer
```

### Configuration

```json
{
  "mcpServers": {
    "puppeteer": {
      "command": "npx",
      "args": ["-y", "@anthropic/mcp-server-puppeteer"],
      "env": {
        "PUPPETEER_EXECUTABLE_PATH": "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
      }
    }
  }
}
```

---

## Option 4: Build Custom Browser MCP Server

For specialized needs, build your own MCP server using the SDK.

### Project Structure

```
browser-mcp-server/
├── package.json
├── src/
│   └── index.ts
└── tsconfig.json
```

### package.json

```json
{
  "name": "browser-mcp-server",
  "version": "1.0.0",
  "type": "module",
  "main": "dist/index.js",
  "scripts": {
    "build": "tsc",
    "start": "node dist/index.js"
  },
  "dependencies": {
    "@modelcontextprotocol/sdk": "^1.0.0",
    "puppeteer": "^22.0.0"
  },
  "devDependencies": {
    "@types/node": "^20.0.0",
    "typescript": "^5.0.0"
  }
}
```

### src/index.ts

```typescript
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import puppeteer, { Browser, Page } from "puppeteer";

// Browser state
let browser: Browser | null = null;
let page: Page | null = null;

async function ensureBrowser(): Promise<Page> {
  if (!browser) {
    browser = await puppeteer.launch({
      headless: false, // Set to true for headless
      args: ['--no-sandbox', '--disable-setuid-sandbox']
    });
  }
  if (!page) {
    page = await browser.newPage();
    await page.setViewport({ width: 1920, height: 1080 });
  }
  return page;
}

// Create MCP server
const server = new Server(
  { name: "browser-automation", version: "1.0.0" },
  { capabilities: { tools: {} } }
);

// Define tools
server.setRequestHandler("tools/list", async () => ({
  tools: [
    {
      name: "navigate",
      description: "Navigate to a URL",
      inputSchema: {
        type: "object",
        properties: {
          url: { type: "string", description: "URL to navigate to" }
        },
        required: ["url"]
      }
    },
    {
      name: "screenshot",
      description: "Take a screenshot of current page",
      inputSchema: {
        type: "object",
        properties: {}
      }
    },
    {
      name: "click",
      description: "Click at coordinates or selector",
      inputSchema: {
        type: "object",
        properties: {
          selector: { type: "string", description: "CSS selector" },
          x: { type: "number", description: "X coordinate" },
          y: { type: "number", description: "Y coordinate" }
        }
      }
    },
    {
      name: "type",
      description: "Type text into focused element",
      inputSchema: {
        type: "object",
        properties: {
          selector: { type: "string", description: "CSS selector" },
          text: { type: "string", description: "Text to type" }
        },
        required: ["text"]
      }
    },
    {
      name: "evaluate",
      description: "Execute JavaScript in page context",
      inputSchema: {
        type: "object",
        properties: {
          script: { type: "string", description: "JavaScript to execute" }
        },
        required: ["script"]
      }
    },
    {
      name: "get_content",
      description: "Get page HTML or text content",
      inputSchema: {
        type: "object",
        properties: {
          type: {
            type: "string",
            enum: ["html", "text"],
            description: "Content type to return"
          }
        }
      }
    }
  ]
}));

// Handle tool calls
server.setRequestHandler("tools/call", async (request) => {
  const { name, arguments: args } = request.params;
  const p = await ensureBrowser();

  switch (name) {
    case "navigate":
      await p.goto(args.url, { waitUntil: "networkidle0" });
      return { content: [{ type: "text", text: `Navigated to ${args.url}` }] };

    case "screenshot":
      const screenshot = await p.screenshot({ encoding: "base64" });
      return {
        content: [{
          type: "image",
          data: screenshot,
          mimeType: "image/png"
        }]
      };

    case "click":
      if (args.selector) {
        await p.click(args.selector);
      } else if (args.x !== undefined && args.y !== undefined) {
        await p.mouse.click(args.x, args.y);
      }
      return { content: [{ type: "text", text: "Clicked" }] };

    case "type":
      if (args.selector) {
        await p.type(args.selector, args.text);
      } else {
        await p.keyboard.type(args.text);
      }
      return { content: [{ type: "text", text: `Typed: ${args.text}` }] };

    case "evaluate":
      const result = await p.evaluate(args.script);
      return {
        content: [{
          type: "text",
          text: JSON.stringify(result, null, 2)
        }]
      };

    case "get_content":
      const content = args.type === "html"
        ? await p.content()
        : await p.evaluate(() => document.body.innerText);
      return { content: [{ type: "text", text: content }] };

    default:
      throw new Error(`Unknown tool: ${name}`);
  }
});

// Start server
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("Browser MCP server running on stdio");
}

main().catch(console.error);
```

### Build and Install

```bash
cd browser-mcp-server
npm install
npm run build

# Add to Claude Code
claude mcp add browser-automation node /path/to/browser-mcp-server/dist/index.js
```

---

## Platform-Specific Notes

### macOS

```bash
# Chrome path
/Applications/Google Chrome.app/Contents/MacOS/Google Chrome

# Grant automation permissions
# System Preferences → Security & Privacy → Accessibility
```

### Linux

```bash
# Install Chrome
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo dpkg -i google-chrome-stable_current_amd64.deb

# For headless, install dependencies
sudo apt-get install -y libx11-xcb1 libxcomposite1 libxdamage1 libxi6 libxtst6
```

### Windows

```powershell
# Chrome path
C:\Program Files\Google\Chrome\Application\chrome.exe

# Or via winget
winget install Google.Chrome
```

---

## Security Considerations

### Local Network Access

Browser automation can access local network resources (192.168.x.x, 10.x.x.x):

```javascript
// Can access router admin panels
await page.goto('http://192.168.0.1');

// Can access NAS interfaces
await page.goto('http://192.168.1.100:5000');

// Can access local development servers
await page.goto('http://localhost:3000');
```

### Credential Handling

**Never** hardcode credentials. Use environment variables or prompt:

```typescript
// Good: Use environment variables
const password = process.env.ROUTER_PASSWORD;

// Better: Prompt user at runtime
const password = await askUser("Enter router password:");
```

### Permission Boundaries

Configure MCP server permissions in Claude Code:

```json
{
  "mcpServers": {
    "browser": {
      "command": "node",
      "args": ["browser-server.js"],
      "allowedDomains": [
        "192.168.0.0/16",
        "10.0.0.0/8",
        "localhost"
      ]
    }
  }
}
```

---

## Usage Examples

### Example 1: Router Configuration

```
User: "Log into my router at 192.168.0.1 and show me connected devices"

Claude uses:
1. navigate → http://192.168.0.1
2. screenshot → See login page
3. form_input → Enter credentials
4. click → Login button
5. navigate → Connected devices page
6. screenshot → Show results
```

### Example 2: Form Automation

```
User: "Fill out the contact form on example.com"

Claude uses:
1. navigate → https://example.com/contact
2. read_page → Get form field references
3. form_input → Fill name, email, message
4. click → Submit button
5. screenshot → Confirm submission
```

### Example 3: Data Extraction

```
User: "Get the latest prices from my supplier portal"

Claude uses:
1. navigate → Supplier login page
2. form_input → Credentials
3. navigate → Pricing page
4. javascript_tool → Extract table data
5. Return structured data
```

---

## Troubleshooting

### Connection Issues

```bash
# Check MCP server is running
claude mcp list

# Restart MCP servers
claude mcp restart

# Check logs
tail -f ~/.claude/logs/mcp-*.log
```

### Browser Not Launching

```bash
# Verify Chrome installation
which google-chrome || which chromium

# Test Puppeteer directly
node -e "require('puppeteer').launch().then(b => { console.log('OK'); b.close(); })"
```

### Permission Denied

```bash
# macOS: Grant accessibility permissions
# Linux: Add user to required groups
sudo usermod -aG video $USER

# Check sandbox issues
--no-sandbox --disable-setuid-sandbox
```

---

## References

- [MCP Protocol Specification](https://modelcontextprotocol.io/)
- [Claude Code Documentation](https://docs.anthropic.com/claude-code)
- [Puppeteer API](https://pptr.dev/)
- [Playwright API](https://playwright.dev/)
