@echo off
REM TASK-116: declare the InputMap actions the games' own code (or their new player
REM controls) need, and move the headless-test actions off the player's keys.
REM Every command is a python invocation of recovery\work\task116\*.py with --apply.
setlocal
set PY=python
set ROOT=F:\moonbit-hof-rs\godot-mcp
set W=%ROOT%\recovery\work\task116

echo == D2: actions the code already reads but the InputMap never declared
%PY% "%W%\add_input_action.py" bomberman bomb_left 65 --apply
%PY% "%W%\add_input_action.py" bomberman bomb_down 83 --apply
%PY% "%W%\add_input_action.py" sokoban soko_left 65 --apply
%PY% "%W%\add_input_action.py" sokoban soko_down 83 --apply

echo == D3: player controls the games were missing
%PY% "%W%\add_input_action.py" lunarlander ll_rotate_left 65 --apply
%PY% "%W%\add_input_action.py" lunarlander ll_rotate_right 68 --apply
%PY% "%W%\add_input_action.py" rtype rt_left 65 --apply
%PY% "%W%\add_input_action.py" rtype rt_right 68 --apply
%PY% "%W%\add_input_action.py" rtype rt_up 87 --apply
%PY% "%W%\add_input_action.py" rtype rt_down 83 --apply
%PY% "%W%\add_input_action.py" puzzlebobble pb_left 65 --apply
%PY% "%W%\add_input_action.py" puzzlebobble pb_right 68 --apply
%PY% "%W%\add_input_action.py" match3 m3_up 87 --apply
%PY% "%W%\add_input_action.py" match3 m3_down 83 --apply
%PY% "%W%\add_input_action.py" match3 m3_swap 32 --apply
%PY% "%W%\add_input_action.py" minesweeper mine_left 65 --apply
%PY% "%W%\add_input_action.py" minesweeper mine_right 68 --apply
%PY% "%W%\add_input_action.py" minesweeper mine_up 87 --apply
%PY% "%W%\add_input_action.py" minesweeper mine_down 83 --apply
%PY% "%W%\add_input_action.py" minesweeper mine_reveal 32 --apply
%PY% "%W%\add_input_action.py" minesweeper mine_flag 70 --apply
%PY% "%W%\add_input_action.py" missilecommand mc_left 65 --apply
%PY% "%W%\add_input_action.py" missilecommand mc_right 68 --apply
%PY% "%W%\add_input_action.py" missilecommand mc_fire 32 --apply
%PY% "%W%\add_input_action.py" towerdefense td_left 65 --apply
%PY% "%W%\add_input_action.py" towerdefense td_right 68 --apply
%PY% "%W%\add_input_action.py" towerdefense td_up 87 --apply
%PY% "%W%\add_input_action.py" towerdefense td_down 83 --apply
%PY% "%W%\add_input_action.py" towerdefense td_place 32 --apply

echo == move the headless-test actions off the player's keys
%PY% "%W%\set_input_key.py" match3 m3_auto_move 71
%PY% "%W%\set_input_key.py" missilecommand mc_auto_fire 71
%PY% "%W%\set_input_key.py" towerdefense td_auto_step 71
%PY% "%W%\set_input_key.py" minesweeper mine_flag_next 71
echo == done
endlocal
