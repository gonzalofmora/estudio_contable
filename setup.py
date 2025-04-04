from setuptools import setup, find_packages

setup(
    name="estudio_contable",
    version="0.1",
    description="automatizaciones para un estudio contable",
    author="G.M.",
    packages=find_packages(where="src"),  # Look for packages in the "src" directory
    package_dir={"": "src"},  # Tell setuptools that packages are under "src"
    install_requires=[
        "pandas>=2.2.3"
    ],
    python_requires=">=3.12"
)

###GABITOOOO