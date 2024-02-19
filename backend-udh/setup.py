import setuptools


with open("README.md") as fp:
    long_description = fp.read()


setuptools.setup(
    name="uniteddreamhomes-backend",
    version="0.0.1",

    description="uniteddreamhomes-backend",
    long_description=long_description,
    long_description_content_type="text/markdown",

    author="Jag",

    package_dir={"": "backend_udh"},
    packages=setuptools.find_packages(where="backend_udh"),

    install_requires=[
        "aws-cdk-lib==2.2.0",
        "constructs>=10.0.0,<11.0.0",
        'aws-cdk.aws-codestar-alpha>=2.0.0alpha1'
    ],    
    python_requires=">=3.6",

    classifiers=[
        "Development Status :: 4 - Beta",

        "Intended Audience :: Developers",

        "Programming Language :: JavaScript",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",

        "Topic :: Software Development :: Code Generators",
        "Topic :: Utilities",

        "Typing :: Typed",
    ],
)
