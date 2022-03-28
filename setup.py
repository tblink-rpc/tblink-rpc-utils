
import os, stat
from setuptools import setup
from setuptools.command.install import install

rootdir = os.path.dirname(os.path.realpath(__file__))

version="0.0.1"

if "BUILD_NUM" in os.environ.keys():
    version += "." + os.environ["BUILD_NUM"]

setup(
  name = "tblink-rpc-utils",
  version = version,
  packages=['tblink_rpc_utils'],
  package_dir = {'' : 'src'},
  author = "Matthew Ballance",
  author_email = "matt.ballance@gmail.com",
  description = ("TbLink-RPC code generation utilities."),
  license = "Apache 2.0",
  keywords = ["SystemVerilog", "Verilog", "RTL"],
  url = "https://github.com/tblink-rpc/tblink-rpc-utils",
  entry_points={
    'console_scripts': [
      'tblink-rpc-utils = tblink_rpc_utils.__main__:main'
    ]
  },
  setup_requires=[
    'setuptools_scm',
  ],
  install_requires=[
      'pyyaml',
      'pykwalify',
      'pyyaml-srcinfo-loader',
      'pytblink_rpc',
  ],
)

