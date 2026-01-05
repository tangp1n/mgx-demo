"""Code generation agent using LangGraph."""
import logging
from typing import Dict, Any, AsyncGenerator
import json

logger = logging.getLogger(__name__)


class CodeGenAgent:
    """
    Agent responsible for generating code based on requirements.

    This agent:
    1. Analyzes user requirements
    2. Generates appropriate project structure
    3. Creates necessary files (package.json, index.html, app.js, etc.)
    4. Installs dependencies
    5. Starts the development server
    """

    def __init__(self, container_lifecycle_service, llm_config=None):
        """
        Initialize code generation agent.

        Args:
            container_lifecycle_service: Service for container operations
            llm_config: LLM configuration (optional, for future enhancements)
        """
        self.container_lifecycle = container_lifecycle_service
        self.llm_config = llm_config

    async def generate_code(
        self,
        application_id: str,
        requirements: str,
        port: int = 8000
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Generate code based on requirements and stream progress.

        Args:
            application_id: Application ID
            requirements: User requirements

        Yields:
            Progress events (thought, tool_call, tool_call_result, text, error)
        """
        try:
            yield {
                "type": "thought",
                "data": {
                    "content": "Analyzing requirements to determine project type and structure..."
                }
            }

            # Determine project type from requirements
            project_type = self._determine_project_type(requirements)

            yield {
                "type": "text",
                "data": {
                    "content": f"Creating a {project_type} application based on your requirements."
                }
            }

            # Generate project structure based on type
            if project_type == "react":
                async for event in self._generate_react_app(application_id, requirements, port):
                    yield event
            elif project_type == "vanilla-js":
                async for event in self._generate_vanilla_js_app(application_id, requirements, port):
                    yield event
            else:
                async for event in self._generate_simple_html_app(application_id, requirements, port):
                    yield event

            yield {
                "type": "text",
                "data": {
                    "content": "✅ Code generation complete! Your application is ready."
                }
            }

        except Exception as e:
            logger.error(f"Code generation failed: {str(e)}")
            yield {
                "type": "error",
                "data": {
                    "error": str(e),
                    "message": f"Code generation failed: {str(e)}"
                }
            }

    def _determine_project_type(self, requirements: str) -> str:
        """
        Determine project type from requirements.

        Args:
            requirements: User requirements

        Returns:
            Project type (simple-html, vanilla-js, react, etc.)
        """
        requirements_lower = requirements.lower()

        if "react" in requirements_lower:
            return "react"
        elif any(word in requirements_lower for word in ["interactive", "dynamic", "form", "api"]):
            return "vanilla-js"
        else:
            return "simple-html"

    async def _start_http_server(
        self,
        application_id: str,
        port: int,
        server_type: str = "python"
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Start HTTP server in container using appropriate method.

        Args:
            application_id: Application ID
            port: Port to start server on
            server_type: Type of server ("python" for static file server using Node.js, or "react" for React dev server)

        Yields:
            Server start events
        """
        yield {
            "type": "tool_call",
            "data": {
                "tool": "start_server",
                "input": {"command": f"Starting {server_type} server on port {port}"}
            }
        }

        if server_type == "python":
            # Create a Node.js script to start the HTTP server
            # Using Node.js since the container is node:18-alpine which doesn't have Python
            # This serves static files from /app directory
            server_script = f"""const http = require('http');
const fs = require('fs');
const path = require('path');

const PORT = {port};
const HOST = '0.0.0.0';

const MIME_TYPES = {{
    '.html': 'text/html',
    '.js': 'text/javascript',
    '.css': 'text/css',
    '.json': 'application/json',
    '.png': 'image/png',
    '.jpg': 'image/jpg',
    '.gif': 'image/gif',
    '.svg': 'image/svg+xml',
    '.wav': 'audio/wav',
    '.mp4': 'video/mp4',
    '.woff': 'application/font-woff',
    '.ttf': 'application/font-ttf',
    '.eot': 'application/vnd.ms-fontobject',
    '.otf': 'application/font-otf',
    '.wasm': 'application/wasm'
}};

const server = http.createServer((req, res) => {{
    let filePath = '.' + req.url;
    if (filePath === './') {{
        filePath = './index.html';
    }}

    const extname = String(path.extname(filePath)).toLowerCase();
    const contentType = MIME_TYPES[extname] || 'application/octet-stream';

    fs.readFile(filePath, (error, content) => {{
        if (error) {{
            if (error.code === 'ENOENT') {{
                res.writeHead(404, {{ 'Content-Type': 'text/html' }});
                res.end('<h1>404 - File Not Found</h1>', 'utf-8');
            }} else {{
                res.writeHead(500);
                res.end('Server Error: ' + error.code + '\\n');
            }}
        }} else {{
            res.writeHead(200, {{ 'Content-Type': contentType }});
            res.end(content, 'utf-8');
        }}
    }});
}});

server.listen(PORT, HOST, () => {{
    console.log(`Server running at http://${{HOST}}:${{PORT}}/`);
}});
"""

            # Write server script to container
            await self.container_lifecycle.write_file(
                application_id,
                "/tmp/server.js",
                server_script
            )

            # Start server in background using Node.js
            start_command = f"sh -c 'cd /app && node /tmp/server.js > /tmp/server.log 2>&1 & echo $! > /tmp/server.pid'"
            result = await self.container_lifecycle.exec_command(
                application_id,
                start_command,
                workdir="/"
            )

        elif server_type == "react":
            # For React, create a startup script that sets PORT and HOST
            # React dev server needs HOST=0.0.0.0 to be accessible from outside container
            startup_script = f"""#!/bin/sh
cd /app
export PORT={port}
export HOST=0.0.0.0
export BROWSER=none
nohup npm start > /tmp/server.log 2>&1 &
echo $! > /tmp/server.pid
"""
            # Write startup script
            await self.container_lifecycle.write_file(
                application_id,
                "/tmp/start_server.sh",
                startup_script
            )

            # Make executable and run
            start_command = "chmod +x /tmp/start_server.sh && /tmp/start_server.sh"
            result = await self.container_lifecycle.exec_command(
                application_id,
                start_command,
                workdir="/"
            )
        else:
            result = {
                "success": False,
                "error": f"Unknown server type: {server_type}"
            }

        yield {
            "type": "tool_call_result",
            "data": {
                "tool": "start_server",
                "result": result
            }
        }

        # Wait a moment for server to start
        import asyncio
        await asyncio.sleep(3 if server_type == "react" else 2)  # React needs more time

        # Check if server process is running
        if server_type == "python":
            pid_check = await self.container_lifecycle.exec_command(
                application_id,
                "cat /tmp/server.pid 2>/dev/null && ps aux | grep -v grep | grep 'node.*server.js' || echo 'Server process not found'",
                workdir="/"
            )
        else:
            pid_check = await self.container_lifecycle.exec_command(
                application_id,
                "cat /tmp/server.pid 2>/dev/null && ps aux | grep -v grep | grep 'node' || echo 'Server process not found'",
                workdir="/"
            )

        # Check if port is listening (using netcat or similar)
        port_check = await self.container_lifecycle.exec_command(
            application_id,
            f"nc -z 0.0.0.0 {port} 2>&1 || echo 'Port {port} check failed'",
            workdir="/"
        )

        # Check server log
        log_check = await self.container_lifecycle.exec_command(
            application_id,
            "tail -n 15 /tmp/server.log 2>&1 || echo 'Log file not found yet'",
            workdir="/"
        )

        logger.info(f"Server PID check ({server_type}): {pid_check.get('output', '')}")
        logger.info(f"Port check: {port_check.get('output', '')}")
        logger.info(f"Server log: {log_check.get('output', '')}")

        # Verify server is accessible
        if "succeeded" in port_check.get('output', '').lower() or port_check.get('exit_code') == 0:
            yield {
                "type": "text",
                "data": {
                    "content": f"✅ {server_type.capitalize()} server started successfully on port {port}"
                }
            }
        else:
            yield {
                "type": "text",
                "data": {
                    "content": f"⚠️  {server_type.capitalize()} server start verification incomplete. Check logs if connection fails."
                }
            }
            yield {
                "type": "text",
                "data": {
                    "content": f"Log preview: {log_check.get('output', '')[:200]}"
                }
            }

    async def _generate_simple_html_app(
        self,
        application_id: str,
        requirements: str,
        port: int = 8000
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Generate a simple HTML application."""

        yield {
            "type": "tool_call",
            "data": {
                "tool": "create_file",
                "input": {"file_path": "/app/index.html", "purpose": "Main HTML file"}
            }
        }

        # Create index.html
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>My Application</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <div class="container">
        <h1>Welcome to Your Application</h1>
        <p>Requirements: {requirements[:100]}...</p>
        <div id="app"></div>
    </div>
    <script src="app.js"></script>
</body>
</html>"""

        result = await self.container_lifecycle.write_file(
            application_id,
            "/app/index.html",
            html_content
        )

        yield {
            "type": "tool_call_result",
            "data": {
                "tool": "create_file",
                "result": result
            }
        }

        # Create styles.css
        yield {
            "type": "tool_call",
            "data": {
                "tool": "create_file",
                "input": {"file_path": "/app/styles.css", "purpose": "Styles"}
            }
        }

        css_content = """* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: system-ui, -apple-system, sans-serif;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
}

.container {
    background: white;
    padding: 2rem;
    border-radius: 10px;
    box-shadow: 0 10px 25px rgba(0,0,0,0.2);
    max-width: 600px;
    width: 90%;
}

h1 {
    color: #333;
    margin-bottom: 1rem;
}

p {
    color: #666;
    line-height: 1.6;
}"""

        result = await self.container_lifecycle.write_file(
            application_id,
            "/app/styles.css",
            css_content
        )

        yield {
            "type": "tool_call_result",
            "data": {
                "tool": "create_file",
                "result": result
            }
        }

        # Create app.js
        yield {
            "type": "tool_call",
            "data": {
                "tool": "create_file",
                "input": {"file_path": "/app/app.js", "purpose": "Main JavaScript"}
            }
        }

        js_content = """console.log('Application loaded!');

const appDiv = document.getElementById('app');
appDiv.innerHTML = `
    <p style="margin-top: 1rem; padding: 1rem; background: #f0f0f0; border-radius: 5px;">
        This is a simple web application. Customize this code to match your requirements!
    </p>
`;"""

        result = await self.container_lifecycle.write_file(
            application_id,
            "/app/app.js",
            js_content
        )

        yield {
            "type": "tool_call_result",
            "data": {
                "tool": "create_file",
                "result": result
            }
        }

        # Start simple HTTP server on the specified port
        async for event in self._start_http_server(application_id, port, server_type="python"):
            yield event

    async def _generate_vanilla_js_app(
        self,
        application_id: str,
        requirements: str,
        port: int = 8000
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Generate a vanilla JavaScript application with some interactivity."""

        # For now, use simple HTML app as base
        async for event in self._generate_simple_html_app(application_id, requirements, port):
            yield event

    async def _generate_react_app(
        self,
        application_id: str,
        requirements: str,
        port: int = 8000
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Generate a React application."""

        yield {
            "type": "thought",
            "data": {
                "content": "Setting up React application structure..."
            }
        }

        # Create package.json
        yield {
            "type": "tool_call",
            "data": {
                "tool": "create_file",
                "input": {"file_path": "/app/package.json", "purpose": "Package configuration"}
            }
        }

        package_json = {
            "name": "my-app",
            "version": "1.0.0",
            "description": "Generated application",
            "scripts": {
                "start": "react-scripts start",
                "build": "react-scripts build"
            },
            "dependencies": {
                "react": "^18.2.0",
                "react-dom": "^18.2.0",
                "react-scripts": "5.0.1"
            },
            "browserslist": {
                "production": [">0.2%", "not dead"],
                "development": ["last 1 chrome version"]
            }
        }

        result = await self.container_lifecycle.write_file(
            application_id,
            "/app/package.json",
            json.dumps(package_json, indent=2)
        )

        yield {
            "type": "tool_call_result",
            "data": {
                "tool": "create_file",
                "result": result
            }
        }

        # Create public/index.html
        yield {
            "type": "tool_call",
            "data": {
                "tool": "create_directory",
                "input": {"path": "/app/public"}
            }
        }

        await self.container_lifecycle.exec_command(
            application_id,
            "mkdir -p /app/public /app/src"
        )

        yield {
            "type": "tool_call_result",
            "data": {
                "tool": "create_directory",
                "result": {"success": True}
            }
        }

        html_content = """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>React App</title>
  </head>
  <body>
    <noscript>You need to enable JavaScript to run this app.</noscript>
    <div id="root"></div>
  </body>
</html>"""

        await self.container_lifecycle.write_file(
            application_id,
            "/app/public/index.html",
            html_content
        )

        # Create src/index.js
        index_js = """import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);"""

        await self.container_lifecycle.write_file(
            application_id,
            "/app/src/index.js",
            index_js
        )

        # Create src/App.js
        app_js = f"""import React from 'react';
import './App.css';

function App() {{
  return (
    <div className="App">
      <header className="App-header">
        <h1>Welcome to Your React App</h1>
        <p>Requirements: {requirements[:100]}...</p>
        <p>Start building your application here!</p>
      </header>
    </div>
  );
}}

export default App;"""

        await self.container_lifecycle.write_file(
            application_id,
            "/app/src/App.js",
            app_js
        )

        # Create src/App.css
        app_css = """.App {
  text-align: center;
}

.App-header {
  background-color: #282c34;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  font-size: calc(10px + 2vmin);
  color: white;
}"""

        await self.container_lifecycle.write_file(
            application_id,
            "/app/src/App.css",
            app_css
        )

        # Create src/index.css
        index_css = """body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
    'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
    sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}"""

        await self.container_lifecycle.write_file(
            application_id,
            "/app/src/index.css",
            index_css
        )

        # Install dependencies
        yield {
            "type": "tool_call",
            "data": {
                "tool": "install_dependencies",
                "input": {"package_manager": "npm"}
            }
        }

        yield {
            "type": "text",
            "data": {
                "content": "Installing dependencies... this may take a few moments."
            }
        }

        result = await self.container_lifecycle.exec_command(
            application_id,
            "npm install --legacy-peer-deps"
        )

        yield {
            "type": "tool_call_result",
            "data": {
                "tool": "install_dependencies",
                "result": result
            }
        }

        # Start React dev server using unified server start method
        async for event in self._start_http_server(application_id, port, server_type="react"):
            yield event
