# Azure AI Agent 開発ハンズオントレーニングのドキュメント

|ドキュメント|トレーニングパート|内容|
|--|--|--|
|[1.deploy-resources.md](1.deploy-resources.md)|1. Azure リソースのデプロイ|今回のトレーニングで使用する Azure リソースとして、Storage アカウント、AI Search アカウント、AI Foundry ハブ/プロジェクトを Azure Portal 上で作成します|
|[2.setting-resources.md](2.setting-resources.md)|2. Azure リソースの設定|作成した Azure リソースの設定を行います。Storage へのファイルアップロードや、アクセス権限付与(RBAC)を行います|
|[3.prepare-index.md](3.prepare-index.md)|3. Azure AI Search インデックスの作成|作成した AI Search にインデックス、データソース、スキルセット、インデクサーを作成し、Pull 型でのインデックス作成を行います。このインデックスは AI エージェントの回答情報として使用されます|
|[4.develop-agent.md](4.develop-agent.md)|4. Azure AI Agent Service での AI エージェントの開発|AI Agent Service を使用して AI エージェントを開発します。基本的な処理から、ストリーミング出力を行う Python プログラムを実装します。そして、Web アプリケーションを実装して Azure Web Apps へデプロイします。|
|[5.extra-trainings.md](5.extra-trainings.md)|5. 追加のトレーニング|時間があれば行うコンテンツです。Semantic Kernel Agent Framework でマルチエージェント開発を行います|
|[6.clean-up.md](6.clean-up.md)|6. 後片付け|今回作成した Azure リソースを削除します。また GitHub Codespaces を使用している場合は、今回使用した Codespace も削除します。|