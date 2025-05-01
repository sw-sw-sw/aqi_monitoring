from setuptools import setup, find_packages

setup(
    name="aqi_monitoring",
    version="0.1.0",
    description="神戸市須磨区の大気質と気象データを収集・分析するシステム",
    author="AQI Monitoring Team",
    author_email="info@example.com",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        # APIおよびウェブスクレイピング
        "requests>=2.28.0",
        # データ処理
        "pandas>=1.5.0",
        # グラフィック生成
        "matplotlib>=3.5.0",
        # HTMLパーシング
        "beautifulsoup4>=4.11.0",
        # 画像処理
        "Pillow>=9.0.0",
        # 動画生成
        "opencv-python>=4.5.0",
        # 環境変数管理
        "python-dotenv>=0.19.0",
        # Anthropic API
        "anthropic>=0.5.0",
        # Webアプリケーション
        "flask>=2.0.0",
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Scientific/Engineering :: Atmospheric Science",
    ],
    entry_points={
        "console_scripts": [
            "aqi-scheduler=scheduler:main",
            "aqi-crawler=suma_crawler:main",
        ],
    },
)