
{ pkgs }: {
  deps = [
    pkgs.swig4
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
    pkgs.swig
    pkgs.opencascade-occt
    pkgs.libGLU
    pkgs.libGL
    pkgs.freetype
    pkgs.freefont_ttf
    pkgs.xsimd
    pkgs.pkg-config
    pkgs.libxcrypt
    pkgs.python312
    pkgs.python312Packages.pip
    pkgs.python312Packages.setuptools
  ];
}
