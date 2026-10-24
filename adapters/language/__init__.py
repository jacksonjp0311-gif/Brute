"""Language adapter: states only what brute.api returned. Template-based; no generative model."""
from .render import render,render_text,resolve
from .checker import check

__all__=['render','render_text','resolve','check']
