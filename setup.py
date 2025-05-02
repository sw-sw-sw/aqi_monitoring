from setuptools import setup, find_packages

setup(
    name="aqi_monitoring",
    version="0.2.0",
    description="神戸市須磨区の大気質と気象データを収集・分析するシステム",
    author="AQI Monitoring Team",
    author_email="info@example.com",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        # APIおよびウェブスクレイピング
        "requests>=2.28.0",
        "httpx>=0.23.0",  # HTTP クライアント（非同期サポート）
        # データ処理
        "pandas>=1.5.0",
        "numpy>=1.20.0",  # 数値計算ライブラリ
        # グラフィック生成
        "matplotlib>=3.5.0",
        "seaborn>=0.12.0",  # 統計データ可視化
        # HTMLパーシング
        "beautifulsoup4>=4.11.0",
        "lxml>=4.9.0",  # 高速XMLパーサー（BeautifulSoup用）
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
        # 地理データ処理（area_urls用）
        "geopy>=2.3.0",
        # 進捗表示
        "tqdm>=4.65.0",
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Atmospheric Science",
        "Topic :: Scientific/Engineering :: Visualization",
    ],
    entry_points={
        "console_scripts": [
            "aqi-scheduler=scheduler:main",
            "aqi-crawler=suma_crawler:main",
            "aqi-movie=movie_generator:main",
            "aqi-image-analyze=image_analyzer:main",
        ],
    },
    package_data={
        "aqi_monitoring": [
            "data/*.csv",
            "static/*.html",
        ],
    },
    include_package_data=True,
)