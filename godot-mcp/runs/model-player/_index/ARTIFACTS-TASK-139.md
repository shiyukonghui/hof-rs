# ARTIFACTS-TASK-139 — 关键产物清单（路径 + sha256 + 大小 + 生成命令）

> 为什么入库：`runs/**` 被 `.gitignore` 忽略（第 12 行 `runs/`、第 43 行
> 为什么入库：`runs/**` 被 `.gitignore` 忽略（第 12 行 `runs/`、第 43 行
> `godot-mcp/runs/`），报告引用的每个 run 产物只存在于本机。本文件把**关键产物**
> 的 sha256 / 大小 / 生成命令**提交进仓**，使结论在 `runs/**` 不入库的前提下仍可事后核验。
>
> 复算：`certutil -hashfile <path> SHA256`，或重跑本清单的生成器
> （命令见本文件表头的 §复算）。

* 生成时刻：`2026-09-28T06:36:10`
* run 目录数：**100**；索引文件数：**800**
* 复算命令：`D:\Anaconda\python.exe tools\playtest_artifact_index.py --task TASK-139 --roots t139-scripted-w30 t139-scripted-w90 t139-jev-v3-w30 t139-jev-v3-w90 t139-playjev-v3-w30 t139-determinism-w30 t139-determinism-w90 runs\model-player\_scripts\t139_results_*.json`

## t139-scripted-w30 / asteroids / scripted

* 目录：`runs/model-player/t139-scripted-w30/asteroids/scripted`
* verdict：`PASS`（counts_as_pass=True，strict=PASS，baseline=PASS，game_side=PASS）
* 注入/接受后变化/rate：8 / 8 / 1.0
* 两窗对齐：1/8 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 3 frame(s))（matched 1/8，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game asteroids --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9963 --window-frames 30 --out-prefix t139-jev-v3-w30`  <- t139_results_t139-jev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game asteroids --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9964 --window-frames 90 --out-prefix t139-jev-v3-w90`  <- t139_results_t139-jev-v3-w90.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game asteroids --backend playjev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9965 --window-frames 30 --out-prefix t139-playjev-v3-w30`  <- t139_results_t139-playjev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game asteroids --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9961 --window-frames 30 --out-prefix t139-scripted-w30`  <- t139_results_t139-scripted-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game asteroids --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9962 --window-frames 90 --out-prefix t139-scripted-w90`  <- t139_results_t139-scripted-w90.json (sweep driver)

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t139-scripted-w30/asteroids/scripted/demo.png` | 88032 | `3fe3d5d5a1f5def9ca6e031506b6a4deade0ae7d9d8ccfaec3ae1343b67f0ebf` |
| `runs/model-player/t139-scripted-w30/asteroids/scripted/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t139-scripted-w30/asteroids/scripted/engine-game.stdout.txt` | 741 | `07ce40c430f219e501ee5621769132f42106f0573b5103e4d631013ac479242d` |
| `runs/model-player/t139-scripted-w30/asteroids/scripted/filmstrip.png` | 51479 | `e0807ec7a26fa05983d34618d89c3cee0877bf8dc1a68dd513e1d1c4eaf35278` |
| `runs/model-player/t139-scripted-w30/asteroids/scripted/frames.json` | 374025 | `e5dff8715576c5619e8b28e121fa27f1a88fefa8153f5d0099fcad694a568fcf` |
| `runs/model-player/t139-scripted-w30/asteroids/scripted/player.json` | 20177 | `3b8268f7cc5aaf449d04c70a0301ade146c48d49c5f560ab707bc2834d86ad27` |
| `runs/model-player/t139-scripted-w30/asteroids/scripted/session.json` | 11258 | `27aabbcf1c0d5f6cf5a73740aa9d8779b1ea3c772709c9955986fdcbc8a6759d` |
| `runs/model-player/t139-scripted-w30/asteroids/scripted/steps.jsonl` | 103934 | `692171eb0db499ca4b57352c893c420ba5215a7ca158436f183fac498223c91b` |
| `calls/**`（341 个文件，1664409 B）| — | `96bfa0181c1d08c4ce5428b60329d71de710821689c0b420c9b91ddfe98c9b69` |
| `frames/**`（25 个文件，262397 B）| — | `394a361341f2e766f3e98490cca9b52545c7648eaf4a5b3c9fe66d5c7d543662` |
| `states/**`（19 个文件，56440 B）| — | `69a442a726afc2b666a3f10417f5f49467190f808885a71de50b5c3d0b4ba5ef` |

## t139-scripted-w30 / bomberman / scripted

