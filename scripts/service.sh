#!/bin/bash

###########################################################
# StoryCraft 服务管理脚本
# 功能：启动、停止、查看 Streamlit 服务状态
###########################################################

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# 切换到项目根目录（向上一级）
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_DIR"

# 配置参数
SERVICE_NAME="StoryCraft"
APP_FILE="src/app.py"
PID_FILE="$PROJECT_DIR/.service.pid"
LOG_FILE="$PROJECT_DIR/.service.log"
STREAMLIT_PORT=30085

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

###########################################################
# 辅助函数
###########################################################

# 打印信息
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# 打印成功信息
print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# 打印警告信息
print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# 打印错误信息
print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 打印分割线
print_separator() {
    echo "============================================================"
}

###########################################################
# 核心功能函数
###########################################################

# 查找并激活虚拟环境
activate_venv() {
    local venv_dirs=(".venv" "venv" "env")
    local venv_found=""

    for dir in "${venv_dirs[@]}"; do
        if [[ -d "$PROJECT_DIR/$dir" ]]; then
            venv_found="$PROJECT_DIR/$dir"
            break
        fi
    done

    if [[ -n "$venv_found" ]]; then
        # 检查虚拟环境是否有效
        if [[ -f "$venv_found/bin/activate" ]]; then
            source "$venv_found/bin/activate"
            print_info "已激活虚拟环境: $venv_found"
            return 0
        elif [[ -f "$venv_found/Scripts/activate" ]]; then
            # Windows 风格虚拟环境
            source "$venv_found/Scripts/activate"
            print_info "已激活虚拟环境: $venv_found"
            return 0
        else
            print_error "虚拟环境目录存在但无效: $venv_found"
            return 1
        fi
    else
        print_error "未找到虚拟环境（已检查: ${venv_dirs[*]}）"
        print_info "请先创建虚拟环境: python -m venv .venv"
        return 1
    fi
}

# 检查依赖
check_dependencies() {
    if [[ ! -f "$APP_FILE" ]]; then
        print_error "应用文件不存在: $APP_FILE"
        return 1
    fi

    # 检查 streamlit 是否已安装
    if ! command -v streamlit &> /dev/null; then
        print_error "未找到 streamlit 命令"
        print_info "请先安装依赖: pip install -r requirements.txt"
        return 1
    fi

    return 0
}

# 检查服务状态
is_service_running() {
    if [[ -f "$PID_FILE" ]]; then
        local pid=$(cat "$PID_FILE" 2>/dev/null)
        if [[ -n "$pid" ]] && ps -p "$pid" > /dev/null 2>&1; then
            return 0  # 服务运行中
        else
            # PID 文件存在但进程不存在，清理无效的 PID 文件
            rm -f "$PID_FILE"
            return 1
        fi
    fi
    return 1
}

# 启动服务
start_service() {
    print_separator
    print_info "正在启动 $SERVICE_NAME 服务..."
    print_separator

    # 检查服务是否已运行
    if is_service_running; then
        print_warning "服务已在运行中！"
        show_status
        return 0
    fi

    # 激活虚拟环境
    if ! activate_venv; then
        return 1
    fi

    # 检查依赖（虚拟环境激活后）
    if [[ ! -f "$APP_FILE" ]]; then
        print_error "应用文件不存在: $APP_FILE"
        return 1
    fi

    # 检查 streamlit 是否已安装（在虚拟环境中）
    if ! command -v streamlit &> /dev/null; then
        print_error "虚拟环境中未找到 streamlit 命令"
        print_info "请先安装依赖: pip install -r requirements.txt"
        return 1
    fi

    # 检查端口是否被占用
    if lsof -Pi :$STREAMLIT_PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
        print_warning "端口 $STREAMLIT_PORT 已被占用"
        print_info "尝试查找占用进程..."
        lsof -Pi :$STREAMLIT_PORT -sTCP:LISTEN
        return 1
    fi

    # 启动 Streamlit 服务（后台运行）
    print_info "正在启动 Streamlit 服务（端口: $STREAMLIT_PORT）..."
    nohup streamlit run "$APP_FILE" --server.port=$STREAMLIT_PORT --server.headless=true > "$LOG_FILE" 2>&1 &

    # 保存 PID
    local pid=$!
    echo $pid > "$PID_FILE"

    # 等待服务启动
    sleep 2

    # 验证服务是否成功启动
    if is_service_running; then
        print_success "服务启动成功！"
        print_separator
        print_info "PID: $pid"
        print_info "日志文件: $LOG_FILE"
        print_info "访问地址: http://localhost:$STREAMLIT_PORT"
        print_separator
        print_info "使用 '$0 stop' 停止服务"
        print_info "使用 '$0 status' 查看状态"
        print_separator
    else
        print_error "服务启动失败，请查看日志: $LOG_FILE"
        rm -f "$PID_FILE"
        return 1
    fi
}

