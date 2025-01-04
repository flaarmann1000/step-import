
{ pkgs }: {
  deps = [
    pkgs.swig4
    pkgs.opencascade-occt
    pkgs.swig
    pkgs.python312
    pkgs.python312Packages.pip
    pkgs.python312Packages.pythonocc-core
    pkgs.rapidjson
    pkgs.fontconfig
    pkgs.tk
    pkgs.tcl
    pkgs.qhull
    pkgs.gtk3
    pkgs.gobject-introspection
    pkgs.ghostscript
    pkgs.ffmpeg-full
    pkgs.cairo
    pkgs.libGLU
    pkgs.libGL
    pkgs.freetype
    pkgs.freefont_ttf
    pkgs.xorg.libX11
    pkgs.xorg.libXrender
    pkgs.xorg.libXext
    pkgs.xsimd
    pkgs.pkg-config
    pkgs.libxcrypt
  ];
}
