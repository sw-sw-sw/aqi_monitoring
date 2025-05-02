from setuptools import setup, find_packages

setup(
    name="aqi_monitoring",
    version="0.3.0",  # バージョンを0.2.1から0.3.0へアップデート
    description="神戸市須磨区の大気質と気象データを収集・分析・可視化するシステム",
    long_description="""
    AQI Monitoring は神戸市須磨区の大気質指数(AQI)と気象データを自動的に収集し、
    分析・可視化するシステムです。Web APIからのデータ取得、大気質データの時系列分析、
    フーリエ解析による周期性の検出、ライブカメラ画像の収集と分析などの機能を備えています。
    また、収集したデータからタイムラプス動画の生成や、大気中の飛行機雲の検出も可能です。
    """,
    long_description_content_type="text/markdown",
    author="AQI Monitoring Team",
    author_email="info@example.com",
    url="https://github.com/example/aqi_monitoring",  # リポジトリURLを追加
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        # APIおよびウェブスクレイピング
        "requests>=2.31.0",
        "httpx>=0.25.0",  # HTTP クライアント（非同期サポート）
        
        # データ処理
        "pandas>=2.0.0",
        "numpy>=1.24.0",  # 数値計算ライブラリ
        
        # 科学計算・信号処理
        "scipy>=1.10.0",  # フーリエ変換などの科学計算
        "scikit-learn>=1.2.0",  # 機械学習ライブラリ
        
        # グラフィック生成
        "matplotlib>=3.7.0",
        "seaborn>=0.12.0",  # 統計データ可視化
        
        # HTMLパーシング
        "beautifulsoup4>=4.12.0",
        "lxml>=4.9.0",  # 高速XMLパーサー（BeautifulSoup用）
        
        # 画像処理
        "Pillow>=10.0.0",
        "opencv-python>=4.8.0",  # 画像処理・動画生成
        
        # 環境変数管理
        "python-dotenv>=1.0.0",
        
        # AI API関連
        "anthropic>=0.8.0",  # Claude API
        "openai>=1.0.0",  # OpenAI API（Qwen API互換用）
        
        # Webアプリケーション
        "flask>=2.3.0",
        
        # 地理データ処理
        "geopy>=2.4.0",
        
        # 進捗表示
        "tqdm>=4.66.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "black>=23.7.0",
            "isort>=5.12.0",
            "flake8>=6.1.0",
            "mypy>=1.5.0",
        ],
        "docs": [
            "sphinx>=7.1.0",
            "sphinx-rtd-theme>=1.2.0",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",  # アルファからベータへ
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",  # ライセンスを追加
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",  # Python 3.12サポートを追加
        "Topic :: Scientific/Engineering :: Atmospheric Science",
        "Topic :: Scientific/Engineering :: Visualization",
        "Topic :: Scientific/Engineering :: Image Processing",
    ],
    entry_points={
        "console_scripts": [
            # 基本コマンド
            "aqi-scheduler=scheduler:main",
            "aqi-crawler=suma_crawler:main",
            "aqi-movie=movie_generator:main",
            
            # 画像分析関連
            "aqi-image-analyze=img_analyzer_claude:main",  # 名前変更
            "aqi-cloud-analyze=img_analyzer_qwen:main",   # Qwen分析追加
            
            # データ処理関連
            "aqi-fetch=aqi_scraper:fetch_aqi_data",
            "aqi-graph=graph_generator:generate_graph",
            "aqi-fourier=graph_generator2:generate_fourier_analysis",
            
            # 位置情報関連
            "aqi-find-nearest=area_urls.find_nearest_points:find_nearest_points",
            "aqi-geocode=area_urls.google_geocording_module:geocode",
        ],
    },
    package_data={
        "aqi_monitoring": [
            # データファイル
            "data/*.csv",
            "data/forecast/*.json",
            "data/debug/*.json",
            "data/image_web_urls/*.csv",
            
            # 画像関連
            "data/image_analysis/**/*.json",
            "data/image_crawler_data/**/*.jpg",
            "data/movies/**/*.mp4",
            
            # Webアプリケーション関連
            "static/*.html",
            "static/*.css",
            "static/*.js",
            "static/images/*.png",
        ],
    },
    include_package_data=True,
    zip_safe=False,  # インストール時にパッケージを展開
)