# 停止服务
stop_service() {
    print_separator
    print_info "正在停止 $SERVICE_NAME 服务..."
    print_separator

    if ! is_service_running; then
        print_warning "服务未运行"
        return 0
    fi

    local pid=$(cat "$PID_FILE" 2>/dev/null)

    print_info "正在终止进程 $pid ..."
    kill "$pid" 2>/dev/null

    # 等待进程终止
    local count=0
    while ps -p "$pid" > /dev/null 2>&1 && [[ $count -lt 10 ]]; do
        sleep 1
        count=$((count + 1))
    done

    # 如果进程仍在运行，强制终止
    if ps -p "$pid" > /dev/null 2>&1; then
        print_warning "进程未响应，正在强制终止..."
        kill -9 "$pid" 2>/dev/null
        sleep 1
    fi

    # 清理 PID 文件
    rm -f "$PID_FILE"

    print_success "服务已停止"
    print_separator
}

# 查看服务状态
show_status() {
    print_separator
    print_info "$SERVICE_NAME 服务状态"
    print_separator

    if is_service_running; then
        local pid=$(cat "$PID_FILE" 2>/dev/null)
        print_success "服务运行中"
        print_info "PID: $pid"
        print_info "端口: $STREAMLIT_PORT"
        print_info "访问地址: http://localhost:$STREAMLIT_PORT"
        print_info "日志文件: $LOG_FILE"
        print_info "启动时间: $(ps -p $pid -o lstart= 2>/dev/null)"
        print_info "内存使用: $(ps -p $pid -o rss= 2>/dev/null | awk '{printf "%.2f MB", $1/1024}')"
        print_separator
    else
        print_warning "服务未运行"
        print_separator
    fi
}

# 查看日志
show_logs() {
    if [[ -f "$LOG_FILE" ]]; then
        print_info "显示最近 50 行日志（Ctrl+C 退出）:"
        print_separator
        tail -n 50 -f "$LOG_FILE"
    else
        print_warning "日志文件不存在: $LOG_FILE"
    fi
}

# 显示帮助信息
show_help() {
    print_separator
    echo "  $SERVICE_NAME 服务管理脚本"
    print_separator
    echo ""
    echo "用法: $0 {start|stop|restart|status|logs|help}"
    echo ""
    echo "命令:"
    echo "  start    - 启动服务"
    echo "  stop     - 停止服务"
    echo "  restart  - 重启服务"
    echo "  status   - 查看服务状态"
    echo "  logs     - 查看实时日志（Ctrl+C 退出）"
    echo "  help     - 显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 start     # 启动服务"
    echo "  $0 stop      # 停止服务"
    echo "  $0 status    # 查看状态"
    echo ""
    print_separator
}

###########################################################
# 主程序入口
###########################################################

main() {
    case "${1:-help}" in
        start)
            start_service
            ;;
        stop)
            stop_service
            ;;
        restart)
            stop_service
            echo ""
            start_service
            ;;
        status)
            show_status
            ;;
        logs)
            show_logs
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            print_error "未知命令: $1"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@"
