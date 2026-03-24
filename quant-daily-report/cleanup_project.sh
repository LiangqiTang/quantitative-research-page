#!/bin/bash
"""
项目清理脚本
用于整理项目目录结构，删除不必要的文件
"""

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 确认函数
confirm() {
    read -p "$1 (y/N): " response
    case $response in
        [Yy]* ) return 0;;
        * ) return 1;;
    esac
}

# 清理临时文件
cleanup_temp_files() {
    log_info "开始清理临时文件..."

    # 删除Python缓存
    log_info "删除Python缓存..."
    find . -type d -name "__pycache__" -prune -exec rm -rf {} + 2>/dev/null || true

    # 删除pytest缓存
    if [ -d ".pytest_cache" ]; then
        log_info "删除pytest缓存..."
        rm -rf .pytest_cache/
    fi

    # 删除macOS系统文件
    if [ "$(uname)" == "Darwin" ]; then
        log_info "删除macOS系统文件..."
        find . -name ".DS_Store" -delete
    fi

    # 删除过期日志
    if [ -f "firebase-debug.log" ]; then
        log_info "删除Firebase调试日志..."
        rm -f firebase-debug.log
    fi

    # 清理系统日志
    if [ -f "quant_daily.log" ]; then
        log_info "清理系统日志..."
        if [ $(wc -l < quant_daily.log) -gt 10000 ]; then
            tail -10000 quant_daily.log > quant_daily.log.tmp
            mv quant_daily.log.tmp quant_daily.log
            log_info "系统日志已清理，保留最后10000行"
        else
            log_info "系统日志大小合适，无需清理"
        fi
    fi

    log_info "临时文件清理完成"
}

# 清理输出目录
cleanup_output() {
    log_info "开始清理输出目录..."

    if [ -d "output" ]; then
        # 删除旧的报告文件
        find output/ -name "*.md" -o -name "*.txt" -o -name "*.html" | grep -v README.md | xargs rm -f 2>/dev/null || true

        # 保留输出目录结构
        log_info "输出目录已清理（保留README.md）"
    else
        log_warn "输出目录不存在"
    fi

    log_info "输出目录清理完成"
}

# 整理测试文件
organize_tests() {
    log_info "开始整理测试文件..."

    if [ ! -d "tests" ]; then
        log_info "创建tests目录..."
        mkdir -p tests
    fi

    # 移动根目录的测试文件到tests目录
    test_files=$(find . -maxdepth 1 -name "test_*.py" -type f)
    if [ -n "$test_files" ]; then
        log_info "移动测试文件到tests目录..."
        mv test_*.py tests/ 2>/dev/null || true

        # 更新导入路径提示
        log_info "测试文件已移动到tests目录"
        log_warn "注意：移动测试文件后可能需要更新导入路径"
    else
        log_info "根目录没有测试文件需要移动"
    fi

    log_info "测试文件整理完成"
}

# 优化目录结构
optimize_structure() {
    log_info "开始优化目录结构..."

    # 创建src目录
    if [ ! -d "src" ]; then
        log_info "创建src目录..."
        mkdir -p src
    fi

    # 移动核心代码到src目录
    modules=("analyzer" "api" "backtester" "data_collector" "factor_mining" "scripts" "utils" "visualizer")
    for module in "${modules[@]}"; do
        if [ -d "$module" ] && [ ! -d "src/$module" ]; then
            log_info "移动$module到src目录..."
            mv "$module" src/
        fi
    done

    log_info "目录结构优化完成"
    log_warn "注意：移动代码后需要更新导入路径和引用"
}

# 创建.gitignore文件
create_gitignore() {
    log_info "创建/更新.gitignore文件..."

    gitignore_content="""# Python
*.pyc
__pycache__/
.pytest_cache/
.tox/
.venv/

# 日志
*.log
logs/

# 输出
output/
!output/README.md

# 环境变量
.env
.env.local
.env.*.local

# macOS
.DS_Store

# Windows
Thumbs.db
*.lnk

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# 构建
build/
dist/
*.egg-info/

# 临时文件
*.tmp
*.temp"""

    echo "$gitignore_content" > .gitignore
    log_info ".gitignore文件已创建/更新"
}

# 显示统计信息
show_stats() {
    log_info "项目统计信息..."

    # 统计Python文件数量
    py_files=$(find . -name "*.py" -type f | grep -v "__pycache__" | grep -v ".pyc" | wc -l)
    # 统计目录数量
    dir_count=$(find . -type d | grep -v "__pycache__" | grep -v ".git" | wc -l)
    # 统计日志文件大小
    log_size=$(du -sh quant_daily.log 2>/dev/null | cut -f1 || echo "N/A")

    echo -e "${GREEN}Python文件数量:${NC} $py_files"
    echo -e "${GREEN}目录数量:${NC} $dir_count"
    echo -e "${GREEN}日志文件大小:${NC} $log_size"
}

# 主函数
main() {
    echo -e "${GREEN}===================== 项目清理脚本 =====================${NC}"
    echo -e "${YELLOW}注意：请在执行前备份重要数据${NC}"
    echo

    # 显示选项菜单
    echo -e "${GREEN}清理选项:${NC}"
    echo "1. 清理临时文件（推荐）"
    echo "2. 清理输出目录"
    echo "3. 整理测试文件"
    echo "4. 优化目录结构（高级）"
    echo "5. 创建/更新.gitignore"
    echo "6. 显示项目统计信息"
    echo "7. 全部执行（1-5）"
    echo "0. 退出"
    echo

    read -p "请选择操作: " choice

    case $choice in
        1)
            cleanup_temp_files
            ;;
        2)
            cleanup_output
            ;;
        3)
            organize_tests
            ;;
        4)
            if confirm "优化目录结构会移动核心代码，可能导致项目暂时无法运行，是否继续？"; then
                optimize_structure
            else
                log_info "已取消优化目录结构"
            fi
            ;;
        5)
            create_gitignore
            ;;
        6)
            show_stats
            ;;
        7)
            cleanup_temp_files
            cleanup_output
            organize_tests
            if confirm "优化目录结构会移动核心代码，可能导致项目暂时无法运行，是否继续？"; then
                optimize_structure
            else
                log_info "已取消优化目录结构"
            fi
            create_gitignore
            log_info "全部清理操作完成"
            ;;
        0)
            log_info "退出"
            exit 0
            ;;
        *)
            log_error "无效选项，请重新选择"
            main
            ;;
    esac

    echo
    log_info "清理脚本执行完成"
}

# 执行主函数
main "$@"