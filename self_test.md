```bash
# ===== Step 0: Set up the environment / 步骤 0：准备环境 =====
# (activate in every new terminal / 每打开一个新终端都要先激活)
cd your-repo-folder              # 进入你的仓库目录
python3 -m venv .venv            # create a virtual environment / 创建虚拟环境
source .venv/bin/activate        # (.venv) appears in the prompt / 成功后提示符前出现 (.venv)
make install                     # install flake8 mypy pytest build / 安装这四个工具

# The repo must contain at least / 仓库里至少要有这些文件:
#   a_maze_ing.py  display.py  config.txt  Makefile  README.md  LICENSE.md
#   pyproject.toml  .gitignore  .flake8  mypy.ini
#   mazegen/__init__.py  mazegen/generator.py  test/test_maze.py
# Default config.txt (required in the repo) / 默认配置 config.txt（项目要求仓库里必须有）:
#   WIDTH=20
#   HEIGHT=15
#   ENTRY=0,0
#   EXIT=19,14
#   OUTPUT_FILE=maze.txt
#   PERFECT=True
#   SEED=42

# ===== Step 1: Automated tests / 步骤 1：自动测试 =====
make test                        # same as python3 -m pytest / 等于 python3 -m pytest
python3 -m pytest -x -v          # stop at the first failure, verbose / 只看第一个失败的详细信息

# ===== Step 2: Run the program by hand / 步骤 2：手动运行程序 =====
make run                         # same as python3 a_maze_ing.py config.txt
# In the menu press 2, 3, 4, 1, then type abc and an empty line, finally 5 to quit
# 菜单里依次按 2, 3, 4, 1，然后输入 abc、空行，最后按 5 退出
cat maze.txt                     # check: hex rows, empty line, entry, exit, path
                                 # 检查：十六进制行、空行、入口、出口、路径

# ===== Step 3: Break the config on purpose (must not crash) =====
# ===== 步骤 3：故意把配置写坏（程序不能崩溃）=====
printf 'WIDTH=abc\n' > bad.txt
python3 a_maze_ing.py bad.txt;     echo "exit code: $?"   # expect "Error: ..." and 1 / 应该是 Error: ... 和 1
python3 a_maze_ing.py nofile.txt;  echo "exit code: $?"   # missing file / 文件不存在
python3 a_maze_ing.py;             echo "exit code: $?"   # no argument -> Usage / 没有参数 -> Usage
rm bad.txt

# ===== Step 4: Official analyzer / 步骤 4：官方分析脚本 =====
python3 maze_analyzer.py --help  # see its options first, then check maze.txt
                                 # 先看它支持哪些参数，再检查 maze.txt
# Generate once with PERFECT=True and once with PERFECT=False and check both
# 分别用 PERFECT=True 和 PERFECT=False 各生成一次并检查

# ===== Step 5: Code style / 步骤 5：代码规范 =====
make lint                        # flake8 . + mypy with the required flags / flake8 加上 mypy 的指定参数
make lint-strict                 # optional, try after lint passes / 可选，基础检查通过后再试

# ===== Step 6: Debugger / 步骤 6：调试器 =====
make debug                       # pdb: n next line, s step into, c continue, p name, q quit
                                 # n 下一行, s 进入函数, c 继续, p 变量名, q 退出

# ===== Step 7: Package it and verify in a clean environment =====
# ===== 步骤 7：打包，并在干净环境里验证 =====
python3 -m build                 # creates dist/mazegen-1.0.0-py3-none-any.whl / 生成 whl
cp dist/mazegen-1.0.0-py3-none-any.whl .   # must be at the repo root / 必须放在仓库根目录
unzip -l mazegen-1.0.0-py3-none-any.whl    # should list mazegen/generator.py / 里面应该有 mazegen/generator.py

python3 -m venv /tmp/testenv
/tmp/testenv/bin/pip install ./mazegen-1.0.0-py3-none-any.whl
cd /tmp                          # LEAVE the repo! Otherwise Python imports the local mazegen folder
                                 # 离开仓库！否则会导入本地的 mazegen 文件夹，测试就没有意义
/tmp/testenv/bin/python -c "
from mazegen import MazeGenerator
m = MazeGenerator(20, 15, seed=42, perfect=False)
print(m.solution)
print(m.hex_rows()[0])
"
cd -                             # go back to the repo / 回到仓库

# ===== Step 8: Rebuild like the evaluator / 步骤 8：按评审流程重建一遍 =====
make clean                       # does NOT delete the root .whl / 不会删除根目录的 .whl
python3 -m venv /tmp/rebuild && /tmp/rebuild/bin/pip install build
/tmp/rebuild/bin/python -m build # evaluators ask you to rebuild from source / 评审时会让你从源码再构建一次

# ===== Step 9: Before submitting / 步骤 9：提交前 =====
git status                       # .whl, LICENSE.md, README.md, config.txt must all be there
                                 # .whl、LICENSE.md、README.md、config.txt 都要在
git add . && git commit -m "message" && git push
# Then clone a fresh copy into /tmp and repeat steps 0-2 and 5 there
# 然后在 /tmp 重新克隆一份，再做一遍步骤 0-2 和 5
```