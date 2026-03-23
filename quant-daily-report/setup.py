from setuptools import setup, find_packages

with open('README.md', 'r', encoding='utf-8') as f:
    long_description = f.read()

with open('requirements.txt', 'r', encoding='utf-8') as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name='quant-daily-report',
    version='1.0.0',
    description='A股量化日报系统 - 全自动量化分析与报告生成系统',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Quant Research Team',
    author_email='your-email@example.com',
    url='https://github.com/your-username/quant-daily-report',
    packages=find_packages(exclude=['tests', 'docs']),
    install_requires=requirements,
    extras_require={
        'dev': [
            'pytest>=7.4.4',
            'pytest-cov>=4.1.0',
            'black>=23.12.1',
            'flake8>=6.1.0',
            'isort>=5.12.0',
            'mypy>=1.8.0'
        ]
    },
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Intended Audience :: Financial and Insurance Industry',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Topic :: Office/Business :: Financial :: Investment',
        'Topic :: Scientific/Engineering :: Information Analysis',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    python_requires='>=3.10',
    entry_points={
        'console_scripts': [
            'quant-daily=main:main',
        ],
    },
    include_package_data=True,
    package_data={
        '': ['*.yaml', '*.json', '*.md'],
    },
    keywords='quantitative, finance, stock market, a-shares, qlib, backtesting',
    project_urls={
        'Bug Reports': 'https://github.com/your-username/quant-daily-report/issues',
        'Source': 'https://github.com/your-username/quant-daily-report',
        'Documentation': 'https://quant-daily-report.readthedocs.io/',
    },
)