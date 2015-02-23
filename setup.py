from setuptool import setup, find_packages

ver_file = os.path.join('marlowe_ui', 'version.py')
vars = {}
exec(open(ver_file).read(), vars)

setup(
    name='ofblockmeshdicthelper',
    version=vars['__version__'],
    description='Helper utilities for OpenFOAM blockMeshDict generation.',
    long_description='Helper utilities for OpenFOAM blockMeshDict generation.',
    author='Takaaki AOKI',
    author_email='aoki.takaaki@gmail.com',
    url='https://github.com/takaakiaoki/ofblockmeshdicthelper',
    parckages=find_packages(),
    package_dir={'ofblockmeshdicthelper': 'ofblockmeshdicthelper'},
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.4",
        "License :: OSI Approved :: MIT License",
        "Development Status :: 4 - Beta",
        "Environment :: Other Environment",
        "Intended Audience :: Science/Research",
        "Operating System :: OS Independent",
        "Operating System :: Microsoft :: Windows :: Windows 7",
        "Topic :: Scientific/Engineering :: Physics"])
