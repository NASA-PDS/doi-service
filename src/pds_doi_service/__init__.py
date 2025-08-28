# encoding: utf-8
"""Planetary Data System's Digital Object Identifier service"""
import importlib.resources

__version__ = VERSION = importlib.resources.files(__name__).joinpath("VERSION.txt").read_text().strip()
