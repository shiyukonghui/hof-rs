# ARTIFACTS-TASK-138 — 关键产物清单（路径 + sha256 + 大小 + 生成命令）

> 为什么入库：`runs/**` 被 `.gitignore` 忽略（第 12 行 `runs/`、第 43 行
> `godot-mcp/runs/`），报告引用的每个 run 产物只存在于本机。本文件把**关键产物**
> 的 sha256 / 大小 / 生成命令**提交进仓**，使结论在 `runs/**` 不入库的前提下仍可事后核验。
>
> 复算：`certutil -hashfile <path> SHA256`，或重跑本清单的生成器
> （命令见本文件表头的 §复算）。

* 生成时刻：`2026-09-28T04:24:52`
* run 目录数：**28**；索引文件数：**224**
* 复算命令：`D:\Anaconda\python.exe runs\model-player\_scripts\t138_artifact_index.py --roots t138-scripted t138-jev-v3 t138-repeat-1 t138-repeat-2 t138-repeat-3 t138-oldctl t138-oldctl2`

## t138-scripted / asteroids / scripted

* 目录：`runs/model-player/t138-scripted/asteroids/scripted`
* verdict：`PASS`（counts_as_pass=True，strict=PASS，baseline=PASS，game_side=PASS）
* 注入/接受后变化/rate：8 / 8 / 1.0
* 两窗对齐：3/8 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 4 frame(s))（matched 3/8，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe runs\model-player\_scripts\t138_windows.py t138-scripted/asteroids/scripted`  <- t136_commands.jsonl
  * `D:\Anaconda\python.exe -c import io,json;L=[json.loads(l) for l in io.open(r'runs/model-player/t138-scripted/asteroids/scripted/steps.jsonl',encoding='utf-8')];s=L[0];print(json.dumps({'fb':s['frame_budget'],'ctl_fb':s['control_diff']['frame_budget'],'ctl':{k:s['control_diff'][k] for k in ('start_drawn','end_drawn','achieved_delta','pixel_diff','movement')}},ensure_ascii=False,indent=1))`  <- t136_commands.jsonl
  * `D:\Anaconda\python.exe runs\model-player\_scripts\t138_step_table.py t138-scripted asteroids scripted`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t138-scripted/asteroids/scripted/demo.png` | 88294 | `aa696cec481d2e794c5c38eb389083de670c5754394f9bef419081ee2378398f` |
| `runs/model-player/t138-scripted/asteroids/scripted/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t138-scripted/asteroids/scripted/engine-game.stdout.txt` | 741 | `30198b50345f423b110840976eb1ddac86cb2105ff0d6906f3714338062c2c1d` |
| `runs/model-player/t138-scripted/asteroids/scripted/filmstrip.png` | 51526 | `dfe2f0b9ce3712cf1e5d70ae53961806deb490126bdd083f2069f79b4d81a4e3` |
| `runs/model-player/t138-scripted/asteroids/scripted/frames.json` | 374072 | `b7fbc8c7ea254ae0979442090a7641286ae68eebaa41976562cf0cf9c7983616` |
| `runs/model-player/t138-scripted/asteroids/scripted/player.json` | 13714 | `e4cfec45c68fbed7a53d6b0e980e1509c7ec2097b2f2ba277115cb6c3434eb2c` |
| `runs/model-player/t138-scripted/asteroids/scripted/session.json` | 10090 | `7864e6417f801ff45e8a68c939f16dbdbfc12c5c2b34fa591903358cf67d511e` |
| `runs/model-player/t138-scripted/asteroids/scripted/steps.jsonl` | 103002 | `3f01f7edb816fdeba62b6f2bc3cbfd0454443e5f092cbf71ce7443d660f98659` |
| `calls/**`（465 个文件，4121080 B）| — | `5b7f4fcf7785634695d3e4f42880f659efe432350394936e4f5eb395c2718ea8` |
| `frames/**`（37 个文件，435756 B）| — | `716b0aa741d6dfb165d5ada005663c9371a8a7f183e9730511dd51272156258a` |
| `states/**`（27 个文件，243517 B）| — | `54d4a1961466a96434b698bacc979d2bf497dcb5e895daa5ae72940260424e56` |

## t138-scripted / bomberman / scripted