* 目录：`runs/model-player/t139-scripted-w30/bomberman/scripted`
* verdict：`INCONCLUSIVE`（counts_as_pass=False，strict=INCONCLUSIVE，baseline=INCONCLUSIVE，game_side=FAIL）
* 注入/接受后变化/rate：12 / 6 / 0.6667
* 两窗对齐：5/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 4 frame(s))（matched 5/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game bomberman --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9963 --window-frames 30 --out-prefix t139-jev-v3-w30`  <- t139_results_t139-jev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game bomberman --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9964 --window-frames 90 --out-prefix t139-jev-v3-w90`  <- t139_results_t139-jev-v3-w90.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game bomberman --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9961 --window-frames 30 --out-prefix t139-scripted-w30`  <- t139_results_t139-scripted-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game bomberman --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9962 --window-frames 90 --out-prefix t139-scripted-w90`  <- t139_results_t139-scripted-w90.json (sweep driver)

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t139-scripted-w30/bomberman/scripted/demo.png` | 154435 | `d4db95906fc39923d9cf85540d7e08b7969b2b0f75e597a919249039c0418dd5` |
| `runs/model-player/t139-scripted-w30/bomberman/scripted/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t139-scripted-w30/bomberman/scripted/engine-game.stdout.txt` | 775 | `e09174de86602854912b848a0e864fdb9f4ae4beebfcf6eaec3facff486f6e5c` |
| `runs/model-player/t139-scripted-w30/bomberman/scripted/filmstrip.png` | 143686 | `c1cd831d3cc1505bb40238b3ba49f6c44ebe377dc5d20724aea25859247050c6` |
| `runs/model-player/t139-scripted-w30/bomberman/scripted/frames.json` | 511988 | `7cc727a973682264e82b46eca536e87f96ac95735a27c885606eb0272d96d8cf` |
| `runs/model-player/t139-scripted-w30/bomberman/scripted/player.json` | 26174 | `fb4accff2e05513c58daca22122009f8a28cfa17cc971ae7d7a588d54ceea59b` |
| `runs/model-player/t139-scripted-w30/bomberman/scripted/session.json` | 11374 | `e1aa0d10a97d9b91f460cb13a82c43b6350677a258b46a21187f7dd14eb2a606` |
| `runs/model-player/t139-scripted-w30/bomberman/scripted/steps.jsonl` | 142842 | `0e5da51c0c45b7a5c8d258f4c403dd8c5a4542a7d8b0fee9c1bc2e9f139e9332` |
| `calls/**`（461 个文件，7113949 B）| — | `777785dccfc51163bc924f79fc12ef36e2ead8ad60b90ab8d3f4a1e150f86e73` |
| `frames/**`（37 个文件，357119 B）| — | `eebdc08291b178f01432b48aa66890a50830f036c22e0c6a033f43ae64df98e4` |
| `states/**`（27 个文件，600564 B）| — | `c9a9f341e7f473de31b395cbc620f205b2e209103c1848247fd869fe604291e3` |

## t139-scripted-w30 / breakout / scripted

* 目录：`runs/model-player/t139-scripted-w30/breakout/scripted`
* verdict：`INCONCLUSIVE`（counts_as_pass=False，strict=INCONCLUSIVE，baseline=INCONCLUSIVE，game_side=INCONCLUSIVE）
* 注入/接受后变化/rate：3 / 3 / 1.0
* 两窗对齐：1/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 6 frame(s))（matched 1/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game breakout --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9963 --window-frames 30 --out-prefix t139-jev-v3-w30`  <- t139_results_t139-jev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game breakout --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9964 --window-frames 90 --out-prefix t139-jev-v3-w90`  <- t139_results_t139-jev-v3-w90.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game breakout --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9961 --window-frames 30 --out-prefix t139-scripted-w30`  <- t139_results_t139-scripted-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game breakout --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9962 --window-frames 90 --out-prefix t139-scripted-w90`  <- t139_results_t139-scripted-w90.json (sweep driver)

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t139-scripted-w30/breakout/scripted/demo.png` | 100739 | `e86a68e5d69d0cdc7dab55474ead5b286ff3a479adc928dd06334aa856d8dc78` |
| `runs/model-player/t139-scripted-w30/breakout/scripted/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t139-scripted-w30/breakout/scripted/engine-game.stdout.txt` | 3633 | `c33c44ca4f3861ca56185bf645d10e9ded0c40cf84fdbce4b962150152838d98` |
| `runs/model-player/t139-scripted-w30/breakout/scripted/filmstrip.png` | 74965 | `1aba600d122a664d4a181ab911b37829491bb30769940874491bb03ca9b5c331` |
| `runs/model-player/t139-scripted-w30/breakout/scripted/frames.json` | 568785 | `7230426129af4586684aeaf195caeea094c1f7e90f506fb3c5a350a6a5da55d0` |
| `runs/model-player/t139-scripted-w30/breakout/scripted/player.json` | 22356 | `833293b3c1908c4f5295dbbecf2f6fda115ae1ea1f3e5b0ad688c83a4ea38ab6` |
| `runs/model-player/t139-scripted-w30/breakout/scripted/session.json` | 11425 | `836a30d02ba4fcee3df6a3e318761844eb9df83354f165511c2f82c00c81f421` |
| `runs/model-player/t139-scripted-w30/breakout/scripted/steps.jsonl` | 126292 | `0db9707b21a04b56c3ca3cd93673f463abf9ca02c03edfd0464fdb3c8902b130` |
| `calls/**`（378 个文件，2790432 B）| — | `be9ab438448b2a09d9eabeab783389f1695db8398f9756a75571b3f3521f14e7` |
| `frames/**`（37 个文件，399844 B）| — | `a324988ecebf1967d6c4dbe3bf47bb87bc89539a57450d7fae3c2c756873bcde` |
| `states/**`（27 个文件，148611 B）| — | `93cb422c213992e2305fffaa4d5b9233ef5219184481ed4bc70ffbe4b7014baf` |

## t139-scripted-w30 / flappy / scripted

* 目录：`runs/model-player/t139-scripted-w30/flappy/scripted`
* verdict：`INCONCLUSIVE`（counts_as_pass=False，strict=INCONCLUSIVE，baseline=INCONCLUSIVE，game_side=FAIL）
* 注入/接受后变化/rate：12 / 1 / 0.0833
* 两窗对齐：3/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 4 frame(s))（matched 3/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game flappy --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9963 --window-frames 30 --out-prefix t139-jev-v3-w30`  <- t139_results_t139-jev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game flappy --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9964 --window-frames 90 --out-prefix t139-jev-v3-w90`  <- t139_results_t139-jev-v3-w90.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game flappy --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9961 --window-frames 30 --out-prefix t139-scripted-w30`  <- t139_results_t139-scripted-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game flappy --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9962 --window-frames 90 --out-prefix t139-scripted-w90`  <- t139_results_t139-scripted-w90.json (sweep driver)

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t139-scripted-w30/flappy/scripted/demo.png` | 97895 | `68904e5f6fdcb966de5812afa3c04682bbf26f4e347ba4aca30a6d87a32cff6b` |
| `runs/model-player/t139-scripted-w30/flappy/scripted/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t139-scripted-w30/flappy/scripted/engine-game.stdout.txt` | 744 | `22e6de9f49c673c0e07bd44f335e190e1589046f765d3f2b910325838bf068d1` |
| `runs/model-player/t139-scripted-w30/flappy/scripted/filmstrip.png` | 62706 | `ae8ef0baf441cc641d717f76f71d258e5f31301a4ba3d2d5d4f6595f1e320ce9` |
| `runs/model-player/t139-scripted-w30/flappy/scripted/frames.json` | 474337 | `6145b13b5fe797efef6847a54762908eee224a8d4419ad4c303b8cc05f258663` |
| `runs/model-player/t139-scripted-w30/flappy/scripted/player.json` | 24241 | `1e88402b622a865767cc63bd1bef79ce35ea7fd0dd2a18678135f45740c89090` |
| `runs/model-player/t139-scripted-w30/flappy/scripted/session.json` | 11211 | `dcbe22d6b6deb82e92d520ca5125a394ae1947a3a4aa12f639461bdc6d0a83d5` |
| `runs/model-player/t139-scripted-w30/flappy/scripted/steps.jsonl` | 128242 | `503795bafd30274dbc579a052e2f6c0ae4b6a74f8a5a4fc9ac57edbc47d2c5d1` |
| `calls/**`（510 个文件，2170112 B）| — | `f792e72c3806fc0507550e606531084bc16f684c5908835fcaeb049961937fdd` |
| `frames/**`（37 个文件，329115 B）| — | `d4631f22c8f94877eea5c94abd5151f1b42cfd17228cef47cb38a45d23b4ac49` |
| `states/**`（27 个文件，77141 B）| — | `ee6c83baeb33d50b37511c22c77fc39067e4e659dc3ed89ba812ac9c9d0a4d3d` |

## t139-scripted-w30 / frogger / scripted

* 目录：`runs/model-player/t139-scripted-w30/frogger/scripted`
* verdict：`INCONCLUSIVE`（counts_as_pass=False，strict=INCONCLUSIVE，baseline=INCONCLUSIVE，game_side=INCONCLUSIVE）
* 注入/接受后变化/rate：1 / 1 / 1.0
* 两窗对齐：0/1 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 1 frame(s))（matched 0/1，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game frogger --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9963 --window-frames 30 --out-prefix t139-jev-v3-w30`  <- t139_results_t139-jev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game frogger --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9964 --window-frames 90 --out-prefix t139-jev-v3-w90`  <- t139_results_t139-jev-v3-w90.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game frogger --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9961 --window-frames 30 --out-prefix t139-scripted-w30`  <- t139_results_t139-scripted-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game frogger --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9962 --window-frames 90 --out-prefix t139-scripted-w90`  <- t139_results_t139-scripted-w90.json (sweep driver)

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t139-scripted-w30/frogger/scripted/demo.png` | 15281 | `8fdec9ae10fdf45f61ef6aebc6726486492e194502b90f155db542222f430881` |
| `runs/model-player/t139-scripted-w30/frogger/scripted/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t139-scripted-w30/frogger/scripted/engine-game.stdout.txt` | 748 | `00e666f2aac546ce8e4fcace522dec5861804969d2feaa8c03aa81e068470e7b` |
| `runs/model-player/t139-scripted-w30/frogger/scripted/filmstrip.png` | 13847 | `41a1abe17bb8745049b0c731ffc6e75789fdeac125e14be700cf546557e0b969` |
| `runs/model-player/t139-scripted-w30/frogger/scripted/frames.json` | 63852 | `cb32981163cea340cf11399b4d8b2319b186ff0c42f78ae09cacaf5e20904312` |
| `runs/model-player/t139-scripted-w30/frogger/scripted/player.json` | 16465 | `f3d4b551ccc1e9f47670525a4ccf04665d818e079ba36deeb08fbde93dd2a6c3` |
| `runs/model-player/t139-scripted-w30/frogger/scripted/session.json` | 11163 | `aaf66cf2a0c8378767ba9d491cb8d0ed9ed70f3db717200b277a79dfe24859b2` |
| `runs/model-player/t139-scripted-w30/frogger/scripted/steps.jsonl` | 10847 | `ec16bec635da869ac31e6db2c7651b3e31f91a6641d5ec70e38210c2522d2160` |
| `calls/**`（40 个文件，233952 B）| — | `03117ab4cc07144f5ea7c4d8ca6e135ef3664abb4a90ec218510de38f9e2c0b0` |
| `frames/**`（4 个文件，45009 B）| — | `a678506b06b394a34820e8b1ec8e4bf7bf5d3f89df744798032147faea1a3201` |
| `states/**`（5 个文件，21032 B）| — | `b775a8e9db8ee687b1af530a0e9485f9a5dca7cce15ee8b5310528fe90fde6e4` |

## t139-scripted-w30 / game2048 / scripted

* 目录：`runs/model-player/t139-scripted-w30/game2048/scripted`
* verdict：`PASS`（counts_as_pass=True，strict=PASS，baseline=PASS，game_side=PASS）
* 注入/接受后变化/rate：8 / 8 / 1.0
* 两窗对齐：1/8 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 3 frame(s))（matched 1/8，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game game2048 --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9963 --window-frames 30 --out-prefix t139-jev-v3-w30`  <- t139_results_t139-jev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game game2048 --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9964 --window-frames 90 --out-prefix t139-jev-v3-w90`  <- t139_results_t139-jev-v3-w90.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game game2048 --backend playjev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9965 --window-frames 30 --out-prefix t139-playjev-v3-w30`  <- t139_results_t139-playjev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game game2048 --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9961 --window-frames 30 --out-prefix t139-scripted-w30`  <- t139_results_t139-scripted-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game game2048 --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9962 --window-frames 90 --out-prefix t139-scripted-w90`  <- t139_results_t139-scripted-w90.json (sweep driver)

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t139-scripted-w30/game2048/scripted/demo.png` | 105326 | `96cd977cad7a157a05cd9b6c6bd772ba6d05f9e17ffbad42242d83a4ba36b822` |
| `runs/model-player/t139-scripted-w30/game2048/scripted/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t139-scripted-w30/game2048/scripted/engine-game.stdout.txt` | 781 | `1f995cb03cea9b51e4c3c4c5c8e140e45874fca5332f2088a05451d7462f1f9d` |
| `runs/model-player/t139-scripted-w30/game2048/scripted/filmstrip.png` | 65250 | `8b39ca1c5bc016326495bf62fcef6deb85db6194028962d7ac1691659d624cf2` |
| `runs/model-player/t139-scripted-w30/game2048/scripted/frames.json` | 452846 | `40bd1b3d886c8941e5b13f71107e294129da2b308d5ec2b8f8d3500756df801f` |
| `runs/model-player/t139-scripted-w30/game2048/scripted/player.json` | 20037 | `5f342e5a64c5558b25f75546f71f651d0a245b3142b1f3c8e833eeb4be1d5cc2` |
| `runs/model-player/t139-scripted-w30/game2048/scripted/session.json` | 11114 | `52c101b2e748b6e36e8b99b4883d18c4c48b1b0928740b56ca4b290516fb4c47` |
| `runs/model-player/t139-scripted-w30/game2048/scripted/steps.jsonl` | 104862 | `0710663f47c824c963356b867381a9e220b1a3f719c14168ac0b12a53d94c671` |
| `calls/**`（337 个文件，2699473 B）| — | `52cb4f71e401467d1f69f3eaec19bbcdf5515e78aba814087e86c3687769fb2f` |
| `frames/**`（25 个文件，321508 B）| — | `d1718aa2c6a7196cd2425f9ebe488ba7f16e3749a276f77c38cbbe017bf0c901` |
| `states/**`（19 个文件，142697 B）| — | `1ff20021ec67f484bce38526bac9a79d6cd86b962809e015b63aa5f038c13ea8` |

## t139-scripted-w30 / lunarlander / scripted

* 目录：`runs/model-player/t139-scripted-w30/lunarlander/scripted`
* verdict：`PASS`（counts_as_pass=True，strict=PASS，baseline=PASS，game_side=PASS）
* 注入/接受后变化/rate：8 / 8 / 1.0
* 两窗对齐：3/8 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 2 frame(s))（matched 3/8，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game lunarlander --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9963 --window-frames 30 --out-prefix t139-jev-v3-w30`  <- t139_results_t139-jev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game lunarlander --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9964 --window-frames 90 --out-prefix t139-jev-v3-w90`  <- t139_results_t139-jev-v3-w90.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game lunarlander --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9961 --window-frames 30 --out-prefix t139-scripted-w30`  <- t139_results_t139-scripted-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game lunarlander --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9962 --window-frames 90 --out-prefix t139-scripted-w90`  <- t139_results_t139-scripted-w90.json (sweep driver)

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t139-scripted-w30/lunarlander/scripted/demo.png` | 107979 | `fe675c0ccd51f4a1a4a15dacdee5ed33787374bcb35921b22c507796c1046466` |
| `runs/model-player/t139-scripted-w30/lunarlander/scripted/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t139-scripted-w30/lunarlander/scripted/engine-game.stdout.txt` | 766 | `5f4336c2e86bcb76d6b2353940a29d5a1c3b6ca337a9a03bfa706f397511bde6` |
| `runs/model-player/t139-scripted-w30/lunarlander/scripted/filmstrip.png` | 74547 | `7e121b223ce72fb916f5091c356afbea366c6eea0c8f759119832428f5c4d443` |
| `runs/model-player/t139-scripted-w30/lunarlander/scripted/frames.json` | 455140 | `25532816a66601fea39b05e296a95dac80941f60d7b27bc192af51e3134e5034` |
| `runs/model-player/t139-scripted-w30/lunarlander/scripted/player.json` | 20165 | `2937aec82ae3f2fe4d9b99f720ecd89348f00c6443d8ea6896dd2140434c9d68` |
| `runs/model-player/t139-scripted-w30/lunarlander/scripted/session.json` | 11190 | `7cdb0dadf1879db676419cf82b250a7ff91838684ecb3d1c0139b64cb0ca2562` |
| `runs/model-player/t139-scripted-w30/lunarlander/scripted/steps.jsonl` | 96394 | `4dc3ff828f2d06ed211fbc5143039190d9a644087593f45b6b7c817846981f53` |
| `calls/**`（311 个文件，3191749 B）| — | `ce773cf1ee07df0ce80cde0546cf119876e399c71278b917bcf53cce8a6dc2e1` |
| `frames/**`（25 个文件，323393 B）| — | `0736b193dccdf7557ede229aaf0f7bf5ab5d6cadb371c09bce01915237cac011` |
| `states/**`（19 个文件，227314 B）| — | `04bae254fe80405c433d7a44e862368ca525f30fd45588bec2d9ef8fc2dad51e` |

## t139-scripted-w30 / match3 / scripted

* 目录：`runs/model-player/t139-scripted-w30/match3/scripted`
* verdict：`PASS`（counts_as_pass=True，strict=PASS，baseline=PASS，game_side=PASS）
* 注入/接受后变化/rate：12 / 8 / 1.0
* 两窗对齐：3/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 4 frame(s))（matched 3/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game match3 --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9963 --window-frames 30 --out-prefix t139-jev-v3-w30`  <- t139_results_t139-jev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game match3 --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9964 --window-frames 90 --out-prefix t139-jev-v3-w90`  <- t139_results_t139-jev-v3-w90.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game match3 --backend playjev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9965 --window-frames 30 --out-prefix t139-playjev-v3-w30`  <- t139_results_t139-playjev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game match3 --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9973 --window-frames 30 --out-prefix t139-scripted-w30`  <- t139_results_t139-scripted-w30-counterev.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game match3 --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9961 --window-frames 30 --out-prefix t139-scripted-w30`  <- t139_results_t139-scripted-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game match3 --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9962 --window-frames 90 --out-prefix t139-scripted-w90`  <- t139_results_t139-scripted-w90.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game match3 --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9969 --window-frames 30 --out-prefix t139-scripted-w30`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t139-scripted-w30/match3/scripted/demo.png` | 194195 | `318ac279eb46746d7107c1178ff9a85a203d43b5a654ecec8b6bcee8124a5333` |
| `runs/model-player/t139-scripted-w30/match3/scripted/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t139-scripted-w30/match3/scripted/engine-game.stdout.txt` | 769 | `fa194dd6d386e6add668da998f42c47f197cadc18429bb24fbfd24227ee6fa38` |
| `runs/model-player/t139-scripted-w30/match3/scripted/filmstrip.png` | 154043 | `38bdbcea42c10e16e0b234c96e405ce2a007215f051c5739c5be1e6ca1503b78` |
| `runs/model-player/t139-scripted-w30/match3/scripted/frames.json` | 611643 | `41789ecf6114da3901fe06dd64170842716a5a694e7cf1117910e68b3ba4419f` |
| `runs/model-player/t139-scripted-w30/match3/scripted/player.json` | 26578 | `8d0b635c60c66815d38b93a739b6b93821f32e27b4d7698c6442ed28a23c7d69` |
| `runs/model-player/t139-scripted-w30/match3/scripted/session.json` | 12973 | `2207a55ddb69a9ab7a89ba4d998e550680d5fbe2cb721cea7f2b174ed803e187` |
| `runs/model-player/t139-scripted-w30/match3/scripted/steps.jsonl` | 141510 | `bc93d0faf4af0bbdfb2395a6d4455ef7f610fa78d4c28d84ea842184106b85c7` |
| `calls/**`（514 个文件，5431697 B）| — | `134ba556a93923dd6cde2aa6479d9bb6bf75658a410ee60df2a49aeade64fc34` |
| `frames/**`（37 个文件，431921 B）| — | `2e16e26adc12d7396140a93f66a0bcbf1ac461f92ac42b4f7499eb0bb3e0a467` |
| `states/**`（27 个文件，330688 B）| — | `53b7074fb5e6b538143cb8e4f8b1550668fc36443f55482fa965a1da1e51757d` |

## t139-scripted-w30 / minesweeper / scripted

* 目录：`runs/model-player/t139-scripted-w30/minesweeper/scripted`
* verdict：`PASS`（counts_as_pass=True，strict=PASS，baseline=PASS，game_side=PASS）
* 注入/接受后变化/rate：12 / 7 / 1.0
* 两窗对齐：3/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 3 frame(s))（matched 3/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game minesweeper --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9963 --window-frames 30 --out-prefix t139-jev-v3-w30`  <- t139_results_t139-jev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game minesweeper --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9964 --window-frames 90 --out-prefix t139-jev-v3-w90`  <- t139_results_t139-jev-v3-w90.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game minesweeper --backend playjev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9965 --window-frames 30 --out-prefix t139-playjev-v3-w30`  <- t139_results_t139-playjev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game minesweeper --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9973 --window-frames 30 --out-prefix t139-scripted-w30`  <- t139_results_t139-scripted-w30-counterev.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game minesweeper --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9961 --window-frames 30 --out-prefix t139-scripted-w30`  <- t139_results_t139-scripted-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game minesweeper --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9962 --window-frames 90 --out-prefix t139-scripted-w90`  <- t139_results_t139-scripted-w90.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game minesweeper --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9969 --window-frames 30 --out-prefix t139-scripted-w30`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t139-scripted-w30/minesweeper/scripted/demo.png` | 186291 | `827275f29072d6cee0af785ad55fdb6212ce6781742933299dc06f5671d34c4a` |
| `runs/model-player/t139-scripted-w30/minesweeper/scripted/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t139-scripted-w30/minesweeper/scripted/engine-game.stdout.txt` | 745 | `f3f63cfb6a580a326c4cec01437ee5ddeb1cf4b2b9df953f7061448fe0ea1755` |
| `runs/model-player/t139-scripted-w30/minesweeper/scripted/filmstrip.png` | 182715 | `bb903653f3b27411a1d883980a94fcd0d53d7bb980bbac97557e61e6858d0426` |
| `runs/model-player/t139-scripted-w30/minesweeper/scripted/frames.json` | 810269 | `03cf928593606e7b9a10ac66bd7227bf367f651a6ebb257d70fdf0f9b03396d1` |
| `runs/model-player/t139-scripted-w30/minesweeper/scripted/player.json` | 27638 | `8eb3fe46165640e313a4b71cca39049f21d3afd3763f3719dd219aa604acf612` |
| `runs/model-player/t139-scripted-w30/minesweeper/scripted/session.json` | 13107 | `6c98a1c729c1e16144ce5f44732b2e83feb08badc354ffaa465fa552bb70f4db` |
| `runs/model-player/t139-scripted-w30/minesweeper/scripted/steps.jsonl` | 140744 | `d7ae38449eeaa25ed66e0ad9380d9a50ba20543fa6971a5e59aadb2ac6af6588` |
| `calls/**`（486 个文件，10020725 B）| — | `0be649587aef294b2a67db21335ff7e2c8b95cb2677c68c86432e1f156e00d28` |
| `frames/**`（37 个文件，580787 B）| — | `845539452efa9b58d0c1ab61e2626c9f2dcfda777bc9c30ae5d5a5f36b8101ba` |
| `states/**`（27 个文件，787282 B）| — | `6aa9bc362cbdbb89cb1da494547a7d4bf01fcca8ec1fc3775d7b6f98ade01aa7` |

## t139-scripted-w30 / missilecommand / scripted

* 目录：`runs/model-player/t139-scripted-w30/missilecommand/scripted`
* verdict：`PASS`（counts_as_pass=True，strict=PASS，baseline=PASS，game_side=PASS）
* 注入/接受后变化/rate：8 / 8 / 1.0
* 两窗对齐：1/8 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 4 frame(s))（matched 1/8，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game missilecommand --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9963 --window-frames 30 --out-prefix t139-jev-v3-w30`  <- t139_results_t139-jev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game missilecommand --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9964 --window-frames 90 --out-prefix t139-jev-v3-w90`  <- t139_results_t139-jev-v3-w90.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game missilecommand --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9961 --window-frames 30 --out-prefix t139-scripted-w30`  <- t139_results_t139-scripted-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game missilecommand --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9962 --window-frames 90 --out-prefix t139-scripted-w90`  <- t139_results_t139-scripted-w90.json (sweep driver)

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t139-scripted-w30/missilecommand/scripted/demo.png` | 108824 | `77337a51aa2d60b768712839dfc3de9b3f8102b9fec3809a0d13f54579e4e82e` |
| `runs/model-player/t139-scripted-w30/missilecommand/scripted/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t139-scripted-w30/missilecommand/scripted/engine-game.stdout.txt` | 742 | `e80b9885a4e22e55eee176bfa76d4383a4de5e4aec31ba09e66c7bde1c2b0cbc` |
| `runs/model-player/t139-scripted-w30/missilecommand/scripted/filmstrip.png` | 56306 | `5fff3de1a77b7398fc08197f66db8df38f0784c122767d5c12a0c051351e5332` |
| `runs/model-player/t139-scripted-w30/missilecommand/scripted/frames.json` | 497512 | `4071e846f8412c3753843b2278e4f1a30f7774e1221954153b737e82ae3e47f2` |
| `runs/model-player/t139-scripted-w30/missilecommand/scripted/player.json` | 20192 | `0758868158933b885a3739360d66f791311895544992873b881e8e8c01efcd8a` |
| `runs/model-player/t139-scripted-w30/missilecommand/scripted/session.json` | 11493 | `8c6f24843cd7435f78f386b421285d079ae00bf13b996dc7e1dc15cbc1fe1d4f` |
| `runs/model-player/t139-scripted-w30/missilecommand/scripted/steps.jsonl` | 98014 | `d4e91a5e9fa6978dce31458aab9ef63a5a8b35c33521dc4e2d9dce38b58eff52` |
| `calls/**`（288 个文件，4823482 B）| — | `4ffd2209874e7d010f26dc3c67f0a2ecf57e2ea2767f8eafbf6b60c3e251d6b8` |
| `frames/**`（25 个文件，354928 B）| — | `b47d027734ea9144b58fdf83327e722530a59b6681aba60981a3a8b3417cf7d9` |
| `states/**`（19 个文件，441910 B）| — | `38b75e91ed96baebbb6f48b8f6f8f0813d23bae7bd617e947ad3db0ebc399493` |

## t139-scripted-w30 / pacman / scripted

* 目录：`runs/model-player/t139-scripted-w30/pacman/scripted`
* verdict：`PASS`（counts_as_pass=True，strict=PASS，baseline=PASS，game_side=PASS）
* 注入/接受后变化/rate：12 / 7 / 1.0
* 两窗对齐：3/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 4 frame(s))（matched 3/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game pacman --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9963 --window-frames 30 --out-prefix t139-jev-v3-w30`  <- t139_results_t139-jev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game pacman --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9964 --window-frames 90 --out-prefix t139-jev-v3-w90`  <- t139_results_t139-jev-v3-w90.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game pacman --backend playjev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9965 --window-frames 30 --out-prefix t139-playjev-v3-w30`  <- t139_results_t139-playjev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game pacman --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9973 --window-frames 30 --out-prefix t139-scripted-w30`  <- t139_results_t139-scripted-w30-counterev.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game pacman --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9961 --window-frames 30 --out-prefix t139-scripted-w30`  <- t139_results_t139-scripted-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game pacman --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9962 --window-frames 90 --out-prefix t139-scripted-w90`  <- t139_results_t139-scripted-w90.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game pacman --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9969 --window-frames 30 --out-prefix t139-scripted-w30`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t139-scripted-w30/pacman/scripted/demo.png` | 146478 | `b2ac36203d74153f2e14cfa946cbeb6e9f4a63bd0761e54e53fcb22702c19a8d` |
| `runs/model-player/t139-scripted-w30/pacman/scripted/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t139-scripted-w30/pacman/scripted/engine-game.stdout.txt` | 733 | `7e700d9d30d52fe18b62bb89f6f3c64a85cf2a2d4d85bbf3cdca632d649968c5` |
| `runs/model-player/t139-scripted-w30/pacman/scripted/filmstrip.png` | 146874 | `889c8b55347b4e8ebb9a5c7d98015b64eac09b169105d5192898e49cda287669` |
| `runs/model-player/t139-scripted-w30/pacman/scripted/frames.json` | 583824 | `06729094ef4ca7da3fbef254a3b36d95513cdab35b4037c8925fe6a9dc644b05` |
| `runs/model-player/t139-scripted-w30/pacman/scripted/player.json` | 26952 | `3e8d31b86e1d9df2ad9afa78938ca1fc84a04826ce8a7e16c007cb15ff2f4cce` |
| `runs/model-player/t139-scripted-w30/pacman/scripted/session.json` | 12538 | `7dcb6f24c6e3959eddab1f8b9673c7a488f38fcf2930f8c73071b6f4ef91983e` |
| `runs/model-player/t139-scripted-w30/pacman/scripted/steps.jsonl` | 143409 | `769e88b08b442c91e09f414158725716f8a9030cb3b20552507c43dac43ff002` |
| `calls/**`（480 个文件，12280904 B）| — | `e9029f7f9d2a4d930cc5d54026e8d654f8e5475837fbc5d2a6a5ff0403e6973e` |
| `frames/**`（37 个文件，411185 B）| — | `463854bf0919d677440265795871e6f990a266ad8130746de430a319c2923e0c` |
| `states/**`（27 个文件，1153928 B）| — | `8050c12f9d71893202cedc3ad0bda0d3da1974ed8739b6318ab2864a496dbb53` |

## t139-scripted-w30 / platformer / scripted

* 目录：`runs/model-player/t139-scripted-w30/platformer/scripted`
* verdict：`PASS`（counts_as_pass=True，strict=PASS，baseline=PASS，game_side=PASS）
* 注入/接受后变化/rate：8 / 8 / 1.0
* 两窗对齐：1/8 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 5 frame(s))（matched 1/8，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game platformer --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9963 --window-frames 30 --out-prefix t139-jev-v3-w30`  <- t139_results_t139-jev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game platformer --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9964 --window-frames 90 --out-prefix t139-jev-v3-w90`  <- t139_results_t139-jev-v3-w90.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game platformer --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9961 --window-frames 30 --out-prefix t139-scripted-w30`  <- t139_results_t139-scripted-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game platformer --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9962 --window-frames 90 --out-prefix t139-scripted-w90`  <- t139_results_t139-scripted-w90.json (sweep driver)

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t139-scripted-w30/platformer/scripted/demo.png` | 107570 | `48541cfe636e0e7d74cda66d492881b789ab83533294cd69dc70de0df86ef251` |
| `runs/model-player/t139-scripted-w30/platformer/scripted/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t139-scripted-w30/platformer/scripted/engine-game.stdout.txt` | 796 | `1c896bb22ee4d78793954132d69e810ddf2f6ab60a18109087989ce5ce3694a3` |
| `runs/model-player/t139-scripted-w30/platformer/scripted/filmstrip.png` | 69073 | `fea0888b8fcf1622fd3cbfd35398eb9cdac919e41b288a3ded329cdd795110c4` |
| `runs/model-player/t139-scripted-w30/platformer/scripted/frames.json` | 388236 | `34ef835dd8f2bfc70a365bb0f8720c100bacfdab4936b7946f84b19a9470bcbd` |
| `runs/model-player/t139-scripted-w30/platformer/scripted/player.json` | 20146 | `ae947b5b6bbf837d28517128dc57907f7da25ecd1110b8e94db79bc98d3c879e` |
| `runs/model-player/t139-scripted-w30/platformer/scripted/session.json` | 11229 | `f981e1ff19384969dc1fd96c7c344e227ff70279bdf2d944dd80eacc04301025` |
| `runs/model-player/t139-scripted-w30/platformer/scripted/steps.jsonl` | 103350 | `0d123cb076107f1fc249644a9d4fbe1b7040ac7876e000461418ad3a548e6f65` |
| `calls/**`（283 个文件，4357035 B）| — | `e582334c1c0d5ea15dbd2394909ca544fb39b8ef8fda042ed413acc559048bc0` |
| `frames/**`（25 个文件，273094 B）| — | `cd1ea931dcd95b3ea3e45deed08143d7ba010eadb77099c2ec0e9b615fa1283b` |
| `states/**`（19 个文件，408545 B）| — | `29a28848318235193e2710b4628e30095c8aebd5c99973bbeb5e0125d9e768f5` |

## t139-scripted-w30 / pong / scripted

* 目录：`runs/model-player/t139-scripted-w30/pong/scripted`
* verdict：`PASS(baseline only)`（counts_as_pass=False，strict=FAIL，baseline=PASS，game_side=FAIL）
* 注入/接受后变化/rate：11 / 10 / 0.9091
* 两窗对齐：2/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 6 frame(s))（matched 2/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game pong --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9963 --window-frames 30 --out-prefix t139-jev-v3-w30`  <- t139_results_t139-jev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game pong --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9964 --window-frames 90 --out-prefix t139-jev-v3-w90`  <- t139_results_t139-jev-v3-w90.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game pong --backend playjev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9965 --window-frames 30 --out-prefix t139-playjev-v3-w30`  <- t139_results_t139-playjev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game pong --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9961 --window-frames 30 --out-prefix t139-scripted-w30`  <- t139_results_t139-scripted-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game pong --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9962 --window-frames 90 --out-prefix t139-scripted-w90`  <- t139_results_t139-scripted-w90.json (sweep driver)

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t139-scripted-w30/pong/scripted/demo.png` | 63700 | `d5f687ad0daff4ceb11b15916e545b3c0b1e27c3de1e58097fe2e0be06691a5c` |
| `runs/model-player/t139-scripted-w30/pong/scripted/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t139-scripted-w30/pong/scripted/engine-game.stdout.txt` | 4628 | `500054a6e4b5a406fd8e494272bb9fbeb73c0036e124c097734ed394496741c0` |
| `runs/model-player/t139-scripted-w30/pong/scripted/filmstrip.png` | 52970 | `c3deedfd9c0d6b834f98a7773ca017e53102b4933f051de0b1a261eb42e66df2` |
| `runs/model-player/t139-scripted-w30/pong/scripted/frames.json` | 265673 | `33397287a977ae508d15cefcc3337735c358445b845b1fbd225c321f5766788d` |
| `runs/model-player/t139-scripted-w30/pong/scripted/player.json` | 23501 | `9f5e3102130e6058e4ead0caa3c7b981726bfa35dea5c3e561821f843c72b0ff` |
| `runs/model-player/t139-scripted-w30/pong/scripted/session.json` | 11392 | `fc76d64273b65fb86cdd040d05a1c8329e8495897fd57bfc64447e5e587c5268` |
| `runs/model-player/t139-scripted-w30/pong/scripted/steps.jsonl` | 146551 | `3f5c1c92683f584435d629a5ddd2cc98f86d648ea498cbeb33cc903391bd7688` |
| `calls/**`（417 个文件，1174463 B）| — | `994ec0438cf368158ffc63aa2ced59a48bb9eaab02080a18af029e820baf85f1` |
| `frames/**`（37 个文件，172744 B）| — | `7760f279ca17ddb6783c62a3b64537ede113d5c1f5be3ff21c3e78a24910c69b` |
| `states/**`（27 个文件，66511 B）| — | `e4e01e8f457e99b7cce025cb260d38ec93cd977c474aeed7650f2d2f1f8d901e` |

## t139-scripted-w30 / puzzlebobble / scripted

* 目录：`runs/model-player/t139-scripted-w30/puzzlebobble/scripted`
* verdict：`PASS`（counts_as_pass=True，strict=PASS，baseline=PASS，game_side=PASS）
* 注入/接受后变化/rate：8 / 8 / 1.0
* 两窗对齐：3/8 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 3 frame(s))（matched 3/8，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game puzzlebobble --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9963 --window-frames 30 --out-prefix t139-jev-v3-w30`  <- t139_results_t139-jev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game puzzlebobble --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9964 --window-frames 90 --out-prefix t139-jev-v3-w90`  <- t139_results_t139-jev-v3-w90.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game puzzlebobble --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9961 --window-frames 30 --out-prefix t139-scripted-w30`  <- t139_results_t139-scripted-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game puzzlebobble --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9962 --window-frames 90 --out-prefix t139-scripted-w90`  <- t139_results_t139-scripted-w90.json (sweep driver)

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t139-scripted-w30/puzzlebobble/scripted/demo.png` | 138756 | `2b46e1d279c7c33b6518fc23d4a65eb9f24444694314ec4f292ca2cd31383f3e` |
| `runs/model-player/t139-scripted-w30/puzzlebobble/scripted/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t139-scripted-w30/puzzlebobble/scripted/engine-game.stdout.txt` | 739 | `ab4441b6545c79782938f5395ecab4bda3a4da62bad24c84c99b5c2619b37ae0` |
| `runs/model-player/t139-scripted-w30/puzzlebobble/scripted/filmstrip.png` | 83632 | `87d297d66adb426d0bc397b4e07c73ddaf11f871f4d185be485901f7ea1b4266` |
| `runs/model-player/t139-scripted-w30/puzzlebobble/scripted/frames.json` | 481952 | `1c73d91f4615f923037ea546d1d880de0ab52a456a924b4b76bdf82417bbba1c` |
| `runs/model-player/t139-scripted-w30/puzzlebobble/scripted/player.json` | 20155 | `c0726f375630eddd5f79750cf1c5b5af62fe9d98f595281a8a3a9b065967e68a` |
| `runs/model-player/t139-scripted-w30/puzzlebobble/scripted/session.json` | 11377 | `43f99246fc8b25e73f0ee9d8a9508fb5e3d4e4cfa8ee5e2a6a165950cc7af8b1` |
| `runs/model-player/t139-scripted-w30/puzzlebobble/scripted/steps.jsonl` | 98047 | `52386e78759d1735dcf2aba9dc785676f13238a84327db8f7b69fe4cf6bfb38d` |
| `calls/**`（298 个文件，4537843 B）| — | `d908cab605374fcba70ebbf5cd34bf31a64b792ca059821cb90a9078f7759629` |
| `frames/**`（25 个文件，343266 B）| — | `0b0c70edf7af9d694a650fabf8ef2b6c2413f09af2dfdd5df3581548387843ce` |
| `states/**`（19 个文件，379477 B）| — | `dcde844b045b36f9d9c4f6467d53bbc80a3c1ce254d10ddddf422e9cba594170` |

## t139-scripted-w30 / rtype / scripted

* 目录：`runs/model-player/t139-scripted-w30/rtype/scripted`
* verdict：`PASS`（counts_as_pass=True，strict=PASS，baseline=PASS，game_side=PASS）
* 注入/接受后变化/rate：8 / 8 / 1.0
* 两窗对齐：1/8 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 2 frame(s))（matched 1/8，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game rtype --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9963 --window-frames 30 --out-prefix t139-jev-v3-w30`  <- t139_results_t139-jev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game rtype --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9964 --window-frames 90 --out-prefix t139-jev-v3-w90`  <- t139_results_t139-jev-v3-w90.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game rtype --backend playjev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9965 --window-frames 30 --out-prefix t139-playjev-v3-w30`  <- t139_results_t139-playjev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game rtype --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9961 --window-frames 30 --out-prefix t139-scripted-w30`  <- t139_results_t139-scripted-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game rtype --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9962 --window-frames 90 --out-prefix t139-scripted-w90`  <- t139_results_t139-scripted-w90.json (sweep driver)

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t139-scripted-w30/rtype/scripted/demo.png` | 121037 | `f7dc99977850e1cac96231528501e93077f122c85f20c3a8dc6467c4c694913f` |
| `runs/model-player/t139-scripted-w30/rtype/scripted/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t139-scripted-w30/rtype/scripted/engine-game.stdout.txt` | 743 | `2c704bc68a7f552b658070e10adc6a3eeefd779f3e98ee155937de3c53a7d8c3` |
| `runs/model-player/t139-scripted-w30/rtype/scripted/filmstrip.png` | 69895 | `dbc5b9c1a6177db97e1014a0f4c1c0b9235e8c768fc894b64389e98f9cdc15bf` |
| `runs/model-player/t139-scripted-w30/rtype/scripted/frames.json` | 430155 | `af52cdd09b7b0c0f59ece9675406d752733a84c970cc52db13fcf65d41c0ff30` |
| `runs/model-player/t139-scripted-w30/rtype/scripted/player.json` | 20150 | `f58fbf8cd254cdaa5bd437da78addc3ff0f91b8df717e434591b66d035a97884` |
| `runs/model-player/t139-scripted-w30/rtype/scripted/session.json` | 11320 | `e3d2fd68e27852b37ceb78121e78b37de17e1badb8dc9ae76346cc612e709e8f` |
| `runs/model-player/t139-scripted-w30/rtype/scripted/steps.jsonl` | 97440 | `24c48d6e7b15bba92e3cc4c18a135cf9e2426de30db4f11bc083e102ef1aa996` |
| `calls/**`（283 个文件，3827828 B）| — | `73620079140c11606b776847876f2b45e597d2efda5b64d92c3c041a5aaff784` |
| `frames/**`（25 个文件，304680 B）| — | `edc8d0ffea326b606dca3e7555186346c0eb2aa126e4f68b6ac5a6414f62d65f` |
| `states/**`（19 个文件，351802 B）| — | `b692dc8dbe39ff4958de780d85c4bd5212a725cdba447719220a448b4edee3b6` |

## t139-scripted-w30 / snake / scripted

* 目录：`runs/model-player/t139-scripted-w30/snake/scripted`
* verdict：`PASS`（counts_as_pass=True，strict=PASS，baseline=PASS，game_side=PASS）
* 注入/接受后变化/rate：8 / 8 / 1.0
* 两窗对齐：1/8 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 6 frame(s))（matched 1/8，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game snake --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9963 --window-frames 30 --out-prefix t139-jev-v3-w30`  <- t139_results_t139-jev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game snake --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9964 --window-frames 90 --out-prefix t139-jev-v3-w90`  <- t139_results_t139-jev-v3-w90.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game snake --backend playjev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9965 --window-frames 30 --out-prefix t139-playjev-v3-w30`  <- t139_results_t139-playjev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game snake --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9961 --window-frames 30 --out-prefix t139-scripted-w30`  <- t139_results_t139-scripted-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game snake --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9962 --window-frames 90 --out-prefix t139-scripted-w90`  <- t139_results_t139-scripted-w90.json (sweep driver)

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t139-scripted-w30/snake/scripted/demo.png` | 44716 | `a15e6a91b4df883c9e668af539ce764722351657abf554b26fe399925af3b4ee` |
| `runs/model-player/t139-scripted-w30/snake/scripted/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t139-scripted-w30/snake/scripted/engine-game.stdout.txt` | 6323 | `21a54d22924bc0f9e3e38b69e89deff8bab8d42e15d78ce335d84bffb00134ee` |
| `runs/model-player/t139-scripted-w30/snake/scripted/filmstrip.png` | 30716 | `10624087db10231db98f7a488d60c4a9d94932b051c83e813c01725bb2395993` |
| `runs/model-player/t139-scripted-w30/snake/scripted/frames.json` | 126931 | `e161ad6afaf232a6fc186da6f1ef638cd29bc4b215bbb35e73c8521ae5c07710` |
| `runs/model-player/t139-scripted-w30/snake/scripted/player.json` | 20155 | `6aab0be7bb712403d21bafb76e2b950b46a0b1f6b65bd0bb602d60d5febd7ce2` |
| `runs/model-player/t139-scripted-w30/snake/scripted/session.json` | 11952 | `e2350e1b34d185b7feb2b56e74dc151310c895f9252be1eb6612ab578fd5c76e` |
| `runs/model-player/t139-scripted-w30/snake/scripted/steps.jsonl` | 102962 | `29031a155f7f2aba7a4b2095b99fa77e203eea1d9f2437f632f3f64a086b20c8` |
| `calls/**`（269 个文件，1606902 B）| — | `d588a5e9d92e7ee8881b3466cba699b69d1ee364706881927c1ddd8447c43b1f` |
| `frames/**`（25 个文件，77380 B）| — | `88485ee7f22a1884aee33591c2aeca13a06e878db658eb4632e5756d90af0467` |
| `states/**`（19 个文件，166645 B）| — | `5fe58104673f781c5908ec3f44381efcc7f09c5ad2b386a239d00d2e95fe83b4` |

## t139-scripted-w30 / sokoban / scripted

* 目录：`runs/model-player/t139-scripted-w30/sokoban/scripted`
* verdict：`PASS`（counts_as_pass=True，strict=PASS，baseline=PASS，game_side=PASS）
* 注入/接受后变化/rate：12 / 9 / 1.0
* 两窗对齐：3/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 3 frame(s))（matched 3/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game sokoban --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9963 --window-frames 30 --out-prefix t139-jev-v3-w30`  <- t139_results_t139-jev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game sokoban --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9964 --window-frames 90 --out-prefix t139-jev-v3-w90`  <- t139_results_t139-jev-v3-w90.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game sokoban --backend playjev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9965 --window-frames 30 --out-prefix t139-playjev-v3-w30`  <- t139_results_t139-playjev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game sokoban --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9973 --window-frames 30 --out-prefix t139-scripted-w30`  <- t139_results_t139-scripted-w30-counterev.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game sokoban --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9961 --window-frames 30 --out-prefix t139-scripted-w30`  <- t139_results_t139-scripted-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game sokoban --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9962 --window-frames 90 --out-prefix t139-scripted-w90`  <- t139_results_t139-scripted-w90.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game sokoban --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9969 --window-frames 30 --out-prefix t139-scripted-w30`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t139-scripted-w30/sokoban/scripted/demo.png` | 139576 | `8d59192b1c13f355664beec196550cdff3fa531986c1e8ad5af3be4e764560b1` |
| `runs/model-player/t139-scripted-w30/sokoban/scripted/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t139-scripted-w30/sokoban/scripted/engine-game.stdout.txt` | 745 | `0d3deebe53ba998ad69d5df94527b64e5d945d59c294d65545ecb17aa65af05d` |
| `runs/model-player/t139-scripted-w30/sokoban/scripted/filmstrip.png` | 107313 | `22f71c379de06c60d2abaefe078356f5413c6b07608869326e69fd633b7ae453` |
| `runs/model-player/t139-scripted-w30/sokoban/scripted/frames.json` | 646915 | `8b8f4ba1fb67765c42b36c336c22f61edacec4a39de934331c908587da22d38c` |
| `runs/model-player/t139-scripted-w30/sokoban/scripted/player.json` | 25486 | `45c6257d58408d10cdfc2d7daaac6014edbdcba7517fbc492d879e20772b75e3` |
| `runs/model-player/t139-scripted-w30/sokoban/scripted/session.json` | 12684 | `3e0115f6738c49132911e7d66e13f274bd56bcb8a4c535e30215c3b05dc35419` |
| `runs/model-player/t139-scripted-w30/sokoban/scripted/steps.jsonl` | 147767 | `b76b403065245b5084e7548010fe84ecc855f62a7abe905d232ce8d802ad75ca` |
| `calls/**`（517 个文件，6097793 B）| — | `56fab73aee16ca6696729109c0bbb18ce2dd82dd0b801bdb969136b162a36e49` |
| `frames/**`（37 个文件，458340 B）| — | `45546e649c50bd312d0a286e26ed3748801eef0362a13c896a7d995ad3dfa23b` |
| `states/**`（27 个文件，374449 B）| — | `63d9e3a41acf8aaca2f9a4a41d92c6af4f489613b0b5fd9a7b8f6555b54111dd` |

## t139-scripted-w30 / spaceinvaders / scripted

* 目录：`runs/model-player/t139-scripted-w30/spaceinvaders/scripted`
* verdict：`PASS`（counts_as_pass=True，strict=PASS，baseline=PASS，game_side=PASS）
* 注入/接受后变化/rate：8 / 8 / 1.0
* 两窗对齐：3/8 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 3 frame(s))（matched 3/8，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game spaceinvaders --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9963 --window-frames 30 --out-prefix t139-jev-v3-w30`  <- t139_results_t139-jev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game spaceinvaders --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9964 --window-frames 90 --out-prefix t139-jev-v3-w90`  <- t139_results_t139-jev-v3-w90.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game spaceinvaders --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9961 --window-frames 30 --out-prefix t139-scripted-w30`  <- t139_results_t139-scripted-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game spaceinvaders --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9962 --window-frames 90 --out-prefix t139-scripted-w90`  <- t139_results_t139-scripted-w90.json (sweep driver)

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t139-scripted-w30/spaceinvaders/scripted/demo.png` | 86174 | `56f238c2c09bb1292d5c4160d4c328182cc5ac00129026abcb39ecda3e22d753` |
| `runs/model-player/t139-scripted-w30/spaceinvaders/scripted/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t139-scripted-w30/spaceinvaders/scripted/engine-game.stdout.txt` | 754 | `0f0aa66fdf540b830ddcc1f4a310d0cc6938bfd7dd1f857d1eea7db0fa40dd28` |
| `runs/model-player/t139-scripted-w30/spaceinvaders/scripted/filmstrip.png` | 61307 | `b4a161ebea9a16654694826334781700f667b0d1e350db04bf9eebcb8d8550ef` |
| `runs/model-player/t139-scripted-w30/spaceinvaders/scripted/frames.json` | 348418 | `97baa699a5604d412437405f9930d8e03a88ea231809b105fd58e6506aa64d26` |
| `runs/model-player/t139-scripted-w30/spaceinvaders/scripted/player.json` | 20169 | `d94123307c4b5bd9704735744ef444dc050c17a8162f93f14a05353572d29584` |
| `runs/model-player/t139-scripted-w30/spaceinvaders/scripted/session.json` | 11291 | `6be878731f32252b980d647bdcf79601e805a249b0ec6c9fbfd1197d8ae79a75` |
| `runs/model-player/t139-scripted-w30/spaceinvaders/scripted/steps.jsonl` | 100564 | `a472a4b6b429cfdc44cf7a5dd58c51d2a3a116751effa38be0cffd0fd3d43502` |
| `calls/**`（312 个文件，2376403 B）| — | `f2c49c09e08b5063ab1db37f3909236a5a4b7ec2823281ac32ae48266c33605c` |
| `frames/**`（25 个文件，243090 B）| — | `dbf728ef8341e588493d872c630b3c7cd681e2726fbc5ce018602093e9045b68` |
| `states/**`（19 个文件，169498 B）| — | `e451a041d2b56b79b732259d6a0c5739fd0ba8dda5ff4ae8cdcc8c8528573425` |

## t139-scripted-w30 / tetris / scripted

* 目录：`runs/model-player/t139-scripted-w30/tetris/scripted`
* verdict：`PASS`（counts_as_pass=True，strict=PASS，baseline=PASS，game_side=PASS）
* 注入/接受后变化/rate：8 / 8 / 1.0
* 两窗对齐：2/8 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 2 frame(s))（matched 2/8，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game tetris --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9963 --window-frames 30 --out-prefix t139-jev-v3-w30`  <- t139_results_t139-jev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game tetris --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9964 --window-frames 90 --out-prefix t139-jev-v3-w90`  <- t139_results_t139-jev-v3-w90.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game tetris --backend playjev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9965 --window-frames 30 --out-prefix t139-playjev-v3-w30`  <- t139_results_t139-playjev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game tetris --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9961 --window-frames 30 --out-prefix t139-scripted-w30`  <- t139_results_t139-scripted-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game tetris --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9962 --window-frames 90 --out-prefix t139-scripted-w90`  <- t139_results_t139-scripted-w90.json (sweep driver)

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t139-scripted-w30/tetris/scripted/demo.png` | 51366 | `d63646b22803d99e27d3e4c201ef7e0ecec39c44656e64e3afeeb73f502c79f5` |
| `runs/model-player/t139-scripted-w30/tetris/scripted/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t139-scripted-w30/tetris/scripted/engine-game.stdout.txt` | 5842 | `1e2f0caf8e2d623e2e859b15cc672b36c036453f616072f7645d20b8a5ad579c` |
| `runs/model-player/t139-scripted-w30/tetris/scripted/filmstrip.png` | 34096 | `cd85452d53a798b699c464c46417fdb682402fee602c4cac11ccb69e3654cb38` |
| `runs/model-player/t139-scripted-w30/tetris/scripted/frames.json` | 196015 | `87fe7426d31108397541e5e3d4cad3c51382dbc5bbd547c2c3e918efa69feb5b` |
| `runs/model-player/t139-scripted-w30/tetris/scripted/player.json` | 20241 | `2ec0385ec2b4fbb6a99e3cded9acc295e841d2e67e1b6172867d4a85854310fe` |
| `runs/model-player/t139-scripted-w30/tetris/scripted/session.json` | 11177 | `329c6ff2867a4efc06bffa7ed2156a403e3893917e5c3247bc45a84c9ba57dab` |
| `runs/model-player/t139-scripted-w30/tetris/scripted/steps.jsonl` | 86859 | `b0d71ca40feb7e0f22eb0392c150e481867a2fd9f49c542a7578dabeb53cd143` |
| `calls/**`（298 个文件，692820 B）| — | `aa70d37da2f140c708bfc37edac4ded355a12d1a317c97cc9562c37f0105ec2d` |
| `frames/**`（25 个文件，128882 B）| — | `0dea8efcfa839d627cd7477206d15531aa3f1b74c390a1f5fb41860ccb3d9af2` |
| `states/**`（19 个文件，29822 B）| — | `d5e53218e2ec93443402f806da3adcaf487c62041e7bd1fede03cf28da3c6255` |

## t139-scripted-w30 / towerdefense / scripted

* 目录：`runs/model-player/t139-scripted-w30/towerdefense/scripted`
* verdict：`PASS`（counts_as_pass=True，strict=PASS，baseline=PASS，game_side=PASS）
* 注入/接受后变化/rate：12 / 9 / 1.0
* 两窗对齐：0/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 4 frame(s))（matched 0/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game towerdefense --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9963 --window-frames 30 --out-prefix t139-jev-v3-w30`  <- t139_results_t139-jev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game towerdefense --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9964 --window-frames 90 --out-prefix t139-jev-v3-w90`  <- t139_results_t139-jev-v3-w90.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game towerdefense --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9973 --window-frames 30 --out-prefix t139-scripted-w30`  <- t139_results_t139-scripted-w30-counterev.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game towerdefense --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9961 --window-frames 30 --out-prefix t139-scripted-w30`  <- t139_results_t139-scripted-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game towerdefense --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9962 --window-frames 90 --out-prefix t139-scripted-w90`  <- t139_results_t139-scripted-w90.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game towerdefense --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9969 --window-frames 30 --out-prefix t139-scripted-w30`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t139-scripted-w30/towerdefense/scripted/demo.png` | 163764 | `94d0b6b64960faf6c9336da8ae6d2c271c123a94fc21c6ce9f1f69c6b563a3af` |
| `runs/model-player/t139-scripted-w30/towerdefense/scripted/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t139-scripted-w30/towerdefense/scripted/engine-game.stdout.txt` | 753 | `88448dd60926ff4b0e3b332421701c0dabb10a58dd90f6d7357f63200049c7af` |
| `runs/model-player/t139-scripted-w30/towerdefense/scripted/filmstrip.png` | 131272 | `a99807424101d51b52c9b7906e2bf78e57d52e95b8b0cc6de12da8a3c2f9e22b` |
| `runs/model-player/t139-scripted-w30/towerdefense/scripted/frames.json` | 637972 | `a39f227135c0f870b6f1e3aa37413ff1c6b39fa88a235b2a689e990c3ad40e1d` |
| `runs/model-player/t139-scripted-w30/towerdefense/scripted/player.json` | 25667 | `65f0001288e92d8c29e211370095d6c94a03e2b9b19c61ad78fcd8d0bb7a5fff` |
| `runs/model-player/t139-scripted-w30/towerdefense/scripted/session.json` | 12932 | `a3db2644f01f74f60f6152e2eabd0d2e69f44e54b43dcb66708f5076bb98dd93` |
| `runs/model-player/t139-scripted-w30/towerdefense/scripted/steps.jsonl` | 138411 | `356a972e7a7cc05fabf2a6378501939179a42dd0424370a5bf833321448686d1` |
| `calls/**`（514 个文件，8672668 B）| — | `30a3e02ca6b4d79942377ebe85107426cab163bc115d0633c0f26a37b65f2675` |
| `frames/**`（37 个文件，451587 B）| — | `b58cb517c354198bdac99867e80f03ed856c21c74e3513846e8cab8294ffcd25` |
| `states/**`（27 个文件，648198 B）| — | `35e07d53c0ba8db8da9a05e9f26a4ae4d7279e6de1cad99eebe17538c1894b42` |

## t139-scripted-w90 / asteroids / scripted

* 目录：`runs/model-player/t139-scripted-w90/asteroids/scripted`
* verdict：`PASS`（counts_as_pass=True，strict=PASS，baseline=PASS，game_side=PASS）
* 注入/接受后变化/rate：8 / 8 / 1.0
* 两窗对齐：0/8 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 3 frame(s))（matched 0/8，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game asteroids --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9963 --window-frames 30 --out-prefix t139-jev-v3-w30`  <- t139_results_t139-jev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game asteroids --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9964 --window-frames 90 --out-prefix t139-jev-v3-w90`  <- t139_results_t139-jev-v3-w90.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game asteroids --backend playjev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9965 --window-frames 30 --out-prefix t139-playjev-v3-w30`  <- t139_results_t139-playjev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game asteroids --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9961 --window-frames 30 --out-prefix t139-scripted-w30`  <- t139_results_t139-scripted-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game asteroids --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9962 --window-frames 90 --out-prefix t139-scripted-w90`  <- t139_results_t139-scripted-w90.json (sweep driver)

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t139-scripted-w90/asteroids/scripted/demo.png` | 88161 | `13fca8c99f2160025bb2cc2bb8e2edf67c84d63db6a3fc2cd1ae58b5ef775e95` |
| `runs/model-player/t139-scripted-w90/asteroids/scripted/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t139-scripted-w90/asteroids/scripted/engine-game.stdout.txt` | 741 | `f773b23ceed749d22f596fc29bf3d7cb2ef7264e7f1d2f20fdf290401f55add6` |
| `runs/model-player/t139-scripted-w90/asteroids/scripted/filmstrip.png` | 49459 | `7d7c51902ce90148acb4067e0e68e243fabe80e79c19e1db02883dc9e4f3dfc0` |
| `runs/model-player/t139-scripted-w90/asteroids/scripted/frames.json` | 371137 | `a89024064b13d2f0734d9b0072e0f887910d4c67aa5c621daa56cd6cb6e48a0c` |
| `runs/model-player/t139-scripted-w90/asteroids/scripted/player.json` | 20183 | `03ecf68423042d82b52aa9f2e441dd293dbda7ac69f88daea164038e71612600` |
| `runs/model-player/t139-scripted-w90/asteroids/scripted/session.json` | 11259 | `d193ae3a48ad9e48124f756b1dfbcf2904d91fb55de6b641837f3b2f88f7c1b4` |
| `runs/model-player/t139-scripted-w90/asteroids/scripted/steps.jsonl` | 100895 | `7ba43e54dad004eb1596b72608a12c087cceeb24d40f064e0a0279b98236374b` |
| `calls/**`（677 个文件，2895876 B）| — | `10f519b18049f68b2334f2b9bf931ab40db2c98d8167ac7f83de6584eda96318` |
| `frames/**`（25 个文件，260239 B）| — | `930a38ef6c50eacdae451e08aee8c8dea23b6ced614db6c5d243bd913d2961d5` |
| `states/**`（19 个文件，55593 B）| — | `7357b561e3f2b9d2213483ac25626bd414427cac32d454bc1b8e4fdff5d1c9a0` |

## t139-scripted-w90 / bomberman / scripted

* 目录：`runs/model-player/t139-scripted-w90/bomberman/scripted`
* verdict：`INCONCLUSIVE`（counts_as_pass=False，strict=INCONCLUSIVE，baseline=INCONCLUSIVE，game_side=FAIL）
* 注入/接受后变化/rate：12 / 6 / 0.6667
* 两窗对齐：2/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 4 frame(s))（matched 2/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game bomberman --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9963 --window-frames 30 --out-prefix t139-jev-v3-w30`  <- t139_results_t139-jev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game bomberman --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9964 --window-frames 90 --out-prefix t139-jev-v3-w90`  <- t139_results_t139-jev-v3-w90.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game bomberman --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9961 --window-frames 30 --out-prefix t139-scripted-w30`  <- t139_results_t139-scripted-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game bomberman --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9962 --window-frames 90 --out-prefix t139-scripted-w90`  <- t139_results_t139-scripted-w90.json (sweep driver)

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t139-scripted-w90/bomberman/scripted/demo.png` | 154435 | `d4db95906fc39923d9cf85540d7e08b7969b2b0f75e597a919249039c0418dd5` |
| `runs/model-player/t139-scripted-w90/bomberman/scripted/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t139-scripted-w90/bomberman/scripted/engine-game.stdout.txt` | 775 | `215d776cec784b58aff5390fe10091ca1cda30709cb0e6b7d48ed5bdd30b5b56` |
| `runs/model-player/t139-scripted-w90/bomberman/scripted/filmstrip.png` | 143686 | `c1cd831d3cc1505bb40238b3ba49f6c44ebe377dc5d20724aea25859247050c6` |
| `runs/model-player/t139-scripted-w90/bomberman/scripted/frames.json` | 511998 | `93d07108459db2fc1b168a1162edb8d6b0a2e1a4b00270b72518ca30f07256fb` |
| `runs/model-player/t139-scripted-w90/bomberman/scripted/player.json` | 26177 | `3fbad2e362e019cf4e276daacb1477abfe27547ef545fde6665823adcfde95b6` |
| `runs/model-player/t139-scripted-w90/bomberman/scripted/session.json` | 11373 | `6246eba1f3a6bb4ff5142e2ae9c5e8a7754b69b23ad524476cceb076be21a311` |
| `runs/model-player/t139-scripted-w90/bomberman/scripted/steps.jsonl` | 142895 | `fc4ed4fa3c7d5e0f096bf06e7ff777b677033ce3234df5c62c19d222f485cc06` |
| `calls/**`（891 个文件，15628612 B）| — | `72d6bdb7420c86701561dcfa7ff283f0159fe7aba54d5b4a54c4b244992a45e6` |
| `frames/**`（37 个文件，357119 B）| — | `5a6c50979a3cd745742b9e28b8ea32fc8d648342c0ebdc77e33d42b7b7ac6c91` |
| `states/**`（27 个文件，600584 B）| — | `a89368fb8781e47e560f94acb14710bdeb022d0f57ce7de7cc9a9cb524e869ba` |

## t139-scripted-w90 / breakout / scripted

* 目录：`runs/model-player/t139-scripted-w90/breakout/scripted`
* verdict：`FAIL`（counts_as_pass=False，strict=FAIL，baseline=INCONCLUSIVE，game_side=FAIL）
* 注入/接受后变化/rate：3 / 2 / 0.6667
* 两窗对齐：4/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 5 frame(s))（matched 4/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game breakout --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9963 --window-frames 30 --out-prefix t139-jev-v3-w30`  <- t139_results_t139-jev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game breakout --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9964 --window-frames 90 --out-prefix t139-jev-v3-w90`  <- t139_results_t139-jev-v3-w90.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game breakout --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9961 --window-frames 30 --out-prefix t139-scripted-w30`  <- t139_results_t139-scripted-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game breakout --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9962 --window-frames 90 --out-prefix t139-scripted-w90`  <- t139_results_t139-scripted-w90.json (sweep driver)

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t139-scripted-w90/breakout/scripted/demo.png` | 98538 | `0f25bd5c88c5247520c911107933185e4c425077b4af34efbe1bedcbc28c08ba` |
| `runs/model-player/t139-scripted-w90/breakout/scripted/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t139-scripted-w90/breakout/scripted/engine-game.stdout.txt` | 5433 | `f4dfa8be0ed3725aa1815d7b4c72294b51e486e54385bc8250fc86e01eac8ac4` |
| `runs/model-player/t139-scripted-w90/breakout/scripted/filmstrip.png` | 73434 | `a15bb64bc4b87cf11dddeb0117848d067787d6f3d85d4a2707dd310959381e07` |
| `runs/model-player/t139-scripted-w90/breakout/scripted/frames.json` | 552110 | `2ec384204ee7996266891446eea8cf2cb33895facbb9f201573fc6ec4ed1b0f0` |
| `runs/model-player/t139-scripted-w90/breakout/scripted/player.json` | 23262 | `d4e96ca9b64b64731fba02b25b7ce6d9794d5a6c1b684a5e7425c49a28c3bed9` |
| `runs/model-player/t139-scripted-w90/breakout/scripted/session.json` | 11425 | `6519aea1af53a90a79e0667e64559a9c5852a7d5697928d527a80373be0045dc` |
| `runs/model-player/t139-scripted-w90/breakout/scripted/steps.jsonl` | 128596 | `31764d47865d96dae674b22eb12a994bbd56ebf5090dfbb82df52b641f2fcf8b` |
| `calls/**`（668 个文件，4570292 B）| — | `ccc1943c54f51796ee5a75fbfb8696adcda052779305b7ec5c213b0e9928304c` |
| `frames/**`（37 个文件，387301 B）| — | `80466ec5880d4dafb7eb883151e7cebc568e01a60ec328a8502baf2bc72c22d1` |
| `states/**`（27 个文件，148499 B）| — | `b03f463b7dbcbdb023886b46ca3361ec2a6e7e1410fa5eccc8ebd1c85c8c8366` |

## t139-scripted-w90 / flappy / scripted

* 目录：`runs/model-player/t139-scripted-w90/flappy/scripted`
* verdict：`INCONCLUSIVE`（counts_as_pass=False，strict=INCONCLUSIVE，baseline=INCONCLUSIVE，game_side=FAIL）
* 注入/接受后变化/rate：12 / 1 / 0.0833
* 两窗对齐：6/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 4 frame(s))（matched 6/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game flappy --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9963 --window-frames 30 --out-prefix t139-jev-v3-w30`  <- t139_results_t139-jev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game flappy --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9964 --window-frames 90 --out-prefix t139-jev-v3-w90`  <- t139_results_t139-jev-v3-w90.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game flappy --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9961 --window-frames 30 --out-prefix t139-scripted-w30`  <- t139_results_t139-scripted-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game flappy --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9962 --window-frames 90 --out-prefix t139-scripted-w90`  <- t139_results_t139-scripted-w90.json (sweep driver)

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t139-scripted-w90/flappy/scripted/demo.png` | 97895 | `68904e5f6fdcb966de5812afa3c04682bbf26f4e347ba4aca30a6d87a32cff6b` |
| `runs/model-player/t139-scripted-w90/flappy/scripted/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t139-scripted-w90/flappy/scripted/engine-game.stdout.txt` | 744 | `46f0c241c785d538b643691c8df5c5fbacbee55b3782d4a9335f29966498a4e8` |
| `runs/model-player/t139-scripted-w90/flappy/scripted/filmstrip.png` | 62706 | `ae8ef0baf441cc641d717f76f71d258e5f31301a4ba3d2d5d4f6595f1e320ce9` |
| `runs/model-player/t139-scripted-w90/flappy/scripted/frames.json` | 474344 | `19d54389913b11532a7601be73639345edddee878b7176963bc29544197da9a4` |
| `runs/model-player/t139-scripted-w90/flappy/scripted/player.json` | 24238 | `0be3a335175ce24949b9b235a8b2ffd90ee80940e677eacd351460d611e3bcc5` |
| `runs/model-player/t139-scripted-w90/flappy/scripted/session.json` | 11209 | `011e18a938166c2c330c32f55097ed70bda040239834b9c1731af02d0df9326d` |
| `runs/model-player/t139-scripted-w90/flappy/scripted/steps.jsonl` | 128274 | `ec43c246f994ec61388e5adf5c8213080c7dd0503a8f81a6ca1c77da37fb9fce` |
| `calls/**`（969 个文件，3494459 B）| — | `923cc0a3399213a180ea1ec65e906794dbd5e3c49c382d5066bc3c45a1b45648` |
| `frames/**`（37 个文件，329115 B）| — | `f5ba363ea883663d59272591255b230552839dcc925e719dd643fd5e5342a82f` |
| `states/**`（27 个文件，77155 B）| — | `867541814af516d8cbd5d5dd2721adbdf1b19e8c3b5d8f619d89e83fb22f4ae8` |

## t139-scripted-w90 / frogger / scripted

* 目录：`runs/model-player/t139-scripted-w90/frogger/scripted`
* verdict：`INCONCLUSIVE`（counts_as_pass=False，strict=INCONCLUSIVE，baseline=INCONCLUSIVE，game_side=INCONCLUSIVE）
* 注入/接受后变化/rate：1 / 1 / 1.0
* 两窗对齐：0/1 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 1 frame(s))（matched 0/1，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game frogger --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9963 --window-frames 30 --out-prefix t139-jev-v3-w30`  <- t139_results_t139-jev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game frogger --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9964 --window-frames 90 --out-prefix t139-jev-v3-w90`  <- t139_results_t139-jev-v3-w90.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game frogger --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9961 --window-frames 30 --out-prefix t139-scripted-w30`  <- t139_results_t139-scripted-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game frogger --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9962 --window-frames 90 --out-prefix t139-scripted-w90`  <- t139_results_t139-scripted-w90.json (sweep driver)

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t139-scripted-w90/frogger/scripted/demo.png` | 15281 | `8fdec9ae10fdf45f61ef6aebc6726486492e194502b90f155db542222f430881` |
| `runs/model-player/t139-scripted-w90/frogger/scripted/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t139-scripted-w90/frogger/scripted/engine-game.stdout.txt` | 748 | `53f58e6d99b878e837e3067af626105075ea07083970037418eeba26317662e7` |
| `runs/model-player/t139-scripted-w90/frogger/scripted/filmstrip.png` | 13847 | `41a1abe17bb8745049b0c731ffc6e75789fdeac125e14be700cf546557e0b969` |
| `runs/model-player/t139-scripted-w90/frogger/scripted/frames.json` | 63852 | `c958629ac07914c319915ea7705038bd0de51e1a56b014243502de6873a3db37` |
| `runs/model-player/t139-scripted-w90/frogger/scripted/player.json` | 16464 | `4cfde4a7d9422f1fb4a321614782d369f67e90e700fd6856136b59c2f52a5834` |
| `runs/model-player/t139-scripted-w90/frogger/scripted/session.json` | 11162 | `2cba144d6df3d1aa4e9eecebfcd3e1fa25f7b9fb60a6b3ff5c19baedbf46b9ef` |
| `runs/model-player/t139-scripted-w90/frogger/scripted/steps.jsonl` | 10848 | `e5ac52848813eebcf363461419efee9261c56e5e0746bbc2767fdcbb08de6959` |
| `calls/**`（80 个文件，393682 B）| — | `3088dca2ab15e81ee3e1dcf7b99d3a18ec9d9cd052183265810e4b4963a2ae03` |
| `frames/**`（4 个文件，45009 B）| — | `9bfaaebb652f6a0db64e9ee1e356705fc7f1ffeda4e5edef5a83c8e7e62506b3` |
| `states/**`（5 个文件，21032 B）| — | `44a10656b6547c6bfcbe8bb0ed4bacd193de92c4b7660ace7494ffd29bcd5d94` |

## t139-scripted-w90 / game2048 / scripted

* 目录：`runs/model-player/t139-scripted-w90/game2048/scripted`
* verdict：`PASS`（counts_as_pass=True，strict=PASS，baseline=PASS，game_side=PASS）
* 注入/接受后变化/rate：8 / 8 / 1.0
* 两窗对齐：3/8 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 3 frame(s))（matched 3/8，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game game2048 --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9963 --window-frames 30 --out-prefix t139-jev-v3-w30`  <- t139_results_t139-jev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game game2048 --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9964 --window-frames 90 --out-prefix t139-jev-v3-w90`  <- t139_results_t139-jev-v3-w90.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game game2048 --backend playjev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9965 --window-frames 30 --out-prefix t139-playjev-v3-w30`  <- t139_results_t139-playjev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game game2048 --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9961 --window-frames 30 --out-prefix t139-scripted-w30`  <- t139_results_t139-scripted-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game game2048 --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9962 --window-frames 90 --out-prefix t139-scripted-w90`  <- t139_results_t139-scripted-w90.json (sweep driver)

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t139-scripted-w90/game2048/scripted/demo.png` | 105326 | `96cd977cad7a157a05cd9b6c6bd772ba6d05f9e17ffbad42242d83a4ba36b822` |
| `runs/model-player/t139-scripted-w90/game2048/scripted/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t139-scripted-w90/game2048/scripted/engine-game.stdout.txt` | 781 | `0c8fb53ebd4419d60d12c005faab5b072ec7245c7ca32affdeeaa9b0d02ff96e` |
| `runs/model-player/t139-scripted-w90/game2048/scripted/filmstrip.png` | 65250 | `8b39ca1c5bc016326495bf62fcef6deb85db6194028962d7ac1691659d624cf2` |
| `runs/model-player/t139-scripted-w90/game2048/scripted/frames.json` | 452854 | `2fd5a5d713bb1ef2f8ed75b349a69091a60b1f019e5fc0e96171d0370dd6ddc3` |
| `runs/model-player/t139-scripted-w90/game2048/scripted/player.json` | 20040 | `8b30a16bf6a720ad1ff3b0f692decfdb5db6c757864b4e016b53a561d05e3b6d` |
| `runs/model-player/t139-scripted-w90/game2048/scripted/session.json` | 11118 | `07d7dba39324bd9564fcea9cc6d925e1f5b81282f7b0e08d34f8c14fc898569a` |
| `runs/model-player/t139-scripted-w90/game2048/scripted/steps.jsonl` | 104901 | `6b05265b9540cc938153a193714e2529cfd630868a87e4dbe391d5711ac4b660` |
| `calls/**`（619 个文件，4570426 B）| — | `d831c6fe1126360271421a7a9a9592b5edb1c3b54e16235b2c9f6ea5a3ea733b` |
| `frames/**`（25 个文件，321508 B）| — | `0c0faa7f441035fb8d665e018afb497780d51743e543071b2dbc54a63e46d163` |
| `states/**`（19 个文件，142714 B）| — | `9392b701478dbaef9fd1d7c989680bb2ef7187c0b86b561f28f1c110a5170f92` |

## t139-scripted-w90 / lunarlander / scripted

* 目录：`runs/model-player/t139-scripted-w90/lunarlander/scripted`
* verdict：`PASS`（counts_as_pass=True，strict=PASS，baseline=PASS，game_side=PASS）
* 注入/接受后变化/rate：8 / 8 / 1.0
* 两窗对齐：0/8 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 3 frame(s))（matched 0/8，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game lunarlander --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9963 --window-frames 30 --out-prefix t139-jev-v3-w30`  <- t139_results_t139-jev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game lunarlander --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9964 --window-frames 90 --out-prefix t139-jev-v3-w90`  <- t139_results_t139-jev-v3-w90.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game lunarlander --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9961 --window-frames 30 --out-prefix t139-scripted-w30`  <- t139_results_t139-scripted-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game lunarlander --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9962 --window-frames 90 --out-prefix t139-scripted-w90`  <- t139_results_t139-scripted-w90.json (sweep driver)

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t139-scripted-w90/lunarlander/scripted/demo.png` | 107979 | `fe675c0ccd51f4a1a4a15dacdee5ed33787374bcb35921b22c507796c1046466` |
| `runs/model-player/t139-scripted-w90/lunarlander/scripted/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t139-scripted-w90/lunarlander/scripted/engine-game.stdout.txt` | 766 | `ba6259d8187086567599a52b79571106a53f5ac3be39eaf6d46cd7cb3d535016` |
| `runs/model-player/t139-scripted-w90/lunarlander/scripted/filmstrip.png` | 74547 | `7e121b223ce72fb916f5091c356afbea366c6eea0c8f759119832428f5c4d443` |
| `runs/model-player/t139-scripted-w90/lunarlander/scripted/frames.json` | 455150 | `ed77409385244da17bb645ddf63f6e3d5adc6ed05e841c7b069ef4fa7a870544` |
| `runs/model-player/t139-scripted-w90/lunarlander/scripted/player.json` | 20170 | `773674a197165e65d327e103801175e6b0f7e8d7ebc97037ab78c9bfcd3d7d13` |
| `runs/model-player/t139-scripted-w90/lunarlander/scripted/session.json` | 11192 | `1ccbb290b02cb8397c733c626d52ee82f8a1963f4626b4a0da018616118947a3` |
| `runs/model-player/t139-scripted-w90/lunarlander/scripted/steps.jsonl` | 96432 | `3a135cfb0cd6b638b753a75ad83908d64c0d47756a35278211f4497c634777ca` |
| `calls/**`（601 个文件，6347687 B）| — | `cbf35c7575481aac62dd0f00da2469f12188c79aad17ead7aa3b4f397228576c` |
| `frames/**`（25 个文件，323393 B）| — | `d2ec01ae3a8805e7f64b21292bd702678acd7d85659ebe3e06a07e02873871b3` |
| `states/**`（19 个文件，227332 B）| — | `30f383b33a1d2ca8938553c05104a8cc31e58a88f8c1d2cbb5e307fcf8901ad1` |

## t139-scripted-w90 / match3 / scripted

* 目录：`runs/model-player/t139-scripted-w90/match3/scripted`
* verdict：`PASS`（counts_as_pass=True，strict=PASS，baseline=PASS，game_side=PASS）
* 注入/接受后变化/rate：12 / 8 / 1.0
* 两窗对齐：3/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 3 frame(s))（matched 3/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game match3 --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9963 --window-frames 30 --out-prefix t139-jev-v3-w30`  <- t139_results_t139-jev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game match3 --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9964 --window-frames 90 --out-prefix t139-jev-v3-w90`  <- t139_results_t139-jev-v3-w90.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game match3 --backend playjev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9965 --window-frames 30 --out-prefix t139-playjev-v3-w30`  <- t139_results_t139-playjev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game match3 --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9973 --window-frames 30 --out-prefix t139-scripted-w30`  <- t139_results_t139-scripted-w30-counterev.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game match3 --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9961 --window-frames 30 --out-prefix t139-scripted-w30`  <- t139_results_t139-scripted-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game match3 --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9962 --window-frames 90 --out-prefix t139-scripted-w90`  <- t139_results_t139-scripted-w90.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game match3 --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9961 --window-frames 90 --out-prefix t139-scripted-w90`  <- t136_commands.jsonl
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game match3 --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9972 --window-frames 90 --out-prefix t139-scripted-w90`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t139-scripted-w90/match3/scripted/demo.png` | 194195 | `318ac279eb46746d7107c1178ff9a85a203d43b5a654ecec8b6bcee8124a5333` |
| `runs/model-player/t139-scripted-w90/match3/scripted/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t139-scripted-w90/match3/scripted/engine-game.stdout.txt` | 769 | `f97f6997591ac469adeab2c3ab93bc1459eb2f686c8c500f07952143c2ca7c31` |
| `runs/model-player/t139-scripted-w90/match3/scripted/filmstrip.png` | 154043 | `38bdbcea42c10e16e0b234c96e405ce2a007215f051c5739c5be1e6ca1503b78` |
| `runs/model-player/t139-scripted-w90/match3/scripted/frames.json` | 611649 | `6dbaf13ba108fb42d001a41a85c9da94e4ce9d7d92d527e89bddfa524ef8a629` |
| `runs/model-player/t139-scripted-w90/match3/scripted/player.json` | 26580 | `9b02eaa38bf25a0a78f4a25652357681f6c353820a44edb4a101a0691285048f` |
| `runs/model-player/t139-scripted-w90/match3/scripted/session.json` | 12972 | `0df28acaf1be14d874973dcb719ddee8da957bf8b9bcf9d5dec04b0371ac3130` |
| `runs/model-player/t139-scripted-w90/match3/scripted/steps.jsonl` | 141561 | `53f6f12037fd1191522ef342df5e62953736e5cf4a944b066353838860a17aba` |
| `calls/**`（978 个文件，10664152 B）| — | `d2c81f168fe521b935644b164eb9f684365acf97e73619000e9f8bfb0b9d3cb1` |
| `frames/**`（37 个文件，431921 B）| — | `4665b0b36f69451cff63ffa1e365f8d371a4232893c49fcb1f01905e78b27a4a` |
| `states/**`（27 个文件，330711 B）| — | `eb40f32850134941e3561c9b4f2fbf329e864ec355fb8d72ec2a067495de6996` |

## t139-scripted-w90 / minesweeper / scripted

* 目录：`runs/model-player/t139-scripted-w90/minesweeper/scripted`
* verdict：`PASS`（counts_as_pass=True，strict=PASS，baseline=PASS，game_side=PASS）
* 注入/接受后变化/rate：12 / 7 / 1.0
* 两窗对齐：2/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 3 frame(s))（matched 2/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game minesweeper --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9963 --window-frames 30 --out-prefix t139-jev-v3-w30`  <- t139_results_t139-jev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game minesweeper --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9964 --window-frames 90 --out-prefix t139-jev-v3-w90`  <- t139_results_t139-jev-v3-w90.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game minesweeper --backend playjev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9965 --window-frames 30 --out-prefix t139-playjev-v3-w30`  <- t139_results_t139-playjev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game minesweeper --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9973 --window-frames 30 --out-prefix t139-scripted-w30`  <- t139_results_t139-scripted-w30-counterev.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game minesweeper --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9961 --window-frames 30 --out-prefix t139-scripted-w30`  <- t139_results_t139-scripted-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game minesweeper --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9962 --window-frames 90 --out-prefix t139-scripted-w90`  <- t139_results_t139-scripted-w90.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game minesweeper --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9972 --window-frames 90 --out-prefix t139-scripted-w90`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t139-scripted-w90/minesweeper/scripted/demo.png` | 186291 | `827275f29072d6cee0af785ad55fdb6212ce6781742933299dc06f5671d34c4a` |
| `runs/model-player/t139-scripted-w90/minesweeper/scripted/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t139-scripted-w90/minesweeper/scripted/engine-game.stdout.txt` | 745 | `82a73354e068f2d1cbf8ac2c58417eafeff9981e95f45c6e1854317d70a75afe` |
| `runs/model-player/t139-scripted-w90/minesweeper/scripted/filmstrip.png` | 182715 | `bb903653f3b27411a1d883980a94fcd0d53d7bb980bbac97557e61e6858d0426` |
| `runs/model-player/t139-scripted-w90/minesweeper/scripted/frames.json` | 810282 | `5b65cef62e901646fccaef06ececdd0cf3eb797bff5a660d0d3ffa05ff287c66` |
| `runs/model-player/t139-scripted-w90/minesweeper/scripted/player.json` | 27641 | `e386def9ed068951978e0afee34b0f39008a6df870e085a3fb6af22b81bbab88` |
| `runs/model-player/t139-scripted-w90/minesweeper/scripted/session.json` | 13107 | `aae433cabf82d40cf78b0734a100ee4ec832b72a07a5b95d514a631255f70a74` |
| `runs/model-player/t139-scripted-w90/minesweeper/scripted/steps.jsonl` | 140789 | `35c6d704057ad37f4a6531d5734c1cc5504e2cdefca2e0739b1f5c094a80a0d8` |
| `calls/**`（875 个文件，20750996 B）| — | `6db9ffe3f25821c3a4e275340d4e3b85d56f8bfc1cdcf81bf00dc24903033111` |
| `frames/**`（37 个文件，580787 B）| — | `8d0841f47e006aab4f86917cec748994b06d0813141093025e69dcb8686d0621` |
| `states/**`（27 个文件，787298 B）| — | `544aacc84d90ae9ae427238577e10f41cf4d2f95e18873f531a9f711042dfe97` |

## t139-scripted-w90 / missilecommand / scripted

* 目录：`runs/model-player/t139-scripted-w90/missilecommand/scripted`
* verdict：`PASS`（counts_as_pass=True，strict=PASS，baseline=PASS，game_side=PASS）
* 注入/接受后变化/rate：8 / 8 / 1.0
* 两窗对齐：5/8 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 3 frame(s))（matched 5/8，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game missilecommand --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9963 --window-frames 30 --out-prefix t139-jev-v3-w30`  <- t139_results_t139-jev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game missilecommand --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9964 --window-frames 90 --out-prefix t139-jev-v3-w90`  <- t139_results_t139-jev-v3-w90.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game missilecommand --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9961 --window-frames 30 --out-prefix t139-scripted-w30`  <- t139_results_t139-scripted-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game missilecommand --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9962 --window-frames 90 --out-prefix t139-scripted-w90`  <- t139_results_t139-scripted-w90.json (sweep driver)

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t139-scripted-w90/missilecommand/scripted/demo.png` | 108824 | `77337a51aa2d60b768712839dfc3de9b3f8102b9fec3809a0d13f54579e4e82e` |
| `runs/model-player/t139-scripted-w90/missilecommand/scripted/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t139-scripted-w90/missilecommand/scripted/engine-game.stdout.txt` | 742 | `bc404b0fc34f5dfa3b9e8887d59dbb5474c31c21dd7f40fb2a02c3c6ceead618` |
| `runs/model-player/t139-scripted-w90/missilecommand/scripted/filmstrip.png` | 56306 | `5fff3de1a77b7398fc08197f66db8df38f0784c122767d5c12a0c051351e5332` |
| `runs/model-player/t139-scripted-w90/missilecommand/scripted/frames.json` | 497519 | `028882bb4133b0b96e6767f3cfd9f1412f52f5f76802c204b315186bbe82a6c1` |
| `runs/model-player/t139-scripted-w90/missilecommand/scripted/player.json` | 20190 | `d5432eb2f5e246aa1836e660f151316ba41d43590fe77dbb0471f76ab16ac8d0` |
| `runs/model-player/t139-scripted-w90/missilecommand/scripted/session.json` | 11493 | `8687070687d14f96633cf7e515d240ede840cdd5c71edee48f63f7cab786f7a7` |
| `runs/model-player/t139-scripted-w90/missilecommand/scripted/steps.jsonl` | 98052 | `ac708b24dec05648561c05321067a725fe2a7baf439b0aa42462002d6db15b74` |
| `calls/**`（587 个文件，11139538 B）| — | `72c0857e2e72c3d5eefd26899560c8e543657cbdaf3a6eac091678248657acdd` |
| `frames/**`（25 个文件，354928 B）| — | `fc8ee3f6437b6d64fdaf2ce260561ddfe7a9d2b676a41d17fd6f8d8e57b94670` |
| `states/**`（19 个文件，441928 B）| — | `a06d47a366fb0991b5a12405c63d26be6fb474ee068e1afe8e9299d75f79580b` |

## t139-scripted-w90 / pacman / scripted

* 目录：`runs/model-player/t139-scripted-w90/pacman/scripted`
* verdict：`PASS`（counts_as_pass=True，strict=PASS，baseline=PASS，game_side=PASS）
* 注入/接受后变化/rate：12 / 7 / 1.0
* 两窗对齐：2/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 5 frame(s))（matched 2/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game pacman --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9963 --window-frames 30 --out-prefix t139-jev-v3-w30`  <- t139_results_t139-jev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game pacman --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9964 --window-frames 90 --out-prefix t139-jev-v3-w90`  <- t139_results_t139-jev-v3-w90.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game pacman --backend playjev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9965 --window-frames 30 --out-prefix t139-playjev-v3-w30`  <- t139_results_t139-playjev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game pacman --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9973 --window-frames 30 --out-prefix t139-scripted-w30`  <- t139_results_t139-scripted-w30-counterev.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game pacman --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9961 --window-frames 30 --out-prefix t139-scripted-w30`  <- t139_results_t139-scripted-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game pacman --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9962 --window-frames 90 --out-prefix t139-scripted-w90`  <- t139_results_t139-scripted-w90.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game pacman --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9961 --window-frames 90 --out-prefix t139-scripted-w90`  <- t136_commands.jsonl
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game pacman --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9972 --window-frames 90 --out-prefix t139-scripted-w90`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t139-scripted-w90/pacman/scripted/demo.png` | 146478 | `b2ac36203d74153f2e14cfa946cbeb6e9f4a63bd0761e54e53fcb22702c19a8d` |
| `runs/model-player/t139-scripted-w90/pacman/scripted/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t139-scripted-w90/pacman/scripted/engine-game.stdout.txt` | 733 | `75d5de601692abfe9408a8f4ac50c6ea59112adc0304125010f250d9576247ca` |
| `runs/model-player/t139-scripted-w90/pacman/scripted/filmstrip.png` | 146874 | `889c8b55347b4e8ebb9a5c7d98015b64eac09b169105d5192898e49cda287669` |
| `runs/model-player/t139-scripted-w90/pacman/scripted/frames.json` | 583834 | `1c387032d6daa7a9a0649f4b74ab35800835502aeb98cc2f344c36d6560fa70c` |
| `runs/model-player/t139-scripted-w90/pacman/scripted/player.json` | 26957 | `38648d148c899a7e2d36328722b3133732d887dee36505363e4e36b5f6c67266` |
| `runs/model-player/t139-scripted-w90/pacman/scripted/session.json` | 12535 | `e864f3568cee70f54c6702c0a9ca69a60a74af4f11c31e26e2ebc6eaab1d74f7` |
| `runs/model-player/t139-scripted-w90/pacman/scripted/steps.jsonl` | 143464 | `1ddcca82a988548aef09c3e07463767abf5b7e21562ab881e5306c2b5b3747cb` |
| `calls/**`（888 个文件，27018773 B）| — | `d4503dd6618de0770afb611bb1e345bb04548f37e2fc90cf7e37bfea30647c77` |
| `frames/**`（37 个文件，411185 B）| — | `c5e191967efaa2c47d022f9c8fd2430a3547b5e9632ef92296bdbee7a762470f` |
| `states/**`（27 个文件，1153945 B）| — | `72ba39947e035203b21971d5e27ef156f640f0d4474d34e18bfd8f108ea27579` |

## t139-scripted-w90 / platformer / scripted

* 目录：`runs/model-player/t139-scripted-w90/platformer/scripted`
* verdict：`INCONCLUSIVE`（counts_as_pass=False，strict=INCONCLUSIVE，baseline=INCONCLUSIVE，game_side=PASS）
* 注入/接受后变化/rate：8 / 5 / 1.0
* 两窗对齐：3/8 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 3 frame(s))（matched 3/8，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game platformer --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9963 --window-frames 30 --out-prefix t139-jev-v3-w30`  <- t139_results_t139-jev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game platformer --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9964 --window-frames 90 --out-prefix t139-jev-v3-w90`  <- t139_results_t139-jev-v3-w90.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game platformer --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9961 --window-frames 30 --out-prefix t139-scripted-w30`  <- t139_results_t139-scripted-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game platformer --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9962 --window-frames 90 --out-prefix t139-scripted-w90`  <- t139_results_t139-scripted-w90.json (sweep driver)

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t139-scripted-w90/platformer/scripted/demo.png` | 107678 | `bcc18f4ffe71dcbfc53816faec34dce7a6ad7a322f6015d1c8fa8ad3102e53b9` |
| `runs/model-player/t139-scripted-w90/platformer/scripted/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t139-scripted-w90/platformer/scripted/engine-game.stdout.txt` | 796 | `f72f6681f4bbfaf7b5735d87d689f0dcd4a9f07d69a645a744190ed1ee93b7f5` |
| `runs/model-player/t139-scripted-w90/platformer/scripted/filmstrip.png` | 69261 | `788efd3b47549ee0766f7c7e6b48c2843e0ad37eb855379180e4b1aa21f3f03f` |
| `runs/model-player/t139-scripted-w90/platformer/scripted/frames.json` | 387339 | `dd86d9d0a158b4237a23f468ee68e45266e16b68038b9c8a909bc2152e847627` |
| `runs/model-player/t139-scripted-w90/platformer/scripted/player.json` | 24376 | `de53c3923b84f02d029ba5314ddb4358649d6da200aeb6c67eb7c2e0d4299106` |
| `runs/model-player/t139-scripted-w90/platformer/scripted/session.json` | 11228 | `005c8d8cf5cc0b054554f5802a6cd9b59853ff17a8bf3c07ab8a14d61176513d` |
| `runs/model-player/t139-scripted-w90/platformer/scripted/steps.jsonl` | 105060 | `5eb80b0faa3886b76a39edc2226021540d7c1738e4ede6579749f677fb0414d6` |
| `calls/**`（573 个文件，9893726 B）| — | `a88bce9818c4c927bcc98e83f57b636180cca1e1c3a31eb20191d0a56c992833` |
| `frames/**`（25 个文件，272412 B）| — | `06bf27c797c3d497ad555600c3ac5ff10015b79893e8d6c9b327a5ca5f977df9` |
| `states/**`（19 个文件，408533 B）| — | `03e02b89dbefddd5e8674e4750cb71a56fa266c3ee9df9870510052da82bf4ca` |

## t139-scripted-w90 / pong / scripted

* 目录：`runs/model-player/t139-scripted-w90/pong/scripted`
* verdict：`PASS`（counts_as_pass=True，strict=PASS，baseline=PASS，game_side=PASS）
* 注入/接受后变化/rate：8 / 8 / 1.0
* 两窗对齐：2/8 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 5 frame(s))（matched 2/8，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game pong --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9963 --window-frames 30 --out-prefix t139-jev-v3-w30`  <- t139_results_t139-jev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game pong --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9964 --window-frames 90 --out-prefix t139-jev-v3-w90`  <- t139_results_t139-jev-v3-w90.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game pong --backend playjev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9965 --window-frames 30 --out-prefix t139-playjev-v3-w30`  <- t139_results_t139-playjev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game pong --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9961 --window-frames 30 --out-prefix t139-scripted-w30`  <- t139_results_t139-scripted-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game pong --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9962 --window-frames 90 --out-prefix t139-scripted-w90`  <- t139_results_t139-scripted-w90.json (sweep driver)

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t139-scripted-w90/pong/scripted/demo.png` | 51913 | `639b6f840d2528ac84d0d21ea30ba449d21bd1ab0949e52492d5e711d95134d0` |
| `runs/model-player/t139-scripted-w90/pong/scripted/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t139-scripted-w90/pong/scripted/engine-game.stdout.txt` | 3576 | `62fd22b3e4f3ebeb914a66eff8fdd5e45fbcd46958deec2735d72c4f980d8997` |
| `runs/model-player/t139-scripted-w90/pong/scripted/filmstrip.png` | 34901 | `548091e0062d002a60c4fef97dca483aec4c8b143a85048d5094c9effdac320f` |
| `runs/model-player/t139-scripted-w90/pong/scripted/frames.json` | 178834 | `1dd30788f9209dbbac9d8ded78a1c2d18058533ae2b24f4843db1b466e157f4f` |
| `runs/model-player/t139-scripted-w90/pong/scripted/player.json` | 20040 | `20aa5dddbdffebdc2c392f61a3219e99249063e41dd3bb111939e9502b6dad5b` |
| `runs/model-player/t139-scripted-w90/pong/scripted/session.json` | 11394 | `c74977e2e0e877befe6e184532e0aa5cf329cf512fde9957e03d31041e5e52b3` |
| `runs/model-player/t139-scripted-w90/pong/scripted/steps.jsonl` | 95302 | `972658efcde1d7315e89feb58e8423ba88cbc83b4fe1301d368092890b43a68a` |
| `calls/**`（805 个文件，2205776 B）| — | `38f003a0db606671232966f766240fb27775c90dcbe6e80c29f33c807d5f3aef` |
| `frames/**`（37 个文件，161312 B）| — | `79248bb9748a65cdc016aab9d18d95d1430ebb6f25c79ca70525de335d7bc0e0` |
| `states/**`（27 个文件，66319 B）| — | `cfd76f3a5fd12e61136552b55efbca247dc142e53a7c8eaacf1ed70bc01652c6` |

## t139-scripted-w90 / puzzlebobble / scripted

* 目录：`runs/model-player/t139-scripted-w90/puzzlebobble/scripted`
* verdict：`PASS`（counts_as_pass=True，strict=PASS，baseline=PASS，game_side=PASS）
* 注入/接受后变化/rate：8 / 8 / 1.0
* 两窗对齐：0/8 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 4 frame(s))（matched 0/8，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game puzzlebobble --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9963 --window-frames 30 --out-prefix t139-jev-v3-w30`  <- t139_results_t139-jev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game puzzlebobble --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9964 --window-frames 90 --out-prefix t139-jev-v3-w90`  <- t139_results_t139-jev-v3-w90.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game puzzlebobble --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9961 --window-frames 30 --out-prefix t139-scripted-w30`  <- t139_results_t139-scripted-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game puzzlebobble --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9962 --window-frames 90 --out-prefix t139-scripted-w90`  <- t139_results_t139-scripted-w90.json (sweep driver)

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t139-scripted-w90/puzzlebobble/scripted/demo.png` | 138756 | `2b46e1d279c7c33b6518fc23d4a65eb9f24444694314ec4f292ca2cd31383f3e` |
| `runs/model-player/t139-scripted-w90/puzzlebobble/scripted/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t139-scripted-w90/puzzlebobble/scripted/engine-game.stdout.txt` | 739 | `f428dc0c470aac5ebca9464f59c660632482d9d523bd75e472e545fe0c9437a7` |
| `runs/model-player/t139-scripted-w90/puzzlebobble/scripted/filmstrip.png` | 83632 | `87d297d66adb426d0bc397b4e07c73ddaf11f871f4d185be485901f7ea1b4266` |
| `runs/model-player/t139-scripted-w90/puzzlebobble/scripted/frames.json` | 481960 | `b29ee21c2c4afbdd2c700acc85f45fd5c37c82f24ee3ef197ca7a242163a1bb8` |
| `runs/model-player/t139-scripted-w90/puzzlebobble/scripted/player.json` | 20161 | `5403305e805c035585bbbf303c293893772e809f085db5f2dec39f4d9c069003` |
| `runs/model-player/t139-scripted-w90/puzzlebobble/scripted/session.json` | 11378 | `985020186442d8bc76dbbf753fa634957cdd232a71924a56f1674730c13febd9` |
| `runs/model-player/t139-scripted-w90/puzzlebobble/scripted/steps.jsonl` | 98206 | `fe3af32e32c8df1072e5f1df6a759aa95c4b7d5df832bf9db2bbc5ab57c19a4b` |
| `calls/**`（602 个文件，9960608 B）| — | `5590c8903c811e54dc52f0acc2500d487e340bcc0047317dae0e0aa14237afed` |
| `frames/**`（25 个文件，343266 B）| — | `177107bd96c13bdd2049cc8256a533ec1b798c43b16846de3efc2c48fd9649f0` |
| `states/**`（19 个文件，379497 B）| — | `e5925ac790f8346ec8bb475e914356cc255bd5c4927faf82af38f1f54ea23052` |

## t139-scripted-w90 / rtype / scripted

* 目录：`runs/model-player/t139-scripted-w90/rtype/scripted`
* verdict：`PASS`（counts_as_pass=True，strict=PASS，baseline=PASS，game_side=PASS）
* 注入/接受后变化/rate：8 / 8 / 1.0
* 两窗对齐：3/8 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 4 frame(s))（matched 3/8，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game rtype --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9963 --window-frames 30 --out-prefix t139-jev-v3-w30`  <- t139_results_t139-jev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game rtype --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9964 --window-frames 90 --out-prefix t139-jev-v3-w90`  <- t139_results_t139-jev-v3-w90.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game rtype --backend playjev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9965 --window-frames 30 --out-prefix t139-playjev-v3-w30`  <- t139_results_t139-playjev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game rtype --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9961 --window-frames 30 --out-prefix t139-scripted-w30`  <- t139_results_t139-scripted-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game rtype --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9962 --window-frames 90 --out-prefix t139-scripted-w90`  <- t139_results_t139-scripted-w90.json (sweep driver)

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t139-scripted-w90/rtype/scripted/demo.png` | 121068 | `d56960bfc32e2d5720149d1c90c9ab737f5193db5703101bb19bbdaaf44fcb59` |
| `runs/model-player/t139-scripted-w90/rtype/scripted/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t139-scripted-w90/rtype/scripted/engine-game.stdout.txt` | 743 | `05ba569c5ff358115b1f090e73efc6d8f60e5052fb6e04ca6ffce0a68dad941f` |
| `runs/model-player/t139-scripted-w90/rtype/scripted/filmstrip.png` | 69700 | `743b885d9b38104537e5f3c93ddc7ab0140c6ec6f5103cc2cda2ee1011df79a9` |
| `runs/model-player/t139-scripted-w90/rtype/scripted/frames.json` | 430147 | `149460385015c8b7b614102eafe4a9cf6c1d9f86f84b63af52fe4026057aec6f` |
| `runs/model-player/t139-scripted-w90/rtype/scripted/player.json` | 20149 | `5df1994fbdcdf9c6700c31eab42eff173bed9aa3a8bc4ce8404658e67e354d77` |
| `runs/model-player/t139-scripted-w90/rtype/scripted/session.json` | 11318 | `b7f054b6ebb02a78ae93cbbfc6852a2db0fb50147fce4d70473c8166a806de0e` |
| `runs/model-player/t139-scripted-w90/rtype/scripted/steps.jsonl` | 97484 | `065dd731402c5289cfab87dd4311c08507735c2d6325412619ee00b7069d4b36` |
| `calls/**`（571 个文件，8584403 B）| — | `5dde1d1022b2e61115c24f293a5323a74fdf0b0108c24475c62f74da13e35f34` |
| `frames/**`（25 个文件，304667 B）| — | `b468ce33365022a148c8151dac336ff73231930f7c5133d6cdd5b08b10f95565` |
| `states/**`（19 个文件，351833 B）| — | `3b1f4280cd3bfc4459d6e684e362ff646c97ab319317c83e296a255545ff09e0` |

## t139-scripted-w90 / snake / scripted

* 目录：`runs/model-player/t139-scripted-w90/snake/scripted`
* verdict：`PASS`（counts_as_pass=True，strict=PASS，baseline=PASS，game_side=PASS）
* 注入/接受后变化/rate：8 / 8 / 1.0
* 两窗对齐：1/8 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 6 frame(s))（matched 1/8，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game snake --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9963 --window-frames 30 --out-prefix t139-jev-v3-w30`  <- t139_results_t139-jev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game snake --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9964 --window-frames 90 --out-prefix t139-jev-v3-w90`  <- t139_results_t139-jev-v3-w90.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game snake --backend playjev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9965 --window-frames 30 --out-prefix t139-playjev-v3-w30`  <- t139_results_t139-playjev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game snake --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9961 --window-frames 30 --out-prefix t139-scripted-w30`  <- t139_results_t139-scripted-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game snake --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9962 --window-frames 90 --out-prefix t139-scripted-w90`  <- t139_results_t139-scripted-w90.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game snake --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9961 --window-frames 90 --out-prefix t139-scripted-w90`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t139-scripted-w90/snake/scripted/demo.png` | 44716 | `a15e6a91b4df883c9e668af539ce764722351657abf554b26fe399925af3b4ee` |
| `runs/model-player/t139-scripted-w90/snake/scripted/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t139-scripted-w90/snake/scripted/engine-game.stdout.txt` | 7420 | `e9b10dae905c6802a38be2845c4bf4ee1d65fab7ad60a880c3899b513648c8d4` |
| `runs/model-player/t139-scripted-w90/snake/scripted/filmstrip.png` | 30716 | `10624087db10231db98f7a488d60c4a9d94932b051c83e813c01725bb2395993` |
| `runs/model-player/t139-scripted-w90/snake/scripted/frames.json` | 126940 | `23b9ef57afa44bb19e543d796d27cc12a14a89805e8ae8a4b408abcb4edb868a` |
| `runs/model-player/t139-scripted-w90/snake/scripted/player.json` | 20159 | `3616a7bbde222f8d458027533f7a89a555f205913e6e81303bd29ca944ee8fcd` |
| `runs/model-player/t139-scripted-w90/snake/scripted/session.json` | 11954 | `313956036f9eabb46515e4543d9adfb5ae31cc7fe80073bd047b49f231506d3a` |
| `runs/model-player/t139-scripted-w90/snake/scripted/steps.jsonl` | 103013 | `26e7e1491031f1d10ddc46347a7161369b32332aebc467c88a62909cffce2e47` |
| `calls/**`（445 个文件，3082027 B）| — | `25f8537b231847c57c42a3adb119fcce66835073a8412e3be76fd27d71ec6560` |
| `frames/**`（25 个文件，77380 B）| — | `2e85e11d947382551f0f6267012c69279333efdb363684577f0ab0aac5500aa2` |
| `states/**`（19 个文件，166663 B）| — | `fa9880ec5da55a8983e5931eea38b0a63d1f1122755268a46d3ec32c12817800` |

## t139-scripted-w90 / sokoban / scripted

* 目录：`runs/model-player/t139-scripted-w90/sokoban/scripted`
* verdict：`PASS`（counts_as_pass=True，strict=PASS，baseline=PASS，game_side=PASS）
* 注入/接受后变化/rate：12 / 9 / 1.0
* 两窗对齐：2/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 4 frame(s))（matched 2/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game sokoban --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9963 --window-frames 30 --out-prefix t139-jev-v3-w30`  <- t139_results_t139-jev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game sokoban --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9964 --window-frames 90 --out-prefix t139-jev-v3-w90`  <- t139_results_t139-jev-v3-w90.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game sokoban --backend playjev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9965 --window-frames 30 --out-prefix t139-playjev-v3-w30`  <- t139_results_t139-playjev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game sokoban --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9973 --window-frames 30 --out-prefix t139-scripted-w30`  <- t139_results_t139-scripted-w30-counterev.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game sokoban --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9961 --window-frames 30 --out-prefix t139-scripted-w30`  <- t139_results_t139-scripted-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game sokoban --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9962 --window-frames 90 --out-prefix t139-scripted-w90`  <- t139_results_t139-scripted-w90.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game sokoban --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9972 --window-frames 90 --out-prefix t139-scripted-w90`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t139-scripted-w90/sokoban/scripted/demo.png` | 139576 | `8d59192b1c13f355664beec196550cdff3fa531986c1e8ad5af3be4e764560b1` |
| `runs/model-player/t139-scripted-w90/sokoban/scripted/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t139-scripted-w90/sokoban/scripted/engine-game.stdout.txt` | 745 | `1a942c46151f85f799233ee887511f00675e58841b083b322c5209b76c635dad` |
| `runs/model-player/t139-scripted-w90/sokoban/scripted/filmstrip.png` | 107313 | `22f71c379de06c60d2abaefe078356f5413c6b07608869326e69fd633b7ae453` |
| `runs/model-player/t139-scripted-w90/sokoban/scripted/frames.json` | 646922 | `1397f0b7c71b4653813506356b0e75b581520f72712a3691b6b3b53a2a4b0f64` |
| `runs/model-player/t139-scripted-w90/sokoban/scripted/player.json` | 25489 | `545332eed73431aefba45c80c1f61230191c8dc85409c8c2de8b202b7f1b6f12` |
| `runs/model-player/t139-scripted-w90/sokoban/scripted/session.json` | 12683 | `8007e321a96bbd5f3ab5c07596af11c69392e948541792974e89769f72157253` |
| `runs/model-player/t139-scripted-w90/sokoban/scripted/steps.jsonl` | 147803 | `60521ab55a6006d5e9506554d0ced58541afa00489655bc370af57b686f1491d` |
| `calls/**`（935 个文件，11493893 B）| — | `ae47846f9801b2dfb4a4355d064e2656e38b5468c7ea3954453110481b9f44f0` |
| `frames/**`（37 个文件，458340 B）| — | `ff4808df4121a973d7f15f417b8ab009c880c17f6ffd2336459f96a9634ed493` |
| `states/**`（27 个文件，374464 B）| — | `ebf0db342eb512642daff127136d87e2a34e441cb3dbf39145de3b7276bcc963` |

## t139-scripted-w90 / spaceinvaders / scripted

* 目录：`runs/model-player/t139-scripted-w90/spaceinvaders/scripted`
* verdict：`PASS`（counts_as_pass=True，strict=PASS，baseline=PASS，game_side=PASS）
* 注入/接受后变化/rate：8 / 8 / 1.0
* 两窗对齐：2/8 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 4 frame(s))（matched 2/8，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game spaceinvaders --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9963 --window-frames 30 --out-prefix t139-jev-v3-w30`  <- t139_results_t139-jev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game spaceinvaders --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9964 --window-frames 90 --out-prefix t139-jev-v3-w90`  <- t139_results_t139-jev-v3-w90.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game spaceinvaders --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9961 --window-frames 30 --out-prefix t139-scripted-w30`  <- t139_results_t139-scripted-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game spaceinvaders --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9962 --window-frames 90 --out-prefix t139-scripted-w90`  <- t139_results_t139-scripted-w90.json (sweep driver)

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t139-scripted-w90/spaceinvaders/scripted/demo.png` | 86285 | `bbc6eed2779e033ef7c2ad0429b6ac2b91b82721d6e88db81b8a74d00925d1d7` |
| `runs/model-player/t139-scripted-w90/spaceinvaders/scripted/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t139-scripted-w90/spaceinvaders/scripted/engine-game.stdout.txt` | 754 | `1f796c8af22fdea1efda0b030e38bdb451790f2570cb27395b0b7482515bd921` |
| `runs/model-player/t139-scripted-w90/spaceinvaders/scripted/filmstrip.png` | 60564 | `2e1908b9aa000be411004863042aeeeefe996a5570d8799ac1c33ee5f0593843` |
| `runs/model-player/t139-scripted-w90/spaceinvaders/scripted/frames.json` | 349846 | `8c719a4262a4b0b7810d10689c272389f8cb1ef64ce94ca7806f3a2fe23ae878` |
| `runs/model-player/t139-scripted-w90/spaceinvaders/scripted/player.json` | 20170 | `be65979cb4f07ad9d22b66ec692ffabda31e392a81fb91fa538a0f280bc27b42` |
| `runs/model-player/t139-scripted-w90/spaceinvaders/scripted/session.json` | 11289 | `17090e0186dfd8580f6456006143e4fb35f2b1e0c60c5f6f5de7fe515fde7d92` |
| `runs/model-player/t139-scripted-w90/spaceinvaders/scripted/steps.jsonl` | 97851 | `bfb1ca63b68061ecbddcae551ef629ec62ac6d0f01f92503074e7f7f5634fe16` |
| `calls/**`（618 个文件，4951283 B）| — | `2b966545e793a5d455a52a1740b13d969ae1a289ba910f2c1943e0a20a3f1d6e` |
| `frames/**`（25 个文件，244147 B）| — | `dca5df4fc4f3d50dfbb84f71753eb5d11fc6e7d80855a39c0738c72402d30fc1` |
| `states/**`（19 个文件，169584 B）| — | `1bb92d3244b73d20a63ea8e45078d0ec46642b5a0195d1a4205d9e575e986981` |

## t139-scripted-w90 / tetris / scripted

* 目录：`runs/model-player/t139-scripted-w90/tetris/scripted`
* verdict：`PASS`（counts_as_pass=True，strict=PASS，baseline=PASS，game_side=PASS）
* 注入/接受后变化/rate：8 / 8 / 1.0
* 两窗对齐：2/8 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 5 frame(s))（matched 2/8，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game tetris --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9963 --window-frames 30 --out-prefix t139-jev-v3-w30`  <- t139_results_t139-jev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game tetris --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9964 --window-frames 90 --out-prefix t139-jev-v3-w90`  <- t139_results_t139-jev-v3-w90.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game tetris --backend playjev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9965 --window-frames 30 --out-prefix t139-playjev-v3-w30`  <- t139_results_t139-playjev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game tetris --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9961 --window-frames 30 --out-prefix t139-scripted-w30`  <- t139_results_t139-scripted-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game tetris --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9962 --window-frames 90 --out-prefix t139-scripted-w90`  <- t139_results_t139-scripted-w90.json (sweep driver)

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t139-scripted-w90/tetris/scripted/demo.png` | 51366 | `d63646b22803d99e27d3e4c201ef7e0ecec39c44656e64e3afeeb73f502c79f5` |
| `runs/model-player/t139-scripted-w90/tetris/scripted/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t139-scripted-w90/tetris/scripted/engine-game.stdout.txt` | 6804 | `6a334e6a11c4bf684fd432e0e1ca5528a9815c8ed3432d10fa2edeb1989fd257` |
| `runs/model-player/t139-scripted-w90/tetris/scripted/filmstrip.png` | 34096 | `cd85452d53a798b699c464c46417fdb682402fee602c4cac11ccb69e3654cb38` |
| `runs/model-player/t139-scripted-w90/tetris/scripted/frames.json` | 196021 | `a1a83363b002c283742f60bc62defd35bc87e59487829499cb4782bf9d61e3c2` |
| `runs/model-player/t139-scripted-w90/tetris/scripted/player.json` | 20244 | `4073de6037e3df82f4c338439340be3889e27446247978f796ef33d08c94e76c` |
| `runs/model-player/t139-scripted-w90/tetris/scripted/session.json` | 11179 | `5496a03b8588d09f4f83b33e46d5f3757347916797a33584ca2d3bf59a54b91c` |
| `runs/model-player/t139-scripted-w90/tetris/scripted/steps.jsonl` | 86897 | `aa0ecbbfab419af06b6319722b10599995b50de551473c166de813f23dba5dfd` |
| `calls/**`（633 个文件，1403939 B）| — | `f39f9be871955995c8f7803af12dfa21463ffe676a7413475b41637ecde2fddf` |
| `frames/**`（25 个文件，128882 B）| — | `a6b4bab3d3cca4ed6e928d47d90b5a5ec71762373b89eec674ca17e86f97af65` |
| `states/**`（19 个文件，29839 B）| — | `2f208695d20175867322b1b81e78d62704bf099f07f8d27a07a760be6bf3e925` |

## t139-scripted-w90 / towerdefense / scripted

* 目录：`runs/model-player/t139-scripted-w90/towerdefense/scripted`
* verdict：`PASS`（counts_as_pass=True，strict=PASS，baseline=PASS，game_side=PASS）
* 注入/接受后变化/rate：12 / 9 / 1.0
* 两窗对齐：1/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 4 frame(s))（matched 1/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game towerdefense --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9963 --window-frames 30 --out-prefix t139-jev-v3-w30`  <- t139_results_t139-jev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game towerdefense --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9964 --window-frames 90 --out-prefix t139-jev-v3-w90`  <- t139_results_t139-jev-v3-w90.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game towerdefense --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9973 --window-frames 30 --out-prefix t139-scripted-w30`  <- t139_results_t139-scripted-w30-counterev.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game towerdefense --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9961 --window-frames 30 --out-prefix t139-scripted-w30`  <- t139_results_t139-scripted-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game towerdefense --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9962 --window-frames 90 --out-prefix t139-scripted-w90`  <- t139_results_t139-scripted-w90.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game towerdefense --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9972 --window-frames 90 --out-prefix t139-scripted-w90`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t139-scripted-w90/towerdefense/scripted/demo.png` | 163764 | `94d0b6b64960faf6c9336da8ae6d2c271c123a94fc21c6ce9f1f69c6b563a3af` |
| `runs/model-player/t139-scripted-w90/towerdefense/scripted/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t139-scripted-w90/towerdefense/scripted/engine-game.stdout.txt` | 753 | `cc30f6bab70d4d113f04a202c540c9707dbc03e1ad8f6cbb5c481a853654785b` |
| `runs/model-player/t139-scripted-w90/towerdefense/scripted/filmstrip.png` | 131272 | `a99807424101d51b52c9b7906e2bf78e57d52e95b8b0cc6de12da8a3c2f9e22b` |
| `runs/model-player/t139-scripted-w90/towerdefense/scripted/frames.json` | 637978 | `3733cd3d1a5c0df703582ade352aa968756ec8b953ff0710890254f86ab9e7aa` |
| `runs/model-player/t139-scripted-w90/towerdefense/scripted/player.json` | 25667 | `d487005397c56549c81d94725990e36635ee377c2806bd7f2411d33bb7219152` |
| `runs/model-player/t139-scripted-w90/towerdefense/scripted/session.json` | 12932 | `4eb52b5db0aafddfcb261e85269ca17a528087b8a8471d7f7d28b3517683490f` |
| `runs/model-player/t139-scripted-w90/towerdefense/scripted/steps.jsonl` | 138454 | `ce06a74b866e5f8b5c43610775b01eb1dfcd965499d3074b3d5d5e143bb44d50` |
| `calls/**`（888 个文件，16983070 B）| — | `5be63150460ec70ffb9246b9ce2b15cf1120c34fff79db2174c675450d85f184` |
| `frames/**`（37 个文件，451587 B）| — | `8264a44c254814c03284242ebbdaed4a960d6b145f0ac504c6e82d1718f12f69` |
| `states/**`（27 个文件，648217 B）| — | `0e9bea19094bff65684217fb7365e44975b0267949b6638cdf61cbd03152a7af` |

## t139-jev-v3-w30 / asteroids / jev

* 目录：`runs/model-player/t139-jev-v3-w30/asteroids/jev`
* verdict：`PASS`（counts_as_pass=True，strict=PASS，baseline=PASS，game_side=None）
* 注入/接受后变化/rate：8 / 8 / 1.0
* 两窗对齐：3/8 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 2 frame(s))（matched 3/8，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game asteroids --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9963 --window-frames 30 --out-prefix t139-jev-v3-w30`  <- t139_results_t139-jev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game asteroids --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9964 --window-frames 90 --out-prefix t139-jev-v3-w90`  <- t139_results_t139-jev-v3-w90.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game asteroids --backend playjev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9965 --window-frames 30 --out-prefix t139-playjev-v3-w30`  <- t139_results_t139-playjev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game asteroids --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9961 --window-frames 30 --out-prefix t139-scripted-w30`  <- t139_results_t139-scripted-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game asteroids --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9962 --window-frames 90 --out-prefix t139-scripted-w90`  <- t139_results_t139-scripted-w90.json (sweep driver)

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t139-jev-v3-w30/asteroids/jev/demo.png` | 97866 | `1d9c3f8808d2e088dfd5952eb0b55e3ea4d1c792057c5fd7a03b0cd324d3632f` |
| `runs/model-player/t139-jev-v3-w30/asteroids/jev/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t139-jev-v3-w30/asteroids/jev/engine-game.stdout.txt` | 741 | `b2b28b5945f0cfd4760ac38f018de5faffc831be2466f67f0238c24d90015947` |
| `runs/model-player/t139-jev-v3-w30/asteroids/jev/filmstrip.png` | 48203 | `edec3737ac6c930b559ffdbab7ba0c6df85bf176a84eece2a1d10ae8a0d8b1df` |
| `runs/model-player/t139-jev-v3-w30/asteroids/jev/frames.json` | 369486 | `4ac00e1577cbdf7872e841ecc3ccadf4000aa9b2262bf68f086fff56c50c0629` |
| `runs/model-player/t139-jev-v3-w30/asteroids/jev/player.json` | 169166 | `bf604b720a350200fb6e372a1c5bd9228a00730609fb5c6b686c425fe6e84fc1` |
| `runs/model-player/t139-jev-v3-w30/asteroids/jev/session.json` | 11151 | `164ec7bdf5336c6fc1129e07a1dc865735e580166f562e4e8ab8f17f7ad73f9d` |
| `runs/model-player/t139-jev-v3-w30/asteroids/jev/steps.jsonl` | 108574 | `41cbbc1a6bb70eb567e794ee70a7743b4fc0fa7e4ff6741eb377bce8e3db32fc` |
| `calls/**`（428 个文件，1728162 B）| — | `e1cb88a27ee58cc83ef41959c71c81ef1804c6ea6fc6ebf0d2f9c9a464a9e21c` |
| `frames/**`（37 个文件，384068 B）| — | `974d20bbfe5b488d52df6c48e759a69a528259439b61edec3db51559dbf9fc36` |
| `states/**`（27 个文件，78512 B）| — | `c6308d1b07cc0a9d35b386ff66f28d24b416741ccf5ac09ab952c392cce80771` |

## t139-jev-v3-w30 / bomberman / jev

* 目录：`runs/model-player/t139-jev-v3-w30/bomberman/jev`
* verdict：`INCONCLUSIVE`（counts_as_pass=False，strict=INCONCLUSIVE，baseline=INCONCLUSIVE，game_side=None）
* 注入/接受后变化/rate：12 / 1 / 0.0833
* 两窗对齐：2/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 3 frame(s))（matched 2/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game bomberman --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9963 --window-frames 30 --out-prefix t139-jev-v3-w30`  <- t139_results_t139-jev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game bomberman --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9964 --window-frames 90 --out-prefix t139-jev-v3-w90`  <- t139_results_t139-jev-v3-w90.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game bomberman --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9961 --window-frames 30 --out-prefix t139-scripted-w30`  <- t139_results_t139-scripted-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game bomberman --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9962 --window-frames 90 --out-prefix t139-scripted-w90`  <- t139_results_t139-scripted-w90.json (sweep driver)

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t139-jev-v3-w30/bomberman/jev/demo.png` | 165491 | `c155730e33668eb7d0da39051a933e131f2f25c163ae5b592d0259992c95f01e` |
| `runs/model-player/t139-jev-v3-w30/bomberman/jev/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t139-jev-v3-w30/bomberman/jev/engine-game.stdout.txt` | 775 | `5ef61df022684999ee2dbb43bc92cc103e904477d3035da13d6c3c9219439824` |
| `runs/model-player/t139-jev-v3-w30/bomberman/jev/filmstrip.png` | 142395 | `265a175470b72a7d914e3cf5182588cef2ff1ae9cf8e33b384669d3cbeb06324` |
| `runs/model-player/t139-jev-v3-w30/bomberman/jev/frames.json` | 510995 | `4cf36239067ee496b8ab55583f14c71d964eaf09e329368342da50b5619afc02` |
| `runs/model-player/t139-jev-v3-w30/bomberman/jev/player.json` | 240860 | `cfb41a0f447118d377c0623965e7a356bda31239a4aba2c8b73c8ec120ffce22` |
| `runs/model-player/t139-jev-v3-w30/bomberman/jev/session.json` | 11261 | `c3fe112e3b22f6bc651d9896427945cdc23bb812b7e30af862f68f78c58a62fb` |
| `runs/model-player/t139-jev-v3-w30/bomberman/jev/steps.jsonl` | 144732 | `1cdcebe8e8430e34c4582472853359d3c3a213bc9fd0ab316b64e6f07ca05467` |
| `calls/**`（417 个文件，6431721 B）| — | `8a6e25bf14f9fbf9cb4f11c77155e476c2949998ad39404d553adc91b624f2bc` |
| `frames/**`（37 个文件，356515 B）| — | `6d04cd6ab875752a98be4de050dec265580d29283189c906e4f7b28fb5c9431c` |
| `states/**`（27 个文件，600130 B）| — | `6e2b063c4d57d757413797f9644320b002c6298175d267877e488ce467acf75f` |

## t139-jev-v3-w30 / breakout / jev

* 目录：`runs/model-player/t139-jev-v3-w30/breakout/jev`
* verdict：`FAIL`（counts_as_pass=False，strict=FAIL，baseline=FAIL，game_side=None）
* 注入/接受后变化/rate：12 / 3 / 0.25
* 两窗对齐：2/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 6 frame(s))（matched 2/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game breakout --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9963 --window-frames 30 --out-prefix t139-jev-v3-w30`  <- t139_results_t139-jev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game breakout --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9964 --window-frames 90 --out-prefix t139-jev-v3-w90`  <- t139_results_t139-jev-v3-w90.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game breakout --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9961 --window-frames 30 --out-prefix t139-scripted-w30`  <- t139_results_t139-scripted-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game breakout --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9962 --window-frames 90 --out-prefix t139-scripted-w90`  <- t139_results_t139-scripted-w90.json (sweep driver)

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t139-jev-v3-w30/breakout/jev/demo.png` | 98296 | `e4c7514bf50113884bd1147906493e89e4a4fd86231f87ef16a993bfb33aee6e` |
| `runs/model-player/t139-jev-v3-w30/breakout/jev/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t139-jev-v3-w30/breakout/jev/engine-game.stdout.txt` | 25402 | `c8562113ffa4808f29c86a24eb6e96da38d268fe25e001ba9b1ef614a8a61f60` |
| `runs/model-player/t139-jev-v3-w30/breakout/jev/filmstrip.png` | 65836 | `f7ebec3fd696e77e4b0feda652256e1e2c0e0287b8fbddf69b5c16b43afbc524` |
| `runs/model-player/t139-jev-v3-w30/breakout/jev/frames.json` | 341519 | `5a9665824afcd5eadf8bf09c11e802c2d4ef1ebe61292211e4a527a6b84b1695` |
| `runs/model-player/t139-jev-v3-w30/breakout/jev/player.json` | 177038 | `f100e6bec3c510af8ba05ef47670ac2354e5d2daa81b34d60720e1dc9d2562b4` |
| `runs/model-player/t139-jev-v3-w30/breakout/jev/session.json` | 11315 | `98c30edb7a13d61523c5632cd66a46a65d3022ada1da78c82111a2e113c5ad0c` |
| `runs/model-player/t139-jev-v3-w30/breakout/jev/steps.jsonl` | 163439 | `1d1ae7b5bb2c59807eb96829755743201cd20988f8b56d2c1b87b943bbcbb991` |
| `calls/**`（321 个文件，1497532 B）| — | `f81d497499d120c20c9929a32d03ec7cab2eea1b1b6a58ca62521d0b3d787988` |
| `frames/**`（37 个文件，229553 B）| — | `2c792509299abb7a3de2a0335ca864339aa9d23d2065553cd98e02200c4bcd02` |
| `states/**`（27 个文件，147339 B）| — | `b98910a469035ce80268368e228d206f7bdad733a571d4851dea99780d8a4281` |

## t139-jev-v3-w30 / flappy / jev

* 目录：`runs/model-player/t139-jev-v3-w30/flappy/jev`
* verdict：`INCONCLUSIVE`（counts_as_pass=False，strict=INCONCLUSIVE，baseline=INCONCLUSIVE，game_side=None）
* 注入/接受后变化/rate：12 / 1 / 0.0833
* 两窗对齐：2/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 4 frame(s))（matched 2/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game flappy --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9963 --window-frames 30 --out-prefix t139-jev-v3-w30`  <- t139_results_t139-jev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game flappy --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9964 --window-frames 90 --out-prefix t139-jev-v3-w90`  <- t139_results_t139-jev-v3-w90.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game flappy --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9961 --window-frames 30 --out-prefix t139-scripted-w30`  <- t139_results_t139-scripted-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game flappy --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9962 --window-frames 90 --out-prefix t139-scripted-w90`  <- t139_results_t139-scripted-w90.json (sweep driver)

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t139-jev-v3-w30/flappy/jev/demo.png` | 107223 | `461d17392fc81adb01d73caa13c323fa2cf6dbb1e576fb512350fc300fa107c9` |
| `runs/model-player/t139-jev-v3-w30/flappy/jev/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t139-jev-v3-w30/flappy/jev/engine-game.stdout.txt` | 744 | `1e6a2a5b905c8fcefad64bc4adc7fe74b288fe2a2ac366ff5d57703e1037f1c9` |
| `runs/model-player/t139-jev-v3-w30/flappy/jev/filmstrip.png` | 62659 | `1b55d1cab92b55345f4c37abc96b407f296f51d0ebb934772085f18ffb681373` |
| `runs/model-player/t139-jev-v3-w30/flappy/jev/frames.json` | 474075 | `b8acd28e193d8cb8e16fd4e8a7987edd1452e4bf6fe2cde6ca82f8cacb8ccaa5` |
| `runs/model-player/t139-jev-v3-w30/flappy/jev/player.json` | 215618 | `5595f8bf5ed163c3602637912f98c6262a292ea083c5c2c672b9baa791df044a` |
| `runs/model-player/t139-jev-v3-w30/flappy/jev/session.json` | 11103 | `01d102e6aac3869724dd5b79be39403e4d5b29e120b4d5be8cd20cbb95edebc5` |
| `runs/model-player/t139-jev-v3-w30/flappy/jev/steps.jsonl` | 135376 | `939b8ed949768f5fed719d9c62feebd1a141850bba2a483bd7c3be5811a31174` |
| `calls/**`（384 个文件，1288557 B）| — | `8c23ded5f7ac71bb3abdc62abafbae0cf089800a8aa7bcc72a94e149f4eb5e33` |
| `frames/**`（37 个文件，329115 B）| — | `411ecb40a165d5559f05db0a172b32683e70bde7f17a5bf02547328e56ff2fdf` |
| `states/**`（27 个文件，77139 B）| — | `5f65fb3cada2106d7e448e26154f2d61bb8ca7ddd50eea9e993ed65cb487270e` |

## t139-jev-v3-w30 / frogger / jev

* 目录：`runs/model-player/t139-jev-v3-w30/frogger/jev`
* verdict：`INCONCLUSIVE`（counts_as_pass=False，strict=INCONCLUSIVE，baseline=INCONCLUSIVE，game_side=None）
* 注入/接受后变化/rate：1 / 1 / 1.0
* 两窗对齐：0/1 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 2 frame(s))（matched 0/1，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game frogger --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9963 --window-frames 30 --out-prefix t139-jev-v3-w30`  <- t139_results_t139-jev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game frogger --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9964 --window-frames 90 --out-prefix t139-jev-v3-w90`  <- t139_results_t139-jev-v3-w90.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game frogger --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9961 --window-frames 30 --out-prefix t139-scripted-w30`  <- t139_results_t139-scripted-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game frogger --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9962 --window-frames 90 --out-prefix t139-scripted-w90`  <- t139_results_t139-scripted-w90.json (sweep driver)

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t139-jev-v3-w30/frogger/jev/demo.png` | 16460 | `6558956f37a432ca70c368ec0db1c72a953a65cabff23e91448506cfc9a77a0e` |
| `runs/model-player/t139-jev-v3-w30/frogger/jev/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t139-jev-v3-w30/frogger/jev/engine-game.stdout.txt` | 748 | `8c3779778545f9e179ea806bf88911307fcb60641f88866eab7f8d96961ad8a6` |
| `runs/model-player/t139-jev-v3-w30/frogger/jev/filmstrip.png` | 13787 | `dc32caa8a5872a2849b207f90bbdc6c64605513c046e8762f1f28bc07a23f70e` |
| `runs/model-player/t139-jev-v3-w30/frogger/jev/frames.json` | 63824 | `e37300b729c806cf0af3b1fb2e1a5f34ed8c4fc0b5747219000a7369d5e8fdab` |
| `runs/model-player/t139-jev-v3-w30/frogger/jev/player.json` | 38094 | `a85975906abc6bc94fb48fee58c097a101ce48b3554f68c464f4b9bcdd5c7d6d` |
| `runs/model-player/t139-jev-v3-w30/frogger/jev/session.json` | 11055 | `83d60b74017c9ace1329f99b736b5b10f324512490892f52a1811594f6906707` |
| `runs/model-player/t139-jev-v3-w30/frogger/jev/steps.jsonl` | 11698 | `fc08594e38b8bd16436195550a2b7b4ea37c1c614ae456f5e2e304e6a75bbd63` |
| `calls/**`（39 个文件，208164 B）| — | `d1b86e4ecfd7f75f890dfe1d6dc2da12563a4627bf5d411ec8e516b5c61be87d` |
| `frames/**`（4 个文件，45009 B）| — | `5747cfd02b02f26a905befc908e480176ef5bd05e28ca8eb5a3cb91de8bb3230` |
| `states/**`（5 个文件，21032 B）| — | `3b3bdfc5601e9ee26d6938a8dc6b8a198e6efbc46bb2321de0c6df71420ee76e` |

## t139-jev-v3-w30 / game2048 / jev

* 目录：`runs/model-player/t139-jev-v3-w30/game2048/jev`
* verdict：`INCONCLUSIVE`（counts_as_pass=False，strict=INCONCLUSIVE，baseline=INCONCLUSIVE，game_side=None）
* 注入/接受后变化/rate：5 / 5 / 1.0
* 两窗对齐：5/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 4 frame(s))（matched 5/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game game2048 --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9963 --window-frames 30 --out-prefix t139-jev-v3-w30`  <- t139_results_t139-jev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game game2048 --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9964 --window-frames 90 --out-prefix t139-jev-v3-w90`  <- t139_results_t139-jev-v3-w90.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game game2048 --backend playjev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9965 --window-frames 30 --out-prefix t139-playjev-v3-w30`  <- t139_results_t139-playjev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game game2048 --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9961 --window-frames 30 --out-prefix t139-scripted-w30`  <- t139_results_t139-scripted-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game game2048 --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9962 --window-frames 90 --out-prefix t139-scripted-w90`  <- t139_results_t139-scripted-w90.json (sweep driver)

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t139-jev-v3-w30/game2048/jev/demo.png` | 140690 | `2fc42369c712da6d13bc81e8d1a77405476301f6b9f07f12af303dbc947b7ee6` |
| `runs/model-player/t139-jev-v3-w30/game2048/jev/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t139-jev-v3-w30/game2048/jev/engine-game.stdout.txt` | 781 | `cd9f23fb6c574ca2b86de1dadf3d53d7009471df4819d32031bb90133af5c178` |
| `runs/model-player/t139-jev-v3-w30/game2048/jev/filmstrip.png` | 90747 | `a4e0c5d897fd5986d8478cf4199e4cba421179f344177cab1fbaf98668581185` |
| `runs/model-player/t139-jev-v3-w30/game2048/jev/frames.json` | 677444 | `d2d09fb47451571bab9f89c449a0c7a7c596c6b9fc3f25969ae1176d273101da` |
| `runs/model-player/t139-jev-v3-w30/game2048/jev/player.json` | 128943 | `99941f36511ce9b53760b033c26f9cad0c55a2fbc9d9a17dfb95689d7428962c` |
| `runs/model-player/t139-jev-v3-w30/game2048/jev/session.json` | 11007 | `c70359c2d418616b7d2806817b57ffb08f0e233d44bb2e5d180f0b92fdfdce3c` |
| `runs/model-player/t139-jev-v3-w30/game2048/jev/steps.jsonl` | 144038 | `b9b9885c51264614710915d827436954e766b4bc391066a1574ca8ccaa5b35c8` |
| `calls/**`（364 个文件，2695733 B）| — | `3e4271b7a445403925162feee3088bf5d5cbd2e4202946f7012b56bc29651878` |
| `frames/**`（37 个文件，481433 B）| — | `0d34fde7f6be1d95b80cb3ec858ddf5b081e4769e2057f81c317ee8981d6964f` |
| `states/**`（27 个文件，202809 B）| — | `1262c2e77944b7ef51e2594e729016adda49b62f0f50252e76c1fc942e51f0d6` |

## t139-jev-v3-w30 / lunarlander / jev

* 目录：`runs/model-player/t139-jev-v3-w30/lunarlander/jev`
* verdict：`INCONCLUSIVE`（counts_as_pass=False，strict=INCONCLUSIVE，baseline=INCONCLUSIVE，game_side=None）
* 注入/接受后变化/rate：0 / 0 / None
* 两窗对齐：1/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 4 frame(s))（matched 1/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game lunarlander --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9963 --window-frames 30 --out-prefix t139-jev-v3-w30`  <- t139_results_t139-jev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game lunarlander --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9964 --window-frames 90 --out-prefix t139-jev-v3-w90`  <- t139_results_t139-jev-v3-w90.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game lunarlander --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9961 --window-frames 30 --out-prefix t139-scripted-w30`  <- t139_results_t139-scripted-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game lunarlander --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9962 --window-frames 90 --out-prefix t139-scripted-w90`  <- t139_results_t139-scripted-w90.json (sweep driver)

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t139-jev-v3-w30/lunarlander/jev/demo.png` | 136641 | `5ccf7b0b66c36063e534b967624081e59e05be1c06c9b330a931367f934933a4` |
| `runs/model-player/t139-jev-v3-w30/lunarlander/jev/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t139-jev-v3-w30/lunarlander/jev/engine-game.stdout.txt` | 766 | `3312607c128b55d81e48de35cb6491eb2281335eb1fb46300b18f2485bc97a0d` |
| `runs/model-player/t139-jev-v3-w30/lunarlander/jev/filmstrip.png` | 105271 | `9f71305a54be9384364f5172fff5367e8b8a7dcdc44ddde4a34f1af4e9a8e6e6` |
| `runs/model-player/t139-jev-v3-w30/lunarlander/jev/frames.json` | 628511 | `a8737b29297b6856bed12761531d00327d05093fe227ebeb3eece90ba344ee66` |
| `runs/model-player/t139-jev-v3-w30/lunarlander/jev/player.json` | 267914 | `c3c3b6469cfc26fd0268007c0466810c5d3c1b90a5e0a92421aaa4c9fb48ebc3` |
| `runs/model-player/t139-jev-v3-w30/lunarlander/jev/session.json` | 11073 | `d9aee019261590944715ccca8177b7fa74d3f9f60784570e06794c3a1e63bf56` |
| `runs/model-player/t139-jev-v3-w30/lunarlander/jev/steps.jsonl` | 124538 | `c498a6781631ad1a989ca6c06f00cfec91216592e6d25017714e64e98c76e822` |
| `calls/**`（322 个文件，3456531 B）| — | `d80fb64966f521bdcc05ab92065b7bebb65b859bbc99dfcdbe9041f5d222b740` |
| `frames/**`（37 个文件，444999 B）| — | `c2b6a7e88951343c5ecf5a3abefcc13d1e97c7c75292a9b0a492cd61959fa1fa` |
| `states/**`（27 个文件，322124 B）| — | `08be6a76bded8bf52f8d04df525c0a953fa4597a3a347ec54b62439973f2f9a6` |

## t139-jev-v3-w30 / match3 / jev

* 目录：`runs/model-player/t139-jev-v3-w30/match3/jev`
* verdict：`INCONCLUSIVE`（counts_as_pass=False，strict=INCONCLUSIVE，baseline=INCONCLUSIVE，game_side=None）
* 注入/接受后变化/rate：12 / 1 / 1.0
* 两窗对齐：2/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 6 frame(s))（matched 2/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game match3 --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9963 --window-frames 30 --out-prefix t139-jev-v3-w30`  <- t139_results_t139-jev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game match3 --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9964 --window-frames 90 --out-prefix t139-jev-v3-w90`  <- t139_results_t139-jev-v3-w90.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game match3 --backend playjev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9965 --window-frames 30 --out-prefix t139-playjev-v3-w30`  <- t139_results_t139-playjev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game match3 --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9973 --window-frames 30 --out-prefix t139-scripted-w30`  <- t139_results_t139-scripted-w30-counterev.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game match3 --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9961 --window-frames 30 --out-prefix t139-scripted-w30`  <- t139_results_t139-scripted-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game match3 --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9962 --window-frames 90 --out-prefix t139-scripted-w90`  <- t139_results_t139-scripted-w90.json (sweep driver)

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t139-jev-v3-w30/match3/jev/demo.png` | 207087 | `e883b0e185866c2b4257264718b525f4e3f6e1f08e1a48072f08511324fe4978` |
| `runs/model-player/t139-jev-v3-w30/match3/jev/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t139-jev-v3-w30/match3/jev/engine-game.stdout.txt` | 769 | `b4d54cd4f304084748cde74ebe4df9104c05d87fc22c5be9b76be27a415fa3f6` |
| `runs/model-player/t139-jev-v3-w30/match3/jev/filmstrip.png` | 148869 | `ba6bcaa78d91fc4062cc957f089acd6e9945ca8f5dffbf3d459498dee0b0ec76` |
| `runs/model-player/t139-jev-v3-w30/match3/jev/frames.json` | 613554 | `070461f5eb7f09ba240d038de5a2f8b68f6c4e116f47a97b2e452db9624bc749` |
| `runs/model-player/t139-jev-v3-w30/match3/jev/player.json` | 281607 | `8cf891f810ff441d22704ddbeeb725c073bfdb97e1521f3cebabf9ad62e6fa4b` |
| `runs/model-player/t139-jev-v3-w30/match3/jev/session.json` | 12865 | `363c83116aa133631952bab180c8b0ed50fa487a785c9f1af7b8fe2d3cb5965a` |
| `runs/model-player/t139-jev-v3-w30/match3/jev/steps.jsonl` | 156878 | `25c886eaaf6d0352751a15553e26139e8913151b0cd1e269da40961eb384cc23` |
| `calls/**`（388 个文件，3732234 B）| — | `7627b68dbc74d8fd5548ef0e2667dc3e30dde9d4247eedcc9d62965b4ad8755b` |
| `frames/**`（37 个文件，433578 B）| — | `c99f300f5f3aae68fb94dbac7f81bc1df7a890aa81fb5a2a64a1c3df5f4ff4c5` |
| `states/**`（27 个文件，330857 B）| — | `31a488c661c2e02aa00f0a9d068d7fc982f20a00ce2fa69269c84559b50b719b` |

## t139-jev-v3-w30 / minesweeper / jev

* 目录：`runs/model-player/t139-jev-v3-w30/minesweeper/jev`
* verdict：`INCONCLUSIVE`（counts_as_pass=False，strict=INCONCLUSIVE，baseline=INCONCLUSIVE，game_side=None）
* 注入/接受后变化/rate：1 / 1 / 1.0
* 两窗对齐：3/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 5 frame(s))（matched 3/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game minesweeper --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9963 --window-frames 30 --out-prefix t139-jev-v3-w30`  <- t139_results_t139-jev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game minesweeper --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9964 --window-frames 90 --out-prefix t139-jev-v3-w90`  <- t139_results_t139-jev-v3-w90.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game minesweeper --backend playjev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9965 --window-frames 30 --out-prefix t139-playjev-v3-w30`  <- t139_results_t139-playjev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game minesweeper --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9973 --window-frames 30 --out-prefix t139-scripted-w30`  <- t139_results_t139-scripted-w30-counterev.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game minesweeper --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9961 --window-frames 30 --out-prefix t139-scripted-w30`  <- t139_results_t139-scripted-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game minesweeper --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9962 --window-frames 90 --out-prefix t139-scripted-w90`  <- t139_results_t139-scripted-w90.json (sweep driver)

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t139-jev-v3-w30/minesweeper/jev/demo.png` | 196661 | `5eca77136d51039c80b07468ca143e24a4fd31f92b6c805d2bd0d130c2a726f8` |
| `runs/model-player/t139-jev-v3-w30/minesweeper/jev/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t139-jev-v3-w30/minesweeper/jev/engine-game.stdout.txt` | 745 | `d9723e7cd8c7b0ec11ef59e5d27502ee6342c63c1954e9c1ac900adbec0a1be2` |
| `runs/model-player/t139-jev-v3-w30/minesweeper/jev/filmstrip.png` | 182681 | `3f6ebc402058886b640d9d6203be2fee0cd658ab5cf9777e3e3b5c581351abeb` |
| `runs/model-player/t139-jev-v3-w30/minesweeper/jev/frames.json` | 810011 | `f6168d25f4f5847036f983fb5d3ed211d3d59e570e9b035f6767230e06d65edb` |
| `runs/model-player/t139-jev-v3-w30/minesweeper/jev/player.json` | 49266 | `c269e30cd5d84f4a4e181d9d67b176f1ce8695432ce93e91e6dd0160d8b31d07` |
| `runs/model-player/t139-jev-v3-w30/minesweeper/jev/session.json` | 12987 | `e495bff68d3c584b3e956392bb9ade448ee377e0598356a651aab8c9e9020f4b` |
| `runs/model-player/t139-jev-v3-w30/minesweeper/jev/steps.jsonl` | 132998 | `14e331a3ef8c8451a46ae2c37c3e22b2e9a552674f29131833eba79b6bec0473` |
| `calls/**`（312 个文件，7335290 B）| — | `2fc44042c00ddb97048186f48914c288c57505752afe02e6a7a04aab0c6599c7` |
| `frames/**`（37 个文件，580787 B）| — | `0414180ef982e8b530b645478075127fd8cdcd1df68afbd6b3b75b8a083313ef` |
| `states/**`（27 个文件，787136 B）| — | `b3078382e764a142b08d8157507ae4cfec00e8401f5304fffd20b99a1e4abf25` |

## t139-jev-v3-w30 / missilecommand / jev

* 目录：`runs/model-player/t139-jev-v3-w30/missilecommand/jev`
* verdict：`INCONCLUSIVE`（counts_as_pass=False，strict=INCONCLUSIVE，baseline=INCONCLUSIVE，game_side=None）
* 注入/接受后变化/rate：1 / 1 / 1.0
* 两窗对齐：1/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 4 frame(s))（matched 1/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game missilecommand --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9963 --window-frames 30 --out-prefix t139-jev-v3-w30`  <- t139_results_t139-jev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game missilecommand --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9964 --window-frames 90 --out-prefix t139-jev-v3-w90`  <- t139_results_t139-jev-v3-w90.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game missilecommand --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9961 --window-frames 30 --out-prefix t139-scripted-w30`  <- t139_results_t139-scripted-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game missilecommand --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9962 --window-frames 90 --out-prefix t139-scripted-w90`  <- t139_results_t139-scripted-w90.json (sweep driver)

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t139-jev-v3-w30/missilecommand/jev/demo.png` | 142634 | `b1bb3b144d9f920bb8d5aaf348bcddfae90df1d2da0a5aff68e38ba9139796dd` |
| `runs/model-player/t139-jev-v3-w30/missilecommand/jev/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t139-jev-v3-w30/missilecommand/jev/engine-game.stdout.txt` | 742 | `58baf6cd9284c73472c9661417cc9e9402b0d1367283b5af966e73079deed15e` |
| `runs/model-player/t139-jev-v3-w30/missilecommand/jev/filmstrip.png` | 85572 | `89c7961b0365555f71517e04dad9f4d9c5cae78dcec08be462301001481deaa3` |
| `runs/model-player/t139-jev-v3-w30/missilecommand/jev/frames.json` | 728069 | `4a8685414ea01702b7881a5a080e59075ecb9acca90bcb0c65f1b1b5ea8dbd52` |
| `runs/model-player/t139-jev-v3-w30/missilecommand/jev/player.json` | 50331 | `7cb19779868d55523b6ed415c6f420adc875ac38dc53d511ae396651349de042` |
| `runs/model-player/t139-jev-v3-w30/missilecommand/jev/session.json` | 11363 | `5fe4b12f4ae50562f5b6907563877c43687b18c6fa0117e72eff8008fc9e67b7` |
| `runs/model-player/t139-jev-v3-w30/missilecommand/jev/steps.jsonl` | 131093 | `279c3702e0f29576f9d93ee9560a0e3b4bdc657398dc15a172e70819396dfb9d` |
| `calls/**`（332 个文件，6272452 B）| — | `5f1fb672fe9eb725f7e479c16d67b1c301d231633b2b46bdaefe38fc85c380ef` |
| `frames/**`（37 个文件，519327 B）| — | `de35adb70689525d693f9f31a32c64475b61451fb92eb513955b5aca1240b520` |
| `states/**`（27 个文件，627674 B）| — | `d0c9f4ad8381d8ae30fa08f8c6959f3d92f5199c9198ca2465678fbb036f2a1e` |

## t139-jev-v3-w30 / pacman / jev

* 目录：`runs/model-player/t139-jev-v3-w30/pacman/jev`
* verdict：`INCONCLUSIVE`（counts_as_pass=False，strict=INCONCLUSIVE，baseline=INCONCLUSIVE，game_side=None）
* 注入/接受后变化/rate：12 / 2 / 1.0
* 两窗对齐：1/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 5 frame(s))（matched 1/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game pacman --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9963 --window-frames 30 --out-prefix t139-jev-v3-w30`  <- t139_results_t139-jev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game pacman --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9964 --window-frames 90 --out-prefix t139-jev-v3-w90`  <- t139_results_t139-jev-v3-w90.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game pacman --backend playjev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9965 --window-frames 30 --out-prefix t139-playjev-v3-w30`  <- t139_results_t139-playjev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game pacman --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9973 --window-frames 30 --out-prefix t139-scripted-w30`  <- t139_results_t139-scripted-w30-counterev.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game pacman --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9961 --window-frames 30 --out-prefix t139-scripted-w30`  <- t139_results_t139-scripted-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game pacman --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9962 --window-frames 90 --out-prefix t139-scripted-w90`  <- t139_results_t139-scripted-w90.json (sweep driver)

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t139-jev-v3-w30/pacman/jev/demo.png` | 157544 | `0677cb7f83416c1defb92e421e7474f029b05993f9d3e2655ada28b728df024c` |
| `runs/model-player/t139-jev-v3-w30/pacman/jev/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t139-jev-v3-w30/pacman/jev/engine-game.stdout.txt` | 733 | `6dfb96306e4b56cc6d09c0df35ef9e061262939f389b0b1b14943d794cb47361` |
| `runs/model-player/t139-jev-v3-w30/pacman/jev/filmstrip.png` | 144849 | `63bda254e46c172b0f829e31929a30333f2171c7fcd139b5962cb019a95003bd` |
| `runs/model-player/t139-jev-v3-w30/pacman/jev/frames.json` | 569053 | `8f0085cb953d82f5d66df6a5fef347478b420213c0945e204c458c728e193669` |
| `runs/model-player/t139-jev-v3-w30/pacman/jev/player.json` | 259350 | `1216e3fb56163cfa795dd9f8b449736461b0d86a2b110fd84b215a2028e2bf9e` |
| `runs/model-player/t139-jev-v3-w30/pacman/jev/session.json` | 12434 | `fd37341ae2e948501d11185638a8460165c32542ede32bc1860cba0cc8bcee05` |
| `runs/model-player/t139-jev-v3-w30/pacman/jev/steps.jsonl` | 153215 | `192f662a16a86b93a62ae328d4f33fb5e33e5a0eaa5214cce67f270ca9158744` |
| `calls/**`（343 个文件，9411493 B）| — | `79308a2532bddd1dbaae71c7381efe452f82f3d777b707ce36d4a015ee3e39e7` |
| `frames/**`（37 个文件，400338 B）| — | `a4f66f8f1456035d8be4a28ee5dd740bd812ac03950aa2524def763760a271ec` |
| `states/**`（27 个文件，1154912 B）| — | `87cc72853c5e08a6a6f93ee17c9cd93545aff7c6cd722a5c161bba58c8d2260c` |

## t139-jev-v3-w30 / platformer / jev

* 目录：`runs/model-player/t139-jev-v3-w30/platformer/jev`
* verdict：`INCONCLUSIVE`（counts_as_pass=False，strict=INCONCLUSIVE，baseline=INCONCLUSIVE，game_side=None）
* 注入/接受后变化/rate：7 / 6 / 0.8571
* 两窗对齐：2/7 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 3 frame(s))（matched 2/7，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game platformer --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9963 --window-frames 30 --out-prefix t139-jev-v3-w30`  <- t139_results_t139-jev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game platformer --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9964 --window-frames 90 --out-prefix t139-jev-v3-w90`  <- t139_results_t139-jev-v3-w90.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game platformer --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9961 --window-frames 30 --out-prefix t139-scripted-w30`  <- t139_results_t139-scripted-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game platformer --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9962 --window-frames 90 --out-prefix t139-scripted-w90`  <- t139_results_t139-scripted-w90.json (sweep driver)

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t139-jev-v3-w30/platformer/jev/demo.png` | 101331 | `d84cc2ab37271140cabf60fcf725027909a31037b5137bd2dd7d88ac7302739d` |
| `runs/model-player/t139-jev-v3-w30/platformer/jev/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t139-jev-v3-w30/platformer/jev/engine-game.stdout.txt` | 796 | `31383d51dee50f5ad169dc56ee5a73a6b0db2f271015e14d684a4b49249b984d` |
| `runs/model-player/t139-jev-v3-w30/platformer/jev/filmstrip.png` | 65059 | `930f4fffa7b9f54891691f2084914c947ca8a830c445d5686a4d176fb4e1a4ba` |
| `runs/model-player/t139-jev-v3-w30/platformer/jev/frames.json` | 329072 | `de75dfb58bc47a468549d1f63949ed8c1ab691f377c971359d7e745567d5a057` |
| `runs/model-player/t139-jev-v3-w30/platformer/jev/player.json` | 150446 | `659febdecd6dccca27c807f57206a8115c634685b2459098fa704d1b73492f1c` |
| `runs/model-player/t139-jev-v3-w30/platformer/jev/session.json` | 11111 | `e5dd72b707cec0d93bff03d0a6cbbce0ce04eb83b4c515c87760c7b8cbc7ad90` |
| `runs/model-player/t139-jev-v3-w30/platformer/jev/steps.jsonl` | 92017 | `dc30f52b8f8d3ffc5fad081aa0ac67ff534d8c4b798e75cf0de614bcb4d0bcf1` |
| `calls/**`（215 个文件，3261580 B）| — | `415832e853b513fc8784bef5571ee530c7ef1dfc87a9585f1d72d60c8c83c053` |
| `frames/**`（22 个文件，231010 B）| — | `f20179be487624eaaa40401fd7eb5a6bc7e2e1758982a099ed7b63e883f0033d` |
| `states/**`（17 个文件，365456 B）| — | `3bb9bcedfbebc0b82c43a2341477f5d1701e51320215b5efc27dd52f8e6983de` |

## t139-jev-v3-w30 / pong / jev

* 目录：`runs/model-player/t139-jev-v3-w30/pong/jev`
* verdict：`FAIL`（counts_as_pass=False，strict=FAIL，baseline=FAIL，game_side=None）
* 注入/接受后变化/rate：12 / 8 / 0.6667
* 两窗对齐：6/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 4 frame(s))（matched 6/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game pong --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9963 --window-frames 30 --out-prefix t139-jev-v3-w30`  <- t139_results_t139-jev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game pong --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9964 --window-frames 90 --out-prefix t139-jev-v3-w90`  <- t139_results_t139-jev-v3-w90.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game pong --backend playjev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9965 --window-frames 30 --out-prefix t139-playjev-v3-w30`  <- t139_results_t139-playjev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game pong --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9961 --window-frames 30 --out-prefix t139-scripted-w30`  <- t139_results_t139-scripted-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game pong --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9962 --window-frames 90 --out-prefix t139-scripted-w90`  <- t139_results_t139-scripted-w90.json (sweep driver)

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t139-jev-v3-w30/pong/jev/demo.png` | 77387 | `0470abb515dda61989da36ca81c070d00a98c6fa77cbcae1e336db318f679436` |
| `runs/model-player/t139-jev-v3-w30/pong/jev/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t139-jev-v3-w30/pong/jev/engine-game.stdout.txt` | 3869 | `9a8daebe6cd0a8634b70c79754b20cea572a7b0583f2f10bf265ef3d722ed5c0` |
| `runs/model-player/t139-jev-v3-w30/pong/jev/filmstrip.png` | 50378 | `b8af1e3b20ae16215ae97a16c2d10cbb6d77ec0637e35bed955949d00a48d79a` |
| `runs/model-player/t139-jev-v3-w30/pong/jev/frames.json` | 267886 | `d7698da997680c0c6c529133c54a65acf164eecd56d323cab0019a0a65b73e5c` |
| `runs/model-player/t139-jev-v3-w30/pong/jev/player.json` | 160221 | `018b124ee4cf316837a35c2b5e2e37a36fbdf8cb66b147574ec678f49d24d3be` |
| `runs/model-player/t139-jev-v3-w30/pong/jev/session.json` | 11294 | `1d6462b672b7c318fba5a49cc0a5c7a796d9750b725dd05ad0b98a7be1f9fbaf` |
| `runs/model-player/t139-jev-v3-w30/pong/jev/steps.jsonl` | 154087 | `ce9ca3efeb1bab7d99504ca25f592ea598fc90c7989fd02ee016d57369745c78` |
| `calls/**`（365 个文件，934515 B）| — | `5c5ed8c752767e92af688ea4b8862ac1c3562395c60ec2d66773dcd19cc29495` |
| `frames/**`（37 个文件，174607 B）| — | `1c14ab840ef201fda00f7be2e20871c24ae709f09a0040a89f7c00b1f9ce04bb` |
| `states/**`（27 个文件，65848 B）| — | `19b7e990f394c747cebe74a363ab936d14aed4fb590617cdbb67379147070b80` |

## t139-jev-v3-w30 / puzzlebobble / jev

* 目录：`runs/model-player/t139-jev-v3-w30/puzzlebobble/jev`
* verdict：`INCONCLUSIVE`（counts_as_pass=False，strict=INCONCLUSIVE，baseline=INCONCLUSIVE，game_side=None）
* 注入/接受后变化/rate：2 / 2 / 1.0
* 两窗对齐：1/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 5 frame(s))（matched 1/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game puzzlebobble --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9963 --window-frames 30 --out-prefix t139-jev-v3-w30`  <- t139_results_t139-jev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game puzzlebobble --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9964 --window-frames 90 --out-prefix t139-jev-v3-w90`  <- t139_results_t139-jev-v3-w90.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game puzzlebobble --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9961 --window-frames 30 --out-prefix t139-scripted-w30`  <- t139_results_t139-scripted-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game puzzlebobble --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9962 --window-frames 90 --out-prefix t139-scripted-w90`  <- t139_results_t139-scripted-w90.json (sweep driver)

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t139-jev-v3-w30/puzzlebobble/jev/demo.png` | 182429 | `0ed82a9e1353758e9d4091894919459e17b198e46aad2904eee1d68d331fbd56` |
| `runs/model-player/t139-jev-v3-w30/puzzlebobble/jev/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t139-jev-v3-w30/puzzlebobble/jev/engine-game.stdout.txt` | 739 | `819ae430e6cb1b8d6a69293ae4541f0b2e4c42ba24aaa2dac236e2cf117f6b9f` |
| `runs/model-player/t139-jev-v3-w30/puzzlebobble/jev/filmstrip.png` | 126534 | `dae2333b047066d6db07031c028718328c4524278fc9329b658804480a2ffe75` |
| `runs/model-player/t139-jev-v3-w30/puzzlebobble/jev/frames.json` | 733277 | `da505e7919e32ff53424704b522bc586b92aed4e0fe43cfa865fa5e304ea607e` |
| `runs/model-player/t139-jev-v3-w30/puzzlebobble/jev/player.json` | 72139 | `8bfbb43e42417617c482883aad4cec9ab802c33bad8f0eae666cba1178d62330` |
| `runs/model-player/t139-jev-v3-w30/puzzlebobble/jev/session.json` | 11264 | `c8f157b3edae2e6c4e6aed5e300e06a99e9230cbbc80ae22062f7746ebfd3a3d` |
| `runs/model-player/t139-jev-v3-w30/puzzlebobble/jev/steps.jsonl` | 139360 | `773c9519121caeb7dd661b480dde14b5b0bb18d2337c39ba27c698caf81e45a3` |
| `calls/**`（321 个文件，5249781 B）| — | `822c9d38ab88b277d90ea8b98dfe2b99ad035bdcd4cf3681fdff3409e3443fec` |
| `frames/**`（37 个文件，523236 B）| — | `80d8b410fc36596f79e4e5bed76e2268f7a80f7af0e37b627c6610a9e2162a8b` |
| `states/**`（27 个文件，539265 B）| — | `0763f6811ee657d9d9790f1803dda99f215341362106d412b98044457d7fa2b7` |

## t139-jev-v3-w30 / rtype / jev

* 目录：`runs/model-player/t139-jev-v3-w30/rtype/jev`
* verdict：`INCONCLUSIVE`（counts_as_pass=False，strict=INCONCLUSIVE，baseline=INCONCLUSIVE，game_side=None）
* 注入/接受后变化/rate：0 / 0 / None
* 两窗对齐：5/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 4 frame(s))（matched 5/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game rtype --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9963 --window-frames 30 --out-prefix t139-jev-v3-w30`  <- t139_results_t139-jev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game rtype --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9964 --window-frames 90 --out-prefix t139-jev-v3-w90`  <- t139_results_t139-jev-v3-w90.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game rtype --backend playjev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9965 --window-frames 30 --out-prefix t139-playjev-v3-w30`  <- t139_results_t139-playjev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game rtype --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9961 --window-frames 30 --out-prefix t139-scripted-w30`  <- t139_results_t139-scripted-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game rtype --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9962 --window-frames 90 --out-prefix t139-scripted-w90`  <- t139_results_t139-scripted-w90.json (sweep driver)

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t139-jev-v3-w30/rtype/jev/demo.png` | 153493 | `9a5a613351dd968364f66c5c2abe33ce813267a46cfcfde65b1fd1461b674128` |
| `runs/model-player/t139-jev-v3-w30/rtype/jev/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t139-jev-v3-w30/rtype/jev/engine-game.stdout.txt` | 743 | `aa31290a9eb71b47dc6a531d3d143b37fa19326b06b1cbabb70aa5c20fdda4a5` |
| `runs/model-player/t139-jev-v3-w30/rtype/jev/filmstrip.png` | 104310 | `0915488e56c95af4c112604207526aa8c2ac1376efd28c0106c98c907b1f0587` |
| `runs/model-player/t139-jev-v3-w30/rtype/jev/frames.json` | 631838 | `310c0731cc02b969813748a3456cdd6c6f5fed4c400cdfa070f4946aa551b4ca` |
| `runs/model-player/t139-jev-v3-w30/rtype/jev/player.json` | 276048 | `89deeb21fec3f42c27fa527a163b6f05be3f37a0745a702fed3c8e5a06c6c836` |
| `runs/model-player/t139-jev-v3-w30/rtype/jev/session.json` | 11222 | `52967e8ce78d65ab8f0286d4b6b40ae2e9a6131520959242d4948abc626e996f` |
| `runs/model-player/t139-jev-v3-w30/rtype/jev/steps.jsonl` | 126140 | `49e04ff21f99e8aa05c9df6c3cf6a941df44128204edb02d0d1e8e8e472ede75` |
| `calls/**`（332 个文件，5122881 B）| — | `e8c33c9590a38d97b70e96bed7952bb07ac5a9047e522629fa3cd6b8a5a62165` |
| `frames/**`（37 个文件，447515 B）| — | `73af99ea39d4b6f662ba8818d8af005b8a8b289a7915a53f9a45502ab4506eb7` |
| `states/**`（27 个文件，499029 B）| — | `6c897b54b27d79fde16d4cba849235459c01e231454caa02d04fbdfe10e9b2fd` |

## t139-jev-v3-w30 / snake / jev

* 目录：`runs/model-player/t139-jev-v3-w30/snake/jev`
* verdict：`INCONCLUSIVE`（counts_as_pass=False，strict=INCONCLUSIVE，baseline=INCONCLUSIVE，game_side=None）
* 注入/接受后变化/rate：10 / 10 / 1.0
* 两窗对齐：1/10 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 4 frame(s))（matched 1/10，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game snake --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9963 --window-frames 30 --out-prefix t139-jev-v3-w30`  <- t139_results_t139-jev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game snake --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9964 --window-frames 90 --out-prefix t139-jev-v3-w90`  <- t139_results_t139-jev-v3-w90.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game snake --backend playjev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9965 --window-frames 30 --out-prefix t139-playjev-v3-w30`  <- t139_results_t139-playjev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game snake --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9961 --window-frames 30 --out-prefix t139-scripted-w30`  <- t139_results_t139-scripted-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game snake --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9962 --window-frames 90 --out-prefix t139-scripted-w90`  <- t139_results_t139-scripted-w90.json (sweep driver)

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t139-jev-v3-w30/snake/jev/demo.png` | 68061 | `4b28b901c7906ec67f67749071489abee84257dfd1657a6358c255ef5355cab4` |
| `runs/model-player/t139-jev-v3-w30/snake/jev/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t139-jev-v3-w30/snake/jev/engine-game.stdout.txt` | 4848 | `438b898dccc1ab40b8081c31527ef4b81c1643e841c7bf32f7d25eb42478ba2a` |
| `runs/model-player/t139-jev-v3-w30/snake/jev/filmstrip.png` | 39350 | `41c2cd88e488e6e81e11ef226c9196883ecb52486fe08e866a11fbef5355615a` |
| `runs/model-player/t139-jev-v3-w30/snake/jev/frames.json` | 156601 | `22a261d2c4647d20da2df6877aa007d89bb8748ce15681a96d6f089f395c90c0` |
| `runs/model-player/t139-jev-v3-w30/snake/jev/player.json` | 118885 | `71285b5161c7736082adc1caba95c46abd974ce8f94e880c58e23227c0daea8d` |
| `runs/model-player/t139-jev-v3-w30/snake/jev/session.json` | 11852 | `73c9200ff31ba6cf35f4decf3ef3f729fea2c910f08770a0aa578b3995195ba8` |
| `runs/model-player/t139-jev-v3-w30/snake/jev/steps.jsonl` | 137136 | `fc6d82bd4c9dbc127445bf847a58b5e8f638ad6d3cd225f9fb2a65a625657143` |
| `calls/**`（267 个文件，1641066 B）| — | `efec3fec72094e317d1308fb7c875c2c0b13746cb65e2a0030c841868d08a024` |
| `frames/**`（31 个文件，95526 B）| — | `8907d862b9c68f75bfb53c55e457b91f179242f950f4035b36c6fe0c82af771c` |
| `states/**`（23 个文件，201751 B）| — | `85fcf57e6c41a4107a13fa9ae89d9d63e09c6ea4089490e6a4a25a8a1cb5a11c` |

## t139-jev-v3-w30 / sokoban / jev

* 目录：`runs/model-player/t139-jev-v3-w30/sokoban/jev`
* verdict：`INCONCLUSIVE`（counts_as_pass=False，strict=INCONCLUSIVE，baseline=INCONCLUSIVE，game_side=None）
* 注入/接受后变化/rate：12 / 1 / 0.0833
* 两窗对齐：3/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 3 frame(s))（matched 3/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game sokoban --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9963 --window-frames 30 --out-prefix t139-jev-v3-w30`  <- t139_results_t139-jev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game sokoban --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9964 --window-frames 90 --out-prefix t139-jev-v3-w90`  <- t139_results_t139-jev-v3-w90.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game sokoban --backend playjev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9965 --window-frames 30 --out-prefix t139-playjev-v3-w30`  <- t139_results_t139-playjev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game sokoban --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9973 --window-frames 30 --out-prefix t139-scripted-w30`  <- t139_results_t139-scripted-w30-counterev.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game sokoban --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9961 --window-frames 30 --out-prefix t139-scripted-w30`  <- t139_results_t139-scripted-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game sokoban --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9962 --window-frames 90 --out-prefix t139-scripted-w90`  <- t139_results_t139-scripted-w90.json (sweep driver)

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t139-jev-v3-w30/sokoban/jev/demo.png` | 146601 | `8b52af723e34c9bad1129f8f98af1a1f5d096cb712f19ea301366dbf5e6e3111` |
| `runs/model-player/t139-jev-v3-w30/sokoban/jev/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t139-jev-v3-w30/sokoban/jev/engine-game.stdout.txt` | 745 | `d1a570401aafaacf008dda1e5bf81dfe6339f6db7fea17570be22121ced61853` |
| `runs/model-player/t139-jev-v3-w30/sokoban/jev/filmstrip.png` | 101789 | `c36aa1e17cee52f19dfcb7cb9aaf4bb2428f85f2ec6d32898a95290f67c394f5` |
| `runs/model-player/t139-jev-v3-w30/sokoban/jev/frames.json` | 586369 | `2db12cf7f7f4966c350690a018b34cce3a97df083bcebeae8931fe6daed46859` |
| `runs/model-player/t139-jev-v3-w30/sokoban/jev/player.json` | 261013 | `4cbfd82d5be08fb99545d6e8146ab57f09747aca49d36a09676a9aec2498daf0` |
| `runs/model-player/t139-jev-v3-w30/sokoban/jev/session.json` | 12579 | `ceda3fe3e1d7e005ac391ff3ca5e5a5bcd4511eabde4408391b737b9324eb947` |
| `runs/model-player/t139-jev-v3-w30/sokoban/jev/steps.jsonl` | 143107 | `683bfe4ce141ded15966fc458406ebe67b46188ac107e16b6d91e0c79c1c8633` |
| `calls/**`（392 个文件，4229758 B）| — | `39f270658c043f379152705668ea73461ad8190694175ee7242cb31d0a02912d` |
| `frames/**`（37 个文件，413183 B）| — | `238a77ae252054d2bb396613bd6df011eefdc470e1ab178e3753475fe6d2a439` |
| `states/**`（27 个文件，374547 B）| — | `691d9fcab420058ce6bddca6ecd5dc493ae0abf8c3e91f803994eb542d82ee4a` |

## t139-jev-v3-w30 / spaceinvaders / jev

* 目录：`runs/model-player/t139-jev-v3-w30/spaceinvaders/jev`
* verdict：`FAIL`（counts_as_pass=False，strict=FAIL，baseline=FAIL，game_side=None）
* 注入/接受后变化/rate：12 / 6 / 0.5
* 两窗对齐：7/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 3 frame(s))（matched 7/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game spaceinvaders --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9963 --window-frames 30 --out-prefix t139-jev-v3-w30`  <- t139_results_t139-jev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game spaceinvaders --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9964 --window-frames 90 --out-prefix t139-jev-v3-w90`  <- t139_results_t139-jev-v3-w90.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game spaceinvaders --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9961 --window-frames 30 --out-prefix t139-scripted-w30`  <- t139_results_t139-scripted-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game spaceinvaders --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9962 --window-frames 90 --out-prefix t139-scripted-w90`  <- t139_results_t139-scripted-w90.json (sweep driver)

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t139-jev-v3-w30/spaceinvaders/jev/demo.png` | 118272 | `5723dc1c84c62ab8e3710376addafb938867b1e129528e2c4ba636ba05b5abe4` |
| `runs/model-player/t139-jev-v3-w30/spaceinvaders/jev/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t139-jev-v3-w30/spaceinvaders/jev/engine-game.stdout.txt` | 754 | `0b6cc2b7e10e6961e2c40cd31a8a3d1827446abc6e149ee4486520f50b36e8b4` |
| `runs/model-player/t139-jev-v3-w30/spaceinvaders/jev/filmstrip.png` | 95208 | `9524783d30e031dcb77ae32a77bb9da009d245a63bfa4f8488f0179c5f0c9547` |
| `runs/model-player/t139-jev-v3-w30/spaceinvaders/jev/frames.json` | 517340 | `c4b09a703b1580cd577db782153bb10fcec99e6d84ae38835aff6d28bed55454` |
| `runs/model-player/t139-jev-v3-w30/spaceinvaders/jev/player.json` | 232801 | `44f04f8e86bacfbf8184a0ddb880c7424a06608a5e5a78556a2561b881fb6355` |
| `runs/model-player/t139-jev-v3-w30/spaceinvaders/jev/session.json` | 11167 | `3600e0950a326758753e1e3a2b99695eaaf11b19829d1817e522287152e6779c` |
| `runs/model-player/t139-jev-v3-w30/spaceinvaders/jev/steps.jsonl` | 160320 | `4fe1431965647ab4281f070829cbefcc606d5c9f02ffac3f35a5738de81849a2` |
| `calls/**`（388 个文件，2822281 B）| — | `c1195da5281c60bd80eac4f9e7a0cd7cf5c345ef91fa594acb1fcc02cac8ca87` |
| `frames/**`（37 个文件，361210 B）| — | `e53b831c6b9ceca193b20090a481a0a25025d715e52c982a00a051c019f3d927` |
| `states/**`（27 个文件，240120 B）| — | `0cba577fed0c1340c8acded6ddac7ce6c407ab7d8306c7b1f5cae38202dc025f` |

## t139-jev-v3-w30 / tetris / jev

* 目录：`runs/model-player/t139-jev-v3-w30/tetris/jev`
* verdict：`PASS`（counts_as_pass=True，strict=PASS，baseline=PASS，game_side=None）
* 注入/接受后变化/rate：8 / 8 / 1.0
* 两窗对齐：3/8 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 3 frame(s))（matched 3/8，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game tetris --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9963 --window-frames 30 --out-prefix t139-jev-v3-w30`  <- t139_results_t139-jev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game tetris --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9964 --window-frames 90 --out-prefix t139-jev-v3-w90`  <- t139_results_t139-jev-v3-w90.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game tetris --backend playjev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9965 --window-frames 30 --out-prefix t139-playjev-v3-w30`  <- t139_results_t139-playjev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game tetris --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9961 --window-frames 30 --out-prefix t139-scripted-w30`  <- t139_results_t139-scripted-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game tetris --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9962 --window-frames 90 --out-prefix t139-scripted-w90`  <- t139_results_t139-scripted-w90.json (sweep driver)

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t139-jev-v3-w30/tetris/jev/demo.png` | 74303 | `d3ce04a38368e33a6fb7647d514b5fe69e8cf8cd2623b33d271cf8b809ce57b0` |
| `runs/model-player/t139-jev-v3-w30/tetris/jev/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t139-jev-v3-w30/tetris/jev/engine-game.stdout.txt` | 6943 | `495a06582a22732354fb5b556ebfccd9cc98045f2822bd3cb8b3357ae3c5335b` |
| `runs/model-player/t139-jev-v3-w30/tetris/jev/filmstrip.png` | 43424 | `3066725330309646e4c60639fa87a0b2e4b5c9ccf66f1e0f99709a8017fe3b7b` |
| `runs/model-player/t139-jev-v3-w30/tetris/jev/frames.json` | 199634 | `d1f41a101ba42293a92b03679b537f7ca85ffbb070603fc39fa0ce619832475c` |
| `runs/model-player/t139-jev-v3-w30/tetris/jev/player.json` | 115978 | `f8aff3094ff8e539fd8fdec78868f91a8f1b2dcb28368306c19429233cb23148` |
| `runs/model-player/t139-jev-v3-w30/tetris/jev/session.json` | 11075 | `46e8a6dfd870a577f1a395f0c6d8de5197e59b0d6ae58e2d5405f1edfd144eec` |
| `runs/model-player/t139-jev-v3-w30/tetris/jev/steps.jsonl` | 98254 | `091e30130b113ccd0843ef5d20d879167dafe7ddae77d2a31e243310757692be` |
| `calls/**`（267 个文件，563097 B）| — | `fafb2dc5df50d2579a7937b88582fe7b01170f84bab0022b773a1603ea636b77` |
| `frames/**`（25 个文件，131740 B）| — | `9331e792a7476f2d6719a088c055f4b7cf5541c1e80b90a8c8516f62d26fa079` |
| `states/**`（19 个文件，30295 B）| — | `a8149a38ffcb899ee511c10f511badb320f20852399bda2657e86956692748c0` |

## t139-jev-v3-w30 / towerdefense / jev

* 目录：`runs/model-player/t139-jev-v3-w30/towerdefense/jev`
* verdict：`INCONCLUSIVE`（counts_as_pass=False，strict=INCONCLUSIVE，baseline=INCONCLUSIVE，game_side=None）
* 注入/接受后变化/rate：8 / 8 / 1.0
* 两窗对齐：2/8 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 4 frame(s))（matched 2/8，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game towerdefense --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9963 --window-frames 30 --out-prefix t139-jev-v3-w30`  <- t139_results_t139-jev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game towerdefense --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9964 --window-frames 90 --out-prefix t139-jev-v3-w90`  <- t139_results_t139-jev-v3-w90.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game towerdefense --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9973 --window-frames 30 --out-prefix t139-scripted-w30`  <- t139_results_t139-scripted-w30-counterev.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game towerdefense --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9961 --window-frames 30 --out-prefix t139-scripted-w30`  <- t139_results_t139-scripted-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game towerdefense --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9962 --window-frames 90 --out-prefix t139-scripted-w90`  <- t139_results_t139-scripted-w90.json (sweep driver)

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t139-jev-v3-w30/towerdefense/jev/demo.png` | 140492 | `0d40b174990e6ada45fa1a1a92e855a5d97a1f71b49853db67ee5480878b2f3b` |
| `runs/model-player/t139-jev-v3-w30/towerdefense/jev/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t139-jev-v3-w30/towerdefense/jev/engine-game.stdout.txt` | 753 | `44117b3c2a43c6927906ad31b08b28bf8a29dcc5f9566bca2497e23b628751c7` |
| `runs/model-player/t139-jev-v3-w30/towerdefense/jev/filmstrip.png` | 80198 | `33ff043a685003fcbd16351a3724e4323ef96e620ceaad88eacee6ce6e10fa06` |
| `runs/model-player/t139-jev-v3-w30/towerdefense/jev/frames.json` | 441936 | `bf70f2be181fb20b84ac4d106b31e53030c453c104fb4adfa4adb8d595b0da46` |
| `runs/model-player/t139-jev-v3-w30/towerdefense/jev/player.json` | 198227 | `912f3d735c8f21912b06be6dbf28b6d68a2d6fa59e1fa26499f6941683f697ea` |
| `runs/model-player/t139-jev-v3-w30/towerdefense/jev/session.json` | 12812 | `3c66df09cbbe2934ef7191dec159c782b4a3ce6ff6177201cf91267eaa7f7e9c` |
| `runs/model-player/t139-jev-v3-w30/towerdefense/jev/steps.jsonl` | 100176 | `abcbf197d5330ce8a68782e717811047593b9ad22b729a40412811d6c7d054cf` |
| `calls/**`（255 个文件，4309205 B）| — | `e3f87d7f557b9983dca2c089ec679b352cd178e9053dac1ecc40f522e2c07a06` |
| `frames/**`（25 个文件，313383 B）| — | `072b5ae8efbfa6bb3e384b3cc5886406465a0f70159a874f5e1af1586e67caf2` |
| `states/**`（19 个文件，451885 B）| — | `695b136d8c64efdece0fbcf8955354d1523665c00876b00c4af43da43c893021` |

## t139-jev-v3-w90 / asteroids / jev

* 目录：`runs/model-player/t139-jev-v3-w90/asteroids/jev`
* verdict：`FAIL`（counts_as_pass=False，strict=FAIL，baseline=FAIL，game_side=None）
* 注入/接受后变化/rate：12 / 3 / 0.25
* 两窗对齐：1/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 4 frame(s))（matched 1/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game asteroids --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9963 --window-frames 30 --out-prefix t139-jev-v3-w30`  <- t139_results_t139-jev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game asteroids --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9964 --window-frames 90 --out-prefix t139-jev-v3-w90`  <- t139_results_t139-jev-v3-w90.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game asteroids --backend playjev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9965 --window-frames 30 --out-prefix t139-playjev-v3-w30`  <- t139_results_t139-playjev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game asteroids --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9961 --window-frames 30 --out-prefix t139-scripted-w30`  <- t139_results_t139-scripted-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game asteroids --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9962 --window-frames 90 --out-prefix t139-scripted-w90`  <- t139_results_t139-scripted-w90.json (sweep driver)

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t139-jev-v3-w90/asteroids/jev/demo.png` | 118731 | `e376baba253ebe6125666645d31d998eee9e1272589a3397fce344bdcc556d37` |
| `runs/model-player/t139-jev-v3-w90/asteroids/jev/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t139-jev-v3-w90/asteroids/jev/engine-game.stdout.txt` | 741 | `6800c8c279af3464f751b84d089c85cc443c3e11fc38bd6df021295a3655458d` |
| `runs/model-player/t139-jev-v3-w90/asteroids/jev/filmstrip.png` | 70993 | `19b65829f0bc999aac0b31c4d0756d21e4996113f37212ce39aab8d0490ff5b4` |
| `runs/model-player/t139-jev-v3-w90/asteroids/jev/frames.json` | 539223 | `1b6e47c2447065239da7aeadd51c2a9a0c7dc472a6ff1bf7a19351f066032449` |
| `runs/model-player/t139-jev-v3-w90/asteroids/jev/player.json` | 245090 | `e6f4cc5104a13408b61152253b03b8cbc416672f101c20ec988673ceb2f5d0a7` |
| `runs/model-player/t139-jev-v3-w90/asteroids/jev/session.json` | 11153 | `60ed0212c279584bb45a639de56d3c08e1d4473877df004c0ac499ba5df5b310` |
| `runs/model-player/t139-jev-v3-w90/asteroids/jev/steps.jsonl` | 149947 | `6e5917cef901e1684964229064f7f870bab5138d95bd3185a890c72fe7c35eef` |
| `calls/**`（861 个文件，2742938 B）| — | `8246e4e77f2598243f21821ccde83b019d5d3e089193c8ba2b4ba0815614120b` |
| `frames/**`（37 个文件，377771 B）| — | `d6fa15f703c3d7ac56e5346b9ac5ed96c1db3cbacd3ee27c472cb1d9a3265cd9` |
| `states/**`（27 个文件，77192 B）| — | `c55b28db32f396a6fa20a890202278033aacc8c86b5a3a2a950f1bd9cfcaee1b` |

## t139-jev-v3-w90 / bomberman / jev

* 目录：`runs/model-player/t139-jev-v3-w90/bomberman/jev`
* verdict：`INCONCLUSIVE`（counts_as_pass=False，strict=INCONCLUSIVE，baseline=INCONCLUSIVE，game_side=None）
* 注入/接受后变化/rate：12 / 1 / 0.0833
* 两窗对齐：4/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 5 frame(s))（matched 4/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game bomberman --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9963 --window-frames 30 --out-prefix t139-jev-v3-w30`  <- t139_results_t139-jev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game bomberman --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9964 --window-frames 90 --out-prefix t139-jev-v3-w90`  <- t139_results_t139-jev-v3-w90.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game bomberman --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9961 --window-frames 30 --out-prefix t139-scripted-w30`  <- t139_results_t139-scripted-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game bomberman --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9962 --window-frames 90 --out-prefix t139-scripted-w90`  <- t139_results_t139-scripted-w90.json (sweep driver)

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t139-jev-v3-w90/bomberman/jev/demo.png` | 165491 | `c155730e33668eb7d0da39051a933e131f2f25c163ae5b592d0259992c95f01e` |
| `runs/model-player/t139-jev-v3-w90/bomberman/jev/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t139-jev-v3-w90/bomberman/jev/engine-game.stdout.txt` | 775 | `0fec1f742d756e43cc4c2a7bc78a5a311efeaaa57e789f2b9ff0bdf4561decf0` |
| `runs/model-player/t139-jev-v3-w90/bomberman/jev/filmstrip.png` | 142395 | `265a175470b72a7d914e3cf5182588cef2ff1ae9cf8e33b384669d3cbeb06324` |
| `runs/model-player/t139-jev-v3-w90/bomberman/jev/frames.json` | 511010 | `bbcb4565fdae22e549b81f3b44af390c69575bfe939faffd4138ef0704f3b43c` |
| `runs/model-player/t139-jev-v3-w90/bomberman/jev/player.json` | 240859 | `d0aa63a376faf15a771d6cd61e6e11cd172a4698f847632e14e9ef54517e00d8` |
| `runs/model-player/t139-jev-v3-w90/bomberman/jev/session.json` | 11261 | `e82a1b57a22f5d7d8be9bd6d767b6069cabfa5099929cb6c2c83a1dbbe549e02` |
| `runs/model-player/t139-jev-v3-w90/bomberman/jev/steps.jsonl` | 144762 | `6eb27ab1dc690ff070ea2a3e1701b8f453d1cf4e4824aed9c8401500ce2a11fd` |
| `calls/**`（754 个文件，13373798 B）| — | `f59bee0e998933d9a6b55836dfde283c279bbdde39b06675fa6afa4607f63dc2` |
| `frames/**`（37 个文件，356515 B）| — | `f4ce0e6b7bfe0899d4ce35e38ca602b100de329238f2a24ced514e0bde3eed99` |
| `states/**`（27 个文件，600143 B）| — | `2e03dec0512b548e6a0725e51fa8c16e7424572dd80ba10cf1ffa9beb5d537ca` |

## t139-jev-v3-w90 / breakout / jev

* 目录：`runs/model-player/t139-jev-v3-w90/breakout/jev`
* verdict：`FAIL`（counts_as_pass=False，strict=FAIL，baseline=FAIL，game_side=None）
* 注入/接受后变化/rate：12 / 3 / 0.25
* 两窗对齐：0/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 5 frame(s))（matched 0/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game breakout --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9963 --window-frames 30 --out-prefix t139-jev-v3-w30`  <- t139_results_t139-jev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game breakout --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9964 --window-frames 90 --out-prefix t139-jev-v3-w90`  <- t139_results_t139-jev-v3-w90.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game breakout --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9961 --window-frames 30 --out-prefix t139-scripted-w30`  <- t139_results_t139-scripted-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game breakout --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9962 --window-frames 90 --out-prefix t139-scripted-w90`  <- t139_results_t139-scripted-w90.json (sweep driver)

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t139-jev-v3-w90/breakout/jev/demo.png` | 96668 | `aec1f57ee0b0a04a5764381869b24fd8aa13270a9aa6557d711d6be1ffbc8597` |
| `runs/model-player/t139-jev-v3-w90/breakout/jev/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t139-jev-v3-w90/breakout/jev/engine-game.stdout.txt` | 32143 | `79c6dc34688696085f7864d4ae120cd21fe653d939de0447df8ed919dcdd339f` |
| `runs/model-player/t139-jev-v3-w90/breakout/jev/filmstrip.png` | 65977 | `c4bed063972f687f86c2d21022464cf7dd1644b6f6137e66c981dd76b2466435` |
| `runs/model-player/t139-jev-v3-w90/breakout/jev/frames.json` | 341550 | `df517569f22ee0d3a899781d68fb4b12f1f0c119e435c0d7780c8c51f34841fa` |
| `runs/model-player/t139-jev-v3-w90/breakout/jev/player.json` | 181925 | `20a225fc30d972166f325147c1441d0115e6e81bc2ed939568edfb2493f78242` |
| `runs/model-player/t139-jev-v3-w90/breakout/jev/session.json` | 11313 | `51bc0aa69760f2dc40cfbdf4197063345122281209919397cf72d809c40ff286` |
| `runs/model-player/t139-jev-v3-w90/breakout/jev/steps.jsonl` | 160578 | `56043ee3c713fe82ae05add71e6f038a6b576ae4861cbc11a56a9c06075dd3a3` |
| `calls/**`（573 个文件，2850625 B）| — | `067337076dcefd2060b4272c2a570a8df7e9a38ec7956d16568493494fe68e08` |
| `frames/**`（37 个文件，229555 B）| — | `4979cba63190821784b5036231d1c1838583b140b20667ad4529b98ac45d6369` |
| `states/**`（27 个文件，147355 B）| — | `58b6e8aedba04961c4b2365751a72e32e001437b0b2296acf4127210f73ebbe7` |

## t139-jev-v3-w90 / flappy / jev

* 目录：`runs/model-player/t139-jev-v3-w90/flappy/jev`
* verdict：`INCONCLUSIVE`（counts_as_pass=False，strict=INCONCLUSIVE，baseline=INCONCLUSIVE，game_side=None）
* 注入/接受后变化/rate：12 / 1 / 0.0833
* 两窗对齐：2/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 4 frame(s))（matched 2/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game flappy --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9963 --window-frames 30 --out-prefix t139-jev-v3-w30`  <- t139_results_t139-jev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game flappy --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9964 --window-frames 90 --out-prefix t139-jev-v3-w90`  <- t139_results_t139-jev-v3-w90.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game flappy --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9961 --window-frames 30 --out-prefix t139-scripted-w30`  <- t139_results_t139-scripted-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game flappy --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9962 --window-frames 90 --out-prefix t139-scripted-w90`  <- t139_results_t139-scripted-w90.json (sweep driver)

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t139-jev-v3-w90/flappy/jev/demo.png` | 107223 | `461d17392fc81adb01d73caa13c323fa2cf6dbb1e576fb512350fc300fa107c9` |
| `runs/model-player/t139-jev-v3-w90/flappy/jev/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t139-jev-v3-w90/flappy/jev/engine-game.stdout.txt` | 744 | `df3f6e8d01a706fb6ce9e5b06a1b33924aef01e88386d8c68d56ad4c6af02d3c` |
| `runs/model-player/t139-jev-v3-w90/flappy/jev/filmstrip.png` | 62659 | `1b55d1cab92b55345f4c37abc96b407f296f51d0ebb934772085f18ffb681373` |
| `runs/model-player/t139-jev-v3-w90/flappy/jev/frames.json` | 474088 | `3e816a35dad79a43644db5992e5bb69f3d02a146741c1daeecacd99836519236` |
| `runs/model-player/t139-jev-v3-w90/flappy/jev/player.json` | 215622 | `c81c1e2467890ebda575c7f0e675f313bbd3582bdc11695f8800c232cb3433cc` |
| `runs/model-player/t139-jev-v3-w90/flappy/jev/session.json` | 11107 | `e07325e1c35ec9d8c97bc96db89dd090975a7237cf39282cec2293e2216dec66` |
| `runs/model-player/t139-jev-v3-w90/flappy/jev/steps.jsonl` | 135417 | `2a8262ab264c016e0635f4763177a82b4b23e7e2c9f152ac803f27b7774da45e` |
| `calls/**`（886 个文件，2734418 B）| — | `398afc72f40c89d1f2848892725a053a344929104468110c272b9afb39f74034` |
| `frames/**`（37 个文件，329115 B）| — | `b39f72c89eac8d1eaab83be410226afb680fe5f839b06f794962cc1b8f472b4a` |
| `states/**`（27 个文件，77158 B）| — | `7cdab5939989a13ea08e4af4028ce31db042774114a6040bbf1d895fc5aa0777` |

## t139-jev-v3-w90 / frogger / jev

* 目录：`runs/model-player/t139-jev-v3-w90/frogger/jev`
* verdict：`INCONCLUSIVE`（counts_as_pass=False，strict=INCONCLUSIVE，baseline=INCONCLUSIVE，game_side=None）
* 注入/接受后变化/rate：1 / 1 / 1.0
* 两窗对齐：0/1 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 3 frame(s))（matched 0/1，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game frogger --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9963 --window-frames 30 --out-prefix t139-jev-v3-w30`  <- t139_results_t139-jev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game frogger --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9964 --window-frames 90 --out-prefix t139-jev-v3-w90`  <- t139_results_t139-jev-v3-w90.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game frogger --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9961 --window-frames 30 --out-prefix t139-scripted-w30`  <- t139_results_t139-scripted-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game frogger --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9962 --window-frames 90 --out-prefix t139-scripted-w90`  <- t139_results_t139-scripted-w90.json (sweep driver)

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t139-jev-v3-w90/frogger/jev/demo.png` | 16460 | `6558956f37a432ca70c368ec0db1c72a953a65cabff23e91448506cfc9a77a0e` |
| `runs/model-player/t139-jev-v3-w90/frogger/jev/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t139-jev-v3-w90/frogger/jev/engine-game.stdout.txt` | 748 | `bca787a38c8fd8a8f1a4d5527e8e285f69de6ca55722e1ffd28f5be57166252e` |
| `runs/model-player/t139-jev-v3-w90/frogger/jev/filmstrip.png` | 13787 | `dc32caa8a5872a2849b207f90bbdc6c64605513c046e8762f1f28bc07a23f70e` |
| `runs/model-player/t139-jev-v3-w90/frogger/jev/frames.json` | 63824 | `169a59c77b9c82eb1f0a7db5f32701fe2d3560fd58786750a3366e1dc1ac1c92` |
| `runs/model-player/t139-jev-v3-w90/frogger/jev/player.json` | 38096 | `fdf617ffebbf2f366e223bbbcd92253a957d8bfa69f65fd75af436662f3fb4e5` |
| `runs/model-player/t139-jev-v3-w90/frogger/jev/session.json` | 11056 | `4bcf3e88f93ee1f0306235bf6d274aacbc182f044707d5d981548be0499eace3` |
| `runs/model-player/t139-jev-v3-w90/frogger/jev/steps.jsonl` | 11708 | `2554ca331afc48aba6f5551713b0a8f11d7a65132f4516b561f495874a5acb45` |
| `calls/**`（76 个文件，359181 B）| — | `a51f5be16cd8754299b6637a0279ed83553bbc86daef8cbecfe038f9abb13940` |
| `frames/**`（4 个文件，45009 B）| — | `d3f0695027bc9907d51e432528eef9a2612aa78601b13d78024d87403210119a` |
| `states/**`（5 个文件，21035 B）| — | `6a1e096c197985eab69fcc7429b93801f0ffb280771f7e5b259a475449f9d4f2` |

## t139-jev-v3-w90 / game2048 / jev

* 目录：`runs/model-player/t139-jev-v3-w90/game2048/jev`
* verdict：`INCONCLUSIVE`（counts_as_pass=False，strict=INCONCLUSIVE，baseline=INCONCLUSIVE，game_side=None）
* 注入/接受后变化/rate：5 / 5 / 1.0
* 两窗对齐：6/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 4 frame(s))（matched 6/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game game2048 --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9963 --window-frames 30 --out-prefix t139-jev-v3-w30`  <- t139_results_t139-jev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game game2048 --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9964 --window-frames 90 --out-prefix t139-jev-v3-w90`  <- t139_results_t139-jev-v3-w90.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game game2048 --backend playjev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9965 --window-frames 30 --out-prefix t139-playjev-v3-w30`  <- t139_results_t139-playjev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game game2048 --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9961 --window-frames 30 --out-prefix t139-scripted-w30`  <- t139_results_t139-scripted-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game game2048 --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9962 --window-frames 90 --out-prefix t139-scripted-w90`  <- t139_results_t139-scripted-w90.json (sweep driver)

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t139-jev-v3-w90/game2048/jev/demo.png` | 140690 | `2fc42369c712da6d13bc81e8d1a77405476301f6b9f07f12af303dbc947b7ee6` |
| `runs/model-player/t139-jev-v3-w90/game2048/jev/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t139-jev-v3-w90/game2048/jev/engine-game.stdout.txt` | 781 | `91ccd0c8eadcf12e36676a6139584bd4baee68353ae168506e56d46eeb0cdfa5` |
| `runs/model-player/t139-jev-v3-w90/game2048/jev/filmstrip.png` | 90747 | `a4e0c5d897fd5986d8478cf4199e4cba421179f344177cab1fbaf98668581185` |
| `runs/model-player/t139-jev-v3-w90/game2048/jev/frames.json` | 677452 | `d033de5b42d7d674fc2ed22b3de1b343c99bdef420df29f4b846207310444e49` |
| `runs/model-player/t139-jev-v3-w90/game2048/jev/player.json` | 128944 | `cccd1a0f176876f3e5bc693f3fa28e46dc67710b850ece774b5c79d6447c0751` |
| `runs/model-player/t139-jev-v3-w90/game2048/jev/session.json` | 11011 | `9c3277082cc1326c1ed7e6e848e281c0081da60689b61e11ad371fca0c8ab2a0` |
| `runs/model-player/t139-jev-v3-w90/game2048/jev/steps.jsonl` | 144082 | `cdd00003c2f9e2e08e8aff04483f45e0f502432474504b0e7b2211c41ec3706b` |
| `calls/**`（830 个文件，6010896 B）| — | `75cd15923959ee9a45e65c48a3d6310ff417a0164893c66fad1381fbbd8b2bad` |
| `frames/**`（37 个文件，481433 B）| — | `a4670225c5a135d8e01d579cdab9d0b344baff2235ffab349f00d3d0a29d5cc5` |
| `states/**`（27 个文件，202828 B）| — | `1edcd23b35c396f0cb202ae949b3e3d1ccb981b32a39b37d6077e6ee3437fc78` |

## t139-jev-v3-w90 / lunarlander / jev

* 目录：`runs/model-player/t139-jev-v3-w90/lunarlander/jev`
* verdict：`INCONCLUSIVE`（counts_as_pass=False，strict=INCONCLUSIVE，baseline=INCONCLUSIVE，game_side=None）
* 注入/接受后变化/rate：0 / 0 / None
* 两窗对齐：3/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 5 frame(s))（matched 3/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game lunarlander --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9963 --window-frames 30 --out-prefix t139-jev-v3-w30`  <- t139_results_t139-jev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game lunarlander --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9964 --window-frames 90 --out-prefix t139-jev-v3-w90`  <- t139_results_t139-jev-v3-w90.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game lunarlander --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9961 --window-frames 30 --out-prefix t139-scripted-w30`  <- t139_results_t139-scripted-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game lunarlander --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9962 --window-frames 90 --out-prefix t139-scripted-w90`  <- t139_results_t139-scripted-w90.json (sweep driver)

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t139-jev-v3-w90/lunarlander/jev/demo.png` | 136641 | `5ccf7b0b66c36063e534b967624081e59e05be1c06c9b330a931367f934933a4` |
| `runs/model-player/t139-jev-v3-w90/lunarlander/jev/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t139-jev-v3-w90/lunarlander/jev/engine-game.stdout.txt` | 766 | `17369d19107ed635bc9ac29aff4f7261b801b774912aa5f321e5db0d9069a336` |
| `runs/model-player/t139-jev-v3-w90/lunarlander/jev/filmstrip.png` | 105271 | `9f71305a54be9384364f5172fff5367e8b8a7dcdc44ddde4a34f1af4e9a8e6e6` |
| `runs/model-player/t139-jev-v3-w90/lunarlander/jev/frames.json` | 628525 | `888bb95c675e04273f8ae3edbf00c63b038996365cc6bc119e89d86b43c138be` |
| `runs/model-player/t139-jev-v3-w90/lunarlander/jev/player.json` | 267920 | `86824262c1fc2ff05a053ebd40851cd6735e47981458afd99cb045a4ede58c6f` |
| `runs/model-player/t139-jev-v3-w90/lunarlander/jev/session.json` | 11075 | `bd2aa8f2df4e3fe9c945fd1d2017f61979f50db1e4e671ac977462a08b43cd95` |
| `runs/model-player/t139-jev-v3-w90/lunarlander/jev/steps.jsonl` | 124581 | `f01b4b7bb6ea079f0af406fc3eb7bdce2199848b255c9a6498d718bf54097ed5` |
| `calls/**`（766 个文件，8282457 B）| — | `dadc7f39f1d0d0e8ee43bd2a9a2252eb80520f14ac4d58c294070055d8342cb2` |
| `frames/**`（37 个文件，444999 B）| — | `13caf5cb2f0f7340a5a1685fcd628e94324a9ff0e047a47e2943f109d988f7c8` |
| `states/**`（27 个文件，322143 B）| — | `47c4fa9308b17b05b7b93942a893a174cf6bab37821741132a78ca9d6408401f` |

## t139-jev-v3-w90 / match3 / jev

* 目录：`runs/model-player/t139-jev-v3-w90/match3/jev`
* verdict：`INCONCLUSIVE`（counts_as_pass=False，strict=INCONCLUSIVE，baseline=INCONCLUSIVE，game_side=None）
* 注入/接受后变化/rate：12 / 1 / 1.0
* 两窗对齐：4/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 3 frame(s))（matched 4/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game match3 --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9963 --window-frames 30 --out-prefix t139-jev-v3-w30`  <- t139_results_t139-jev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game match3 --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9964 --window-frames 90 --out-prefix t139-jev-v3-w90`  <- t139_results_t139-jev-v3-w90.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game match3 --backend playjev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9965 --window-frames 30 --out-prefix t139-playjev-v3-w30`  <- t139_results_t139-playjev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game match3 --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9973 --window-frames 30 --out-prefix t139-scripted-w30`  <- t139_results_t139-scripted-w30-counterev.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game match3 --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9961 --window-frames 30 --out-prefix t139-scripted-w30`  <- t139_results_t139-scripted-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game match3 --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9962 --window-frames 90 --out-prefix t139-scripted-w90`  <- t139_results_t139-scripted-w90.json (sweep driver)

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t139-jev-v3-w90/match3/jev/demo.png` | 207087 | `e883b0e185866c2b4257264718b525f4e3f6e1f08e1a48072f08511324fe4978` |
| `runs/model-player/t139-jev-v3-w90/match3/jev/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t139-jev-v3-w90/match3/jev/engine-game.stdout.txt` | 769 | `aa39bee4281871c58c4da7de16e2d539a1261d4f1d2f18f32b5362b22388129e` |
| `runs/model-player/t139-jev-v3-w90/match3/jev/filmstrip.png` | 148869 | `ba6bcaa78d91fc4062cc957f089acd6e9945ca8f5dffbf3d459498dee0b0ec76` |
| `runs/model-player/t139-jev-v3-w90/match3/jev/frames.json` | 613553 | `1f9b0354ee1bbdcf1fb7b6b55edf9d432bf980dd835ab8d8523483285d2784fe` |
| `runs/model-player/t139-jev-v3-w90/match3/jev/player.json` | 283528 | `248ba0016c7c9e16bf992d8fb23395fec464b9ba7f5ab5aacd057b0826f03219` |
| `runs/model-player/t139-jev-v3-w90/match3/jev/session.json` | 12869 | `3e4fc98db54623338994048ee9eb4ee3a6c10aed146e2dabb30deee95282295c` |
| `runs/model-player/t139-jev-v3-w90/match3/jev/steps.jsonl` | 158507 | `46fce5b25f34a81760c40ee5472ec7e9d398835dc75ecb17de8355b33173aa5a` |
| `calls/**`（779 个文件，8094246 B）| — | `4904ecafe2d1a8b2f37290baefced3bbb0aad87fefd42f1b35fcd8a876bc426f` |
| `frames/**`（37 个文件，433578 B）| — | `737416028e1dc8d298a4a3c189608692d2ccbc8485dfb4d7be4985e3e99ef8a1` |
| `states/**`（27 个文件，330874 B）| — | `e5df78a738ac4f9cd278c17a1a333e9779e82df96dca4dc9420ae8a339a30361` |

## t139-jev-v3-w90 / minesweeper / jev

* 目录：`runs/model-player/t139-jev-v3-w90/minesweeper/jev`
* verdict：`INCONCLUSIVE`（counts_as_pass=False，strict=INCONCLUSIVE，baseline=INCONCLUSIVE，game_side=None）
* 注入/接受后变化/rate：1 / 1 / 1.0
* 两窗对齐：5/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 4 frame(s))（matched 5/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game minesweeper --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9963 --window-frames 30 --out-prefix t139-jev-v3-w30`  <- t139_results_t139-jev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game minesweeper --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9964 --window-frames 90 --out-prefix t139-jev-v3-w90`  <- t139_results_t139-jev-v3-w90.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game minesweeper --backend playjev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9965 --window-frames 30 --out-prefix t139-playjev-v3-w30`  <- t139_results_t139-playjev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game minesweeper --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9973 --window-frames 30 --out-prefix t139-scripted-w30`  <- t139_results_t139-scripted-w30-counterev.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game minesweeper --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9961 --window-frames 30 --out-prefix t139-scripted-w30`  <- t139_results_t139-scripted-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game minesweeper --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9962 --window-frames 90 --out-prefix t139-scripted-w90`  <- t139_results_t139-scripted-w90.json (sweep driver)

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t139-jev-v3-w90/minesweeper/jev/demo.png` | 196661 | `5eca77136d51039c80b07468ca143e24a4fd31f92b6c805d2bd0d130c2a726f8` |
| `runs/model-player/t139-jev-v3-w90/minesweeper/jev/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t139-jev-v3-w90/minesweeper/jev/engine-game.stdout.txt` | 745 | `2d588d1a2b121f014f37d8e6d66a9c34748e2e318c8b8189b55b24fd0346cf0f` |
| `runs/model-player/t139-jev-v3-w90/minesweeper/jev/filmstrip.png` | 182681 | `3f6ebc402058886b640d9d6203be2fee0cd658ab5cf9777e3e3b5c581351abeb` |
| `runs/model-player/t139-jev-v3-w90/minesweeper/jev/frames.json` | 810024 | `b4183858d67ce0652fa23c2937185ddbbaeab08d17b9b1b4199386d03463b716` |
| `runs/model-player/t139-jev-v3-w90/minesweeper/jev/player.json` | 49263 | `bbe634abefb71a22b39c2488dc28898afc2e0547ccd1daf15d37eb9cd1a28c41` |
| `runs/model-player/t139-jev-v3-w90/minesweeper/jev/session.json` | 12985 | `93b60d0843fde93c722388ed950da5f2beb039ad05faa50b8e6e8ccee78029bd` |
| `runs/model-player/t139-jev-v3-w90/minesweeper/jev/steps.jsonl` | 133036 | `2d6d52fdce1ec30f2a8adc9a10f80698723ca0ae6012818d80b6c9a32564c167` |
| `calls/**`（666 个文件，16743750 B）| — | `b1228ec9d56911bd29152795a603b140ed9a128024222c1d3bf0d02049956a45` |
| `frames/**`（37 个文件，580787 B）| — | `1034b09eecf4aa4830a1af841708f3f7a1af44deb3c6a815d09f261825751bc0` |
| `states/**`（27 个文件，787157 B）| — | `f6882e57fa94417b42e9a2ed688f848d2f0b6feaf2aa92704ea1e360c24af048` |

## t139-jev-v3-w90 / missilecommand / jev

* 目录：`runs/model-player/t139-jev-v3-w90/missilecommand/jev`
* verdict：`INCONCLUSIVE`（counts_as_pass=False，strict=INCONCLUSIVE，baseline=INCONCLUSIVE，game_side=None）
* 注入/接受后变化/rate：1 / 1 / 1.0
* 两窗对齐：3/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 5 frame(s))（matched 3/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game missilecommand --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9963 --window-frames 30 --out-prefix t139-jev-v3-w30`  <- t139_results_t139-jev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game missilecommand --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9964 --window-frames 90 --out-prefix t139-jev-v3-w90`  <- t139_results_t139-jev-v3-w90.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game missilecommand --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9961 --window-frames 30 --out-prefix t139-scripted-w30`  <- t139_results_t139-scripted-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game missilecommand --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9962 --window-frames 90 --out-prefix t139-scripted-w90`  <- t139_results_t139-scripted-w90.json (sweep driver)

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t139-jev-v3-w90/missilecommand/jev/demo.png` | 142634 | `b1bb3b144d9f920bb8d5aaf348bcddfae90df1d2da0a5aff68e38ba9139796dd` |
| `runs/model-player/t139-jev-v3-w90/missilecommand/jev/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t139-jev-v3-w90/missilecommand/jev/engine-game.stdout.txt` | 742 | `637038658d6361c3a0597921a7f961006f265f37c99a60dcf1ac3aac0504df06` |
| `runs/model-player/t139-jev-v3-w90/missilecommand/jev/filmstrip.png` | 85572 | `89c7961b0365555f71517e04dad9f4d9c5cae78dcec08be462301001481deaa3` |
| `runs/model-player/t139-jev-v3-w90/missilecommand/jev/frames.json` | 728075 | `eb8b8240278e68779209e7f86273dc7b6d36146c93bf39c99444d4a67d1c11c6` |
| `runs/model-player/t139-jev-v3-w90/missilecommand/jev/player.json` | 50336 | `13ad827a407992eb50a59d9aab38dddd2b6130840eac932c45261427742ecec7` |
| `runs/model-player/t139-jev-v3-w90/missilecommand/jev/session.json` | 11364 | `5eb31f902aeeca632603fda38627c3d2f6e0ec55aa2c40cc5b70ac4cccb08004` |
| `runs/model-player/t139-jev-v3-w90/missilecommand/jev/steps.jsonl` | 131143 | `cc9d7b8cc4783ee0c382aef11c95ac3df7a4f5d0138ed3a93bc4606efc2aa7d0` |
| `calls/**`（719 个文件，14349677 B）| — | `40d32987acc6731d7075ba9899ed968aba0f76ac4bbfe06ee25886ec05df85f9` |
| `frames/**`（37 个文件，519327 B）| — | `addcb577f8e751ae4afb05558332ed61b9fdcef15cb8aacc061f2b97c8c18d2a` |
| `states/**`（27 个文件，627696 B）| — | `3fa24f825992c6bf10fc9097ad956cb8e0bbe1d1daed8bc59d41c4694d5fb336` |

## t139-jev-v3-w90 / pacman / jev

* 目录：`runs/model-player/t139-jev-v3-w90/pacman/jev`
* verdict：`INCONCLUSIVE`（counts_as_pass=False，strict=INCONCLUSIVE，baseline=INCONCLUSIVE，game_side=None）
* 注入/接受后变化/rate：12 / 2 / 1.0
* 两窗对齐：3/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 4 frame(s))（matched 3/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game pacman --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9963 --window-frames 30 --out-prefix t139-jev-v3-w30`  <- t139_results_t139-jev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game pacman --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9964 --window-frames 90 --out-prefix t139-jev-v3-w90`  <- t139_results_t139-jev-v3-w90.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game pacman --backend playjev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9965 --window-frames 30 --out-prefix t139-playjev-v3-w30`  <- t139_results_t139-playjev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game pacman --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9973 --window-frames 30 --out-prefix t139-scripted-w30`  <- t139_results_t139-scripted-w30-counterev.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game pacman --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9961 --window-frames 30 --out-prefix t139-scripted-w30`  <- t139_results_t139-scripted-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game pacman --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9962 --window-frames 90 --out-prefix t139-scripted-w90`  <- t139_results_t139-scripted-w90.json (sweep driver)

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t139-jev-v3-w90/pacman/jev/demo.png` | 157544 | `0677cb7f83416c1defb92e421e7474f029b05993f9d3e2655ada28b728df024c` |
| `runs/model-player/t139-jev-v3-w90/pacman/jev/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t139-jev-v3-w90/pacman/jev/engine-game.stdout.txt` | 733 | `7338a8bf6f313dd05a0a5d9ea444d5cd5570fa0fe1a5dc49253b49b870a9d487` |
| `runs/model-player/t139-jev-v3-w90/pacman/jev/filmstrip.png` | 144849 | `63bda254e46c172b0f829e31929a30333f2171c7fcd139b5962cb019a95003bd` |
| `runs/model-player/t139-jev-v3-w90/pacman/jev/frames.json` | 569065 | `283338b4a534c66a669e8607426a82c86e54a8c12fe5f70cda9ff96b619e30af` |
| `runs/model-player/t139-jev-v3-w90/pacman/jev/player.json` | 260636 | `ff5da1d8b68261b3ee5d9be992af1c936b420093d9ea35546204cef8c5a201a7` |
| `runs/model-player/t139-jev-v3-w90/pacman/jev/session.json` | 12433 | `5519a2fc0d81c513b581e705bf7254b392406a8758776456a76fa8b41b9a262b` |
| `runs/model-player/t139-jev-v3-w90/pacman/jev/steps.jsonl` | 154318 | `f97d861ade0221686a71dd05e694862629e072bbd54a249f481f2713636c92b4` |
| `calls/**`（714 个文件，23492245 B）| — | `3ffa8f2ccbf45ad290f122f9f4455f01164dace1f73b1da34e54a5e6be3c7a9d` |
| `frames/**`（37 个文件，400338 B）| — | `64a0eb7e84aab670bd526501a9add7c515044439ac3d77c032cc3cfab0f64766` |
| `states/**`（27 个文件，1154931 B）| — | `d04ec96f7de03776f093da2c8ca59d7ddc6bf6dd9a987115e054f76c7b07d638` |

## t139-jev-v3-w90 / platformer / jev

* 目录：`runs/model-player/t139-jev-v3-w90/platformer/jev`
* verdict：`INCONCLUSIVE`（counts_as_pass=False，strict=INCONCLUSIVE，baseline=INCONCLUSIVE，game_side=None）
* 注入/接受后变化/rate：6 / 4 / 0.6667
* 两窗对齐：4/6 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 4 frame(s))（matched 4/6，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game platformer --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9963 --window-frames 30 --out-prefix t139-jev-v3-w30`  <- t139_results_t139-jev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game platformer --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9964 --window-frames 90 --out-prefix t139-jev-v3-w90`  <- t139_results_t139-jev-v3-w90.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game platformer --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9961 --window-frames 30 --out-prefix t139-scripted-w30`  <- t139_results_t139-scripted-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game platformer --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9962 --window-frames 90 --out-prefix t139-scripted-w90`  <- t139_results_t139-scripted-w90.json (sweep driver)

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t139-jev-v3-w90/platformer/jev/demo.png` | 88055 | `e5a9138fc9a908650a1d65e5d30f6e310558004455a5838bc938781e128dbd5f` |
| `runs/model-player/t139-jev-v3-w90/platformer/jev/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t139-jev-v3-w90/platformer/jev/engine-game.stdout.txt` | 796 | `15ac94caf8b5cca943661ab102d52f63f22e0c1db4db4567be2f37229dfb05c9` |
| `runs/model-player/t139-jev-v3-w90/platformer/jev/filmstrip.png` | 53343 | `e215668e6d6669891c4c5108694f3dd2da8863f0af8307f2beed709b375c204d` |
| `runs/model-player/t139-jev-v3-w90/platformer/jev/frames.json` | 288961 | `f8caede6de145569b83c0312f4a3ad029e6a024853ccbf5e6e6a8d0a79ae4b07` |
| `runs/model-player/t139-jev-v3-w90/platformer/jev/player.json` | 136105 | `36e7a07d280696be945d30fc33fb505ff07d1dadfe7df8523fa8eb63dda28e54` |
| `runs/model-player/t139-jev-v3-w90/platformer/jev/session.json` | 11113 | `5acee44f9c78d53c9850e5c8787abe55bcbaee3249edb13145cf327b149793d4` |
| `runs/model-player/t139-jev-v3-w90/platformer/jev/steps.jsonl` | 80945 | `ea39b16de249df18e39aabff5e3e127f1284931fc1815ec975fd368ad05b9f6a` |
| `calls/**`（382 个文件，6649531 B）| — | `da6c1cf2e55064d3527cb132e48061c47668ff23c4b8fd0e553304c61d480959` |
| `frames/**`（19 个文件，203073 B）| — | `34dc6c31f13c95fff22090648239764fe614a25806da6db674da324d6cf66ef2` |
| `states/**`（15 个文件，322457 B）| — | `7fb99d635cca3b738062023114c181231e864de77dee8cf12fab0744f556a2a5` |

## t139-jev-v3-w90 / pong / jev

* 目录：`runs/model-player/t139-jev-v3-w90/pong/jev`
* verdict：`PASS(baseline only)`（counts_as_pass=False，strict=FAIL，baseline=PASS，game_side=None）
* 注入/接受后变化/rate：8 / 7 / 0.875
* 两窗对齐：6/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 6 frame(s))（matched 6/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game pong --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9963 --window-frames 30 --out-prefix t139-jev-v3-w30`  <- t139_results_t139-jev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game pong --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9964 --window-frames 90 --out-prefix t139-jev-v3-w90`  <- t139_results_t139-jev-v3-w90.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game pong --backend playjev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9965 --window-frames 30 --out-prefix t139-playjev-v3-w30`  <- t139_results_t139-playjev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game pong --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9961 --window-frames 30 --out-prefix t139-scripted-w30`  <- t139_results_t139-scripted-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game pong --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9962 --window-frames 90 --out-prefix t139-scripted-w90`  <- t139_results_t139-scripted-w90.json (sweep driver)

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t139-jev-v3-w90/pong/jev/demo.png` | 91850 | `c04ea3f2b12483e8e4f8e8a4c9c9c9ff77c5dbd0f67b81f4c4361224240c87a5` |
| `runs/model-player/t139-jev-v3-w90/pong/jev/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t139-jev-v3-w90/pong/jev/engine-game.stdout.txt` | 3334 | `bddcd697df7c770c586734f9da8dc769ada1efaa0b6a389bbe80871d013471a2` |
| `runs/model-player/t139-jev-v3-w90/pong/jev/filmstrip.png` | 62239 | `68dc998c5d2c0b7defc2438d813b67f3c7e4cc12e1ba3dc1c9dbc62b7740a097` |
| `runs/model-player/t139-jev-v3-w90/pong/jev/frames.json` | 418208 | `6fd339ba928a517c9067d3921c47f43f04827d58f02030ca91ad92e2dddaa3bb` |
| `runs/model-player/t139-jev-v3-w90/pong/jev/player.json` | 209649 | `c7349d2b2ba54aba05dbc315f30b32ec4a36f85d87607a5d59d1d1f405ddd813` |
| `runs/model-player/t139-jev-v3-w90/pong/jev/session.json` | 11295 | `9487ae4dc024e0be874bb83704f8cbb7a6028c590a9ca472fe5ad7bfde4b0aa7` |
| `runs/model-player/t139-jev-v3-w90/pong/jev/steps.jsonl` | 140785 | `cac659005dacbfb8136a155d751e739899e0618ffbbc3f0b4fb3aa4f1e989fa4` |
| `calls/**`（786 个文件，2180141 B）| — | `53b903619b3022bfefa0c23110ca92161f45f92a3ab7401c4320965cdebbc030` |
| `frames/**`（37 个文件，287318 B）| — | `919fb872fed633c4904f45753604257ddfeee067ae0899b21f6fa62b8c29e4ce` |
| `states/**`（27 个文件，65976 B）| — | `c759291768a6d9c58a64fe91aae95c7e374952046da2894bca97899e1771a4ec` |

## t139-jev-v3-w90 / puzzlebobble / jev

* 目录：`runs/model-player/t139-jev-v3-w90/puzzlebobble/jev`
* verdict：`INCONCLUSIVE`（counts_as_pass=False，strict=INCONCLUSIVE，baseline=INCONCLUSIVE，game_side=None）
* 注入/接受后变化/rate：2 / 2 / 1.0
* 两窗对齐：3/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 3 frame(s))（matched 3/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game puzzlebobble --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9963 --window-frames 30 --out-prefix t139-jev-v3-w30`  <- t139_results_t139-jev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game puzzlebobble --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9964 --window-frames 90 --out-prefix t139-jev-v3-w90`  <- t139_results_t139-jev-v3-w90.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game puzzlebobble --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9961 --window-frames 30 --out-prefix t139-scripted-w30`  <- t139_results_t139-scripted-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game puzzlebobble --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9962 --window-frames 90 --out-prefix t139-scripted-w90`  <- t139_results_t139-scripted-w90.json (sweep driver)

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t139-jev-v3-w90/puzzlebobble/jev/demo.png` | 182429 | `0ed82a9e1353758e9d4091894919459e17b198e46aad2904eee1d68d331fbd56` |
| `runs/model-player/t139-jev-v3-w90/puzzlebobble/jev/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t139-jev-v3-w90/puzzlebobble/jev/engine-game.stdout.txt` | 739 | `b1f6cf0b190850459fc0410ff6562e693e94fc1c02001ecc30be80a1b6bf2db5` |
| `runs/model-player/t139-jev-v3-w90/puzzlebobble/jev/filmstrip.png` | 126534 | `dae2333b047066d6db07031c028718328c4524278fc9329b658804480a2ffe75` |
| `runs/model-player/t139-jev-v3-w90/puzzlebobble/jev/frames.json` | 733291 | `044698b9609141044a6a2a721350be1c1b059110fa0b98c43d6b13c71d558541` |
| `runs/model-player/t139-jev-v3-w90/puzzlebobble/jev/player.json` | 72131 | `6fb09dbd3113c124d3203a397b5a10d59bd0a5b588407c80e6868667c310709f` |
| `runs/model-player/t139-jev-v3-w90/puzzlebobble/jev/session.json` | 11264 | `df877fe0ceed4ee4b90137d4b162c9d06fc9a11599525da26e5f761a23d3a216` |
| `runs/model-player/t139-jev-v3-w90/puzzlebobble/jev/steps.jsonl` | 139461 | `bec9206e9e3a547b4874036ef6418553ba321dc210db911c258f69564e3a8480` |
| `calls/**`（722 个文件，12469974 B）| — | `d53f60a05fa3f15b523a8d787607f1e14dba74d6110da2afa168e842a9963ef9` |
| `frames/**`（37 个文件，523236 B）| — | `443e7b6eed140ed015f42c0411a7652b38247beaf24527934f719f71cff7e12e` |
| `states/**`（27 个文件，539285 B）| — | `bbaaa1dbfe0cb661dabf548350540b1ad17b73b2e940107adccd88d0d4be88b4` |

## t139-jev-v3-w90 / rtype / jev

* 目录：`runs/model-player/t139-jev-v3-w90/rtype/jev`
* verdict：`INCONCLUSIVE`（counts_as_pass=False，strict=INCONCLUSIVE，baseline=INCONCLUSIVE，game_side=None）
* 注入/接受后变化/rate：0 / 0 / None
* 两窗对齐：7/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 5 frame(s))（matched 7/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game rtype --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9963 --window-frames 30 --out-prefix t139-jev-v3-w30`  <- t139_results_t139-jev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game rtype --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9964 --window-frames 90 --out-prefix t139-jev-v3-w90`  <- t139_results_t139-jev-v3-w90.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game rtype --backend playjev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9965 --window-frames 30 --out-prefix t139-playjev-v3-w30`  <- t139_results_t139-playjev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game rtype --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9961 --window-frames 30 --out-prefix t139-scripted-w30`  <- t139_results_t139-scripted-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game rtype --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9962 --window-frames 90 --out-prefix t139-scripted-w90`  <- t139_results_t139-scripted-w90.json (sweep driver)

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t139-jev-v3-w90/rtype/jev/demo.png` | 153493 | `9a5a613351dd968364f66c5c2abe33ce813267a46cfcfde65b1fd1461b674128` |
| `runs/model-player/t139-jev-v3-w90/rtype/jev/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t139-jev-v3-w90/rtype/jev/engine-game.stdout.txt` | 743 | `6146234f39ccc7a0d3850ae534963675666edff7e391da0dcbed2e6d7216d647` |
| `runs/model-player/t139-jev-v3-w90/rtype/jev/filmstrip.png` | 104310 | `0915488e56c95af4c112604207526aa8c2ac1376efd28c0106c98c907b1f0587` |
| `runs/model-player/t139-jev-v3-w90/rtype/jev/frames.json` | 631851 | `328a632504e6514144e9d0334be87fb6d21aef9f88d6f5981bade155c99ba99d` |
| `runs/model-player/t139-jev-v3-w90/rtype/jev/player.json` | 276042 | `aff4c4fdbbf9462ffce1b09ed27019e207ea59e54bb297cd75cfdbaae7298cb9` |
| `runs/model-player/t139-jev-v3-w90/rtype/jev/session.json` | 11220 | `fe4a7ec09aba6a9f106fa6dbe9beaf4285cc3fc4e4ed0f711a51dc188436b6dc` |
| `runs/model-player/t139-jev-v3-w90/rtype/jev/steps.jsonl` | 126175 | `27991cc0480371728b381b5e51d63a557d637bad439d1f5d40a11bef6000ac27` |
| `calls/**`（740 个文件，11915027 B）| — | `775a52240f5f70a520b1f3fa97ba06e2c7c0941ca31719a12695377923f14eda` |
| `frames/**`（37 个文件，447515 B）| — | `956b77b45fe7bb52762812c06261107cb403e03a6d830b3ff246b473190edaf8` |
| `states/**`（27 个文件，499047 B）| — | `e0b224d0ba601684a7281530b76e8969114783b8043336abcc8ee68ab0f27ff7` |

## t139-jev-v3-w90 / snake / jev

* 目录：`runs/model-player/t139-jev-v3-w90/snake/jev`
* verdict：`INCONCLUSIVE`（counts_as_pass=False，strict=INCONCLUSIVE，baseline=INCONCLUSIVE，game_side=None）
* 注入/接受后变化/rate：10 / 10 / 1.0
* 两窗对齐：0/10 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 6 frame(s))（matched 0/10，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game snake --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9963 --window-frames 30 --out-prefix t139-jev-v3-w30`  <- t139_results_t139-jev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game snake --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9964 --window-frames 90 --out-prefix t139-jev-v3-w90`  <- t139_results_t139-jev-v3-w90.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game snake --backend playjev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9965 --window-frames 30 --out-prefix t139-playjev-v3-w30`  <- t139_results_t139-playjev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game snake --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9961 --window-frames 30 --out-prefix t139-scripted-w30`  <- t139_results_t139-scripted-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game snake --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9962 --window-frames 90 --out-prefix t139-scripted-w90`  <- t139_results_t139-scripted-w90.json (sweep driver)

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t139-jev-v3-w90/snake/jev/demo.png` | 68061 | `4b28b901c7906ec67f67749071489abee84257dfd1657a6358c255ef5355cab4` |
| `runs/model-player/t139-jev-v3-w90/snake/jev/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t139-jev-v3-w90/snake/jev/engine-game.stdout.txt` | 6186 | `cbfd67d3048a1cb36588bfa110748d09fc462952ec3ee8fd8e71f66710d011be` |
| `runs/model-player/t139-jev-v3-w90/snake/jev/filmstrip.png` | 39350 | `41c2cd88e488e6e81e11ef226c9196883ecb52486fe08e866a11fbef5355615a` |
| `runs/model-player/t139-jev-v3-w90/snake/jev/frames.json` | 156611 | `b5cf5238dac27e286a95fc6d57dcf1bd3d3d055595c8d8e33d6ce2e01e9c7826` |
| `runs/model-player/t139-jev-v3-w90/snake/jev/player.json` | 118889 | `ab485992e553e24db86b632d82f4131d28b1ae859809180d306998501e752de5` |
| `runs/model-player/t139-jev-v3-w90/snake/jev/session.json` | 11852 | `6f52bd4db9b17e1e893d56478881a22792695637cb0b044a857b7302f99e4edd` |
| `runs/model-player/t139-jev-v3-w90/snake/jev/steps.jsonl` | 137175 | `948c0f2c445ab924587b1acb7edd373eae52ff91083392c680b61386d58146a3` |
| `calls/**`（472 个文件，3354609 B）| — | `d491c9ccc4ab5248257b1be21601764dc9460391f44efe4f371fe3c32f4962ce` |
| `frames/**`（31 个文件，95526 B）| — | `86592a26390e66bfbb427c2d70335f039125427021cdcdc1bdcabed716357374` |
| `states/**`（23 个文件，201766 B）| — | `c720469301ea89bf8a1aeeff9e66aa617efa122d59db74976b97c75596c51d3c` |

## t139-jev-v3-w90 / sokoban / jev

* 目录：`runs/model-player/t139-jev-v3-w90/sokoban/jev`
* verdict：`INCONCLUSIVE`（counts_as_pass=False，strict=INCONCLUSIVE，baseline=INCONCLUSIVE，game_side=None）
* 注入/接受后变化/rate：12 / 1 / 0.0833
* 两窗对齐：7/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 2 frame(s))（matched 7/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game sokoban --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9963 --window-frames 30 --out-prefix t139-jev-v3-w30`  <- t139_results_t139-jev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game sokoban --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9964 --window-frames 90 --out-prefix t139-jev-v3-w90`  <- t139_results_t139-jev-v3-w90.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game sokoban --backend playjev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9965 --window-frames 30 --out-prefix t139-playjev-v3-w30`  <- t139_results_t139-playjev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game sokoban --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9973 --window-frames 30 --out-prefix t139-scripted-w30`  <- t139_results_t139-scripted-w30-counterev.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game sokoban --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9961 --window-frames 30 --out-prefix t139-scripted-w30`  <- t139_results_t139-scripted-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game sokoban --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9962 --window-frames 90 --out-prefix t139-scripted-w90`  <- t139_results_t139-scripted-w90.json (sweep driver)

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t139-jev-v3-w90/sokoban/jev/demo.png` | 146601 | `8b52af723e34c9bad1129f8f98af1a1f5d096cb712f19ea301366dbf5e6e3111` |
| `runs/model-player/t139-jev-v3-w90/sokoban/jev/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t139-jev-v3-w90/sokoban/jev/engine-game.stdout.txt` | 745 | `a8fa9012e93b8db76332bdd0fb720ec52ae5253c26f6bb0b46d1ed4c054e0236` |
| `runs/model-player/t139-jev-v3-w90/sokoban/jev/filmstrip.png` | 101789 | `c36aa1e17cee52f19dfcb7cb9aaf4bb2428f85f2ec6d32898a95290f67c394f5` |
| `runs/model-player/t139-jev-v3-w90/sokoban/jev/frames.json` | 586376 | `b31692563846e19c08676adb045ee494441902647cb725dbc3374f91c95234b2` |
| `runs/model-player/t139-jev-v3-w90/sokoban/jev/player.json` | 261013 | `97562849caa9b48378d09b21a86e5b17a487f872c298e72f845eb14dc8d741ad` |
| `runs/model-player/t139-jev-v3-w90/sokoban/jev/session.json` | 12579 | `839e6a16d8a6d14b39e91c22ca7fb7a3a9230d0934dfad0e339268a4f41b201f` |
| `runs/model-player/t139-jev-v3-w90/sokoban/jev/steps.jsonl` | 143139 | `42a33b4a89ac29436e824ee25c18560a78c3c213306df5f5430a5c51b2931419` |
| `calls/**`（843 个文件，10031410 B）| — | `53549b6faf98e35f3a7be81a0be31ed9f53133ae9535961c97a9e96360c495fe` |
| `frames/**`（37 个文件，413183 B）| — | `8efbfce4930f266aeedf1eb3fab5636dfa39469164080d8a06ca154d80d5d015` |
| `states/**`（27 个文件，374566 B）| — | `5a16cbf48eebcd41784f3cfb03065ce2ceeed51d652afdc19772d4127b2ad9bc` |

## t139-jev-v3-w90 / spaceinvaders / jev

* 目录：`runs/model-player/t139-jev-v3-w90/spaceinvaders/jev`
* verdict：`INCONCLUSIVE`（counts_as_pass=False，strict=INCONCLUSIVE，baseline=INCONCLUSIVE，game_side=None）
* 注入/接受后变化/rate：12 / 12 / 1.0
* 两窗对齐：4/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 2 frame(s))（matched 4/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game spaceinvaders --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9963 --window-frames 30 --out-prefix t139-jev-v3-w30`  <- t139_results_t139-jev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game spaceinvaders --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9964 --window-frames 90 --out-prefix t139-jev-v3-w90`  <- t139_results_t139-jev-v3-w90.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game spaceinvaders --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9961 --window-frames 30 --out-prefix t139-scripted-w30`  <- t139_results_t139-scripted-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game spaceinvaders --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9962 --window-frames 90 --out-prefix t139-scripted-w90`  <- t139_results_t139-scripted-w90.json (sweep driver)

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t139-jev-v3-w90/spaceinvaders/jev/demo.png` | 116588 | `f7c0d592bf562defa9b1e7efd2e6adb7fa516c5bd0decfbf4aae1814483e6983` |
| `runs/model-player/t139-jev-v3-w90/spaceinvaders/jev/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t139-jev-v3-w90/spaceinvaders/jev/engine-game.stdout.txt` | 754 | `aa7f926f420a50de27a22b711dcc63b9038f4d8c23020bec539ff43cd199c0b8` |
| `runs/model-player/t139-jev-v3-w90/spaceinvaders/jev/filmstrip.png` | 94303 | `0dd2dd20388cdc0867119178f40ff8c017e3b38ed932b3fbbe04430bc552e321` |
| `runs/model-player/t139-jev-v3-w90/spaceinvaders/jev/frames.json` | 517268 | `3fcdf21632c3959e7d0bdae37e83704ae002d0a9a72f845f8c8182d82f22474c` |
| `runs/model-player/t139-jev-v3-w90/spaceinvaders/jev/player.json` | 232665 | `556084b1ff0ca6d52b1053767481fd4cc80cec8b2fa8708ee5595c2ee53edb4f` |
| `runs/model-player/t139-jev-v3-w90/spaceinvaders/jev/session.json` | 11167 | `6cb084e503bf889a1325d1221361a25d061d48bc742e463035da07c7019ea2f3` |
| `runs/model-player/t139-jev-v3-w90/spaceinvaders/jev/steps.jsonl` | 158637 | `30b785d5f7e910cfed634268d28acd90090ed09393c0e9a0e021dcda812db1e9` |
| `calls/**`（834 个文件，6489609 B）| — | `b454cde0509667abdbd97d181f5bc8b48cf0eab68c305ee8c0084d307ab13d2a` |
| `frames/**`（37 个文件，361155 B）| — | `cefb5e4900f91d5cc094c9afa72d1fe3dd25ecdc79ac1c6ded6d781a00d81f0a` |
| `states/**`（27 个文件，240257 B）| — | `1a5115876eca841f106628248e74c8f5f01d0e4b6846a649c0e282c8e3cbe0b4` |

## t139-jev-v3-w90 / tetris / jev

* 目录：`runs/model-player/t139-jev-v3-w90/tetris/jev`
* verdict：`PASS`（counts_as_pass=True，strict=PASS，baseline=PASS，game_side=None）
* 注入/接受后变化/rate：8 / 8 / 1.0
* 两窗对齐：3/8 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 3 frame(s))（matched 3/8，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game tetris --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9963 --window-frames 30 --out-prefix t139-jev-v3-w30`  <- t139_results_t139-jev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game tetris --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9964 --window-frames 90 --out-prefix t139-jev-v3-w90`  <- t139_results_t139-jev-v3-w90.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game tetris --backend playjev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9965 --window-frames 30 --out-prefix t139-playjev-v3-w30`  <- t139_results_t139-playjev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game tetris --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9961 --window-frames 30 --out-prefix t139-scripted-w30`  <- t139_results_t139-scripted-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game tetris --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9962 --window-frames 90 --out-prefix t139-scripted-w90`  <- t139_results_t139-scripted-w90.json (sweep driver)

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t139-jev-v3-w90/tetris/jev/demo.png` | 74303 | `d3ce04a38368e33a6fb7647d514b5fe69e8cf8cd2623b33d271cf8b809ce57b0` |
| `runs/model-player/t139-jev-v3-w90/tetris/jev/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t139-jev-v3-w90/tetris/jev/engine-game.stdout.txt` | 7988 | `8f222cd13d57fbd77c1c0d695b77d32f34d434064efac2a6d1659adc50276861` |
| `runs/model-player/t139-jev-v3-w90/tetris/jev/filmstrip.png` | 43424 | `3066725330309646e4c60639fa87a0b2e4b5c9ccf66f1e0f99709a8017fe3b7b` |
| `runs/model-player/t139-jev-v3-w90/tetris/jev/frames.json` | 199643 | `538cc5a84d6d3e03a19928d44b3fdc853aefc58a2c82aa21d923f137c344053f` |
| `runs/model-player/t139-jev-v3-w90/tetris/jev/player.json` | 115970 | `a21965f00c9658db5960263d863deefdd6f8ca3503eb3c9d7b38301cd2d73cfb` |
| `runs/model-player/t139-jev-v3-w90/tetris/jev/session.json` | 11075 | `0402c614b46248d23c7cd9aae37e9bb0ea666b82ceebc1a58a7592df8273fe81` |
| `runs/model-player/t139-jev-v3-w90/tetris/jev/steps.jsonl` | 98281 | `39e6d5785d2e404c4b2cf2eafc6bb909897fcac869fd753caf2603718b6dc91a` |
| `calls/**`（570 个文件，1088629 B）| — | `4a92003aec11a2f4c5aac829143cb73d52d45b4ab4414c1f79ad24a21adafea8` |
| `frames/**`（25 个文件，131740 B）| — | `9dc301a194d673c06564ebbd34296fe8985bfe2645c657cd4d96bf5031526d78` |
| `states/**`（19 个文件，30311 B）| — | `c9012d5ae92daf3bd55ec57a4973d3f8170df29075791b12004bbd7514b49015` |

## t139-jev-v3-w90 / towerdefense / jev

* 目录：`runs/model-player/t139-jev-v3-w90/towerdefense/jev`
* verdict：`INCONCLUSIVE`（counts_as_pass=False，strict=INCONCLUSIVE，baseline=INCONCLUSIVE，game_side=None）
* 注入/接受后变化/rate：8 / 8 / 1.0
* 两窗对齐：4/8 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 2 frame(s))（matched 4/8，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game towerdefense --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9963 --window-frames 30 --out-prefix t139-jev-v3-w30`  <- t139_results_t139-jev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game towerdefense --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9964 --window-frames 90 --out-prefix t139-jev-v3-w90`  <- t139_results_t139-jev-v3-w90.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game towerdefense --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9973 --window-frames 30 --out-prefix t139-scripted-w30`  <- t139_results_t139-scripted-w30-counterev.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game towerdefense --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9961 --window-frames 30 --out-prefix t139-scripted-w30`  <- t139_results_t139-scripted-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game towerdefense --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9962 --window-frames 90 --out-prefix t139-scripted-w90`  <- t139_results_t139-scripted-w90.json (sweep driver)

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t139-jev-v3-w90/towerdefense/jev/demo.png` | 140492 | `0d40b174990e6ada45fa1a1a92e855a5d97a1f71b49853db67ee5480878b2f3b` |
| `runs/model-player/t139-jev-v3-w90/towerdefense/jev/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t139-jev-v3-w90/towerdefense/jev/engine-game.stdout.txt` | 753 | `041dd9d6460afdffca4b15ac0e474cbf387f3bb3efd25a3d9a2bbbf09c7d165e` |
| `runs/model-player/t139-jev-v3-w90/towerdefense/jev/filmstrip.png` | 80198 | `33ff043a685003fcbd16351a3724e4323ef96e620ceaad88eacee6ce6e10fa06` |
| `runs/model-player/t139-jev-v3-w90/towerdefense/jev/frames.json` | 441940 | `a25655c92765c69f8a52b552505d45d3c50e6937a0c4a0734e9a174e46a72285` |
| `runs/model-player/t139-jev-v3-w90/towerdefense/jev/player.json` | 198232 | `27a6ce5757ebfb69fe0f9145578b9a9900ae320e1cfbb80b0defef0f19121f2c` |
| `runs/model-player/t139-jev-v3-w90/towerdefense/jev/session.json` | 12811 | `f4dd0ea24025992da1768ef1da65b67d17ba9031ec1613df9bafc0384e7f57d8` |
| `runs/model-player/t139-jev-v3-w90/towerdefense/jev/steps.jsonl` | 100210 | `33a5f805ac5482a17398be5fb74262fcb2249c0fffedf536fb70bff5a3c20626` |
| `calls/**`（508 个文件，9702696 B）| — | `c2ac3dbd9e6085ead01196a96dc9eeb441e62e369fccba28b98b9e882dc2103a` |
| `frames/**`（25 个文件，313383 B）| — | `76cc9493c617c3c216b1305d41ab1c661c3cb91756f7cd30e967d89ec41613f0` |
| `states/**`（19 个文件，451902 B）| — | `82dc8de951f367e588f305467ace18886beca0d9ac304297a73cb4ca2478f378` |

## t139-playjev-v3-w30 / asteroids / playjev

* 目录：`runs/model-player/t139-playjev-v3-w30/asteroids/playjev`
* verdict：`INCONCLUSIVE`（counts_as_pass=False，strict=INCONCLUSIVE，baseline=INCONCLUSIVE，game_side=None）
* 注入/接受后变化/rate：12 / 12 / 1.0
* 两窗对齐：4/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 4 frame(s))（matched 4/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game asteroids --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9963 --window-frames 30 --out-prefix t139-jev-v3-w30`  <- t139_results_t139-jev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game asteroids --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9964 --window-frames 90 --out-prefix t139-jev-v3-w90`  <- t139_results_t139-jev-v3-w90.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game asteroids --backend playjev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9965 --window-frames 30 --out-prefix t139-playjev-v3-w30`  <- t139_results_t139-playjev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game asteroids --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9961 --window-frames 30 --out-prefix t139-scripted-w30`  <- t139_results_t139-scripted-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game asteroids --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9962 --window-frames 90 --out-prefix t139-scripted-w90`  <- t139_results_t139-scripted-w90.json (sweep driver)

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t139-playjev-v3-w30/asteroids/playjev/demo.png` | 121655 | `3342198c1efc8f00f9b41fd2845c454f55f3684b4e713dc41f55b80ab186a9c7` |
| `runs/model-player/t139-playjev-v3-w30/asteroids/playjev/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t139-playjev-v3-w30/asteroids/playjev/engine-game.stdout.txt` | 741 | `0e77f5b62430913c85669ed88c2b2b5e62ec625c21644129cd60a0b89bb75429` |
| `runs/model-player/t139-playjev-v3-w30/asteroids/playjev/filmstrip.png` | 74488 | `6aa722ce8d50609ed5ae957c6825a46473e9a12b156a361a74e340e72165b219` |
| `runs/model-player/t139-playjev-v3-w30/asteroids/playjev/frames.json` | 551545 | `2927281bed1d23c8e66214922870b5ac5ff0c52a90cbea56ec86e564b7259a28` |
| `runs/model-player/t139-playjev-v3-w30/asteroids/playjev/player.json` | 344606 | `b0a3a2fda589fa467754ee61efd2514861685f7d793344a37de2770dd5c50fd2` |
| `runs/model-player/t139-playjev-v3-w30/asteroids/playjev/session.json` | 11128 | `11de06db5ad42d579184df2492443eda8fbd1a53cc0270fc7c9717af65c38819` |
| `runs/model-player/t139-playjev-v3-w30/asteroids/playjev/steps.jsonl` | 148540 | `fdcb4df7089e5ebff344a277bd9d0a56ac878bd54fdf281734bf2cb7dc7cb01c` |
| `calls/**`（393 个文件，1389916 B）| — | `e602ddd980206af2516b359ce6ec7edf9d0073a680f4a7a164e2b638676f674a` |
| `frames/**`（37 个文件，386829 B）| — | `7306aed97b2f7f7ad7390641fc39ea0883b391b7a828624cc0ea9a3877556fa2` |
| `states/**`（27 个文件，76460 B）| — | `3ae838b7b631be05d62778ce60b600364814145587cab97bba2e11a086602de8` |

## t139-playjev-v3-w30 / game2048 / playjev

* 目录：`runs/model-player/t139-playjev-v3-w30/game2048/playjev`
* verdict：`PASS`（counts_as_pass=True，strict=PASS，baseline=PASS，game_side=None）
* 注入/接受后变化/rate：12 / 5 / 1.0
* 两窗对齐：5/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 5 frame(s))（matched 5/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game game2048 --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9963 --window-frames 30 --out-prefix t139-jev-v3-w30`  <- t139_results_t139-jev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game game2048 --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9964 --window-frames 90 --out-prefix t139-jev-v3-w90`  <- t139_results_t139-jev-v3-w90.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game game2048 --backend playjev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9965 --window-frames 30 --out-prefix t139-playjev-v3-w30`  <- t139_results_t139-playjev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game game2048 --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9961 --window-frames 30 --out-prefix t139-scripted-w30`  <- t139_results_t139-scripted-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game game2048 --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9962 --window-frames 90 --out-prefix t139-scripted-w90`  <- t139_results_t139-scripted-w90.json (sweep driver)

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t139-playjev-v3-w30/game2048/playjev/demo.png` | 144075 | `1a24abe897b338361630759605b316c98ff0748f408aff732418da6b93e3164e` |
| `runs/model-player/t139-playjev-v3-w30/game2048/playjev/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t139-playjev-v3-w30/game2048/playjev/engine-game.stdout.txt` | 781 | `953409c1cac21513aeea24c555bb5c0183d71d8e3c6b970a249ada5f20d1b04a` |
| `runs/model-player/t139-playjev-v3-w30/game2048/playjev/filmstrip.png` | 89905 | `da36142c4a3e30bc4d04393c73e8df29b950a1c4bced1822a97bc0d0c5be9ec6` |
| `runs/model-player/t139-playjev-v3-w30/game2048/playjev/frames.json` | 623824 | `526c02e59cabdb052e3f9dffdb6653930bb345a7ba6b2c4c9746bf66b7052918` |
| `runs/model-player/t139-playjev-v3-w30/game2048/playjev/player.json` | 376207 | `0d29d0e53c457bed8518c5fd7e4fe227316c9f17d4e45c322f2a024297dad036` |
| `runs/model-player/t139-playjev-v3-w30/game2048/playjev/session.json` | 10986 | `f2708636dabf5b0b5d6d3974dcccc10a947e0d64f7627fbc0817007d9af8b6fb` |
| `runs/model-player/t139-playjev-v3-w30/game2048/playjev/steps.jsonl` | 165382 | `2690aaaf4f9cf284ed1d1ec991a6e84fa9336ca6d7c268b66942825c40fdaa6f` |
| `calls/**`（400 个文件，2705922 B）| — | `fba984223dab5c9277f8b7aed515e0aeac8309cf3bdc41c78457638653a3f121` |
| `frames/**`（37 个文件，440996 B）| — | `8c041eb3650c43957348de9436bfa1f21d553f4426248ffc64bb644dedfd2336` |
| `states/**`（27 个文件，202637 B）| — | `0633deffd426103e12d68cb36d9bf7eb402aefc73822884f83c1dca2687d24d3` |

## t139-playjev-v3-w30 / match3 / playjev

* 目录：`runs/model-player/t139-playjev-v3-w30/match3/playjev`
* verdict：`INCONCLUSIVE`（counts_as_pass=False，strict=INCONCLUSIVE，baseline=INCONCLUSIVE，game_side=None）
* 注入/接受后变化/rate：12 / 4 / 0.3333
* 两窗对齐：3/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 3 frame(s))（matched 3/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game match3 --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9963 --window-frames 30 --out-prefix t139-jev-v3-w30`  <- t139_results_t139-jev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game match3 --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9964 --window-frames 90 --out-prefix t139-jev-v3-w90`  <- t139_results_t139-jev-v3-w90.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game match3 --backend playjev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9965 --window-frames 30 --out-prefix t139-playjev-v3-w30`  <- t139_results_t139-playjev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game match3 --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9973 --window-frames 30 --out-prefix t139-scripted-w30`  <- t139_results_t139-scripted-w30-counterev.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game match3 --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9961 --window-frames 30 --out-prefix t139-scripted-w30`  <- t139_results_t139-scripted-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game match3 --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9962 --window-frames 90 --out-prefix t139-scripted-w90`  <- t139_results_t139-scripted-w90.json (sweep driver)

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t139-playjev-v3-w30/match3/playjev/demo.png` | 204278 | `95625525af761a107d95433b836bcb1e2b16821335afca2910fb6fb545460035` |
| `runs/model-player/t139-playjev-v3-w30/match3/playjev/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t139-playjev-v3-w30/match3/playjev/engine-game.stdout.txt` | 769 | `1e6c49ab6f2c9986dff6423d971778d54d9dc622ac94a246d1a7f8109485b8ff` |
| `runs/model-player/t139-playjev-v3-w30/match3/playjev/filmstrip.png` | 143258 | `60197946725b7dd7365ac0f4165dff19939e8f4f9ff9c36a47ab14cac5a09da0` |
| `runs/model-player/t139-playjev-v3-w30/match3/playjev/frames.json` | 609055 | `5dd67f557740ba9182cf594168163de231b5e815e8a1c93fc34cac6ca0a11bf4` |
| `runs/model-player/t139-playjev-v3-w30/match3/playjev/player.json` | 371634 | `96e3183481d1a3ee1b8cf27919f00e463b414c9b3561fd2e2fde56e3e08cb0f7` |
| `runs/model-player/t139-playjev-v3-w30/match3/playjev/session.json` | 12844 | `777c49fbb0a933951edb4489b90b94153a60a964f2538b04873fc784742b5b70` |
| `runs/model-player/t139-playjev-v3-w30/match3/playjev/steps.jsonl` | 149161 | `d44c54a2612547ae49cfd14f7069a95a74038872b37723aff65570e336e8db97` |
| `calls/**`（401 个文件，3856246 B）| — | `c38b52dfc6e18f90b01117f15b533f6f9a3f14121860f7204542d5904f3a82e0` |
| `frames/**`（37 个文件，429940 B）| — | `4cb115d11d59238376666248ac941696efa6f6e1d536f8ecebc55559ef44f6eb` |
| `states/**`（27 个文件，329462 B）| — | `4e6cc57452005744cfb4b37485e56723e959be6ac79d5cd56f279df23af0da73` |

## t139-playjev-v3-w30 / minesweeper / playjev

* 目录：`runs/model-player/t139-playjev-v3-w30/minesweeper/playjev`
* verdict：`INCONCLUSIVE`（counts_as_pass=False，strict=INCONCLUSIVE，baseline=INCONCLUSIVE，game_side=None）
* 注入/接受后变化/rate：12 / 4 / 0.3333
* 两窗对齐：4/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 5 frame(s))（matched 4/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game minesweeper --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9963 --window-frames 30 --out-prefix t139-jev-v3-w30`  <- t139_results_t139-jev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game minesweeper --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9964 --window-frames 90 --out-prefix t139-jev-v3-w90`  <- t139_results_t139-jev-v3-w90.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game minesweeper --backend playjev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9965 --window-frames 30 --out-prefix t139-playjev-v3-w30`  <- t139_results_t139-playjev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game minesweeper --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9973 --window-frames 30 --out-prefix t139-scripted-w30`  <- t139_results_t139-scripted-w30-counterev.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game minesweeper --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9961 --window-frames 30 --out-prefix t139-scripted-w30`  <- t139_results_t139-scripted-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game minesweeper --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9962 --window-frames 90 --out-prefix t139-scripted-w90`  <- t139_results_t139-scripted-w90.json (sweep driver)

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t139-playjev-v3-w30/minesweeper/playjev/demo.png` | 153153 | `c3543f093cbdd76035dbb653d428898bee908e910f01b959225577530ede764d` |
| `runs/model-player/t139-playjev-v3-w30/minesweeper/playjev/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t139-playjev-v3-w30/minesweeper/playjev/engine-game.stdout.txt` | 745 | `e4a7756505b6392ec8ea1b3a6b2546534b9c30b350317c31fd80dbfd1fb68b69` |
| `runs/model-player/t139-playjev-v3-w30/minesweeper/playjev/filmstrip.png` | 128011 | `913317c0ada268725f83789a73532b87ed3e9431716b7d1ebef922c3d76b38f4` |
| `runs/model-player/t139-playjev-v3-w30/minesweeper/playjev/frames.json` | 621775 | `f611ebc48d3ba122007f5b97fd92982146eacac8f08b1085dbb1bb86ea161aa3` |
| `runs/model-player/t139-playjev-v3-w30/minesweeper/playjev/player.json` | 385859 | `032b10b6c23c07b9ef4249c9047c5e242951011e8eab08d6bcbded53763fa8d5` |
| `runs/model-player/t139-playjev-v3-w30/minesweeper/playjev/session.json` | 12963 | `cf7c0d37dca4c8781f7853514420a847816470b73500f6c8f6921149fd22c194` |
| `runs/model-player/t139-playjev-v3-w30/minesweeper/playjev/steps.jsonl` | 151944 | `824bbdc2d0f7d83e3fcbf1b5e5ea022100dcbe7426130635bd6bc10aa4f6968b` |
| `calls/**`（361 个文件，7274464 B）| — | `de3d2bd3e08e44b0f7e58aa4bc6400996c4539dc57122cae5c951cd371fd020c` |
| `frames/**`（37 个文件，439449 B）| — | `a3b2c10aec6a9afa02ef123786ab19b273a1fdc0df7851bcebbf65fd3827db1a` |
| `states/**`（27 个文件，785169 B）| — | `c11a4870bbd43d8d76d0535c9f244531504de31390e9b2e6a7bca4109bcfe9ae` |

## t139-playjev-v3-w30 / pacman / playjev

* 目录：`runs/model-player/t139-playjev-v3-w30/pacman/playjev`
* verdict：`FAIL`（counts_as_pass=False，strict=FAIL，baseline=FAIL，game_side=None）
* 注入/接受后变化/rate：12 / 0 / None
* 两窗对齐：2/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 4 frame(s))（matched 2/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game pacman --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9963 --window-frames 30 --out-prefix t139-jev-v3-w30`  <- t139_results_t139-jev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game pacman --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9964 --window-frames 90 --out-prefix t139-jev-v3-w90`  <- t139_results_t139-jev-v3-w90.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game pacman --backend playjev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9965 --window-frames 30 --out-prefix t139-playjev-v3-w30`  <- t139_results_t139-playjev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game pacman --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9973 --window-frames 30 --out-prefix t139-scripted-w30`  <- t139_results_t139-scripted-w30-counterev.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game pacman --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9961 --window-frames 30 --out-prefix t139-scripted-w30`  <- t139_results_t139-scripted-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game pacman --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9962 --window-frames 90 --out-prefix t139-scripted-w90`  <- t139_results_t139-scripted-w90.json (sweep driver)

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t139-playjev-v3-w30/pacman/playjev/demo.png` | 153644 | `30e498fbafb8fa65aa3deeccde163e4d954b4111329bd756e3ed52b12f927602` |
| `runs/model-player/t139-playjev-v3-w30/pacman/playjev/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t139-playjev-v3-w30/pacman/playjev/engine-game.stdout.txt` | 733 | `52a8c596f92fcb424b6721a86253e1ad2ccb4b531afe684698747783e6e97be5` |
| `runs/model-player/t139-playjev-v3-w30/pacman/playjev/filmstrip.png` | 141068 | `01afb6f0313deba66d0375f719205d0ce8442b51eb6a859eade89cd71ed28833` |
| `runs/model-player/t139-playjev-v3-w30/pacman/playjev/frames.json` | 592033 | `7b1f97ec84163e30f83b4575e8ac2cfb22f0601ba384d0be0742b03dab2e4790` |
| `runs/model-player/t139-playjev-v3-w30/pacman/playjev/player.json` | 366834 | `ff3d43344405baea5075002902a8906f8e3d84978d84463b51dbaf5817b7ac29` |
| `runs/model-player/t139-playjev-v3-w30/pacman/playjev/session.json` | 12407 | `257a85032cfe2c96e3082d4d2b887fc95ea4d967b71ec7ca41106953f2c85856` |
| `runs/model-player/t139-playjev-v3-w30/pacman/playjev/steps.jsonl` | 154789 | `3aab0766e9a96bb8b8b53a8f0b663e08bacf1f3ffd6035c0fb719b1a068389a5` |
| `calls/**`（362 个文件，10419163 B）| — | `d346267d63c44a3f28b9593fd3aea437eca5f1dae64b8db56a4491d09c9cf303` |
| `frames/**`（37 个文件，417286 B）| — | `7ed402fcc12bacc84adbc37b66ae0461fe54179aa32ecac0085a6937fb7d8364` |
| `states/**`（27 个文件，1185224 B）| — | `c5277a6f694bff5a33d065d9c4bcc6948ba87e62738a9454c1e8ae5cf677be79` |

## t139-playjev-v3-w30 / pong / playjev

* 目录：`runs/model-player/t139-playjev-v3-w30/pong/playjev`
* verdict：`INCONCLUSIVE`（counts_as_pass=False，strict=INCONCLUSIVE，baseline=INCONCLUSIVE，game_side=None）
* 注入/接受后变化/rate：12 / 1 / 0.0833
* 两窗对齐：0/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 4 frame(s))（matched 0/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game pong --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9963 --window-frames 30 --out-prefix t139-jev-v3-w30`  <- t139_results_t139-jev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game pong --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9964 --window-frames 90 --out-prefix t139-jev-v3-w90`  <- t139_results_t139-jev-v3-w90.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game pong --backend playjev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9965 --window-frames 30 --out-prefix t139-playjev-v3-w30`  <- t139_results_t139-playjev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game pong --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9961 --window-frames 30 --out-prefix t139-scripted-w30`  <- t139_results_t139-scripted-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game pong --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9962 --window-frames 90 --out-prefix t139-scripted-w90`  <- t139_results_t139-scripted-w90.json (sweep driver)

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t139-playjev-v3-w30/pong/playjev/demo.png` | 74650 | `b02cbc9cd141647175612ef3bf2cebde0dac141eb01ad63f3a49d3f40f9555c2` |
| `runs/model-player/t139-playjev-v3-w30/pong/playjev/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t139-playjev-v3-w30/pong/playjev/engine-game.stdout.txt` | 4402 | `3be223765ee7be32efc1b7aa419acd167bd149e87ed90fb7b13b97cd8e74b109` |
| `runs/model-player/t139-playjev-v3-w30/pong/playjev/filmstrip.png` | 45424 | `ede963a4d87a83609e06bd273226910194c99e6442cb6044b62d72509615948f` |
| `runs/model-player/t139-playjev-v3-w30/pong/playjev/frames.json` | 251147 | `d2a1901f01df03c85d29c4362f2c434e1e09e58224e82d657eaa52710f9d0960` |
| `runs/model-player/t139-playjev-v3-w30/pong/playjev/player.json` | 253912 | `2734f27acac82a3890384a89a8d6e1bbf32dac19a6006d5af298d23d352f3b14` |
| `runs/model-player/t139-playjev-v3-w30/pong/playjev/session.json` | 11269 | `e0bbc695b5eed5516a2dc65f6edf083fbc592e56c65fa462d4a4686da7f6cd99` |
| `runs/model-player/t139-playjev-v3-w30/pong/playjev/steps.jsonl` | 146035 | `0b84ed24689729915b94da4da8e15ec9a0b18aca769a4e4aa152ff405b85dcee` |
| `calls/**`（367 个文件，911159 B）| — | `5c60e2d155cd6643cf54372c4626ac2b52170263721277962ec71a004dacebbb` |
| `frames/**`（37 个文件，161791 B）| — | `c695b34d33e8c7a3f11448324633078d5f9a39fe0b631987bbc4a7d9fc560196` |
| `states/**`（27 个文件，64721 B）| — | `503448a4723ec44f94f44399d466b897185ac3f846497290766acef7499a5ff4` |

## t139-playjev-v3-w30 / rtype / playjev

* 目录：`runs/model-player/t139-playjev-v3-w30/rtype/playjev`
* verdict：`PASS`（counts_as_pass=True，strict=PASS，baseline=PASS，game_side=None）
* 注入/接受后变化/rate：8 / 8 / 1.0
* 两窗对齐：2/8 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 3 frame(s))（matched 2/8，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game rtype --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9963 --window-frames 30 --out-prefix t139-jev-v3-w30`  <- t139_results_t139-jev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game rtype --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9964 --window-frames 90 --out-prefix t139-jev-v3-w90`  <- t139_results_t139-jev-v3-w90.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game rtype --backend playjev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9965 --window-frames 30 --out-prefix t139-playjev-v3-w30`  <- t139_results_t139-playjev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game rtype --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9961 --window-frames 30 --out-prefix t139-scripted-w30`  <- t139_results_t139-scripted-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game rtype --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9962 --window-frames 90 --out-prefix t139-scripted-w90`  <- t139_results_t139-scripted-w90.json (sweep driver)

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t139-playjev-v3-w30/rtype/playjev/demo.png` | 128592 | `945a79109d1a747ffae229bcedf7488ff89293542646ab2379aefde4bd8782c1` |
| `runs/model-player/t139-playjev-v3-w30/rtype/playjev/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t139-playjev-v3-w30/rtype/playjev/engine-game.stdout.txt` | 743 | `f6086cfb922c3de099fb842e8c215a3d8ae51493dbe3636ad80cd0c71aa94f54` |
| `runs/model-player/t139-playjev-v3-w30/rtype/playjev/filmstrip.png` | 68951 | `6cb3ca8ca48389bb069ccec9190cb328a99bedfffc3e40dceac7f0d672dcb849` |
| `runs/model-player/t139-playjev-v3-w30/rtype/playjev/frames.json` | 426908 | `69ea953fc3b9f9a5f04561e6caf4423052e2998e7f6d086587413cdd1259fb3a` |
| `runs/model-player/t139-playjev-v3-w30/rtype/playjev/player.json` | 256032 | `aafe3816b6101ab00498b1dbc193eeb4f7452966a00fa5869ab5541edf64dbd1` |
| `runs/model-player/t139-playjev-v3-w30/rtype/playjev/session.json` | 11197 | `e8f6dc13ec511df6740f6e306145f57471a1a804c297795e78b90abbe1bb6b49` |
| `runs/model-player/t139-playjev-v3-w30/rtype/playjev/steps.jsonl` | 105715 | `e7bdd3c3558465f69da73a91cffc8da5e501b99c1a3ecb502c729faaef7dd240` |
| `calls/**`（253 个文件，3425055 B）| — | `aeb3908a035bdf3ef87fad30da7f233f247fcca7c459dbf9f338a13b21da45fd` |
| `frames/**`（25 个文件，302224 B）| — | `e40940be44b3d6689a651a813e5b7e2e82e5a322f4ae58f47a0b2c72700d4c91` |
| `states/**`（19 个文件，351623 B）| — | `6253f65d355bbb18dd8519bdde53725421fc855fbaa8a72831df2b01425cadad` |

## t139-playjev-v3-w30 / snake / playjev

* 目录：`runs/model-player/t139-playjev-v3-w30/snake/playjev`
* verdict：`INCONCLUSIVE`（counts_as_pass=False，strict=INCONCLUSIVE，baseline=INCONCLUSIVE，game_side=None）
* 注入/接受后变化/rate：12 / 4 / 0.3636
* 两窗对齐：1/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 6 frame(s))（matched 1/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game snake --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9963 --window-frames 30 --out-prefix t139-jev-v3-w30`  <- t139_results_t139-jev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game snake --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9964 --window-frames 90 --out-prefix t139-jev-v3-w90`  <- t139_results_t139-jev-v3-w90.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game snake --backend playjev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9965 --window-frames 30 --out-prefix t139-playjev-v3-w30`  <- t139_results_t139-playjev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game snake --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9961 --window-frames 30 --out-prefix t139-scripted-w30`  <- t139_results_t139-scripted-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game snake --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9962 --window-frames 90 --out-prefix t139-scripted-w90`  <- t139_results_t139-scripted-w90.json (sweep driver)

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t139-playjev-v3-w30/snake/playjev/demo.png` | 65779 | `d66bcd31fd5c69fa4a557f2e2ab9b9bf6a4981f5d71b87bab6ac64b7b0c10943` |
| `runs/model-player/t139-playjev-v3-w30/snake/playjev/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t139-playjev-v3-w30/snake/playjev/engine-game.stdout.txt` | 9520 | `246e2b4684a45d223c8d6ac994ca1fe221ab0803ce2cedace40d34a9825a90b4` |
| `runs/model-player/t139-playjev-v3-w30/snake/playjev/filmstrip.png` | 44049 | `d0afbc1715d8dd72d8f6e4d9f7ac6a664c6f2a225b261147df38e9e48c224982` |
| `runs/model-player/t139-playjev-v3-w30/snake/playjev/frames.json` | 187918 | `8143ff20e47f7bc7206428fcd190b85fd8cba4d31235115710c907a81bf10c4e` |
| `runs/model-player/t139-playjev-v3-w30/snake/playjev/player.json` | 236844 | `0ab3c4a12a56a1b16261f23c9c2be5f990c50fe5dd8830a5d86a5cafe94a06dc` |
| `runs/model-player/t139-playjev-v3-w30/snake/playjev/session.json` | 11828 | `26288dcc43e80bd029424ce25b5d49b04ac0a186449018df3516edd34dafd946` |
| `runs/model-player/t139-playjev-v3-w30/snake/playjev/steps.jsonl` | 154331 | `0d4787a34035a8dea3ba074ae01c6e05414ff600a39105e7a3b5a4c9874d408e` |
| `calls/**`（306 个文件，1850970 B）| — | `51c8d84748971b974f7fa571c00bba894eb9c257836b04e7333442a315ce5239` |
| `frames/**`（37 个文件，114563 B）| — | `2ab7e692f0438b533a925ac672ca3a819d2b74f2b54e76a532354490724af5d0` |
| `states/**`（27 个文件，237369 B）| — | `2db15f313e6af8040f44dca5f024f29cfa037a0295e1a84abf11bacbd3c8ccb2` |

## t139-playjev-v3-w30 / sokoban / playjev

* 目录：`runs/model-player/t139-playjev-v3-w30/sokoban/playjev`
* verdict：`PASS`（counts_as_pass=True，strict=PASS，baseline=PASS，game_side=None）
* 注入/接受后变化/rate：12 / 4 / 1.0
* 两窗对齐：3/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 5 frame(s))（matched 3/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game sokoban --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9963 --window-frames 30 --out-prefix t139-jev-v3-w30`  <- t139_results_t139-jev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game sokoban --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9964 --window-frames 90 --out-prefix t139-jev-v3-w90`  <- t139_results_t139-jev-v3-w90.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game sokoban --backend playjev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9965 --window-frames 30 --out-prefix t139-playjev-v3-w30`  <- t139_results_t139-playjev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game sokoban --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9973 --window-frames 30 --out-prefix t139-scripted-w30`  <- t139_results_t139-scripted-w30-counterev.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game sokoban --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9961 --window-frames 30 --out-prefix t139-scripted-w30`  <- t139_results_t139-scripted-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game sokoban --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9962 --window-frames 90 --out-prefix t139-scripted-w90`  <- t139_results_t139-scripted-w90.json (sweep driver)

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t139-playjev-v3-w30/sokoban/playjev/demo.png` | 151809 | `2ec30cc61afd21ff505f74c50caf290319ccb6e0c5843e8ca32a3b93b0087581` |
| `runs/model-player/t139-playjev-v3-w30/sokoban/playjev/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t139-playjev-v3-w30/sokoban/playjev/engine-game.stdout.txt` | 745 | `2820883d356605672bf26138cc499dc2592acfc1cfcaaf819323cbbd8b99379b` |
| `runs/model-player/t139-playjev-v3-w30/sokoban/playjev/filmstrip.png` | 104413 | `e6061731adec0270553f753d1a907444f27f89c0b4b6f82a090db7d03dd1b6f1` |
| `runs/model-player/t139-playjev-v3-w30/sokoban/playjev/frames.json` | 643140 | `a89047f6be63d441da6d1b04821962f86ee212e2ef9f44c57178b57837005ac2` |
| `runs/model-player/t139-playjev-v3-w30/sokoban/playjev/player.json` | 380453 | `ce9cc7d62796160acab86833e9b519d8cd2360e9f71b0cc176dc56b021a97e38` |
| `runs/model-player/t139-playjev-v3-w30/sokoban/playjev/session.json` | 12554 | `561e8b8d1116378e5d5f42ae824684afd25739c97836edbfa4b4cbc467d29b3e` |
| `runs/model-player/t139-playjev-v3-w30/sokoban/playjev/steps.jsonl` | 160927 | `212eb127bae67e37dbec2e8366c35a3764694b1019d126606916de22097d706f` |
| `calls/**`（391 个文件，4269266 B）| — | `95815c08d53ae45d39bcc6aab70f434c686b0a699ba90c463ac879b11dd58507` |
| `frames/**`（37 个文件，455461 B）| — | `36bb64734358524718c02404d8aecd7b493c10b1768415b06517e78959797702` |
| `states/**`（27 个文件，374179 B）| — | `04a24e574560c85848cbb5301710a83e72bfcb7f02ff03ef75f5c203d71bc892` |

## t139-playjev-v3-w30 / tetris / playjev

* 目录：`runs/model-player/t139-playjev-v3-w30/tetris/playjev`
* verdict：`INCONCLUSIVE`（counts_as_pass=False，strict=INCONCLUSIVE，baseline=INCONCLUSIVE，game_side=None）
* 注入/接受后变化/rate：0 / 0 / None
* 两窗对齐：3/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 4 frame(s))（matched 3/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game tetris --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9963 --window-frames 30 --out-prefix t139-jev-v3-w30`  <- t139_results_t139-jev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game tetris --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9964 --window-frames 90 --out-prefix t139-jev-v3-w90`  <- t139_results_t139-jev-v3-w90.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game tetris --backend playjev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9965 --window-frames 30 --out-prefix t139-playjev-v3-w30`  <- t139_results_t139-playjev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game tetris --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9961 --window-frames 30 --out-prefix t139-scripted-w30`  <- t139_results_t139-scripted-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game tetris --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9962 --window-frames 90 --out-prefix t139-scripted-w90`  <- t139_results_t139-scripted-w90.json (sweep driver)

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t139-playjev-v3-w30/tetris/playjev/demo.png` | 68731 | `f37f24a934741f20032811cf6babce1df3e0a3d6665d4c42df3ae41405673890` |
| `runs/model-player/t139-playjev-v3-w30/tetris/playjev/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t139-playjev-v3-w30/tetris/playjev/engine-game.stdout.txt` | 7335 | `b8b62e09e9c74152e6b7881a53709816b8c4cd0c5f0bb5127c721b5f99b5f50c` |
| `runs/model-player/t139-playjev-v3-w30/tetris/playjev/filmstrip.png` | 42823 | `b83408cf62d21d61d36bf140a2ba57fe24fe49a2e8ee597709c2118850ff0565` |
| `runs/model-player/t139-playjev-v3-w30/tetris/playjev/frames.json` | 286782 | `01175e8a42575365533e557b3e17643170c42c925ccc783b7f4c8d136383ccf1` |
| `runs/model-player/t139-playjev-v3-w30/tetris/playjev/player.json` | 259025 | `ab9225548db76990a8b2d311b9c51ea7b1e4a4711aecff261501ca54a46554f0` |
| `runs/model-player/t139-playjev-v3-w30/tetris/playjev/session.json` | 11050 | `9023ea125f38dc46461e001d9aa5687c586206f2552f811ddb9794d8e57c38bb` |
| `runs/model-player/t139-playjev-v3-w30/tetris/playjev/steps.jsonl` | 129091 | `c3582e9ad9703d8d33db4a74ab1624c51db0f0cd89d90e24f36f38ca0629b607` |
| `calls/**`（358 个文件，795286 B）| — | `72cd255ca5a820d396092f4ea9e00edfa173e60e40c7ee1ddb7310ad9715491e` |
| `frames/**`（37 个文件，188182 B）| — | `a19f86376a6a63785425028613379045ab260cfddd21b8eb2350d7b446da1be4` |
| `states/**`（27 个文件，41775 B）| — | `9c399ad28438976f7b05d6c325f93ee0db305e1eedeae49400e8208110b80f53` |

## t139-determinism-w30 / asteroids / scripted

* 目录：`runs/model-player/t139-determinism-w30/asteroids/scripted`
* verdict：`PASS`（counts_as_pass=True，strict=PASS，baseline=PASS，game_side=PASS）
* 注入/接受后变化/rate：8 / 8 / 1.0
* 两窗对齐：3/8 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 4 frame(s))（matched 3/8，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game asteroids --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9963 --window-frames 30 --out-prefix t139-jev-v3-w30`  <- t139_results_t139-jev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game asteroids --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9964 --window-frames 90 --out-prefix t139-jev-v3-w90`  <- t139_results_t139-jev-v3-w90.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game asteroids --backend playjev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9965 --window-frames 30 --out-prefix t139-playjev-v3-w30`  <- t139_results_t139-playjev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game asteroids --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9961 --window-frames 30 --out-prefix t139-scripted-w30`  <- t139_results_t139-scripted-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game asteroids --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9962 --window-frames 90 --out-prefix t139-scripted-w90`  <- t139_results_t139-scripted-w90.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game asteroids --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9967 --window-frames 30 --out-prefix t139-determinism-w30`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t139-determinism-w30/asteroids/scripted/demo.png` | 89017 | `0d4b11ca1687d43f183344a08336b14bba88a603cba5b6af5b94086129af5457` |
| `runs/model-player/t139-determinism-w30/asteroids/scripted/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t139-determinism-w30/asteroids/scripted/engine-game.stdout.txt` | 741 | `db1eb88118485c969ac34ff83462763a5e281be86e4a98b2aad9725a73acdcb8` |
| `runs/model-player/t139-determinism-w30/asteroids/scripted/filmstrip.png` | 52005 | `affb4af08355cde2b70dd8aeda8d6e285ff1df13446e303fabad57e3993c6578` |
| `runs/model-player/t139-determinism-w30/asteroids/scripted/frames.json` | 375941 | `dde60d897232dc482aeefebc1096b780dc146371c56dc39409383f49d46e95ef` |
| `runs/model-player/t139-determinism-w30/asteroids/scripted/player.json` | 20177 | `e691f3a38040bfb090dbcd11842979562c89daa83bcd15a81c6f8e911bf63b49` |
| `runs/model-player/t139-determinism-w30/asteroids/scripted/session.json` | 11264 | `e429fe970477cc92d5822b72cce29bbfcd323eb5463656d77d4670a854739d2b` |
| `runs/model-player/t139-determinism-w30/asteroids/scripted/steps.jsonl` | 104297 | `907111e076c2e3e62b72cf76eb4faa43e89fe76e8f20621f81ffbb0a7929d79d` |
| `calls/**`（528 个文件，4288650 B）| — | `38038a2881dd30cbe056d09183ecb7c8d01f881ccf040e5882675f843af82cb4` |
| `frames/**`（37 个文件，410524 B）| — | `a41325cd48d5455d0210f860061272570fb31b63c6de37b73fa60c64dc65aa55` |
| `states/**`（27 个文件，100861 B）| — | `e047023ec5e84f0a925bbd8c215afbc9194f4a6be87db9f96c9ec0ed6e496d0c` |

## t139-determinism-w30 / breakout / scripted

* 目录：`runs/model-player/t139-determinism-w30/breakout/scripted`
* verdict：`INCONCLUSIVE`（counts_as_pass=False，strict=INCONCLUSIVE，baseline=INCONCLUSIVE，game_side=INCONCLUSIVE）
* 注入/接受后变化/rate：3 / 3 / 1.0
* 两窗对齐：1/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 5 frame(s))（matched 1/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game breakout --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9963 --window-frames 30 --out-prefix t139-jev-v3-w30`  <- t139_results_t139-jev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game breakout --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9964 --window-frames 90 --out-prefix t139-jev-v3-w90`  <- t139_results_t139-jev-v3-w90.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game breakout --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9961 --window-frames 30 --out-prefix t139-scripted-w30`  <- t139_results_t139-scripted-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game breakout --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9962 --window-frames 90 --out-prefix t139-scripted-w90`  <- t139_results_t139-scripted-w90.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game breakout --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9967 --window-frames 30 --out-prefix t139-determinism-w30`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t139-determinism-w30/breakout/scripted/demo.png` | 101199 | `187876d7710499aacb08bd597421d7eb4afb9b78320058f7fd3b2e0791812ae3` |
| `runs/model-player/t139-determinism-w30/breakout/scripted/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t139-determinism-w30/breakout/scripted/engine-game.stdout.txt` | 3606 | `2142de80faaeccb21cadfc806eb3479ddeaf7e3f3171b27c69b3eca135a893ef` |
| `runs/model-player/t139-determinism-w30/breakout/scripted/filmstrip.png` | 75007 | `55629fc6f64b6f4064e83eff5e759b11c7cd4fa5ff38e36a1ae981aef1f6b379` |
| `runs/model-player/t139-determinism-w30/breakout/scripted/frames.json` | 568905 | `d9da460834f012b5f6ded2fd7b9728055a28c1f693e877f5cdf64e54277dcffe` |
| `runs/model-player/t139-determinism-w30/breakout/scripted/player.json` | 22354 | `79e8d889d84fc44e7b53bce6c8f38882eac43f8db18cceb47bd82b59f910fe85` |
| `runs/model-player/t139-determinism-w30/breakout/scripted/session.json` | 11429 | `30aa39df5731fcf97a841adbb7a87e2f0f61b64928374278738587e72740e774` |
| `runs/model-player/t139-determinism-w30/breakout/scripted/steps.jsonl` | 125670 | `6e640656c444eacb3dc8bbb5c65fee78a776df27b4aa723d6d8461df9489a6ef` |
| `calls/**`（486 个文件，2798054 B）| — | `89bd733d41a434f1ec1dbd8bcce54d08ca1e3c5819d2c460a4404668e8271f66` |
| `frames/**`（37 个文件，399872 B）| — | `48a654384e02d3a80b4b2c99336b7de2f6a845f78d54a38dffba702b39b25220` |
| `states/**`（27 个文件，148637 B）| — | `2e4149e07dea04c1a785f994545ab908b237a68126a06dfeb58d896a14f28dfe` |

## t139-determinism-w30 / pacman / scripted

* 目录：`runs/model-player/t139-determinism-w30/pacman/scripted`
* verdict：`PASS`（counts_as_pass=True，strict=PASS，baseline=PASS，game_side=PASS）
* 注入/接受后变化/rate：12 / 7 / 1.0
* 两窗对齐：1/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 5 frame(s))（matched 1/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game pacman --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9963 --window-frames 30 --out-prefix t139-jev-v3-w30`  <- t139_results_t139-jev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game pacman --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9964 --window-frames 90 --out-prefix t139-jev-v3-w90`  <- t139_results_t139-jev-v3-w90.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game pacman --backend playjev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9965 --window-frames 30 --out-prefix t139-playjev-v3-w30`  <- t139_results_t139-playjev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game pacman --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9973 --window-frames 30 --out-prefix t139-scripted-w30`  <- t139_results_t139-scripted-w30-counterev.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game pacman --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9961 --window-frames 30 --out-prefix t139-scripted-w30`  <- t139_results_t139-scripted-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game pacman --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9962 --window-frames 90 --out-prefix t139-scripted-w90`  <- t139_results_t139-scripted-w90.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game pacman --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9967 --window-frames 30 --out-prefix t139-determinism-w30`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t139-determinism-w30/pacman/scripted/demo.png` | 146478 | `b2ac36203d74153f2e14cfa946cbeb6e9f4a63bd0761e54e53fcb22702c19a8d` |
| `runs/model-player/t139-determinism-w30/pacman/scripted/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t139-determinism-w30/pacman/scripted/engine-game.stdout.txt` | 733 | `62af81429a42cd35a6e91aa5c498da6e2bff132fe94f065e91992a8f02bc7c30` |
| `runs/model-player/t139-determinism-w30/pacman/scripted/filmstrip.png` | 146874 | `889c8b55347b4e8ebb9a5c7d98015b64eac09b169105d5192898e49cda287669` |
| `runs/model-player/t139-determinism-w30/pacman/scripted/frames.json` | 583930 | `6b438e7a89e456155c287e0d155922a054c8252a6a684cff751299a9d12b500f` |
| `runs/model-player/t139-determinism-w30/pacman/scripted/player.json` | 26951 | `74dc5814183787d40381bef7b2827aff869276c0f3fe2f2fd226608e7e67ec9c` |
| `runs/model-player/t139-determinism-w30/pacman/scripted/session.json` | 12541 | `2985a82d9d49f114acb7bf9d38c075ad764e2e5301ddb5e146849a16fa29c02a` |
| `runs/model-player/t139-determinism-w30/pacman/scripted/steps.jsonl` | 143591 | `6562fe74bc6a476759564aeeb169353a2ef3b74fa3546fc872c6bb950dbb64d2` |
| `calls/**`（501 个文件，12686039 B）| — | `7ae3dabc9f3d0cda7c8f1321fe32698d94cebf7690588da7da9536f745a136bf` |
| `frames/**`（37 个文件，411185 B）| — | `386052c3b39457ccf5d174f979384cfb0303482a6271b7b8392a17bcb26fd6e6` |
| `states/**`（27 个文件，1153928 B）| — | `e03771a6eb7f72b82810da0914df325bca47e3125736509659179c2369ab0e27` |

## t139-determinism-w30 / pong / scripted

* 目录：`runs/model-player/t139-determinism-w30/pong/scripted`
* verdict：`PASS`（counts_as_pass=True，strict=PASS，baseline=PASS，game_side=PASS）
* 注入/接受后变化/rate：9 / 9 / 1.0
* 两窗对齐：1/10 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 3 frame(s))（matched 1/10，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game pong --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9963 --window-frames 30 --out-prefix t139-jev-v3-w30`  <- t139_results_t139-jev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game pong --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9964 --window-frames 90 --out-prefix t139-jev-v3-w90`  <- t139_results_t139-jev-v3-w90.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game pong --backend playjev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9965 --window-frames 30 --out-prefix t139-playjev-v3-w30`  <- t139_results_t139-playjev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game pong --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9961 --window-frames 30 --out-prefix t139-scripted-w30`  <- t139_results_t139-scripted-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game pong --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9962 --window-frames 90 --out-prefix t139-scripted-w90`  <- t139_results_t139-scripted-w90.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game pong --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9967 --window-frames 30 --out-prefix t139-determinism-w30`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t139-determinism-w30/pong/scripted/demo.png` | 63935 | `b1dfbede9dbd0b0925df4c1766fb1a504ca227f409d4c844309a5f2aad518410` |
| `runs/model-player/t139-determinism-w30/pong/scripted/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t139-determinism-w30/pong/scripted/engine-game.stdout.txt` | 4099 | `bb2744a4fa70594d9a4a9d3e6be1d88073cc67cde33ef5794901f878999003cc` |
| `runs/model-player/t139-determinism-w30/pong/scripted/filmstrip.png` | 45270 | `96110248de5d29b2e0f06635b5a6acc73ca1276809898cb27b2508d457c283b3` |
| `runs/model-player/t139-determinism-w30/pong/scripted/frames.json` | 210732 | `8f13387c9e7225650a9a6eb77fc3a29783869501f3f143ce9b7daf8e84eaec3a` |
| `runs/model-player/t139-determinism-w30/pong/scripted/player.json` | 21377 | `114ccc7a535d4ac3e0e71cd9c31cd6386aa6d68a4acdd3ad31adb2da282bb58c` |
| `runs/model-player/t139-determinism-w30/pong/scripted/session.json` | 11398 | `d59417a442ed0e6e2b5b72d3a3f931a730fb882a114145b83e788d34490e7561` |
| `runs/model-player/t139-determinism-w30/pong/scripted/steps.jsonl` | 122582 | `5b30cd0ce6baea0e54106b90eb2c4e2bd5a6f5100dd85552086a66dae44695c4` |
| `calls/**`（458 个文件，1321748 B）| — | `57371d0da8e75c4b52aabec9c7731d93ed7a017d35cafb54e4ef8698d6660cdd` |
| `frames/**`（37 个文件，162167 B）| — | `4276e8ba7632848253c3b7c07f6d91ab2064c80a40efe46d162dca40f26a66ad` |
| `states/**`（27 个文件，66578 B）| — | `7068b21820657423deb6201b06f18eb2082b728a7baaf81e75fc7eac17e55b95` |

## t139-determinism-w30 / tetris / scripted

* 目录：`runs/model-player/t139-determinism-w30/tetris/scripted`
* verdict：`PASS`（counts_as_pass=True，strict=PASS，baseline=PASS，game_side=PASS）
* 注入/接受后变化/rate：8 / 8 / 1.0
* 两窗对齐：3/8 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 2 frame(s))（matched 3/8，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game tetris --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9963 --window-frames 30 --out-prefix t139-jev-v3-w30`  <- t139_results_t139-jev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game tetris --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9964 --window-frames 90 --out-prefix t139-jev-v3-w90`  <- t139_results_t139-jev-v3-w90.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game tetris --backend playjev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9965 --window-frames 30 --out-prefix t139-playjev-v3-w30`  <- t139_results_t139-playjev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game tetris --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9961 --window-frames 30 --out-prefix t139-scripted-w30`  <- t139_results_t139-scripted-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game tetris --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9962 --window-frames 90 --out-prefix t139-scripted-w90`  <- t139_results_t139-scripted-w90.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game tetris --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9967 --window-frames 30 --out-prefix t139-determinism-w30`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t139-determinism-w30/tetris/scripted/demo.png` | 51366 | `d63646b22803d99e27d3e4c201ef7e0ecec39c44656e64e3afeeb73f502c79f5` |
| `runs/model-player/t139-determinism-w30/tetris/scripted/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t139-determinism-w30/tetris/scripted/engine-game.stdout.txt` | 5842 | `56bca4a5cfd1796faf66a1fc354b75d3b002138f41c8869b7f12c4eac25d7ef5` |
| `runs/model-player/t139-determinism-w30/tetris/scripted/filmstrip.png` | 34096 | `cd85452d53a798b699c464c46417fdb682402fee602c4cac11ccb69e3654cb38` |
| `runs/model-player/t139-determinism-w30/tetris/scripted/frames.json` | 196084 | `4c273a4ba89ba80f2c83ab29f9d6b68a741400c9d54107d6671e1d2e4472a1be` |
| `runs/model-player/t139-determinism-w30/tetris/scripted/player.json` | 20241 | `64738f055eacae113b8b426de496103b0aadf107af47126b4a0ff7f9dd61f92b` |
| `runs/model-player/t139-determinism-w30/tetris/scripted/session.json` | 11184 | `e42667d92e62650eed4a421179910128c2fc18bf3db8706f01e72f90cae7a15a` |
| `runs/model-player/t139-determinism-w30/tetris/scripted/steps.jsonl` | 86981 | `afea6932547bb9e8a969742be77b2625bb664b34f1a23845ddbdba948bed2026` |
| `calls/**`（476 个文件，1298195 B）| — | `cc966d3510b7a28bb3d948a29b003b28648bb3d43b867acb012c34763d051838` |
| `frames/**`（37 个文件，191122 B）| — | `15e868b15d7f2cea57e9eba63e39b81ca169535217c969741fbac6498f2b6c4c` |
| `states/**`（27 个文件，42520 B）| — | `5fbd86dfedd3ea1175020d316a232c9bf26ec3fcb4468874694c3842f0759691` |

## t139-determinism-w90 / asteroids / scripted

* 目录：`runs/model-player/t139-determinism-w90/asteroids/scripted`
* verdict：`PASS`（counts_as_pass=True，strict=PASS，baseline=PASS，game_side=PASS）
* 注入/接受后变化/rate：8 / 8 / 1.0
* 两窗对齐：4/8 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 3 frame(s))（matched 4/8，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game asteroids --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9963 --window-frames 30 --out-prefix t139-jev-v3-w30`  <- t139_results_t139-jev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game asteroids --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9964 --window-frames 90 --out-prefix t139-jev-v3-w90`  <- t139_results_t139-jev-v3-w90.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game asteroids --backend playjev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9965 --window-frames 30 --out-prefix t139-playjev-v3-w30`  <- t139_results_t139-playjev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game asteroids --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9961 --window-frames 30 --out-prefix t139-scripted-w30`  <- t139_results_t139-scripted-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game asteroids --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9962 --window-frames 90 --out-prefix t139-scripted-w90`  <- t139_results_t139-scripted-w90.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game asteroids --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9967 --window-frames 90 --out-prefix t139-determinism-w90`  <- t136_commands.jsonl
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game asteroids --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9968 --window-frames 90 --out-prefix t139-determinism-w90`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t139-determinism-w90/asteroids/scripted/demo.png` | 88261 | `90e60487ad8ed233d1263ffc48deef17937001ced8fd3e0946498df7207f3b48` |
| `runs/model-player/t139-determinism-w90/asteroids/scripted/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t139-determinism-w90/asteroids/scripted/engine-game.stdout.txt` | 741 | `028b6aeb5d058c05ce18b3d888814ce82d5745f4972ef9b674d026449143e564` |
| `runs/model-player/t139-determinism-w90/asteroids/scripted/filmstrip.png` | 49414 | `a72603780c6bf0d13fa7ecd3357937a79c766ca8f584c3225c4a4fe058d54e63` |
| `runs/model-player/t139-determinism-w90/asteroids/scripted/frames.json` | 371240 | `d0172b8434d784d4366dbc250a7259a0d93461f70fb226dca8a4a8e5191cf849` |
| `runs/model-player/t139-determinism-w90/asteroids/scripted/player.json` | 20180 | `f1b525caf3dbdb49dbb511d9e88c6b91103503e2bc49f50e53c8135160c265e8` |
| `runs/model-player/t139-determinism-w90/asteroids/scripted/session.json` | 11266 | `70c256a9b861846507d43f4490486f74c0ea517db0d5e694b68a46fd17aa1419` |
| `runs/model-player/t139-determinism-w90/asteroids/scripted/steps.jsonl` | 101551 | `8dfb66f6a4dff044c3e4d664c2232aa7b28486d6912d25ee53e5f910aca76edc` |
| `calls/**`（682 个文件，3044145 B）| — | `739500b7e461cda37fe928eabdf6d8e404b647bcc3803ff90f83732fa046092b` |
| `frames/**`（25 个文件，260248 B）| — | `576c0e826d47ce118d942d05bd477b699254a92b51da2f1fd6ac2dcde6a80679` |
| `states/**`（19 个文件，55695 B）| — | `57d772ff97fd0a2425b24d88ef8f8b17b8ca4da050a19ab255ebbda1ccac365e` |

## t139-determinism-w90 / breakout / scripted

* 目录：`runs/model-player/t139-determinism-w90/breakout/scripted`
* verdict：`FAIL`（counts_as_pass=False，strict=FAIL，baseline=INCONCLUSIVE，game_side=FAIL）
* 注入/接受后变化/rate：3 / 2 / 0.6667
* 两窗对齐：1/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 4 frame(s))（matched 1/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game breakout --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9963 --window-frames 30 --out-prefix t139-jev-v3-w30`  <- t139_results_t139-jev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game breakout --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9964 --window-frames 90 --out-prefix t139-jev-v3-w90`  <- t139_results_t139-jev-v3-w90.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game breakout --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9961 --window-frames 30 --out-prefix t139-scripted-w30`  <- t139_results_t139-scripted-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game breakout --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9962 --window-frames 90 --out-prefix t139-scripted-w90`  <- t139_results_t139-scripted-w90.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game breakout --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9967 --window-frames 90 --out-prefix t139-determinism-w90`  <- t136_commands.jsonl
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game breakout --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9968 --window-frames 90 --out-prefix t139-determinism-w90`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t139-determinism-w90/breakout/scripted/demo.png` | 93251 | `30358170c4283f4c2261c40f53a7b44dfb9383d4b4c0416ee42796b7d982b2a5` |
| `runs/model-player/t139-determinism-w90/breakout/scripted/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t139-determinism-w90/breakout/scripted/engine-game.stdout.txt` | 7837 | `f059aed1eb16167baeb8357e4edf58b3b5c6ab03618f21b0d108e87b29969111` |
| `runs/model-player/t139-determinism-w90/breakout/scripted/filmstrip.png` | 71759 | `ffbebf89698b2d3a8854146f80116f166fe40026af01966ea4cb62e45e65b943` |
| `runs/model-player/t139-determinism-w90/breakout/scripted/frames.json` | 504031 | `c137a68620941289fe4fa3e761ad9ae61e3a45a8cee9d4373da81f5795defcc7` |
| `runs/model-player/t139-determinism-w90/breakout/scripted/player.json` | 23264 | `ca797fb0452c830cca8dd50198234b41ae8436de22dc738063f7410ebf2ebb40` |
| `runs/model-player/t139-determinism-w90/breakout/scripted/session.json` | 11431 | `9c386f5aa7e966541bb6610527179126f5f6e739d397505acd2bb21472b89120` |
| `runs/model-player/t139-determinism-w90/breakout/scripted/steps.jsonl` | 132114 | `7cbba06a7285e0b138be2713889925e3f6032c085b414d6221b5b068e3624f8e` |
| `calls/**`（709 个文件，4993600 B）| — | `27e044b33ba5b314747198a1ba8175d655fc7f8e1eb0f990e4606f6e44246fd3` |
| `frames/**`（37 个文件，351154 B）| — | `a3034f06a9b308f9a1707aaa403f45e2c9a324ed8e31dfffb1f6234d2d67da7c` |
| `states/**`（27 个文件，148240 B）| — | `f38a903ebc87dcb5492968f2b839158f94aa671dcacd5ed6060cbc52cecfde9d` |

## t139-determinism-w90 / pacman / scripted

* 目录：`runs/model-player/t139-determinism-w90/pacman/scripted`
* verdict：`PASS`（counts_as_pass=True，strict=PASS，baseline=PASS，game_side=PASS）
* 注入/接受后变化/rate：12 / 7 / 1.0
* 两窗对齐：2/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 3 frame(s))（matched 2/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game pacman --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9963 --window-frames 30 --out-prefix t139-jev-v3-w30`  <- t139_results_t139-jev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game pacman --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9964 --window-frames 90 --out-prefix t139-jev-v3-w90`  <- t139_results_t139-jev-v3-w90.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game pacman --backend playjev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9965 --window-frames 30 --out-prefix t139-playjev-v3-w30`  <- t139_results_t139-playjev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game pacman --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9973 --window-frames 30 --out-prefix t139-scripted-w30`  <- t139_results_t139-scripted-w30-counterev.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game pacman --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9961 --window-frames 30 --out-prefix t139-scripted-w30`  <- t139_results_t139-scripted-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game pacman --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9962 --window-frames 90 --out-prefix t139-scripted-w90`  <- t139_results_t139-scripted-w90.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game pacman --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9967 --window-frames 90 --out-prefix t139-determinism-w90`  <- t136_commands.jsonl
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game pacman --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9968 --window-frames 90 --out-prefix t139-determinism-w90`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t139-determinism-w90/pacman/scripted/demo.png` | 146478 | `b2ac36203d74153f2e14cfa946cbeb6e9f4a63bd0761e54e53fcb22702c19a8d` |
| `runs/model-player/t139-determinism-w90/pacman/scripted/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t139-determinism-w90/pacman/scripted/engine-game.stdout.txt` | 733 | `c61debeae349a7b9b69c0619319ef38c1ecbc2e5a890fd31d0a3495d61dee3c4` |
| `runs/model-player/t139-determinism-w90/pacman/scripted/filmstrip.png` | 146874 | `889c8b55347b4e8ebb9a5c7d98015b64eac09b169105d5192898e49cda287669` |
| `runs/model-player/t139-determinism-w90/pacman/scripted/frames.json` | 583947 | `136da22eb7234f113e30cd677ae9f641d26765460cb99551fba5299727217566` |
| `runs/model-player/t139-determinism-w90/pacman/scripted/player.json` | 26954 | `8eb94131026654d8b65db55efede4518783512a8d530ae3c3138943ff09474d0` |
| `runs/model-player/t139-determinism-w90/pacman/scripted/session.json` | 12543 | `262c707737897c0f3be3cb655f0fcef46fdad0cf3f50674512568f6c565c0cf3` |
| `runs/model-player/t139-determinism-w90/pacman/scripted/steps.jsonl` | 143640 | `cdefc95327c269cf0029e2e2aa3835fc0ff56dd1fc402a0f5d98d833ba787bdb` |
| `calls/**`（910 个文件，27551662 B）| — | `47e9ee677450b6cbf46f2e6f65752079d12a52e4195938e8e24a419579131b83` |
| `frames/**`（37 个文件，411185 B）| — | `d25a2fc6f764683b7a91ca44eb29b03250282e5721ffde9a330bd726de026ae7` |
| `states/**`（27 个文件，1153945 B）| — | `e79de5f5601fb31af60d0ab2231ab6986270e27ccd0de01b92379ebc1c7b08e4` |

## t139-determinism-w90 / pong / scripted

* 目录：`runs/model-player/t139-determinism-w90/pong/scripted`
* verdict：`PASS`（counts_as_pass=True，strict=PASS，baseline=PASS，game_side=PASS）
* 注入/接受后变化/rate：8 / 8 / 1.0
* 两窗对齐：4/8 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 3 frame(s))（matched 4/8，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game pong --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9963 --window-frames 30 --out-prefix t139-jev-v3-w30`  <- t139_results_t139-jev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game pong --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9964 --window-frames 90 --out-prefix t139-jev-v3-w90`  <- t139_results_t139-jev-v3-w90.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game pong --backend playjev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9965 --window-frames 30 --out-prefix t139-playjev-v3-w30`  <- t139_results_t139-playjev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game pong --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9961 --window-frames 30 --out-prefix t139-scripted-w30`  <- t139_results_t139-scripted-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game pong --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9962 --window-frames 90 --out-prefix t139-scripted-w90`  <- t139_results_t139-scripted-w90.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game pong --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9967 --window-frames 90 --out-prefix t139-determinism-w90`  <- t136_commands.jsonl
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game pong --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9968 --window-frames 90 --out-prefix t139-determinism-w90`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t139-determinism-w90/pong/scripted/demo.png` | 52196 | `7c7890eb1bd75fe5878aa0798d17ff3f6bfa1d1435c8a72411415d63f7e3c608` |
| `runs/model-player/t139-determinism-w90/pong/scripted/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t139-determinism-w90/pong/scripted/engine-game.stdout.txt` | 3579 | `b8ee114909ceafd444f3030ead94567a5a560ee5827efccf609acf874c82a2f8` |
| `runs/model-player/t139-determinism-w90/pong/scripted/filmstrip.png` | 34715 | `961cd5d9c616739dd28485f7df81172fbf0d8e5183eb025014f01c744bccd1b2` |
| `runs/model-player/t139-determinism-w90/pong/scripted/frames.json` | 178767 | `11c1d8421b1f0c06e9a053becaa3fdfcbd596137170a5ca5493fa6223b21b35c` |
| `runs/model-player/t139-determinism-w90/pong/scripted/player.json` | 20036 | `ec34dab6b1ed409c37e1dd0873423ae8caca03f09935b0b59761526e7143131d` |
| `runs/model-player/t139-determinism-w90/pong/scripted/session.json` | 11398 | `50291a423ca374b42a2e4756a1a568af6b8e0e94b48c7d9797a4a2e2cb28377d` |
| `runs/model-player/t139-determinism-w90/pong/scripted/steps.jsonl` | 94163 | `49d6d925f6b707fd06dcb42817b01c38f0c47dac72ad3d31d7bf86db476b6e95` |
| `calls/**`（935 个文件，2883957 B）| — | `8eab8d2931d778d9d07d2caa0ded426a70a9eeb5cb148599cd2cdf7f7211a9b7` |
| `frames/**`（37 个文件，210561 B）| — | `08de6a9a7a5a0b2b27f3ed1d346a8c4a74a9e7bbf02c0c6f8d2cd774dc28ab6e` |
| `states/**`（27 个文件，66224 B）| — | `3f5a2a1c41c6acf8d40b4fe4f73882d1832024d553b5e72528a2c2239d6b533f` |

## t139-determinism-w90 / tetris / scripted

* 目录：`runs/model-player/t139-determinism-w90/tetris/scripted`
* verdict：`PASS`（counts_as_pass=True，strict=PASS，baseline=PASS，game_side=PASS）
* 注入/接受后变化/rate：8 / 8 / 1.0
* 两窗对齐：3/8 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 4 frame(s))（matched 3/8，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game tetris --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9963 --window-frames 30 --out-prefix t139-jev-v3-w30`  <- t139_results_t139-jev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game tetris --backend jev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9964 --window-frames 90 --out-prefix t139-jev-v3-w90`  <- t139_results_t139-jev-v3-w90.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game tetris --backend playjev --player model --variant V3 --image-form full --change-margin strict --steps 12 --port 9965 --window-frames 30 --out-prefix t139-playjev-v3-w30`  <- t139_results_t139-playjev-v3-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game tetris --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9961 --window-frames 30 --out-prefix t139-scripted-w30`  <- t139_results_t139-scripted-w30.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game tetris --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9962 --window-frames 90 --out-prefix t139-scripted-w90`  <- t139_results_t139-scripted-w90.json (sweep driver)
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game tetris --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9967 --window-frames 90 --out-prefix t139-determinism-w90`  <- t136_commands.jsonl
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game tetris --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9968 --window-frames 90 --out-prefix t139-determinism-w90`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t139-determinism-w90/tetris/scripted/demo.png` | 51366 | `d63646b22803d99e27d3e4c201ef7e0ecec39c44656e64e3afeeb73f502c79f5` |
| `runs/model-player/t139-determinism-w90/tetris/scripted/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t139-determinism-w90/tetris/scripted/engine-game.stdout.txt` | 6804 | `0ed5a4f27ec10d61c43718b0a6865a6a3d0657db92509f2f3b44c10247e46ae6` |
| `runs/model-player/t139-determinism-w90/tetris/scripted/filmstrip.png` | 34096 | `cd85452d53a798b699c464c46417fdb682402fee602c4cac11ccb69e3654cb38` |
| `runs/model-player/t139-determinism-w90/tetris/scripted/frames.json` | 196098 | `dda7610c63a113c2c6b76005e3c18c24ce07d01aceb9225d4b6f50ce441e252a` |
| `runs/model-player/t139-determinism-w90/tetris/scripted/player.json` | 20241 | `a77ada3bff5afcfbd9d884897ed73d83e109397c5dde737165b8deb19398bfb4` |
| `runs/model-player/t139-determinism-w90/tetris/scripted/session.json` | 11181 | `380ce8b3f2354a72bbab86a2c5f0614f9161086654935ffd60cb1280f4ebe04e` |
| `runs/model-player/t139-determinism-w90/tetris/scripted/steps.jsonl` | 87016 | `2cc1262d9b5c1ae665fc89f81dcd837c5c08f072259473cf7474ce00577a8b0d` |
| `calls/**`（965 个文件，2384356 B）| — | `13d19463cddec185c128522f26002c62faef429d9bcbaeac17d2290cf6235e00` |
| `frames/**`（37 个文件，190551 B）| — | `66ef005d51cec9d5e508b62f66cfb7e74cca8ea8a22edf69fe67df3ce0ebb850` |
| `states/**`（27 个文件，49743 B）| — | `f5ed07fe492f8a957f61837671ca2fed4b93c69e418d528bdf31349bc41e79b8` |
