"""Web application entry point.

Launches the Gradio interface defined in app.ui.
"""
from __future__ import annotations

from app.ui import demo

if __name__ == "__main__":
    demo.launch(server_name="127.0.0.1", server_port=7860, inbrowser=True)