* 目录：`runs/model-player/t138-scripted/bomberman/scripted`
* verdict：`FAIL`（counts_as_pass=False，strict=FAIL，baseline=FAIL，game_side=FAIL）
* 注入/接受后变化/rate：12 / 6 / 0.5
* 两窗对齐：1/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 5 frame(s))（matched 1/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t138-scripted/bomberman/scripted/demo.png` | 154216 | `e627813ed3a2f5e3604bb45b19efa57d92163265073969e807da9820b0041872` |
| `runs/model-player/t138-scripted/bomberman/scripted/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t138-scripted/bomberman/scripted/engine-game.stdout.txt` | 775 | `3863f573ec20eae2ca198a195fb8370c7b162ad0f5d7a114a5358f58404fbcb7` |
| `runs/model-player/t138-scripted/bomberman/scripted/filmstrip.png` | 143686 | `c1cd831d3cc1505bb40238b3ba49f6c44ebe377dc5d20724aea25859247050c6` |
| `runs/model-player/t138-scripted/bomberman/scripted/frames.json` | 511843 | `ac6f7fb38ec6e17acbcd32f66aa56e972fe0ef6a7165b51a42d88f1f639ca296` |
| `runs/model-player/t138-scripted/bomberman/scripted/player.json` | 15474 | `947347007e17483b2368dba8451e53d32764434d9fcb1416b7feab1239888f7d` |
| `runs/model-player/t138-scripted/bomberman/scripted/session.json` | 10206 | `45b26a0b05480f220d5a90681db83b2208f8a8edf8f7313e6b01602c88853301` |
| `runs/model-player/t138-scripted/bomberman/scripted/steps.jsonl` | 139474 | `caf98520cc70b77686f179341229755d35f1baaa8a6f0ac6811eff6f03fc0c51` |
| `calls/**`（519 个文件，8019801 B）| — | `846f41be5c9872da44d2b7ffdd69445ab6834ab2f37a3e7adc34beeb02d835a7` |
| `frames/**`（37 个文件，357119 B）| — | `24a2ee1d1e936bda70c13b569536caa3ec51f7b12b9f28a1480dce2fa038ad7b` |
| `states/**`（27 个文件，600566 B）| — | `24c47c3482bd6366fe4f4d7f880dcec524c9602d0300deb1c5d6512402036050` |

## t138-scripted / breakout / scripted

* 目录：`runs/model-player/t138-scripted/breakout/scripted`
* verdict：`INCONCLUSIVE`（counts_as_pass=False，strict=INCONCLUSIVE，baseline=INCONCLUSIVE，game_side=INCONCLUSIVE）
* 注入/接受后变化/rate：3 / 3 / 1.0
* 两窗对齐：1/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 5 frame(s))（matched 1/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t138-scripted/breakout/scripted/demo.png` | 100834 | `2672ab069bab1f12752aec815ea31de7721122ed04a431501e93d3b29c25afe0` |
| `runs/model-player/t138-scripted/breakout/scripted/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t138-scripted/breakout/scripted/engine-game.stdout.txt` | 3621 | `b4be184e8f75f4398e57de1fa50499fca4d1f2dd2a6a4b54a39eee5e1fd756bf` |
| `runs/model-player/t138-scripted/breakout/scripted/filmstrip.png` | 74962 | `14eb7d1113fdd3b98450a62c5a6a833ed0a28a079fa8eb0f9bc2684986a13da6` |
| `runs/model-player/t138-scripted/breakout/scripted/frames.json` | 568737 | `f0892184fc18a63b4f185b6ff4ad20fdff1ab4b7ca44564a82e6c3f99f2b7283` |
| `runs/model-player/t138-scripted/breakout/scripted/player.json` | 14621 | `212e318bea939428e960f6d7e93a8860ce44aec4ea8d05c09e8842a2079a094f` |
| `runs/model-player/t138-scripted/breakout/scripted/session.json` | 10257 | `5596a6fa4e1c4efb326e0705587931c6687ee368e45fefac96d41f3d8ad5ae97` |
| `runs/model-player/t138-scripted/breakout/scripted/steps.jsonl` | 124012 | `7a48d31014afd79cbeed3b4e89d0e44f014dcedf16de9f9ed8b7ba463010126c` |
| `calls/**`（378 个文件，2780262 B）| — | `ddb71e9ef21facbf27218c85337617b157fd92f844427c20129d637179b899e9` |
| `frames/**`（37 个文件，399896 B）| — | `4aadf82421afced955b99a7ef926cdcd3d066c6b3a29954c00b118cf9fe57e3b` |
| `states/**`（27 个文件，148623 B）| — | `3e66896323251d851f0df4bb942d61c2477f1c2d632198494d0ff1bb621d9cd5` |

## t138-scripted / flappy / scripted

* 目录：`runs/model-player/t138-scripted/flappy/scripted`
* verdict：`INCONCLUSIVE`（counts_as_pass=False，strict=INCONCLUSIVE，baseline=INCONCLUSIVE，game_side=FAIL）
* 注入/接受后变化/rate：12 / 1 / 0.0833
* 两窗对齐：5/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 4 frame(s))（matched 5/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t138-scripted/flappy/scripted/demo.png` | 97895 | `68904e5f6fdcb966de5812afa3c04682bbf26f4e347ba4aca30a6d87a32cff6b` |
| `runs/model-player/t138-scripted/flappy/scripted/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t138-scripted/flappy/scripted/engine-game.stdout.txt` | 744 | `1e88c35338f4cc00521094c5ef651ab9818cf96907eb156cc934505bf191aee5` |
| `runs/model-player/t138-scripted/flappy/scripted/filmstrip.png` | 62706 | `ae8ef0baf441cc641d717f76f71d258e5f31301a4ba3d2d5d4f6595f1e320ce9` |
| `runs/model-player/t138-scripted/flappy/scripted/frames.json` | 474194 | `04c99bd795a7292d0bf7186850b25d1164c14b22a6964cb079615ddd02d8fc3b` |
| `runs/model-player/t138-scripted/flappy/scripted/player.json` | 16400 | `ab6fd21a56a99513643b5cca68e5673beab96b1486e666d19d177bb63fc2eb56` |
| `runs/model-player/t138-scripted/flappy/scripted/session.json` | 10043 | `3687be1752abe8aab2a6b6ede3eb29736dbc4b59ecb6d4a6157c54ba5f2e602e` |
| `runs/model-player/t138-scripted/flappy/scripted/steps.jsonl` | 126796 | `f9cd9f0da3e9497057672c3fc35059cd71083ec74c6b44206f7310260583befd` |
| `calls/**`（456 个文件，1719730 B）| — | `987ee8952d26cb69c5e5c0eb05cd80b86252964d9a1b573cd28c18fe47ba639c` |
| `frames/**`（37 个文件，329115 B）| — | `fa001f50ed47bb1d91a16c6a2d1ad8af7ed2f5448cd148ef33da5ec245b1363d` |
| `states/**`（27 个文件，77137 B）| — | `f6362068ac788ba174f8fdd7a92cdada60c8b82a513a8e58682f0b8aaf36097e` |

## t138-scripted / frogger / scripted

* 目录：`runs/model-player/t138-scripted/frogger/scripted`
* verdict：`INCONCLUSIVE`（counts_as_pass=False，strict=INCONCLUSIVE，baseline=INCONCLUSIVE，game_side=INCONCLUSIVE）
* 注入/接受后变化/rate：1 / 1 / 1.0
* 两窗对齐：0/1 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 2 frame(s))（matched 0/1，all_matched=False）
* ack 缺失步数：0
* 生成命令：

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t138-scripted/frogger/scripted/demo.png` | 15281 | `8fdec9ae10fdf45f61ef6aebc6726486492e194502b90f155db542222f430881` |
| `runs/model-player/t138-scripted/frogger/scripted/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t138-scripted/frogger/scripted/engine-game.stdout.txt` | 748 | `76a7b17dcc9cb9111a1bee94cd2037423dfea34772f296aa4ad10d3974c3d208` |
| `runs/model-player/t138-scripted/frogger/scripted/filmstrip.png` | 13847 | `41a1abe17bb8745049b0c731ffc6e75789fdeac125e14be700cf546557e0b969` |
| `runs/model-player/t138-scripted/frogger/scripted/frames.json` | 63836 | `8f432d5ce9d4b96b94f1681a264c1ef5a7aae0e470b82312e4eeae8da9360cac` |
| `runs/model-player/t138-scripted/frogger/scripted/player.json` | 12533 | `728419300c4011abcd31278e16bcec0286e46c4f326c1bd31e8f057856bb9a57` |
| `runs/model-player/t138-scripted/frogger/scripted/session.json` | 9995 | `6eb1e2b1cb3eec892297af03ab2f32ab8f9c7248d05911e6fb441f6c4a770cc9` |
| `runs/model-player/t138-scripted/frogger/scripted/steps.jsonl` | 10728 | `fd8f7f0330b8fc85b3ca85cfd4d64e3f3d0d2bff6449dce7e7971165aa7678d0` |
| `calls/**`（346 个文件，1422542 B）| — | `4462d5d54d11dba32752bc935b743cd6d0e06c7049065462af99fbf334bbfe66` |
| `frames/**`（37 个文件，388041 B）| — | `0ca1491606df3a9a3580cbad10d320963008deef6f8f6719116905d6f88f82bd` |
| `states/**`（27 个文件，84846 B）| — | `875cec8a233dfccad0caa6863285db889f68f954212bc6b8f8b094e9057772a3` |

## t138-scripted / game2048 / scripted

* 目录：`runs/model-player/t138-scripted/game2048/scripted`
* verdict：`PASS`（counts_as_pass=True，strict=PASS，baseline=PASS，game_side=PASS）
* 注入/接受后变化/rate：8 / 8 / 1.0
* 两窗对齐：1/8 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 2 frame(s))（matched 1/8，all_matched=False）
* ack 缺失步数：0
* 生成命令：

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t138-scripted/game2048/scripted/demo.png` | 105371 | `809c95dd28efc6f280e6bd364770a565a01f855ca91df2314b109f8ebb8bee36` |
| `runs/model-player/t138-scripted/game2048/scripted/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t138-scripted/game2048/scripted/engine-game.stdout.txt` | 781 | `91f979e169cd398d118d8119c1ccd410e8cfe5e42616530afe82456ca80013f7` |
| `runs/model-player/t138-scripted/game2048/scripted/filmstrip.png` | 65250 | `8b39ca1c5bc016326495bf62fcef6deb85db6194028962d7ac1691659d624cf2` |
| `runs/model-player/t138-scripted/game2048/scripted/frames.json` | 452743 | `7e430f36e6ee49b649221ecf519200f6c94e60463bebfd76a42e29352f362efd` |
| `runs/model-player/t138-scripted/game2048/scripted/player.json` | 13576 | `a2e00f198432d5ec5de4ff6f1499233a6e2ab704844a82f67f67fe5a356af1ed` |
| `runs/model-player/t138-scripted/game2048/scripted/session.json` | 9950 | `7214bd784ad1b7aee3269441dab1a77bf2893d4f957e3a03ad7a8a3ac7f44741` |
| `runs/model-player/t138-scripted/game2048/scripted/steps.jsonl` | 103909 | `5c7063469231b6702a8cbbeaeded6eac22c6f43fe8d49e373c8094902f9fc808` |
| `calls/**`（294 个文件，2164116 B）| — | `7e75dd73f72aa2d5192469bb5071f4088dd79b6fce13290c9bd0443fce8987cd` |
| `frames/**`（25 个文件，321508 B）| — | `fe0c28f55132a681ff8027e18e5fa5c93343339277a791e6f35c97e7e9312db8` |
| `states/**`（19 个文件，142695 B）| — | `c21f996f1f843c191989531977ea40af77db27526565cc9b0e9541551388e305` |

## t138-scripted / lunarlander / scripted

* 目录：`runs/model-player/t138-scripted/lunarlander/scripted`
* verdict：`PASS`（counts_as_pass=True，strict=PASS，baseline=PASS，game_side=PASS）
* 注入/接受后变化/rate：8 / 8 / 1.0
* 两窗对齐：1/8 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 3 frame(s))（matched 1/8，all_matched=False）
* ack 缺失步数：0
* 生成命令：

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t138-scripted/lunarlander/scripted/demo.png` | 108025 | `d877e81176d2cb4f70b9b351240b3182b8096b92341d9de4d127e30218f3dca5` |
| `runs/model-player/t138-scripted/lunarlander/scripted/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t138-scripted/lunarlander/scripted/engine-game.stdout.txt` | 766 | `8edbfd709a3b8d531c295d65f019d1443952aa5812eddd3e545ce97b37400673` |
| `runs/model-player/t138-scripted/lunarlander/scripted/filmstrip.png` | 74547 | `7e121b223ce72fb916f5091c356afbea366c6eea0c8f759119832428f5c4d443` |
| `runs/model-player/t138-scripted/lunarlander/scripted/frames.json` | 455040 | `84051fd26d75c79e018983a574ecbf687bc3836826bc99900009d63ab64019d2` |
| `runs/model-player/t138-scripted/lunarlander/scripted/player.json` | 13704 | `57f1a900bfcce28544b327cb64e80fd534613f9624bdf19d24ead1084a767820` |
| `runs/model-player/t138-scripted/lunarlander/scripted/session.json` | 10025 | `d28b2e04527f2bd5100aaff3dd4c1f231d66ce7e9407c9128dfd9b56a4447c82` |
| `runs/model-player/t138-scripted/lunarlander/scripted/steps.jsonl` | 95443 | `9b86595dbdc72180f9a873ff7ed535c12e43a2b67533dc670318086dc02b4b64` |
| `calls/**`（397 个文件，4049179 B）| — | `f4cc3271abd878960fc2f7fc5979965e6b6c22796d74b8d0b2223df51fb881e6` |
| `frames/**`（34 个文件，449077 B）| — | `4d6c648a8b8378a0d72d75e8a2f1e6ee65e5c89200dfe82aa8c03af153d7ad11` |
| `states/**`（25 个文件，299231 B）| — | `fe2423a7fcf4d576830bc2d27a08a48e280347bb2818cf3bb72877a6569aa6eb` |

## t138-scripted / match3 / scripted

* 目录：`runs/model-player/t138-scripted/match3/scripted`
* verdict：`FAIL`（counts_as_pass=False，strict=FAIL，baseline=FAIL，game_side=FAIL）
* 注入/接受后变化/rate：12 / 8 / 0.6667
* 两窗对齐：2/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 4 frame(s))（matched 2/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t138-scripted/match3/scripted/demo.png` | 193922 | `0486c7cfb1cf7cc489de698f26380c2e75d238987d1168e4c2ebcbaafd563a73` |
| `runs/model-player/t138-scripted/match3/scripted/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t138-scripted/match3/scripted/engine-game.stdout.txt` | 769 | `bc88e0077f899351fa3a31dcfc02d38c6ebe10012ff172ca4fc375c34f1e9114` |
| `runs/model-player/t138-scripted/match3/scripted/filmstrip.png` | 154043 | `38bdbcea42c10e16e0b234c96e405ce2a007215f051c5739c5be1e6ca1503b78` |
| `runs/model-player/t138-scripted/match3/scripted/frames.json` | 611492 | `341897bce202fda4df22fe68367e0be396eab22850ade0bbdc054a09f984c7fa` |
| `runs/model-player/t138-scripted/match3/scripted/player.json` | 14818 | `aa2e7e16f2097b57ac4f12249bd0f6fbac6639b392796cbc75a13d591dfe13f3` |
| `runs/model-player/t138-scripted/match3/scripted/session.json` | 10208 | `f5ce4489f19d4917ca2f756ae36cb326c39dab9cd35bf277cb6c2f1ed7950ce4` |
| `runs/model-player/t138-scripted/match3/scripted/steps.jsonl` | 136990 | `3fa44a4ad8633098b8bd442f4a7d380d279716dff5170d249711c8cb72e7162a` |
| `calls/**`（451 个文件，4473835 B）| — | `a1da39ea335ee083e5423b7e6b98d4048e3d9c5335a46787b345bf70d96f89a9` |
| `frames/**`（37 个文件，431921 B）| — | `095856417da69ba335e3d3e1676011ce256958c469fea4cee4761881a775dc54` |
| `states/**`（27 个文件，330690 B）| — | `29a39398d61177763c6ebccc5323b25cd6373db2f988d569b099d892b1c59408` |

## t138-scripted / minesweeper / scripted

* 目录：`runs/model-player/t138-scripted/minesweeper/scripted`
* verdict：`INCONCLUSIVE`（counts_as_pass=False，strict=INCONCLUSIVE，baseline=INCONCLUSIVE，game_side=FAIL）
* 注入/接受后变化/rate：12 / 7 / 0.5833
* 两窗对齐：6/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 5 frame(s))（matched 6/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t138-scripted/minesweeper/scripted/demo.png` | 186247 | `b8eac16be98b56a3c8c15d89f73002a9c9b3938d44245953344196f465ec5872` |
| `runs/model-player/t138-scripted/minesweeper/scripted/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t138-scripted/minesweeper/scripted/engine-game.stdout.txt` | 745 | `889e699d2a959c58d6e8a9e4918a89e33201f2d54b0d250b05a15213b5bd9dad` |
| `runs/model-player/t138-scripted/minesweeper/scripted/filmstrip.png` | 182715 | `bb903653f3b27411a1d883980a94fcd0d53d7bb980bbac97557e61e6858d0426` |
| `runs/model-player/t138-scripted/minesweeper/scripted/frames.json` | 810127 | `3d27fd152aadcaf4b37b37997650ea74e37afe7e2bd5012bae7e3bc6caaef816` |
| `runs/model-player/t138-scripted/minesweeper/scripted/player.json` | 15602 | `c921e90cafddad311d28d96fccafbed514ddb214500a3f929bf94812ca2566e0` |
| `runs/model-player/t138-scripted/minesweeper/scripted/session.json` | 10391 | `72050c9638ca55cb554cd16263e3ae5a4f8fef42b9edb9b21502b718011cc947` |
| `runs/model-player/t138-scripted/minesweeper/scripted/steps.jsonl` | 135294 | `5c43c7d12b1e64f7a173ad2883875b7288f9345dfe93b4551cc6e0db8ea151b0` |
| `calls/**`（396 个文件，8187339 B）| — | `f750830cc98d1400059e40a4ffeb4ab6b36f508f2fc1d0de9472614c799a0d4a` |
| `frames/**`（37 个文件，580787 B）| — | `9763237e761455fb674b62b6adbcc58f15c304b2472e3873dadb735d7d4bdb16` |
| `states/**`（27 个文件，787285 B）| — | `e867ddd8376b426ae0f0f9f33ba18de1c3c815bb0e7a44be7295bc306ce0e10a` |

## t138-scripted / missilecommand / scripted

* 目录：`runs/model-player/t138-scripted/missilecommand/scripted`
* verdict：`PASS`（counts_as_pass=True，strict=PASS，baseline=PASS，game_side=PASS）
* 注入/接受后变化/rate：8 / 8 / 1.0
* 两窗对齐：3/8 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 4 frame(s))（matched 3/8，all_matched=False）
* ack 缺失步数：0
* 生成命令：

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t138-scripted/missilecommand/scripted/demo.png` | 108869 | `60b210600a2e3ddb16ccb8092f036b65d23566110a3b77c716fcfe3f937934bd` |
| `runs/model-player/t138-scripted/missilecommand/scripted/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t138-scripted/missilecommand/scripted/engine-game.stdout.txt` | 742 | `108e092cd106e6e1dac70a3e5de087d53dc59075a777eac68fce7b5f8fd47894` |
| `runs/model-player/t138-scripted/missilecommand/scripted/filmstrip.png` | 56306 | `5fff3de1a77b7398fc08197f66db8df38f0784c122767d5c12a0c051351e5332` |
| `runs/model-player/t138-scripted/missilecommand/scripted/frames.json` | 497414 | `5609de79f0eb0fb9282493248d0f2cecc424c5c514f511bfbf55f40ae3be10a4` |
| `runs/model-player/t138-scripted/missilecommand/scripted/player.json` | 13723 | `dee2a25761e012814fc200024cac0f639cd6cfecb9c44c9f8c575393a6fa8fc2` |
| `runs/model-player/t138-scripted/missilecommand/scripted/session.json` | 10322 | `04013dd71b1738614da581bb66dd02ab8b5a5454c4659ce9675dfdeabff24fa8` |
| `runs/model-player/t138-scripted/missilecommand/scripted/steps.jsonl` | 97054 | `d4f6a44ff4beea3961ae0a14c3a482d8f52b586d9fd30913d9a7b8fd71dd6bc6` |
| `calls/**`（376 个文件，6473918 B）| — | `f814a3b861a5b6d903feca351b990484747c74c57278266a309c125903a78f88` |
| `frames/**`（33 个文件，470880 B）| — | `a780fcb45bee457765586b55eacb4a6ce19076e3ddd9beb96352f0f06e40cfe4` |
| `states/**`（24 个文件，558921 B）| — | `41c51fe0ab1d92c7f41ad4427e9876a463d532dfe016b7759c4310dfb9d34bb6` |

## t138-scripted / pacman / scripted

* 目录：`runs/model-player/t138-scripted/pacman/scripted`
* verdict：`FAIL`（counts_as_pass=False，strict=FAIL，baseline=FAIL，game_side=FAIL）
* 注入/接受后变化/rate：12 / 7 / 0.5833
* 两窗对齐：4/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 6 frame(s))（matched 4/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t138-scripted/pacman/scripted/demo.png` | 146261 | `2cc6856fa5fb63a3ac71ea5c36d30e40e5b778de4675c34f96914cb9a76361e0` |
| `runs/model-player/t138-scripted/pacman/scripted/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t138-scripted/pacman/scripted/engine-game.stdout.txt` | 733 | `71f01958bca9e75f06728f18ab6f6800b15876b696d8dc74fe5ccbf934b0e9a4` |
| `runs/model-player/t138-scripted/pacman/scripted/filmstrip.png` | 146874 | `889c8b55347b4e8ebb9a5c7d98015b64eac09b169105d5192898e49cda287669` |
| `runs/model-player/t138-scripted/pacman/scripted/frames.json` | 583675 | `4ed5a0a430ba86df0a1950e03aaf821dd4c98204355f95a004f1e0b93efc07e2` |
| `runs/model-player/t138-scripted/pacman/scripted/player.json` | 14865 | `3a9bcd96cd1de5c035d50b0e44e0397a50f4a1341815e4e1ca5c22d10b70b078` |
| `runs/model-player/t138-scripted/pacman/scripted/session.json` | 10078 | `033a37ebaa84b88490ef69813ecbb1df9c8a18a15098394e39aacb690e3b5883` |
| `runs/model-player/t138-scripted/pacman/scripted/steps.jsonl` | 138495 | `a2b9a09ed73af9f01aed07db58dd1858c77dbac1eb623a15c1769f2942ff845b` |
| `calls/**`（406 个文件，10321045 B）| — | `b2e6a5ec8eaf88f63f8ec822a40f274b914d431511a1b070fe25cf3297e5d4a7` |
| `frames/**`（37 个文件，411185 B）| — | `6aa3c268b045f9e1829e372d3f40d1316ced8f3c45a585a63f32f2138945597f` |
| `states/**`（27 个文件，1153928 B）| — | `a32fa34c4bcdba59f0b904a71c0b53aa4198a68ea495161336dd6b84798c2a07` |

## t138-scripted / platformer / scripted

* 目录：`runs/model-player/t138-scripted/platformer/scripted`
* verdict：`INCONCLUSIVE`（counts_as_pass=False，strict=INCONCLUSIVE，baseline=INCONCLUSIVE，game_side=FAIL）
* 注入/接受后变化/rate：7 / 4 / 0.5714
* 两窗对齐：0/7 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 4 frame(s))（matched 0/7，all_matched=False）
* ack 缺失步数：0
* 生成命令：

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t138-scripted/platformer/scripted/demo.png` | 95253 | `888b342efa6301bd352ed452732dea7d769d870c4c1be2347ae29894150f8abd` |
| `runs/model-player/t138-scripted/platformer/scripted/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t138-scripted/platformer/scripted/engine-game.stdout.txt` | 796 | `987a20bedbe4a08cab6249a4694dae89b1b8fd85c09b36df99f15f517a9dcad8` |
| `runs/model-player/t138-scripted/platformer/scripted/filmstrip.png` | 65126 | `2f1e839eac5965a86bf7ad183f311863c31e3a56ff5c9a95d9af74f8d4e7d84e` |
| `runs/model-player/t138-scripted/platformer/scripted/frames.json` | 331469 | `027ba64af7399057f9f169e2171ee47ebc29a0f34800a55722703199607dada5` |
| `runs/model-player/t138-scripted/platformer/scripted/player.json` | 14815 | `d49cf9138010ffe4e03f28b0dd5e004f04751ecb02d8e8d12a998eaec2ccd710` |
| `runs/model-player/t138-scripted/platformer/scripted/session.json` | 10059 | `9684a19b2e873cc4d8486fce9db6879161f9887844c2875e52c151e32bf7908e` |
| `runs/model-player/t138-scripted/platformer/scripted/steps.jsonl` | 92436 | `c9c4fb6fee67cd14c33929ecffec77198cc62f4960e852202c6a80e7be0a016b` |
| `calls/**`（230 个文件，3556323 B）| — | `c9e9ede218261547d18e43f33c4699c35bdf231d5d5be358dc804e9bbc57c0e6` |
| `frames/**`（22 个文件，232753 B）| — | `7c6720bfea17bc80e21d04a0f7227d21f480f9638fa77cb2b820907bfa95929b` |
| `states/**`（17 个文件，365514 B）| — | `3662e8a0af3594718d1e75871b9eb4547642bdda5c4777ffd0afccabaf2a8cc2` |

## t138-scripted / pong / scripted

* 目录：`runs/model-player/t138-scripted/pong/scripted`
* verdict：`PASS`（counts_as_pass=True，strict=PASS，baseline=PASS，game_side=PASS）
* 注入/接受后变化/rate：10 / 10 / 1.0
* 两窗对齐：4/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 4 frame(s))（matched 4/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t138-scripted/pong/scripted/demo.png` | 62983 | `2dcec22573477bb738b2395e2cb91263fd03d26a76883befb632680613320901` |
| `runs/model-player/t138-scripted/pong/scripted/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t138-scripted/pong/scripted/engine-game.stdout.txt` | 4639 | `bc5a3b837b58c0ecae95622b2c6fb6efa2644d7eb1d17715a0550e79fe09f236` |
| `runs/model-player/t138-scripted/pong/scripted/filmstrip.png` | 52156 | `485b8c6088570a9c6db182329d55081ab050ad698c5eff9e1180a60465c3efb3` |
| `runs/model-player/t138-scripted/pong/scripted/frames.json` | 265682 | `8f6626cc0bca41772562f9205e56faa28df7118be0cf086abbcee76964b93143` |
| `runs/model-player/t138-scripted/pong/scripted/player.json` | 14827 | `8b4b064d3562526adbc8eff2ddcc5be420fc2ff553a2d377ea1d86394570b0d0` |
| `runs/model-player/t138-scripted/pong/scripted/session.json` | 10225 | `fb66676e85a182546a1ae21e8271d235a86efe16b862c0e0a573a7ae54c5592c` |
| `runs/model-player/t138-scripted/pong/scripted/steps.jsonl` | 143102 | `df7cd1a13fbe19b0c1a6c373d831ea1969fef21d62b36be7a47a3d87aad3a7c6` |
| `calls/**`（370 个文件，969517 B）| — | `aebf2f072ab91d186f7ab5d105e7b1e14db42442eef84f0b39b14c020a9f574c` |
| `frames/**`（37 个文件，172864 B）| — | `7a1436b004ee5d4bb5102fc877352cd1877e6790e12132d24229ff8c05a693d9` |
| `states/**`（27 个文件，66510 B）| — | `31fac415bb53cc541c5e869ab7fb16c0dd160257493549edc8dd36dc9400bc08` |

## t138-scripted / puzzlebobble / scripted

* 目录：`runs/model-player/t138-scripted/puzzlebobble/scripted`
* verdict：`PASS`（counts_as_pass=True，strict=PASS，baseline=PASS，game_side=PASS）
* 注入/接受后变化/rate：8 / 8 / 1.0
* 两窗对齐：2/8 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 5 frame(s))（matched 2/8，all_matched=False）
* ack 缺失步数：0
* 生成命令：

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t138-scripted/puzzlebobble/scripted/demo.png` | 138801 | `053c2cf9844abd98551f01dffdcd7f6238bafa1f1d74e7cfc753af9a63d49783` |
| `runs/model-player/t138-scripted/puzzlebobble/scripted/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t138-scripted/puzzlebobble/scripted/engine-game.stdout.txt` | 739 | `0cc64ccf537c796318c1c4e85adf902d1c768734e617038200fe7c411d37b872` |
| `runs/model-player/t138-scripted/puzzlebobble/scripted/filmstrip.png` | 83632 | `87d297d66adb426d0bc397b4e07c73ddaf11f871f4d185be485901f7ea1b4266` |
| `runs/model-player/t138-scripted/puzzlebobble/scripted/frames.json` | 481854 | `fafa70d80805bb8f6d3f0c72d7c479ec15c91f94c26f98d66feb85242379789b` |
| `runs/model-player/t138-scripted/puzzlebobble/scripted/player.json` | 13693 | `f57046ed7481a4d0d30d56a1451a2422c67a71cfc5f1a6e3fce33325e698c91a` |
| `runs/model-player/t138-scripted/puzzlebobble/scripted/session.json` | 10210 | `bdb23fd31fcda8a8237664123b3097569e18f6309299eb47b274c281df3cd6c4` |
| `runs/model-player/t138-scripted/puzzlebobble/scripted/steps.jsonl` | 97098 | `a4ebdf8d4d38caf21d56ce109ca940e17d9452de065d9832276eaef0b145a7d2` |
| `calls/**`（259 个文件，3825093 B）| — | `240f00f774a9c5d97e8402a6712fd53d8aefcdcc6f5655a6aa7f088c0756b4d2` |
| `frames/**`（25 个文件，343266 B）| — | `f69bd949bfb476e0bea0e3b4765fd2ced5ece8695e17edbe69638fa22a2f240b` |
| `states/**`（19 个文件，379481 B）| — | `6bc29ac62445471b2bb29096bbf4a91459111af02b0d60b58f6fd1885ed59a3a` |

## t138-scripted / rtype / scripted

* 目录：`runs/model-player/t138-scripted/rtype/scripted`
* verdict：`PASS`（counts_as_pass=True，strict=PASS，baseline=PASS，game_side=PASS）
* 注入/接受后变化/rate：8 / 8 / 1.0
* 两窗对齐：6/8 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 3 frame(s))（matched 6/8，all_matched=False）
* ack 缺失步数：0
* 生成命令：

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t138-scripted/rtype/scripted/demo.png` | 121101 | `c3dee8e7392808b32dac466cd1b9640632a4601c6dd6a3e32a4e5c96dd1637f6` |
| `runs/model-player/t138-scripted/rtype/scripted/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t138-scripted/rtype/scripted/engine-game.stdout.txt` | 743 | `f8f4e947219d02967787de0b3a607876e5a9afa694de8b45c75233704f8e0a9d` |
| `runs/model-player/t138-scripted/rtype/scripted/filmstrip.png` | 69669 | `683106576cac1eea836899958011ac7cfd92c6fe9d5f14025f2654134d2410d8` |
| `runs/model-player/t138-scripted/rtype/scripted/frames.json` | 430033 | `33e0938e35335f28774cbfd52e33409b132800a144b10680fc2a37186b49a8da` |
| `runs/model-player/t138-scripted/rtype/scripted/player.json` | 13684 | `40156955bb39034f21133684865f4ac606de5dc640b80ba47ee81a7ff734925f` |
| `runs/model-player/t138-scripted/rtype/scripted/session.json` | 10153 | `842e8c74e67fb73a38b4ce9805f874b8725040bbe5ef5b1dc819020be8cf5fd9` |
| `runs/model-player/t138-scripted/rtype/scripted/steps.jsonl` | 96494 | `700318014f52f794df308660a26f11e5f156cf9a1cbbcdfb4d0fcd292914b7b6` |
| `calls/**`（262 个文件，3580432 B）| — | `3f3982d904ee21a9c95bda6f4faabf477f15d001fcffae13147962549f8032e7` |
| `frames/**`（25 个文件，304656 B）| — | `61cff458221246219f69fb86081c0a350dfcf13d74a16fdf91a14c33d6c06d68` |
| `states/**`（19 个文件，351815 B）| — | `6f9508fa6fb67f1460b149618802b0ef4f80c11c19e640232e481e25c9f7f6cf` |

## t138-scripted / snake / scripted

* 目录：`runs/model-player/t138-scripted/snake/scripted`
* verdict：`PASS`（counts_as_pass=True，strict=PASS，baseline=PASS，game_side=PASS）
* 注入/接受后变化/rate：8 / 8 / 1.0
* 两窗对齐：0/8 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 5 frame(s))（matched 0/8，all_matched=False）
* ack 缺失步数：0
* 生成命令：

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t138-scripted/snake/scripted/demo.png` | 44762 | `927559e6d1ebbf56d445ad35bf310ba1a616beb8b70d41d088586b125932f37b` |
| `runs/model-player/t138-scripted/snake/scripted/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t138-scripted/snake/scripted/engine-game.stdout.txt` | 6323 | `ee72a7163e4fb1e69f61af5f6405a96262a081eded3aa77987161d8ec5299de8` |
| `runs/model-player/t138-scripted/snake/scripted/filmstrip.png` | 30716 | `10624087db10231db98f7a488d60c4a9d94932b051c83e813c01725bb2395993` |
| `runs/model-player/t138-scripted/snake/scripted/frames.json` | 126829 | `97ed12206a86e1fbbcbbe5a3ad02480a2178e961b0510416fa8fe36dbb674ffc` |
| `runs/model-player/t138-scripted/snake/scripted/player.json` | 13689 | `6371c959166caaea8291d1e20f85990d608293e343fd97ed6a7351d41a158c8b` |
| `runs/model-player/t138-scripted/snake/scripted/session.json` | 10782 | `8933cdf1d1f03272300e6e40afeeaefb5994aa32d117a6973c0776176db1f3d8` |
| `runs/model-player/t138-scripted/snake/scripted/steps.jsonl` | 102002 | `3694979acbfeb680ab073d80fedaf9d0fdb7a7e9ece9b508c97616703daa6937` |
| `calls/**`（206 个文件，1252558 B）| — | `b08bbda9f485b1ede9522a95e5d5ddb2701540c6b4df16777f23d9367be9c4a2` |
| `frames/**`（25 个文件，77380 B）| — | `3c93f7ffd6d30e1f73f7b796e8bd34cb58dcfdf3b2be887a1a4745fd1922b242` |
| `states/**`（19 个文件，166645 B）| — | `32f71e4b5146d0489db228a45fac09918ac8a7224ea634d185ac1a7afdccab87` |

## t138-scripted / sokoban / scripted

* 目录：`runs/model-player/t138-scripted/sokoban/scripted`
* verdict：`FAIL`（counts_as_pass=False，strict=FAIL，baseline=FAIL，game_side=FAIL）
* 注入/接受后变化/rate：12 / 9 / 0.75
* 两窗对齐：1/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 5 frame(s))（matched 1/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t138-scripted/sokoban/scripted/demo.png` | 139282 | `6da03e1b986b4e8d28bfb1d49fa60754892e2bd70fac322d13806807cc84c953` |
| `runs/model-player/t138-scripted/sokoban/scripted/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t138-scripted/sokoban/scripted/engine-game.stdout.txt` | 745 | `b7d12e202ad5bcd049feac54d6e95ebc68785271fc54889514d241fdddea347b` |
| `runs/model-player/t138-scripted/sokoban/scripted/filmstrip.png` | 107313 | `22f71c379de06c60d2abaefe078356f5413c6b07608869326e69fd633b7ae453` |
| `runs/model-player/t138-scripted/sokoban/scripted/frames.json` | 646768 | `7cd14641f320138f818678a86df79c3cd6b2d99b1e37bcf0e7c40b64ccac1648` |
| `runs/model-player/t138-scripted/sokoban/scripted/player.json` | 14786 | `0cc4c51f8bd42c82434c333fb7d1394f9388fdafc250b1e7460c72521892a92c` |
| `runs/model-player/t138-scripted/sokoban/scripted/session.json` | 10199 | `0fbbadd2cd45210bed2120bb436ab0463f1773b9c2563a70c74173097d6eb4ec` |
| `runs/model-player/t138-scripted/sokoban/scripted/steps.jsonl` | 144240 | `dd3d36bccb4a22082e5408dfac384ef6ef37c54706e00402b03c72c19c6479eb` |
| `calls/**`（389 个文件，4250522 B）| — | `25376dd15181e984773525c03e627795eb1ac0bdd94bce40ffbcc9812b028390` |
| `frames/**`（37 个文件，458340 B）| — | `c5aa8b529419dba5dd2fc3362ee8185287705c5624afa219ae301a96652efc07` |
| `states/**`（27 个文件，374446 B）| — | `a24cfab3f2cf40c65e3e6b8389a9e0e885b72db6edc142591d87817bed94a53b` |

## t138-scripted / spaceinvaders / scripted

* 目录：`runs/model-player/t138-scripted/spaceinvaders/scripted`
* verdict：`PASS`（counts_as_pass=True，strict=PASS，baseline=PASS，game_side=PASS）
* 注入/接受后变化/rate：8 / 8 / 1.0
* 两窗对齐：3/8 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 3 frame(s))（matched 3/8，all_matched=False）
* ack 缺失步数：0
* 生成命令：

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t138-scripted/spaceinvaders/scripted/demo.png` | 86285 | `b2a870945577c2f27f514ba1b9a336f29de4df8a907d8a771e18c09ab0886474` |
| `runs/model-player/t138-scripted/spaceinvaders/scripted/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t138-scripted/spaceinvaders/scripted/engine-game.stdout.txt` | 754 | `7a3fb781f85f4131100d1cd1018c9f63a9272c02e03220b73fa569947e23fdae` |
| `runs/model-player/t138-scripted/spaceinvaders/scripted/filmstrip.png` | 61618 | `4b8a39f231bca4a55769081243cf36a7d0c4cf4e08aa5337b0fddc8a8b883cd1` |
| `runs/model-player/t138-scripted/spaceinvaders/scripted/frames.json` | 349696 | `7ceebaf9200626cea388e6a8ecf04c02f91248448b0d7a2b4c9ec7772db070b2` |
| `runs/model-player/t138-scripted/spaceinvaders/scripted/player.json` | 13705 | `9c98bcbb31f8a4f6c0a6be79ba549ece494fc90b96956fb762334784f95a2edc` |
| `runs/model-player/t138-scripted/spaceinvaders/scripted/session.json` | 10122 | `359857f8dda0442d8400ea3b1247f15e9796028b235175c51ce59a8bb4a060eb` |
| `runs/model-player/t138-scripted/spaceinvaders/scripted/steps.jsonl` | 97053 | `50456ff9bea5a494b2fddd014ca1e57d1dd75b5d9df0ec5b2f8d10caf68e013c` |
| `calls/**`（266 个文件，1955207 B）| — | `21861f7fb5394c6b3eff73beb5fdc249b27754fcd76728d0b7ceecc04f04bf0e` |
| `frames/**`（25 个文件，244113 B）| — | `4b715871cbdf5b1ab0ce928585b61db780c0be6e84d13b9d2bcbd06933705f6f` |
| `states/**`（19 个文件，169510 B）| — | `d7305931c83da57556373fdc9282969f125c7d4d34c22894ddf631f5ceb1dbd8` |

## t138-scripted / tetris / scripted

* 目录：`runs/model-player/t138-scripted/tetris/scripted`
* verdict：`PASS`（counts_as_pass=True，strict=PASS，baseline=PASS，game_side=PASS）
* 注入/接受后变化/rate：8 / 8 / 1.0
* 两窗对齐：4/8 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 4 frame(s))（matched 4/8，all_matched=False）
* ack 缺失步数：0
* 生成命令：

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t138-scripted/tetris/scripted/demo.png` | 51413 | `9118b686ea7a721eaae3fd2474eab91fce394e3ea814a1607c80add8241407d8` |
| `runs/model-player/t138-scripted/tetris/scripted/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t138-scripted/tetris/scripted/engine-game.stdout.txt` | 5842 | `01d7f573bce2b8a60b69c4b52030190f027c8d4df45976c2a4557fcaeb324d21` |
| `runs/model-player/t138-scripted/tetris/scripted/filmstrip.png` | 34096 | `cd85452d53a798b699c464c46417fdb682402fee602c4cac11ccb69e3654cb38` |
| `runs/model-player/t138-scripted/tetris/scripted/frames.json` | 195913 | `f7e3fbc88b2b312602ffa222723701e2eb63870a92168de4f7e49f675378ece9` |
| `runs/model-player/t138-scripted/tetris/scripted/player.json` | 13773 | `933cbe60716dd5ea2b053abcdc988507532cc99246da9b6cf98191d869f230d7` |
| `runs/model-player/t138-scripted/tetris/scripted/session.json` | 10007 | `a79781ed582ea4cb0c8e838572ed5fea5c1621e6a5f536c193ea3d40614ded55` |
| `runs/model-player/t138-scripted/tetris/scripted/steps.jsonl` | 85901 | `1a44a88f61d7b2b65efcf0271851d775a4c6460a424a9fc060a50f31ba119e21` |
| `calls/**`（270 个文件，558849 B）| — | `8001ec72036f2c037f89528003d7789f18a49b1ad4c3324d0931cda24bc9707c` |
| `frames/**`（25 个文件，128882 B）| — | `2776fabd6859a1ff8fbdcd1e4f4e901cddea5b3120bac19607d1876fab734fe7` |
| `states/**`（19 个文件，29822 B）| — | `634c99ec4bb2f1cd3e2da56cd6a3f453184bd44515700148445a8168fd33f708` |

## t138-scripted / towerdefense / scripted

* 目录：`runs/model-player/t138-scripted/towerdefense/scripted`
* verdict：`INCONCLUSIVE`（counts_as_pass=False，strict=INCONCLUSIVE，baseline=INCONCLUSIVE，game_side=FAIL）
* 注入/接受后变化/rate：12 / 9 / 0.75
* 两窗对齐：6/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 3 frame(s))（matched 6/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t138-scripted/towerdefense/scripted/demo.png` | 163710 | `08abefc40f3a17da4bd12596e00af8370327de85fdc94128a6ca274eaf882130` |
| `runs/model-player/t138-scripted/towerdefense/scripted/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t138-scripted/towerdefense/scripted/engine-game.stdout.txt` | 753 | `7b9c9346b115410e888a6c4ef0d63d0aa1378d1a63aa5dce4aac8f70cee5c043` |
| `runs/model-player/t138-scripted/towerdefense/scripted/filmstrip.png` | 131272 | `a99807424101d51b52c9b7906e2bf78e57d52e95b8b0cc6de12da8a3c2f9e22b` |
| `runs/model-player/t138-scripted/towerdefense/scripted/frames.json` | 637829 | `4a9376e908b6f6be7cfd0366501f82cb0bc314b932eead31f934b8ce6d0d658c` |
| `runs/model-player/t138-scripted/towerdefense/scripted/player.json` | 15573 | `7175fac843433c6fd50f0f8c191215deab06a109efd0a39683d681a2511778ba` |
| `runs/model-player/t138-scripted/towerdefense/scripted/session.json` | 10351 | `c71cdb93e6809d86e95d1c1a860a6f5687990982d8aa927465f27d3ca5ab2b5a` |
| `runs/model-player/t138-scripted/towerdefense/scripted/steps.jsonl` | 134814 | `4f9e7b7a14aef30c4298fd4ae6d5673f9f6c5352feb2f19889e34860218b3caa` |
| `calls/**`（378 个文件，6411441 B）| — | `4677e7ba3054c674fa6aab815b57669499655bdd1618587b7766a748cb6d057a` |
| `frames/**`（37 个文件，451587 B）| — | `9ad77795960236667d74900d63ebf25ae22541b389f6b3c75145f8a637c21784` |
| `states/**`（27 个文件，648200 B）| — | `ca2f3f973ba0c2c4ffa67d46469ee67d4e7943bb2f2a846b1a1020bcd553f9e1` |

## t138-jev-v3 / asteroids / jev

* 目录：`runs/model-player/t138-jev-v3/asteroids/jev`
* verdict：`FAIL`（counts_as_pass=False，strict=FAIL，baseline=FAIL，game_side=None）
* 注入/接受后变化/rate：12 / 4 / 0.3333
* 两窗对齐：4/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 4 frame(s))（matched 4/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe runs\model-player\_scripts\t138_step_table.py t138-jev-v3 asteroids jev`  <- t136_commands.jsonl
  * `D:\Anaconda\python.exe -c import io,json;d=r'runs/model-player';import os
for pre,arm,g in (('t138-jev-v3','jev','tetris'),('t138-jev-v3','jev','asteroids'),('t138-jev-v3','jev','pong')):
 p=os.path.join(d,pre,g,arm,'player.json');s=json.load(io.open(p,encoding='utf-8'))
 print(pre,g,s.get('verdict'),'injected',s.get('injected_steps'),'changed',s.get('changed_steps_of_accepted'),'rate',s.get('accepted_and_changed_rate'),'strict_fail',s.get('strict_fail_steps'),'fixed',s.get('MODEL_FIXED_POINT'),'noprog',s.get('MODEL_NO_PROGRESS'),'one_action_loop',s.get('one_action_loop'),'ack_missing',(s.get('ack_missing') or {}).get('count'),'align',(s.get('frame_alignment') or {}).get('reading'))`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t138-jev-v3/asteroids/jev/demo.png` | 118720 | `efbcee93e14f5af05bfa7a136eb17538c6db8267b1ef61c3007f0432e70e20e9` |
| `runs/model-player/t138-jev-v3/asteroids/jev/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t138-jev-v3/asteroids/jev/engine-game.stdout.txt` | 741 | `d99cb4bd66cb1f6d9d16c75c722d8c7b85aa754fb6e49f3aaf0d4e1e662b5905` |
| `runs/model-player/t138-jev-v3/asteroids/jev/filmstrip.png` | 70904 | `9988634a347822619e968776642c53709ba849b38dd0beb538013adc36137931` |
| `runs/model-player/t138-jev-v3/asteroids/jev/frames.json` | 539083 | `4fe4fc956c755dbca78e5452325b053aae8eeb2388c5b2acf84e26f26a2f19df` |
| `runs/model-player/t138-jev-v3/asteroids/jev/player.json` | 236365 | `aa3b9b07d189e814933296a73867fbe67ea7fa7ab3d49c7c4e4360fda1abfafa` |
| `runs/model-player/t138-jev-v3/asteroids/jev/session.json` | 9985 | `2eb249d6b0bc6f43f101701d639c6fdb266dc0f26985f581b67bf3567f37610d` |
| `runs/model-player/t138-jev-v3/asteroids/jev/steps.jsonl` | 148502 | `06f783f34c5b9278754d7086cfc137dc8cf01cb5e9cf0464363e252f32e7c638` |
| `calls/**`（395 个文件，1391899 B）| — | `2cb6f6dc0d71a8b7b5c5460b02024651c0ead5fc4dc91b7cdff5a26d42bfa742` |
| `frames/**`（37 个文件，377786 B）| — | `e8cff1e22c5c999cb15ab0298df8e30dbfb74ba826d80e309274f9e00c4755fb` |
| `states/**`（27 个文件，77197 B）| — | `106a820c0d7411ccebc0a07b5b096988f6cab684835b1ccb425be6948cfbc254` |

## t138-jev-v3 / pong / jev

* 目录：`runs/model-player/t138-jev-v3/pong/jev`
* verdict：`FAIL`（counts_as_pass=False，strict=FAIL，baseline=FAIL，game_side=None）
* 注入/接受后变化/rate：12 / 7 / 0.5833
* 两窗对齐：4/12 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 4 frame(s))（matched 4/12，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe runs\model-player\_scripts\t138_step_table.py t138-jev-v3 pong jev`  <- t136_commands.jsonl
  * `D:\Anaconda\python.exe -c import io,json;d=r'runs/model-player';import os
for pre,arm,g in (('t138-jev-v3','jev','tetris'),('t138-jev-v3','jev','asteroids'),('t138-jev-v3','jev','pong')):
 p=os.path.join(d,pre,g,arm,'player.json');s=json.load(io.open(p,encoding='utf-8'))
 print(pre,g,s.get('verdict'),'injected',s.get('injected_steps'),'changed',s.get('changed_steps_of_accepted'),'rate',s.get('accepted_and_changed_rate'),'strict_fail',s.get('strict_fail_steps'),'fixed',s.get('MODEL_FIXED_POINT'),'noprog',s.get('MODEL_NO_PROGRESS'),'one_action_loop',s.get('one_action_loop'),'ack_missing',(s.get('ack_missing') or {}).get('count'),'align',(s.get('frame_alignment') or {}).get('reading'))`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t138-jev-v3/pong/jev/demo.png` | 75505 | `3f9ac91deb33feee13fa2734a7120a8506cb9629e1c2320255ff09e8eca852e9` |
| `runs/model-player/t138-jev-v3/pong/jev/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t138-jev-v3/pong/jev/engine-game.stdout.txt` | 4818 | `97718f3a63ecad319ca2e766c1f2011c80ebce25be4d7565c474ca7df236ab09` |
| `runs/model-player/t138-jev-v3/pong/jev/filmstrip.png` | 50481 | `8bdb50a31eff86404a46d6b2c09d859f78ee02770435d1afcedabf281bbc1fe7` |
| `runs/model-player/t138-jev-v3/pong/jev/frames.json` | 240558 | `97dee6b678ed8ced37c0f6b7f97a7c25785738b52c9688e56b1c7f321b88051c` |
| `runs/model-player/t138-jev-v3/pong/jev/player.json` | 144721 | `f5acd6be364b49f9f2aff6f49b6d24ad1b0ad6cf3704ac5a74d4994955f7ef18` |
| `runs/model-player/t138-jev-v3/pong/jev/session.json` | 10126 | `b3f065ab657a9402c31ae5198eb18dbc9a96dbe8f28ad885d0285ee09f6550c1` |
| `runs/model-player/t138-jev-v3/pong/jev/steps.jsonl` | 156345 | `8a5d791b49d9774f24471d480e36b2732fd429015afeb668a486fcf87f123324` |
| `calls/**`（390 个文件，973699 B）| — | `301a6d7cb8040355f507e2cee3e8573be164a59413dd3923aaadb8518dc0621b` |
| `frames/**`（37 个文件，154213 B）| — | `86d74054db01e17c1fa1af6be17e26c3057ea08414ff6b8b3522e6ea20c8c6f8` |
| `states/**`（27 个文件，66097 B）| — | `d548589a072b92de70f289a1533e5d90818b54af5296145b8f1b0041f2f716fa` |

## t138-jev-v3 / tetris / jev

* 目录：`runs/model-player/t138-jev-v3/tetris/jev`
* verdict：`PASS`（counts_as_pass=True，strict=PASS，baseline=PASS，game_side=None）
* 注入/接受后变化/rate：8 / 8 / 1.0
* 两窗对齐：1/8 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 4 frame(s))（matched 1/8，all_matched=False）
* ack 缺失步数：0
* 生成命令：
  * `D:\Anaconda\python.exe -c import io,json;d=r'runs/model-player';import os
for pre,arm,g in (('t138-jev-v3','jev','tetris'),('t138-jev-v3','jev','asteroids'),('t138-jev-v3','jev','pong')):
 p=os.path.join(d,pre,g,arm,'player.json');s=json.load(io.open(p,encoding='utf-8'))
 print(pre,g,s.get('verdict'),'injected',s.get('injected_steps'),'changed',s.get('changed_steps_of_accepted'),'rate',s.get('accepted_and_changed_rate'),'strict_fail',s.get('strict_fail_steps'),'fixed',s.get('MODEL_FIXED_POINT'),'noprog',s.get('MODEL_NO_PROGRESS'),'one_action_loop',s.get('one_action_loop'),'ack_missing',(s.get('ack_missing') or {}).get('count'),'align',(s.get('frame_alignment') or {}).get('reading'))`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t138-jev-v3/tetris/jev/demo.png` | 74346 | `d19479a96f06300a29de029494ea40a8df270cb1f4e844653b0f7ec712b04ec2` |
| `runs/model-player/t138-jev-v3/tetris/jev/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t138-jev-v3/tetris/jev/engine-game.stdout.txt` | 6942 | `326ee124f57ecec8f0c6eaf8c5b1ba01039d98482c396fd286401ba0535bf960` |
| `runs/model-player/t138-jev-v3/tetris/jev/filmstrip.png` | 43424 | `3066725330309646e4c60639fa87a0b2e4b5c9ccf66f1e0f99709a8017fe3b7b` |
| `runs/model-player/t138-jev-v3/tetris/jev/frames.json` | 199535 | `8b93d24cc26580199f633f0f6850f91d31aa3732833346ef9f1c696fc42ed4cc` |
| `runs/model-player/t138-jev-v3/tetris/jev/player.json` | 109538 | `98b2cff7b5778979287fce2fb1979af3d70434d8bbd19cc5f156feaf432cc9c4` |
| `runs/model-player/t138-jev-v3/tetris/jev/session.json` | 9906 | `1cd694747e8a04e6cbaed9e7033ccccf9af7a6c36900e32b32990a9985fd4e6d` |
| `runs/model-player/t138-jev-v3/tetris/jev/steps.jsonl` | 97291 | `2bec97910b2ca275935ddc30c383912ada42ca640ddea101a9dca3bb328fff82` |
| `calls/**`（263 个文件，556150 B）| — | `f1ad4f26e987d5f2faf582925a1177a6856260169b40457b9423413d09cf7e5d` |
| `frames/**`（25 个文件，131740 B）| — | `9d7bc7a701f047b1b20d7b2d8df3c7d63c630de7c5ff8474be02dfa8d230e58c` |
| `states/**`（19 个文件，30296 B）| — | `8c4933162ae3c2f20b410367721f3c19b8627c52a8cb85a3525c8bb53e4ff305` |

## t138-repeat-1 / asteroids / scripted

* 目录：`runs/model-player/t138-repeat-1/asteroids/scripted`
* verdict：`PASS`（counts_as_pass=True，strict=PASS，baseline=PASS，game_side=PASS）
* 注入/接受后变化/rate：8 / 8 / 1.0
* 两窗对齐：4/8 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 3 frame(s))（matched 4/8，all_matched=False）
* ack 缺失步数：0
* 生成命令：

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t138-repeat-1/asteroids/scripted/demo.png` | 88809 | `977faf8b529857d05d23884d422c618bddc58d65c1f56d40d521bc57f4a0f70c` |
| `runs/model-player/t138-repeat-1/asteroids/scripted/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t138-repeat-1/asteroids/scripted/engine-game.stdout.txt` | 741 | `213716a95ecfe2dd74912f6d31a13a677ca0790a05b0d36da080c2eb447be5d6` |
| `runs/model-player/t138-repeat-1/asteroids/scripted/filmstrip.png` | 51813 | `f7816c9ecc0a763e06d2bf48732e2e2659ee42623ca12c0a94dfdf6324bde8c0` |
| `runs/model-player/t138-repeat-1/asteroids/scripted/frames.json` | 375527 | `61c9936ac9c767b5ec84840284492c54b95120cfbd5f82d08fae8e9f7eae2a9f` |
| `runs/model-player/t138-repeat-1/asteroids/scripted/player.json` | 13713 | `35cb15782cb4f982f149f1c4460f40671eeecff935e10abe881d00b059ba5e6c` |
| `runs/model-player/t138-repeat-1/asteroids/scripted/session.json` | 10092 | `fa2b1817f9192172512c05ab6b623f3f799ed9f5f471e63ddda0010ba04b0a99` |
| `runs/model-player/t138-repeat-1/asteroids/scripted/steps.jsonl` | 102850 | `63bc612b583baf2edca0a031a2f1c9602fb250eff6c02a52336ec98f8fb8a180` |
| `calls/**`（272 个文件，998052 B）| — | `1fd16ae989cd3bbaa1f018a7f272c84001fd5eeaaf9e521a8924e8596ed9668e` |
| `frames/**`（25 个文件，263608 B）| — | `e94a30307b828a0ba00c34fd54a7a9ee20224a4554a54ee63ef8dfcd9fce953b` |
| `states/**`（19 个文件，56434 B）| — | `c3e637194a430c5efc58a94042c89fadc43aecfe166ad2011da9be772f21e794` |

## t138-repeat-2 / asteroids / scripted

* 目录：`runs/model-player/t138-repeat-2/asteroids/scripted`
* verdict：`PASS`（counts_as_pass=True，strict=PASS，baseline=PASS，game_side=PASS）
* 注入/接受后变化/rate：8 / 8 / 1.0
* 两窗对齐：2/8 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 5 frame(s))（matched 2/8，all_matched=False）
* ack 缺失步数：0
* 生成命令：

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t138-repeat-2/asteroids/scripted/demo.png` | 88007 | `7b7a1a52abe26ef2d6708c06deb63a33aa4d315b9b41e3d50ea9525f279cea62` |
| `runs/model-player/t138-repeat-2/asteroids/scripted/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t138-repeat-2/asteroids/scripted/engine-game.stdout.txt` | 741 | `213716a95ecfe2dd74912f6d31a13a677ca0790a05b0d36da080c2eb447be5d6` |
| `runs/model-player/t138-repeat-2/asteroids/scripted/filmstrip.png` | 51152 | `51628140d7ed70251fb4a91e177b490d40da45a815504f5220fce5783f66e28a` |
| `runs/model-player/t138-repeat-2/asteroids/scripted/frames.json` | 373753 | `37d5f07de3bbe2fcc101ee461c23dad239313692589cf1feb4061e6a4365a022` |
| `runs/model-player/t138-repeat-2/asteroids/scripted/player.json` | 13714 | `5e1f619b4f66033779ede797cee753a34d50fd58c4ef0711d2233df518bfafa6` |
| `runs/model-player/t138-repeat-2/asteroids/scripted/session.json` | 10090 | `54dc35d95354327c5fa6ede049e100cf5f0d9a79b414fbb627087ef6b5841535` |
| `runs/model-player/t138-repeat-2/asteroids/scripted/steps.jsonl` | 102794 | `06cb5e8ca3ec59ee954e16fad46f47c38710a43bf3cffafcdd3afba0f97d3140` |
| `calls/**`（272 个文件，997469 B）| — | `41b266808641f346ae63de1b742af7b302b174fc0f5efa7a472addebe525874d` |
| `frames/**`（25 个文件，262275 B）| — | `ed342f3d448818037389f7174b66f584deebf88d28e9d1cbb469c7a073048dd5` |
| `states/**`（19 个文件，56358 B）| — | `c2e8634d20a5b2b4e1ca0568d117514d0c2b5cff386eec8e36147d25ddf950f6` |

## t138-repeat-3 / asteroids / scripted

* 目录：`runs/model-player/t138-repeat-3/asteroids/scripted`
* verdict：`PASS`（counts_as_pass=True，strict=PASS，baseline=PASS，game_side=PASS）
* 注入/接受后变化/rate：8 / 8 / 1.0
* 两窗对齐：4/8 steps have the two windows on the SAME achieved drawn-frame count (max |residual| = 3 frame(s))（matched 4/8，all_matched=False）
* ack 缺失步数：0
* 生成命令：

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t138-repeat-3/asteroids/scripted/demo.png` | 88436 | `6fc8fe0e154fce40b4517e72e775f85a82324af7943bea1953a0f527838924d1` |
| `runs/model-player/t138-repeat-3/asteroids/scripted/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t138-repeat-3/asteroids/scripted/engine-game.stdout.txt` | 741 | `213716a95ecfe2dd74912f6d31a13a677ca0790a05b0d36da080c2eb447be5d6` |
| `runs/model-player/t138-repeat-3/asteroids/scripted/filmstrip.png` | 51449 | `1adb92300284c87b9ffed1769028284c16df197d88dbacb1ac37445431c02ac6` |
| `runs/model-player/t138-repeat-3/asteroids/scripted/frames.json` | 374732 | `69b3bbb83c983dac949b70c9db6c7e4f9bec1f4e10023292ecaa0a91b3d80a1a` |
| `runs/model-player/t138-repeat-3/asteroids/scripted/player.json` | 13711 | `3afa31e4b8e286f51bf77373d3a111686b5c8a9b290951e2b2ddc84d0fce35a5` |
| `runs/model-player/t138-repeat-3/asteroids/scripted/session.json` | 10089 | `164d5ec932dfb05b37d8db2c1f6c59812eb906ad89d0f79670cd671af9ae3f03` |
| `runs/model-player/t138-repeat-3/asteroids/scripted/steps.jsonl` | 102973 | `db449238978cb3324106f42a86c450c0df61dab079ff1115325931e650f44ab6` |
| `calls/**`（258 个文件，956341 B）| — | `4cf7e2e18dd4068f68db7ea183b2fab10ba3ee160e7c4fc2e90aef109271ad9b` |
| `frames/**`（25 个文件，263006 B）| — | `378cfa597e1021a43e33eff86931cfc8298261227db3e29822b1de5a3b3ccede` |
| `states/**`（19 个文件，56460 B）| — | `dcbee1e302c3d4e824158b54d2b7a2d4636af3c4f1c3eef1b95def1f8b4069a9` |

## t138-oldctl / asteroids / scripted

* 目录：`runs/model-player/t138-oldctl/asteroids/scripted`
* verdict：`PASS`（counts_as_pass=True，strict=PASS，baseline=PASS，game_side=PASS）
* 注入/接受后变化/rate：8 / 8 / 1.0
* 两窗对齐：None（matched None/None，all_matched=None）
* ack 缺失步数：None
* 生成命令：
  * `D:\Anaconda\python.exe runs\model-player\t138-oldcode\playtest_player_HEAD.py run --game asteroids --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9954 --out-prefix t138-oldctl`  <- t136_commands.jsonl
  * `D:\Anaconda\python.exe tools\_t138_tmp_playtest_player_HEAD.py run --game asteroids --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9954 --out-prefix t138-oldctl`  <- t136_commands.jsonl
  * `D:\Anaconda\python.exe tools\_t138_tmp_playtest_player_HEAD.py run --game asteroids --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9954 --out-prefix t138-oldctl2`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t138-oldctl/asteroids/scripted/demo.png` | 89050 | `24b2116cbd3e90206486d9083907f2c19a0eef3919452ba445a753881289c016` |
| `runs/model-player/t138-oldctl/asteroids/scripted/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t138-oldctl/asteroids/scripted/engine-game.stdout.txt` | 741 | `5b146904b1de99c94fb1bacaf4b7823aed4571caa3793443247118230d31e003` |
| `runs/model-player/t138-oldctl/asteroids/scripted/filmstrip.png` | 51942 | `2289625e6c053b133877f62e3042ab01a8cf48c6270506491f811e1326d25691` |
| `runs/model-player/t138-oldctl/asteroids/scripted/frames.json` | 375666 | `351973da24ed204e8c09fffbe37bde143dc1bf24e68b6718da9330d5f6662390` |
| `runs/model-player/t138-oldctl/asteroids/scripted/player.json` | 9390 | `3caaa54c1d8df3ca728a91209bfc45d5784e97d85d4147e9eafda5ea4c4d0197` |
| `runs/model-player/t138-oldctl/asteroids/scripted/session.json` | 8840 | `3c21f56d8ec9e09d3a3d791cc228d93abd377bd8b67d963a13572345d11c7e67` |
| `runs/model-player/t138-oldctl/asteroids/scripted/steps.jsonl` | 86504 | `98d53c428e848a9d34aeaa2a1381f0a77ca70c60d491c0521d9ddf52b2141ffa` |
| `calls/**`（108 个文件，550678 B）| — | `274cd14f225f9fccd4c1ddc7e7529b639beaaa624361bde18188343e0a55d53d` |
| `frames/**`（25 个文件，263775 B）| — | `6fbeda47c045bd342ede7ad02d766af566316650aa548bf3946f301400981e6e` |
| `states/**`（19 个文件，56682 B）| — | `104488bee9c8d7cdb4e291e759fbde5ad67789b4b576e60f879643bb96181d04` |

## t138-oldctl2 / asteroids / scripted

* 目录：`runs/model-player/t138-oldctl2/asteroids/scripted`
* verdict：`PASS(baseline only)`（counts_as_pass=False，strict=FAIL，baseline=PASS，game_side=FAIL）
* 注入/接受后变化/rate：12 / 10 / 0.8333
* 两窗对齐：None（matched None/None，all_matched=None）
* ack 缺失步数：None
* 生成命令：
  * `D:\Anaconda\python.exe tools\_t138_tmp_playtest_player_HEAD.py run --game asteroids --backend scripted --player scripted --variant V1 --image-form full --steps 12 --port 9954 --out-prefix t138-oldctl2`  <- t136_commands.jsonl

| 文件 | 大小(B) | sha256 |
|---|---|---|
| `runs/model-player/t138-oldctl2/asteroids/scripted/demo.png` | 109333 | `73ab26b6f687466b1098817d27a709c68445aa46427156f31681e020efda846b` |
| `runs/model-player/t138-oldctl2/asteroids/scripted/engine-game.stderr.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `runs/model-player/t138-oldctl2/asteroids/scripted/engine-game.stdout.txt` | 741 | `5b146904b1de99c94fb1bacaf4b7823aed4571caa3793443247118230d31e003` |
| `runs/model-player/t138-oldctl2/asteroids/scripted/filmstrip.png` | 77072 | `8e65a8691b67e5663ea399a382cadfdc3d23256528b017aeb81bca7f390bcae9` |
| `runs/model-player/t138-oldctl2/asteroids/scripted/frames.json` | 548842 | `73f0c0063333cf41a085aca8d9c6f6e6104d55140116c730c365392651fc6158` |
| `runs/model-player/t138-oldctl2/asteroids/scripted/player.json` | 11046 | `3aeec386a1ffe595d27e37d6b761358eda95cff1ef8c435858f1e11ff426e850` |
| `runs/model-player/t138-oldctl2/asteroids/scripted/session.json` | 8842 | `f0f5d45b670ff8281a1cf60eff030582404b8b9f8d48c78b5d12ac7d3d9245e2` |
| `runs/model-player/t138-oldctl2/asteroids/scripted/steps.jsonl` | 137098 | `62bdbc020946f32672b085760d6cafe0ae82de43a4f6c0426f3e7f325ba1437c` |
| `calls/**`（162 个文件，796190 B）| — | `812f55694775ddedc80548211aaa1b86f2962731d7d4924250b47392f3712437` |
| `frames/**`（37 个文件，384979 B）| — | `3e1a493ba98c3781260defea83c88ff9f6e51d6a1b90d06493b7fe9043eb0f5e` |
| `states/**`（27 个文件，79363 B）| — | `bfb4c4600f94ec82ec1b23e280cbe2ab7b37fc460852b4beee073ce9e844c0bf` |
