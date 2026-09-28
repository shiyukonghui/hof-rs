# ARTIFACTS-TASK-140 — 关键产物清单（路径 + sha256 + 大小 + 生成命令）

> 为什么入库：`runs/**` 被 `.gitignore` 忽略（第 12 行 `runs/`、第 43 行
> 为什么入库：`runs/**` 被 `.gitignore` 忽略（第 12 行 `runs/`、第 43 行
> `godot-mcp/runs/`），报告引用的每个 run 产物只存在于本机。本文件把**关键产物**
> 的 sha256 / 大小 / 生成命令**提交进仓**，使结论在 `runs/**` 不入库的前提下仍可事后核验。
>
> 复算：`certutil -hashfile <path> SHA256`，或重跑本清单的生成器
> （命令见本文件表头的 §复算）。

* 生成时刻：`2026-09-28T09:41:45`
* run 目录数：**115**；索引文件数：**921**
* 复算命令：`D:\Anaconda\python.exe tools\playtest_artifact_index.py --task TASK-140 --roots t140-prefix4-w90-r1 t140-postfix4-w90-r1 t140-postfix4-w90-r2 t140-postfix4-w90-r3 t140-scripted-w90-r1 t140-scripted-w90-r2 t140-jev-v3-w90-r1 t140-jev-v3-w90-r2 t140-playjev-v3-w90-r1 t140-playjev-v3-w90-r2 t140-w30-demo t140-respawn-demo F:\moonbit-hof-rs\godot-mcp\runs\model-player\_index\ARTIFACTS-TASK-140.json F:\moonbit-hof-rs\godot-mcp\runs\model-player\_index\ARTIFACTS-TASK-140.md`

## t140-prefix4-w90-r1 / asteroids / scripted

* 目录：`runs/model-player/t140-prefix4-w90-r1/asteroids/scripted`
* verdict：`PASS`（counts_as_pass=True，strict=PASS，baseline=PASS，game_side=PASS）
* 档位+轮次：`PASS @w90 r1`（window=90，round=1，reporting=90，at_reporting_window=True，reporting_state=ok）
* 注入/接受后变化/rate：8 / 8 / 1.0
* 两窗对齐：0/8 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 3 frame(s))（matched 0/8，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:/Anaconda/python.exe runs/model-player/_scripts/t140_sweep.py --arm scripted --window 90 --round 1 --port-base 9977 --prefix t140-prefix4-w90-r1 asteroids frogger bomberman flappy`  <- t136_commands.jsonl
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game asteroids --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9977 --window-frames 90 --round 1 --change-margin strict --out-prefix t140-prefix4-w90-r1`  <- t136_commands.jsonl
  * `D:/Anaconda/python.exe runs/model-player/_scripts/t140_sha.py runs/model-player/t140-prefix4-w90-r1/frogger/scripted/frames/002_01_before.png runs/model-player/t140-prefix4-w90-r1/frogger/scripted/frames/004_01_after.png runs/model-player/t140-postfix4-w90-r2/frogger/scripted/frames/002_01_before.png runs/model-player/t140-postfix4-w90-r2/frogger/scripted/frames/004_01_after.png runs/model-player/t140-prefix4-w90-r1/bomberman/scripted/frames/013_04_after.png runs/model-player/t140-postfix4-w90-r3/bomberman/scripted/frames/004_01_after.png runs/model-player/t140-prefix4-w90-r1/flappy/scripted/frames/002_01_before.png runs/model-player/t140-postfix4-w90-r2/flappy/scripted/frames/002_01_before.png runs/model-player/t139-jev-v3-w90/asteroids/jev/frames/016_05_after.png runs/model-player/t139-jev-v3-w90/asteroids/jev/frames/037_12_after.png`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t140-prefix4-w90-r1/asteroids/scripted/demo.png` | 87970 | `5c134f48ea3feaea3ec9b8e51268215a3227a10ae7301c66ffa47f57bd56ba97` |
| `runs/model-player/t140-prefix4-w90-r1/asteroids/scripted/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t140-prefix4-w90-r1/asteroids/scripted/engine-game.stdout.txt` | 741 | `769cc75548e8812cf05e2d6fd969e1002c927ccf4d8b271ab0bf62550c486206` |
| `runs/model-player/t140-prefix4-w90-r1/asteroids/scripted/filmstrip.png` | 49044 | `1f70454363e226aebce76096d96ec26d0d96e78236e7d39b493f9f4deffdac71` |
| `runs/model-player/t140-prefix4-w90-r1/asteroids/scripted/frames.json` | 370597 | `db53d572f6b18c5bd50c8ebe634378ec3b12371621febbd1d861894fa72acfdd` |
| `runs/model-player/t140-prefix4-w90-r1/asteroids/scripted/player.json` | 22504 | `740b364e89d7deee711872558c71e705cfd6ef0cc1ff654ebfed5d5f9e908c17` |
| `runs/model-player/t140-prefix4-w90-r1/asteroids/scripted/session.json` | 12187 | `e70d327039ca26c1ae9fdf6a2afef90bd638e7aa129e0c1e5773a9c1dde60a9c` |
| `runs/model-player/t140-prefix4-w90-r1/asteroids/scripted/steps.jsonl` | 100970 | `0f6ce9c199e87498d44e65a8dfab58764269ad00a46ec0d39fe4c5deffad55b6` |
| `calls/**`（581 个文件，1903649 B）| — | `4341befb03a4c7501a15cdeaccb63492a27d6d1314908421c25efff41a231c36` |
| `frames/**`（25 个文件，259791 B）| — | `3a670d11ccd6f83b3414c5d7db8e9e911d9b557e7ab41d9ff5f68f747a150d27` |
| `states/**`（19 个文件，55469 B）| — | `8dcc3f75f96f0909684cf56f1542b1f7cbff8992dba402266298d1386b93f9c6` |

## t140-prefix4-w90-r1 / bomberman / scripted

* 目录：`runs/model-player/t140-prefix4-w90-r1/bomberman/scripted`
* verdict：`INCONCLUSIVE`（counts_as_pass=False，strict=INCONCLUSIVE，baseline=INCONCLUSIVE，game_side=FAIL）
* 档位+轮次：`INCONCLUSIVE @w90 r1`（window=90，round=1，reporting=90，at_reporting_window=True，reporting_state=ok）
* 注入/接受后变化/rate：12 / 6 / 0.6667
* 两窗对齐：3/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 3 frame(s))（matched 3/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:/Anaconda/python.exe runs/model-player/_scripts/t140_sweep.py --arm scripted --window 90 --round 1 --port-base 9977 --prefix t140-prefix4-w90-r1 asteroids frogger bomberman flappy`  <- t136_commands.jsonl
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game bomberman --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9977 --window-frames 90 --round 1 --change-margin strict --out-prefix t140-prefix4-w90-r1`  <- t136_commands.jsonl
  * `D:/Anaconda/python.exe runs/model-player/_scripts/t140_sha.py runs/model-player/t140-prefix4-w90-r1/frogger/scripted/frames/002_01_before.png runs/model-player/t140-prefix4-w90-r1/frogger/scripted/frames/004_01_after.png runs/model-player/t140-postfix4-w90-r2/frogger/scripted/frames/002_01_before.png runs/model-player/t140-postfix4-w90-r2/frogger/scripted/frames/004_01_after.png runs/model-player/t140-prefix4-w90-r1/bomberman/scripted/frames/013_04_after.png runs/model-player/t140-postfix4-w90-r3/bomberman/scripted/frames/004_01_after.png runs/model-player/t140-prefix4-w90-r1/flappy/scripted/frames/002_01_before.png runs/model-player/t140-postfix4-w90-r2/flappy/scripted/frames/002_01_before.png runs/model-player/t139-jev-v3-w90/asteroids/jev/frames/016_05_after.png runs/model-player/t139-jev-v3-w90/asteroids/jev/frames/037_12_after.png`  <- t136_commands.jsonl
  * `D:/Anaconda/python.exe runs/model-player/_scripts/t140_sha.py runs/model-player/t140-postfix4-w90-r3/bomberman/scripted/frames/007_02_after.png runs/model-player/t140-prefix4-w90-r1/bomberman/scripted/frames/010_03_after.png runs/model-player/t140-prefix4-w90-r1/bomberman/scripted/frames/007_02_after.png`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t140-prefix4-w90-r1/bomberman/scripted/demo.png` | 154435 | `d4db95906fc39923d9cf85540d7e08b7969b2b0f75e597a919249039c0418dd5` |
| `runs/model-player/t140-prefix4-w90-r1/bomberman/scripted/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t140-prefix4-w90-r1/bomberman/scripted/engine-game.stdout.txt` | 775 | `4d3d6e4ef88e7cef200f2adf89f74a12223bbe29d21825a721bf3c7ed7b31773` |
| `runs/model-player/t140-prefix4-w90-r1/bomberman/scripted/filmstrip.png` | 143686 | `c1cd831d3cc1505bb40238b3ba49f6c44ebe377dc5d20724aea25859247050c6` |
| `runs/model-player/t140-prefix4-w90-r1/bomberman/scripted/frames.json` | 512072 | `bc3c01b7528d1a3b74beb3c245bd21574baced3deb16766ef6ce87c7ace2d47b` |
| `runs/model-player/t140-prefix4-w90-r1/bomberman/scripted/player.json` | 28522 | `fd587125fecc11c8cfee3dedf902a880b8bb7a096c2378bdecb6365ab3f4f8d9` |
| `runs/model-player/t140-prefix4-w90-r1/bomberman/scripted/session.json` | 12298 | `0d6ec42558ceaff5107709347154fa3b3eac5e63f8d8a1074aba8954605263a1` |
| `runs/model-player/t140-prefix4-w90-r1/bomberman/scripted/steps.jsonl` | 143006 | `00bb25c401ec2458cbd290b09a8e96f31a9c17350e1c07781a397317da5d4865` |
| `calls/**`（783 个文件，13965028 B）| — | `f4a5f2d7fa85af72bcc7a860bff4f691529c74235e18ffeeee36d9412f00f719` |
| `frames/**`（37 个文件，357119 B）| — | `b7bf78ec705205b3fb1e7c9145c2394ec8ecce2eed04661f8c82ed5148a3f4e1` |
| `states/**`（27 个文件，600583 B）| — | `d54e307df9643c9eb7ed17014d5aaa47a6f0646df0ab34ec236ba569aa7dd0ad` |

## t140-prefix4-w90-r1 / flappy / scripted

* 目录：`runs/model-player/t140-prefix4-w90-r1/flappy/scripted`
* verdict：`INCONCLUSIVE`（counts_as_pass=False，strict=INCONCLUSIVE，baseline=INCONCLUSIVE，game_side=FAIL）
* 档位+轮次：`INCONCLUSIVE @w90 r1`（window=90，round=1，reporting=90，at_reporting_window=True，reporting_state=ok）
* 注入/接受后变化/rate：12 / 1 / 0.0833
* 两窗对齐：4/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 3 frame(s))（matched 4/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:/Anaconda/python.exe runs/model-player/_scripts/t140_sweep.py --arm scripted --window 90 --round 1 --port-base 9977 --prefix t140-prefix4-w90-r1 asteroids frogger bomberman flappy`  <- t136_commands.jsonl
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game flappy --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9977 --window-frames 90 --round 1 --change-margin strict --out-prefix t140-prefix4-w90-r1`  <- t136_commands.jsonl
  * `D:/Anaconda/python.exe runs/model-player/_scripts/t140_steps.py runs/model-player/t140-prefix4-w90-r1/flappy/scripted/steps.jsonl`  <- t136_commands.jsonl
  * `D:/Anaconda/python.exe runs/model-player/_scripts/t140_sha.py runs/model-player/t140-prefix4-w90-r1/frogger/scripted/frames/002_01_before.png runs/model-player/t140-prefix4-w90-r1/frogger/scripted/frames/004_01_after.png runs/model-player/t140-postfix4-w90-r2/frogger/scripted/frames/002_01_before.png runs/model-player/t140-postfix4-w90-r2/frogger/scripted/frames/004_01_after.png runs/model-player/t140-prefix4-w90-r1/bomberman/scripted/frames/013_04_after.png runs/model-player/t140-postfix4-w90-r3/bomberman/scripted/frames/004_01_after.png runs/model-player/t140-prefix4-w90-r1/flappy/scripted/frames/002_01_before.png runs/model-player/t140-postfix4-w90-r2/flappy/scripted/frames/002_01_before.png runs/model-player/t139-jev-v3-w90/asteroids/jev/frames/016_05_after.png runs/model-player/t139-jev-v3-w90/asteroids/jev/frames/037_12_after.png`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t140-prefix4-w90-r1/flappy/scripted/demo.png` | 97895 | `68904e5f6fdcb966de5812afa3c04682bbf26f4e347ba4aca30a6d87a32cff6b` |
| `runs/model-player/t140-prefix4-w90-r1/flappy/scripted/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t140-prefix4-w90-r1/flappy/scripted/engine-game.stdout.txt` | 744 | `9b5d2f1c0a597b8c39f1abedcf7e60362e6abf09ad1e97e625b18f8abb94b99d` |
| `runs/model-player/t140-prefix4-w90-r1/flappy/scripted/filmstrip.png` | 62706 | `ae8ef0baf441cc641d717f76f71d258e5f31301a4ba3d2d5d4f6595f1e320ce9` |
| `runs/model-player/t140-prefix4-w90-r1/flappy/scripted/frames.json` | 474420 | `87c442a547c925e2cb4ed0211bf5df66a36509eebd4036063faf6497cd159d73` |
| `runs/model-player/t140-prefix4-w90-r1/flappy/scripted/player.json` | 26586 | `49a207db77b69beea5c98e27e9b3adb44fa9a333b3f6631e4138ee2d54668615` |
| `runs/model-player/t140-prefix4-w90-r1/flappy/scripted/session.json` | 12139 | `3612ad4117788db096ba3215b0d5730612c3716ba36ac515330eab7ab406cf6e` |
| `runs/model-player/t140-prefix4-w90-r1/flappy/scripted/steps.jsonl` | 128392 | `45c6d41f8fe72569d42f26df1c2c8a9a373355f9419ad9a53ea3ed1f49cc3596` |
| `calls/**`（870 个文件，2688246 B）| — | `68a8dc1d66f90594af8953d566db64296d4f70d078bb135fe2192d7617e3e1d5` |
| `frames/**`（37 个文件，329115 B）| — | `cf9dc85128645d12646a5b90101bec5c0a3afd1dcbb17e0ebd9c5bc0cd336aa3` |
| `states/**`（27 个文件，77155 B）| — | `f65a7a375f4813753cb91d6b671bbf1738ad935ef5b9935a278d35b9c97c251a` |

## t140-prefix4-w90-r1 / frogger / scripted

* 目录：`runs/model-player/t140-prefix4-w90-r1/frogger/scripted`
* verdict：`INCONCLUSIVE`（counts_as_pass=False，strict=INCONCLUSIVE，baseline=INCONCLUSIVE，game_side=INCONCLUSIVE）
* 档位+轮次：`INCONCLUSIVE @w90 r1`（window=90，round=1，reporting=90，at_reporting_window=True，reporting_state=ok）
* 注入/接受后变化/rate：1 / 1 / 1.0
* 两窗对齐：1/1 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 0 frame(s))（matched 1/1，all_matched=True）
* ack 缺失步数：0
* 生成命令：
  * `D:/Anaconda/python.exe runs/model-player/_scripts/t140_sweep.py --arm scripted --window 90 --round 1 --port-base 9977 --prefix t140-prefix4-w90-r1 asteroids frogger bomberman flappy`  <- t136_commands.jsonl
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game frogger --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9977 --window-frames 90 --round 1 --change-margin strict --out-prefix t140-prefix4-w90-r1`  <- t136_commands.jsonl
  * `D:/Anaconda/python.exe runs/model-player/_scripts/t139_anchors.py t140-prefix4-w90-r1 frogger scripted 1 2 3`  <- t136_commands.jsonl
  * `D:/Anaconda/python.exe runs/model-player/_scripts/t140_sha.py runs/model-player/t140-prefix4-w90-r1/frogger/scripted/frames/002_01_before.png runs/model-player/t140-prefix4-w90-r1/frogger/scripted/frames/004_01_after.png runs/model-player/t140-postfix4-w90-r2/frogger/scripted/frames/002_01_before.png runs/model-player/t140-postfix4-w90-r2/frogger/scripted/frames/004_01_after.png runs/model-player/t140-prefix4-w90-r1/bomberman/scripted/frames/013_04_after.png runs/model-player/t140-postfix4-w90-r3/bomberman/scripted/frames/004_01_after.png runs/model-player/t140-prefix4-w90-r1/flappy/scripted/frames/002_01_before.png runs/model-player/t140-postfix4-w90-r2/flappy/scripted/frames/002_01_before.png runs/model-player/t139-jev-v3-w90/asteroids/jev/frames/016_05_after.png runs/model-player/t139-jev-v3-w90/asteroids/jev/frames/037_12_after.png`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t140-prefix4-w90-r1/frogger/scripted/demo.png` | 15281 | `8fdec9ae10fdf45f61ef6aebc6726486492e194502b90f155db542222f430881` |
| `runs/model-player/t140-prefix4-w90-r1/frogger/scripted/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t140-prefix4-w90-r1/frogger/scripted/engine-game.stdout.txt` | 748 | `4be55242805147c1e1e17e771aee6df9348a5e1f8a67d55ac6eed5428f1d5ec0` |
| `runs/model-player/t140-prefix4-w90-r1/frogger/scripted/filmstrip.png` | 13847 | `41a1abe17bb8745049b0c731ffc6e75789fdeac125e14be700cf546557e0b969` |
| `runs/model-player/t140-prefix4-w90-r1/frogger/scripted/frames.json` | 63860 | `858888269db321cf23210d0f4f87d554e96217edb7c95a792a4aa0431c8c7741` |
| `runs/model-player/t140-prefix4-w90-r1/frogger/scripted/player.json` | 18806 | `d1cb119365fab99b02b6182b5a0a968ea707da24e53dbc4242561152246a3eec` |
| `runs/model-player/t140-prefix4-w90-r1/frogger/scripted/session.json` | 12089 | `0ceac7910c89c6a2ad4b99c376955aa65ad937025520e2cdf7ff3b18423055b8` |
| `runs/model-player/t140-prefix4-w90-r1/frogger/scripted/steps.jsonl` | 10857 | `4f180baeb047ca99007deb23230e1f1ac5a9a84d08e713a11a82147522d6fe36` |
| `calls/**`（77 个文件，363151 B）| — | `d982c6c09b0c83a6c8f21e421619bc2a31f909ab66ed3d64fca6ed7028d1f75f` |
| `frames/**`（4 个文件，45009 B）| — | `5af234e2666a51ebc002d5a31fcde758167a7a8cffcabb265a87e6e147f8edaa` |
| `states/**`（5 个文件，21032 B）| — | `55da4d361b42303d36016b4cadf6e2c29690a63b5ee7f785f1853b506d7b52ce` |

## t140-postfix4-w90-r1 / asteroids / scripted

* 目录：`runs/model-player/t140-postfix4-w90-r1/asteroids/scripted`
* verdict：`PASS`（counts_as_pass=True，strict=PASS，baseline=PASS，game_side=PASS）
* 档位+轮次：`PASS @w90 r1`（window=90，round=1，reporting=90，at_reporting_window=True，reporting_state=ok）
* 注入/接受后变化/rate：8 / 8 / 1.0
* 两窗对齐：5/8 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 1 frame(s))（matched 5/8，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:/Anaconda/python.exe runs/model-player/_scripts/t140_sweep.py --arm scripted --window 90 --round 1 --port-base 9978 --prefix t140-postfix4-w90-r1 asteroids frogger bomberman flappy`  <- t136_commands.jsonl
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game asteroids --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9978 --window-frames 90 --round 1 --change-margin strict --out-prefix t140-postfix4-w90-r1`  <- t136_commands.jsonl
  * `D:/Anaconda/python.exe runs/model-player/_scripts/t140_steps.py runs/model-player/t140-postfix4-w90-r1/asteroids/scripted/steps.jsonl`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t140-postfix4-w90-r1/asteroids/scripted/demo.png` | 87875 | `e6727c68421ad6bb3c702f2469f0a2d2add21f04cfabcc5aee12b88f3e04ed0c` |
| `runs/model-player/t140-postfix4-w90-r1/asteroids/scripted/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t140-postfix4-w90-r1/asteroids/scripted/engine-game.stdout.txt` | 741 | `547aa0d78f5afd57f9a5b811644b1e926517b71e0f5a14c4ca41d02f368f084e` |
| `runs/model-player/t140-postfix4-w90-r1/asteroids/scripted/filmstrip.png` | 48477 | `2635e5de1d416918657bb3683ddb42974b3b8db7a69af230f5c4deb3348c94ec` |
| `runs/model-player/t140-postfix4-w90-r1/asteroids/scripted/frames.json` | 370583 | `a0e60fa1facdfaf8bad0b448d80238d1240f8c200ad902e7cdb7f40d391407ff` |
| `runs/model-player/t140-postfix4-w90-r1/asteroids/scripted/player.json` | 22494 | `1b5cad6be0fa4ead5385a8d9026589b684fd4f8098c859ea0599e6472496067e` |
| `runs/model-player/t140-postfix4-w90-r1/asteroids/scripted/session.json` | 12189 | `bb8b4d01b39c26fa2b8b426bf82bb1168647432cb407be6e6c32dae3ae023ea0` |
| `runs/model-player/t140-postfix4-w90-r1/asteroids/scripted/steps.jsonl` | 100569 | `24da2ee0a2f1fd8f1457e23e77be7f1dcd4d0ea1a8ef5b5fc5a06fc6f731e920` |
| `calls/**`（939 个文件，3119127 B）| — | `fef03c43a054b99bf23a4e914d567e231655be2498c57d75d8bb4b08d3660927` |
| `frames/**`（25 个文件，259775 B）| — | `e23dc2a51d8741b951076f52202755eb0c23157a3280d291858880642c68a9ce` |
| `states/**`（19 个文件，58849 B）| — | `849a8c26ee3616b530c89af7d04f920f6718a740184e4fa2c77046557782452f` |

## t140-postfix4-w90-r1 / bomberman / scripted

* 目录：`runs/model-player/t140-postfix4-w90-r1/bomberman/scripted`
* verdict：`INCONCLUSIVE`（counts_as_pass=False，strict=INCONCLUSIVE，baseline=INCONCLUSIVE，game_side=FAIL）
* 档位+轮次：`INCONCLUSIVE @w90 r1`（window=90，round=1，reporting=90，at_reporting_window=True，reporting_state=ok）
* 注入/接受后变化/rate：12 / 6 / 0.6667
* 两窗对齐：8/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 1 frame(s))（matched 8/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:/Anaconda/python.exe runs/model-player/_scripts/t140_sweep.py --arm scripted --window 90 --round 1 --port-base 9978 --prefix t140-postfix4-w90-r1 asteroids frogger bomberman flappy`  <- t136_commands.jsonl
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game bomberman --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9978 --window-frames 90 --round 1 --change-margin strict --out-prefix t140-postfix4-w90-r1`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t140-postfix4-w90-r1/bomberman/scripted/demo.png` | 155682 | `fe63ed9be1d6ac9b920d153ae6941213b1d3927ceb4ff3df5a21cb132683aa70` |
| `runs/model-player/t140-postfix4-w90-r1/bomberman/scripted/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t140-postfix4-w90-r1/bomberman/scripted/engine-game.stdout.txt` | 775 | `6c5132264fe8e80c3085841bb1adf0b5d58fff33d40333e4304cc1ba534572a7` |
| `runs/model-player/t140-postfix4-w90-r1/bomberman/scripted/filmstrip.png` | 145036 | `69414bcc6012f58ff2d580e5537c5b8a0bdb0882c489543a267bc9a73ca3a840` |
| `runs/model-player/t140-postfix4-w90-r1/bomberman/scripted/frames.json` | 512368 | `c03b5861f7d07a49c74cd99b1ba710b5ae1b9813df928466036c1cb7146c8e42` |
| `runs/model-player/t140-postfix4-w90-r1/bomberman/scripted/player.json` | 28512 | `7336ef7b47474b9240f1f2b8d45d7fcb42f0209504d2ab18946aa4c02f3b0795` |
| `runs/model-player/t140-postfix4-w90-r1/bomberman/scripted/session.json` | 12303 | `02cff1a58413b2bd8bb80dcb3d8f70c9fa02bf3ba3f10d99d8c73a6b22156e79` |
| `runs/model-player/t140-postfix4-w90-r1/bomberman/scripted/steps.jsonl` | 143284 | `6edf802529689a0336686a4b27921b83016d512208f8440b3a105e50bbebee57` |
| `calls/**`（1362 个文件，25613168 B）| — | `ade569c9e2e2e65d4589eb2b75d8f56b85918d07cfe8127b34cd9c1f563edddf` |
| `frames/**`（37 个文件，357249 B）| — | `8d00402138fe1c936b29966a51b614294e5a7f45eed421ce96c87a2f98bf189e` |
| `states/**`（27 个文件，602283 B）| — | `c6b20fa39e30a5d614c955e679a8fffea4b3a06d15d0c4f925e501ab66ec4a51` |

## t140-postfix4-w90-r1 / flappy / scripted

* 目录：`runs/model-player/t140-postfix4-w90-r1/flappy/scripted`
* verdict：`FAIL`（counts_as_pass=False，strict=FAIL，baseline=FAIL，game_side=FAIL）
* 档位+轮次：`FAIL @w90 r1`（window=90，round=1，reporting=90，at_reporting_window=True，reporting_state=ok）
* 注入/接受后变化/rate：12 / 6 / 0.5
* 两窗对齐：8/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 2 frame(s))（matched 8/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:/Anaconda/python.exe runs/model-player/_scripts/t140_sweep.py --arm scripted --window 90 --round 1 --port-base 9978 --prefix t140-postfix4-w90-r1 asteroids frogger bomberman flappy`  <- t136_commands.jsonl
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game flappy --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9978 --window-frames 90 --round 1 --change-margin strict --out-prefix t140-postfix4-w90-r1`  <- t136_commands.jsonl
  * `D:/Anaconda/python.exe runs/model-player/_scripts/t140_steps.py runs/model-player/t140-postfix4-w90-r1/flappy/scripted/steps.jsonl`  <- t136_commands.jsonl
  * `D:/Anaconda/python.exe runs/model-player/_scripts/t139_anchors.py t140-postfix4-w90-r1 flappy scripted 1 2 4`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t140-postfix4-w90-r1/flappy/scripted/demo.png` | 112997 | `a18f931ebcdd73a8a1724ad337ae04df3b52e60bf1698d83d52ce94f653a980e` |
| `runs/model-player/t140-postfix4-w90-r1/flappy/scripted/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t140-postfix4-w90-r1/flappy/scripted/engine-game.stdout.txt` | 743 | `06fc823c8b0fd3148836e04359ad5cc1ea99fb1d0a66280c6d0521342bd771f7` |
| `runs/model-player/t140-postfix4-w90-r1/flappy/scripted/filmstrip.png` | 110943 | `e3da07a16a408d81e13309e321c66884124b0a6d49d3e2a96bab3414af8b15e1` |
| `runs/model-player/t140-postfix4-w90-r1/flappy/scripted/frames.json` | 562193 | `81c6ff532d1c05d6db42127a28bddb5ac9baf186e8b6fa2bd7c2e03180f2287d` |
| `runs/model-player/t140-postfix4-w90-r1/flappy/scripted/player.json` | 24960 | `302855e77ba490de92f1bc41b21624aded8626cb35c51ce29d941eb31e75c9d1` |
| `runs/model-player/t140-postfix4-w90-r1/flappy/scripted/session.json` | 12140 | `f6ce25df80e02f2fb752331ac1ae0377b1a5ded0aee4e3eeecf6cba51b893643` |
| `runs/model-player/t140-postfix4-w90-r1/flappy/scripted/steps.jsonl` | 179033 | `ff5d8356a399ef8b22893261b750b18feb3ca78ca8d072d0a2b675292c766746` |
| `calls/**`（1482 个文件，4994902 B）| — | `4c41c1f373d86daa697bade7a52c1d8085cd1f77f900c64bb43538847c77b5f5` |
| `frames/**`（37 个文件，395091 B）| — | `07d04713bc2c7b187280ddf1a2dbcb3ca3d4e7459639af17eadf1e5f412fe5f5` |
| `states/**`（27 个文件，86670 B）| — | `a4179dae7216d614fd1d5a7552fb9e8b6ca23ade61d320ac1029eefaf1cdcd3e` |

## t140-postfix4-w90-r1 / frogger / scripted

* 目录：`runs/model-player/t140-postfix4-w90-r1/frogger/scripted`
* verdict：`PASS`（counts_as_pass=True，strict=PASS，baseline=PASS，game_side=PASS）
* 档位+轮次：`PASS @w90 r1`（window=90，round=1，reporting=90，at_reporting_window=True，reporting_state=ok）
* 注入/接受后变化/rate：8 / 8 / 1.0
* 两窗对齐：4/8 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 1 frame(s))（matched 4/8，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:/Anaconda/python.exe runs/model-player/_scripts/t140_sweep.py --arm scripted --window 90 --round 1 --port-base 9978 --prefix t140-postfix4-w90-r1 asteroids frogger bomberman flappy`  <- t136_commands.jsonl
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game frogger --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9978 --window-frames 90 --round 1 --change-margin strict --out-prefix t140-postfix4-w90-r1`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t140-postfix4-w90-r1/frogger/scripted/demo.png` | 100474 | `554a11c0b48c915fdc02953022ef86c7d6dbc776d76a15ece834be6e907b92fe` |
| `runs/model-player/t140-postfix4-w90-r1/frogger/scripted/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t140-postfix4-w90-r1/frogger/scripted/engine-game.stdout.txt` | 748 | `edb9a0b688366376d8c18be03621d39393c2d22d1e1444a27b0b787b7d04232c` |
| `runs/model-player/t140-postfix4-w90-r1/frogger/scripted/filmstrip.png` | 60493 | `c5da6c3227b12c0f95f5e6a1d52a9e8dab00988296d0d0a20162f25fbdd2b47b` |
| `runs/model-player/t140-postfix4-w90-r1/frogger/scripted/frames.json` | 401768 | `b5a12da273377122c571a8c2b86c775982f19215e610c099e9bd378c23f13c7c` |
| `runs/model-player/t140-postfix4-w90-r1/frogger/scripted/player.json` | 22393 | `72c34229a4066d9a2a8d529099c1a565a83b05c1326e0d7363af98b2dcf7fb68` |
| `runs/model-player/t140-postfix4-w90-r1/frogger/scripted/session.json` | 12092 | `7b2328751922ff487ccf670d8b67d64bd04206f83886c42070dd4b9d566b8a4e` |
| `runs/model-player/t140-postfix4-w90-r1/frogger/scripted/steps.jsonl` | 91073 | `d0e24093a27bf598ef153492f5e88c20b46e40544626f1e10a401226b9bb59a3` |
| `calls/**`（930 个文件，4109535 B）| — | `f573446f9ed33a0adb4256bde01e935f11345de8627b641d4c7310be3f4e21fa` |
| `frames/**`（25 个文件，283172 B）| — | `2545034cbb7cc70f53227be0d86ee8a661a51147a150212166d68fffcc8ca386` |
| `states/**`（19 个文件，84336 B）| — | `567154233202f6032bfe8a08b315abc58a7d4679e896dcd8087e744f8c63c3fa` |

## t140-postfix4-w90-r2 / asteroids / scripted

* 目录：`runs/model-player/t140-postfix4-w90-r2/asteroids/scripted`
* verdict：`PASS`（counts_as_pass=True，strict=PASS，baseline=PASS，game_side=PASS）
* 档位+轮次：`PASS @w90 r1`（window=90，round=1，reporting=90，at_reporting_window=True，reporting_state=ok）
* 注入/接受后变化/rate：8 / 8 / 1.0
* 两窗对齐：5/8 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 2 frame(s))（matched 5/8，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:/Anaconda/python.exe runs/model-player/_scripts/t140_sweep.py --arm scripted --window 90 --round 1 --port-base 9979 --prefix t140-postfix4-w90-r2 asteroids frogger bomberman flappy`  <- t136_commands.jsonl
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game asteroids --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9979 --window-frames 90 --round 1 --change-margin strict --out-prefix t140-postfix4-w90-r2`  <- t136_commands.jsonl
  * `D:/Anaconda/python.exe runs/model-player/_scripts/t140_sha.py runs/model-player/t140-prefix4-w90-r1/frogger/scripted/frames/002_01_before.png runs/model-player/t140-prefix4-w90-r1/frogger/scripted/frames/004_01_after.png runs/model-player/t140-postfix4-w90-r2/frogger/scripted/frames/002_01_before.png runs/model-player/t140-postfix4-w90-r2/frogger/scripted/frames/004_01_after.png runs/model-player/t140-prefix4-w90-r1/bomberman/scripted/frames/013_04_after.png runs/model-player/t140-postfix4-w90-r3/bomberman/scripted/frames/004_01_after.png runs/model-player/t140-prefix4-w90-r1/flappy/scripted/frames/002_01_before.png runs/model-player/t140-postfix4-w90-r2/flappy/scripted/frames/002_01_before.png runs/model-player/t139-jev-v3-w90/asteroids/jev/frames/016_05_after.png runs/model-player/t139-jev-v3-w90/asteroids/jev/frames/037_12_after.png`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t140-postfix4-w90-r2/asteroids/scripted/demo.png` | 87997 | `d24e859c3c819027ba3dd5788562d43bac163e53517ecde2c6da1a982ac82261` |
| `runs/model-player/t140-postfix4-w90-r2/asteroids/scripted/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t140-postfix4-w90-r2/asteroids/scripted/engine-game.stdout.txt` | 741 | `065b4343c956856d259ad6c07351935b44d97ad4a14c807d485bda8850054187` |
| `runs/model-player/t140-postfix4-w90-r2/asteroids/scripted/filmstrip.png` | 48534 | `12a27eedeb440c5284653c5aa74c5d961a0d384204f0ed20a11bd7901616bc34` |
| `runs/model-player/t140-postfix4-w90-r2/asteroids/scripted/frames.json` | 370410 | `98874c43cf76060f6ebad97d7de0b3e3c187cca12efdb10bc60645c61d2a2ea7` |
| `runs/model-player/t140-postfix4-w90-r2/asteroids/scripted/player.json` | 22494 | `a268504fb0b17a7e1e06a2caafc0acd9adf2116b9a33f29ce1947d0b6228b98b` |
| `runs/model-player/t140-postfix4-w90-r2/asteroids/scripted/session.json` | 12187 | `8ffcbecd6b1ee20384d49737f46bd54cc3cb0c856be7c944f0d1a91bc8ef1741` |
| `runs/model-player/t140-postfix4-w90-r2/asteroids/scripted/steps.jsonl` | 100135 | `8b5cbd83a7381b16d9aee1146e4be68fbc3ff05d6662e1d24773ce3171275ae4` |
| `calls/**`（969 个文件，3208071 B）| — | `3e755d504c743baeb91d7edafe13287a7870fa0a8aa3eee8400a243e9f8f67a2` |
| `frames/**`（25 个文件，259629 B）| — | `82c6ac9cd0304e0e239ffe79ec31eed128b2ac4b972b4fbd4a9b62bf43678063` |
| `states/**`（19 个文件，58710 B）| — | `88e00d8b4473eb433ad8beaa44bb95523ed0a04cb30780ae6b77d4532d428ddf` |

## t140-postfix4-w90-r2 / bomberman / scripted

* 目录：`runs/model-player/t140-postfix4-w90-r2/bomberman/scripted`
* verdict：`INCONCLUSIVE`（counts_as_pass=False，strict=INCONCLUSIVE，baseline=INCONCLUSIVE，game_side=FAIL）
* 档位+轮次：`INCONCLUSIVE @w90 r1`（window=90，round=1，reporting=90，at_reporting_window=True，reporting_state=ok）
* 注入/接受后变化/rate：12 / 6 / 0.6667
* 两窗对齐：5/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 2 frame(s))（matched 5/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:/Anaconda/python.exe runs/model-player/_scripts/t140_sweep.py --arm scripted --window 90 --round 1 --port-base 9979 --prefix t140-postfix4-w90-r2 asteroids frogger bomberman flappy`  <- t136_commands.jsonl
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game bomberman --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9979 --window-frames 90 --round 1 --change-margin strict --out-prefix t140-postfix4-w90-r2`  <- t136_commands.jsonl
  * `D:/Anaconda/python.exe runs/model-player/_scripts/t140_steps.py runs/model-player/t140-postfix4-w90-r2/bomberman/scripted/steps.jsonl`  <- t136_commands.jsonl
  * `D:/Anaconda/python.exe runs/model-player/_scripts/t139_anchors.py t140-postfix4-w90-r2 bomberman scripted 1 5`  <- t136_commands.jsonl
  * `D:/Anaconda/python.exe runs/model-player/_scripts/t140_sha.py runs/model-player/t140-prefix4-w90-r1/frogger/scripted/frames/002_01_before.png runs/model-player/t140-prefix4-w90-r1/frogger/scripted/frames/004_01_after.png runs/model-player/t140-postfix4-w90-r2/frogger/scripted/frames/002_01_before.png runs/model-player/t140-postfix4-w90-r2/frogger/scripted/frames/004_01_after.png runs/model-player/t140-prefix4-w90-r1/bomberman/scripted/frames/013_04_after.png runs/model-player/t140-postfix4-w90-r3/bomberman/scripted/frames/004_01_after.png runs/model-player/t140-prefix4-w90-r1/flappy/scripted/frames/002_01_before.png runs/model-player/t140-postfix4-w90-r2/flappy/scripted/frames/002_01_before.png runs/model-player/t139-jev-v3-w90/asteroids/jev/frames/016_05_after.png runs/model-player/t139-jev-v3-w90/asteroids/jev/frames/037_12_after.png`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t140-postfix4-w90-r2/bomberman/scripted/demo.png` | 155682 | `fe63ed9be1d6ac9b920d153ae6941213b1d3927ceb4ff3df5a21cb132683aa70` |
| `runs/model-player/t140-postfix4-w90-r2/bomberman/scripted/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t140-postfix4-w90-r2/bomberman/scripted/engine-game.stdout.txt` | 775 | `7f06d4d733aadbd0fa4a327900499e127facdf0e90cdc58b82266439b407cb5b` |
| `runs/model-player/t140-postfix4-w90-r2/bomberman/scripted/filmstrip.png` | 145036 | `69414bcc6012f58ff2d580e5537c5b8a0bdb0882c489543a267bc9a73ca3a840` |
| `runs/model-player/t140-postfix4-w90-r2/bomberman/scripted/frames.json` | 512359 | `11e588324d4c80f6cd0adf628660bce015a2ddf483c32c2f5fb5bba8e1c43855` |
| `runs/model-player/t140-postfix4-w90-r2/bomberman/scripted/player.json` | 28516 | `b296fdb9fb64065a5db5726c699767ddadc64b5bc3c6377fd8da23ea6be71f25` |
| `runs/model-player/t140-postfix4-w90-r2/bomberman/scripted/session.json` | 12303 | `a6e3cfd7c8761d40023e0815b678074fc371cbf700e555005b43220ab5a21e0f` |
| `runs/model-player/t140-postfix4-w90-r2/bomberman/scripted/steps.jsonl` | 143280 | `cb347637461c237a99e24d38d64646668116a0467abf989481e1dda3bbc2b57a` |
| `calls/**`（1317 个文件，24711143 B）| — | `3d9ae14de3055023351bd4810112b969eb3668ebccf3ae2ae8bbd54734e959f9` |
| `frames/**`（37 个文件，357249 B）| — | `0167e909742fed9c3ff475e4c1104ce20d69fb125e9968b5aecd999b7f8ca3f0` |
| `states/**`（27 个文件，602278 B）| — | `e5fd303fc65781d3db89a495a8ef9f126f390a3b0107df8e03b1a2ee251d8adf` |

## t140-postfix4-w90-r2 / flappy / scripted

* 目录：`runs/model-player/t140-postfix4-w90-r2/flappy/scripted`
* verdict：`PASS(baseline only)`（counts_as_pass=False，strict=FAIL，baseline=PASS，game_side=FAIL）
* 档位+轮次：`PASS(baseline only) @w90 r1`（window=90，round=1，reporting=90，at_reporting_window=True，reporting_state=ok）
* 注入/接受后变化/rate：9 / 8 / 0.8889
* 两窗对齐：6/9 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 1 frame(s))（matched 6/9，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:/Anaconda/python.exe runs/model-player/_scripts/t140_sweep.py --arm scripted --window 90 --round 1 --port-base 9979 --prefix t140-postfix4-w90-r2 asteroids frogger bomberman flappy`  <- t136_commands.jsonl
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game flappy --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9979 --window-frames 90 --round 1 --change-margin strict --out-prefix t140-postfix4-w90-r2`  <- t136_commands.jsonl
  * `D:/Anaconda/python.exe runs/model-player/_scripts/t140_steps.py runs/model-player/t140-postfix4-w90-r2/flappy/scripted/steps.jsonl`  <- t136_commands.jsonl
  * `D:/Anaconda/python.exe runs/model-player/_scripts/t140_sha.py runs/model-player/t140-prefix4-w90-r1/frogger/scripted/frames/002_01_before.png runs/model-player/t140-prefix4-w90-r1/frogger/scripted/frames/004_01_after.png runs/model-player/t140-postfix4-w90-r2/frogger/scripted/frames/002_01_before.png runs/model-player/t140-postfix4-w90-r2/frogger/scripted/frames/004_01_after.png runs/model-player/t140-prefix4-w90-r1/bomberman/scripted/frames/013_04_after.png runs/model-player/t140-postfix4-w90-r3/bomberman/scripted/frames/004_01_after.png runs/model-player/t140-prefix4-w90-r1/flappy/scripted/frames/002_01_before.png runs/model-player/t140-postfix4-w90-r2/flappy/scripted/frames/002_01_before.png runs/model-player/t139-jev-v3-w90/asteroids/jev/frames/016_05_after.png runs/model-player/t139-jev-v3-w90/asteroids/jev/frames/037_12_after.png`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t140-postfix4-w90-r2/flappy/scripted/demo.png` | 99142 | `f6103b14ebdfe67533670f3b480b397cba27961b1d9fd83ca59baf5d1b27eac4` |
| `runs/model-player/t140-postfix4-w90-r2/flappy/scripted/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t140-postfix4-w90-r2/flappy/scripted/engine-game.stdout.txt` | 743 | `a69b9872b0efc4fa6cd5bf926b4c81e24ac1af88a577774f86529a3b2ea3383d` |
| `runs/model-player/t140-postfix4-w90-r2/flappy/scripted/filmstrip.png` | 89006 | `6e13a41e10696564d0f25797ebc3fcb9a920a010bbec217c782f43383ba8cde4` |
| `runs/model-player/t140-postfix4-w90-r2/flappy/scripted/frames.json` | 429697 | `08edb430a83327d29b5d3483b1a3a55954dfff80b33e55c31220e3c851a7314a` |
| `runs/model-player/t140-postfix4-w90-r2/flappy/scripted/player.json` | 23801 | `f7de5f5ef4d8a9cd0a4c433809200011987aec1a93ff3ed9ed2a7ca0031dd564` |
| `runs/model-player/t140-postfix4-w90-r2/flappy/scripted/session.json` | 12135 | `e2cd43fe202aa8160921328f4e1b0a32605b0ec24a0b439eddd526f17998db64` |
| `runs/model-player/t140-postfix4-w90-r2/flappy/scripted/steps.jsonl` | 141071 | `9ff17d4e99138053926eac519fb9fcc3b815ef43796b400c0bc050296564ad15` |
| `calls/**`（1087 个文件，3711357 B）| — | `e7ac44915771cd212b52e0c9f5c0644e31cd3eaad9d733c77323e6cd58f2f59b` |
| `frames/**`（28 个文件，302166 B）| — | `55814d6e3382cd5a93cc878d4dd1df20018599669f168b61a2c62b444ddd65ed` |
| `states/**`（21 个文件，67952 B）| — | `e3bed8e204700e0abe55803f7fcbc79f144f22686feaf79b3ae100cd7bd92b2a` |

## t140-postfix4-w90-r2 / frogger / scripted

* 目录：`runs/model-player/t140-postfix4-w90-r2/frogger/scripted`
* verdict：`PASS`（counts_as_pass=True，strict=PASS，baseline=PASS，game_side=PASS）
* 档位+轮次：`PASS @w90 r1`（window=90，round=1，reporting=90，at_reporting_window=True，reporting_state=ok）
* 注入/接受后变化/rate：8 / 8 / 1.0
* 两窗对齐：4/8 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 2 frame(s))（matched 4/8，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:/Anaconda/python.exe runs/model-player/_scripts/t140_sweep.py --arm scripted --window 90 --round 1 --port-base 9979 --prefix t140-postfix4-w90-r2 asteroids frogger bomberman flappy`  <- t136_commands.jsonl
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game frogger --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9979 --window-frames 90 --round 1 --change-margin strict --out-prefix t140-postfix4-w90-r2`  <- t136_commands.jsonl
  * `D:/Anaconda/python.exe runs/model-player/_scripts/t139_anchors.py t140-postfix4-w90-r2 frogger scripted 1 2`  <- t136_commands.jsonl
  * `D:/Anaconda/python.exe runs/model-player/_scripts/t140_steps.py runs/model-player/t140-postfix4-w90-r2/frogger/scripted/steps.jsonl`  <- t136_commands.jsonl
  * `D:/Anaconda/python.exe runs/model-player/_scripts/t140_sha.py runs/model-player/t140-prefix4-w90-r1/frogger/scripted/frames/002_01_before.png runs/model-player/t140-prefix4-w90-r1/frogger/scripted/frames/004_01_after.png runs/model-player/t140-postfix4-w90-r2/frogger/scripted/frames/002_01_before.png runs/model-player/t140-postfix4-w90-r2/frogger/scripted/frames/004_01_after.png runs/model-player/t140-prefix4-w90-r1/bomberman/scripted/frames/013_04_after.png runs/model-player/t140-postfix4-w90-r3/bomberman/scripted/frames/004_01_after.png runs/model-player/t140-prefix4-w90-r1/flappy/scripted/frames/002_01_before.png runs/model-player/t140-postfix4-w90-r2/flappy/scripted/frames/002_01_before.png runs/model-player/t139-jev-v3-w90/asteroids/jev/frames/016_05_after.png runs/model-player/t139-jev-v3-w90/asteroids/jev/frames/037_12_after.png`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t140-postfix4-w90-r2/frogger/scripted/demo.png` | 100474 | `554a11c0b48c915fdc02953022ef86c7d6dbc776d76a15ece834be6e907b92fe` |
| `runs/model-player/t140-postfix4-w90-r2/frogger/scripted/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t140-postfix4-w90-r2/frogger/scripted/engine-game.stdout.txt` | 748 | `abd2b5dd79b0c3ac7b0864475567ba0279160e6a9786b416a98b254799fee6c2` |
| `runs/model-player/t140-postfix4-w90-r2/frogger/scripted/filmstrip.png` | 60493 | `c5da6c3227b12c0f95f5e6a1d52a9e8dab00988296d0d0a20162f25fbdd2b47b` |
| `runs/model-player/t140-postfix4-w90-r2/frogger/scripted/frames.json` | 401768 | `c6d65fc5d5567d1accdeae2fef1f585820dbcad2ea07434c440656bfa77dee32` |
| `runs/model-player/t140-postfix4-w90-r2/frogger/scripted/player.json` | 22389 | `14d9c165dc2fefa1737e3bde9868126c5c0467671ea4b156c069c9c672a88a56` |
| `runs/model-player/t140-postfix4-w90-r2/frogger/scripted/session.json` | 12090 | `0b33c909374d42de3f8009453c2a8c5d51b04145534809332abe74030d6bc770` |
| `runs/model-player/t140-postfix4-w90-r2/frogger/scripted/steps.jsonl` | 91067 | `f1f2fcadf5a4bad0912779594dc26d7ee2b98f80f7685d0edf3e9aea811ff7a2` |
| `calls/**`（955 个文件，4217206 B）| — | `0782e188deb951bd2af532a82cc6a609165493b81740ca1117ed3c264dc799e8` |
| `frames/**`（25 个文件，283172 B）| — | `91b1974e6e2283c2977e895326d9523084be8af735acdf81171d60013f40f2a9` |
| `states/**`（19 个文件，84336 B）| — | `ef523aedbbf4507ceb45d919620aae420097d9ff4c2977541902736c2d024c57` |

## t140-postfix4-w90-r3 / bomberman / scripted

* 目录：`runs/model-player/t140-postfix4-w90-r3/bomberman/scripted`
* verdict：`PASS`（counts_as_pass=True，strict=PASS，baseline=PASS，game_side=PASS）
* 档位+轮次：`PASS @w90 r1`（window=90，round=1，reporting=90，at_reporting_window=True，reporting_state=ok）
* 注入/接受后变化/rate：12 / 6 / 1.0
* 两窗对齐：7/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 2 frame(s))（matched 7/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:/Anaconda/python.exe runs/model-player/_scripts/t140_sweep.py --arm scripted --window 90 --round 1 --port-base 9980 --prefix t140-postfix4-w90-r3 bomberman`  <- t136_commands.jsonl
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game bomberman --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9980 --window-frames 90 --round 1 --change-margin strict --out-prefix t140-postfix4-w90-r3`  <- t136_commands.jsonl
  * `D:/Anaconda/python.exe runs/model-player/_scripts/t140_sha.py runs/model-player/t140-prefix4-w90-r1/frogger/scripted/frames/002_01_before.png runs/model-player/t140-prefix4-w90-r1/frogger/scripted/frames/004_01_after.png runs/model-player/t140-postfix4-w90-r2/frogger/scripted/frames/002_01_before.png runs/model-player/t140-postfix4-w90-r2/frogger/scripted/frames/004_01_after.png runs/model-player/t140-prefix4-w90-r1/bomberman/scripted/frames/013_04_after.png runs/model-player/t140-postfix4-w90-r3/bomberman/scripted/frames/004_01_after.png runs/model-player/t140-prefix4-w90-r1/flappy/scripted/frames/002_01_before.png runs/model-player/t140-postfix4-w90-r2/flappy/scripted/frames/002_01_before.png runs/model-player/t139-jev-v3-w90/asteroids/jev/frames/016_05_after.png runs/model-player/t139-jev-v3-w90/asteroids/jev/frames/037_12_after.png`  <- t136_commands.jsonl
  * `D:/Anaconda/python.exe runs/model-player/_scripts/t140_sha.py runs/model-player/t140-postfix4-w90-r3/bomberman/scripted/frames/007_02_after.png runs/model-player/t140-prefix4-w90-r1/bomberman/scripted/frames/010_03_after.png runs/model-player/t140-prefix4-w90-r1/bomberman/scripted/frames/007_02_after.png`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t140-postfix4-w90-r3/bomberman/scripted/demo.png` | 155674 | `13ff9e9dfc93545dd24f74fc479fddf868739446811f7e9142fe0948bb0f84eb` |
| `runs/model-player/t140-postfix4-w90-r3/bomberman/scripted/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t140-postfix4-w90-r3/bomberman/scripted/engine-game.stdout.txt` | 775 | `f36e5382569b7ab3f08cb5e936461030668276d9f9ee5e4a439bbba1176af5b0` |
| `runs/model-player/t140-postfix4-w90-r3/bomberman/scripted/filmstrip.png` | 145036 | `69414bcc6012f58ff2d580e5537c5b8a0bdb0882c489543a267bc9a73ca3a840` |
| `runs/model-player/t140-postfix4-w90-r3/bomberman/scripted/frames.json` | 512362 | `78fd3af79577360bad4036b32f9678f67cad209d29316037512adf3216562834` |
| `runs/model-player/t140-postfix4-w90-r3/bomberman/scripted/player.json` | 30342 | `b88ff893a9e5dc47ab2f6b9ed7a376a287c94b1739fc77ec0610bfcb0657c715` |
| `runs/model-player/t140-postfix4-w90-r3/bomberman/scripted/session.json` | 13061 | `ee85b9157c1ab7aa46ef78645533a0f329a1bfdd4a17f04895a13284bfb3a4f3` |
| `runs/model-player/t140-postfix4-w90-r3/bomberman/scripted/steps.jsonl` | 146981 | `a29dea5b91d6ceb8d0b7e4b0aca55fb08871d3713752b7af1815dd1861cadc88` |
| `calls/**`（1318 个文件，24764847 B）| — | `06cd4e659f5f74ca1899ec060afab5ebcf09900bb1b91c8344d152e5a7b58162` |
| `frames/**`（37 个文件，357249 B）| — | `7bba9f1f054db58c82c741796e3f06dbc2dd13636feb7ffe52c53a56e81dc887` |
| `states/**`（27 个文件，603042 B）| — | `930f270517d38d9335af2a930d890e1dda3a0a88f6d572d3008f082b8c50cfd5` |

## t140-scripted-w90-r1 / asteroids / scripted

* 目录：`runs/model-player/t140-scripted-w90-r1/asteroids/scripted`
* verdict：`PASS`（counts_as_pass=True，strict=PASS，baseline=PASS，game_side=PASS）
* 档位+轮次：`PASS @w90 r1`（window=90，round=1，reporting=90，at_reporting_window=True，reporting_state=ok）
* 注入/接受后变化/rate：8 / 8 / 1.0
* 两窗对齐：5/8 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 2 frame(s))（matched 5/8，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game asteroids --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9981 --window-frames 90 --round 1 --change-margin strict --out-prefix t140-scripted-w90-r1`  <- t136_commands.jsonl
  * `D:/Anaconda/python.exe runs/model-player/_scripts/t140_gate_check.py runs/model-player/t140-scripted-w90-r1/asteroids/scripted runs/model-player/t139-scripted-w30/asteroids/scripted runs/model-player/t139-jev-v3-w90/asteroids/jev`  <- t136_commands.jsonl
  * `D:/Anaconda/python.exe runs/model-player/_scripts/t140_gate_check.py runs/model-player/t139-scripted-w30/asteroids/scripted runs/model-player/t140-scripted-w90-r1/asteroids/scripted`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t140-scripted-w90-r1/asteroids/scripted/demo.png` | 87997 | `9796d7e20a4458c2d72ab1eee2e4c0192fc0008605dc49d4c632137d807f59db` |
| `runs/model-player/t140-scripted-w90-r1/asteroids/scripted/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t140-scripted-w90-r1/asteroids/scripted/engine-game.stdout.txt` | 741 | `3748762cefbb9278ab92fda82ba8ce334d5043a036a375884ae7658864f1b599` |
| `runs/model-player/t140-scripted-w90-r1/asteroids/scripted/filmstrip.png` | 48436 | `cc4f66d3b433003058963b5895da9d96ddc7ead634092a17868fc98fed80ce4a` |
| `runs/model-player/t140-scripted-w90-r1/asteroids/scripted/frames.json` | 370738 | `131ba720f71aee535b7114fee84e8cc6eb80ab7eacd8b28a84267ce72a6f9ca6` |
| `runs/model-player/t140-scripted-w90-r1/asteroids/scripted/player.json` | 22493 | `2734778810ecb7309c79e76dbb92424badc45e924880068187409db1d5241db6` |
| `runs/model-player/t140-scripted-w90-r1/asteroids/scripted/session.json` | 12188 | `8a66f08e78c101efcf022359e294659c846c547d2e34346bc83f2b9420774109` |
| `runs/model-player/t140-scripted-w90-r1/asteroids/scripted/steps.jsonl` | 100254 | `3d021982d4185ba63cc5891745b282f65a96bf29ba312721232f7fc2a3920f0c` |
| `calls/**`（913 个文件，3031327 B）| — | `30d657abdf0152d5d2711b208b374a0f579ecdf3b80964daa5440826913bb77c` |
| `frames/**`（25 个文件，259889 B）| — | `2efbc3dcc84f0f5edfbd205e5f5ae6479067e1c4d8a1b39c50270caf2dcc921e` |
| `states/**`（19 个文件，58706 B）| — | `0aa6bd57e01d3a8f51b5464a835829f131f2b53d16b6792ae59bc416aa54303a` |

## t140-scripted-w90-r1 / bomberman / scripted

* 目录：`runs/model-player/t140-scripted-w90-r1/bomberman/scripted`
* verdict：`PASS`（counts_as_pass=True，strict=PASS，baseline=PASS，game_side=PASS）
* 档位+轮次：`PASS @w90 r1`（window=90，round=1，reporting=90，at_reporting_window=True，reporting_state=ok）
* 注入/接受后变化/rate：12 / 6 / 1.0
* 两窗对齐：2/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 2 frame(s))（matched 2/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game bomberman --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9981 --window-frames 90 --round 1 --change-margin strict --out-prefix t140-scripted-w90-r1`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t140-scripted-w90-r1/bomberman/scripted/demo.png` | 155674 | `13ff9e9dfc93545dd24f74fc479fddf868739446811f7e9142fe0948bb0f84eb` |
| `runs/model-player/t140-scripted-w90-r1/bomberman/scripted/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t140-scripted-w90-r1/bomberman/scripted/engine-game.stdout.txt` | 775 | `a5610c6f57d43dddbb9bd7e648b3acbdb204a874b366ba6fdbee7be334c7e346` |
| `runs/model-player/t140-scripted-w90-r1/bomberman/scripted/filmstrip.png` | 145036 | `69414bcc6012f58ff2d580e5537c5b8a0bdb0882c489543a267bc9a73ca3a840` |
| `runs/model-player/t140-scripted-w90-r1/bomberman/scripted/frames.json` | 512365 | `ad7f7778523a4fd42965576afbcde96a0a71d879a7a7718964a6fc512422889f` |
| `runs/model-player/t140-scripted-w90-r1/bomberman/scripted/player.json` | 30348 | `48b0d69022d0209b3a1656429aee468d17af2a0cdb817be7d960e271d416c078` |
| `runs/model-player/t140-scripted-w90-r1/bomberman/scripted/session.json` | 13063 | `c09cb01f8a851604b014732ac28509e403b75373bc28b8476c751b73a6feaa10` |
| `runs/model-player/t140-scripted-w90-r1/bomberman/scripted/steps.jsonl` | 146993 | `557cca89187d195c4971db822cfb388dc99f6fb1c72dde53dc862bfcb3864662` |
| `calls/**`（1329 个文件，24986496 B）| — | `00d83adcfc96dff595518fc8966eb9b482e4a3613138885719d1a7c2dddb0cb0` |
| `frames/**`（37 个文件，357249 B）| — | `3f7c26c11bc23977f6840e4bca25c3f26121d5ddbada8f0e910d32731c2076cc` |
| `states/**`（27 个文件，603046 B）| — | `2b1c92b0b91006877499073518bf25baeabaa823eb7effecf11f1e7590fc576f` |

## t140-scripted-w90-r1 / breakout / scripted

* 目录：`runs/model-player/t140-scripted-w90-r1/breakout/scripted`
* verdict：`INCONCLUSIVE`（counts_as_pass=False，strict=INCONCLUSIVE，baseline=INCONCLUSIVE，game_side=INCONCLUSIVE）
* 档位+轮次：`INCONCLUSIVE @w90 r1`（window=90，round=1，reporting=90，at_reporting_window=True，reporting_state=ok）
* 注入/接受后变化/rate：2 / 2 / 1.0
* 两窗对齐：3/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 2 frame(s))（matched 3/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game breakout --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9981 --window-frames 90 --round 1 --change-margin strict --out-prefix t140-scripted-w90-r1`  <- t136_commands.jsonl
  * `D:/Anaconda/python.exe tools/playtest_player.py stability --run runs/model-player/t140-scripted-w90-r1/breakout/scripted/player.json --run runs/model-player/t140-scripted-w90-r2/breakout/scripted/player.json --run runs/model-player/t139-scripted-w90/breakout/scripted/player.json --out runs/model-player/_scripts/t140_unstable_breakout.json`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t140-scripted-w90-r1/breakout/scripted/demo.png` | 103720 | `b50bb653e769de66507c1b7c5e331475850a07b3d43e5d35013a8240c90ff2a7` |
| `runs/model-player/t140-scripted-w90-r1/breakout/scripted/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t140-scripted-w90-r1/breakout/scripted/engine-game.stdout.txt` | 5354 | `26db5f35d9f40a312dda0ba418660896ba642b0b2fef847c92257e69243a103d` |
| `runs/model-player/t140-scripted-w90-r1/breakout/scripted/filmstrip.png` | 74557 | `940ab1bbd0ea9848055d6fbb282c4d0fb77a33da7ee9136cded988eab70acbe4` |
| `runs/model-player/t140-scripted-w90-r1/breakout/scripted/frames.json` | 583620 | `ff7d602c210d81f1e7aa9c6035f4f61e2c6c66f59dba43ea5adbb791d84730a2` |
| `runs/model-player/t140-scripted-w90-r1/breakout/scripted/player.json` | 24641 | `77720fe0adcb7ee8ec2a18a4b7cec3ef5718f8acb7443636e30e770a2f47bb37` |
| `runs/model-player/t140-scripted-w90-r1/breakout/scripted/session.json` | 12355 | `407cf397d769def1a8d79910f3f3a0feea98bda5c737e21959a0f295a78df034` |
| `runs/model-player/t140-scripted-w90-r1/breakout/scripted/steps.jsonl` | 122918 | `21d2c5feb94c5f2dacf673812acbd71dc93cb0629ecab0b5b2bf097a63ca37d0` |
| `calls/**`（1023 个文件，5758235 B）| — | `4687b4016b5449a606f488925abaf08fcf99f161edad67c5dce9fce8d8ad51ee` |
| `frames/**`（37 个文件，410852 B）| — | `4ff4a4e55047c5267ada6a5b7ccfc537e4556fc04fd1144ade9546470693b104` |
| `states/**`（27 个文件，148664 B）| — | `e1fe415a215d9716f38b7c98fcb5abb6ff46e5dffadb3a242c643b1af8b077b4` |

## t140-scripted-w90-r1 / flappy / scripted

* 目录：`runs/model-player/t140-scripted-w90-r1/flappy/scripted`
* verdict：`PASS(baseline only)`（counts_as_pass=False，strict=FAIL，baseline=PASS，game_side=FAIL）
* 档位+轮次：`PASS(baseline only) @w90 r1`（window=90，round=1，reporting=90，at_reporting_window=True，reporting_state=ok）
* 注入/接受后变化/rate：12 / 7 / 0.5833
* 两窗对齐：9/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 1 frame(s))（matched 9/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game flappy --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9981 --window-frames 90 --round 1 --change-margin strict --out-prefix t140-scripted-w90-r1`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t140-scripted-w90-r1/flappy/scripted/demo.png` | 111053 | `6df6e84e7b2c3c4eb5d26fa56df26926718529733d2c18b759d3fcf91509064e` |
| `runs/model-player/t140-scripted-w90-r1/flappy/scripted/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t140-scripted-w90-r1/flappy/scripted/engine-game.stdout.txt` | 743 | `f7d3adfaf6330b4029d2e72ae89ec87c01c3db4fa2ba1586c5b89267b386c02f` |
| `runs/model-player/t140-scripted-w90-r1/flappy/scripted/filmstrip.png` | 115508 | `6a6b88f81e913f73dbca9f40e728bca2faf943b6242830b68f385894adac3277` |
| `runs/model-player/t140-scripted-w90-r1/flappy/scripted/frames.json` | 575046 | `7b6428b78ae79690f6205c161fbac14f4eb12b5a032415c8eac86c2ea51e7329` |
| `runs/model-player/t140-scripted-w90-r1/flappy/scripted/player.json` | 29311 | `3704c1e4ba473a823f469076b8c35db3baf11c05d1eecaaa653053c86327bded` |
| `runs/model-player/t140-scripted-w90-r1/flappy/scripted/session.json` | 12140 | `e088887cee3c88940758cddf31f4c830e0065c4298f85f7c8962b013a16c90e4` |
| `runs/model-player/t140-scripted-w90-r1/flappy/scripted/steps.jsonl` | 188400 | `7ebe488956375dcf2104345f05067793b9749ab0d627b5400c840fca2ee1b555` |
| `calls/**`（1429 个文件，4877950 B）| — | `0e451594d963cc78e274e475fcf8bbd376589fef081fff9896813edf63c10788` |
| `frames/**`（37 个文件，404702 B）| — | `030fa8a8fd81bb2a9b9da7fb6173aed24bc7e6a340e0986c3c107b72b2d1a0a2` |
| `states/**`（27 个文件，87473 B）| — | `d8544d0e834b5a48b7928de645069ddc3d4440175df57412507a77930b01375f` |

## t140-scripted-w90-r1 / frogger / scripted

* 目录：`runs/model-player/t140-scripted-w90-r1/frogger/scripted`
* verdict：`PASS`（counts_as_pass=True，strict=PASS，baseline=PASS，game_side=PASS）
* 档位+轮次：`PASS @w90 r1`（window=90，round=1，reporting=90，at_reporting_window=True，reporting_state=ok）
* 注入/接受后变化/rate：8 / 8 / 1.0
* 两窗对齐：4/8 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 1 frame(s))（matched 4/8，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game frogger --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9981 --window-frames 90 --round 1 --change-margin strict --out-prefix t140-scripted-w90-r1`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t140-scripted-w90-r1/frogger/scripted/demo.png` | 100474 | `554a11c0b48c915fdc02953022ef86c7d6dbc776d76a15ece834be6e907b92fe` |
| `runs/model-player/t140-scripted-w90-r1/frogger/scripted/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t140-scripted-w90-r1/frogger/scripted/engine-game.stdout.txt` | 748 | `b770982c85ef43f5f535537c4c7d2b9729d3304ecf1e729c24a6af1fd9c478f4` |
| `runs/model-player/t140-scripted-w90-r1/frogger/scripted/filmstrip.png` | 60493 | `c5da6c3227b12c0f95f5e6a1d52a9e8dab00988296d0d0a20162f25fbdd2b47b` |
| `runs/model-player/t140-scripted-w90-r1/frogger/scripted/frames.json` | 401771 | `0a9feed934b7c99382b86c1b2d3076c90f059cd92f9c00af4dbe214effa3f246` |
| `runs/model-player/t140-scripted-w90-r1/frogger/scripted/player.json` | 22393 | `c0d37b93bb6660d0e72a8ae965e945ab208e3f4d744a656415187daf9a9630c5` |
| `runs/model-player/t140-scripted-w90-r1/frogger/scripted/session.json` | 12093 | `9369420042b2f6156ebd6fb5aa9b18092ebe0ce62073e145a4e029e791c2d8b4` |
| `runs/model-player/t140-scripted-w90-r1/frogger/scripted/steps.jsonl` | 91073 | `f8baf14c2620c4e06bf8cc5d8304701c5856c90b3a132840bb18d81d175203de` |
| `calls/**`（936 个文件，4135375 B）| — | `1d7054c039ed2a2c5250c1f3bd966c80e792cda62301da4a25cec6b0dfcb28ab` |
| `frames/**`（25 个文件，283172 B）| — | `1ff3d0ebff62861b316a3e52c20ff6f0d4025ea8f2227c95b20e5baddecb50a4` |
| `states/**`（19 个文件，84336 B）| — | `30d4b00190b5881f14cf260b5602bb6414008e489037196f9cd75a6cf4184e50` |

## t140-scripted-w90-r1 / game2048 / scripted

* 目录：`runs/model-player/t140-scripted-w90-r1/game2048/scripted`
* verdict：`PASS`（counts_as_pass=True，strict=PASS，baseline=PASS，game_side=PASS）
* 档位+轮次：`PASS @w90 r1`（window=90，round=1，reporting=90，at_reporting_window=True，reporting_state=ok）
* 注入/接受后变化/rate：8 / 8 / 1.0
* 两窗对齐：6/8 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 1 frame(s))（matched 6/8，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game game2048 --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9981 --window-frames 90 --round 1 --change-margin strict --out-prefix t140-scripted-w90-r1`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t140-scripted-w90-r1/game2048/scripted/demo.png` | 105326 | `96cd977cad7a157a05cd9b6c6bd772ba6d05f9e17ffbad42242d83a4ba36b822` |
| `runs/model-player/t140-scripted-w90-r1/game2048/scripted/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t140-scripted-w90-r1/game2048/scripted/engine-game.stdout.txt` | 781 | `c95821b0fe00299cb3bd91dd8a636de7758f5b09ac135596932c2fcbf308cd4c` |
| `runs/model-player/t140-scripted-w90-r1/game2048/scripted/filmstrip.png` | 65250 | `8b39ca1c5bc016326495bf62fcef6deb85db6194028962d7ac1691659d624cf2` |
| `runs/model-player/t140-scripted-w90-r1/game2048/scripted/frames.json` | 452932 | `7b07a6fdef03ff114e48f086b915ed60fe7ecfb925ce14f842f40b9e4f17f918` |
| `runs/model-player/t140-scripted-w90-r1/game2048/scripted/player.json` | 22352 | `9cbcd2e1729abd880448996a0ec9fc627e7de2084c7d011bb8ce093b5d0389b9` |
| `runs/model-player/t140-scripted-w90-r1/game2048/scripted/session.json` | 12048 | `47c102c49c9cfcf114bf301f371fb6c33b7756d223b56e99b798bb2ffa4cb2d2` |
| `runs/model-player/t140-scripted-w90-r1/game2048/scripted/steps.jsonl` | 104980 | `4ed62baf24ffcc70a7dfa784b60886b11657c459ac2f2a21d8737b17e4d3ec42` |
| `calls/**`（966 个文件，6819856 B）| — | `32435cc7bcabf25b0b53ab5732e02d373c236c4cb75afae3e557c3e775e7bbe4` |
| `frames/**`（25 个文件，321508 B）| — | `05d194f0d5a32c9f1a8e66348c252cb6aeab146ee71ce5d17c9e93826f420d3b` |
| `states/**`（19 个文件，142694 B）| — | `85957eb5194a05c2cba8739144773dc9f0e7721b9f0f37b8ae4ecbe48395110f` |

## t140-scripted-w90-r1 / lunarlander / scripted

* 目录：`runs/model-player/t140-scripted-w90-r1/lunarlander/scripted`
* verdict：`PASS`（counts_as_pass=True，strict=PASS，baseline=PASS，game_side=PASS）
* 档位+轮次：`PASS @w90 r1`（window=90，round=1，reporting=90，at_reporting_window=True，reporting_state=ok）
* 注入/接受后变化/rate：8 / 8 / 1.0
* 两窗对齐：5/8 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 1 frame(s))（matched 5/8，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game lunarlander --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9981 --window-frames 90 --round 1 --change-margin strict --out-prefix t140-scripted-w90-r1`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t140-scripted-w90-r1/lunarlander/scripted/demo.png` | 107979 | `fe675c0ccd51f4a1a4a15dacdee5ed33787374bcb35921b22c507796c1046466` |
| `runs/model-player/t140-scripted-w90-r1/lunarlander/scripted/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t140-scripted-w90-r1/lunarlander/scripted/engine-game.stdout.txt` | 766 | `c8a3a4d25ab104eca262eb6e7c4fa8fa24fd71873453144c809cc18c99d49427` |
| `runs/model-player/t140-scripted-w90-r1/lunarlander/scripted/filmstrip.png` | 74547 | `7e121b223ce72fb916f5091c356afbea366c6eea0c8f759119832428f5c4d443` |
| `runs/model-player/t140-scripted-w90-r1/lunarlander/scripted/frames.json` | 455224 | `7e6c4f24d94715fb55320b7b001a207ab1955f636a24ffcff12344b4cfcf92a5` |
| `runs/model-player/t140-scripted-w90-r1/lunarlander/scripted/player.json` | 22486 | `dbdb3976b68d75e27fa549ab24b3d443393514ee35e726c4b7096a40a89c76cf` |
| `runs/model-player/t140-scripted-w90-r1/lunarlander/scripted/session.json` | 12123 | `06187926b6ae7f2a161bbe1c35e42d26111336d27526353e71e367a3b3666ca7` |
| `runs/model-player/t140-scripted-w90-r1/lunarlander/scripted/steps.jsonl` | 96502 | `ccd6ab1295b038fbb62e1219e845075c645b64ae365eb9738da1216c72c55ac2` |
| `calls/**`（954 个文件，10071887 B）| — | `176042ecbfa3f3b6b8f3dc2f1eafd2e8beee2f6e2e8edc2177ab375df50822c1` |
| `frames/**`（25 个文件，323393 B）| — | `e85adc9b86491618afa245df012ccdc2e64645d1e8237fd38c9a1f9a908f0f93` |
| `states/**`（19 个文件，227311 B）| — | `977b64a229ab4285881ea14823a317114c0b3c803e23662ab7fdf33de39679f9` |

## t140-scripted-w90-r1 / match3 / scripted

* 目录：`runs/model-player/t140-scripted-w90-r1/match3/scripted`
* verdict：`PASS`（counts_as_pass=True，strict=PASS，baseline=PASS，game_side=PASS）
* 档位+轮次：`PASS @w90 r1`（window=90，round=1，reporting=90，at_reporting_window=True，reporting_state=ok）
* 注入/接受后变化/rate：12 / 8 / 1.0
* 两窗对齐：9/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 1 frame(s))（matched 9/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game match3 --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9981 --window-frames 90 --round 1 --change-margin strict --out-prefix t140-scripted-w90-r1`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t140-scripted-w90-r1/match3/scripted/demo.png` | 194195 | `318ac279eb46746d7107c1178ff9a85a203d43b5a654ecec8b6bcee8124a5333` |
| `runs/model-player/t140-scripted-w90-r1/match3/scripted/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t140-scripted-w90-r1/match3/scripted/engine-game.stdout.txt` | 769 | `621c9455d95436ed6b4d1c67f766a8b5a0fdd5adcaf1a060f0e766ca079cff7b` |
| `runs/model-player/t140-scripted-w90-r1/match3/scripted/filmstrip.png` | 154043 | `38bdbcea42c10e16e0b234c96e405ce2a007215f051c5739c5be1e6ca1503b78` |
| `runs/model-player/t140-scripted-w90-r1/match3/scripted/frames.json` | 611783 | `a9cba039e4103bb1dd99ce7448203b8993c6b2b785b257f7bc541ed5884a9353` |
| `runs/model-player/t140-scripted-w90-r1/match3/scripted/player.json` | 28887 | `6aee1dd468fa519c99c58d72f096f48b6454dbbed8b29a8eb737aed2068f4a99` |
| `runs/model-player/t140-scripted-w90-r1/match3/scripted/session.json` | 13903 | `cdc4af23afbf579992107e2856f8babf4c5a5a1d7043f8533be8ab3b2399cb53` |
| `runs/model-player/t140-scripted-w90-r1/match3/scripted/steps.jsonl` | 141698 | `3d4899a3260fc29ffa01b283b9293406ca4cfc537f54d75c09b942074665928b` |
| `calls/**`（1386 个文件，14854477 B）| — | `127d7653b49371f672c8a27dd03164207d1dc4faad471ca3dc36f6365c6a9c33` |
| `frames/**`（37 个文件，431921 B）| — | `afc023aa80f45a9b3641d9030a1fab503dd7dcbf07a96842a4224a64c211bf8e` |
| `states/**`（27 个文件，330696 B）| — | `544c89203efb56dd3a2d30aa87d369a9a4eea61e21996b4d9c19448f5b077e1a` |

## t140-scripted-w90-r1 / minesweeper / scripted

* 目录：`runs/model-player/t140-scripted-w90-r1/minesweeper/scripted`
* verdict：`PASS`（counts_as_pass=True，strict=PASS，baseline=PASS，game_side=PASS）
* 档位+轮次：`PASS @w90 r1`（window=90，round=1，reporting=90，at_reporting_window=True，reporting_state=ok）
* 注入/接受后变化/rate：12 / 7 / 1.0
* 两窗对齐：7/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 2 frame(s))（matched 7/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game minesweeper --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9981 --window-frames 90 --round 1 --change-margin strict --out-prefix t140-scripted-w90-r1`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t140-scripted-w90-r1/minesweeper/scripted/demo.png` | 186291 | `827275f29072d6cee0af785ad55fdb6212ce6781742933299dc06f5671d34c4a` |
| `runs/model-player/t140-scripted-w90-r1/minesweeper/scripted/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t140-scripted-w90-r1/minesweeper/scripted/engine-game.stdout.txt` | 745 | `865b8561c908b334557972e62494a86a7bb73b2ba2f36b04d0052e68607be03b` |
| `runs/model-player/t140-scripted-w90-r1/minesweeper/scripted/filmstrip.png` | 182715 | `bb903653f3b27411a1d883980a94fcd0d53d7bb980bbac97557e61e6858d0426` |
| `runs/model-player/t140-scripted-w90-r1/minesweeper/scripted/frames.json` | 810416 | `a327b43fd02cc4bd4af30866e7282b7ede8020464e4998012812acd2be474edd` |
| `runs/model-player/t140-scripted-w90-r1/minesweeper/scripted/player.json` | 29953 | `1402eb5b9b8847266acf9e17e7c5c7caa52da6fc17717e6057353fd1d34448f9` |
| `runs/model-player/t140-scripted-w90-r1/minesweeper/scripted/session.json` | 14036 | `27c3d8e4125e95f460a109c242bc04c2fdf9fbccedf2fc93af057db56d985add` |
| `runs/model-player/t140-scripted-w90-r1/minesweeper/scripted/steps.jsonl` | 140942 | `222a0132c22e5c1fbf2e849ee70ba004630636df3e7a3524ab8729c73fc52812` |
| `calls/**`（1319 个文件，32950742 B）| — | `1ea1cc615e438d4955ad91da1217e8759d17ed5d7488ca1d00c3c606746433a2` |
| `frames/**`（37 个文件，580787 B）| — | `26ce272591f6dd8c74c3db7ed88154c711729ee59fa7c20a37902fc7b7b0e289` |
| `states/**`（27 个文件，787281 B）| — | `345adae01bf689a77b5c6967a69dffff196a2e975d7d30ed1f2dbb0485c769f7` |

## t140-scripted-w90-r1 / missilecommand / scripted

* 目录：`runs/model-player/t140-scripted-w90-r1/missilecommand/scripted`
* verdict：`PASS`（counts_as_pass=True，strict=PASS，baseline=PASS，game_side=PASS）
* 档位+轮次：`PASS @w90 r1`（window=90，round=1，reporting=90，at_reporting_window=True，reporting_state=ok）
* 注入/接受后变化/rate：8 / 8 / 1.0
* 两窗对齐：4/8 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 1 frame(s))（matched 4/8，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game missilecommand --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9981 --window-frames 90 --round 1 --change-margin strict --out-prefix t140-scripted-w90-r1`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t140-scripted-w90-r1/missilecommand/scripted/demo.png` | 108824 | `77337a51aa2d60b768712839dfc3de9b3f8102b9fec3809a0d13f54579e4e82e` |
| `runs/model-player/t140-scripted-w90-r1/missilecommand/scripted/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t140-scripted-w90-r1/missilecommand/scripted/engine-game.stdout.txt` | 742 | `f7cba23dd005fff75edbea0b69f0009e95cf2df356f37aeaf6c524dc942da295` |
| `runs/model-player/t140-scripted-w90-r1/missilecommand/scripted/filmstrip.png` | 56306 | `5fff3de1a77b7398fc08197f66db8df38f0784c122767d5c12a0c051351e5332` |
| `runs/model-player/t140-scripted-w90-r1/missilecommand/scripted/frames.json` | 497604 | `c06c592020113fe5fd25d428193bb7143f1fc8f823bc40cbbf4391a9ed742d0b` |
| `runs/model-player/t140-scripted-w90-r1/missilecommand/scripted/player.json` | 22506 | `b2b9b4bed3bf4b80211e1b1fd289757675985e49b0b501364db880395c54a562` |
| `runs/model-player/t140-scripted-w90-r1/missilecommand/scripted/session.json` | 12417 | `026fda2e0903570aa265b173a4537239ab8675797eaff6a6d448c39f96d6db15` |
| `runs/model-player/t140-scripted-w90-r1/missilecommand/scripted/steps.jsonl` | 98133 | `7ddade7ea72695095f20a21664c8b75dd238de3a212021acd94f2af5de2ba6a8` |
| `calls/**`（889 个文件，17527365 B）| — | `838adf59f761159089d1de950707f7b5c8cc45b0c36fb0f8808d0890de1cf6e7` |
| `frames/**`（25 个文件，354928 B）| — | `622cc02f5b2cb2893f7c485eb4863a89a5268de7ae3559c39121c6b83592fbff` |
| `states/**`（19 个文件，441907 B）| — | `4925edd3a9b00998e023839f14dfe04905985e1e1601d162b0148988c8dc30aa` |

## t140-scripted-w90-r1 / pacman / scripted

* 目录：`runs/model-player/t140-scripted-w90-r1/pacman/scripted`
* verdict：`PASS`（counts_as_pass=True，strict=PASS，baseline=PASS，game_side=PASS）
* 档位+轮次：`PASS @w90 r1`（window=90，round=1，reporting=90，at_reporting_window=True，reporting_state=ok）
* 注入/接受后变化/rate：12 / 7 / 1.0
* 两窗对齐：5/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 1 frame(s))（matched 5/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game pacman --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9981 --window-frames 90 --round 1 --change-margin strict --out-prefix t140-scripted-w90-r1`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t140-scripted-w90-r1/pacman/scripted/demo.png` | 146478 | `b2ac36203d74153f2e14cfa946cbeb6e9f4a63bd0761e54e53fcb22702c19a8d` |
| `runs/model-player/t140-scripted-w90-r1/pacman/scripted/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t140-scripted-w90-r1/pacman/scripted/engine-game.stdout.txt` | 733 | `7ad59a9195cb2c3d6095f8a711dd99528076c8fb3549824da53b900b1ea72f5e` |
| `runs/model-player/t140-scripted-w90-r1/pacman/scripted/filmstrip.png` | 146874 | `889c8b55347b4e8ebb9a5c7d98015b64eac09b169105d5192898e49cda287669` |
| `runs/model-player/t140-scripted-w90-r1/pacman/scripted/frames.json` | 583966 | `77358adb83b9e48fc1cd490be2ce4d108b57daa873b77cb5fdf087810f052eb9` |
| `runs/model-player/t140-scripted-w90-r1/pacman/scripted/player.json` | 29264 | `640711a406cedf9ee9dfac396f806818ffc6e99b68495957a670dd5c2daaafd2` |
| `runs/model-player/t140-scripted-w90-r1/pacman/scripted/session.json` | 13467 | `d335210210d9e1e6dfac284fb46697e167a22c363990585a56a6063d91ad6646` |
| `runs/model-player/t140-scripted-w90-r1/pacman/scripted/steps.jsonl` | 143610 | `96dc254451d32383046047ebb2a403a04d8e28513d1f921f52e91a7e971bd2ca` |
| `calls/**`（1298 个文件，45658686 B）| — | `ea8984eb24fcb5b0d05703a5b7f954105aeaed9d4b7aa643ba43a97700297830` |
| `frames/**`（37 个文件，411185 B）| — | `c7a7debc1a24775dd2d651d5f0a5ea0a889376f29b16c2b01978cdd359a154d2` |
| `states/**`（27 个文件，1153931 B）| — | `5a81ae3e98c7d867d6fcc6eeebac38cbfeb06fabfa9ea1d65c7e0430ad007c11` |

## t140-scripted-w90-r1 / platformer / scripted

* 目录：`runs/model-player/t140-scripted-w90-r1/platformer/scripted`
* verdict：`INCONCLUSIVE`（counts_as_pass=False，strict=INCONCLUSIVE，baseline=INCONCLUSIVE，game_side=FAIL）
* 档位+轮次：`INCONCLUSIVE @w90 r1`（window=90，round=1，reporting=90，at_reporting_window=True，reporting_state=ok）
* 注入/接受后变化/rate：6 / 3 / 0.5
* 两窗对齐：2/6 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 2 frame(s))（matched 2/6，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game platformer --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9981 --window-frames 90 --round 1 --change-margin strict --out-prefix t140-scripted-w90-r1`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t140-scripted-w90-r1/platformer/scripted/demo.png` | 82215 | `0907c0d5f870a8e3f12dbac2c49597070e88b76e21624d30dfca6de80923f7c6` |
| `runs/model-player/t140-scripted-w90-r1/platformer/scripted/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t140-scripted-w90-r1/platformer/scripted/engine-game.stdout.txt` | 796 | `1685175067406e18ecfda2df5c4f2e91f31113d184807b6ea9a6c58a729c2093` |
| `runs/model-player/t140-scripted-w90-r1/platformer/scripted/filmstrip.png` | 51784 | `caeb8f313ef44d4fc3b790b43db7714dfe4731d4996bad4f57f1e7b49071cf7a` |
| `runs/model-player/t140-scripted-w90-r1/platformer/scripted/frames.json` | 282888 | `0fb477c4be901c18829c16e2120ee960ea788d142845a75fb7ac7f10dcf28562` |
| `runs/model-player/t140-scripted-w90-r1/platformer/scripted/player.json` | 24279 | `6275f7b5776bd068db4a89d193b2cf71bafd94cfb4955d86b817c0cf238feb5e` |
| `runs/model-player/t140-scripted-w90-r1/platformer/scripted/session.json` | 12157 | `f94eb02f0a9ddbe78da29ac478cd3f105640ea1203338b6604032f59b4c4bb82` |
| `runs/model-player/t140-scripted-w90-r1/platformer/scripted/steps.jsonl` | 78697 | `e8cb5f81298ae06914201118f75d8d66a2f92c8a0a413f145da91db8fa708176` |
| `calls/**`（649 个文件，11843451 B）| — | `735f52de35effe18d8e54379d4fd1f7d96fc67d77519a4979d1951e27ba32014` |
| `frames/**`（19 个文件，198367 B）| — | `4e2f5e15f95f35120b25fbaa60c3690d1706b927eaf29eecc2174cf238b8b6e1` |
| `states/**`（15 个文件，322470 B）| — | `e9c2eba7fb5afd11e222eab531b48a54586372050898a74e88d3db9f831f5cd3` |

## t140-scripted-w90-r1 / pong / scripted

* 目录：`runs/model-player/t140-scripted-w90-r1/pong/scripted`
* verdict：`PASS`（counts_as_pass=True，strict=PASS，baseline=PASS，game_side=PASS）
* 档位+轮次：`PASS @w90 r1`（window=90，round=1，reporting=90，at_reporting_window=True，reporting_state=ok）
* 注入/接受后变化/rate：8 / 8 / 1.0
* 两窗对齐：3/8 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 2 frame(s))（matched 3/8，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game pong --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9981 --window-frames 90 --round 1 --change-margin strict --out-prefix t140-scripted-w90-r1`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t140-scripted-w90-r1/pong/scripted/demo.png` | 55877 | `86386b0f1935a732045bcebf462327b8d5f495cf328a3c45378f968bbddaf082` |
| `runs/model-player/t140-scripted-w90-r1/pong/scripted/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t140-scripted-w90-r1/pong/scripted/engine-game.stdout.txt` | 4195 | `b764980306519f7cbd635082f2f2c97f45280820da63ccd33f18ddefe14a1b85` |
| `runs/model-player/t140-scripted-w90-r1/pong/scripted/filmstrip.png` | 35553 | `3f0ffcc40d9ea559ea3a1e137bf024a3f7311e315972c3ba79595cd6ad998cf2` |
| `runs/model-player/t140-scripted-w90-r1/pong/scripted/frames.json` | 221144 | `dcc7ce3ee83e76cd96ce362e9d048c267dec33c99f13b3a92d567f2fa58c8a6e` |
| `runs/model-player/t140-scripted-w90-r1/pong/scripted/player.json` | 22349 | `3974d298d2006418d4da4a3eb53070d15a1214be521b88afd54bde42108879ee` |
| `runs/model-player/t140-scripted-w90-r1/pong/scripted/session.json` | 12322 | `a6d1606936a17d29a0d4d46d7322471845c03131f524869c538580ceee030de9` |
| `runs/model-player/t140-scripted-w90-r1/pong/scripted/steps.jsonl` | 91796 | `85f05d24e349a1f226efbaa297ddbf295f8cb5fbed873aaed56b8cf98caa4ec7` |
| `calls/**`（880 个文件，2272686 B）| — | `5b1af50344366666bbeb25d2648d9ad4c2afebaeff2dcb24eca44569c31c2679` |
| `frames/**`（25 个文件，147885 B）| — | `f4cb7f809c7365390fc0c32b0fe3f64ae2513ccbc52f94abbd63e66d370e620c` |
| `states/**`（19 个文件，46297 B）| — | `10fd901673d3d1ae7a2300e1bb9627659e5a617b8d4beca1c70688f8130b82c3` |

## t140-scripted-w90-r1 / puzzlebobble / scripted

* 目录：`runs/model-player/t140-scripted-w90-r1/puzzlebobble/scripted`
* verdict：`PASS`（counts_as_pass=True，strict=PASS，baseline=PASS，game_side=PASS）
* 档位+轮次：`PASS @w90 r1`（window=90，round=1，reporting=90，at_reporting_window=True，reporting_state=ok）
* 注入/接受后变化/rate：8 / 8 / 1.0
* 两窗对齐：5/8 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 2 frame(s))（matched 5/8，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game puzzlebobble --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9981 --window-frames 90 --round 1 --change-margin strict --out-prefix t140-scripted-w90-r1`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t140-scripted-w90-r1/puzzlebobble/scripted/demo.png` | 138756 | `2b46e1d279c7c33b6518fc23d4a65eb9f24444694314ec4f292ca2cd31383f3e` |
| `runs/model-player/t140-scripted-w90-r1/puzzlebobble/scripted/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t140-scripted-w90-r1/puzzlebobble/scripted/engine-game.stdout.txt` | 739 | `625657264f9d8a87c69f6b397f3998464725b7ddfbc721a6968686b9a0935159` |
| `runs/model-player/t140-scripted-w90-r1/puzzlebobble/scripted/filmstrip.png` | 83632 | `87d297d66adb426d0bc397b4e07c73ddaf11f871f4d185be485901f7ea1b4266` |
| `runs/model-player/t140-scripted-w90-r1/puzzlebobble/scripted/frames.json` | 482040 | `4b332b0b1ca1a60bac77e955f118106963ed9af56b1a05dae652c87ed38c1bec` |
| `runs/model-player/t140-scripted-w90-r1/puzzlebobble/scripted/player.json` | 22475 | `d0aeb465b58a893f86a75490ab1d720fad45a1eb9c99a8543199c3723a8d1984` |
| `runs/model-player/t140-scripted-w90-r1/puzzlebobble/scripted/session.json` | 12308 | `c63f46a597b89e5800d3018c3e5bd995853b8973e5ccaa380e5269d8d271baf5` |
| `runs/model-player/t140-scripted-w90-r1/puzzlebobble/scripted/steps.jsonl` | 98516 | `89de9dd03699305562d9d1d97335ad6567ca9b355d3985ea3e3b8b17006b7cd0` |
| `calls/**`（895 个文件，15275796 B）| — | `da451e65a1eac4d44393c48335184aef7e3b7e9fe1e57e9417beddd4a9716ba6` |
| `frames/**`（25 个文件，343266 B）| — | `0ddf50e86066041a4a717ff4ffb38d0dcf026bccb86ee7678d7b326ec48a6d86` |
| `states/**`（19 个文件，379479 B）| — | `a46b0898cb83884cd12830652dc159a0f8b7aa6981609e404a9e6d38bffef5c7` |

## t140-scripted-w90-r1 / rtype / scripted

* 目录：`runs/model-player/t140-scripted-w90-r1/rtype/scripted`
* verdict：`PASS`（counts_as_pass=True，strict=PASS，baseline=PASS，game_side=PASS）
* 档位+轮次：`PASS @w90 r1`（window=90，round=1，reporting=90，at_reporting_window=True，reporting_state=ok）
* 注入/接受后变化/rate：8 / 8 / 1.0
* 两窗对齐：4/8 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 1 frame(s))（matched 4/8，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game rtype --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9981 --window-frames 90 --round 1 --change-margin strict --out-prefix t140-scripted-w90-r1`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t140-scripted-w90-r1/rtype/scripted/demo.png` | 120935 | `ad4b653e3f155de1c1039f9c31c3c0a488c288966de635bc021fc8e4d02d6203` |
| `runs/model-player/t140-scripted-w90-r1/rtype/scripted/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t140-scripted-w90-r1/rtype/scripted/engine-game.stdout.txt` | 743 | `39382eca3d388152e8d094a7a17d0ede353d04c6bfc133b433e92baade6018f6` |
| `runs/model-player/t140-scripted-w90-r1/rtype/scripted/filmstrip.png` | 69537 | `684622463ae3fca5c0c83dd510a30b7f9b7731661f7bdb6e5966cebfc4b12ab3` |
| `runs/model-player/t140-scripted-w90-r1/rtype/scripted/frames.json` | 430228 | `d4c166369592ca7777e5e127098120866312c7f67361524f2d828c19e5e5e616` |
| `runs/model-player/t140-scripted-w90-r1/rtype/scripted/player.json` | 22463 | `86f112f0658c37e8e7fd09c5fa9a2d4afaa74ad4fee67230baa5c480fd859427` |
| `runs/model-player/t140-scripted-w90-r1/rtype/scripted/session.json` | 12252 | `1a36f15c6f0f448da195d1302ec9b20c9c2e41ac7112b0a3789bbed0da46b3f5` |
| `runs/model-player/t140-scripted-w90-r1/rtype/scripted/steps.jsonl` | 97495 | `27b4b123b3b6e7781463866ae57cbcd1e01078c2d403acbde59fbfdcb79fbfe1` |
| `calls/**`（897 个文件，14171259 B）| — | `227b550b0e19573056213b66070de8f08414612fa7682d36b07a416394137fa8` |
| `frames/**`（25 个文件，304672 B）| — | `1ab54b870f4a0fc5fa3d781a91da229d901e658898f04d42a1fd14af1cd4b600` |
| `states/**`（19 个文件，351745 B）| — | `107be7ca5bcf64004a103231ecfe6307bb7b74b7b8ae369d6d16e93ca0bc7dad` |

## t140-scripted-w90-r1 / snake / scripted

* 目录：`runs/model-player/t140-scripted-w90-r1/snake/scripted`
* verdict：`PASS`（counts_as_pass=True，strict=PASS，baseline=PASS，game_side=PASS）
* 档位+轮次：`PASS @w90 r1`（window=90，round=1，reporting=90，at_reporting_window=True，reporting_state=ok）
* 注入/接受后变化/rate：8 / 8 / 1.0
* 两窗对齐：4/8 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 3 frame(s))（matched 4/8，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game snake --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9981 --window-frames 90 --round 1 --change-margin strict --out-prefix t140-scripted-w90-r1`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t140-scripted-w90-r1/snake/scripted/demo.png` | 44716 | `a15e6a91b4df883c9e668af539ce764722351657abf554b26fe399925af3b4ee` |
| `runs/model-player/t140-scripted-w90-r1/snake/scripted/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t140-scripted-w90-r1/snake/scripted/engine-game.stdout.txt` | 9537 | `04264139c31b600881fbbfdd92c482538b96c4e3247e3c4b1066971fe76f2939` |
| `runs/model-player/t140-scripted-w90-r1/snake/scripted/filmstrip.png` | 30716 | `10624087db10231db98f7a488d60c4a9d94932b051c83e813c01725bb2395993` |
| `runs/model-player/t140-scripted-w90-r1/snake/scripted/frames.json` | 127019 | `d35766a47b500a7449bd56edf2736a239c9872a593ef34ca68635bb6796de079` |
| `runs/model-player/t140-scripted-w90-r1/snake/scripted/player.json` | 22466 | `bcae25f7f2dd67e1a01dd9e1074ac7491c4e6360c1407974f31627cfb2075185` |
| `runs/model-player/t140-scripted-w90-r1/snake/scripted/session.json` | 12884 | `5e5eb5d6b88b604c8d97496d6c5cd0a21549c413aa475376e2a661dcdb3abe3f` |
| `runs/model-player/t140-scripted-w90-r1/snake/scripted/steps.jsonl` | 103102 | `6809fef8776b4515814a14e6ee62c664d5320fac6e5368d68652f1a0ff33bf1d` |
| `calls/**`（647 个文件，4937831 B）| — | `14c1369380cd02f0547cbbb4ead081620b405044586b1803ed4792e914f4dad9` |
| `frames/**`（25 个文件，77380 B）| — | `f389dcfb62a35cb652070313a04ce6237d6919dc28908c49f7d793e7a3ae2fa4` |
| `states/**`（19 个文件，166646 B）| — | `c85baf4312882118eb374ebbae3c96f49c3eecdfaf60d8c86f4fb6ec8ea11e58` |

## t140-scripted-w90-r1 / sokoban / scripted

* 目录：`runs/model-player/t140-scripted-w90-r1/sokoban/scripted`
* verdict：`PASS`（counts_as_pass=True，strict=PASS，baseline=PASS，game_side=PASS）
* 档位+轮次：`PASS @w90 r1`（window=90，round=1，reporting=90，at_reporting_window=True，reporting_state=ok）
* 注入/接受后变化/rate：12 / 9 / 1.0
* 两窗对齐：7/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 1 frame(s))（matched 7/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game sokoban --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9981 --window-frames 90 --round 1 --change-margin strict --out-prefix t140-scripted-w90-r1`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t140-scripted-w90-r1/sokoban/scripted/demo.png` | 139576 | `8d59192b1c13f355664beec196550cdff3fa531986c1e8ad5af3be4e764560b1` |
| `runs/model-player/t140-scripted-w90-r1/sokoban/scripted/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t140-scripted-w90-r1/sokoban/scripted/engine-game.stdout.txt` | 745 | `7d6ba91417af3c05c1df9fdbc4ad001c2da00a4e7b2594189b7594eec8e7a372` |
| `runs/model-player/t140-scripted-w90-r1/sokoban/scripted/filmstrip.png` | 107313 | `22f71c379de06c60d2abaefe078356f5413c6b07608869326e69fd633b7ae453` |
| `runs/model-player/t140-scripted-w90-r1/sokoban/scripted/frames.json` | 647059 | `39815d2613b13807f74f39284f5ceefdf50f02da4045e0d82baea254324e01bd` |
| `runs/model-player/t140-scripted-w90-r1/sokoban/scripted/player.json` | 27800 | `8fabb459365368deae582f5ac86e33d499ecc498dda494b70da806b70d460b91` |
| `runs/model-player/t140-scripted-w90-r1/sokoban/scripted/session.json` | 13616 | `28d6b3fae9730c21f95aeacd0bae2fd9db068cb8f5f2db38f8d9056de653c51c` |
| `runs/model-player/t140-scripted-w90-r1/sokoban/scripted/steps.jsonl` | 147955 | `2f8ce2d9523186d09b98d8593bbe1a1e9a106adffe09ace5b8580e437033e219` |
| `calls/**`（1345 个文件，16545801 B）| — | `9ae0c30bdaa41f775da9253c916f5c09e658034f0d8e726b35a2301badc1ffe3` |
| `frames/**`（37 个文件，458340 B）| — | `52a26e95f2a6fb54d60746a039a81ababb559e85c697b54d967305d917ec2434` |
| `states/**`（27 个文件，374450 B）| — | `185156f8287cad52b3f0cd84d3ad134d68fb08539db6d1b8cbf28a5f2b8e0ce0` |

## t140-scripted-w90-r1 / spaceinvaders / scripted

* 目录：`runs/model-player/t140-scripted-w90-r1/spaceinvaders/scripted`
* verdict：`PASS`（counts_as_pass=True，strict=PASS，baseline=PASS，game_side=PASS）
* 档位+轮次：`PASS @w90 r1`（window=90，round=1，reporting=90，at_reporting_window=True，reporting_state=ok）
* 注入/接受后变化/rate：8 / 8 / 1.0
* 两窗对齐：6/8 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 1 frame(s))（matched 6/8，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game spaceinvaders --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9981 --window-frames 90 --round 1 --change-margin strict --out-prefix t140-scripted-w90-r1`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t140-scripted-w90-r1/spaceinvaders/scripted/demo.png` | 85916 | `a70ae5bb1d303cd982c6463f4688ce75bc42dde5995066297690df6ed215eb95` |
| `runs/model-player/t140-scripted-w90-r1/spaceinvaders/scripted/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t140-scripted-w90-r1/spaceinvaders/scripted/engine-game.stdout.txt` | 754 | `d5931951df43356cc2b0ce7ad46ed78e1b987feb9520f3a789f3b848d2bfb5b9` |
| `runs/model-player/t140-scripted-w90-r1/spaceinvaders/scripted/filmstrip.png` | 59991 | `7f389d6261f31455be7451285a60fcf8b0a151ef6ddadd8eda5c8a1e5f2a7d8d` |
| `runs/model-player/t140-scripted-w90-r1/spaceinvaders/scripted/frames.json` | 348207 | `6afb1999bc01263cdce449132f84b7581dca38696877f31aad1e08e06feacb2a` |
| `runs/model-player/t140-scripted-w90-r1/spaceinvaders/scripted/player.json` | 22489 | `3691aa97440987a87716a7de0817ca5185c971d0d067a4d5c04300ebe3e3d744` |
| `runs/model-player/t140-scripted-w90-r1/spaceinvaders/scripted/session.json` | 12222 | `268b7be3ab09bc1560135e1c331f55135b821092c8b60f89609a813d4932dfb8` |
| `runs/model-player/t140-scripted-w90-r1/spaceinvaders/scripted/steps.jsonl` | 97754 | `4b6e36b62f6f6f9f697dbcb2f41b467fd6b23709913fd9ab4316b3243bd1c734` |
| `calls/**`（909 个文件，7264162 B）| — | `46571f26375f50132553e8fbf9e60e50693008b8f00b308c59937ef96b26a3f3` |
| `frames/**`（25 个文件，242861 B）| — | `9d0657b84160f1ef007e660c6e24c51d2727ddc5aa742290c3c6e08d1c03b695` |
| `states/**`（19 个文件，169612 B）| — | `eab0fec4189899826cd9d96299eed8623fae837ef90306137ff4a5930e704ae5` |

## t140-scripted-w90-r1 / tetris / scripted

* 目录：`runs/model-player/t140-scripted-w90-r1/tetris/scripted`
* verdict：`PASS`（counts_as_pass=True，strict=PASS，baseline=PASS，game_side=PASS）
* 档位+轮次：`PASS @w90 r1`（window=90，round=1，reporting=90，at_reporting_window=True，reporting_state=ok）
* 注入/接受后变化/rate：8 / 8 / 1.0
* 两窗对齐：6/8 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 1 frame(s))（matched 6/8，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game tetris --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9981 --window-frames 90 --round 1 --change-margin strict --out-prefix t140-scripted-w90-r1`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t140-scripted-w90-r1/tetris/scripted/demo.png` | 51366 | `d63646b22803d99e27d3e4c201ef7e0ecec39c44656e64e3afeeb73f502c79f5` |
| `runs/model-player/t140-scripted-w90-r1/tetris/scripted/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t140-scripted-w90-r1/tetris/scripted/engine-game.stdout.txt` | 8802 | `fb00c9865b9b4b64c2a2ca0b60f55f1a53c1730f750b27f4e354a6fbafa38888` |
| `runs/model-player/t140-scripted-w90-r1/tetris/scripted/filmstrip.png` | 34096 | `cd85452d53a798b699c464c46417fdb682402fee602c4cac11ccb69e3654cb38` |
| `runs/model-player/t140-scripted-w90-r1/tetris/scripted/frames.json` | 196100 | `e94c7a50b599e53b025e90e5465c7fe610bf71e08ba4c0dca0ae440bb665bb56` |
| `runs/model-player/t140-scripted-w90-r1/tetris/scripted/player.json` | 22553 | `afcb8ec1743e4f4e8e90c23761ef5d63ceb62fc0b735ce819444f0dc850be054` |
| `runs/model-player/t140-scripted-w90-r1/tetris/scripted/session.json` | 12106 | `5214bc38f7b814e01ce0bbe32b29a05cfe42c0a57106f2b6bede6a7562585601` |
| `runs/model-player/t140-scripted-w90-r1/tetris/scripted/steps.jsonl` | 86988 | `28419d58f9fb92bff1a0911316ff5fdca48e89f44935d56735d1027cc53b9b14` |
| `calls/**`（943 个文件，1706001 B）| — | `fe726ced822cd392069bf444269dd45bada279986f614aab2c5bd1ceed488453` |
| `frames/**`（25 个文件，128882 B）| — | `c875bd1d3e35eec4e287cb4c42802ea7c0c95563ebf4554442bcfa6adb43470b` |
| `states/**`（19 个文件，29824 B）| — | `26628f278dec0232e421f55fc66121ed8a66667de91c4443ac2ba34b57edb4eb` |

## t140-scripted-w90-r1 / towerdefense / scripted

* 目录：`runs/model-player/t140-scripted-w90-r1/towerdefense/scripted`
* verdict：`PASS`（counts_as_pass=True，strict=PASS，baseline=PASS，game_side=PASS）
* 档位+轮次：`PASS @w90 r1`（window=90，round=1，reporting=90，at_reporting_window=True，reporting_state=ok）
* 注入/接受后变化/rate：12 / 9 / 1.0
* 两窗对齐：7/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 2 frame(s))（matched 7/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game towerdefense --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9981 --window-frames 90 --round 1 --change-margin strict --out-prefix t140-scripted-w90-r1`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t140-scripted-w90-r1/towerdefense/scripted/demo.png` | 163764 | `94d0b6b64960faf6c9336da8ae6d2c271c123a94fc21c6ce9f1f69c6b563a3af` |
| `runs/model-player/t140-scripted-w90-r1/towerdefense/scripted/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t140-scripted-w90-r1/towerdefense/scripted/engine-game.stdout.txt` | 753 | `698c7e9dabdb7f9dde87915a76ff8c5ab006015ccc1fd4e6cf8c265d011bb325` |
| `runs/model-player/t140-scripted-w90-r1/towerdefense/scripted/filmstrip.png` | 131272 | `a99807424101d51b52c9b7906e2bf78e57d52e95b8b0cc6de12da8a3c2f9e22b` |
| `runs/model-player/t140-scripted-w90-r1/towerdefense/scripted/frames.json` | 638118 | `a3496996b973bc8b5430cc9dad01613633dffda1c5303950dadcb60ae9c1fabf` |
| `runs/model-player/t140-scripted-w90-r1/towerdefense/scripted/player.json` | 27981 | `84d1a78bcfab4b6be2e7a7edcf10a9f4f197fd18d70ed5e3e470a461e5f1d0c7` |
| `runs/model-player/t140-scripted-w90-r1/towerdefense/scripted/session.json` | 13861 | `f64c3fab36c30c999fd185e4e643d60134d9899f39fc5a7e9712a96d9d5b0c58` |
| `runs/model-player/t140-scripted-w90-r1/towerdefense/scripted/steps.jsonl` | 138610 | `1c36065efb5818c5510a6563da2e85c6b454b95e94765acf2d66def56a3979fe` |
| `calls/**`（1324 个文件，26771329 B）| — | `66bef415d9b38d2da72bd6d1a573c007161edb3c8f8efc4ad313fb4b66d61440` |
| `frames/**`（37 个文件，451587 B）| — | `c201b5ea35b43063dfc7dad63d72342971c4e94180c8fc7cfe5532f760f83ddc` |
| `states/**`（27 个文件，648205 B）| — | `ddd86188e67cfe27275b7def3940324d63da985214982141883d5039ab8d05e4` |

## t140-scripted-w90-r2 / asteroids / scripted

* 目录：`runs/model-player/t140-scripted-w90-r2/asteroids/scripted`
* verdict：`PASS`（counts_as_pass=True，strict=PASS，baseline=PASS，game_side=PASS）
* 档位+轮次：`PASS @w90 r2`（window=90，round=2，reporting=90，at_reporting_window=True，reporting_state=ok）
* 注入/接受后变化/rate：8 / 8 / 1.0
* 两窗对齐：4/8 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 1 frame(s))（matched 4/8，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game asteroids --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9982 --window-frames 90 --round 2 --change-margin strict --out-prefix t140-scripted-w90-r2`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t140-scripted-w90-r2/asteroids/scripted/demo.png` | 88026 | `158f023cc41889d34b10223593d71204b1919985567c23608661f1d454163ba4` |
| `runs/model-player/t140-scripted-w90-r2/asteroids/scripted/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t140-scripted-w90-r2/asteroids/scripted/engine-game.stdout.txt` | 741 | `a5c81d170b128e4b809f37591c1ad4b2d59f624f6561ecfa8dcdd4ac4d2b3c1a` |
| `runs/model-player/t140-scripted-w90-r2/asteroids/scripted/filmstrip.png` | 48735 | `2488d47fc754b4130e63b1da1a78072120885191f2a9d59835fc895f1c0466a5` |
| `runs/model-player/t140-scripted-w90-r2/asteroids/scripted/frames.json` | 370613 | `e910aff98e6929b2bad5278fcaaeee33955e777e0a84adc545ed8fbef5a3b560` |
| `runs/model-player/t140-scripted-w90-r2/asteroids/scripted/player.json` | 22496 | `3cc6de902f39cdf87bcc15f6e6b857f68d26b8d1864d9ebf4af6f6d9dd70daf5` |
| `runs/model-player/t140-scripted-w90-r2/asteroids/scripted/session.json` | 12189 | `f99f0318efaeb7a4dc8fe0bf2c559728ba9070dc5e8523a1b066980cbb43921e` |
| `runs/model-player/t140-scripted-w90-r2/asteroids/scripted/steps.jsonl` | 100255 | `da2884a77c86ba26d687a8a2d6ea013a9a4f1e536448504fd490264e51ac158a` |
| `calls/**`（969 个文件，3206632 B）| — | `21a0c417afc3229e156062b1ec789f9ce66fa26fa9a27af5fb4a35d3ebecc203` |
| `frames/**`（25 个文件，259783 B）| — | `7c9087eb86e7654c960bbe0553a32cfed86de4975e1d2da0364bfd515b8d3242` |
| `states/**`（19 个文件，58730 B）| — | `9811ddc78bdd58f3f37ddfa1a331d6ae92b245eb9b82233ba2d3d23bd91d0945` |

## t140-scripted-w90-r2 / bomberman / scripted

* 目录：`runs/model-player/t140-scripted-w90-r2/bomberman/scripted`
* verdict：`PASS`（counts_as_pass=True，strict=PASS，baseline=PASS，game_side=PASS）
* 档位+轮次：`PASS @w90 r2`（window=90，round=2，reporting=90，at_reporting_window=True，reporting_state=ok）
* 注入/接受后变化/rate：12 / 6 / 1.0
* 两窗对齐：7/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 3 frame(s))（matched 7/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game bomberman --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9982 --window-frames 90 --round 2 --change-margin strict --out-prefix t140-scripted-w90-r2`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t140-scripted-w90-r2/bomberman/scripted/demo.png` | 155674 | `13ff9e9dfc93545dd24f74fc479fddf868739446811f7e9142fe0948bb0f84eb` |
| `runs/model-player/t140-scripted-w90-r2/bomberman/scripted/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t140-scripted-w90-r2/bomberman/scripted/engine-game.stdout.txt` | 775 | `54cdf1c1aa0b496fda34934b4984d530f0941735a5438660c1cec7c1eba32d9f` |
| `runs/model-player/t140-scripted-w90-r2/bomberman/scripted/filmstrip.png` | 145036 | `69414bcc6012f58ff2d580e5537c5b8a0bdb0882c489543a267bc9a73ca3a840` |
| `runs/model-player/t140-scripted-w90-r2/bomberman/scripted/frames.json` | 512360 | `c67571a21ea5e5a75a2a90e187052cfa18cdce53d49dc28d739aa2f8589dab98` |
| `runs/model-player/t140-scripted-w90-r2/bomberman/scripted/player.json` | 30343 | `949cce25a4804ee834abab771f06138752c356fef396a06c0992e5f0f0a9c0e6` |
| `runs/model-player/t140-scripted-w90-r2/bomberman/scripted/session.json` | 13062 | `2d63dd7e71c98d2d95b996125d49fde2f46b6b81032d558ae94971ef896c67aa` |
| `runs/model-player/t140-scripted-w90-r2/bomberman/scripted/steps.jsonl` | 146989 | `ce5514f73d02a0a95f0f41015b591cfeb7f98025ce3c5dea035f741715521a60` |
| `calls/**`（1340 个文件，25206758 B）| — | `832ecb5c404706d946959281032300db3bc090e365c43ce89a5f545c91a5fd44` |
| `frames/**`（37 个文件，357249 B）| — | `47564a604da8ee2677cd89a405acaa69e01103e6bca2e4e607e58097738401fc` |
| `states/**`（27 个文件，603046 B）| — | `8f15e4e1ac6cd96e75f1df6d369b13ec56220ea8ffb6268793b4dbb47f27f0b6` |

## t140-scripted-w90-r2 / breakout / scripted

* 目录：`runs/model-player/t140-scripted-w90-r2/breakout/scripted`
* verdict：`INCONCLUSIVE`（counts_as_pass=False，strict=INCONCLUSIVE，baseline=INCONCLUSIVE，game_side=INCONCLUSIVE）
* 档位+轮次：`INCONCLUSIVE @w90 r2`（window=90，round=2，reporting=90，at_reporting_window=True，reporting_state=ok）
* 注入/接受后变化/rate：2 / 2 / 1.0
* 两窗对齐：5/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 2 frame(s))（matched 5/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game breakout --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9982 --window-frames 90 --round 2 --change-margin strict --out-prefix t140-scripted-w90-r2`  <- t136_commands.jsonl
  * `D:/Anaconda/python.exe tools/playtest_player.py stability --run runs/model-player/t140-scripted-w90-r1/breakout/scripted/player.json --run runs/model-player/t140-scripted-w90-r2/breakout/scripted/player.json --run runs/model-player/t139-scripted-w90/breakout/scripted/player.json --out runs/model-player/_scripts/t140_unstable_breakout.json`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t140-scripted-w90-r2/breakout/scripted/demo.png` | 103914 | `8faeb68be3753380cdeafa6ee5f66705283f56475f003af7329245828b4e2058` |
| `runs/model-player/t140-scripted-w90-r2/breakout/scripted/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t140-scripted-w90-r2/breakout/scripted/engine-game.stdout.txt` | 5371 | `e87aa10d8055a9e070ea9df32408bf1720bb230b86c781c759d2dabecb06231c` |
| `runs/model-player/t140-scripted-w90-r2/breakout/scripted/filmstrip.png` | 74673 | `ee6f777805c30acc168011146f57825881bd5ea7c644c24d001f01a85897641e` |
| `runs/model-player/t140-scripted-w90-r2/breakout/scripted/frames.json` | 583619 | `42a8b405c1e65b61574dce67e11c342c3e7a299d3a1b5de7b84a5eb5775f0bc3` |
| `runs/model-player/t140-scripted-w90-r2/breakout/scripted/player.json` | 24637 | `97d8c0ca5d522bb89c344771057bb029026c063611e26a928c0dcfdfaa46b448` |
| `runs/model-player/t140-scripted-w90-r2/breakout/scripted/session.json` | 12353 | `e88239622bf062b0fa40bc2480ac59f9fe46ce7cf3681a69cf05036bf8aa54c5` |
| `runs/model-player/t140-scripted-w90-r2/breakout/scripted/steps.jsonl` | 122706 | `f8e8d7050449a76469e804dbc858dc0a92b5a248dd30790722393c060aeca9d6` |
| `calls/**`（994 个文件，5601509 B）| — | `c8104a19c6cb74ba2cb5a6613ae807a99dcf944a61c0192dd4a0cc227c3b2d51` |
| `frames/**`（37 个文件，410851 B）| — | `067dc9d80b323a6ad255c74f00865a9892aeebced8657aba79043ae58f31bb02` |
| `states/**`（27 个文件，148665 B）| — | `c41fbcfb985cfece6613aa5d8f1e8c9ddab622a3b5f30b6a5c51e2dd55b48e31` |

## t140-scripted-w90-r2 / flappy / scripted

* 目录：`runs/model-player/t140-scripted-w90-r2/flappy/scripted`
* verdict：`PASS(baseline only)`（counts_as_pass=False，strict=FAIL，baseline=PASS，game_side=FAIL）
* 档位+轮次：`PASS(baseline only) @w90 r2`（window=90，round=2，reporting=90，at_reporting_window=True，reporting_state=ok）
* 注入/接受后变化/rate：12 / 7 / 0.5833
* 两窗对齐：6/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 2 frame(s))（matched 6/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game flappy --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9982 --window-frames 90 --round 2 --change-margin strict --out-prefix t140-scripted-w90-r2`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t140-scripted-w90-r2/flappy/scripted/demo.png` | 110411 | `5c643f6af60c5f0b9a4aa5434dbc12ba405bf01cf6e9d2749c50fa9436b48403` |
| `runs/model-player/t140-scripted-w90-r2/flappy/scripted/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t140-scripted-w90-r2/flappy/scripted/engine-game.stdout.txt` | 743 | `9335cef7fc9483cccdd538a78c8fb09cf1f0c7292b5b8031c00eb16514a6c019` |
| `runs/model-player/t140-scripted-w90-r2/flappy/scripted/filmstrip.png` | 116190 | `953ab87e999b096122ccdfc1e337009ca46f6441be7754c2a06ec27469eb4479` |
| `runs/model-player/t140-scripted-w90-r2/flappy/scripted/frames.json` | 572034 | `f4f33987da742a46b1499a243841545800bf158364ca2442111261f86b857b90` |
| `runs/model-player/t140-scripted-w90-r2/flappy/scripted/player.json` | 29315 | `c9880850d5b770aba952250b0454221dabcd2b2c2c4c7ee912c645a17bfc3b6f` |
| `runs/model-player/t140-scripted-w90-r2/flappy/scripted/session.json` | 12141 | `8410167cdaa98b73878e84bca8b53bb24c110ad0d25c7168e9e880c9a44721b4` |
| `runs/model-player/t140-scripted-w90-r2/flappy/scripted/steps.jsonl` | 188403 | `6c93d0836ad19b6389e389d93af59ba1f306554f9245e808e10c7c28fd660ead` |
| `calls/**`（1444 个文件，4924117 B）| — | `652c7dd58138cbb49706f8756526896ca769b4b598d8dabcde5fd883764f79a3` |
| `frames/**`（37 个文件，402439 B）| — | `c04bc1f1a5cf446bc0a178376e3ab87f2e573cbf38b0ac511cfaf0fe9375f815` |
| `states/**`（27 个文件，87470 B）| — | `19fbe65db8da51f5257f7438aaf63ad495c1e489a8d329a92d5d624bac255f59` |

## t140-scripted-w90-r2 / frogger / scripted

* 目录：`runs/model-player/t140-scripted-w90-r2/frogger/scripted`
* verdict：`PASS`（counts_as_pass=True，strict=PASS，baseline=PASS，game_side=PASS）
* 档位+轮次：`PASS @w90 r2`（window=90，round=2，reporting=90，at_reporting_window=True，reporting_state=ok）
* 注入/接受后变化/rate：8 / 8 / 1.0
* 两窗对齐：4/8 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 2 frame(s))（matched 4/8，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game frogger --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9982 --window-frames 90 --round 2 --change-margin strict --out-prefix t140-scripted-w90-r2`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t140-scripted-w90-r2/frogger/scripted/demo.png` | 100474 | `554a11c0b48c915fdc02953022ef86c7d6dbc776d76a15ece834be6e907b92fe` |
| `runs/model-player/t140-scripted-w90-r2/frogger/scripted/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t140-scripted-w90-r2/frogger/scripted/engine-game.stdout.txt` | 748 | `8e29a679a43437d159918caef7f0b9a096e5c49e0e47679f33adbdf049c2c9ea` |
| `runs/model-player/t140-scripted-w90-r2/frogger/scripted/filmstrip.png` | 60493 | `c5da6c3227b12c0f95f5e6a1d52a9e8dab00988296d0d0a20162f25fbdd2b47b` |
| `runs/model-player/t140-scripted-w90-r2/frogger/scripted/frames.json` | 401768 | `6147ed0c8f629747e1f85fde211ae7cbb07108897fcb90a15b4bd2393dc16e00` |
| `runs/model-player/t140-scripted-w90-r2/frogger/scripted/player.json` | 22393 | `fcbf91c88c5a86982cf675c6a0907385f649a4ad4296318e5f95d72477f76d0f` |
| `runs/model-player/t140-scripted-w90-r2/frogger/scripted/session.json` | 12093 | `18958f2dd23d7271e17ceac7a573dc6759558da09cb301e791de3ae9687c4209` |
| `runs/model-player/t140-scripted-w90-r2/frogger/scripted/steps.jsonl` | 91072 | `72d20443cebf029dcb5187721549a2d8397988f5cc03bdc8416f1d6a39d0ef4d` |
| `calls/**`（974 个文件，4298570 B）| — | `5114176e8a43843db8dfe795cb16a963757c2c36975258392a996392b17a3fb6` |
| `frames/**`（25 个文件，283172 B）| — | `ff6364c548508ddcde22f5315bb44671b45fb05603d716f7f76a5259d2795dff` |
| `states/**`（19 个文件，84336 B）| — | `53783b41e8e35c36fe3941a5b36320bba8e73a65803e4a2791f56fd5bd8f809d` |

## t140-scripted-w90-r2 / game2048 / scripted

* 目录：`runs/model-player/t140-scripted-w90-r2/game2048/scripted`
* verdict：`PASS`（counts_as_pass=True，strict=PASS，baseline=PASS，game_side=PASS）
* 档位+轮次：`PASS @w90 r2`（window=90，round=2，reporting=90，at_reporting_window=True，reporting_state=ok）
* 注入/接受后变化/rate：8 / 8 / 1.0
* 两窗对齐：5/8 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 1 frame(s))（matched 5/8，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game game2048 --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9982 --window-frames 90 --round 2 --change-margin strict --out-prefix t140-scripted-w90-r2`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t140-scripted-w90-r2/game2048/scripted/demo.png` | 105326 | `96cd977cad7a157a05cd9b6c6bd772ba6d05f9e17ffbad42242d83a4ba36b822` |
| `runs/model-player/t140-scripted-w90-r2/game2048/scripted/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t140-scripted-w90-r2/game2048/scripted/engine-game.stdout.txt` | 781 | `c70cfd4cd565d85c4b1d3e613f5c6c0b742e4cd19d9fbd7f913e1eca95a709c0` |
| `runs/model-player/t140-scripted-w90-r2/game2048/scripted/filmstrip.png` | 65250 | `8b39ca1c5bc016326495bf62fcef6deb85db6194028962d7ac1691659d624cf2` |
| `runs/model-player/t140-scripted-w90-r2/game2048/scripted/frames.json` | 452932 | `548a56c76b9bcb5f606a47e5dbb7d286e859fcc1d62e785bfe4b185af99a6517` |
| `runs/model-player/t140-scripted-w90-r2/game2048/scripted/player.json` | 22352 | `d58f80ac2c440428e247527a8cb31e3c5f9f748eab762bf966af1bf5ad8f11fc` |
| `runs/model-player/t140-scripted-w90-r2/game2048/scripted/session.json` | 12046 | `387bd6100d34f8a8724626e04a50fe3fe93b369df322714eff6d36d58c21dcfe` |
| `runs/model-player/t140-scripted-w90-r2/game2048/scripted/steps.jsonl` | 104982 | `c24a21d088570263b5cc97166ecc371cd5d966f7a00abb145adb9cf20517bb2c` |
| `calls/**`（942 个文件，6649117 B）| — | `8421bbe82de4c92408ee3caeca03dadb2a9121e0f2af805f368ad712e1eefc77` |
| `frames/**`（25 个文件，321508 B）| — | `2f8cc6547859135d579d7cffc65332a44d6dff9c45eb8b12af65aa0d7cb8661c` |
| `states/**`（19 个文件，142694 B）| — | `c87af1f4bce085f2399d0c64880b20dea1f7f584d66535fe4bdb8a1b119f3c1b` |

## t140-scripted-w90-r2 / lunarlander / scripted

* 目录：`runs/model-player/t140-scripted-w90-r2/lunarlander/scripted`
* verdict：`PASS`（counts_as_pass=True，strict=PASS，baseline=PASS，game_side=PASS）
* 档位+轮次：`PASS @w90 r2`（window=90，round=2，reporting=90，at_reporting_window=True，reporting_state=ok）
* 注入/接受后变化/rate：8 / 8 / 1.0
* 两窗对齐：7/8 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 1 frame(s))（matched 7/8，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game lunarlander --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9982 --window-frames 90 --round 2 --change-margin strict --out-prefix t140-scripted-w90-r2`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t140-scripted-w90-r2/lunarlander/scripted/demo.png` | 107979 | `fe675c0ccd51f4a1a4a15dacdee5ed33787374bcb35921b22c507796c1046466` |
| `runs/model-player/t140-scripted-w90-r2/lunarlander/scripted/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t140-scripted-w90-r2/lunarlander/scripted/engine-game.stdout.txt` | 766 | `12ae8323a9753ed702af07c6a4643afdb3e6b0fd531a1014635000df419450be` |
| `runs/model-player/t140-scripted-w90-r2/lunarlander/scripted/filmstrip.png` | 74547 | `7e121b223ce72fb916f5091c356afbea366c6eea0c8f759119832428f5c4d443` |
| `runs/model-player/t140-scripted-w90-r2/lunarlander/scripted/frames.json` | 455226 | `f02818aa942d52372f0f17a6e40078f46574ce5bea4e1cf2cac542c2f4d3482a` |
| `runs/model-player/t140-scripted-w90-r2/lunarlander/scripted/player.json` | 22482 | `cf08b2a0ba463d95a4f5abbd0c24626f05d381f5950f896cf6e1817042c7cce4` |
| `runs/model-player/t140-scripted-w90-r2/lunarlander/scripted/session.json` | 12122 | `34365511ebe01fb0575b46ca3517ecf302e81d62b94665adb792d42d5f0988a1` |
| `runs/model-player/t140-scripted-w90-r2/lunarlander/scripted/steps.jsonl` | 96500 | `8678580d90502d8c9597c4eaa29c1f590a03e2ed1744d8ab12ae80e4074da5bc` |
| `calls/**`（923 个文件，9733511 B）| — | `d5a9b97ecb41a05dac937c8942aba3242bf44bb244fce7f08cddcccc980875b3` |
| `frames/**`（25 个文件，323393 B）| — | `259166d41ca820a880679869bc0c1469cf22a53a06cab1c70cbee1496f3252b1` |
| `states/**`（19 个文件，227311 B）| — | `9a02e3e4b77dcb33d479392941205332f240d508c241ebb5a51fa163a9d5a670` |

## t140-scripted-w90-r2 / match3 / scripted

* 目录：`runs/model-player/t140-scripted-w90-r2/match3/scripted`
* verdict：`PASS`（counts_as_pass=True，strict=PASS，baseline=PASS，game_side=PASS）
* 档位+轮次：`PASS @w90 r2`（window=90，round=2，reporting=90，at_reporting_window=True，reporting_state=ok）
* 注入/接受后变化/rate：12 / 8 / 1.0
* 两窗对齐：8/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 2 frame(s))（matched 8/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game match3 --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9982 --window-frames 90 --round 2 --change-margin strict --out-prefix t140-scripted-w90-r2`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t140-scripted-w90-r2/match3/scripted/demo.png` | 194195 | `318ac279eb46746d7107c1178ff9a85a203d43b5a654ecec8b6bcee8124a5333` |
| `runs/model-player/t140-scripted-w90-r2/match3/scripted/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t140-scripted-w90-r2/match3/scripted/engine-game.stdout.txt` | 769 | `8b1436369002bf8d33305c0fe3cfc6498b3e3ad1f79b7315dac2998aaee085c1` |
| `runs/model-player/t140-scripted-w90-r2/match3/scripted/filmstrip.png` | 154043 | `38bdbcea42c10e16e0b234c96e405ce2a007215f051c5739c5be1e6ca1503b78` |
| `runs/model-player/t140-scripted-w90-r2/match3/scripted/frames.json` | 611783 | `58127ee907898a5cec2aa7cba46b26f4c0e68b129d70d418d5a69cbfe5b56fff` |
| `runs/model-player/t140-scripted-w90-r2/match3/scripted/player.json` | 28883 | `f4a1888b459b21ebe20807e39364a29f7d4bfeaa56c864d93c7626d924be7ee0` |
| `runs/model-player/t140-scripted-w90-r2/match3/scripted/session.json` | 13898 | `1f15450744a9271d1d39ddc58f6f5886cbf141be4e2504842f904226d52540e4` |
| `runs/model-player/t140-scripted-w90-r2/match3/scripted/steps.jsonl` | 141697 | `be689b619ca740e6b8d6c7ff1679ed1881e61b1fbf4c40825a57b377c9ff1df7` |
| `calls/**`（1384 个文件，14832339 B）| — | `afc48a475225a8a46a23cfdc4202500d79a8a9ffa21236d8bf168b30579b814e` |
| `frames/**`（37 个文件，431921 B）| — | `0e3674e9c50e97f3a95ee87763f05c0a40b22fa92b48ed1ecefba3eea3d528c0` |
| `states/**`（27 个文件，330696 B）| — | `7226f4b86d1b957e44af7d5687d87e345cc8842d7e886e4cb29ef3120fbdb5fa` |

## t140-scripted-w90-r2 / minesweeper / scripted

* 目录：`runs/model-player/t140-scripted-w90-r2/minesweeper/scripted`
* verdict：`PASS`（counts_as_pass=True，strict=PASS，baseline=PASS，game_side=PASS）
* 档位+轮次：`PASS @w90 r2`（window=90，round=2，reporting=90，at_reporting_window=True，reporting_state=ok）
* 注入/接受后变化/rate：12 / 7 / 1.0
* 两窗对齐：6/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 2 frame(s))（matched 6/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game minesweeper --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9982 --window-frames 90 --round 2 --change-margin strict --out-prefix t140-scripted-w90-r2`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t140-scripted-w90-r2/minesweeper/scripted/demo.png` | 186291 | `827275f29072d6cee0af785ad55fdb6212ce6781742933299dc06f5671d34c4a` |
| `runs/model-player/t140-scripted-w90-r2/minesweeper/scripted/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t140-scripted-w90-r2/minesweeper/scripted/engine-game.stdout.txt` | 745 | `8f74add7132303dfbb5dbe499b27a0c4d1c9043fe7624e715b759ebc7c7ad09b` |
| `runs/model-player/t140-scripted-w90-r2/minesweeper/scripted/filmstrip.png` | 182715 | `bb903653f3b27411a1d883980a94fcd0d53d7bb980bbac97557e61e6858d0426` |
| `runs/model-player/t140-scripted-w90-r2/minesweeper/scripted/frames.json` | 810414 | `ab8368aef77012aee22c17ad7afd0cf72feb54b82615571161f5aba4626a1d42` |
| `runs/model-player/t140-scripted-w90-r2/minesweeper/scripted/player.json` | 29953 | `a459066ef3a0700f9270dfb6a48dd906b08e123fc8e90baca2ceba8666402ae1` |
| `runs/model-player/t140-scripted-w90-r2/minesweeper/scripted/session.json` | 14034 | `a453bc1b1fdee9cb67e40e58762bc290e28d4cd4c25a5f0cfa462da4530ea6a8` |
| `runs/model-player/t140-scripted-w90-r2/minesweeper/scripted/steps.jsonl` | 140940 | `71a5cd4fecf9593da578254d5db894fc19b9879b5a9c6e8829742adb6dfe41fc` |
| `calls/**`（1316 个文件，32870404 B）| — | `b7f7edbd0aae2bd8076a7bb6c1e0420d3e4d730d131bd7abe309908eecdb6536` |
| `frames/**`（37 个文件，580787 B）| — | `7c817a64251d1b1c88ea3a6c1eef264c67bb09617a8b31333f5fcc33ea409c22` |
| `states/**`（27 个文件，787283 B）| — | `fe87339d1d0a4b1588eab4ed96ffad39df51f47684e3768607c871d459a97b0c` |

## t140-scripted-w90-r2 / missilecommand / scripted

* 目录：`runs/model-player/t140-scripted-w90-r2/missilecommand/scripted`
* verdict：`PASS`（counts_as_pass=True，strict=PASS，baseline=PASS，game_side=PASS）
* 档位+轮次：`PASS @w90 r2`（window=90，round=2，reporting=90，at_reporting_window=True，reporting_state=ok）
* 注入/接受后变化/rate：8 / 8 / 1.0
* 两窗对齐：7/8 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 1 frame(s))（matched 7/8，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game missilecommand --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9982 --window-frames 90 --round 2 --change-margin strict --out-prefix t140-scripted-w90-r2`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t140-scripted-w90-r2/missilecommand/scripted/demo.png` | 108824 | `77337a51aa2d60b768712839dfc3de9b3f8102b9fec3809a0d13f54579e4e82e` |
| `runs/model-player/t140-scripted-w90-r2/missilecommand/scripted/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t140-scripted-w90-r2/missilecommand/scripted/engine-game.stdout.txt` | 742 | `eb6998d7215078c305bc48203e7fb1aaa8b3c1d24eae1d947d55fbc92ebc3491` |
| `runs/model-player/t140-scripted-w90-r2/missilecommand/scripted/filmstrip.png` | 56306 | `5fff3de1a77b7398fc08197f66db8df38f0784c122767d5c12a0c051351e5332` |
| `runs/model-player/t140-scripted-w90-r2/missilecommand/scripted/frames.json` | 497605 | `9be5d1ea99680088112a1d88bf5fb3f72ad9dd6a5c0adf92109a38ea0cb1e776` |
| `runs/model-player/t140-scripted-w90-r2/missilecommand/scripted/player.json` | 22507 | `7f19609564d5270fa049f66d327496b84bd2306661fcc1a749760c7466200285` |
| `runs/model-player/t140-scripted-w90-r2/missilecommand/scripted/session.json` | 12422 | `49062e4a76e39c6b6dad21c43764fcea9fc6f7d5e4ecd5396d00e1e000db13b7` |
| `runs/model-player/t140-scripted-w90-r2/missilecommand/scripted/steps.jsonl` | 98132 | `268500087014658aeff872824e1792230a129070066a0ea2fda935c7705f37dc` |
| `calls/**`（897 个文件，17692247 B）| — | `e2aab9548c6c8f95e6e34982c538cc611ec52245d15338c0d9537c28dc105b64` |
| `frames/**`（25 个文件，354928 B）| — | `0a50a301ef681281c59fc931a2cfd97ca1d10917d82a75b5749f51a91f7d56e4` |
| `states/**`（19 个文件，441909 B）| — | `78b001263d2e08dc007354040cbcc8389e23de8936c5cf431bb54e4eaf9d0a35` |

## t140-scripted-w90-r2 / pacman / scripted

* 目录：`runs/model-player/t140-scripted-w90-r2/pacman/scripted`
* verdict：`PASS`（counts_as_pass=True，strict=PASS，baseline=PASS，game_side=PASS）
* 档位+轮次：`PASS @w90 r2`（window=90，round=2，reporting=90，at_reporting_window=True，reporting_state=ok）
* 注入/接受后变化/rate：12 / 7 / 1.0
* 两窗对齐：9/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 2 frame(s))（matched 9/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game pacman --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9982 --window-frames 90 --round 2 --change-margin strict --out-prefix t140-scripted-w90-r2`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t140-scripted-w90-r2/pacman/scripted/demo.png` | 146478 | `b2ac36203d74153f2e14cfa946cbeb6e9f4a63bd0761e54e53fcb22702c19a8d` |
| `runs/model-player/t140-scripted-w90-r2/pacman/scripted/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t140-scripted-w90-r2/pacman/scripted/engine-game.stdout.txt` | 733 | `7ab29be64414882e0931d60dc62b7fdca1003ef4aee875d93485d748789413ee` |
| `runs/model-player/t140-scripted-w90-r2/pacman/scripted/filmstrip.png` | 146874 | `889c8b55347b4e8ebb9a5c7d98015b64eac09b169105d5192898e49cda287669` |
| `runs/model-player/t140-scripted-w90-r2/pacman/scripted/frames.json` | 583967 | `c3db6c8472d261e2f159940b3bb1d59d660652d477350c614b03a654fe94cd32` |
| `runs/model-player/t140-scripted-w90-r2/pacman/scripted/player.json` | 29261 | `680f4789986ef467e96de622508911254bc4ed014f27cc7e8e22f81ffc8f4613` |
| `runs/model-player/t140-scripted-w90-r2/pacman/scripted/session.json` | 13468 | `c58cc21c67b5036f5686565f8b4301867a2a2b3343f5f3588c4f829d546aa726` |
| `runs/model-player/t140-scripted-w90-r2/pacman/scripted/steps.jsonl` | 143607 | `963c965e6eb5039432b221c1f1cc843594327d79fd144da7ba830665b91088d3` |
| `calls/**`（1277 个文件，44851218 B）| — | `1d6c2590685e9cbe16f3e70077fa4e58ef55a679b6ab23b1e5110e805fa3f196` |
| `frames/**`（37 个文件，411185 B）| — | `1c83aaef48e90a2349db2d6eb99a8ddf9eb103f14566374c5e431122ae3192af` |
| `states/**`（27 个文件，1153931 B）| — | `ca5e16a4edaec239ec8cbccad444234d9e85f094c69db9a9aa61dd1878461ee7` |

## t140-scripted-w90-r2 / platformer / scripted

* 目录：`runs/model-player/t140-scripted-w90-r2/platformer/scripted`
* verdict：`INCONCLUSIVE`（counts_as_pass=False，strict=INCONCLUSIVE，baseline=INCONCLUSIVE，game_side=FAIL）
* 档位+轮次：`INCONCLUSIVE @w90 r2`（window=90，round=2，reporting=90，at_reporting_window=True，reporting_state=ok）
* 注入/接受后变化/rate：6 / 3 / 0.5
* 两窗对齐：3/6 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 2 frame(s))（matched 3/6，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game platformer --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9982 --window-frames 90 --round 2 --change-margin strict --out-prefix t140-scripted-w90-r2`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t140-scripted-w90-r2/platformer/scripted/demo.png` | 82213 | `c917350a893572dff4989e51e7b8f317049c2f6a07e4aace932a06ce8f3bcde1` |
| `runs/model-player/t140-scripted-w90-r2/platformer/scripted/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t140-scripted-w90-r2/platformer/scripted/engine-game.stdout.txt` | 796 | `b4ee5e0514daa6e7457777a59308ed8c7b8280a6f68f35c88dca30bfa204a12e` |
| `runs/model-player/t140-scripted-w90-r2/platformer/scripted/filmstrip.png` | 51794 | `e4223495ed3708b9a1eeb1074adee045a2cdc480b89437d385c729f0759f7708` |
| `runs/model-player/t140-scripted-w90-r2/platformer/scripted/frames.json` | 282887 | `b269b8a8d8a3d0d09a5a555e686f7054871635d8baec7b37ed2b7b5f5b52d4fa` |
| `runs/model-player/t140-scripted-w90-r2/platformer/scripted/player.json` | 24278 | `82698ad84a94dc09d726b81f69ba687b290129089121a0cefd25f23922a6627a` |
| `runs/model-player/t140-scripted-w90-r2/platformer/scripted/session.json` | 12157 | `50a6a59f4c71a5f4b26f78983ad13ead6ebed1737989937f3671f1b2b0f5202b` |
| `runs/model-player/t140-scripted-w90-r2/platformer/scripted/steps.jsonl` | 78910 | `4d4ce9d597171208ff3b413306659e83f80079bcdf363e4d31c3f7730521174f` |
| `calls/**`（689 个文件，12622463 B）| — | `bdd58fdc9f873da435abd1bbf3d99172718d5e3d0c3ce227c8d3a5da0e811b14` |
| `frames/**`（19 个文件，198370 B）| — | `dacd9ca887a72195b6496b0033c6c78bffa98780c7941b83fb958542a3f7e76e` |
| `states/**`（15 个文件，322471 B）| — | `fb2f45b0a88c61b76b6fd9cd5def86c62ea913f0f32c0d81ae5320f83a83e930` |

## t140-scripted-w90-r2 / pong / scripted

* 目录：`runs/model-player/t140-scripted-w90-r2/pong/scripted`
* verdict：`PASS`（counts_as_pass=True，strict=PASS，baseline=PASS，game_side=PASS）
* 档位+轮次：`PASS @w90 r2`（window=90，round=2，reporting=90，at_reporting_window=True，reporting_state=ok）
* 注入/接受后变化/rate：8 / 8 / 1.0
* 两窗对齐：3/8 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 2 frame(s))（matched 3/8，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game pong --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9982 --window-frames 90 --round 2 --change-margin strict --out-prefix t140-scripted-w90-r2`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t140-scripted-w90-r2/pong/scripted/demo.png` | 55294 | `72dad525de9aec25963b3aecbc61785a40ffe7f952ea20e04ecd67aebac9d99f` |
| `runs/model-player/t140-scripted-w90-r2/pong/scripted/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t140-scripted-w90-r2/pong/scripted/engine-game.stdout.txt` | 4208 | `69248a67d50097418f23633631a7a581940be9f0aeb212f70edd05d07f39ddd4` |
| `runs/model-player/t140-scripted-w90-r2/pong/scripted/filmstrip.png` | 35601 | `21f0231b65da613c4351bebdc72638ff2e63cc1fe047a211faa27c6a94f9886a` |
| `runs/model-player/t140-scripted-w90-r2/pong/scripted/frames.json` | 221160 | `ca4e6320c38dfda2f005dce4fcc5dc948745dda2a9c20d762e360db0d80a2568` |
| `runs/model-player/t140-scripted-w90-r2/pong/scripted/player.json` | 22350 | `aa6f6414c8283ce952ec052576860bf77cfe426a0018781f6d6ade315a5de9f1` |
| `runs/model-player/t140-scripted-w90-r2/pong/scripted/session.json` | 12324 | `b8df70457dd6ca508fafa4d7523237981568e99cd6c599d9c39a90ad9e22271d` |
| `runs/model-player/t140-scripted-w90-r2/pong/scripted/steps.jsonl` | 91130 | `c2bd20094cb0a6a1693267d6eebefaef17bf521a6d56c2ff09cd0db8d0fad8ab` |
| `calls/**`（900 个文件，2332911 B）| — | `b6f66c9fb04ed7628c2ec5c8cad5fe918bf56b0f0fa93563efe979e8313e9e3c` |
| `frames/**`（25 个文件，147893 B）| — | `88cfdb647847b1643365ed01f45d2290d89eeeb1b433c79f04453455bc08e77d` |
| `states/**`（19 个文件，46532 B）| — | `fac6f6516ce5a77e1c000d413204998191dec375f050e1ce0f695b7e0f5a50d9` |

## t140-scripted-w90-r2 / puzzlebobble / scripted

* 目录：`runs/model-player/t140-scripted-w90-r2/puzzlebobble/scripted`
* verdict：`PASS`（counts_as_pass=True，strict=PASS，baseline=PASS，game_side=PASS）
* 档位+轮次：`PASS @w90 r2`（window=90，round=2，reporting=90，at_reporting_window=True，reporting_state=ok）
* 注入/接受后变化/rate：8 / 8 / 1.0
* 两窗对齐：2/8 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 2 frame(s))（matched 2/8，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game puzzlebobble --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9982 --window-frames 90 --round 2 --change-margin strict --out-prefix t140-scripted-w90-r2`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t140-scripted-w90-r2/puzzlebobble/scripted/demo.png` | 138756 | `2b46e1d279c7c33b6518fc23d4a65eb9f24444694314ec4f292ca2cd31383f3e` |
| `runs/model-player/t140-scripted-w90-r2/puzzlebobble/scripted/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t140-scripted-w90-r2/puzzlebobble/scripted/engine-game.stdout.txt` | 739 | `213d7d1d78b0f7491124c3e15ec21ca16b440ccefba4af7800c07bb998803fc7` |
| `runs/model-player/t140-scripted-w90-r2/puzzlebobble/scripted/filmstrip.png` | 83632 | `87d297d66adb426d0bc397b4e07c73ddaf11f871f4d185be485901f7ea1b4266` |
| `runs/model-player/t140-scripted-w90-r2/puzzlebobble/scripted/frames.json` | 482040 | `ac3ecbf9987206ad22eff42eaad80810ba06b045a0e7f6517bb51bb06ff99035` |
| `runs/model-player/t140-scripted-w90-r2/puzzlebobble/scripted/player.json` | 22476 | `89da0165ffa358613a8996c00512c2ebebfa722ee89fbcb68d2551155c807c9f` |
| `runs/model-player/t140-scripted-w90-r2/puzzlebobble/scripted/session.json` | 12306 | `5517a54a1c4c5ba721b107fa17175d66f37c4a02c65963a60fa54b29380c5429` |
| `runs/model-player/t140-scripted-w90-r2/puzzlebobble/scripted/steps.jsonl` | 98233 | `d2b6a2a5d47ab59d4eb16c8e80966e0e926cf1e6ae15d4d278fdef744c079bbd` |
| `calls/**`（876 个文件，14933697 B）| — | `be551ab5b2aeae0fe00e7512a6b8f44e97b9964bd7b5c15c28e0453c915f928d` |
| `frames/**`（25 个文件，343266 B）| — | `31253163b2680027b572ba2b5eaeb17a658cf00ee22023d85a25e92ecd1593e9` |
| `states/**`（19 个文件，379475 B）| — | `a13772dd1c1dbe3260ef940fc54bf049e6d44e0633628f1c36f18857db92985b` |

## t140-scripted-w90-r2 / rtype / scripted

* 目录：`runs/model-player/t140-scripted-w90-r2/rtype/scripted`
* verdict：`PASS`（counts_as_pass=True，strict=PASS，baseline=PASS，game_side=PASS）
* 档位+轮次：`PASS @w90 r2`（window=90，round=2，reporting=90，at_reporting_window=True，reporting_state=ok）
* 注入/接受后变化/rate：8 / 8 / 1.0
* 两窗对齐：2/8 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 2 frame(s))（matched 2/8，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game rtype --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9982 --window-frames 90 --round 2 --change-margin strict --out-prefix t140-scripted-w90-r2`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t140-scripted-w90-r2/rtype/scripted/demo.png` | 120976 | `a8c2b56a91d0e7bca428bb2ad2fe6152882501bbd370f80d661b298e61e1bea0` |
| `runs/model-player/t140-scripted-w90-r2/rtype/scripted/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t140-scripted-w90-r2/rtype/scripted/engine-game.stdout.txt` | 743 | `a44e6dc452df9a5773cfa254c95e7bb55d4c887f49e8c149bb522229f522ba26` |
| `runs/model-player/t140-scripted-w90-r2/rtype/scripted/filmstrip.png` | 69706 | `8bed55161da5b1567961cca5c69b5b2b5c7f2e6c34e38aa08cadebdaf468b967` |
| `runs/model-player/t140-scripted-w90-r2/rtype/scripted/frames.json` | 430187 | `beb0e4ab04b7b874a7065666fc8776ecae5620e07b0f4aca402ae43f29c71751` |
| `runs/model-player/t140-scripted-w90-r2/rtype/scripted/player.json` | 22465 | `6274de42a55d4c327e7dcfc017e84e735c96ad06366350540f2785075c071619` |
| `runs/model-player/t140-scripted-w90-r2/rtype/scripted/session.json` | 12253 | `7ddfe0f8e61fd602dc30b2b273c52c9dc9b7b8d246b96664cfa1f7f0ef336e04` |
| `runs/model-player/t140-scripted-w90-r2/rtype/scripted/steps.jsonl` | 97577 | `7705848b1577f74bb688a4c146e5e21076222bb683cec83aa34d168dac3ab70b` |
| `calls/**`（909 个文件，14374877 B）| — | `fc31e2df0c352e772293136e30b882dc4d9c172fa9ff0f240745f2b0621aa6bc` |
| `frames/**`（25 个文件，304633 B）| — | `a489304c36f8f74a13820b9cdcd568db44e7d18a9d7f13f196e92b88dbb6eafc` |
| `states/**`（19 个文件，351816 B）| — | `bd236d84d1f24fb6f42da2d85d4ec279ed1d42314ddcc7392b36909fe96a2b2a` |

## t140-scripted-w90-r2 / snake / scripted

* 目录：`runs/model-player/t140-scripted-w90-r2/snake/scripted`
* verdict：`PASS`（counts_as_pass=True，strict=PASS，baseline=PASS，game_side=PASS）
* 档位+轮次：`PASS @w90 r2`（window=90，round=2，reporting=90，at_reporting_window=True，reporting_state=ok）
* 注入/接受后变化/rate：8 / 8 / 1.0
* 两窗对齐：4/8 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 2 frame(s))（matched 4/8，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game snake --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9982 --window-frames 90 --round 2 --change-margin strict --out-prefix t140-scripted-w90-r2`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t140-scripted-w90-r2/snake/scripted/demo.png` | 44861 | `cb6823c8f55ad13e09fbad6d197cde71faeaac15cd71a7145f30b32357eaa2de` |
| `runs/model-player/t140-scripted-w90-r2/snake/scripted/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t140-scripted-w90-r2/snake/scripted/engine-game.stdout.txt` | 9537 | `8aec08ea4464d8d963f4887a2139e4394ec4e5ba1ecf5ac2c0796c4f1f921b27` |
| `runs/model-player/t140-scripted-w90-r2/snake/scripted/filmstrip.png` | 30677 | `e245517504b4d55f6b299e777eb0f7ccad10266b072985bc18d2c3c8727d0e91` |
| `runs/model-player/t140-scripted-w90-r2/snake/scripted/frames.json` | 127068 | `456da167b9315c077bc45f5b0e51ac973d1ab05d17e655f96bc6ebca4e50ee50` |
| `runs/model-player/t140-scripted-w90-r2/snake/scripted/player.json` | 22466 | `c96e084d2bfa53103e1e00b338d2fae730a5fcb357c4772dd90d3bcf6f5ae2d5` |
| `runs/model-player/t140-scripted-w90-r2/snake/scripted/session.json` | 12884 | `e1441f5cb3881672265208881cd4b212768019c14ef38129491f839b15b2b0ac` |
| `runs/model-player/t140-scripted-w90-r2/snake/scripted/steps.jsonl` | 103421 | `0eb14d69ecdd9c2265a7be7587a2bb1b8c8a104b32d7a778f63217182da92d51` |
| `calls/**`（665 个文件，5087965 B）| — | `aa30e1f542dfb47478433f7ed0aa28d60bf245bdd0467b086fdcc93246042213` |
| `frames/**`（25 个文件，77413 B）| — | `d06745f122016f641c6420a2d376a4dc5c2e005d9f82ca3a6908b142fa2302ef` |
| `states/**`（19 个文件，166637 B）| — | `3a308a011fa39fca8ea6802bdb5e5ff35893c11a6881ad9d66783f89c18c192b` |

## t140-scripted-w90-r2 / sokoban / scripted

* 目录：`runs/model-player/t140-scripted-w90-r2/sokoban/scripted`
* verdict：`PASS`（counts_as_pass=True，strict=PASS，baseline=PASS，game_side=PASS）
* 档位+轮次：`PASS @w90 r2`（window=90，round=2，reporting=90，at_reporting_window=True，reporting_state=ok）
* 注入/接受后变化/rate：12 / 9 / 1.0
* 两窗对齐：6/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 23 frame(s))（matched 6/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game sokoban --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9982 --window-frames 90 --round 2 --change-margin strict --out-prefix t140-scripted-w90-r2`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t140-scripted-w90-r2/sokoban/scripted/demo.png` | 139576 | `8d59192b1c13f355664beec196550cdff3fa531986c1e8ad5af3be4e764560b1` |
| `runs/model-player/t140-scripted-w90-r2/sokoban/scripted/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t140-scripted-w90-r2/sokoban/scripted/engine-game.stdout.txt` | 745 | `659656b70b4eac1b433a87234e3034873f6f121a8d5baadee4ea2538a12c98fd` |
| `runs/model-player/t140-scripted-w90-r2/sokoban/scripted/filmstrip.png` | 107313 | `22f71c379de06c60d2abaefe078356f5413c6b07608869326e69fd633b7ae453` |
| `runs/model-player/t140-scripted-w90-r2/sokoban/scripted/frames.json` | 647055 | `e4123285975211ae228bd67c2e28007e55b9859a094e74968ee8307538d0504f` |
| `runs/model-player/t140-scripted-w90-r2/sokoban/scripted/player.json` | 27805 | `ef42ea8c5ae93d7b86a034298a2266d1b97d8aa9b55f5f1e3f3585d8daca54ac` |
| `runs/model-player/t140-scripted-w90-r2/sokoban/scripted/session.json` | 13614 | `04912a9cba1307bdcefdf324def9ff13720046c46ba5e7fca7e4f0ee224c582e` |
| `runs/model-player/t140-scripted-w90-r2/sokoban/scripted/steps.jsonl` | 147961 | `93c054db3a487922b4129e51f12a8b08fce40d58f05cfe2927d7060a6c17989c` |
| `calls/**`（1353 个文件，16649656 B）| — | `e8aba8841547f584e681088057f4ebf530e97efcb36bebccf64046a2438671bb` |
| `frames/**`（37 个文件，458340 B）| — | `68425fbcb1cd6e3046cc947e38a43647fe918857838d7a37f767e7eb57373004` |
| `states/**`（27 个文件，374451 B）| — | `7a8a1cae2d3d17bcfc29046c3b612d88becf17d3e7e18bff41f718af2c28fecd` |

## t140-scripted-w90-r2 / spaceinvaders / scripted

* 目录：`runs/model-player/t140-scripted-w90-r2/spaceinvaders/scripted`
* verdict：`PASS`（counts_as_pass=True，strict=PASS，baseline=PASS，game_side=PASS）
* 档位+轮次：`PASS @w90 r2`（window=90，round=2，reporting=90，at_reporting_window=True，reporting_state=ok）
* 注入/接受后变化/rate：8 / 8 / 1.0
* 两窗对齐：6/8 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 1 frame(s))（matched 6/8，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game spaceinvaders --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9982 --window-frames 90 --round 2 --change-margin strict --out-prefix t140-scripted-w90-r2`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t140-scripted-w90-r2/spaceinvaders/scripted/demo.png` | 86197 | `fc8ee9a08307ddcb3af29296a43d8f4c8799690bbd9cdcbd4cb9ada8cbdc5c7f` |
| `runs/model-player/t140-scripted-w90-r2/spaceinvaders/scripted/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t140-scripted-w90-r2/spaceinvaders/scripted/engine-game.stdout.txt` | 754 | `009d23c0807600542f6d74dc40790ca249c34217580d72406be80f22db3c58a5` |
| `runs/model-player/t140-scripted-w90-r2/spaceinvaders/scripted/filmstrip.png` | 60806 | `3e868b15da00d242b729b3e33f1b957aa0716c1065c34f9da0db95ac021b7c12` |
| `runs/model-player/t140-scripted-w90-r2/spaceinvaders/scripted/frames.json` | 349614 | `76a06b6353c71a113c9a92fd59490f04d678d93ec9cde7a760197de6473ac512` |
| `runs/model-player/t140-scripted-w90-r2/spaceinvaders/scripted/player.json` | 22487 | `4cd2c1cc83ebd05dd993929682f8b8e2c721b0b7f73952c3d5f75ee93bab9d21` |
| `runs/model-player/t140-scripted-w90-r2/spaceinvaders/scripted/session.json` | 12219 | `41eb9144b5988a631989de67f498cfc3cb8ea92ecbd839f68f174ea467c24db6` |
| `runs/model-player/t140-scripted-w90-r2/spaceinvaders/scripted/steps.jsonl` | 98928 | `972e111a82c74eef3534b486a8ffa3e4a0180561a2edcd53c76fedad5b803292` |
| `calls/**`（940 个文件，7524138 B）| — | `ea8f54904c4b2568f6c6c01d9f22bf45728bbdd0cef8301c9c6d56fecbb71dbb` |
| `frames/**`（25 个文件，243918 B）| — | `845521ae93b46c7083fc471ea1b93649f6a0230c1063e5cf2b5c9022bf9b3d90` |
| `states/**`（19 个文件，169672 B）| — | `d75e427e1c9419662120e1c0ace87844d8704a98b680140236b36b08fbd12de1` |

## t140-scripted-w90-r2 / tetris / scripted

* 目录：`runs/model-player/t140-scripted-w90-r2/tetris/scripted`
* verdict：`PASS`（counts_as_pass=True，strict=PASS，baseline=PASS，game_side=PASS）
* 档位+轮次：`PASS @w90 r2`（window=90，round=2，reporting=90，at_reporting_window=True，reporting_state=ok）
* 注入/接受后变化/rate：8 / 8 / 1.0
* 两窗对齐：4/8 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 2 frame(s))（matched 4/8，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game tetris --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9982 --window-frames 90 --round 2 --change-margin strict --out-prefix t140-scripted-w90-r2`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t140-scripted-w90-r2/tetris/scripted/demo.png` | 51366 | `d63646b22803d99e27d3e4c201ef7e0ecec39c44656e64e3afeeb73f502c79f5` |
| `runs/model-player/t140-scripted-w90-r2/tetris/scripted/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t140-scripted-w90-r2/tetris/scripted/engine-game.stdout.txt` | 8950 | `57837c108c122d9886f178c66b1fcff84419f0199865a9a86e8577205098c42a` |
| `runs/model-player/t140-scripted-w90-r2/tetris/scripted/filmstrip.png` | 34096 | `cd85452d53a798b699c464c46417fdb682402fee602c4cac11ccb69e3654cb38` |
| `runs/model-player/t140-scripted-w90-r2/tetris/scripted/frames.json` | 196100 | `eb8f982e8c43584914ee2719d5714b9937256769cf8fed67339cd821c5295295` |
| `runs/model-player/t140-scripted-w90-r2/tetris/scripted/player.json` | 22556 | `6b077bbf0b7647c0b870186b688aca04f323c8c3259d1aa5d6232ae1926d7064` |
| `runs/model-player/t140-scripted-w90-r2/tetris/scripted/session.json` | 12108 | `f6b8f6659fc4984bb3d3e5dc23325b4f18e0a78df06ac6553d182eff6d564cb2` |
| `runs/model-player/t140-scripted-w90-r2/tetris/scripted/steps.jsonl` | 86986 | `b6b48772dc84779f32e4bf42dc9b4cb6a3feb8bfd1865dd569669c2bff257f0f` |
| `calls/**`（950 个文件，1717661 B）| — | `f582382ad8f13a2d5d7b7de38c993db358796bb105829e6b8447e7a719b88f3d` |
| `frames/**`（25 个文件，128882 B）| — | `e5dc1fd576640852d56771d6ebd903f7c01d011d586da98a37be70cf80ea19ec` |
| `states/**`（19 个文件，29824 B）| — | `e2e208e1fb1ada30777c2e12c9bae4238e345e9e2d10117e581f46084e8d2c63` |

## t140-scripted-w90-r2 / towerdefense / scripted

* 目录：`runs/model-player/t140-scripted-w90-r2/towerdefense/scripted`
* verdict：`PASS`（counts_as_pass=True，strict=PASS，baseline=PASS，game_side=PASS）
* 档位+轮次：`PASS @w90 r2`（window=90，round=2，reporting=90，at_reporting_window=True，reporting_state=ok）
* 注入/接受后变化/rate：12 / 9 / 1.0
* 两窗对齐：7/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 1 frame(s))（matched 7/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game towerdefense --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9982 --window-frames 90 --round 2 --change-margin strict --out-prefix t140-scripted-w90-r2`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t140-scripted-w90-r2/towerdefense/scripted/demo.png` | 163764 | `94d0b6b64960faf6c9336da8ae6d2c271c123a94fc21c6ce9f1f69c6b563a3af` |
| `runs/model-player/t140-scripted-w90-r2/towerdefense/scripted/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t140-scripted-w90-r2/towerdefense/scripted/engine-game.stdout.txt` | 753 | `0bc52b43148b98ea185f3648f41ff086ab28cd18b33af21d6489c0e70ee56351` |
| `runs/model-player/t140-scripted-w90-r2/towerdefense/scripted/filmstrip.png` | 131272 | `a99807424101d51b52c9b7906e2bf78e57d52e95b8b0cc6de12da8a3c2f9e22b` |
| `runs/model-player/t140-scripted-w90-r2/towerdefense/scripted/frames.json` | 638116 | `55a711a7ee703d9da9508324910862b79a3cff823e61941b546781df95cf0737` |
| `runs/model-player/t140-scripted-w90-r2/towerdefense/scripted/player.json` | 27982 | `e39e17bb0630607fbfbf0ee98b5e160fff67df5599558f188e91ffcd9f4ad4c8` |
| `runs/model-player/t140-scripted-w90-r2/towerdefense/scripted/session.json` | 13863 | `bdb41c5b4a90bd55f1385fcfe9f12d6d791e0c4fe5c6585b572fd1ce7eb83510` |
| `runs/model-player/t140-scripted-w90-r2/towerdefense/scripted/steps.jsonl` | 138606 | `1f80ffd41c227d10182e7a35363b08ad696c45aa459b23bfad075ef5817ad5fb` |
| `calls/**`（1345 个文件，27220002 B）| — | `c83f33286d5104dd29b0b27f3191c9f4e91f20039f687e0c47011e96aca54b0e` |
| `frames/**`（37 个文件，451587 B）| — | `0197f0c2d5b7d79dd71b75281267460cfbfcaad1e247acca4c330b6f383d3b68` |
| `states/**`（27 个文件，648201 B）| — | `ea4271818f8741477ad64bdc7809116688bd14c86a7f89262df1b879dc58043e` |

## t140-jev-v3-w90-r1 / asteroids / jev

* 目录：`runs/model-player/t140-jev-v3-w90-r1/asteroids/jev`
* verdict：`PASS`（counts_as_pass=True，strict=PASS，baseline=PASS，game_side=None）
* 档位+轮次：`PASS @w90 r1`（window=90，round=1，reporting=90，at_reporting_window=True，reporting_state=ok）
* 注入/接受后变化/rate：8 / 8 / 1.0
* 两窗对齐：6/8 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 1 frame(s))（matched 6/8，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game asteroids --backend jev --player model --variant V3 --image-form full --steps 12 --port 9983 --window-frames 90 --round 1 --change-margin strict --out-prefix t140-jev-v3-w90-r1`  <- t136_commands.jsonl
  * `D:/Anaconda/python.exe runs/model-player/_scripts/t140_steps.py runs/model-player/t140-jev-v3-w90-r1/asteroids/jev/steps.jsonl`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t140-jev-v3-w90-r1/asteroids/jev/demo.png` | 98317 | `251647f81dce1971abc01915d96240eef7e330bb8c7ce3c1e298614bb6c5f204` |
| `runs/model-player/t140-jev-v3-w90-r1/asteroids/jev/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t140-jev-v3-w90-r1/asteroids/jev/engine-game.stdout.txt` | 741 | `f435dcc8dc28e48c3e9430c29c6a468f6ceac4f8daf241729d6cbe78a3764777` |
| `runs/model-player/t140-jev-v3-w90-r1/asteroids/jev/filmstrip.png` | 48872 | `c647b215cbafa6fdcd4bc189b30de975c7a6495620d77a69604180af2c7c0cc0` |
| `runs/model-player/t140-jev-v3-w90-r1/asteroids/jev/frames.json` | 370027 | `3bffb9c5711be6f9e8293531e49103a0858d13908b6dab768f012439706647c0` |
| `runs/model-player/t140-jev-v3-w90-r1/asteroids/jev/player.json` | 171675 | `1f2e58e8ad8e0a15c78548431a626acef544975527718b9871e4f95978f04327` |
| `runs/model-player/t140-jev-v3-w90-r1/asteroids/jev/session.json` | 12080 | `e971990e8b7f2877b256c4b050ade6ada5f5d229b93d6c685186a5cbbabd04f5` |
| `runs/model-player/t140-jev-v3-w90-r1/asteroids/jev/steps.jsonl` | 109356 | `615d8d20fc46b34ee1603fc6278963eb2d586a81319404ba4c3c2e57b4647dcd` |
| `calls/**`（943 个文件，3117476 B）| — | `a213feb6de1db453ca6864b017f0494f3b437f5f1fcb8d5d82d3175584f46bd5` |
| `frames/**`（25 个文件，259475 B）| — | `4b2d5704a31cf6ef273347b5c6d37d08d6632a1c86d9f2906c06d3bb713facc7` |
| `states/**`（19 个文件，58566 B）| — | `e2de6b4156037ba2ce68ff2f2770b6579e15b24d9e2820424ed3c51e227cb4aa` |

## t140-jev-v3-w90-r1 / bomberman / jev

* 目录：`runs/model-player/t140-jev-v3-w90-r1/bomberman/jev`
* verdict：`INCONCLUSIVE`（counts_as_pass=False，strict=INCONCLUSIVE，baseline=INCONCLUSIVE，game_side=None）
* 档位+轮次：`INCONCLUSIVE @w90 r1`（window=90，round=1，reporting=90，at_reporting_window=True，reporting_state=ok）
* 注入/接受后变化/rate：12 / 1 / 1.0
* 两窗对齐：7/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 2 frame(s))（matched 7/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game bomberman --backend jev --player model --variant V3 --image-form full --steps 12 --port 9983 --window-frames 90 --round 1 --change-margin strict --out-prefix t140-jev-v3-w90-r1`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t140-jev-v3-w90-r1/bomberman/jev/demo.png` | 165544 | `3b2bb0ffa65d5e923df056832da4ac3115f8d8ae0e50edda9f0b64f3c318fd6e` |
| `runs/model-player/t140-jev-v3-w90-r1/bomberman/jev/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t140-jev-v3-w90-r1/bomberman/jev/engine-game.stdout.txt` | 775 | `174b5ca9992024f749e0360410bae9885ec59ecaa6690cd63328c3d9e5e194af` |
| `runs/model-player/t140-jev-v3-w90-r1/bomberman/jev/filmstrip.png` | 142395 | `265a175470b72a7d914e3cf5182588cef2ff1ae9cf8e33b384669d3cbeb06324` |
| `runs/model-player/t140-jev-v3-w90-r1/bomberman/jev/frames.json` | 511150 | `9c21cecb1e3caddcb9fee0f429812816213b498df64664e2ec4e849defe46090` |
| `runs/model-player/t140-jev-v3-w90-r1/bomberman/jev/player.json` | 250448 | `188bc380c53943071d02af1ff01de4165bd1959b6cacf56571a8e5b03c69bd93` |
| `runs/model-player/t140-jev-v3-w90-r1/bomberman/jev/session.json` | 12950 | `6672d3ca50730cf6a377156109293268e6fe440553d1a47c588c227fa39ccc4e` |
| `runs/model-player/t140-jev-v3-w90-r1/bomberman/jev/steps.jsonl` | 157991 | `9b61e8c7a28e3891b67bc1d6dddf178ffb864b006b16a6603f3eccfbd652d171` |
| `calls/**`（1383 个文件，26080078 B）| — | `ae39a1c1748ac8af527c95d77f23f16285205e2e746ffe9bdd5f502c6ff963bc` |
| `frames/**`（37 个文件，356515 B）| — | `0c74ab7fc9db3643fbdcc823d98394082db9fa5971d39ef568cf93636ffd1d89` |
| `states/**`（27 个文件，603261 B）| — | `ef46f2968bdaf487fe0da405e44a8407f3b8596ffcbd0b24b162866408201329` |

## t140-jev-v3-w90-r1 / breakout / jev

* 目录：`runs/model-player/t140-jev-v3-w90-r1/breakout/jev`
* verdict：`FAIL`（counts_as_pass=False，strict=FAIL，baseline=FAIL，game_side=None）
* 档位+轮次：`FAIL @w90 r1`（window=90，round=1，reporting=90，at_reporting_window=True，reporting_state=ok）
* 注入/接受后变化/rate：12 / 8 / 0.6667
* 两窗对齐：7/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 2 frame(s))（matched 7/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game breakout --backend jev --player model --variant V3 --image-form full --steps 12 --port 9983 --window-frames 90 --round 1 --change-margin strict --out-prefix t140-jev-v3-w90-r1`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t140-jev-v3-w90-r1/breakout/jev/demo.png` | 96712 | `48385d6a4f41228c0a0ac428fd0f3445aef1f5d754f3f26b94d23b04d6c29230` |
| `runs/model-player/t140-jev-v3-w90-r1/breakout/jev/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t140-jev-v3-w90-r1/breakout/jev/engine-game.stdout.txt` | 44250 | `8cb23ed7edbbe97a25b332d4e3ceee470a5e178ed8d20500caa4fb35ba95f7c6` |
| `runs/model-player/t140-jev-v3-w90-r1/breakout/jev/filmstrip.png` | 65649 | `dd46f869ba65756cc819e07858101aa5a4d93cc82ddd23c685adec7ca30e4e46` |
| `runs/model-player/t140-jev-v3-w90-r1/breakout/jev/frames.json` | 341660 | `306766c95c1bdaa289b4a1b51d0d15ae0d13bbba8e1348e0cf8bfba59910de49` |
| `runs/model-player/t140-jev-v3-w90-r1/breakout/jev/player.json` | 179035 | `9ed79dddc282c599377bda6d9c8518cb75746f66bcf113aefb5c517990a7884d` |
| `runs/model-player/t140-jev-v3-w90-r1/breakout/jev/session.json` | 12243 | `02d1d400b8386d83554b8d1c0b8983d052907f5146217ac1770311d739009237` |
| `runs/model-player/t140-jev-v3-w90-r1/breakout/jev/steps.jsonl` | 157864 | `8b3d3ee1b452deff7225a7f8d3a5107d434faf76e32c3210d0f7b8ba244bf9c3` |
| `calls/**`（1028 个文件，5292217 B）| — | `88c6edbb2354640c313e573e3e20c4214f3fc3b5b0d8e572733626f9d64c13a5` |
| `frames/**`（37 个文件，229556 B）| — | `3b3c7864d8034fc2329856ab1f3477a398f620c528d1fd5c9c78f8b504d0bec3` |
| `states/**`（27 个文件，147341 B）| — | `9278d1b0c71021c45a3ead581d27376b352beb5ebb4c05871254e433e229f241` |

## t140-jev-v3-w90-r1 / flappy / jev

* 目录：`runs/model-player/t140-jev-v3-w90-r1/flappy/jev`
* verdict：`FAIL`（counts_as_pass=False，strict=FAIL，baseline=FAIL，game_side=None）
* 档位+轮次：`FAIL @w90 r1`（window=90，round=1，reporting=90，at_reporting_window=True，reporting_state=ok）
* 注入/接受后变化/rate：12 / 5 / 0.4167
* 两窗对齐：8/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 1 frame(s))（matched 8/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game flappy --backend jev --player model --variant V3 --image-form full --steps 12 --port 9983 --window-frames 90 --round 1 --change-margin strict --out-prefix t140-jev-v3-w90-r1`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t140-jev-v3-w90-r1/flappy/jev/demo.png` | 120449 | `e095584f41d3526a5f6c1a75c52165f936e95e399ecb51bb0e5f26579ba2350e` |
| `runs/model-player/t140-jev-v3-w90-r1/flappy/jev/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t140-jev-v3-w90-r1/flappy/jev/engine-game.stdout.txt` | 743 | `a6248defa35d14c491d8aba22b3121cd686d4870b10e988bec63e3a05cbb3464` |
| `runs/model-player/t140-jev-v3-w90-r1/flappy/jev/filmstrip.png` | 118895 | `609dea3e2491c518b937bc85513abf9c12a462850d454eaf9189deb34710406b` |
| `runs/model-player/t140-jev-v3-w90-r1/flappy/jev/frames.json` | 565314 | `1ecdd957e3f2dabead58dae975a7316ba99486a5614c94c2f39581b8a8b047bd` |
| `runs/model-player/t140-jev-v3-w90-r1/flappy/jev/player.json` | 251381 | `18c7a6b0fbf2046dfc9a331ed23c22462abf80868573b4859c5434a927b39515` |
| `runs/model-player/t140-jev-v3-w90-r1/flappy/jev/session.json` | 12036 | `4b4c7b621bc13900d064fb0f9ce7243d815a58bc43e62896725708f04354cf3f` |
| `runs/model-player/t140-jev-v3-w90-r1/flappy/jev/steps.jsonl` | 197629 | `334d53f2854381feda097af8817c3c95e6ed69bbb085019dbc52b34fafadec53` |
| `calls/**`（1383 个文件，4718337 B）| — | `37792d518f16c3b21f9e3cc74c03ac1ae07d5c9959909985f4588dd99acdc7e9` |
| `frames/**`（37 个文件，397599 B）| — | `02c6c84bdde2282f298e6128bd0e3919e839fe2ad7b5bfd88733b6e93d0df300` |
| `states/**`（27 个文件，87424 B）| — | `966026ce93bea9404205b0fcb0144a9531a1609faea22c8e2892be6a7b3e9ae6` |

## t140-jev-v3-w90-r1 / frogger / jev

* 目录：`runs/model-player/t140-jev-v3-w90-r1/frogger/jev`
* verdict：`INCONCLUSIVE`（counts_as_pass=False，strict=INCONCLUSIVE，baseline=INCONCLUSIVE，game_side=None）
* 档位+轮次：`INCONCLUSIVE @w90 r1`（window=90，round=1，reporting=90，at_reporting_window=True，reporting_state=ok）
* 注入/接受后变化/rate：12 / 6 / 1.0
* 两窗对齐：7/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 1 frame(s))（matched 7/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game frogger --backend jev --player model --variant V3 --image-form full --steps 12 --port 9983 --window-frames 90 --round 1 --change-margin strict --out-prefix t140-jev-v3-w90-r1`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t140-jev-v3-w90-r1/frogger/jev/demo.png` | 135672 | `8cebfc5131cdf4c76dff1079d79066c4b64b0919df871f37844dc1e511b6fda8` |
| `runs/model-player/t140-jev-v3-w90-r1/frogger/jev/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t140-jev-v3-w90-r1/frogger/jev/engine-game.stdout.txt` | 748 | `6df1a0acc8ad6d87d8ed78bbcfe5526bec982686159cab3de3e3c84d1d80cff8` |
| `runs/model-player/t140-jev-v3-w90-r1/frogger/jev/filmstrip.png` | 92818 | `92acdc1dc714ba6e05b6c14be7384d1439ac5850af2cfef9e5f5387a6d44d41c` |
| `runs/model-player/t140-jev-v3-w90-r1/frogger/jev/frames.json` | 594396 | `e43d0ccb166c5c1863a0b13cec116f3e0a848b1e4dce00fff6011cfcd0c193d0` |
| `runs/model-player/t140-jev-v3-w90-r1/frogger/jev/player.json` | 267839 | `87064b2356c1d48d825a9f143e836ac011d50625306d4ded39447af3252144ae` |
| `runs/model-player/t140-jev-v3-w90-r1/frogger/jev/session.json` | 11982 | `2bcf63ab30f2a157c6005b032aa160a86e68e5b11596206999f061af49089d15` |
| `runs/model-player/t140-jev-v3-w90-r1/frogger/jev/steps.jsonl` | 148706 | `64ccbed9c0bf0ea91e1df32410d377358aa90504f1c127f58fbb7161dc429d8c` |
| `calls/**`（1467 个文件，6458749 B）| — | `92f6f5baa0bd60c301558d2f15ff48bd1bc08cbd7eeb696857df130c30dd882f` |
| `frames/**`（37 个文件，419130 B）| — | `795f8fa6a4356bd0a1eddf3e43c6888344b1f9d753c17e1f0fef6298102f0c5b` |
| `states/**`（27 个文件，119928 B）| — | `371db6067c2ca0ed3311e1347899bd37e3414ee9e00dd54c89606b0ff5c856d5` |

## t140-jev-v3-w90-r1 / game2048 / jev

* 目录：`runs/model-player/t140-jev-v3-w90-r1/game2048/jev`
* verdict：`INCONCLUSIVE`（counts_as_pass=False，strict=INCONCLUSIVE，baseline=INCONCLUSIVE，game_side=None）
* 档位+轮次：`INCONCLUSIVE @w90 r1`（window=90，round=1，reporting=90，at_reporting_window=True，reporting_state=ok）
* 注入/接受后变化/rate：5 / 5 / 1.0
* 两窗对齐：8/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 2 frame(s))（matched 8/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game game2048 --backend jev --player model --variant V3 --image-form full --steps 12 --port 9983 --window-frames 90 --round 1 --change-margin strict --out-prefix t140-jev-v3-w90-r1`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t140-jev-v3-w90-r1/game2048/jev/demo.png` | 140690 | `2fc42369c712da6d13bc81e8d1a77405476301f6b9f07f12af303dbc947b7ee6` |
| `runs/model-player/t140-jev-v3-w90-r1/game2048/jev/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t140-jev-v3-w90-r1/game2048/jev/engine-game.stdout.txt` | 781 | `ee36fbde82ee2f3fe3e14f48c9d13d50f76bfb30a7d1b6e589bd28f5aaff9b3c` |
| `runs/model-player/t140-jev-v3-w90-r1/game2048/jev/filmstrip.png` | 90747 | `a4e0c5d897fd5986d8478cf4199e4cba421179f344177cab1fbaf98668581185` |
| `runs/model-player/t140-jev-v3-w90-r1/game2048/jev/frames.json` | 677587 | `a9b7b28f88c6ac1ce431eef428581e60e5aff024eeb82693055d83bf44fa42b6` |
| `runs/model-player/t140-jev-v3-w90-r1/game2048/jev/player.json` | 131275 | `d33d9dd81a826ce6e984926932cd503fc39cc6303c3db76b511fb151904f3f0d` |
| `runs/model-player/t140-jev-v3-w90-r1/game2048/jev/session.json` | 11938 | `56ff7d16a2aa624e6a7aeacad10d59a2ab04f34c717c5eed694d3e7b5138e00b` |
| `runs/model-player/t140-jev-v3-w90-r1/game2048/jev/steps.jsonl` | 144209 | `275b928a9b02a871df61ec80840bdc9fba20e6bf36d79d8fc6d9873a358c76b2` |
| `calls/**`（1368 个文件，9837642 B）| — | `f2b763456409cc1e70b8b49005920cf99a8f9f7a188130c1b2ea006f6a0bd7a9` |
| `frames/**`（37 个文件，481433 B）| — | `a66b8bd8620fbfa9bff5fa27e74f28f74b54858d503cdaeb47bd6c89d6c46772` |
| `states/**`（27 个文件，202809 B）| — | `6a48c26176c2716aa0f6163da150a1be7200297ddf91c5e0aaa54305baf340e2` |

## t140-jev-v3-w90-r1 / lunarlander / jev

* 目录：`runs/model-player/t140-jev-v3-w90-r1/lunarlander/jev`
* verdict：`INCONCLUSIVE`（counts_as_pass=False，strict=INCONCLUSIVE，baseline=INCONCLUSIVE，game_side=None）
* 档位+轮次：`INCONCLUSIVE @w90 r1`（window=90，round=1，reporting=90，at_reporting_window=True，reporting_state=ok）
* 注入/接受后变化/rate：0 / 0 / None
* 两窗对齐：6/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 1 frame(s))（matched 6/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game lunarlander --backend jev --player model --variant V3 --image-form full --steps 12 --port 9983 --window-frames 90 --round 1 --change-margin strict --out-prefix t140-jev-v3-w90-r1`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t140-jev-v3-w90-r1/lunarlander/jev/demo.png` | 136641 | `5ccf7b0b66c36063e534b967624081e59e05be1c06c9b330a931367f934933a4` |
| `runs/model-player/t140-jev-v3-w90-r1/lunarlander/jev/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t140-jev-v3-w90-r1/lunarlander/jev/engine-game.stdout.txt` | 766 | `f7d2e254c19ad4e86d3580b66c75f80a670e69690e9565e0224b4c3638a16366` |
| `runs/model-player/t140-jev-v3-w90-r1/lunarlander/jev/filmstrip.png` | 105271 | `9f71305a54be9384364f5172fff5367e8b8a7dcdc44ddde4a34f1af4e9a8e6e6` |
| `runs/model-player/t140-jev-v3-w90-r1/lunarlander/jev/frames.json` | 628656 | `13139ccdcc1a86529909a02e8adef8cc8ef9cbb0340dd2f59bfb3bec569b1c0f` |
| `runs/model-player/t140-jev-v3-w90-r1/lunarlander/jev/player.json` | 270249 | `3c7adcd64dc63e636d0d77f729f819e6e4b6298b966a53a59f9e7a230d5e1802` |
| `runs/model-player/t140-jev-v3-w90-r1/lunarlander/jev/session.json` | 12005 | `208252cc55a848c02fe5cc998e4bc1393d1fd1433a8fd76a8fb2c87ca2c56f0e` |
| `runs/model-player/t140-jev-v3-w90-r1/lunarlander/jev/steps.jsonl` | 124725 | `40f425aad44de410dadb4a405cfde6da6b993a99a4e4c46e262a90177e481546` |
| `calls/**`（1379 个文件，14944648 B）| — | `d2ffad7d188be51d4a0a92c5eeb0a9d6dcfc359826e108e03e69f42681378364` |
| `frames/**`（37 个文件，444999 B）| — | `577aea90d619ce575d5075155a6132e6fba2656570da96d7c8a602aba8c81998` |
| `states/**`（27 个文件，322134 B）| — | `3b13aa17ac3ab4e8bc396219bd4bdffe04af334f5419e7957c6f60733da92616` |

## t140-jev-v3-w90-r1 / match3 / jev

* 目录：`runs/model-player/t140-jev-v3-w90-r1/match3/jev`
* verdict：`INCONCLUSIVE`（counts_as_pass=False，strict=INCONCLUSIVE，baseline=INCONCLUSIVE，game_side=None）
* 档位+轮次：`INCONCLUSIVE @w90 r1`（window=90，round=1，reporting=90，at_reporting_window=True，reporting_state=ok）
* 注入/接受后变化/rate：12 / 1 / 1.0
* 两窗对齐：5/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 2 frame(s))（matched 5/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game match3 --backend jev --player model --variant V3 --image-form full --steps 12 --port 9983 --window-frames 90 --round 1 --change-margin strict --out-prefix t140-jev-v3-w90-r1`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t140-jev-v3-w90-r1/match3/jev/demo.png` | 207087 | `e883b0e185866c2b4257264718b525f4e3f6e1f08e1a48072f08511324fe4978` |
| `runs/model-player/t140-jev-v3-w90-r1/match3/jev/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t140-jev-v3-w90-r1/match3/jev/engine-game.stdout.txt` | 769 | `9c1e40bff1d323adb542765c6a0f500fb216780658c98a7a8fd2c8c256f66a4e` |
| `runs/model-player/t140-jev-v3-w90-r1/match3/jev/filmstrip.png` | 148869 | `ba6bcaa78d91fc4062cc957f089acd6e9945ca8f5dffbf3d459498dee0b0ec76` |
| `runs/model-player/t140-jev-v3-w90-r1/match3/jev/frames.json` | 613689 | `684f080d705e61dc5d0b50ff61e3ed01f9e72685494bcb9bb5501878e99e7b89` |
| `runs/model-player/t140-jev-v3-w90-r1/match3/jev/player.json` | 285858 | `c125707f13bb3bfbc335b08143c536a150bbb9b6b3aad2dcc476a509571abc4f` |
| `runs/model-player/t140-jev-v3-w90-r1/match3/jev/session.json` | 13799 | `16aea368833c5e78117791c75b1156e3ca4cd25da0ca0572b221b7e5c8bedc1d` |
| `runs/model-player/t140-jev-v3-w90-r1/match3/jev/steps.jsonl` | 158657 | `cf4a8dfd6fb338ff00d7a266b14e71d179ff90a95fdc575aad27759777b045a6` |
| `calls/**`（1418 个文件，15222731 B）| — | `07f441e54f027b4cad896e1a600daeaf4f091219cef488711c92168c54ff3924` |
| `frames/**`（37 个文件，433578 B）| — | `bcfbfee8645fccadc581b1c5903aae88e3176820744965d18b01cf2f7280efb5` |
| `states/**`（27 个文件，330865 B）| — | `2ff05e5da35855d607c84528d4dcb4341c97b007e44eb3dbe9cd320938d69bd5` |

## t140-jev-v3-w90-r1 / minesweeper / jev

* 目录：`runs/model-player/t140-jev-v3-w90-r1/minesweeper/jev`
* verdict：`INCONCLUSIVE`（counts_as_pass=False，strict=INCONCLUSIVE，baseline=INCONCLUSIVE，game_side=None）
* 档位+轮次：`INCONCLUSIVE @w90 r1`（window=90，round=1，reporting=90，at_reporting_window=True，reporting_state=ok）
* 注入/接受后变化/rate：1 / 1 / 1.0
* 两窗对齐：5/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 2 frame(s))（matched 5/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game minesweeper --backend jev --player model --variant V3 --image-form full --steps 12 --port 9983 --window-frames 90 --round 1 --change-margin strict --out-prefix t140-jev-v3-w90-r1`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t140-jev-v3-w90-r1/minesweeper/jev/demo.png` | 196661 | `5eca77136d51039c80b07468ca143e24a4fd31f92b6c805d2bd0d130c2a726f8` |
| `runs/model-player/t140-jev-v3-w90-r1/minesweeper/jev/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t140-jev-v3-w90-r1/minesweeper/jev/engine-game.stdout.txt` | 745 | `2b3927aa13e5fbcf365a7321f5fcf8af43b67a09de8c2766fe4bdc834773694d` |
| `runs/model-player/t140-jev-v3-w90-r1/minesweeper/jev/filmstrip.png` | 182681 | `3f6ebc402058886b640d9d6203be2fee0cd658ab5cf9777e3e3b5c581351abeb` |
| `runs/model-player/t140-jev-v3-w90-r1/minesweeper/jev/frames.json` | 810156 | `cf894f319010ea1a1293370383031f50189ab44b086bbf4e65c898d4b3196fc8` |
| `runs/model-player/t140-jev-v3-w90-r1/minesweeper/jev/player.json` | 51599 | `8eff22fc21be7f29a479c20f113602f2d478a4516bd9a276ac25ed8f5a1f3312` |
| `runs/model-player/t140-jev-v3-w90-r1/minesweeper/jev/session.json` | 13918 | `27afd3fd26363166c59943c0ce6fe26e5476d91a8a2cf4c393f9155d2e7f912f` |
| `runs/model-player/t140-jev-v3-w90-r1/minesweeper/jev/steps.jsonl` | 133177 | `05e7787e88afa3112831c325c038388bdcced974032c1f307e09c97aa513bc90` |
| `calls/**`（1312 个文件，33912341 B）| — | `376ca08a39561c71b981caa1e98f1bd54b02c2595120d81a56de087787e2fdac` |
| `frames/**`（37 个文件，580787 B）| — | `1b2cca5ae805be4e73780535de3c8a81267b2c0fb48ce75de1a034dec3caa8b9` |
| `states/**`（27 个文件，787144 B）| — | `f4166ac851a3b842bc0c32c25e0398d50a0ccad680491b36dc0d157e11434cc6` |

## t140-jev-v3-w90-r1 / missilecommand / jev

* 目录：`runs/model-player/t140-jev-v3-w90-r1/missilecommand/jev`
* verdict：`INCONCLUSIVE`（counts_as_pass=False，strict=INCONCLUSIVE，baseline=INCONCLUSIVE，game_side=None）
* 档位+轮次：`INCONCLUSIVE @w90 r1`（window=90，round=1，reporting=90，at_reporting_window=True，reporting_state=ok）
* 注入/接受后变化/rate：1 / 1 / 1.0
* 两窗对齐：7/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 2 frame(s))（matched 7/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game missilecommand --backend jev --player model --variant V3 --image-form full --steps 12 --port 9983 --window-frames 90 --round 1 --change-margin strict --out-prefix t140-jev-v3-w90-r1`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t140-jev-v3-w90-r1/missilecommand/jev/demo.png` | 142634 | `b1bb3b144d9f920bb8d5aaf348bcddfae90df1d2da0a5aff68e38ba9139796dd` |
| `runs/model-player/t140-jev-v3-w90-r1/missilecommand/jev/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t140-jev-v3-w90-r1/missilecommand/jev/engine-game.stdout.txt` | 742 | `07996e78c2744d53a7405f6334fc5c2fb278fe7ad7cfa8cb8adfb52ef74327a5` |
| `runs/model-player/t140-jev-v3-w90-r1/missilecommand/jev/filmstrip.png` | 85572 | `89c7961b0365555f71517e04dad9f4d9c5cae78dcec08be462301001481deaa3` |
| `runs/model-player/t140-jev-v3-w90-r1/missilecommand/jev/frames.json` | 728207 | `09f76d4a911c937059be4db96908abda48198f90844bc3453438d61c4ab2cc13` |
| `runs/model-player/t140-jev-v3-w90-r1/missilecommand/jev/player.json` | 52670 | `b4496718f78dd68ffea43c907cf4ce5a70e9b1340f0a53052c553388b43a5437` |
| `runs/model-player/t140-jev-v3-w90-r1/missilecommand/jev/session.json` | 12294 | `4696077b29bf587f3bb81fccc22deed3cf0efa6c378600271aeda0600a68e872` |
| `runs/model-player/t140-jev-v3-w90-r1/missilecommand/jev/steps.jsonl` | 131266 | `1509e6d462f9a576529c682943859db2ae23f8c8adc9fec81aeddc78afe83d80` |
| `calls/**`（1297 个文件，26412249 B）| — | `f2e597024427b712feae5ac16b8cdcac78f820fb0e0dca11c1a45f5f0c02ca98` |
| `frames/**`（37 个文件，519327 B）| — | `fc00dd63898ed69a27a65ec170d3af9f0e540ad80198b6990e7fc1234863d14f` |
| `states/**`（27 个文件，627680 B）| — | `90b4306afd81e19940aa1bb10c0d3a438a79d4647a646b4a724c08a148fcb2fe` |

## t140-jev-v3-w90-r1 / pacman / jev

* 目录：`runs/model-player/t140-jev-v3-w90-r1/pacman/jev`
* verdict：`INCONCLUSIVE`（counts_as_pass=False，strict=INCONCLUSIVE，baseline=INCONCLUSIVE，game_side=None）
* 档位+轮次：`INCONCLUSIVE @w90 r1`（window=90，round=1，reporting=90，at_reporting_window=True，reporting_state=ok）
* 注入/接受后变化/rate：12 / 2 / 1.0
* 两窗对齐：6/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 2 frame(s))（matched 6/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game pacman --backend jev --player model --variant V3 --image-form full --steps 12 --port 9983 --window-frames 90 --round 1 --change-margin strict --out-prefix t140-jev-v3-w90-r1`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t140-jev-v3-w90-r1/pacman/jev/demo.png` | 157544 | `0677cb7f83416c1defb92e421e7474f029b05993f9d3e2655ada28b728df024c` |
| `runs/model-player/t140-jev-v3-w90-r1/pacman/jev/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t140-jev-v3-w90-r1/pacman/jev/engine-game.stdout.txt` | 733 | `89c07a8a4464e369f6b679f727cf1cabea23b5077b7933d40848dca0a012fe83` |
| `runs/model-player/t140-jev-v3-w90-r1/pacman/jev/filmstrip.png` | 144849 | `63bda254e46c172b0f829e31929a30333f2171c7fcd139b5962cb019a95003bd` |
| `runs/model-player/t140-jev-v3-w90-r1/pacman/jev/frames.json` | 569203 | `67738f9d183082111a818a9598a475ceee121f37dd41d642a682cef6ca050cf2` |
| `runs/model-player/t140-jev-v3-w90-r1/pacman/jev/player.json` | 262968 | `d39e2d3d1cb4f8972fe86586682472d2c861463fff2f378924fcc5c43822f191` |
| `runs/model-player/t140-jev-v3-w90-r1/pacman/jev/session.json` | 13364 | `f518fb6837d634209cba1f717d700af55cdc510ae251b98fefd223dd0495a805` |
| `runs/model-player/t140-jev-v3-w90-r1/pacman/jev/steps.jsonl` | 154465 | `902549d9e2a74df1a077ba9afe64d8e90dcec27b265a39da7bffe556531efdf1` |
| `calls/**`（1337 个文件，47154333 B）| — | `fc85629d24d531b14682176fb0a535ef208387f84170bc6907cf9a63995988ee` |
| `frames/**`（37 个文件，400338 B）| — | `ed0e3f728537e26b3460e14052522f5a792e5ab5bdba4c3435dfd8cddc46fb10` |
| `states/**`（27 个文件，1154913 B）| — | `5cf7718391d1aa8b055fa7816e529c8beea3355fa7ab45b3984904ab9fce336a` |

## t140-jev-v3-w90-r1 / platformer / jev

* 目录：`runs/model-player/t140-jev-v3-w90-r1/platformer/jev`
* verdict：`INCONCLUSIVE`（counts_as_pass=False，strict=INCONCLUSIVE，baseline=INCONCLUSIVE，game_side=None）
* 档位+轮次：`INCONCLUSIVE @w90 r1`（window=90，round=1，reporting=90，at_reporting_window=True，reporting_state=ok）
* 注入/接受后变化/rate：4 / 1 / 0.25
* 两窗对齐：1/4 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 1 frame(s))（matched 1/4，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game platformer --backend jev --player model --variant V3 --image-form full --steps 12 --port 9983 --window-frames 90 --round 1 --change-margin strict --out-prefix t140-jev-v3-w90-r1`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t140-jev-v3-w90-r1/platformer/jev/demo.png` | 60512 | `c552ffe9c662c1808aa65980a37ef173b3e64156f939c1ad7c1081530e7f8ef3` |
| `runs/model-player/t140-jev-v3-w90-r1/platformer/jev/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t140-jev-v3-w90-r1/platformer/jev/engine-game.stdout.txt` | 796 | `3b8260d69dada2f56d5eb1cf9c07bf725f28c3b45d7b03e6fb37723681f3e523` |
| `runs/model-player/t140-jev-v3-w90-r1/platformer/jev/filmstrip.png` | 39230 | `60ac807373a6758e9e681903df7846b57238d59208288688f868cac56724db1d` |
| `runs/model-player/t140-jev-v3-w90-r1/platformer/jev/frames.json` | 192872 | `105d7608a673e2ed330c09ce9961988f976d31ed211d781afaf89b24cc6b1424` |
| `runs/model-player/t140-jev-v3-w90-r1/platformer/jev/player.json` | 97559 | `e73fbccc4312069c850e4c08d52b0ace82b5f57efbabc8d9602f057fcfc3063d` |
| `runs/model-player/t140-jev-v3-w90-r1/platformer/jev/session.json` | 12041 | `bf98369a58952bd6e2210b8cdc340fdfe3db38ba0d800b161f8da036c8141f2d` |
| `runs/model-player/t140-jev-v3-w90-r1/platformer/jev/steps.jsonl` | 56542 | `e93571d00fda5cd3567ad214f8e90a75d0eca06606e9e57d549256cf444a2d64` |
| `calls/**`（462 个文件，8461562 B）| — | `27804e6ace096b0d0bad05909454472c0db069ff409ee1777bffaa56bd658559` |
| `frames/**`（13 个文件，135287 B）| — | `2eeb33c534c9418dcef171778fdc352b7a30f40763abd0d510fb609a61af1f03` |
| `states/**`（11 个文件，236416 B）| — | `0484ed18ba4e674c2b3beffff9e887731592fbfb25a3a3da3591297e3f887434` |

## t140-jev-v3-w90-r1 / pong / jev

* 目录：`runs/model-player/t140-jev-v3-w90-r1/pong/jev`
* verdict：`PASS(baseline only)`（counts_as_pass=False，strict=FAIL，baseline=PASS，game_side=None）
* 档位+轮次：`PASS(baseline only) @w90 r1`（window=90，round=1，reporting=90，at_reporting_window=True，reporting_state=ok）
* 注入/接受后变化/rate：8 / 7 / 0.875
* 两窗对齐：6/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 2 frame(s))（matched 6/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game pong --backend jev --player model --variant V3 --image-form full --steps 12 --port 9983 --window-frames 90 --round 1 --change-margin strict --out-prefix t140-jev-v3-w90-r1`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t140-jev-v3-w90-r1/pong/jev/demo.png` | 91762 | `37b5c300a13def866a4a95748b6beff9feeab602c25ae7cf689324fa474b502c` |
| `runs/model-player/t140-jev-v3-w90-r1/pong/jev/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t140-jev-v3-w90-r1/pong/jev/engine-game.stdout.txt` | 4053 | `1ed5ed708635a382551a07f2b8b9849168d1616115b0a079e2c2f4122c049f01` |
| `runs/model-player/t140-jev-v3-w90-r1/pong/jev/filmstrip.png` | 60797 | `13003492760dcc1ea8e2c02ab67654fffcc490c1d14c0031d03d6caec1e9cb20` |
| `runs/model-player/t140-jev-v3-w90-r1/pong/jev/frames.json` | 428829 | `5d111ae1e94d340da4a16d8fa9729dd1ef19a4608a8fa50591e10f313124fb13` |
| `runs/model-player/t140-jev-v3-w90-r1/pong/jev/player.json` | 211992 | `fcc8ee47615fb0e152f13eb92ab29cb557cab4102dba3bc67df264a036de9efb` |
| `runs/model-player/t140-jev-v3-w90-r1/pong/jev/session.json` | 12225 | `16bb04ad7c1bb0838d941eb5885b097f959180e3502898aa625f111717a40654` |
| `runs/model-player/t140-jev-v3-w90-r1/pong/jev/steps.jsonl` | 138557 | `ef148a2eda210ccf79b15081cba192ca9087c4dc9dd8cf19f9b95cf74368b1a8` |
| `calls/**`（1417 个文件，3750338 B）| — | `60abef965164063a1f2bb39d3f98d37562243a0186c49f75a4c53af1c3b44608` |
| `frames/**`（37 个文件，295177 B）| — | `3f611176b4d0b5862be9c0b1ccc21f27a7c99544370c22adcd81e5ccb4d8b4b2` |
| `states/**`（27 个文件，65499 B）| — | `35c18c9b9eb3787acc430074ebc672169e1d2abf46bead9e6f923ec7e6ad7a01` |

## t140-jev-v3-w90-r1 / puzzlebobble / jev

* 目录：`runs/model-player/t140-jev-v3-w90-r1/puzzlebobble/jev`
* verdict：`INCONCLUSIVE`（counts_as_pass=False，strict=INCONCLUSIVE，baseline=INCONCLUSIVE，game_side=None）
* 档位+轮次：`INCONCLUSIVE @w90 r1`（window=90，round=1，reporting=90，at_reporting_window=True，reporting_state=ok）
* 注入/接受后变化/rate：2 / 2 / 1.0
* 两窗对齐：6/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 2 frame(s))（matched 6/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game puzzlebobble --backend jev --player model --variant V3 --image-form full --steps 12 --port 9983 --window-frames 90 --round 1 --change-margin strict --out-prefix t140-jev-v3-w90-r1`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t140-jev-v3-w90-r1/puzzlebobble/jev/demo.png` | 182429 | `0ed82a9e1353758e9d4091894919459e17b198e46aad2904eee1d68d331fbd56` |
| `runs/model-player/t140-jev-v3-w90-r1/puzzlebobble/jev/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t140-jev-v3-w90-r1/puzzlebobble/jev/engine-game.stdout.txt` | 739 | `f103c5c112401e13574bf6aca4637a69bf6148cd96b11e790a7eab20d0075186` |
| `runs/model-player/t140-jev-v3-w90-r1/puzzlebobble/jev/filmstrip.png` | 126534 | `dae2333b047066d6db07031c028718328c4524278fc9329b658804480a2ffe75` |
| `runs/model-player/t140-jev-v3-w90-r1/puzzlebobble/jev/frames.json` | 733427 | `b3bfb2701666286a10cb3657a5ec0172e8d8ac44d6453309ed46d33c92a18d5f` |
| `runs/model-player/t140-jev-v3-w90-r1/puzzlebobble/jev/player.json` | 74468 | `d778f394d16da485185dc73d00e8ca4e0ede8820ff792fdef4ca0761ff2db540` |
| `runs/model-player/t140-jev-v3-w90-r1/puzzlebobble/jev/session.json` | 12191 | `2b9ec6873763b0895cb6cf42b615feb04ed780ca31e54c3df480f54fdd815ffa` |
| `runs/model-player/t140-jev-v3-w90-r1/puzzlebobble/jev/steps.jsonl` | 139481 | `651b1483ed004a259704592390221b75e7517cbb19ec58798c6e9c93fb2750f8` |
| `calls/**`（1340 个文件，23596918 B）| — | `e8101f2b741eb72894f3bf88ecd6543db40d3114707ba09e6b211bcd2bba90bc` |
| `frames/**`（37 个文件，523236 B）| — | `f1890b4a2d79ebe97d40d2d55919f27761e60bb7acf418d959b1394d3d48bd3f` |
| `states/**`（27 个文件，539271 B）| — | `71bb1bf5597ef67ea54a8975958617673d932a12077ae729e5dd270d020efdc0` |

## t140-jev-v3-w90-r1 / rtype / jev

* 目录：`runs/model-player/t140-jev-v3-w90-r1/rtype/jev`
* verdict：`INCONCLUSIVE`（counts_as_pass=False，strict=INCONCLUSIVE，baseline=INCONCLUSIVE，game_side=None）
* 档位+轮次：`INCONCLUSIVE @w90 r1`（window=90，round=1，reporting=90，at_reporting_window=True，reporting_state=ok）
* 注入/接受后变化/rate：0 / 0 / None
* 两窗对齐：5/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 1 frame(s))（matched 5/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game rtype --backend jev --player model --variant V3 --image-form full --steps 12 --port 9983 --window-frames 90 --round 1 --change-margin strict --out-prefix t140-jev-v3-w90-r1`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t140-jev-v3-w90-r1/rtype/jev/demo.png` | 153493 | `9a5a613351dd968364f66c5c2abe33ce813267a46cfcfde65b1fd1461b674128` |
| `runs/model-player/t140-jev-v3-w90-r1/rtype/jev/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t140-jev-v3-w90-r1/rtype/jev/engine-game.stdout.txt` | 743 | `01292b004cb066c56c071df56ed3e152c80161e86203013964cb0b95e4c93bc3` |
| `runs/model-player/t140-jev-v3-w90-r1/rtype/jev/filmstrip.png` | 104310 | `0915488e56c95af4c112604207526aa8c2ac1376efd28c0106c98c907b1f0587` |
| `runs/model-player/t140-jev-v3-w90-r1/rtype/jev/frames.json` | 631993 | `3601c16b2091ee58b6b70fed177683c98cdf335c316c0adea530e40675c817ab` |
| `runs/model-player/t140-jev-v3-w90-r1/rtype/jev/player.json` | 278378 | `b5fd72544b9b11a66c5db2e54d7370f108e2d9751149b857172f6dbb196ff337` |
| `runs/model-player/t140-jev-v3-w90-r1/rtype/jev/session.json` | 12149 | `7e655f63ac46164bec53e84e5b5df99f67d956ebed7341dd070b77a2a739d1b2` |
| `runs/model-player/t140-jev-v3-w90-r1/rtype/jev/steps.jsonl` | 126309 | `9522248549f47379570f22e1099b1e3bc85af1c108ff2f4c5f4b872eb2aee58d` |
| `calls/**`（1343 个文件，21952442 B）| — | `51194943195e66e69c84787f9bd7d8a6b2719d1b53cb262bb9e714fe308d61bc` |
| `frames/**`（37 个文件，447515 B）| — | `5d746aebce755c330bccbbbf7967d4a0382491bf14f31b66bcb4ce18bfb88423` |
| `states/**`（27 个文件，499032 B）| — | `5f2786393c3520e6edc7524f6ce82dd24b8de1bb73023028fb3d6374d5112ab3` |

## t140-jev-v3-w90-r1 / snake / jev

* 目录：`runs/model-player/t140-jev-v3-w90-r1/snake/jev`
* verdict：`INCONCLUSIVE`（counts_as_pass=False，strict=INCONCLUSIVE，baseline=INCONCLUSIVE，game_side=None）
* 档位+轮次：`INCONCLUSIVE @w90 r1`（window=90，round=1，reporting=90，at_reporting_window=True，reporting_state=ok）
* 注入/接受后变化/rate：10 / 10 / 1.0
* 两窗对齐：2/10 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 2 frame(s))（matched 2/10，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game snake --backend jev --player model --variant V3 --image-form full --steps 12 --port 9983 --window-frames 90 --round 1 --change-margin strict --out-prefix t140-jev-v3-w90-r1`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t140-jev-v3-w90-r1/snake/jev/demo.png` | 68061 | `4b28b901c7906ec67f67749071489abee84257dfd1657a6358c255ef5355cab4` |
| `runs/model-player/t140-jev-v3-w90-r1/snake/jev/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t140-jev-v3-w90-r1/snake/jev/engine-game.stdout.txt` | 8868 | `af00d14504666416ffab1cb7bee9cee666576151469f8e46de6bafc69e243fdc` |
| `runs/model-player/t140-jev-v3-w90-r1/snake/jev/filmstrip.png` | 39350 | `41c2cd88e488e6e81e11ef226c9196883ecb52486fe08e866a11fbef5355615a` |
| `runs/model-player/t140-jev-v3-w90-r1/snake/jev/frames.json` | 156709 | `e19da8fa6aed176f0e5af7e77a33a88ec0fe3c7a5a662e2a93e1713344b76442` |
| `runs/model-player/t140-jev-v3-w90-r1/snake/jev/player.json` | 121213 | `5a782da9d658956d2665474c32e30d4cf371775358cfdca38279e9b5c807e8f1` |
| `runs/model-player/t140-jev-v3-w90-r1/snake/jev/session.json` | 12782 | `a9e15a8a14b238b797f31d8d829a391ebb0ab0c306412ee46807955495989e14` |
| `runs/model-player/t140-jev-v3-w90-r1/snake/jev/steps.jsonl` | 137297 | `ae98be688dd3d8987b36d06e5c564990dbd063097d8c24548f5abc9e723eaeae` |
| `calls/**`（839 个文件，6421270 B）| — | `3ada3dae07146755253b4a09907c9beee61e53ab9030677d500fdfe1dcac0d81` |
| `frames/**`（31 个文件，95526 B）| — | `cd35f5a63510e17483d16a0cc2361ee90359c2f46e464edc39338fc1df3023b0` |
| `states/**`（23 个文件，201744 B）| — | `31a13d41cdbfa3a9a2cea0754dd72340ef415cb96616b8232114544ef722fa19` |

## t140-jev-v3-w90-r1 / sokoban / jev

* 目录：`runs/model-player/t140-jev-v3-w90-r1/sokoban/jev`
* verdict：`INCONCLUSIVE`（counts_as_pass=False，strict=INCONCLUSIVE，baseline=INCONCLUSIVE，game_side=None）
* 档位+轮次：`INCONCLUSIVE @w90 r1`（window=90，round=1，reporting=90，at_reporting_window=True，reporting_state=ok）
* 注入/接受后变化/rate：12 / 1 / 0.0833
* 两窗对齐：8/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 1 frame(s))（matched 8/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game sokoban --backend jev --player model --variant V3 --image-form full --steps 12 --port 9983 --window-frames 90 --round 1 --change-margin strict --out-prefix t140-jev-v3-w90-r1`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t140-jev-v3-w90-r1/sokoban/jev/demo.png` | 146601 | `8b52af723e34c9bad1129f8f98af1a1f5d096cb712f19ea301366dbf5e6e3111` |
| `runs/model-player/t140-jev-v3-w90-r1/sokoban/jev/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t140-jev-v3-w90-r1/sokoban/jev/engine-game.stdout.txt` | 745 | `aa1fd0d7f2a58170a028add31f4d297b1cda7c5a8f57b09a096627bf158f988e` |
| `runs/model-player/t140-jev-v3-w90-r1/sokoban/jev/filmstrip.png` | 101789 | `c36aa1e17cee52f19dfcb7cb9aaf4bb2428f85f2ec6d32898a95290f67c394f5` |
| `runs/model-player/t140-jev-v3-w90-r1/sokoban/jev/frames.json` | 586511 | `4976a9edbbfb7200b6570b67b535b02d15c137a886d1197fe432bb00508cc119` |
| `runs/model-player/t140-jev-v3-w90-r1/sokoban/jev/player.json` | 263341 | `80288d37158282502320cfe4a2e4acece6d894960cba4c7d92825f96e13949ac` |
| `runs/model-player/t140-jev-v3-w90-r1/sokoban/jev/session.json` | 13508 | `8b8f3f9f5742196bbb7d36b3cd177df981375d46c426530b62ff76eee79c06ef` |
| `runs/model-player/t140-jev-v3-w90-r1/sokoban/jev/steps.jsonl` | 143282 | `2de31bb0f076e49d48afede93d11bfc352e30397eae0b2078fb6c404774400eb` |
| `calls/**`（1457 个文件，17929960 B）| — | `d98c8a40968763ae35d89f7b98586495869b37f298fc261d71c37086adcca611` |
| `frames/**`（37 个文件，413183 B）| — | `b2b057e7acf0bc74657cb778a30f462ba12bfec58df9b252a7dd25fe4f9b39cb` |
| `states/**`（27 个文件，374553 B）| — | `cd9b33600fd472258c76e4ea6bb576ed36b1c6b881c4e5d0f7cb70e4d3e06007` |

## t140-jev-v3-w90-r1 / spaceinvaders / jev

* 目录：`runs/model-player/t140-jev-v3-w90-r1/spaceinvaders/jev`
* verdict：`INCONCLUSIVE`（counts_as_pass=False，strict=INCONCLUSIVE，baseline=INCONCLUSIVE，game_side=None）
* 档位+轮次：`INCONCLUSIVE @w90 r1`（window=90，round=1，reporting=90，at_reporting_window=True，reporting_state=ok）
* 注入/接受后变化/rate：12 / 6 / 0.5
* 两窗对齐：6/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 2 frame(s))（matched 6/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game spaceinvaders --backend jev --player model --variant V3 --image-form full --steps 12 --port 9983 --window-frames 90 --round 1 --change-margin strict --out-prefix t140-jev-v3-w90-r1`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t140-jev-v3-w90-r1/spaceinvaders/jev/demo.png` | 116442 | `0a3f240dac4cdf082f4a3b0edc86784bb8194789d6588433ff7118dbcfb5fa53` |
| `runs/model-player/t140-jev-v3-w90-r1/spaceinvaders/jev/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t140-jev-v3-w90-r1/spaceinvaders/jev/engine-game.stdout.txt` | 754 | `13b32300de4d6329eeb84ad0c85166e3187e81d2a99a31d1fa498739cd218e5d` |
| `runs/model-player/t140-jev-v3-w90-r1/spaceinvaders/jev/filmstrip.png` | 92625 | `0f43368d81bf79943bb861a78971ce428e7404383a49fce7939540cef8742b6a` |
| `runs/model-player/t140-jev-v3-w90-r1/spaceinvaders/jev/frames.json` | 517063 | `9e8fff2a7f9aab164781fc4e2be5fb3d682037f6fb33fd76cf3eff23d470aff9` |
| `runs/model-player/t140-jev-v3-w90-r1/spaceinvaders/jev/player.json` | 236787 | `ceff6361b29555794307f0498dd6800f61178678dc02f562e497c34e0ef2c81d` |
| `runs/model-player/t140-jev-v3-w90-r1/spaceinvaders/jev/session.json` | 12095 | `204d00c97253c8f69831949afd7852ab9393d9a8ac8a874a247bb3c26f88eff5` |
| `runs/model-player/t140-jev-v3-w90-r1/spaceinvaders/jev/steps.jsonl` | 154389 | `feab8558a79ab6a60fe8a8b0b319e246e48eeefe49de21ed3db56781d92cb0f0` |
| `calls/**`（1432 个文件，11408842 B）| — | `537305678913fe9dcd293c0bd7017cfa233c5c8f1f8330223689e738538be42f` |
| `frames/**`（37 个文件，360918 B）| — | `33867d21945edef2fccf31877bf4233b9dc2f7bcb9e5906e100daaeb71940ad0` |
| `states/**`（27 个文件，240359 B）| — | `a7cff83a24446725b6c706b72ed45cd89e8beb7ebc04136792c99c88dc7b0d04` |

## t140-jev-v3-w90-r1 / tetris / jev

* 目录：`runs/model-player/t140-jev-v3-w90-r1/tetris/jev`
* verdict：`PASS`（counts_as_pass=True，strict=PASS，baseline=PASS，game_side=None）
* 档位+轮次：`PASS @w90 r1`（window=90，round=1，reporting=90，at_reporting_window=True，reporting_state=ok）
* 注入/接受后变化/rate：8 / 8 / 1.0
* 两窗对齐：5/8 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 2 frame(s))（matched 5/8，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game tetris --backend jev --player model --variant V3 --image-form full --steps 12 --port 9983 --window-frames 90 --round 1 --change-margin strict --out-prefix t140-jev-v3-w90-r1`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t140-jev-v3-w90-r1/tetris/jev/demo.png` | 74303 | `d3ce04a38368e33a6fb7647d514b5fe69e8cf8cd2623b33d271cf8b809ce57b0` |
| `runs/model-player/t140-jev-v3-w90-r1/tetris/jev/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t140-jev-v3-w90-r1/tetris/jev/engine-game.stdout.txt` | 10004 | `27eb88082f957668eb5c3379e4db3dfbc8902339edc4f6c4a81934f92d330a72` |
| `runs/model-player/t140-jev-v3-w90-r1/tetris/jev/filmstrip.png` | 43424 | `3066725330309646e4c60639fa87a0b2e4b5c9ccf66f1e0f99709a8017fe3b7b` |
| `runs/model-player/t140-jev-v3-w90-r1/tetris/jev/frames.json` | 199719 | `08a304abb372fff28c3c2e9216ea239c857e62851df5582716a366fe394b4435` |
| `runs/model-player/t140-jev-v3-w90-r1/tetris/jev/player.json` | 118275 | `eb1ccab96715ead7be84e557c574e57dfd0bc3b6ec9669bd536626f2c7b22435` |
| `runs/model-player/t140-jev-v3-w90-r1/tetris/jev/session.json` | 12002 | `022e2cdd2bcdd29017cd278033e7cb567eb8cdd6233c5754226d3d9abf1eeb6c` |
| `runs/model-player/t140-jev-v3-w90-r1/tetris/jev/steps.jsonl` | 98369 | `6e6018b2a8d999bc145f191d2cc738148492128597875f2b3dab82423132281a` |
| `calls/**`（989 个文件，1814712 B）| — | `f420934ae9b4b23f22e65df7be7864997a563fe87739fe15b28a8ce47646cc25` |
| `frames/**`（25 个文件，131740 B）| — | `86205762ac60d0dee30b3d51783e2350d8b4cc59c31f1ac0cbda599d0c96e066` |
| `states/**`（19 个文件，30294 B）| — | `2a76edd96baf7004f63fdc58eb28f9ef25ffc648bc915b5e3b27791f00ac1227` |

## t140-jev-v3-w90-r1 / towerdefense / jev

* 目录：`runs/model-player/t140-jev-v3-w90-r1/towerdefense/jev`
* verdict：`INCONCLUSIVE`（counts_as_pass=False，strict=INCONCLUSIVE，baseline=INCONCLUSIVE，game_side=None）
* 档位+轮次：`INCONCLUSIVE @w90 r1`（window=90，round=1，reporting=90，at_reporting_window=True，reporting_state=ok）
* 注入/接受后变化/rate：8 / 8 / 1.0
* 两窗对齐：4/8 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 1 frame(s))（matched 4/8，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game towerdefense --backend jev --player model --variant V3 --image-form full --steps 12 --port 9983 --window-frames 90 --round 1 --change-margin strict --out-prefix t140-jev-v3-w90-r1`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t140-jev-v3-w90-r1/towerdefense/jev/demo.png` | 140492 | `0d40b174990e6ada45fa1a1a92e855a5d97a1f71b49853db67ee5480878b2f3b` |
| `runs/model-player/t140-jev-v3-w90-r1/towerdefense/jev/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t140-jev-v3-w90-r1/towerdefense/jev/engine-game.stdout.txt` | 753 | `fd923f6cf98c849c5979f87114033f267b55e6f1a539f0167e0d1062b79b3e32` |
| `runs/model-player/t140-jev-v3-w90-r1/towerdefense/jev/filmstrip.png` | 80198 | `33ff043a685003fcbd16351a3724e4323ef96e620ceaad88eacee6ce6e10fa06` |
| `runs/model-player/t140-jev-v3-w90-r1/towerdefense/jev/frames.json` | 442025 | `1344d0c72c22b48c9b4d01b7df93673d5ad11b33652629072239eebad96ad6f0` |
| `runs/model-player/t140-jev-v3-w90-r1/towerdefense/jev/player.json` | 200567 | `6481ef40dee20d54fc456d11ce122539eff3f0d1cef1274d386572945b3a0c86` |
| `runs/model-player/t140-jev-v3-w90-r1/towerdefense/jev/session.json` | 13742 | `6344e7cd6bff4cb46a48665fc9933781fc178ea4932d56d2210c423edbf30091` |
| `runs/model-player/t140-jev-v3-w90-r1/towerdefense/jev/steps.jsonl` | 100285 | `d51ba17da11ed56c57767312fdff72bdc55e187498128e65f64363628c0fa4d4` |
| `calls/**`（908 个文件，18227969 B）| — | `5bed29d02bf6a5592d2bfebf7d791ce840b31d3297a14cf93f5917fea3cdf2ed` |
| `frames/**`（25 个文件，313383 B）| — | `4f7dfcb34246bc2a2cebbb0b6c1664e53f11d86a8633994af9170cca09cb44a2` |
| `states/**`（19 个文件，451881 B）| — | `b9068f3cc975199bafcb009df179732e6e915a5728669bdb63eee875bed3ccce` |

## t140-jev-v3-w90-r2 / asteroids / jev

* 目录：`runs/model-player/t140-jev-v3-w90-r2/asteroids/jev`
* verdict：`PASS(baseline only)`（counts_as_pass=False，strict=FAIL，baseline=PASS，game_side=None）
* 档位+轮次：`PASS(baseline only) @w90 r2`（window=90，round=2，reporting=90，at_reporting_window=True，reporting_state=ok）
* 注入/接受后变化/rate：12 / 10 / 0.8333
* 两窗对齐：4/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 2 frame(s))（matched 4/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game asteroids --backend jev --player model --variant V3 --image-form full --steps 12 --port 9984 --window-frames 90 --round 2 --change-margin strict --out-prefix t140-jev-v3-w90-r2`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t140-jev-v3-w90-r2/asteroids/jev/demo.png` | 122780 | `b1c8a098cf7a851a64449cc10eb54015d7a4192dab35bf508c5837216f8f825a` |
| `runs/model-player/t140-jev-v3-w90-r2/asteroids/jev/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t140-jev-v3-w90-r2/asteroids/jev/engine-game.stdout.txt` | 741 | `b31977d0132388ff666b97ba12522590464a511bd2e2a46f5f4c9b4ab3d573e0` |
| `runs/model-player/t140-jev-v3-w90-r2/asteroids/jev/filmstrip.png` | 77307 | `179adf545c1d350198a6aa9f2c09ccfc318a9d1b2db69c09e83312d58c5dd177` |
| `runs/model-player/t140-jev-v3-w90-r2/asteroids/jev/frames.json` | 548484 | `54d4916addacb2cffc37a8a99417a8af3f0dbc6669ed0fcf13de3e9abad4d9a0` |
| `runs/model-player/t140-jev-v3-w90-r2/asteroids/jev/player.json` | 250614 | `3c715aa900cf42fdd2e959ddabcce105a37ad4d9336534e044e7ad364f61eeff` |
| `runs/model-player/t140-jev-v3-w90-r2/asteroids/jev/session.json` | 12082 | `6fcad21efd683fbd0ad2dfd5737d51d9e9d71771ea178ce0016a2e95c87fd918` |
| `runs/model-player/t140-jev-v3-w90-r2/asteroids/jev/steps.jsonl` | 168604 | `46e4da63fbef1f6a9e20bf4b132341c46ca79a6a0710c82850d15c13e2b7a79e` |
| `calls/**`（1440 个文件，4816344 B）| — | `b513aacd4ec7a6d1ddfe5ad0ef0c10e20d54913545f675a4433c9ec818fcd454` |
| `frames/**`（37 个文件，384625 B）| — | `a1f47edaf55d122b645532db3fccd1116a43202802066b70af303ebcadb62f33` |
| `states/**`（27 个文件，84857 B）| — | `c5472459856d27666e0f76e40e8fc23bc7a55c990a298d73b1f64ff17dc20b7b` |

## t140-jev-v3-w90-r2 / bomberman / jev

* 目录：`runs/model-player/t140-jev-v3-w90-r2/bomberman/jev`
* verdict：`INCONCLUSIVE`（counts_as_pass=False，strict=INCONCLUSIVE，baseline=INCONCLUSIVE，game_side=None）
* 档位+轮次：`INCONCLUSIVE @w90 r2`（window=90，round=2，reporting=90，at_reporting_window=True，reporting_state=ok）
* 注入/接受后变化/rate：12 / 1 / 1.0
* 两窗对齐：8/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 2 frame(s))（matched 8/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game bomberman --backend jev --player model --variant V3 --image-form full --steps 12 --port 9984 --window-frames 90 --round 2 --change-margin strict --out-prefix t140-jev-v3-w90-r2`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t140-jev-v3-w90-r2/bomberman/jev/demo.png` | 165544 | `3b2bb0ffa65d5e923df056832da4ac3115f8d8ae0e50edda9f0b64f3c318fd6e` |
| `runs/model-player/t140-jev-v3-w90-r2/bomberman/jev/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t140-jev-v3-w90-r2/bomberman/jev/engine-game.stdout.txt` | 775 | `650ca2f294068b7e4eacb7e78c227b7984ca162d68aecad99b1faf8e3e563d5f` |
| `runs/model-player/t140-jev-v3-w90-r2/bomberman/jev/filmstrip.png` | 142395 | `265a175470b72a7d914e3cf5182588cef2ff1ae9cf8e33b384669d3cbeb06324` |
| `runs/model-player/t140-jev-v3-w90-r2/bomberman/jev/frames.json` | 511148 | `c29f2786c7970ced6f3ab6054d9737ee0b8ad69786a97349673edae5ca11a9c0` |
| `runs/model-player/t140-jev-v3-w90-r2/bomberman/jev/player.json` | 250444 | `309ed518ecb63304ed3fdbcf5125ec043c2d2769e3577f50a4e2c918b47bd398` |
| `runs/model-player/t140-jev-v3-w90-r2/bomberman/jev/session.json` | 12951 | `ab0795561bfa92eae5ec9162480a447718f710bb439b7fb686982fa586545d03` |
| `runs/model-player/t140-jev-v3-w90-r2/bomberman/jev/steps.jsonl` | 158001 | `d4909a2e17913737fdfb96ca33a4b4c8b18cf79e3c77a93b15bdc870630f781c` |
| `calls/**`（1368 个文件，25777975 B）| — | `2cc59edc70e1deda852bbb45799566c00cf448ffae75946d89b24eb4b34fa106` |
| `frames/**`（37 个文件，356515 B）| — | `64a84177d7af20a9ea304aee068948b54a23f3a0862af9b7334f2daf0fbb29af` |
| `states/**`（27 个文件，603262 B）| — | `13f4ff62546c8f062439f8c899388e2fc37a2ca3ebc1ffc32eab487d15c1d953` |

## t140-jev-v3-w90-r2 / breakout / jev

* 目录：`runs/model-player/t140-jev-v3-w90-r2/breakout/jev`
* verdict：`FAIL`（counts_as_pass=False，strict=FAIL，baseline=FAIL，game_side=None）
* 档位+轮次：`FAIL @w90 r2`（window=90，round=2，reporting=90，at_reporting_window=True，reporting_state=ok）
* 注入/接受后变化/rate：12 / 7 / 0.5833
* 两窗对齐：2/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 2 frame(s))（matched 2/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game breakout --backend jev --player model --variant V3 --image-form full --steps 12 --port 9984 --window-frames 90 --round 2 --change-margin strict --out-prefix t140-jev-v3-w90-r2`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t140-jev-v3-w90-r2/breakout/jev/demo.png` | 96914 | `4a0291ae71667092d9a2338bf9394200cefe5195ffd8243285afa488afc8b269` |
| `runs/model-player/t140-jev-v3-w90-r2/breakout/jev/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t140-jev-v3-w90-r2/breakout/jev/engine-game.stdout.txt` | 44043 | `0e22317ebfe9864aa32b97cf84192b4ab01e7757c0d9333ec28f108d66fe2c17` |
| `runs/model-player/t140-jev-v3-w90-r2/breakout/jev/filmstrip.png` | 65879 | `23241797eb6e1c932e9d566bd7253b624b24befdd41721aecb47cb86cdb7c401` |
| `runs/model-player/t140-jev-v3-w90-r2/breakout/jev/frames.json` | 341653 | `10242ab450747b453d2548cf91c99eccb93da175b973190ee2266c063d38af7b` |
| `runs/model-player/t140-jev-v3-w90-r2/breakout/jev/player.json` | 179909 | `383c403bfc5ac0612b9328e6454e53d44a768740a5ec1f6d5750a6264b879238` |
| `runs/model-player/t140-jev-v3-w90-r2/breakout/jev/session.json` | 12245 | `7a5bb79cbc57e15296caa1c32adcc853af9e1e97792dd6c5e8f0788ebf27788b` |
| `runs/model-player/t140-jev-v3-w90-r2/breakout/jev/steps.jsonl` | 162777 | `d4c0806a59c42e8203cc9305f7f55e09569e2aac8b4245c0b31374f16cad7c13` |
| `calls/**`（1081 个文件，5576601 B）| — | `79eef26eb445f4ced1e969f9cc2b245c5cc2adcbd435818bdb34cf696b326415` |
| `frames/**`（37 个文件，229547 B）| — | `01f9732355c1169e828bc96f5c62cfc83a505fc103cae23be4a7d0de611522e6` |
| `states/**`（27 个文件，147305 B）| — | `7527b115e99bf492f3900184a624650de27318a7337a51dd88a8efc9a47603be` |

## t140-jev-v3-w90-r2 / flappy / jev

* 目录：`runs/model-player/t140-jev-v3-w90-r2/flappy/jev`
* verdict：`FAIL`（counts_as_pass=False，strict=FAIL，baseline=FAIL，game_side=None）
* 档位+轮次：`FAIL @w90 r2`（window=90，round=2，reporting=90，at_reporting_window=True，reporting_state=ok）
* 注入/接受后变化/rate：3 / 1 / 0.3333
* 两窗对齐：5/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 2 frame(s))（matched 5/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game flappy --backend jev --player model --variant V3 --image-form full --steps 12 --port 9984 --window-frames 90 --round 2 --change-margin strict --out-prefix t140-jev-v3-w90-r2`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t140-jev-v3-w90-r2/flappy/jev/demo.png` | 117153 | `641ca0f96ce2d78fb894609c3e03d5be998b43df5009bc0767fd9265588b39cc` |
| `runs/model-player/t140-jev-v3-w90-r2/flappy/jev/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t140-jev-v3-w90-r2/flappy/jev/engine-game.stdout.txt` | 743 | `8562b5eac025bd585778ec0b62b8dd56b7559bfb01f015e08ba722c681a0b174` |
| `runs/model-player/t140-jev-v3-w90-r2/flappy/jev/filmstrip.png` | 90438 | `234ed35662e59523c3a229e1819d13ea20eec8ae5b9a94aaf73adaf0f2302a9d` |
| `runs/model-player/t140-jev-v3-w90-r2/flappy/jev/frames.json` | 550451 | `0a78dbd52c0cf9e82dfaf8160f11f650f7cd1354cc0cce5f4c0ba20d6fa5f541` |
| `runs/model-player/t140-jev-v3-w90-r2/flappy/jev/player.json` | 240651 | `7502dc6a4cd02bb66a77cbb6dc02b6203a08fd404987f160f4044d3abdab2d53` |
| `runs/model-player/t140-jev-v3-w90-r2/flappy/jev/session.json` | 12034 | `5e77eb3bc8f8eac7bebcceea6952af4b4ca43a8a17c25300803d6fb02e1b52cb` |
| `runs/model-player/t140-jev-v3-w90-r2/flappy/jev/steps.jsonl` | 144818 | `7535d2825cdbc600d566a217272adbb05de807210d94a53ec9018aa5d52853ea` |
| `calls/**`（1435 个文件，4956206 B）| — | `4cbff6d20cabf662d783103a0fca58eba9b6819a8c34c123caf5639fda1b3249` |
| `frames/**`（37 个文件，386424 B）| — | `83c5e88194ebc4cf92bc2ecd997ca419b5c96a569f3c936c761589e6d08440ae` |
| `states/**`（27 个文件，87082 B）| — | `e079ce6a73cf72f2628162a250f645cf0d9f5da2132399a771fe2c6b155b51f7` |

## t140-jev-v3-w90-r2 / frogger / jev

* 目录：`runs/model-player/t140-jev-v3-w90-r2/frogger/jev`
* verdict：`INCONCLUSIVE`（counts_as_pass=False，strict=INCONCLUSIVE，baseline=INCONCLUSIVE，game_side=None）
* 档位+轮次：`INCONCLUSIVE @w90 r2`（window=90，round=2，reporting=90，at_reporting_window=True，reporting_state=ok）
* 注入/接受后变化/rate：12 / 6 / 1.0
* 两窗对齐：7/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 1 frame(s))（matched 7/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game frogger --backend jev --player model --variant V3 --image-form full --steps 12 --port 9984 --window-frames 90 --round 2 --change-margin strict --out-prefix t140-jev-v3-w90-r2`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t140-jev-v3-w90-r2/frogger/jev/demo.png` | 135672 | `8cebfc5131cdf4c76dff1079d79066c4b64b0919df871f37844dc1e511b6fda8` |
| `runs/model-player/t140-jev-v3-w90-r2/frogger/jev/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t140-jev-v3-w90-r2/frogger/jev/engine-game.stdout.txt` | 748 | `b9dcff7cc5db98881ae2b3239d0ecc9259d1141978e46543903d1d2d84bfeea1` |
| `runs/model-player/t140-jev-v3-w90-r2/frogger/jev/filmstrip.png` | 92818 | `92acdc1dc714ba6e05b6c14be7384d1439ac5850af2cfef9e5f5387a6d44d41c` |
| `runs/model-player/t140-jev-v3-w90-r2/frogger/jev/frames.json` | 594401 | `43f2166ff522feb8914e3d7aac7d3cbdce5fde9519cdad662f1ad8427411de11` |
| `runs/model-player/t140-jev-v3-w90-r2/frogger/jev/player.json` | 267833 | `d30d22422716ac61889b4257e0c5f89a8fb3dd7d91106cc0d0532e35c1d66239` |
| `runs/model-player/t140-jev-v3-w90-r2/frogger/jev/session.json` | 11983 | `cdd7fe17516c7cd61cffe74d153b7001716690b71c252d955a51d4d8937119cd` |
| `runs/model-player/t140-jev-v3-w90-r2/frogger/jev/steps.jsonl` | 148709 | `16faa1bbbf0058ae9cfe32f1b3e238dbe48aadb578a29df0bf20e381de7b72c8` |
| `calls/**`（1483 个文件，6527594 B）| — | `08f2fd2e4382dabaa937810c2bbf516f6c623e2899587d58f0a5aedd02bb07cd` |
| `frames/**`（37 个文件，419130 B）| — | `3e1116a8c565c83046bd5f50ea9ae21091f31e8a78b91ee3db4f81b7c82eea8c` |
| `states/**`（27 个文件，119928 B）| — | `7512c20189eeb8b3b6c4461097caf631f2e6915f84b568d6995af03bc9fcfd9f` |

## t140-jev-v3-w90-r2 / game2048 / jev

* 目录：`runs/model-player/t140-jev-v3-w90-r2/game2048/jev`
* verdict：`INCONCLUSIVE`（counts_as_pass=False，strict=INCONCLUSIVE，baseline=INCONCLUSIVE，game_side=None）
* 档位+轮次：`INCONCLUSIVE @w90 r2`（window=90，round=2，reporting=90，at_reporting_window=True，reporting_state=ok）
* 注入/接受后变化/rate：5 / 5 / 1.0
* 两窗对齐：6/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 2 frame(s))（matched 6/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game game2048 --backend jev --player model --variant V3 --image-form full --steps 12 --port 9984 --window-frames 90 --round 2 --change-margin strict --out-prefix t140-jev-v3-w90-r2`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t140-jev-v3-w90-r2/game2048/jev/demo.png` | 140690 | `2fc42369c712da6d13bc81e8d1a77405476301f6b9f07f12af303dbc947b7ee6` |
| `runs/model-player/t140-jev-v3-w90-r2/game2048/jev/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t140-jev-v3-w90-r2/game2048/jev/engine-game.stdout.txt` | 781 | `dab23e1e1475d16d2cc9f85515a6fd8da35a19db56adb634405ebc86154547f2` |
| `runs/model-player/t140-jev-v3-w90-r2/game2048/jev/filmstrip.png` | 90747 | `a4e0c5d897fd5986d8478cf4199e4cba421179f344177cab1fbaf98668581185` |
| `runs/model-player/t140-jev-v3-w90-r2/game2048/jev/frames.json` | 677592 | `9837a4e352989bd743faefce223831eae218ac33a470f0f5939be1638b0ff954` |
| `runs/model-player/t140-jev-v3-w90-r2/game2048/jev/player.json` | 131276 | `152abc5b8fd76f5d0edc617973649bd9654e94d627f78a138fd3bc29309c0ef6` |
| `runs/model-player/t140-jev-v3-w90-r2/game2048/jev/session.json` | 11937 | `e12ea72b078ae88d9d7645544a48d85f6b39d79c1de8e41607b2566c40adc956` |
| `runs/model-player/t140-jev-v3-w90-r2/game2048/jev/steps.jsonl` | 144209 | `07ecfd3f82b8b5d3cc32e378bdb41f8ea9488dd5c2c21218cc3b9171573f7de1` |
| `calls/**`（1427 个文件，10257391 B）| — | `dfe1952ff24943ab8ce734b513a79b54b3d4ae796dead4bafa3128246e85c8dd` |
| `frames/**`（37 个文件，481433 B）| — | `aeed35706fdc588f7f370f3f2ddb114c5e83f55de49bbb1eb372c1729dea404b` |
| `states/**`（27 个文件，202815 B）| — | `2c051a0b0e227623c02a9bfad7443fe4a576348a34f06485c35d9567d1efe626` |

## t140-jev-v3-w90-r2 / lunarlander / jev

* 目录：`runs/model-player/t140-jev-v3-w90-r2/lunarlander/jev`
* verdict：`INCONCLUSIVE`（counts_as_pass=False，strict=INCONCLUSIVE，baseline=INCONCLUSIVE，game_side=None）
* 档位+轮次：`INCONCLUSIVE @w90 r2`（window=90，round=2，reporting=90，at_reporting_window=True，reporting_state=ok）
* 注入/接受后变化/rate：0 / 0 / None
* 两窗对齐：9/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 1 frame(s))（matched 9/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game lunarlander --backend jev --player model --variant V3 --image-form full --steps 12 --port 9984 --window-frames 90 --round 2 --change-margin strict --out-prefix t140-jev-v3-w90-r2`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t140-jev-v3-w90-r2/lunarlander/jev/demo.png` | 136641 | `5ccf7b0b66c36063e534b967624081e59e05be1c06c9b330a931367f934933a4` |
| `runs/model-player/t140-jev-v3-w90-r2/lunarlander/jev/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t140-jev-v3-w90-r2/lunarlander/jev/engine-game.stdout.txt` | 766 | `c4a229b83e823466bca161da3cbb59f9e94fe7386c5ee5b35f724e7ce9420315` |
| `runs/model-player/t140-jev-v3-w90-r2/lunarlander/jev/filmstrip.png` | 105271 | `9f71305a54be9384364f5172fff5367e8b8a7dcdc44ddde4a34f1af4e9a8e6e6` |
| `runs/model-player/t140-jev-v3-w90-r2/lunarlander/jev/frames.json` | 628653 | `c1ac67ee04da21fb73b87d923b1d54c5ac90a6c2f4be4ceea1bf7e0d9d029dd8` |
| `runs/model-player/t140-jev-v3-w90-r2/lunarlander/jev/player.json` | 270240 | `8c252d5efb50fbca575524bb3a180979db3789c04dfc0fb7680061ebe1c301e2` |
| `runs/model-player/t140-jev-v3-w90-r2/lunarlander/jev/session.json` | 12002 | `dd29679af9101e3b748c9dbd5d2fc3610162ea4857bfde8230c63bbb4c3ad449` |
| `runs/model-player/t140-jev-v3-w90-r2/lunarlander/jev/steps.jsonl` | 124722 | `399d051f272ea9a4d0f6698a8d802e024078c9a0be0cbe1d96df3e1c5d0f0271` |
| `calls/**`（1404 个文件，15216412 B）| — | `ded2a6921da62d69f6cf1d42d4a6af1b1802863020095600fbb6b6a74c9790e3` |
| `frames/**`（37 个文件，444999 B）| — | `e29968bf53c61f91525ae9298c9ff7156d8758644f612a9af13c2a9bfe42a2f9` |
| `states/**`（27 个文件，322133 B）| — | `6a7cfe1ab9aacd77e566de09bd42b8a4bcf5d80068cfd50150fdc3783f2263ba` |

## t140-jev-v3-w90-r2 / match3 / jev

* 目录：`runs/model-player/t140-jev-v3-w90-r2/match3/jev`
* verdict：`INCONCLUSIVE`（counts_as_pass=False，strict=INCONCLUSIVE，baseline=INCONCLUSIVE，game_side=None）
* 档位+轮次：`INCONCLUSIVE @w90 r2`（window=90，round=2，reporting=90，at_reporting_window=True，reporting_state=ok）
* 注入/接受后变化/rate：12 / 1 / 1.0
* 两窗对齐：8/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 2 frame(s))（matched 8/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game match3 --backend jev --player model --variant V3 --image-form full --steps 12 --port 9984 --window-frames 90 --round 2 --change-margin strict --out-prefix t140-jev-v3-w90-r2`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t140-jev-v3-w90-r2/match3/jev/demo.png` | 207087 | `e883b0e185866c2b4257264718b525f4e3f6e1f08e1a48072f08511324fe4978` |
| `runs/model-player/t140-jev-v3-w90-r2/match3/jev/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t140-jev-v3-w90-r2/match3/jev/engine-game.stdout.txt` | 769 | `148a34e6a891ece90cd3925f9dcec944fe1cc2bd57aaaf2828d71a5a5bcea410` |
| `runs/model-player/t140-jev-v3-w90-r2/match3/jev/filmstrip.png` | 148869 | `ba6bcaa78d91fc4062cc957f089acd6e9945ca8f5dffbf3d459498dee0b0ec76` |
| `runs/model-player/t140-jev-v3-w90-r2/match3/jev/frames.json` | 613694 | `a6679cd8fdf21db304f4b2045f5148055580033df88b1bf9f3f78a0853560d64` |
| `runs/model-player/t140-jev-v3-w90-r2/match3/jev/player.json` | 285855 | `aea41e0ca4c3f77e9e46d778d53b2235aec4a398bc48252a077456aaa1e0236d` |
| `runs/model-player/t140-jev-v3-w90-r2/match3/jev/session.json` | 13799 | `675f914289c0193e60be989b39418b9783b9daf83a36336b98fe044aa55bf0cb` |
| `runs/model-player/t140-jev-v3-w90-r2/match3/jev/steps.jsonl` | 158663 | `cb1e664b838eec9b751080c820d3ff6e04aa030dd60ca1ebe9b9779b9a1620fc` |
| `calls/**`（1439 个文件，15457118 B）| — | `27c200587e8dc46a46e5162db28d0111057410e4d354608aad880f70cdfed42d` |
| `frames/**`（37 个文件，433578 B）| — | `a104ee5454991fa7a1ecada0e6f9f5ce3409abccbde0bc89b2623a09ead46865` |
| `states/**`（27 个文件，330864 B）| — | `016db1edb0db31d3ee765912516ab2afbffa26474f805f90a1099473dc3747e9` |

## t140-jev-v3-w90-r2 / minesweeper / jev

* 目录：`runs/model-player/t140-jev-v3-w90-r2/minesweeper/jev`
* verdict：`INCONCLUSIVE`（counts_as_pass=False，strict=INCONCLUSIVE，baseline=INCONCLUSIVE，game_side=None）
* 档位+轮次：`INCONCLUSIVE @w90 r2`（window=90，round=2，reporting=90，at_reporting_window=True，reporting_state=ok）
* 注入/接受后变化/rate：1 / 1 / 1.0
* 两窗对齐：5/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 2 frame(s))（matched 5/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game minesweeper --backend jev --player model --variant V3 --image-form full --steps 12 --port 9984 --window-frames 90 --round 2 --change-margin strict --out-prefix t140-jev-v3-w90-r2`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t140-jev-v3-w90-r2/minesweeper/jev/demo.png` | 196661 | `5eca77136d51039c80b07468ca143e24a4fd31f92b6c805d2bd0d130c2a726f8` |
| `runs/model-player/t140-jev-v3-w90-r2/minesweeper/jev/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t140-jev-v3-w90-r2/minesweeper/jev/engine-game.stdout.txt` | 745 | `b9a7f503a03ba5dc1db9d74f7971bd8d6d84804093b99abc3b8e2031e8a70840` |
| `runs/model-player/t140-jev-v3-w90-r2/minesweeper/jev/filmstrip.png` | 182681 | `3f6ebc402058886b640d9d6203be2fee0cd658ab5cf9777e3e3b5c581351abeb` |
| `runs/model-player/t140-jev-v3-w90-r2/minesweeper/jev/frames.json` | 810157 | `f702fc9677d5d269d5ad5cf65a20a7278018d612b903159de95b69e9fd7e3f0e` |
| `runs/model-player/t140-jev-v3-w90-r2/minesweeper/jev/player.json` | 51598 | `bb2714d6f15386494a28dc35984b2df652d4459291735a40595992bb1d98d919` |
| `runs/model-player/t140-jev-v3-w90-r2/minesweeper/jev/session.json` | 13916 | `2d07c382633d23b4d22cdc95b132e07fdca348325161331e7cef0153f44baa3b` |
| `runs/model-player/t140-jev-v3-w90-r2/minesweeper/jev/steps.jsonl` | 133177 | `b99edc42fab25b5d1e5a0556280e617d2a436b7aeef70c32bc0103122c7d16e3` |
| `calls/**`（1314 个文件，33965346 B）| — | `8eb0542a56cd36b36726975cbad3e62326c6e571e0794518a118bd1563bdf4bd` |
| `frames/**`（37 个文件，580787 B）| — | `fbe2092db71e4ffba163e26b8af954f941d658d97ad3dc21bd24860e84684e64` |
| `states/**`（27 个文件，787145 B）| — | `481878f5e2f397209e2f8a468165c93420ed2ea635960ec89cad2cec6dda0ee5` |

## t140-jev-v3-w90-r2 / missilecommand / jev

* 目录：`runs/model-player/t140-jev-v3-w90-r2/missilecommand/jev`
* verdict：`INCONCLUSIVE`（counts_as_pass=False，strict=INCONCLUSIVE，baseline=INCONCLUSIVE，game_side=None）
* 档位+轮次：`INCONCLUSIVE @w90 r2`（window=90，round=2，reporting=90，at_reporting_window=True，reporting_state=ok）
* 注入/接受后变化/rate：1 / 1 / 1.0
* 两窗对齐：4/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 2 frame(s))（matched 4/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game missilecommand --backend jev --player model --variant V3 --image-form full --steps 12 --port 9984 --window-frames 90 --round 2 --change-margin strict --out-prefix t140-jev-v3-w90-r2`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t140-jev-v3-w90-r2/missilecommand/jev/demo.png` | 142634 | `b1bb3b144d9f920bb8d5aaf348bcddfae90df1d2da0a5aff68e38ba9139796dd` |
| `runs/model-player/t140-jev-v3-w90-r2/missilecommand/jev/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t140-jev-v3-w90-r2/missilecommand/jev/engine-game.stdout.txt` | 742 | `58ec317dfb6e3010057c263b84473a858c212b99c276761599648e175059e45d` |
| `runs/model-player/t140-jev-v3-w90-r2/missilecommand/jev/filmstrip.png` | 85572 | `89c7961b0365555f71517e04dad9f4d9c5cae78dcec08be462301001481deaa3` |
| `runs/model-player/t140-jev-v3-w90-r2/missilecommand/jev/frames.json` | 728210 | `4d29da1d4e3d56269212acf09f1a858b1f95b60660e7fe1a0406d35c57ca9726` |
| `runs/model-player/t140-jev-v3-w90-r2/missilecommand/jev/player.json` | 52671 | `35404871cc8ee35b45d50c5ef0d641af585adaacc69174db3aeff0f3910f3bb6` |
| `runs/model-player/t140-jev-v3-w90-r2/missilecommand/jev/session.json` | 12293 | `c23ed89e9d61b763237d14174683d43b8ed77bd04a6df37064537c1f0c08fdec` |
| `runs/model-player/t140-jev-v3-w90-r2/missilecommand/jev/steps.jsonl` | 131276 | `41070afd63dafb190086a29363910278b58d5178d3add957733cd82d7a329ab0` |
| `calls/**`（1327 个文件，27038665 B）| — | `53423f3b66ab480c968bdb127753380111d17a838d08adfca2adb23fd66c1366` |
| `frames/**`（37 个文件，519327 B）| — | `c92b654196a081a6b7893f1d75fe3d6bdf6528af3df32e368c7df1f1bf7e28bf` |
| `states/**`（27 个文件，627680 B）| — | `cc9ec16d49a1051c3a1bc351d2d92621d253ee2d685be768a189f8981df078b1` |

## t140-jev-v3-w90-r2 / pacman / jev

* 目录：`runs/model-player/t140-jev-v3-w90-r2/pacman/jev`
* verdict：`INCONCLUSIVE`（counts_as_pass=False，strict=INCONCLUSIVE，baseline=INCONCLUSIVE，game_side=None）
* 档位+轮次：`INCONCLUSIVE @w90 r2`（window=90，round=2，reporting=90，at_reporting_window=True，reporting_state=ok）
* 注入/接受后变化/rate：12 / 2 / 1.0
* 两窗对齐：7/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 2 frame(s))（matched 7/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game pacman --backend jev --player model --variant V3 --image-form full --steps 12 --port 9984 --window-frames 90 --round 2 --change-margin strict --out-prefix t140-jev-v3-w90-r2`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t140-jev-v3-w90-r2/pacman/jev/demo.png` | 157544 | `0677cb7f83416c1defb92e421e7474f029b05993f9d3e2655ada28b728df024c` |
| `runs/model-player/t140-jev-v3-w90-r2/pacman/jev/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t140-jev-v3-w90-r2/pacman/jev/engine-game.stdout.txt` | 733 | `2e4ce85958e73568d911ab303bee7223b5bee946dbade232b105e47e08b40ed0` |
| `runs/model-player/t140-jev-v3-w90-r2/pacman/jev/filmstrip.png` | 144849 | `63bda254e46c172b0f829e31929a30333f2171c7fcd139b5962cb019a95003bd` |
| `runs/model-player/t140-jev-v3-w90-r2/pacman/jev/frames.json` | 569203 | `0d78bd0321f94eaf0c120679f7d082dda292125c687d32bf406c1e787f132725` |
| `runs/model-player/t140-jev-v3-w90-r2/pacman/jev/player.json` | 262964 | `1f27c6be6db4bc25f455dc039e188da6e61f9518c1a4a39925da168b2a463b97` |
| `runs/model-player/t140-jev-v3-w90-r2/pacman/jev/session.json` | 13364 | `847a872a82fa6a797fef0a503cba02da11c3745792be07c92e60d31198df9726` |
| `runs/model-player/t140-jev-v3-w90-r2/pacman/jev/steps.jsonl` | 154464 | `ea9f2459a79854aac13867367a7c487438f860fc60895376c6d5cad0bd2a736c` |
| `calls/**`（1336 个文件，47114302 B）| — | `3f2ec7db03d30efdeb6319aead320c3639ee733f8735e813efaadbd790b11833` |
| `frames/**`（37 个文件，400338 B）| — | `b8ba3cb36e4761f0d82571fc21557fe266cb7775ad5e0dd0a9ebd6e8c58e7aa1` |
| `states/**`（27 个文件，1154913 B）| — | `9faf845fffcd49b6fe3aff70766e80a07a16da5c171d02ba2f7137be9abf02a9` |

## t140-jev-v3-w90-r2 / platformer / jev

* 目录：`runs/model-player/t140-jev-v3-w90-r2/platformer/jev`
* verdict：`INCONCLUSIVE`（counts_as_pass=False，strict=INCONCLUSIVE，baseline=INCONCLUSIVE，game_side=None）
* 档位+轮次：`INCONCLUSIVE @w90 r2`（window=90，round=2，reporting=90，at_reporting_window=True，reporting_state=ok）
* 注入/接受后变化/rate：4 / 1 / 0.25
* 两窗对齐：3/4 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 2 frame(s))（matched 3/4，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game platformer --backend jev --player model --variant V3 --image-form full --steps 12 --port 9984 --window-frames 90 --round 2 --change-margin strict --out-prefix t140-jev-v3-w90-r2`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t140-jev-v3-w90-r2/platformer/jev/demo.png` | 60406 | `931e9866b5376ab34d1fcd5bdd4d706bff51d26e8010f2a4e62b9f90b4a9dfe8` |
| `runs/model-player/t140-jev-v3-w90-r2/platformer/jev/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t140-jev-v3-w90-r2/platformer/jev/engine-game.stdout.txt` | 796 | `225b2854066b40b232873f63f31c7016d492d1d07da6878e3e4bb53d0c8d4f54` |
| `runs/model-player/t140-jev-v3-w90-r2/platformer/jev/filmstrip.png` | 39370 | `9f8dbc91980ffd8b5dd9aab8fdda3a7beb3b788e987fafe9058bdf0341c2d71a` |
| `runs/model-player/t140-jev-v3-w90-r2/platformer/jev/frames.json` | 193356 | `d658ec2237c881d59de40a07706652c9abb1c2e7d6d002e9eed4be45c2223eb1` |
| `runs/model-player/t140-jev-v3-w90-r2/platformer/jev/player.json` | 97480 | `b71731b0289f9cfcc62cca8cbc92b45efb437554cd889139a92e08c2ff36da24` |
| `runs/model-player/t140-jev-v3-w90-r2/platformer/jev/session.json` | 12040 | `2b03f654cd5001454aa8b5930e779c34861f45ba350c4b85a99c1d724530cee2` |
| `runs/model-player/t140-jev-v3-w90-r2/platformer/jev/steps.jsonl` | 55999 | `c410acfd36e5d0da42be66872056c4a59ccb8f0619fcd81dc71b2d33f9cd983f` |
| `calls/**`（465 个文件，8520189 B）| — | `121f09e62b27b0b8ac1df9d92d4235625c59416b2910de0f70420a97345add10` |
| `frames/**`（13 个文件，135653 B）| — | `30a3bf92b5f3cecbfb0030b9196b5fc496866898b0d16229ca51888f3ed28c63` |
| `states/**`（11 个文件，236414 B）| — | `09935bd825aa9607cf7e9fb8b9511c662cd5255c2a910086067775376d69bd36` |

## t140-jev-v3-w90-r2 / pong / jev

* 目录：`runs/model-player/t140-jev-v3-w90-r2/pong/jev`
* verdict：`PASS(baseline only)`（counts_as_pass=False，strict=FAIL，baseline=PASS，game_side=None）
* 档位+轮次：`PASS(baseline only) @w90 r2`（window=90，round=2，reporting=90，at_reporting_window=True，reporting_state=ok）
* 注入/接受后变化/rate：8 / 7 / 0.875
* 两窗对齐：6/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 2 frame(s))（matched 6/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game pong --backend jev --player model --variant V3 --image-form full --steps 12 --port 9984 --window-frames 90 --round 2 --change-margin strict --out-prefix t140-jev-v3-w90-r2`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t140-jev-v3-w90-r2/pong/jev/demo.png` | 91344 | `f7b94ba974f156ee11592cc7ce8d587cd4a4b4bf063b3fc9e2bf616fd28cd9ab` |
| `runs/model-player/t140-jev-v3-w90-r2/pong/jev/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t140-jev-v3-w90-r2/pong/jev/engine-game.stdout.txt` | 4063 | `67c860a9173d290f4ae6862bc7d07611b822cdb47636cc4e94d58028a6ceb862` |
| `runs/model-player/t140-jev-v3-w90-r2/pong/jev/filmstrip.png` | 60793 | `237ec81dc0dac9b06676a4a19472ae43e7ccbdd728d71e2ebe822c96a8e18c4d` |
| `runs/model-player/t140-jev-v3-w90-r2/pong/jev/frames.json` | 428820 | `acbff595d5205813f0f38539e026eecc0d6b8ddaffc5ffa46f1690540fbe2f57` |
| `runs/model-player/t140-jev-v3-w90-r2/pong/jev/player.json` | 211978 | `2ebe60713e9b30de086dbc7733826800a0289b834e91a8fd744b9c51dcc6f3de` |
| `runs/model-player/t140-jev-v3-w90-r2/pong/jev/session.json` | 12226 | `8c420607247a0853bd8c3ee47cb481391fee2e243b7fd624edb1995bb9385541` |
| `runs/model-player/t140-jev-v3-w90-r2/pong/jev/steps.jsonl` | 138347 | `4b40a5206a5183a514b151fa7e7be076ac245fdf430133b46c47c8e7a707279a` |
| `calls/**`（1337 个文件，3565386 B）| — | `42f748bf05409f216241b577811fcca2733e8155e610f09d37bb68afa98955ce` |
| `frames/**`（37 个文件，295168 B）| — | `39101329ed807ad911f74e197e989d0a6cebd66a1636e663ad13bec505653e0a` |
| `states/**`（27 个文件，65790 B）| — | `b255a69177dc6fb82657c33e0a42f36c28e662b386f7c8db0d0e86bdc69f8f11` |

## t140-jev-v3-w90-r2 / puzzlebobble / jev

* 目录：`runs/model-player/t140-jev-v3-w90-r2/puzzlebobble/jev`
* verdict：`INCONCLUSIVE`（counts_as_pass=False，strict=INCONCLUSIVE，baseline=INCONCLUSIVE，game_side=None）
* 档位+轮次：`INCONCLUSIVE @w90 r2`（window=90，round=2，reporting=90，at_reporting_window=True，reporting_state=ok）
* 注入/接受后变化/rate：2 / 2 / 1.0
* 两窗对齐：8/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 2 frame(s))（matched 8/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game puzzlebobble --backend jev --player model --variant V3 --image-form full --steps 12 --port 9984 --window-frames 90 --round 2 --change-margin strict --out-prefix t140-jev-v3-w90-r2`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t140-jev-v3-w90-r2/puzzlebobble/jev/demo.png` | 182429 | `0ed82a9e1353758e9d4091894919459e17b198e46aad2904eee1d68d331fbd56` |
| `runs/model-player/t140-jev-v3-w90-r2/puzzlebobble/jev/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t140-jev-v3-w90-r2/puzzlebobble/jev/engine-game.stdout.txt` | 739 | `92090585e8af16a8f2a5f786213b0f51dd67a85f58d50768fcfa3478c4229a71` |
| `runs/model-player/t140-jev-v3-w90-r2/puzzlebobble/jev/filmstrip.png` | 126534 | `dae2333b047066d6db07031c028718328c4524278fc9329b658804480a2ffe75` |
| `runs/model-player/t140-jev-v3-w90-r2/puzzlebobble/jev/frames.json` | 733425 | `28ebdf2d664cf453f2ed9dd894609413598052114f8f32b2f40a9614592bae38` |
| `runs/model-player/t140-jev-v3-w90-r2/puzzlebobble/jev/player.json` | 74468 | `3d0cb2b57c70925fde74f6e15dd2b7f6a8e6c25e2da75bdb6735b147fe1dc2b9` |
| `runs/model-player/t140-jev-v3-w90-r2/puzzlebobble/jev/session.json` | 12194 | `76b63a48b0cc2539ee8bf8870d51faa101d67b08e43b11142ef03b8fff2831c1` |
| `runs/model-player/t140-jev-v3-w90-r2/puzzlebobble/jev/steps.jsonl` | 139710 | `9a23ce6e4e913a5c58309ba249e3590a61be0636a4b02481bd4c49e590b94776` |
| `calls/**`（1332 个文件，23452792 B）| — | `bee92cc6c58803c8caae626ed2feac0fa9536302978dbb2b2eb6b7cdd19616d8` |
| `frames/**`（37 个文件，523236 B）| — | `93ea0aeebcc1856e007a9202fe28805bb1a5bee9f8a33e535f7a53d5c668096b` |
| `states/**`（27 个文件，539272 B）| — | `e9f1168559abc30d48ddc32065e94e6ea3c751cff0cdfe5463c283f0b4ec5765` |

## t140-jev-v3-w90-r2 / rtype / jev

* 目录：`runs/model-player/t140-jev-v3-w90-r2/rtype/jev`
* verdict：`INCONCLUSIVE`（counts_as_pass=False，strict=INCONCLUSIVE，baseline=INCONCLUSIVE，game_side=None）
* 档位+轮次：`INCONCLUSIVE @w90 r2`（window=90，round=2，reporting=90，at_reporting_window=True，reporting_state=ok）
* 注入/接受后变化/rate：0 / 0 / None
* 两窗对齐：8/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 1 frame(s))（matched 8/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game rtype --backend jev --player model --variant V3 --image-form full --steps 12 --port 9984 --window-frames 90 --round 2 --change-margin strict --out-prefix t140-jev-v3-w90-r2`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t140-jev-v3-w90-r2/rtype/jev/demo.png` | 153493 | `9a5a613351dd968364f66c5c2abe33ce813267a46cfcfde65b1fd1461b674128` |
| `runs/model-player/t140-jev-v3-w90-r2/rtype/jev/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t140-jev-v3-w90-r2/rtype/jev/engine-game.stdout.txt` | 743 | `7c9ec86977edd71d48527f1f467745b3c09720ddee9213b85a548a9c1911471a` |
| `runs/model-player/t140-jev-v3-w90-r2/rtype/jev/filmstrip.png` | 104310 | `0915488e56c95af4c112604207526aa8c2ac1376efd28c0106c98c907b1f0587` |
| `runs/model-player/t140-jev-v3-w90-r2/rtype/jev/frames.json` | 631993 | `5e4aa51d8dd472e5fc7672e2151032634493af0ea5e8a274c2b08c5d6718c086` |
| `runs/model-player/t140-jev-v3-w90-r2/rtype/jev/player.json` | 278367 | `4444146a0a6410d964d72fd47c39908f3d63d3037b4b72c3e6fb9a5e6e659d2c` |
| `runs/model-player/t140-jev-v3-w90-r2/rtype/jev/session.json` | 12152 | `6747baf819ddca0309beef8bc0c509e615ac9704099b619940872911bb4e2e96` |
| `runs/model-player/t140-jev-v3-w90-r2/rtype/jev/steps.jsonl` | 126317 | `0acd2e0f30ef3ecbe9812075792133ea959bd48acfb84f587c736c2761005811` |
| `calls/**`（1349 个文件，22052418 B）| — | `8a61f49f7537cad55443b8c107b8cf7bfe00aa9e3262366ff21e91e3bd9529b7` |
| `frames/**`（37 个文件，447515 B）| — | `dbf98b028b732c2f14c26ab361949dcb1af91fcfa84f103cf9d46700cca531ac` |
| `states/**`（27 个文件，499035 B）| — | `1968fb435827e989aba20935a463737750a33b4918af4c40ae75ac6ae3343c03` |

## t140-jev-v3-w90-r2 / snake / jev

* 目录：`runs/model-player/t140-jev-v3-w90-r2/snake/jev`
* verdict：`INCONCLUSIVE`（counts_as_pass=False，strict=INCONCLUSIVE，baseline=INCONCLUSIVE，game_side=None）
* 档位+轮次：`INCONCLUSIVE @w90 r2`（window=90，round=2，reporting=90，at_reporting_window=True，reporting_state=ok）
* 注入/接受后变化/rate：10 / 10 / 1.0
* 两窗对齐：3/10 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 3 frame(s))（matched 3/10，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game snake --backend jev --player model --variant V3 --image-form full --steps 12 --port 9984 --window-frames 90 --round 2 --change-margin strict --out-prefix t140-jev-v3-w90-r2`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t140-jev-v3-w90-r2/snake/jev/demo.png` | 68061 | `4b28b901c7906ec67f67749071489abee84257dfd1657a6358c255ef5355cab4` |
| `runs/model-player/t140-jev-v3-w90-r2/snake/jev/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t140-jev-v3-w90-r2/snake/jev/engine-game.stdout.txt` | 8553 | `18c5da07c9b2eb0f78db0acf62028f0b5e953a21d05f99f4aa7f124e2c65145c` |
| `runs/model-player/t140-jev-v3-w90-r2/snake/jev/filmstrip.png` | 39350 | `41c2cd88e488e6e81e11ef226c9196883ecb52486fe08e866a11fbef5355615a` |
| `runs/model-player/t140-jev-v3-w90-r2/snake/jev/frames.json` | 156712 | `3d0a27a338e9c9a162b28525c9a5c7f8d1693509dbee54f74c4cc9bacdd6f49c` |
| `runs/model-player/t140-jev-v3-w90-r2/snake/jev/player.json` | 121211 | `51995031e696b9870b6fcf1a02b51e35b186fc9156fd05e9b5e4a3ed6150e226` |
| `runs/model-player/t140-jev-v3-w90-r2/snake/jev/session.json` | 12781 | `6212c7be0d5d5b34c9095aa617ebfdc9edaed0ef184f8d91cfaf925ecb344d13` |
| `runs/model-player/t140-jev-v3-w90-r2/snake/jev/steps.jsonl` | 137292 | `8a6fe684ca81dc7388cfcf0498bb48d930aa0910fec1d635530b7aa332e36514` |
| `calls/**`（793 个文件，6036852 B）| — | `819d7cbcad8daaccc076c498c64c1ec1f4ae037dc7bbc11735736e290bbe8c82` |
| `frames/**`（31 个文件，95526 B）| — | `57aa802c7a059ebf525d6bfecc622a4d9a71acbde7ce92ff3dbc01b6f1c5618a` |
| `states/**`（23 个文件，201744 B）| — | `446f7f1514d0821bb16106aeabc0b86fc328bcd00afd4ca312a444ce3d5965b0` |

## t140-jev-v3-w90-r2 / sokoban / jev

* 目录：`runs/model-player/t140-jev-v3-w90-r2/sokoban/jev`
* verdict：`INCONCLUSIVE`（counts_as_pass=False，strict=INCONCLUSIVE，baseline=INCONCLUSIVE，game_side=None）
* 档位+轮次：`INCONCLUSIVE @w90 r2`（window=90，round=2，reporting=90，at_reporting_window=True，reporting_state=ok）
* 注入/接受后变化/rate：12 / 1 / 0.0833
* 两窗对齐：9/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 1 frame(s))（matched 9/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game sokoban --backend jev --player model --variant V3 --image-form full --steps 12 --port 9984 --window-frames 90 --round 2 --change-margin strict --out-prefix t140-jev-v3-w90-r2`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t140-jev-v3-w90-r2/sokoban/jev/demo.png` | 146601 | `8b52af723e34c9bad1129f8f98af1a1f5d096cb712f19ea301366dbf5e6e3111` |
| `runs/model-player/t140-jev-v3-w90-r2/sokoban/jev/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t140-jev-v3-w90-r2/sokoban/jev/engine-game.stdout.txt` | 745 | `21cfe1735b5328719111f61c85f2574f33da4647fa692135768b2073a4c487b9` |
| `runs/model-player/t140-jev-v3-w90-r2/sokoban/jev/filmstrip.png` | 101789 | `c36aa1e17cee52f19dfcb7cb9aaf4bb2428f85f2ec6d32898a95290f67c394f5` |
| `runs/model-player/t140-jev-v3-w90-r2/sokoban/jev/frames.json` | 586508 | `00e06388d811903b4be2e9c76122af7a80fb805b3edcf5bc9bac46e6b7560d8a` |
| `runs/model-player/t140-jev-v3-w90-r2/sokoban/jev/player.json` | 263341 | `96e4f25696514b2b78c1e97e50f1948efd2e92d68510169ad36b7a555b0f58e3` |
| `runs/model-player/t140-jev-v3-w90-r2/sokoban/jev/session.json` | 13508 | `c546c6d32fcf54993f8e77844653bd339082ba68415bf80e98e81c4158717117` |
| `runs/model-player/t140-jev-v3-w90-r2/sokoban/jev/steps.jsonl` | 143289 | `e98f328ec6cb87669fd3721615a2bd288d53048a222d3b4ce800e4f74824e033` |
| `calls/**`（1407 个文件，17286723 B）| — | `be05f0778aa7ee254177fdb85220e73ad9e599b21b6e778972dd7a19597cbb2a` |
| `frames/**`（37 个文件，413183 B）| — | `6e02ebd0673e5e8d190c3c30fda80a91a5034052127c12c811fd329398449b30` |
| `states/**`（27 个文件，374555 B）| — | `15f9eedfaf29c98c5db9c67d88cb1c04b20ccb8c77448521b30db85c4eb03e9d` |

## t140-jev-v3-w90-r2 / spaceinvaders / jev

* 目录：`runs/model-player/t140-jev-v3-w90-r2/spaceinvaders/jev`
* verdict：`INCONCLUSIVE`（counts_as_pass=False，strict=INCONCLUSIVE，baseline=INCONCLUSIVE，game_side=None）
* 档位+轮次：`INCONCLUSIVE @w90 r2`（window=90，round=2，reporting=90，at_reporting_window=True，reporting_state=ok）
* 注入/接受后变化/rate：12 / 6 / 0.5
* 两窗对齐：7/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 2 frame(s))（matched 7/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game spaceinvaders --backend jev --player model --variant V3 --image-form full --steps 12 --port 9984 --window-frames 90 --round 2 --change-margin strict --out-prefix t140-jev-v3-w90-r2`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t140-jev-v3-w90-r2/spaceinvaders/jev/demo.png` | 116772 | `242f9482441ba79ee114a7ce51109da234b06871a408c44b0b60b18083934b84` |
| `runs/model-player/t140-jev-v3-w90-r2/spaceinvaders/jev/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t140-jev-v3-w90-r2/spaceinvaders/jev/engine-game.stdout.txt` | 754 | `70c0af70bf61006e66b0792e9b4b98ec0dfc51946e077be9f8c97f8a61a0d0af` |
| `runs/model-player/t140-jev-v3-w90-r2/spaceinvaders/jev/filmstrip.png` | 92625 | `0f43368d81bf79943bb861a78971ce428e7404383a49fce7939540cef8742b6a` |
| `runs/model-player/t140-jev-v3-w90-r2/spaceinvaders/jev/frames.json` | 517062 | `162eea417f9e6bba3c9a74641ccabe7493f5865412374d17d5e3cb843720a592` |
| `runs/model-player/t140-jev-v3-w90-r2/spaceinvaders/jev/player.json` | 235203 | `cb2d70db999b415be152b357c58dbece754b5268659ccefc49a125cc644f2036` |
| `runs/model-player/t140-jev-v3-w90-r2/spaceinvaders/jev/session.json` | 12094 | `84ffe1953cb6b2349fd88c28e48a63eaaee0ceaf4284d127ad874b7de62c51ee` |
| `runs/model-player/t140-jev-v3-w90-r2/spaceinvaders/jev/steps.jsonl` | 153914 | `078d65e39d67d12d6dc3681611963df37579e12d472286e760c7fa52ed38d841` |
| `calls/**`（1423 个文件，11332463 B）| — | `6100fcb4c07f0ebb4e9ab64c474f3dcb2678ad90402e87a552405072556a578f` |
| `frames/**`（37 个文件，360918 B）| — | `f7581339de80c6801205b2705fa92f803844da15d4622f4da32cb6b3ba4e106b` |
| `states/**`（27 个文件，240335 B）| — | `ef8713f16f493aa80d88eb8a38d537f8bde1e68943046c87f7b77f11cdbb108b` |

## t140-jev-v3-w90-r2 / tetris / jev

* 目录：`runs/model-player/t140-jev-v3-w90-r2/tetris/jev`
* verdict：`PASS`（counts_as_pass=True，strict=PASS，baseline=PASS，game_side=None）
* 档位+轮次：`PASS @w90 r2`（window=90，round=2，reporting=90，at_reporting_window=True，reporting_state=ok）
* 注入/接受后变化/rate：8 / 8 / 1.0
* 两窗对齐：3/8 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 2 frame(s))（matched 3/8，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game tetris --backend jev --player model --variant V3 --image-form full --steps 12 --port 9984 --window-frames 90 --round 2 --change-margin strict --out-prefix t140-jev-v3-w90-r2`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t140-jev-v3-w90-r2/tetris/jev/demo.png` | 74303 | `d3ce04a38368e33a6fb7647d514b5fe69e8cf8cd2623b33d271cf8b809ce57b0` |
| `runs/model-player/t140-jev-v3-w90-r2/tetris/jev/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t140-jev-v3-w90-r2/tetris/jev/engine-game.stdout.txt` | 10079 | `5e99641b630afe005f1ec9cf914434ab7151299c97da27cb87892f8db9de9740` |
| `runs/model-player/t140-jev-v3-w90-r2/tetris/jev/filmstrip.png` | 43424 | `3066725330309646e4c60639fa87a0b2e4b5c9ccf66f1e0f99709a8017fe3b7b` |
| `runs/model-player/t140-jev-v3-w90-r2/tetris/jev/frames.json` | 199719 | `a1424640faa8208f9ad718f85724e6a0cfa3919459bffbc6bfe7a1ae77e5a7cf` |
| `runs/model-player/t140-jev-v3-w90-r2/tetris/jev/player.json` | 118283 | `d80d800f35fa08ce05c11bcb0038078e2198e70cd64e1aa1f2a0cc52479d71c5` |
| `runs/model-player/t140-jev-v3-w90-r2/tetris/jev/session.json` | 12003 | `1faa9ca7144572f5df93642c991aa1fb3911c66965afcf9d6bc73ddf51b0d118` |
| `runs/model-player/t140-jev-v3-w90-r2/tetris/jev/steps.jsonl` | 98368 | `53b21c29f3cf46872ba7a1bea47eddbf11e8f60ad9d6689a21e892ba833c2885` |
| `calls/**`（977 个文件，1793844 B）| — | `5dcd8ead1f3e4ab29ce12bf38a485f112554587792955b50badfaa2244a4eb7d` |
| `frames/**`（25 个文件，131740 B）| — | `5671719bba14d36f8cb602d79bd9181755b93011268c9a3d3a590d41889e21ae` |
| `states/**`（19 个文件，30294 B）| — | `6aca61e336f427560ecd995237ebb8ae7c089d505eb5cb4c8ef68c51138d2ce8` |

## t140-jev-v3-w90-r2 / towerdefense / jev

* 目录：`runs/model-player/t140-jev-v3-w90-r2/towerdefense/jev`
* verdict：`INCONCLUSIVE`（counts_as_pass=False，strict=INCONCLUSIVE，baseline=INCONCLUSIVE，game_side=None）
* 档位+轮次：`INCONCLUSIVE @w90 r2`（window=90，round=2，reporting=90，at_reporting_window=True，reporting_state=ok）
* 注入/接受后变化/rate：8 / 8 / 1.0
* 两窗对齐：3/8 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 2 frame(s))（matched 3/8，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game towerdefense --backend jev --player model --variant V3 --image-form full --steps 12 --port 9984 --window-frames 90 --round 2 --change-margin strict --out-prefix t140-jev-v3-w90-r2`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t140-jev-v3-w90-r2/towerdefense/jev/demo.png` | 140492 | `0d40b174990e6ada45fa1a1a92e855a5d97a1f71b49853db67ee5480878b2f3b` |
| `runs/model-player/t140-jev-v3-w90-r2/towerdefense/jev/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t140-jev-v3-w90-r2/towerdefense/jev/engine-game.stdout.txt` | 753 | `0d8b427d4d1bcc18308f68cafd3434025b7048db6951987d67ca072c666ca6ce` |
| `runs/model-player/t140-jev-v3-w90-r2/towerdefense/jev/filmstrip.png` | 80198 | `33ff043a685003fcbd16351a3724e4323ef96e620ceaad88eacee6ce6e10fa06` |
| `runs/model-player/t140-jev-v3-w90-r2/towerdefense/jev/frames.json` | 442024 | `ea167cf73ef499d986f7ef13597e7c590cfc6775502b21836bc89ce83b274558` |
| `runs/model-player/t140-jev-v3-w90-r2/towerdefense/jev/player.json` | 200562 | `bb6c999c42e935807704117bb8e3ea1271db787f29bb27226aa1cba2d66dbe3b` |
| `runs/model-player/t140-jev-v3-w90-r2/towerdefense/jev/session.json` | 13742 | `94234a0783137a6bf6bcceb9f22ede3dff7196409311d88037ec979bc940a2be` |
| `runs/model-player/t140-jev-v3-w90-r2/towerdefense/jev/steps.jsonl` | 100286 | `dd4cd8f4ac973e450175face923021f68b1a868b8c04b7b99acf184ec6adfa4c` |
| `calls/**`（899 个文件，18035039 B）| — | `6ab26f18a5d53dd20be75cf7c376fab3f50d5312932683fcbb82e5987a0348de` |
| `frames/**`（25 个文件，313383 B）| — | `515da4ca41d666d562dec96cac19bd34871ec0020c65d772d69476280db3acf4` |
| `states/**`（19 个文件，451883 B）| — | `8c476fa41da6cdddd50dba90f31bb36d491aa3b23021772e307edaf82b26152a` |

## t140-playjev-v3-w90-r1 / asteroids / playjev

* 目录：`runs/model-player/t140-playjev-v3-w90-r1/asteroids/playjev`
* verdict：`PASS`（counts_as_pass=True，strict=PASS，baseline=PASS，game_side=None）
* 档位+轮次：`PASS @w90 r1`（window=90，round=1，reporting=90，at_reporting_window=True，reporting_state=ok）
* 注入/接受后变化/rate：9 / 9 / 1.0
* 两窗对齐：4/9 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 2 frame(s))（matched 4/9，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game asteroids --backend playjev --player model --variant V3 --image-form full --steps 12 --port 9985 --window-frames 90 --round 1 --change-margin strict --out-prefix t140-playjev-v3-w90-r1`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t140-playjev-v3-w90-r1/asteroids/playjev/demo.png` | 110221 | `431df7c0a4e5485a98e3b1ee1a69938675315e494259423d724472a8ad15bac5` |
| `runs/model-player/t140-playjev-v3-w90-r1/asteroids/playjev/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t140-playjev-v3-w90-r1/asteroids/playjev/engine-game.stdout.txt` | 741 | `afe38f31986e6d9273761209a968784123241a483160c83d8f98c4ac59d5471c` |
| `runs/model-player/t140-playjev-v3-w90-r1/asteroids/playjev/filmstrip.png` | 56220 | `7b8ec987872f262b90955215262494e4e667dce2bf470832cce23b3370d8b54b` |
| `runs/model-player/t140-playjev-v3-w90-r1/asteroids/playjev/frames.json` | 418279 | `0f270e3a5eee976636a23bebdb648476060e7e328d6aa2ada7ca3fc034817907` |
| `runs/model-player/t140-playjev-v3-w90-r1/asteroids/playjev/player.json` | 265722 | `80ca173c26f9a365190b7db2ba2aa5a9dd556a0669750e2cf746b0988ecfe2bc` |
| `runs/model-player/t140-playjev-v3-w90-r1/asteroids/playjev/session.json` | 12058 | `849408a519a22e7af19b0bb039d147c5d3903342894fdccc5436f4101e9bff90` |
| `runs/model-player/t140-playjev-v3-w90-r1/asteroids/playjev/steps.jsonl` | 112336 | `3fd306640eae8078dea89e28c120198fd3957ba18670bed855ba9fc174c46a61` |
| `calls/**`（1095 个文件，3533211 B）| — | `328be3d46e55f3246f6d1aa04a2d85e6decabd534c3fc5730e60f6c14c4441c7` |
| `frames/**`（28 个文件，293335 B）| — | `073171ed694c30ca3c41b130a73cb81f000c79870683a0fe361ba588c2130bda` |
| `states/**`（21 个文件，63193 B）| — | `7b4e7e89a3f65252488ec327ee8cfb25a28963a7a0b6f66eee17cb2fc65d662d` |

## t140-playjev-v3-w90-r1 / game2048 / playjev

* 目录：`runs/model-player/t140-playjev-v3-w90-r1/game2048/playjev`
* verdict：`PASS`（counts_as_pass=True，strict=PASS，baseline=PASS，game_side=None）
* 档位+轮次：`PASS @w90 r1`（window=90，round=1，reporting=90，at_reporting_window=True，reporting_state=ok）
* 注入/接受后变化/rate：12 / 5 / 1.0
* 两窗对齐：10/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 2 frame(s))（matched 10/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game game2048 --backend playjev --player model --variant V3 --image-form full --steps 12 --port 9985 --window-frames 90 --round 1 --change-margin strict --out-prefix t140-playjev-v3-w90-r1`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t140-playjev-v3-w90-r1/game2048/playjev/demo.png` | 144075 | `1a24abe897b338361630759605b316c98ff0748f408aff732418da6b93e3164e` |
| `runs/model-player/t140-playjev-v3-w90-r1/game2048/playjev/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t140-playjev-v3-w90-r1/game2048/playjev/engine-game.stdout.txt` | 781 | `bddc13036f3d93bd4544d6921b24d00027cbc63f56aa22514eaf2328553936bb` |
| `runs/model-player/t140-playjev-v3-w90-r1/game2048/playjev/filmstrip.png` | 89905 | `da36142c4a3e30bc4d04393c73e8df29b950a1c4bced1822a97bc0d0c5be9ec6` |
| `runs/model-player/t140-playjev-v3-w90-r1/game2048/playjev/frames.json` | 623960 | `4e358eb87731e9fe383d773a2b72e533715e19d8282f15f1ef5c84548fed1d1c` |
| `runs/model-player/t140-playjev-v3-w90-r1/game2048/playjev/player.json` | 378558 | `6a10fe123fa6a54447ecd1c39527faf76e639618651412733c265f2fa70d3b67` |
| `runs/model-player/t140-playjev-v3-w90-r1/game2048/playjev/session.json` | 11911 | `abaabf6122dc78ffcf576cce3ce51e2c5e4b768bffa39aeb467b10a8c46add16` |
| `runs/model-player/t140-playjev-v3-w90-r1/game2048/playjev/steps.jsonl` | 165596 | `4c4ad26e369a1b4aa4a17efeaa4306d8535d4253e2f95507caa0755e63b4fff3` |
| `calls/**`（1438 个文件，10082343 B）| — | `0f2a1cc29a4354b74126d0d9924638c9b49244ec2bfc4215f3dc7f4e2b1de8da` |
| `frames/**`（37 个文件，440996 B）| — | `ccb936ca1e3afc2c6b35e4831b1f5b84009a9fc6fbd077c7b09e582975b089c7` |
| `states/**`（27 个文件，202635 B）| — | `8737e3ec3d51d3d8ff3bd8a945705495d177a59e922003dfc99a5b5429cf1938` |

## t140-playjev-v3-w90-r1 / match3 / playjev

* 目录：`runs/model-player/t140-playjev-v3-w90-r1/match3/playjev`
* verdict：`INCONCLUSIVE`（counts_as_pass=False，strict=INCONCLUSIVE，baseline=INCONCLUSIVE，game_side=None）
* 档位+轮次：`INCONCLUSIVE @w90 r1`（window=90，round=1，reporting=90，at_reporting_window=True，reporting_state=ok）
* 注入/接受后变化/rate：12 / 4 / 0.3333
* 两窗对齐：6/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 2 frame(s))（matched 6/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game match3 --backend playjev --player model --variant V3 --image-form full --steps 12 --port 9985 --window-frames 90 --round 1 --change-margin strict --out-prefix t140-playjev-v3-w90-r1`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t140-playjev-v3-w90-r1/match3/playjev/demo.png` | 204278 | `95625525af761a107d95433b836bcb1e2b16821335afca2910fb6fb545460035` |
| `runs/model-player/t140-playjev-v3-w90-r1/match3/playjev/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t140-playjev-v3-w90-r1/match3/playjev/engine-game.stdout.txt` | 769 | `bf95ba69e6a267abbadbd2e86daddffeec74f1a9fb3e7b6caa26b881a59c42e4` |
| `runs/model-player/t140-playjev-v3-w90-r1/match3/playjev/filmstrip.png` | 143258 | `60197946725b7dd7365ac0f4165dff19939e8f4f9ff9c36a47ab14cac5a09da0` |
| `runs/model-player/t140-playjev-v3-w90-r1/match3/playjev/frames.json` | 609194 | `ab6aa77164934bfaa18ecb70e4c145521c973d5daf785525145e810f33429651` |
| `runs/model-player/t140-playjev-v3-w90-r1/match3/playjev/player.json` | 373992 | `938b404e0525323b2a1aca0b7e7b18ea90939b841c6dcf37309af012481f8857` |
| `runs/model-player/t140-playjev-v3-w90-r1/match3/playjev/session.json` | 13773 | `6d714f284a57205f52c03be77ec8dbcc21dfb2c5faabee78ca28cadfbe9006c7` |
| `runs/model-player/t140-playjev-v3-w90-r1/match3/playjev/steps.jsonl` | 149372 | `c592fcfc4461be66b7d1dd43f93dc86882e9ff24c43ded2b44e05187fd49c29d` |
| `calls/**`（1425 个文件，15222725 B）| — | `5d6da833fd17455b5a07c00bea7fca985e8d7d4404b5b9a1db620276301a4da3` |
| `frames/**`（37 个文件，429940 B）| — | `0a391306bf622230abd3e392bc86a6008341aacfe0fc60c0485cf2e3dd2d28d3` |
| `states/**`（27 个文件，329457 B）| — | `d3ea3108e99de420c09846e288f823a0e3f2aea1e354b2213d8cfda9cb59a9d8` |

## t140-playjev-v3-w90-r1 / minesweeper / playjev

* 目录：`runs/model-player/t140-playjev-v3-w90-r1/minesweeper/playjev`
* verdict：`INCONCLUSIVE`（counts_as_pass=False，strict=INCONCLUSIVE，baseline=INCONCLUSIVE，game_side=None）
* 档位+轮次：`INCONCLUSIVE @w90 r1`（window=90，round=1，reporting=90，at_reporting_window=True，reporting_state=ok）
* 注入/接受后变化/rate：12 / 4 / 0.3333
* 两窗对齐：9/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 2 frame(s))（matched 9/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game minesweeper --backend playjev --player model --variant V3 --image-form full --steps 12 --port 9985 --window-frames 90 --round 1 --change-margin strict --out-prefix t140-playjev-v3-w90-r1`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t140-playjev-v3-w90-r1/minesweeper/playjev/demo.png` | 153153 | `c3543f093cbdd76035dbb653d428898bee908e910f01b959225577530ede764d` |
| `runs/model-player/t140-playjev-v3-w90-r1/minesweeper/playjev/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t140-playjev-v3-w90-r1/minesweeper/playjev/engine-game.stdout.txt` | 745 | `17aef0822fcb5dd26e2f405626483826036dbbd56af89af68c47c53edc19acac` |
| `runs/model-player/t140-playjev-v3-w90-r1/minesweeper/playjev/filmstrip.png` | 128011 | `913317c0ada268725f83789a73532b87ed3e9431716b7d1ebef922c3d76b38f4` |
| `runs/model-player/t140-playjev-v3-w90-r1/minesweeper/playjev/frames.json` | 621930 | `968b3702c0cbf7baafb551d45664afc08eb6d0b8ac7636e680133da0b83d3614` |
| `runs/model-player/t140-playjev-v3-w90-r1/minesweeper/playjev/player.json` | 388227 | `c24644b358b9c2d646b44058c442f43676e220d7bd467413b631882d9f20ae5f` |
| `runs/model-player/t140-playjev-v3-w90-r1/minesweeper/playjev/session.json` | 13890 | `ba2b3a7ef322ca7f543588cd6498684cc8376a443b065115296910628d7d654b` |
| `runs/model-player/t140-playjev-v3-w90-r1/minesweeper/playjev/steps.jsonl` | 152154 | `b60cea3c74fdee4fb71e661a14627a8c7aa35a347c73a0480db4e3b588bab27d` |
| `calls/**`（1346 个文件，33374946 B）| — | `e6588152e314e33219bd5063e09df73e2ea357fec541e3d0974690dfcb1aa696` |
| `frames/**`（37 个文件，439449 B）| — | `80c50f6327cbca8868f8acd7336b217629babfedaa40ff4214e8854563cf067d` |
| `states/**`（27 个文件，785161 B）| — | `b9be42810debdd29ac085a69733df160c24c73c313065effb334b22dcdff8816` |

## t140-playjev-v3-w90-r1 / pacman / playjev

* 目录：`runs/model-player/t140-playjev-v3-w90-r1/pacman/playjev`
* verdict：`FAIL`（counts_as_pass=False，strict=FAIL，baseline=FAIL，game_side=None）
* 档位+轮次：`FAIL @w90 r1`（window=90，round=1，reporting=90，at_reporting_window=True，reporting_state=ok）
* 注入/接受后变化/rate：12 / 0 / None
* 两窗对齐：5/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 2 frame(s))（matched 5/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game pacman --backend playjev --player model --variant V3 --image-form full --steps 12 --port 9985 --window-frames 90 --round 1 --change-margin strict --out-prefix t140-playjev-v3-w90-r1`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t140-playjev-v3-w90-r1/pacman/playjev/demo.png` | 153644 | `30e498fbafb8fa65aa3deeccde163e4d954b4111329bd756e3ed52b12f927602` |
| `runs/model-player/t140-playjev-v3-w90-r1/pacman/playjev/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t140-playjev-v3-w90-r1/pacman/playjev/engine-game.stdout.txt` | 733 | `08cf100e5e93ecae4fa5fc3944b9a10fb63acba8b21e10cc6fbccfb18b123d2a` |
| `runs/model-player/t140-playjev-v3-w90-r1/pacman/playjev/filmstrip.png` | 141068 | `01afb6f0313deba66d0375f719205d0ce8442b51eb6a859eade89cd71ed28833` |
| `runs/model-player/t140-playjev-v3-w90-r1/pacman/playjev/frames.json` | 592176 | `1b76ce77eb0a95a11b5144a731765ff7487c14d0b8b69e3c0ae985a8df60f7ef` |
| `runs/model-player/t140-playjev-v3-w90-r1/pacman/playjev/player.json` | 369178 | `76b91865bfeaea8264055f4635d1e2100dce1fff94817c34b3269f4cc9fb2067` |
| `runs/model-player/t140-playjev-v3-w90-r1/pacman/playjev/session.json` | 13338 | `91360e77193f61cf320f702b0c3806d46fcd3e69d346ee5199cb2d7914481487` |
| `runs/model-player/t140-playjev-v3-w90-r1/pacman/playjev/steps.jsonl` | 155006 | `662e427dc05061152afcb53275ad3aa4c82addea70d8969892117f0872b1de60` |
| `calls/**`（1333 个文件，48325465 B）| — | `f58c0973692da21e2b8b6a948be91f5d5b349234f1114fe1aacadfd0020adcbd` |
| `frames/**`（37 个文件，417286 B）| — | `86a4c2b49f099c7e8cac5885f6db27894f2ba0f57cf199c725c5912312e23d04` |
| `states/**`（27 个文件，1185215 B）| — | `e4b51ff8d1123d2fb0349dabe58dfe1732fba9de72cd02953362fe9055ca80ca` |

## t140-playjev-v3-w90-r1 / pong / playjev

* 目录：`runs/model-player/t140-playjev-v3-w90-r1/pong/playjev`
* verdict：`INCONCLUSIVE`（counts_as_pass=False，strict=INCONCLUSIVE，baseline=INCONCLUSIVE，game_side=None）
* 档位+轮次：`INCONCLUSIVE @w90 r1`（window=90，round=1，reporting=90，at_reporting_window=True，reporting_state=ok）
* 注入/接受后变化/rate：12 / 1 / 0.0833
* 两窗对齐：9/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 2 frame(s))（matched 9/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game pong --backend playjev --player model --variant V3 --image-form full --steps 12 --port 9985 --window-frames 90 --round 1 --change-margin strict --out-prefix t140-playjev-v3-w90-r1`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t140-playjev-v3-w90-r1/pong/playjev/demo.png` | 74650 | `b02cbc9cd141647175612ef3bf2cebde0dac141eb01ad63f3a49d3f40f9555c2` |
| `runs/model-player/t140-playjev-v3-w90-r1/pong/playjev/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t140-playjev-v3-w90-r1/pong/playjev/engine-game.stdout.txt` | 6417 | `275a1234a9502969e596eb2f0543b8ada16dbb793637ac3abc127cde331ba149` |
| `runs/model-player/t140-playjev-v3-w90-r1/pong/playjev/filmstrip.png` | 45424 | `ede963a4d87a83609e06bd273226910194c99e6442cb6044b62d72509615948f` |
| `runs/model-player/t140-playjev-v3-w90-r1/pong/playjev/frames.json` | 251300 | `57e3fc9a54721ec4d9a8be8ff3dfc6265d6d0f78941091d0336199c0e4f9eb1f` |
| `runs/model-player/t140-playjev-v3-w90-r1/pong/playjev/player.json` | 256258 | `4e9defe6fa236374f229a00bcc5f676f9d7c6fb938ea6aff5df91c7ee16a8d0a` |
| `runs/model-player/t140-playjev-v3-w90-r1/pong/playjev/session.json` | 12201 | `74932f5398fcfb687ff656f341326cab7f8a2173199e1e56b6f72a8f309e7397` |
| `runs/model-player/t140-playjev-v3-w90-r1/pong/playjev/steps.jsonl` | 146098 | `94f75998be74e5eff951c4948b6e5c119b3c166998fd2aedc0628cdebf089aef` |
| `calls/**`（1402 个文件，3448495 B）| — | `64a6c5f2dae7a5846a7f00bfa0ff7ab7f208aab3363770c8b17131ff59fd47fa` |
| `frames/**`（37 个文件，161791 B）| — | `856ca0d9b2ef2b197668b08f5da7c49418018f37a040f57236c4efb6adc451ab` |
| `states/**`（27 个文件，64456 B）| — | `43d8b6fb4991dc4da51006c810beaa8c21edc67dec95ff08978e12e8a175d0c3` |

## t140-playjev-v3-w90-r1 / rtype / playjev

* 目录：`runs/model-player/t140-playjev-v3-w90-r1/rtype/playjev`
* verdict：`PASS`（counts_as_pass=True，strict=PASS，baseline=PASS，game_side=None）
* 档位+轮次：`PASS @w90 r1`（window=90，round=1，reporting=90，at_reporting_window=True，reporting_state=ok）
* 注入/接受后变化/rate：12 / 5 / 1.0
* 两窗对齐：3/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 2 frame(s))（matched 3/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game rtype --backend playjev --player model --variant V3 --image-form full --steps 12 --port 9985 --window-frames 90 --round 1 --change-margin strict --out-prefix t140-playjev-v3-w90-r1`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t140-playjev-v3-w90-r1/rtype/playjev/demo.png` | 157956 | `0832f6502a8a3d806e76012dbcb8c349b3c08b2132dcb8043234d7dc96441d81` |
| `runs/model-player/t140-playjev-v3-w90-r1/rtype/playjev/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t140-playjev-v3-w90-r1/rtype/playjev/engine-game.stdout.txt` | 743 | `5dd367ab8423332671987c0653ca1b6ee5a2664ae90ea68b9b1250875d00991f` |
| `runs/model-player/t140-playjev-v3-w90-r1/rtype/playjev/filmstrip.png` | 104892 | `3f2e925906ae1e80a3b3175b3a02940fc1db6433950fe877a342e51e56bd5f16` |
| `runs/model-player/t140-playjev-v3-w90-r1/rtype/playjev/frames.json` | 631673 | `d04d0f09935f35bffa6c1dfbaa3eac0f1292223d42a0c3175987a96ef3861daf` |
| `runs/model-player/t140-playjev-v3-w90-r1/rtype/playjev/player.json` | 381670 | `3170e360f4c9b53cc9885e934cb887a73b6c76ac5962028830d52a5691679c1c` |
| `runs/model-player/t140-playjev-v3-w90-r1/rtype/playjev/session.json` | 12125 | `ebab230f43325f69513972eb708723fec0c89374d3de7dc531f2a9419c6ecac8` |
| `runs/model-player/t140-playjev-v3-w90-r1/rtype/playjev/steps.jsonl` | 157944 | `cc19f41a2a8b4871134f9e7700d59aabfd54956cd1e9c9704e34fa86cb410bc9` |
| `calls/**`（1382 个文件，21862999 B）| — | `86fc3ded5a241ab902de1a906286719f0fc0a45f993e468754096594e59aacd7` |
| `frames/**`（37 个文件，447001 B）| — | `81761241b5f87bee4348349c02c4fceb1c9a867b9663e0bd8a0be1605465a971` |
| `states/**`（27 个文件，499940 B）| — | `96de1ca70b9c694ff7f01b7d641dfa963e47ac3e7908e19edd99b6a092c2768c` |

## t140-playjev-v3-w90-r1 / snake / playjev

* 目录：`runs/model-player/t140-playjev-v3-w90-r1/snake/playjev`
* verdict：`INCONCLUSIVE`（counts_as_pass=False，strict=INCONCLUSIVE，baseline=INCONCLUSIVE，game_side=None）
* 档位+轮次：`INCONCLUSIVE @w90 r1`（window=90，round=1，reporting=90，at_reporting_window=True，reporting_state=ok）
* 注入/接受后变化/rate：12 / 4 / 0.3636
* 两窗对齐：4/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 3 frame(s))（matched 4/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game snake --backend playjev --player model --variant V3 --image-form full --steps 12 --port 9985 --window-frames 90 --round 1 --change-margin strict --out-prefix t140-playjev-v3-w90-r1`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t140-playjev-v3-w90-r1/snake/playjev/demo.png` | 65779 | `d66bcd31fd5c69fa4a557f2e2ab9b9bf6a4981f5d71b87bab6ac64b7b0c10943` |
| `runs/model-player/t140-playjev-v3-w90-r1/snake/playjev/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t140-playjev-v3-w90-r1/snake/playjev/engine-game.stdout.txt` | 14419 | `74de56dde76d0efff8d291fcc18929c3025f0942de7db0230c7852b62588980a` |
| `runs/model-player/t140-playjev-v3-w90-r1/snake/playjev/filmstrip.png` | 44049 | `d0afbc1715d8dd72d8f6e4d9f7ac6a664c6f2a225b261147df38e9e48c224982` |
| `runs/model-player/t140-playjev-v3-w90-r1/snake/playjev/frames.json` | 188044 | `6c90fc68c4c9703ac62f52576389f96f33f8aedfedd68221e6e519fb1f4ff1dd` |
| `runs/model-player/t140-playjev-v3-w90-r1/snake/playjev/player.json` | 239202 | `9779ab82de71d3a09fa1ddd2a1bc5c40edacc3b204ea6039053ee0b981c7e6c0` |
| `runs/model-player/t140-playjev-v3-w90-r1/snake/playjev/session.json` | 12757 | `0aa62a373ad89e68da79c44d2f1e55b2c0866a02f7738c4b46c377c22426de1d` |
| `runs/model-player/t140-playjev-v3-w90-r1/snake/playjev/steps.jsonl` | 154553 | `f049391fb9736d26828f866b734019fcde1b534842d1a7a06054669a2809d133` |
| `calls/**`（973 个文件，7438514 B）| — | `c58d199a6baeed4a4863a68a6719a6b0a6276d3d6c6da6eb27f5856396aa0656` |
| `frames/**`（37 个文件，114563 B）| — | `1c7e89be6f7aa5e85deb48dc3748f286efe71cba4d5d0233212565357e234e4d` |
| `states/**`（27 个文件，237352 B）| — | `5c9508c46aa1130d5792adde16476b5c8e280672b95de1e548d693e6faeb59e9` |

## t140-playjev-v3-w90-r1 / sokoban / playjev

* 目录：`runs/model-player/t140-playjev-v3-w90-r1/sokoban/playjev`
* verdict：`PASS`（counts_as_pass=True，strict=PASS，baseline=PASS，game_side=None）
* 档位+轮次：`PASS @w90 r1`（window=90，round=1，reporting=90，at_reporting_window=True，reporting_state=ok）
* 注入/接受后变化/rate：12 / 4 / 1.0
* 两窗对齐：5/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 1 frame(s))（matched 5/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game sokoban --backend playjev --player model --variant V3 --image-form full --steps 12 --port 9985 --window-frames 90 --round 1 --change-margin strict --out-prefix t140-playjev-v3-w90-r1`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t140-playjev-v3-w90-r1/sokoban/playjev/demo.png` | 151809 | `2ec30cc61afd21ff505f74c50caf290319ccb6e0c5843e8ca32a3b93b0087581` |
| `runs/model-player/t140-playjev-v3-w90-r1/sokoban/playjev/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t140-playjev-v3-w90-r1/sokoban/playjev/engine-game.stdout.txt` | 745 | `5365bdc63adf885fda5204ffb25e5fda6e31e9f5258e36ef3bb22c48a090530b` |
| `runs/model-player/t140-playjev-v3-w90-r1/sokoban/playjev/filmstrip.png` | 104413 | `e6061731adec0270553f753d1a907444f27f89c0b4b6f82a090db7d03dd1b6f1` |
| `runs/model-player/t140-playjev-v3-w90-r1/sokoban/playjev/frames.json` | 643277 | `e2f17619fe7fdec760077ae00f3960ba0f55d58c5a5fcf485e6d9d585a3278d5` |
| `runs/model-player/t140-playjev-v3-w90-r1/sokoban/playjev/player.json` | 382807 | `4d7867053bd37d1d5c86bf9db13e89b6bda5726e0503978fd0efc6390272ad24` |
| `runs/model-player/t140-playjev-v3-w90-r1/sokoban/playjev/session.json` | 13482 | `85187ddcf74aa8157376fa461e5626981f9789c04f3386aaaa2244bfb7e81c19` |
| `runs/model-player/t140-playjev-v3-w90-r1/sokoban/playjev/steps.jsonl` | 161147 | `2c77c519b84264e2b87751928fd57e7b2f2e33ecfada53932e5200da53eca83c` |
| `calls/**`（1392 个文件，17132201 B）| — | `d8675be07137494750f403e4fa81a120e6c7d197119a22c97a9de2d9956ac4d7` |
| `frames/**`（37 个文件，455461 B）| — | `e668c1d5587347738733254ab3e8b8de1cf30a18bf571e9f44ff009c5ab5b5e4` |
| `states/**`（27 个文件，374180 B）| — | `032d9c60d354ccdf14cb5e35ab5a98eeff0ff75a205dd24a8f1f2c368b31014a` |

## t140-playjev-v3-w90-r1 / tetris / playjev

* 目录：`runs/model-player/t140-playjev-v3-w90-r1/tetris/playjev`
* verdict：`INCONCLUSIVE`（counts_as_pass=False，strict=INCONCLUSIVE，baseline=INCONCLUSIVE，game_side=None）
* 档位+轮次：`INCONCLUSIVE @w90 r1`（window=90，round=1，reporting=90，at_reporting_window=True，reporting_state=ok）
* 注入/接受后变化/rate：0 / 0 / None
* 两窗对齐：8/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 1 frame(s))（matched 8/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game tetris --backend playjev --player model --variant V3 --image-form full --steps 12 --port 9985 --window-frames 90 --round 1 --change-margin strict --out-prefix t140-playjev-v3-w90-r1`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t140-playjev-v3-w90-r1/tetris/playjev/demo.png` | 68731 | `f37f24a934741f20032811cf6babce1df3e0a3d6665d4c42df3ae41405673890` |
| `runs/model-player/t140-playjev-v3-w90-r1/tetris/playjev/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t140-playjev-v3-w90-r1/tetris/playjev/engine-game.stdout.txt` | 11775 | `000c9c588b76e2ed4f1b1c12e8095fc484a1f16055b75b6cbf2e110d12773749` |
| `runs/model-player/t140-playjev-v3-w90-r1/tetris/playjev/filmstrip.png` | 42823 | `b83408cf62d21d61d36bf140a2ba57fe24fe49a2e8ee597709c2118850ff0565` |
| `runs/model-player/t140-playjev-v3-w90-r1/tetris/playjev/frames.json` | 286919 | `3335261a2bb519890f010ddbee5d37be6074442c4e83756bc208285c158f0e84` |
| `runs/model-player/t140-playjev-v3-w90-r1/tetris/playjev/player.json` | 261372 | `7dfdd1848da0669108f7cd669a0ed0e28cdd8f596b10c497d244a4dcaf2bfc82` |
| `runs/model-player/t140-playjev-v3-w90-r1/tetris/playjev/session.json` | 11978 | `a86610319364da5ed1a3522490107cca294c9c8bf983f18dd4e18e0875634e61` |
| `runs/model-player/t140-playjev-v3-w90-r1/tetris/playjev/steps.jsonl` | 129281 | `d2c10f409530e0f4da7a21d162e54575f7e294198378671d42343a5a328a0420` |
| `calls/**`（1426 个文件，2590655 B）| — | `b33c48d08ca5487ac431ce9e8df05b68716a4ca54eb2616c766f9451aa9496b1` |
| `frames/**`（37 个文件，188182 B）| — | `58e5791ff5642124842f3ac9af225d6ff7caeb1121e07869790e7c5e9947d361` |
| `states/**`（27 个文件，41776 B）| — | `25d498cbd0c7818859eeeb86ac7c78a3e9da15d0207bd3d665af5ffbb507b70b` |

## t140-playjev-v3-w90-r2 / asteroids / playjev

* 目录：`runs/model-player/t140-playjev-v3-w90-r2/asteroids/playjev`
* verdict：`PASS`（counts_as_pass=True，strict=PASS，baseline=PASS，game_side=None）
* 档位+轮次：`PASS @w90 r2`（window=90，round=2，reporting=90，at_reporting_window=True，reporting_state=ok）
* 注入/接受后变化/rate：8 / 8 / 1.0
* 两窗对齐：5/8 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 1 frame(s))（matched 5/8，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game asteroids --backend playjev --player model --variant V3 --image-form full --steps 12 --port 9986 --window-frames 90 --round 2 --change-margin strict --out-prefix t140-playjev-v3-w90-r2`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t140-playjev-v3-w90-r2/asteroids/playjev/demo.png` | 98691 | `996c9bc91f73164522f096d792060298e4d49c2963693c2f447c8952e3471ccb` |
| `runs/model-player/t140-playjev-v3-w90-r2/asteroids/playjev/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t140-playjev-v3-w90-r2/asteroids/playjev/engine-game.stdout.txt` | 741 | `f5d742dfaa955afa6beda5e48b7a439c348ce70d2a858d63b3ba5c3dc6f0745f` |
| `runs/model-player/t140-playjev-v3-w90-r2/asteroids/playjev/filmstrip.png` | 48274 | `5348716af3509c41f92503cc90720b68deee11e1a4fab41039794702b498761c` |
| `runs/model-player/t140-playjev-v3-w90-r2/asteroids/playjev/frames.json` | 380004 | `04f561903e95213b307701132549b5cff340160d2f92efb8fc07d445119772b8` |
| `runs/model-player/t140-playjev-v3-w90-r2/asteroids/playjev/player.json` | 240581 | `e12d964c7ae79f7f7dc400774d9b0c60f34d2e2593b6bdc7f26570c6aee93e38` |
| `runs/model-player/t140-playjev-v3-w90-r2/asteroids/playjev/session.json` | 12058 | `7ee9b76ff60faf9952e2ee0f9f6e2c5d2a9c3b51882e08dc52366ea89674ba01` |
| `runs/model-player/t140-playjev-v3-w90-r2/asteroids/playjev/steps.jsonl` | 100790 | `bd7829e5e6fa0ebe3cdfb75e05fe71d12e801e0e7500e9383a16e7f2ab2a6bd9` |
| `calls/**`（978 个文件，3247995 B）| — | `94ba2a47706b8fbb5d9bd91603f2e847017194673ec0da3c37f6027c85b930dd` |
| `frames/**`（25 个文件，266801 B）| — | `59776159c064be82b08b50d20414003f3812396d59a34a4a0685c4e3046417ec` |
| `states/**`（19 个文件，59002 B）| — | `642b9c639b194c6844f72ab40c47c6d1a0c572978150196f3d12951255ebd8e9` |

## t140-playjev-v3-w90-r2 / game2048 / playjev

* 目录：`runs/model-player/t140-playjev-v3-w90-r2/game2048/playjev`
* verdict：`PASS`（counts_as_pass=True，strict=PASS，baseline=PASS，game_side=None）
* 档位+轮次：`PASS @w90 r2`（window=90，round=2，reporting=90，at_reporting_window=True，reporting_state=ok）
* 注入/接受后变化/rate：12 / 5 / 1.0
* 两窗对齐：5/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 2 frame(s))（matched 5/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game game2048 --backend playjev --player model --variant V3 --image-form full --steps 12 --port 9986 --window-frames 90 --round 2 --change-margin strict --out-prefix t140-playjev-v3-w90-r2`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t140-playjev-v3-w90-r2/game2048/playjev/demo.png` | 144075 | `1a24abe897b338361630759605b316c98ff0748f408aff732418da6b93e3164e` |
| `runs/model-player/t140-playjev-v3-w90-r2/game2048/playjev/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t140-playjev-v3-w90-r2/game2048/playjev/engine-game.stdout.txt` | 781 | `714ec7e45e2af124c25c8595a455f1895443743d50ffaeb5842fb4285286041c` |
| `runs/model-player/t140-playjev-v3-w90-r2/game2048/playjev/filmstrip.png` | 89905 | `da36142c4a3e30bc4d04393c73e8df29b950a1c4bced1822a97bc0d0c5be9ec6` |
| `runs/model-player/t140-playjev-v3-w90-r2/game2048/playjev/frames.json` | 623959 | `4ff28c97de7a9e4889a7feea33a33e2fb450799f3ddd36b62ea167a952be57f4` |
| `runs/model-player/t140-playjev-v3-w90-r2/game2048/playjev/player.json` | 378566 | `75ae074c667f976068fbf734faafd11da72f670a5145eee2c008731fcd04042e` |
| `runs/model-player/t140-playjev-v3-w90-r2/game2048/playjev/session.json` | 11914 | `56b0a1d798000072e554ea5e089fa531cd7cfe8c4cb69e6de37e5dc93a0451a3` |
| `runs/model-player/t140-playjev-v3-w90-r2/game2048/playjev/steps.jsonl` | 165611 | `f8890697487494b129f150bac10057c3f78956cb8e34acf49b0d571ede5cd486` |
| `calls/**`（1391 个文件，9748412 B）| — | `493b2393145bb1d88bd9d4a16c622dc5b4cc5dcb1085abb2e51cb9c037706828` |
| `frames/**`（37 个文件，440996 B）| — | `3898b9c48efc488a9aefed8446474087a83a11430914ee6c32f6fd6331362b03` |
| `states/**`（27 个文件，202636 B）| — | `eb55866f2ed179d18d00c6c5890b1be21c1370a0dc22b814f6573813dd89e644` |

## t140-playjev-v3-w90-r2 / match3 / playjev

* 目录：`runs/model-player/t140-playjev-v3-w90-r2/match3/playjev`
* verdict：`INCONCLUSIVE`（counts_as_pass=False，strict=INCONCLUSIVE，baseline=INCONCLUSIVE，game_side=None）
* 档位+轮次：`INCONCLUSIVE @w90 r2`（window=90，round=2，reporting=90，at_reporting_window=True，reporting_state=ok）
* 注入/接受后变化/rate：12 / 4 / 0.3333
* 两窗对齐：9/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 2 frame(s))（matched 9/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game match3 --backend playjev --player model --variant V3 --image-form full --steps 12 --port 9986 --window-frames 90 --round 2 --change-margin strict --out-prefix t140-playjev-v3-w90-r2`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t140-playjev-v3-w90-r2/match3/playjev/demo.png` | 204278 | `95625525af761a107d95433b836bcb1e2b16821335afca2910fb6fb545460035` |
| `runs/model-player/t140-playjev-v3-w90-r2/match3/playjev/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t140-playjev-v3-w90-r2/match3/playjev/engine-game.stdout.txt` | 769 | `fddc8a5d29e990bed8fbeb677961da9bb38ab8e6f59b20689a6f34196c84279c` |
| `runs/model-player/t140-playjev-v3-w90-r2/match3/playjev/filmstrip.png` | 143258 | `60197946725b7dd7365ac0f4165dff19939e8f4f9ff9c36a47ab14cac5a09da0` |
| `runs/model-player/t140-playjev-v3-w90-r2/match3/playjev/frames.json` | 609195 | `87711b49fbb0580dbea2c3788645942d13d761cd729af5bfa4945d512192f571` |
| `runs/model-player/t140-playjev-v3-w90-r2/match3/playjev/player.json` | 373990 | `806a3b6be1b55996f22f38467b5f96dad2488d48f96e9dca60c29eb37e048520` |
| `runs/model-player/t140-playjev-v3-w90-r2/match3/playjev/session.json` | 13772 | `6133a16ac7b3f3fd2d7b2fba7a70fc5eeed2aefe04e630bf081e62ddc0a53926` |
| `runs/model-player/t140-playjev-v3-w90-r2/match3/playjev/steps.jsonl` | 149366 | `3900a8f99ce3e6146033649c94ba1a4ee5257b05735ba3a00420ed219c77ddc2` |
| `calls/**`（1468 个文件，15700124 B）| — | `f4ba10957981bc8389eafab8109e34b7cac1432bb2f3aa25ece2512202c540b0` |
| `frames/**`（37 个文件，429940 B）| — | `11dbffe610af3bc927921ef96ba7df3345526080e419b6ab07ac77a94154c30a` |
| `states/**`（27 个文件，329459 B）| — | `4032a3555c9182f04a76994caea1310de5d496d56483de9ee65cf2e7f9c57f5d` |

## t140-playjev-v3-w90-r2 / minesweeper / playjev

* 目录：`runs/model-player/t140-playjev-v3-w90-r2/minesweeper/playjev`
* verdict：`INCONCLUSIVE`（counts_as_pass=False，strict=INCONCLUSIVE，baseline=INCONCLUSIVE，game_side=None）
* 档位+轮次：`INCONCLUSIVE @w90 r2`（window=90，round=2，reporting=90，at_reporting_window=True，reporting_state=ok）
* 注入/接受后变化/rate：12 / 4 / 0.3333
* 两窗对齐：4/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 2 frame(s))（matched 4/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game minesweeper --backend playjev --player model --variant V3 --image-form full --steps 12 --port 9986 --window-frames 90 --round 2 --change-margin strict --out-prefix t140-playjev-v3-w90-r2`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t140-playjev-v3-w90-r2/minesweeper/playjev/demo.png` | 153153 | `c3543f093cbdd76035dbb653d428898bee908e910f01b959225577530ede764d` |
| `runs/model-player/t140-playjev-v3-w90-r2/minesweeper/playjev/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t140-playjev-v3-w90-r2/minesweeper/playjev/engine-game.stdout.txt` | 745 | `ed2b430f0935ccb0f76b0571b7f9b1c71545cecb58ad367308a90c503235c3a3` |
| `runs/model-player/t140-playjev-v3-w90-r2/minesweeper/playjev/filmstrip.png` | 128011 | `913317c0ada268725f83789a73532b87ed3e9431716b7d1ebef922c3d76b38f4` |
| `runs/model-player/t140-playjev-v3-w90-r2/minesweeper/playjev/frames.json` | 621927 | `6842f07c55f0313bca679c05ce1ea90cf3f0a6738a400625652506f8c1a92432` |
| `runs/model-player/t140-playjev-v3-w90-r2/minesweeper/playjev/player.json` | 388228 | `7cce5932e4449a42a9484e2a1f219c636a15b66b0a791c5ade41bec59e3ad2c4` |
| `runs/model-player/t140-playjev-v3-w90-r2/minesweeper/playjev/session.json` | 13893 | `f222c8669ab2a0b0412aa8bb2fa6c3ec6d92078ff4743d9bab0d4f909e761fdd` |
| `runs/model-player/t140-playjev-v3-w90-r2/minesweeper/playjev/steps.jsonl` | 152156 | `e90ce0976702f083dc06793f352844fd7fac4e372e9643d44e89d68c55786e9a` |
| `calls/**`（1323 个文件，32765416 B）| — | `1aaae7982689847683c399a41311c8e2e356c7167457261c6a6861bec763f721` |
| `frames/**`（37 个文件，439449 B）| — | `cc4613d3144adea11d24cc4b8e21ea2cf7a1030246567e0b7699e9f764d6e025` |
| `states/**`（27 个文件，785160 B）| — | `211c97b8cf2a2399b43aa30b0a0250ce72dc3d8adc6546964da838b3a8b18d58` |

## t140-playjev-v3-w90-r2 / pacman / playjev

* 目录：`runs/model-player/t140-playjev-v3-w90-r2/pacman/playjev`
* verdict：`FAIL`（counts_as_pass=False，strict=FAIL，baseline=FAIL，game_side=None）
* 档位+轮次：`FAIL @w90 r2`（window=90，round=2，reporting=90，at_reporting_window=True，reporting_state=ok）
* 注入/接受后变化/rate：12 / 0 / None
* 两窗对齐：3/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 2 frame(s))（matched 3/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game pacman --backend playjev --player model --variant V3 --image-form full --steps 12 --port 9986 --window-frames 90 --round 2 --change-margin strict --out-prefix t140-playjev-v3-w90-r2`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t140-playjev-v3-w90-r2/pacman/playjev/demo.png` | 153644 | `30e498fbafb8fa65aa3deeccde163e4d954b4111329bd756e3ed52b12f927602` |
| `runs/model-player/t140-playjev-v3-w90-r2/pacman/playjev/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t140-playjev-v3-w90-r2/pacman/playjev/engine-game.stdout.txt` | 733 | `b28cb19354f955eb915e771e13987049b70fb42ee2b2827d130343936ad608f4` |
| `runs/model-player/t140-playjev-v3-w90-r2/pacman/playjev/filmstrip.png` | 141068 | `01afb6f0313deba66d0375f719205d0ce8442b51eb6a859eade89cd71ed28833` |
| `runs/model-player/t140-playjev-v3-w90-r2/pacman/playjev/frames.json` | 592176 | `d925f1a73ef06e03e7e08c70af2f56e56689a537773920c34bb98bc0705f59d1` |
| `runs/model-player/t140-playjev-v3-w90-r2/pacman/playjev/player.json` | 369180 | `7636f1b825c93b0e08c239663594d2571bc900836008c484d5fc5e20258f85cf` |
| `runs/model-player/t140-playjev-v3-w90-r2/pacman/playjev/session.json` | 13337 | `39420a98fd9f2528ba14d2dd9b3ca9991b24a281602ec9fefa5bd9d2ea2cdfb1` |
| `runs/model-player/t140-playjev-v3-w90-r2/pacman/playjev/steps.jsonl` | 155008 | `21949540a7fafda9b938386fd720fc981cd528f37c5eb9cb5a1e587e5df340e8` |
| `calls/**`（1337 个文件，48481643 B）| — | `347445314a5e9d1a097abae5eecfc82cd0a4d5da36bdfd86a25c03645ad84ee2` |
| `frames/**`（37 个文件，417286 B）| — | `988174fad9525a365801644fcbb42f7ad94a1ec6afe342956d646abfdb4f5ad1` |
| `states/**`（27 个文件，1185215 B）| — | `407b37c1c53e64c70e034964b0d21f810ec7bde6522584b6ffc11bea758de1d6` |

## t140-playjev-v3-w90-r2 / pong / playjev

* 目录：`runs/model-player/t140-playjev-v3-w90-r2/pong/playjev`
* verdict：`INCONCLUSIVE`（counts_as_pass=False，strict=INCONCLUSIVE，baseline=INCONCLUSIVE，game_side=None）
* 档位+轮次：`INCONCLUSIVE @w90 r2`（window=90，round=2，reporting=90，at_reporting_window=True，reporting_state=ok）
* 注入/接受后变化/rate：12 / 1 / 0.0833
* 两窗对齐：5/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 2 frame(s))（matched 5/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game pong --backend playjev --player model --variant V3 --image-form full --steps 12 --port 9986 --window-frames 90 --round 2 --change-margin strict --out-prefix t140-playjev-v3-w90-r2`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t140-playjev-v3-w90-r2/pong/playjev/demo.png` | 74650 | `b02cbc9cd141647175612ef3bf2cebde0dac141eb01ad63f3a49d3f40f9555c2` |
| `runs/model-player/t140-playjev-v3-w90-r2/pong/playjev/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t140-playjev-v3-w90-r2/pong/playjev/engine-game.stdout.txt` | 6482 | `2044c897cef436f38d9c8955ffce3ef5103a0681ff80de2eccd339b792f59908` |
| `runs/model-player/t140-playjev-v3-w90-r2/pong/playjev/filmstrip.png` | 45424 | `ede963a4d87a83609e06bd273226910194c99e6442cb6044b62d72509615948f` |
| `runs/model-player/t140-playjev-v3-w90-r2/pong/playjev/frames.json` | 251301 | `a30d06cd4c698aad8fe354c7c0a4f787471fd87186375276008d3a0e3aed7298` |
| `runs/model-player/t140-playjev-v3-w90-r2/pong/playjev/player.json` | 256264 | `18116827f98130ee9460d6efb250572d3532b83d7b793e33e8000501cc532f18` |
| `runs/model-player/t140-playjev-v3-w90-r2/pong/playjev/session.json` | 12200 | `11ce275cf2fc10a162e29b64711694a2edff11ce83001fdb124fb13e601161f3` |
| `runs/model-player/t140-playjev-v3-w90-r2/pong/playjev/steps.jsonl` | 146258 | `b9da7abe90dc19baf5033e4fb177cf16b22a0202348a216c5f94d77ba9cbbdb2` |
| `calls/**`（1432 个文件，3536026 B）| — | `49a5c5f141a6f14170a40863453a762fb0bdbc801c43df891dbf2ba62fe12bb8` |
| `frames/**`（37 个文件，161791 B）| — | `75b155c0cee8c7c949b9fd4885c894a06f3e267d3d39af99c3ddca176b1151f8` |
| `states/**`（27 个文件，64720 B）| — | `7e945159c36c678f110bf80c5d1db7b8668853f9a2b6c4770692e481890d754b` |

## t140-playjev-v3-w90-r2 / rtype / playjev

* 目录：`runs/model-player/t140-playjev-v3-w90-r2/rtype/playjev`
* verdict：`PASS`（counts_as_pass=True，strict=PASS，baseline=PASS，game_side=None）
* 档位+轮次：`PASS @w90 r2`（window=90，round=2，reporting=90，at_reporting_window=True，reporting_state=ok）
* 注入/接受后变化/rate：12 / 6 / 1.0
* 两窗对齐：8/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 1 frame(s))（matched 8/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game rtype --backend playjev --player model --variant V3 --image-form full --steps 12 --port 9986 --window-frames 90 --round 2 --change-margin strict --out-prefix t140-playjev-v3-w90-r2`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t140-playjev-v3-w90-r2/rtype/playjev/demo.png` | 158321 | `398a7bdd96503aab9128ca7c15f6deb1deadee846887681976487714a6492273` |
| `runs/model-player/t140-playjev-v3-w90-r2/rtype/playjev/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t140-playjev-v3-w90-r2/rtype/playjev/engine-game.stdout.txt` | 743 | `429bc725ec19b99ad86d2ace041044e9411687226a1712a3675c6195b469bfaa` |
| `runs/model-player/t140-playjev-v3-w90-r2/rtype/playjev/filmstrip.png` | 105150 | `883a41ef34c259c1a2c340f31222174dfbdca0c659d087825755d18830ae8bc2` |
| `runs/model-player/t140-playjev-v3-w90-r2/rtype/playjev/frames.json` | 631532 | `eab16a8f1ec4f3322516b8dccad7ddcf5a7555efcff248f7d1cc80d89a8b62d8` |
| `runs/model-player/t140-playjev-v3-w90-r2/rtype/playjev/player.json` | 380813 | `5c33ca4365610e48554731aafd5640aa54ea0f24ab6c228b4dc3745fde9df7eb` |
| `runs/model-player/t140-playjev-v3-w90-r2/rtype/playjev/session.json` | 12125 | `55f181c2f24f9ae2bb4b2df15a3772c0e64c8de4505acde6b8886b7046334544` |
| `runs/model-player/t140-playjev-v3-w90-r2/rtype/playjev/steps.jsonl` | 157995 | `37d171394d94cd398bca7f1bce69ff7fecac557fe7c5e0e2d61fcb734430801c` |
| `calls/**`（1427 个文件，22613236 B）| — | `749487a2c345aa2384f54d12758fdbd4a6577681052e1f1f7e79ff32a04badc0` |
| `frames/**`（37 个文件，446937 B）| — | `675bd02c3582d16a4d7e7acb6047a1c327044dbca3d052f1f418e6fc4cc40f16` |
| `states/**`（27 个文件，499930 B）| — | `431113a4dfcc95680ef5930882c5fef1aa81ed0639993bde6baa31cd0575608b` |

## t140-playjev-v3-w90-r2 / snake / playjev

* 目录：`runs/model-player/t140-playjev-v3-w90-r2/snake/playjev`
* verdict：`INCONCLUSIVE`（counts_as_pass=False，strict=INCONCLUSIVE，baseline=INCONCLUSIVE，game_side=None）
* 档位+轮次：`INCONCLUSIVE @w90 r2`（window=90，round=2，reporting=90，at_reporting_window=True，reporting_state=ok）
* 注入/接受后变化/rate：12 / 4 / 0.3636
* 两窗对齐：6/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 2 frame(s))（matched 6/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game snake --backend playjev --player model --variant V3 --image-form full --steps 12 --port 9986 --window-frames 90 --round 2 --change-margin strict --out-prefix t140-playjev-v3-w90-r2`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t140-playjev-v3-w90-r2/snake/playjev/demo.png` | 65779 | `d66bcd31fd5c69fa4a557f2e2ab9b9bf6a4981f5d71b87bab6ac64b7b0c10943` |
| `runs/model-player/t140-playjev-v3-w90-r2/snake/playjev/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t140-playjev-v3-w90-r2/snake/playjev/engine-game.stdout.txt` | 14262 | `87ed889bf15c9e9048197848456c91a563c42f9d2caf2005b38370a93bce2ac6` |
| `runs/model-player/t140-playjev-v3-w90-r2/snake/playjev/filmstrip.png` | 44049 | `d0afbc1715d8dd72d8f6e4d9f7ac6a664c6f2a225b261147df38e9e48c224982` |
| `runs/model-player/t140-playjev-v3-w90-r2/snake/playjev/frames.json` | 188043 | `cc24e12cf5cf6869090e7364afb5357a6c2f6cbb50b95a44b5850a170960b264` |
| `runs/model-player/t140-playjev-v3-w90-r2/snake/playjev/player.json` | 239194 | `9ee004bb086dfef1f6b34efe7ed2cd9e245b35e01dc8945574a075d3a5889552` |
| `runs/model-player/t140-playjev-v3-w90-r2/snake/playjev/session.json` | 12758 | `1537e8937c9071efbcc05d3b4751807e9ac46e599b2f69ed3f248a7e3ebda940` |
| `runs/model-player/t140-playjev-v3-w90-r2/snake/playjev/steps.jsonl` | 154553 | `3c4bdccd1ee23286fd19bdf7b164a272ddbb964d6ab7c002b815e44a206f21f6` |
| `calls/**`（990 个文件，7580475 B）| — | `3c3bc321c69aa886459f5149bbb1ff0143f281482fa98103de6c5a0b02fce22c` |
| `frames/**`（37 个文件，114563 B）| — | `a4b6573f1c0fa2f60cce8520476c972294cdbf8297180ca9d6da07b6a69f5507` |
| `states/**`（27 个文件，237352 B）| — | `ddecf4f312e0ea4bec75871898d24e8bd692d8328f6419a449aec0f572e03cae` |

## t140-playjev-v3-w90-r2 / sokoban / playjev

* 目录：`runs/model-player/t140-playjev-v3-w90-r2/sokoban/playjev`
* verdict：`PASS`（counts_as_pass=True，strict=PASS，baseline=PASS，game_side=None）
* 档位+轮次：`PASS @w90 r2`（window=90，round=2，reporting=90，at_reporting_window=True，reporting_state=ok）
* 注入/接受后变化/rate：12 / 4 / 1.0
* 两窗对齐：10/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 1 frame(s))（matched 10/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game sokoban --backend playjev --player model --variant V3 --image-form full --steps 12 --port 9986 --window-frames 90 --round 2 --change-margin strict --out-prefix t140-playjev-v3-w90-r2`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t140-playjev-v3-w90-r2/sokoban/playjev/demo.png` | 151809 | `2ec30cc61afd21ff505f74c50caf290319ccb6e0c5843e8ca32a3b93b0087581` |
| `runs/model-player/t140-playjev-v3-w90-r2/sokoban/playjev/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t140-playjev-v3-w90-r2/sokoban/playjev/engine-game.stdout.txt` | 745 | `c583431a5175827ce2c6eedfa99535e645ffbdb7046637f5709818d4cd98fe96` |
| `runs/model-player/t140-playjev-v3-w90-r2/sokoban/playjev/filmstrip.png` | 104413 | `e6061731adec0270553f753d1a907444f27f89c0b4b6f82a090db7d03dd1b6f1` |
| `runs/model-player/t140-playjev-v3-w90-r2/sokoban/playjev/frames.json` | 643279 | `5aa38a99952207325f5edae08444b9ee601d5cf8c4499e0abd48344e594896e1` |
| `runs/model-player/t140-playjev-v3-w90-r2/sokoban/playjev/player.json` | 382792 | `509086620d098a2aecca522d88bb014d28ca45c1ea15f5c044bd67d8b8ed36ab` |
| `runs/model-player/t140-playjev-v3-w90-r2/sokoban/playjev/session.json` | 13482 | `640988f60203a93f91aa107bc2e293edc9cba4d326b8b5c6f78b497ae31c8a3a` |
| `runs/model-player/t140-playjev-v3-w90-r2/sokoban/playjev/steps.jsonl` | 161141 | `2cd10b36f8d8bfaa74f2752d854a293a68f23291cf557075a05b2ca6299f325e` |
| `calls/**`（1374 个文件，16900965 B）| — | `400fa6f443cfc1e5b74a7b7b518fda6352c07d357f5ac3187b9e830bb7408b30` |
| `frames/**`（37 个文件，455461 B）| — | `7022eca90a38ef283945d0533965c9ce695f56eefdddc6501c3add49b67182d9` |
| `states/**`（27 个文件，374178 B）| — | `d1d39824269f1239cdabeaa9ea55d70d27491bc277207e7420184655655b95b0` |

## t140-playjev-v3-w90-r2 / tetris / playjev

* 目录：`runs/model-player/t140-playjev-v3-w90-r2/tetris/playjev`
* verdict：`INCONCLUSIVE`（counts_as_pass=False，strict=INCONCLUSIVE，baseline=INCONCLUSIVE，game_side=None）
* 档位+轮次：`INCONCLUSIVE @w90 r2`（window=90，round=2，reporting=90，at_reporting_window=True，reporting_state=ok）
* 注入/接受后变化/rate：0 / 0 / None
* 两窗对齐：8/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 2 frame(s))（matched 8/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game tetris --backend playjev --player model --variant V3 --image-form full --steps 12 --port 9986 --window-frames 90 --round 2 --change-margin strict --out-prefix t140-playjev-v3-w90-r2`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t140-playjev-v3-w90-r2/tetris/playjev/demo.png` | 68731 | `f37f24a934741f20032811cf6babce1df3e0a3d6665d4c42df3ae41405673890` |
| `runs/model-player/t140-playjev-v3-w90-r2/tetris/playjev/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t140-playjev-v3-w90-r2/tetris/playjev/engine-game.stdout.txt` | 11775 | `4979753933e611150362f8d4af07565de1ec532a3acb87aac0b7cdb35e40185e` |
| `runs/model-player/t140-playjev-v3-w90-r2/tetris/playjev/filmstrip.png` | 42823 | `b83408cf62d21d61d36bf140a2ba57fe24fe49a2e8ee597709c2118850ff0565` |
| `runs/model-player/t140-playjev-v3-w90-r2/tetris/playjev/frames.json` | 286923 | `10140945f4fff83b02a6d754246ffcfe550509992d988759e06ec9b4e3c3d1a7` |
| `runs/model-player/t140-playjev-v3-w90-r2/tetris/playjev/player.json` | 261385 | `90c3657510c6c42b2594d08d0ad78ac34cf57e2260f46143f46df44eb4fd2c03` |
| `runs/model-player/t140-playjev-v3-w90-r2/tetris/playjev/session.json` | 11980 | `95724e2c6ea786439b15bd008a1a77930f4b152c370dab3d2cd27081db5b8c27` |
| `runs/model-player/t140-playjev-v3-w90-r2/tetris/playjev/steps.jsonl` | 129284 | `761fc0414e205ebe6f65f453ab05774c71084f580c32f8d71175d820a383f02d` |
| `calls/**`（1429 个文件，2595670 B）| — | `e6926b7290ba3cc1af0594e66685e0d7d2d9aff0626861ffd9641a616dc969f1` |
| `frames/**`（37 个文件，188182 B）| — | `8c073eb16719d9524d6f1b5cc0e1cd6d09f93a0a562ad32290d4489ee5197078` |
| `states/**`（27 个文件，41776 B）| — | `84e98f34c3cfea01c209d03a72a13fa7cc851bc90e4c4ae769dad50352fc043c` |

## t140-w30-demo / asteroids / scripted

* 目录：`runs/model-player/t140-w30-demo/asteroids/scripted`
* verdict：`PASS`（counts_as_pass=False，strict=PASS，baseline=PASS，game_side=PASS）
* 档位+轮次：`PASS @w30 r1 [reference only: window 30 < reporting 90]`（window=30，round=1，reporting=90，at_reporting_window=False，reporting_state=BELOW_REPORTING_WINDOW）
* 注入/接受后变化/rate：8 / 8 / 1.0
* 两窗对齐：5/8 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 1 frame(s))（matched 5/8，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:/Anaconda/python.exe runs/model-player/_scripts/t140_sweep.py --arm scripted --window 30 --round 1 --port-base 9987 --prefix t140-w30-demo asteroids`  <- t136_commands.jsonl
  * `D:\Anaconda\python.exe F:\moonbit-hof-rs\godot-mcp\tools\playtest_player.py run --game asteroids --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9987 --window-frames 30 --round 1 --change-margin strict --out-prefix t140-w30-demo`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t140-w30-demo/asteroids/scripted/demo.png` | 88641 | `603fcb8635010e9a55fee9e8244251e1f40f82af19844681daf82ee9fb014438` |
| `runs/model-player/t140-w30-demo/asteroids/scripted/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t140-w30-demo/asteroids/scripted/engine-game.stdout.txt` | 741 | `27fa94c5fa5fa657bc8156c08f749a2aed985223b7b7acd982d9efb7509709cd` |
| `runs/model-player/t140-w30-demo/asteroids/scripted/filmstrip.png` | 51580 | `4e6beca99fb4ce7627845fda8563e2c035c2be491dbd3da72a0089f7ae957314` |
| `runs/model-player/t140-w30-demo/asteroids/scripted/frames.json` | 374780 | `16bdff8e471243968d7498b99d1f49dd6f13e8a63f165e23f35929c8c6444c7a` |
| `runs/model-player/t140-w30-demo/asteroids/scripted/player.json` | 22647 | `1a31814bf5c12ad2a7fe4806d4b9ee87d8b06f6d9bd6f8a6a5213122c71b2106` |
| `runs/model-player/t140-w30-demo/asteroids/scripted/session.json` | 12176 | `8acdc47e1be4dd3d44c4895f3fa4c4a9ae442fffc1bd722524016f6ce1643116` |
| `runs/model-player/t140-w30-demo/asteroids/scripted/steps.jsonl` | 101103 | `89394f67fb4ca71be5fcd6b994686d5ec0ac0c0b06e4c97a245c5a3d1f484602` |
| `calls/**`（409 个文件，1469124 B）| — | `4b7dbbcd10c97b5d1b8795623314db777f365e8eb4c7257a637b3cd47562d4d6` |
| `frames/**`（25 个文件，263051 B）| — | `2031b4856863907c4bbe5b34d9cb778a429a355b807e271437be5bad7b4b0ffa` |
| `states/**`（19 个文件，59721 B）| — | `92ac8182bc364d41d1666751154dd66d49473d0766be5d7ee3a64d5495e0927b` |

## t140-respawn-demo / asteroids / scripted

* 目录：`runs/model-player/t140-respawn-demo/asteroids/scripted`
* verdict：`PASS(baseline only)`（counts_as_pass=False，strict=FAIL，baseline=PASS，game_side=FAIL）
* 档位+轮次：`PASS(baseline only) @w90 r1`（window=90，round=1，reporting=90，at_reporting_window=True，reporting_state=ok）
* 注入/接受后变化/rate：9 / 8 / 0.8889
* 两窗对齐：5/9 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 1 frame(s))（matched 5/9，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:/Anaconda/python.exe tools/playtest_player.py run --game asteroids --backend scripted --player scripted --variant V1 --image-form full --steps 24 --port 9988 --window-frames 90 --round 1 --change-margin strict --out-prefix t140-respawn-demo --prep-actions ast_thrust ast_thrust ast_thrust`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t140-respawn-demo/asteroids/scripted/demo.png` | 99544 | `9b944b7b1bfcaf891ecb812eeff4fbf6ec7480a184e9d3e5ce677d4c2e76916a` |
| `runs/model-player/t140-respawn-demo/asteroids/scripted/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t140-respawn-demo/asteroids/scripted/engine-game.stdout.txt` | 741 | `b5a3a8fa64cf93e816e62cf11e5f18e687396adcdaef9a829a6b663f4e1801c3` |
| `runs/model-player/t140-respawn-demo/asteroids/scripted/filmstrip.png` | 69303 | `7179c22ced26a6f8770f6d773f8ab1b7bd85435f449e89798780f9e55903bbaa` |
| `runs/model-player/t140-respawn-demo/asteroids/scripted/frames.json` | 504513 | `5ca710f68c8e01802a853c7b3a779b456fd73f5639e6e0cc73d50bcdc8ab7179` |
| `runs/model-player/t140-respawn-demo/asteroids/scripted/player.json` | 30925 | `1c2c58209b79f887a1931d2aabfede9418d16eab558521312e5e77761ffef517` |
| `runs/model-player/t140-respawn-demo/asteroids/scripted/prep.json` | 7129 | `691cdccaadf62dba36c686eb552404010272d0ee019a64ac626ebb06dfed3341` |
| `runs/model-player/t140-respawn-demo/asteroids/scripted/session.json` | 12182 | `1eb99b768a4c3b5608a039a04376f260e08d3fce73d9df6441b08f0574ce15b9` |
| `runs/model-player/t140-respawn-demo/asteroids/scripted/steps.jsonl` | 119193 | `aff859aa78b22fd81784e1dcc8614a734f75bcba6516968963bfaf57b93c3e1b` |
| `calls/**`（1189 个文件，3979474 B）| — | `c611df98eae34e706ee4d4054b0bdf1c50448670614486357ef910040e6a3fe3` |
| `frames/**`（34 个文件，353556 B）| — | `43a83d1c6eb122c882241eb9280e553b7dc8e60f907b1e2e0a22225c4cd3fde7` |
| `states/**`（23 个文件，71598 B）| — | `91762fdca017c0c64c223f66c93e06288f292681fa25974ae16f6c3347c62de5` |
