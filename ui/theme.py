"""
ui/theme.py — Generation 4 Theme Engine
===========================================
Defines the styling system for the Khushi AI Desktop Interface.
Supports Light Mode, Dark Mode, Accent Color presets (Blue, Purple, Green, Orange, Red),
and a custom premium Glassmorphism QSS theme.
"""
from __future__ import annotations

import logging
from typing import Dict

logger = logging.getLogger(__name__)

# Accent Color Presets (Hex values)
ACCENTS = {
    "blue": {
        "primary": "#0078D4",
        "primary_hover": "#106EBE",
        "primary_glow": "rgba(0, 120, 212, 0.25)",
        "accent": "#0078D4",
    },
    "purple": {
        "primary": "#8A2BE2",
        "primary_hover": "#7B1FA2",
        "primary_glow": "rgba(138, 43, 226, 0.25)",
        "accent": "#8A2BE2",
    },
    "green": {
        "primary": "#107C41",
        "primary_hover": "#0B5931",
        "primary_glow": "rgba(16, 124, 65, 0.25)",
        "accent": "#107C41",
    },
    "orange": {
        "primary": "#D83B01",
        "primary_hover": "#B33000",
        "primary_glow": "rgba(216, 59, 1, 0.25)",
        "accent": "#D83B01",
    },
    "red": {
        "primary": "#E81123",
        "primary_hover": "#C30010",
        "primary_glow": "rgba(232, 17, 35, 0.25)",
        "accent": "#E81123",
    },
    "glass": {
        "primary": "#9A4BFC",
        "primary_hover": "#B075FF",
        "primary_glow": "rgba(154, 75, 252, 0.3)",
        "accent": "#9A4BFC",
    }
}


