from setuptools import setup, find_packages

setup(
    name='dianplus-printer',  # 项目名称
    version='0.0.1',           # 项目版本
    packages=find_packages(),  # 自动找到项目中的包
    install_requires=[
        # 项目依赖的其他 Python 包，例如：
        'pyqt6>=6.8.0',
        'PyQt6-WebEngine>=6.8.0',
        'flask>=3.1.0',
        'waitress>=3.0.2',
        'pyinstaller>=6.11.1',
    ],
    entry_points={
        'console_scripts': [
            'start=app:main',  # 可执行脚本的入口点
        ],
    },
    author='jingtian',           # 作者名字
    author_email='jingtian@dianplus.cn',  # 作者邮箱
    description='支持网络打印的插件',  # 项目简短描述
    long_description=open('README.md').read(),  # 项目详细描述，通常从 README 文件中读取
    long_description_content_type='text/markdown',  # README 文件格式
    url='https://git.dianplus.cn/frontend/python-printer',  # 项目主页链接
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.9',  # 项目支持的 Python 版本
)