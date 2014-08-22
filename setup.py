import os
import setuptools

def read(fname):
	return open(os.path.join(os.path.dirname(__file__), fname)).read()

setuptools.setup(
	name="cvu",
	version="0.4.2",
	maintainer="Roan LaPlante",
	maintainer_email="rlaplant@nmr.mgh.harvard.edu",
	description=("A visualizer for human brain networks"),
	license="Visuddhimagga Sutta; GPLv3+",
	packages=["cvu"],
	package_data={'cvu':['data/*','fsavg5/label/*','fsavg5/surf/*','orders/*','cmaps/*']},
	data_files=[('licenses',['licenses/ENTHOUGHT_LICENSE',
					'licenses/YORICK_LICENSE','licenses/COLORBREWER_LICENSE']),
				('',['README','LICENSE'])],
	scripts=['bin/cvu'],
	url="https://github.com/aestrivex/cvu",
	long_description=read('README'),
	classifiers=[
		"Development Status :: 4 - Beta",
		"Environment :: X11 Applications",
		"Intended Audience :: Science/Research",
		"License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
		"Natural Language :: English",
		"Programming Language :: Python :: 2.7",
		"Topic :: Scientific/Engineering :: Visualization",
	],
	platforms=['any'],
	requires=["numpy","scipy","bctpy","mne"]
)
