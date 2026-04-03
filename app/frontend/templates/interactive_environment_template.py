from __future__ import annotations

from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components
from utils.spritesheet_animation import play_spritesheet_animation


ROOT_DIR = Path(__file__).resolve().parents[3]
SPRITESHEET_PATH = ROOT_DIR / "Assets" / "gui" / "bar_chart_animation_spritesheet.png"


@st.cache_data(show_spinner=False)
def _interactive_sprite_css() -> str:
    if not SPRITESHEET_PATH.exists():
        return ""
    return play_spritesheet_animation(
        spritesheet=SPRITESHEET_PATH,
        px=640,
        speed=10,
        class_name=".interactive-sprite-bar-chart",
        display_size_px=44,
    )


def _with_loading_overlay(html: str, sprite_css: str) -> str:
    loader_style = """
    <style>
    body {
      position: relative;
    }
    #mynetwork {
      visibility: hidden;
      opacity: 0;
      transition: opacity 240ms ease;
    }
    #interactive-loader {
      position: absolute;
      inset: 0;
      z-index: 9999;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      gap: 16px;
      min-height: 760px;
      background: rgba(255, 255, 255, 0.94);
      transition: opacity 220ms ease;
    }
    #interactive-loader.is-hidden {
      opacity: 0;
      pointer-events: none;
    }
    .interactive-loader-breathe {
      animation: interactive-loader-breathe 2s ease-in-out infinite;
    }
    .interactive-loader {
      width: 168px;
      aspect-ratio: 1 / 1;
      position: relative;
      display: grid;
      place-items: center;
    }
    .interactive-loader-track {
      position: absolute;
      inset: 0;
      border-radius: 50%;
      border: 7px solid #d5f1e7;
    }
    .interactive-loader-progress {
      position: absolute;
      inset: 0;
      border-radius: 50%;
      background: conic-gradient(
        from 0deg,
        transparent 0deg 300deg,
        #23c58f 325deg 356deg,
        transparent 360deg
      );
      -webkit-mask: radial-gradient(farthest-side, transparent calc(100% - 7px), #000 calc(100% - 7px));
      mask: radial-gradient(farthest-side, transparent calc(100% - 7px), #000 calc(100% - 7px));
      animation: interactive-loader-spin 1.1s linear infinite;
    }
    .interactive-loader-core {
      width: 88px;
      aspect-ratio: 1 / 1;
      border-radius: 50%;
      background: linear-gradient(155deg, #3ccd84 0%, #22c98f 54%, #1ecdb4 100%);
      display: grid;
      place-items: center;
    }
    .interactive-sprite-bar-chart {
      width: 44px;
      height: 44px;
      background-repeat: no-repeat;
      background-position: 0 0;
      background-size: cover;
    }
    .interactive-loader-text {
      margin: 0;
      color: #6b7280;
      font-size: 16px;
      font-weight: 600;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }
    @keyframes interactive-loader-spin {
      from { transform: rotate(0deg); }
      to { transform: rotate(360deg); }
    }
    @keyframes interactive-loader-breathe {
      0% { transform: scale(0.82); }
      50% { transform: scale(0.95); }
      100% { transform: scale(0.82); }
    }
    __SPRITE_CSS__
    </style>
    """
    loader_style = loader_style.replace("__SPRITE_CSS__", sprite_css)

    loader_markup = """
    <div id="interactive-loader" aria-live="polite" aria-label="Loading interactive graph">
      <div class="interactive-loader-breathe">
        <div class="interactive-loader">
          <div class="interactive-loader-track"></div>
          <div class="interactive-loader-progress"></div>
          <div class="interactive-loader-core">
            <div class="interactive-sprite-bar-chart" aria-hidden="true"></div>
          </div>
        </div>
      </div>
      <p class="interactive-loader-text">Preparing interactive graph...</p>
    </div>
    """

    loader_script = """
    <script>
    (function () {
      var loader = document.getElementById("interactive-loader");
      var networkContainer = document.getElementById("mynetwork");
      var boundToNetwork = false;
      var revealed = false;

      function revealGraph() {
        if (revealed) return;
        revealed = true;

        if (networkContainer) {
          networkContainer.style.visibility = "visible";
          networkContainer.style.opacity = "1";
        }

        if (loader) {
          loader.classList.add("is-hidden");
          setTimeout(function () {
            if (loader && loader.parentNode) loader.parentNode.removeChild(loader);
          }, 240);
        }
      }

      function bindToNetworkStabilization() {
        if (boundToNetwork) return true;
        if (window.network && typeof window.network.once === "function") {
          window.network.once("stabilized", revealGraph);
          boundToNetwork = true;
          return true;
        }
        return false;
      }

      var bindInterval = setInterval(function () {
        if (bindToNetworkStabilization()) {
          clearInterval(bindInterval);
        }
      }, 100);

      window.addEventListener("load", function () {
        if (!bindToNetworkStabilization()) {
          setTimeout(revealGraph, 1200);
        }
      });

      setTimeout(function () {
        clearInterval(bindInterval);
        revealGraph();
      }, 8000);
    })();
    </script>
    """

    with_styles = html.replace("</head>", f"{loader_style}</head>", 1) if "</head>" in html else f"{loader_style}{html}"
    with_loader = with_styles.replace("<body>", f"<body>{loader_markup}", 1) if "<body>" in with_styles else f"{loader_markup}{with_styles}"
    return with_loader.replace("</body>", f"{loader_script}</body>", 1) if "</body>" in with_loader else f"{with_loader}{loader_script}"


def _inject_styles() -> None:
    st.markdown(
        """
        <style>
        .interactive-env-wrap {
            border: 1px solid #e5e7eb;
            border-radius: 12px;
            overflow: hidden;
            background: #ffffff;
            box-shadow: 0 1px 2px rgba(16, 24, 40, 0.04);
        }
        .interactive-env-note {
            margin: 0 0 12px 0;
            color: #64748b;
            font-size: 0.9rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_interactive_environment(title: str, graph_html_path: Path) -> None:
    _inject_styles()
    st.subheader(title)

    if not graph_html_path.exists():
        st.warning(f"Interactive graph not found: {graph_html_path}")
        return

    raw_html = graph_html_path.read_text(encoding="utf-8")
    embedded_html = _with_loading_overlay(raw_html, _interactive_sprite_css())

    st.markdown('<p class="interactive-env-note">Use mouse wheel to zoom, drag nodes, and click nodes/edges for details.</p>', unsafe_allow_html=True)
    st.markdown('<div class="interactive-env-wrap">', unsafe_allow_html=True)
    components.html(embedded_html, height=820, scrolling=True)
    st.markdown("</div>", unsafe_allow_html=True)