def get_qss(theme_name: str = "dark", accent_name: str = "purple") -> str:
    """
    Generate and return the full QSS stylesheet for the application.
    """
    accent = ACCENTS.get(accent_name.lower(), ACCENTS["purple"])
    
    if theme_name.lower() == "light":
        # Sleek Minimalist Light Mode QSS
        return f"""
        * {{
            font-family: "Segoe UI", -apple-system, BlinkMacSystemFont, "Segoe UI Variable", Roboto, Helvetica, Arial, sans-serif;
            font-size: 13px;
            color: #1F1F1F;
        }}
        
        QMainWindow {{
            background-color: #F3F3F3;
        }}
        
        /* Left Sidebar */
        #SidebarContainer {{
            background-color: #EAEAEA;
            border-right: 1px solid #DCDCDD;
        }}
        
        QToolButton {{
            background-color: transparent;
            border: none;
            border-radius: 6px;
            padding: 8px;
            margin: 4px 6px;
        }}
        
        QToolButton:hover {{
            background-color: rgba(0, 0, 0, 0.05);
        }}
        
        QToolButton:checked {{
            background-color: rgba(0, 0, 0, 0.08);
            border-left: 3px solid {accent["primary"]};
        }}
        
        /* Center Chat Panel */
        #ChatContainer {{
            background-color: #FFFFFF;
        }}
        
        QScrollArea {{
            border: none;
            background-color: transparent;
        }}
        
        QScrollBar:vertical {{
            border: none;
            background-color: transparent;
            width: 8px;
            margin: 0px;
        }}
        
        QScrollBar::handle:vertical {{
            background-color: #C1C1C1;
            min-height: 20px;
            border-radius: 4px;
        }}
        
        QScrollBar::handle:vertical:hover {{
            background-color: #A6A6A6;
        }}
        
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
        
        /* Chat Input */
        #ChatInput {{
            background-color: #F8F9FA;
            border: 1px solid #E2E8F0;
            border-radius: 8px;
            padding: 10px 14px;
            color: #1F1F1F;
            font-size: 14px;
        }}
        
        #ChatInput:focus {{
            border: 1.5px solid {accent["primary"]};
            background-color: #FFFFFF;
        }}
        
        /* Right Dashboard Panel */
        #DashboardContainer {{
            background-color: #F8F9FA;
            border-left: 1px solid #DCDCDD;
        }}
        
        #DashboardTitle {{
            font-size: 16px;
            font-weight: bold;
            color: #1F1F1F;
            margin-bottom: 12px;
        }}
        
        .DashboardCard {{
            background-color: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 8px;
            padding: 10px;
            margin-bottom: 8px;
        }}
        
        .TelemetryLabel {{
            font-size: 11px;
            color: #64748B;
        }}
        
        .TelemetryValue {{
            font-size: 14px;
            font-weight: bold;
            color: #0F172A;
        }}
        
        QProgressBar {{
            background-color: #E2E8F0;
            border: none;
            border-radius: 3px;
            text-align: center;
            height: 6px;
        }}
        
        QProgressBar::chunk {{
            background-color: {accent["primary"]};
            border-radius: 3px;
        }}
        
        /* Buttons */
        QPushButton {{
            background-color: {accent["primary"]};
            color: #FFFFFF;
            border: none;
            border-radius: 6px;
            padding: 8px 16px;
            font-weight: 600;
        }}
        
        QPushButton:hover {{
            background-color: {accent["primary_hover"]};
        }}
        
        QPushButton:pressed {{
            background-color: {accent["primary_hover"]};
        }}
        """
        
    else:
        # Default Dark / Glassmorphism Theme (A Vision Pro + Win 11 Acrylic styling)
        # Background is rich translucent dark grey; borders are thin semi-transparent white
        return f"""
        * {{
            font-family: "Segoe UI", -apple-system, BlinkMacSystemFont, "Segoe UI Variable", Roboto, Helvetica, Arial, sans-serif;
            font-size: 13px;
            color: #E2E8F0;
        }}
        
        QMainWindow {{
            background-color: #0F0F11;
        }}
        
        /* Left Sidebar with animated Glassmorphism highlights */
        #SidebarContainer {{
            background-color: #141416;
            border-right: 1px solid rgba(255, 255, 255, 0.05);
        }}
        
        QToolButton {{
            background-color: transparent;
            border: none;
            border-radius: 6px;
            padding: 8px;
            margin: 4px 6px;
        }}
        
        QToolButton:hover {{
            background-color: rgba(255, 255, 255, 0.06);
        }}
        
        QToolButton:checked {{
            background-color: rgba(255, 255, 255, 0.1);
            border-left: 3px solid {accent["primary"]};
        }}
        
        /* Center Chat Panel */
        #ChatContainer {{
            background-color: #1A1A1E;
        }}
        
        QScrollArea {{
            border: none;
            background-color: transparent;
        }}
        
        QScrollBar:vertical {{
            border: none;
            background-color: transparent;
            width: 8px;
            margin: 0px;
        }}
        
        QScrollBar::handle:vertical {{
            background-color: rgba(255, 255, 255, 0.15);
            min-height: 20px;
            border-radius: 4px;
        }}
        
        QScrollBar::handle:vertical:hover {{
            background-color: rgba(255, 255, 255, 0.25);
        }}
        
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
        
        /* Chat Input area resembling Linear.app / Raycast bar */
        #ChatInput {{
            background-color: #16161A;
            border: 1px solid rgba(255, 255, 255, 0.07);
            border-radius: 8px;
            padding: 10px 14px;
            color: #F8FAFC;
            font-size: 14px;
        }}
        
        #ChatInput:focus {{
            border: 1.5px solid {accent["primary"]};
            background-color: #1C1C22;
        }}
        
        /* Right Dashboard Panel */
        #DashboardContainer {{
            background-color: #131317;
            border-left: 1px solid rgba(255, 255, 255, 0.05);
        }}
        
        #DashboardTitle {{
            font-size: 15px;
            font-weight: bold;
            color: #F8FAFC;
            margin-bottom: 12px;
        }}
        
        .DashboardCard {{
            background-color: #18181D;
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 8px;
            padding: 10px;
            margin-bottom: 8px;
        }}
        
        .TelemetryLabel {{
            font-size: 11px;
            color: #94A3B8;
        }}
        
        .TelemetryValue {{
            font-size: 13px;
            font-weight: bold;
            color: #F8FAFC;
        }}
        
        QProgressBar {{
            background-color: rgba(255, 255, 255, 0.08);
            border: none;
            border-radius: 3px;
            text-align: center;
            height: 6px;
        }}
        
        QProgressBar::chunk {{
            background-color: {accent["primary"]};
            border-radius: 3px;
        }}
        
        /* Interactive Buttons */
        QPushButton {{
            background-color: {accent["primary"]};
            color: #FFFFFF;
            border: none;
            border-radius: 6px;
            padding: 8px 16px;
            font-weight: 600;
        }}
        
        QPushButton:hover {{
            background-color: {accent["primary_hover"]};
        }}
        
        QPushButton:pressed {{
            background-color: {accent["primary_hover"]};
        }}
        """
