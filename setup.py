from setuptools import setup, find_packages


install_requires = [
    'pymmcore-plus',
    'opencv-python>=4.7.0',
    'matplotlib',
    'scikit-image',
    'pandas',
    'numpy',
    'logger',
    'ipdb'
]


setup(
    name="ControlCamera",
    version="0.0.1",
    description="A class to control cameras interfaced with Micro-Manager",
    author="Alienor Lahlou",
    author_email="alienor.lahlou@sony.com",
    packages=find_packages(),
    install_requires=install_requires,
    license="GPLv3",
    python_requires=">=3.7",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)