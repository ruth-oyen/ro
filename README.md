# RO(Excel2Html) 
Excelファイル
![Excel](images/excel.png)
変換後のHtmlファイル
![Html](images/html.png)

## 説明
Excelファイルをhtmlに変換します。pushするGitHubのリポジトリをGitHub Pagesに設定すると、pushするだけでホームページを作ることができます。
<span style="color: red; ">
Excelファイルは個人樹法が紛れ込みやすいので注意してください。 ファイルのプロパティとかもチェックが必要です。pushする前に各種のAIにチェックさせるのもよいかと思います。
</span>

## アクセスカウンタ
[256さん](https://256server.com/)からお借りしています。[Moe Counter!](https://counter.256server.com/)で生成できます。
生成された文字列を[scripts/counter.txt](scripts/counter.txt)にいれてmakeすると[src/index.xlsx](src/index.xlsx)の{{ACCESS_COUNTER}}のテキストボックスの場所にアクセスカウンタを挿入したしたindex.htmlが生成されます。

## 課題
現状、表示するブラウザによって見え方がバラバラです。まあ、それも味かなと思ってしばらくは放置の予定。
