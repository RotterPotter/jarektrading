from setuptools import find_packages, setup

# Ensure the README exists
try:
    with open("app/Readme.md", "r") as f:
        long_description = f.read()
except FileNotFoundError:
    long_description = "Helpful model for trading."

setup(
    name="jarektrading",
    version="0.2.2",
    description="Helpful model for trading.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="",
    author="Oleksandr Nazarevych",
    author_email="oleksandr.o.nazarevych@gmail.com",
    license="MIT",
    package_dir={"": "app"},  # Specify the root folder
    packages=find_packages(where="app"),  # Automatically find packages in "app"
    install_requires=[],  # Corrected typo
    extras_require={
        "dev": ["twine>=4.0.2"],
    },
    python_requires=">=3.10",
    classifiers=[
        "License :: OSI Approved :: MIT License"
    ],
)
