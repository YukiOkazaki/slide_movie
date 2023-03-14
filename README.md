# slide_movie
CS解説のスライドを音声読み上げ付きで動画化します．  
参考：[GoogleスライドとOpen JTalkで動画作成 - Qiita](https://qiita.com/mananam/items/0007ec2bf69cf3132413)

## スライドから画像，シナリオを生成
- `convert.gs`の1行目に対象のスライド群が格納されているフォルダIDを指定
	- [【GAS】GoogleドライブのフォルダIDの取得方法](https://tetsuooo.net/gas/748/)
- GASで`convert.gs`の`saveSlide()`を実行
- 得られた画像とシナリオをダウンロード

## 画像とシナリオから動画を作成

### ディレクトリ構成
```
.
├── MMDAgent_Example-1.8
│   └── Voice
│       └── mei
│           └── mei_normal.htsvoice
├── caption_all.py
├── meiryo.ttc
├── out
├── silent_video
├── slide
│   ├── ...
│   ├── 4-3-1_WWWの話
│   ├── 4-3-2_Cookieの話
│   │   ├── 001.jpeg
│   │   ├── 002.jpeg
│   │   ├── ...
│   │   ├── 017.jpeg
│   │   ├── 018.jpeg
│   │   └── 4-3-2_Cookieの話-scenario.txt
│   ├── 4-3-3_HTTPとHTTPSの話
│   ├── 4-3-4_WWWのまとめの話
│   ├── ...
├── sound
└── video
```


### 前準備
- Open JTalkのインストール
	- [OpenJTalk + python で日本語テキストを発話 - Qiita](https://qiita.com/kkoba84/items/b828229c374a249965a9)
- FFmpegのインストール
	- [FFmpegのインストール（WSL環境） | Optical Learning Blog](http://optical-learning-blog.realop.co.jp/?eid=7)
- 読み上げ音声をダウンロードし解凍
	- [MMDAgent - Browse /MMDAgent_Example/MMDAgent_Example-1.8 at SourceForge.net](https://sourceforge.net/projects/mmdagent/files/MMDAgent_Example/MMDAgent_Example-1.8/)
- その他必要なPythonパッケージのインストール
- ダウンロードした画像とシナリオを解凍し，`slide`ディレクトリを作成し保存


### 動画化
- `caption_all.py`を実行する
- 生成された動画ファイルは`out`ディレクトリに格納される
