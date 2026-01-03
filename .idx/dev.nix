
{ pkgs, ... }:
{
  channel = "stable-24.05";

  packages = [
    pkgs.python312
    pkgs.python312Packages.pip

    pkgs.poppler_utils
    pkgs.ffmpeg

    pkgs.libjpeg
    pkgs.zlib
    pkgs.libtiff
    pkgs.freetype
    pkgs.lcms2
    pkgs.libwebp
    pkgs.harfbuzz
    pkgs.fribidi

    # X11 libs
    pkgs.xorg.libxcb
    pkgs.xorg.libSM
    pkgs.xorg.libXext

    pkgs.libreoffice

    # OpenGL stack
    pkgs.mesa
    pkgs.libglvnd
    pkgs.mesa.drivers

    # 🔹 NEW: GLib (provides libgthread-2.0.so.0)
    pkgs.glib
    pkgs.gh
  ];

  env = {
    PYTHONUTF8 = "1";

    # 🔹 Make Nix store libs visible to native wheels at runtime
    #    (glib provides libgthread-2.0.so.0 here)
    LD_LIBRARY_PATH =
      "${pkgs.stdenv.cc.cc.lib}/lib:${pkgs.mesa}/lib:${pkgs.libglvnd}/lib:${pkgs.glib}/lib";
  };

  idx = {
    extensions = [
      "ms-python.python"
      "ms-python.vscode-pylance"
      "ms-python.black-formatter"
      "ms-python.flake8"
      "ms-python.pylint"
      "ms-toolsai.jupyter"
    ];
    previews = { enable = true; previews = { }; };
    workspace = {
      onCreate = { note = "echo 'Workspace created — bootstrap handled in onStart'"; };
      onStart = {
        ensure-venv = ''
          if [ ! -x ".venv/bin/python" ]; then
            echo "[IDX] Creating Python venv..."
            python3 -m venv .venv
          fi
          echo "[IDX] Upgrading pip & installing requirements (if present)..."
          .venv/bin/python -m pip install --upgrade pip setuptools wheel

          # 🔹 Enforce headless OpenCV to avoid GUI/GLib linkage issues
          .venv/bin/python -m pip uninstall -y opencv-python opencv-contrib-python || true
          .venv/bin/python -m pip install --upgrade "opencv-python-headless>=4.8,<5"

          # NOTE: make sure requirements.txt doesn't re-add `opencv-python`
          if [ -f requirements.txt ]; then
            grep -i "opencv-python" requirements.txt && \
              echo "[IDX] ⚠️ requirements.txt lists GUI OpenCV — please remove it." || true
            .venv/bin/python -m pip install -r requirements.txt
          fi
        '';
        check-tools = ''
          which python3 || true
          pdftoppm -v || true
          ffmpeg -version || true
        '';
      };
    };
  };
}
