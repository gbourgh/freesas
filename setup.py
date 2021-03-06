#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import os
import platform
import glob
import numpy
from setuptools import setup
from setuptools.command.build_ext import build_ext as _build_ext
from numpy.distutils.core import Extension as _Extension

cmdclass = {}

#########
# Cython
#########

def check_cython():
    """
    Check if cython must be activated fron te command line or the environment.
    """

    if "WITH_CYTHON" in os.environ and os.environ["WITH_CYTHON"] == "False":
        print("No Cython requested by environment")
        return False

    if ("--no-cython" in sys.argv):
        sys.argv.remove("--no-cython")
        os.environ["WITH_CYTHON"] = "False"
        print("No Cython requested by command line")
        return False

    try:
        import Cython.Compiler.Version
    except ImportError:
        return False
    else:
        if Cython.Compiler.Version.version < "0.17":
            return False
    return True

def check_openmp():
    """
    Do we compile with OpenMP ?
    """
    if "WITH_OPENMP" in os.environ:
        print("OpenMP requested by environment: " + os.environ["WITH_OPENMP"])
        if os.environ["WITH_OPENMP"] == "False":
            return False
        else:
            return True
    if ("--no-openmp" in sys.argv):
        sys.argv.remove("--no-openmp")
        os.environ["WITH_OPENMP"] = "False"
        print("No OpenMP requested by command line")
        return False
    elif ("--openmp" in sys.argv):
        sys.argv.remove("--openmp")
        os.environ["WITH_OPENMP"] = "True"
        print("OpenMP requested by command line")
        return True

    if platform.system() == "Darwin":
        # By default Xcode5 & XCode6 do not support OpenMP, Xcode4 is OK.
        osx = tuple([int(i) for i in platform.mac_ver()[0].split(".")])
        if osx >= (10, 8):
            return False
    return True


USE_OPENMP = "openmp" if check_openmp() else ""
USE_CYTHON = check_cython()
if USE_CYTHON:
    from Cython.Build import cythonize


def Extension(name, source=None, can_use_openmp=False, extra_sources=None, **kwargs):
    """
    Wrapper for distutils' Extension
    """
    if source is None:
        sources = name.split(".")
    else:
        sources = source.split("/")
    cython_c_ext = ".pyx" if USE_CYTHON else ".c"
    sources = [os.path.join(*sources) + cython_c_ext]
    if extra_sources:
        sources.extend(extra_sources)
    if "include_dirs" in kwargs:
        include_dirs = set(kwargs.pop("include_dirs"))
        include_dirs.add(numpy.get_include())
        include_dirs = list(include_dirs)
    else:
        include_dirs = [numpy.get_include()]

    if can_use_openmp and USE_OPENMP:
        extra_compile_args = set(kwargs.pop("extra_compile_args", []))
        extra_compile_args.add(USE_OPENMP)
        kwargs["extra_compile_args"] = list(extra_compile_args)

        extra_link_args = set(kwargs.pop("extra_link_args", []))
        extra_link_args.add(USE_OPENMP)
        kwargs["extra_link_args"] = list(extra_link_args)

    ext = _Extension(name=name, sources=sources, include_dirs=include_dirs, **kwargs)

    if USE_CYTHON:
        cext = cythonize([ext], compile_time_env={"HAVE_OPENMP": bool(USE_OPENMP)})
        if cext:
            ext = cext[0]
    return ext


ext_modules = [
               Extension("freesas._distance", can_use_openmp=True),
               ]

script_files = glob.glob("scripts/*.py")

# ################### #
# build_doc commandes #
# ################### #

try:
    import sphinx
    import sphinx.util.console
    sphinx.util.console.color_terminal = lambda: False
    from sphinx.setup_command import BuildDoc
except ImportError:
    sphinx = None

if sphinx:
    class build_doc(BuildDoc):
        def run(self):

            # make sure the python path is pointing to the newly built
            # code so that the documentation is built on this and not a
            # previously installed version

            build = self.get_finalized_command('build')
            sys.path.insert(0, os.path.abspath(build.build_lib))

            # Build the Users Guide in HTML and TeX format
            for builder in ('html', 'latex'):
                self.builder = builder
                self.builder_target_dir = os.path.join(self.build_dir, builder)
                self.mkpath(self.builder_target_dir)
                BuildDoc.run(self)
            sys.path.pop(0)
    cmdclass['build_doc'] = build_doc

class build_ext(_build_ext):
    """
    We subclass the build_ext class in order to handle compiler flags
    for openmp and opencl etc in a cross platform way
    """
    translator = {
        # Compiler
        # name, compileflag, linkflag
        'msvc': {
            'openmp': ('/openmp', ' '),
            'debug': ('/Zi', ' '),
            'OpenCL': 'OpenCL',
        },
        'mingw32': {
            'openmp': ('-fopenmp', '-fopenmp'),
            'debug': ('-g', '-g'),
            'stdc++': 'stdc++',
            'OpenCL': 'OpenCL'
        },
        'default': {
            'openmp': ('-fopenmp', '-fopenmp'),
            'debug': ('-g', '-g'),
            'stdc++': 'stdc++',
            'OpenCL': 'OpenCL'
        }
    }

    def build_extensions(self):
        # print("Compiler: %s" % self.compiler.compiler_type)
        if self.compiler.compiler_type in self.translator:
            trans = self.translator[self.compiler.compiler_type]
        else:
            trans = self.translator['default']

        for e in self.extensions:
            e.extra_compile_args = [trans[arg][0] if arg in trans else arg
                                    for arg in e.extra_compile_args]
            e.extra_link_args = [trans[arg][1] if arg in trans else arg
                                 for arg in e.extra_link_args]
            e.libraries = [trans[arg] for arg in e.libraries if arg in trans]
        _build_ext.build_extensions(self)

cmdclass['build_ext'] = build_ext


setup(name="freesas",
      version="0.3",
      author="Guillaume Bonamis, Jerome Kieffer",
      author_email="jerome.kieffer@esrf.fr",
      description="Free tools to analyze Small angle scattering data",
      packages=["freesas"],
      test_suite="test",
      data_files=glob.glob("testdata/*"),
      scripts=script_files,
      install_requires=['numpy'],
      ext_modules=ext_modules,
      cmdclass=cmdclass
      )
