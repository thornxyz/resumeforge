"""
WebSocket server that bridges between browser and Texlab LSP server.
"""

import asyncio
import json
import logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from typing import Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()


class TexlabBridge:
    """Manages communication between WebSocket client and Texlab process."""

    def __init__(self, websocket: WebSocket):
        self.websocket = websocket
        self.texlab_process: Optional[asyncio.subprocess.Process] = None
        self.client_to_server_task: Optional[asyncio.Task] = None
        self.server_to_client_task: Optional[asyncio.Task] = None

    async def start(self):
        """Start Texlab process and communication tasks."""
        # Start texlab in stdio mode
        self.texlab_process = await asyncio.create_subprocess_exec(
            "texlab",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        logger.info("Texlab process started")

        # Start bidirectional communication
        self.client_to_server_task = asyncio.create_task(
            self._forward_client_to_server()
        )
        self.server_to_client_task = asyncio.create_task(
            self._forward_server_to_client()
        )

        # Also log stderr
        asyncio.create_task(self._log_stderr())

    async def _forward_client_to_server(self):
        """Forward messages from WebSocket client to Texlab."""
        try:
            while True:
                # Receive JSON-RPC message from client
                data = await self.websocket.receive_text()
                logger.debug(f"Client -> Server: {data[:100]}...")

                # Forward to Texlab (LSP uses Content-Length header format)
                message_bytes = data.encode("utf-8")
                header = f"Content-Length: {len(message_bytes)}\r\n\r\n"
                full_message = header.encode("utf-8") + message_bytes

                self.texlab_process.stdin.write(full_message)
                await self.texlab_process.stdin.drain()

        except WebSocketDisconnect:
            logger.info("WebSocket disconnected")
        except Exception as e:
            logger.error(f"Error forwarding client to server: {e}")

    async def _forward_server_to_client(self):
        """Forward messages from Texlab to WebSocket client."""
        try:
            while True:
                # Read LSP message from Texlab (Content-Length header format)
                header_line = await self.texlab_process.stdout.readline()
                if not header_line:
                    break

                # Parse Content-Length header
                header = header_line.decode("utf-8").strip()
                if not header.startswith("Content-Length:"):
                    continue

                content_length = int(header.split(":")[1].strip())

                # Read empty line
                await self.texlab_process.stdout.readline()

                # Read message body
                message_bytes = await self.texlab_process.stdout.readexactly(
                    content_length
                )
                message = message_bytes.decode("utf-8")

                logger.debug(f"Server -> Client: {message[:100]}...")

                # Forward to WebSocket client
                await self.websocket.send_text(message)

        except Exception as e:
            logger.error(f"Error forwarding server to client: {e}")

    async def _log_stderr(self):
        """Log Texlab stderr output."""
        try:
            while True:
                line = await self.texlab_process.stderr.readline()
                if not line:
                    break
                logger.warning(f"Texlab stderr: {line.decode('utf-8').strip()}")
        except Exception as e:
            logger.error(f"Error reading stderr: {e}")

    async def stop(self):
        """Stop all tasks and terminate Texlab process."""
        logger.info("Stopping Texlab bridge")

        if self.client_to_server_task:
            self.client_to_server_task.cancel()
        if self.server_to_client_task:
            self.server_to_client_task.cancel()

        if self.texlab_process:
            self.texlab_process.terminate()
            await self.texlab_process.wait()


@app.websocket("/lsp")
async def lsp_websocket(websocket: WebSocket):
    """WebSocket endpoint for LSP communication."""
    await websocket.accept()
    logger.info("WebSocket connection established")

    bridge = TexlabBridge(websocket)

    try:
        await bridge.start()

        # Wait for tasks to complete (they won't unless there's an error or disconnect)
        await asyncio.gather(
            bridge.client_to_server_task,
            bridge.server_to_client_task,
            return_exceptions=True,
        )
    except Exception as e:
        logger.error(f"Error in WebSocket handler: {e}")
    finally:
        await bridge.stop()
        logger.info("WebSocket connection closed")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
