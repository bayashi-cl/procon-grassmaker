# procon-grassmaker

ACコードをアーカイブし、提出した日付に草を生やします。

(同じようなツールに[
procon-gardener](https://github.com/togatoga/procon-gardener)がありますが、こちらはACコードを**すべて**保存します。)

## 対応サービス

* [AtCoder](https://atcoder.jp)
* [codeforces](https://codeforces.com)
* [Aizu Online Judge](https://onlinejudge.u-aizu.ac.jp)

## usage

1. アーカイブ先で`git --init`（&& githubリポジトリを作成）
1. アーカイブ先に`.grassmaker/config.toml`を作成し、各サービスのユーサー名を設定
1. `procon-grassmaker --init` で設定ファイルを生成（生成先：`~/.config/procon-grassmaker/settings.toml`）
1. 設定ファイル内にアーカイブ先のパスを記入


## config.tomlの書式

```
[username]
atcoder = "bayashi_cl"
codeforces = "bayashi_cl"
aizuonlinejudge = "bayashi_cl"
```
