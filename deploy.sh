#!/bin/bash
# デプロイメントスクリプト for Slack Canvas Creator

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_NAME="slack-canvas-creator-from-threads"
SERVICE_NAME="slack-canvas-creator"
INSTALL_DIR="/opt/$PROJECT_NAME"
SERVICE_USER="slackapp"

# カラー出力用
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 使用方法を表示
show_usage() {
    echo "Usage: $0 [install|uninstall|restart|status|logs]"
    echo ""
    echo "Commands:"
    echo "  install   - Install the service (requires sudo)"
    echo "  uninstall - Remove the service (requires sudo)"
    echo "  restart   - Restart the service (requires sudo)"
    echo "  status    - Show service status"
    echo "  logs      - Show service logs"
    exit 1
}

# サービスをインストール
install_service() {
    print_info "Installing $SERVICE_NAME service..."

    # ユーザーが存在するかチェック
    if ! id "$SERVICE_USER" &>/dev/null; then
        print_info "Creating user $SERVICE_USER..."
        sudo useradd --system --create-home --home-dir "/home/$SERVICE_USER" --shell /bin/false "$SERVICE_USER"
    fi

    # インストールディレクトリを作成
    print_info "Creating installation directory..."
    sudo mkdir -p "$INSTALL_DIR"

    # プロジェクトファイルをコピー
    print_info "Copying project files..."
    sudo cp -r "$SCRIPT_DIR"/* "$INSTALL_DIR/"
    sudo chown -R "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR"

    # Python環境をセットアップ
    print_info "Installing Python dependencies with system pip..."
    cd "$INSTALL_DIR"

    # Python 3.12以上が必要
    PYTHON_VERSION=$(python3 -c "import sys; print('.'.join(map(str, sys.version_info[:2])))")
    REQUIRED_VERSION="3.12"

    if python3 -c "import sys; exit(0 if sys.version_info >= (3, 12) else 1)"; then
        print_info "Python $PYTHON_VERSION detected (>= $REQUIRED_VERSION required)"
    else
        print_error "Python $REQUIRED_VERSION or higher is required. Current version: $PYTHON_VERSION"
        print_error "Please install Python 3.12+ or use Ubuntu 24.04+ which includes Python 3.12"
        exit 1
    fi

    # 依存関係をインストール
    sudo -u "$SERVICE_USER" python3 -m pip install --user -r requirements.txt

    # ユーザーのpipインストールパスを確認
    USER_SITE=$(sudo -u "$SERVICE_USER" python3 -c "import site; print(site.USER_SITE)")
    USER_BASE=$(sudo -u "$SERVICE_USER" python3 -c "import site; print(site.USER_BASE)")
    print_info "Packages installed to: $USER_SITE"
    print_info "User base directory: $USER_BASE"

    # 環境変数ファイルの確認
    if [ ! -f "$INSTALL_DIR/.env" ]; then
        print_warn ".env file not found. Please create it manually:"
        echo "  sudo -u $SERVICE_USER nano $INSTALL_DIR/.env"
        echo ""
        echo "Required environment variables:"
        echo "  SLACK_BOT_TOKEN="
        echo "  SLACK_SIGNING_SECRET="
        echo "  SLACK_APP_TOKEN="
        echo "  OPENAI_API_KEY="
        echo "  PORT=3000"
        echo "  HOST=0.0.0.0"
    fi

    # systemdユニットファイルをコピー
    print_info "Installing systemd unit file..."
    sudo cp "$INSTALL_DIR/$SERVICE_NAME.service" "/etc/systemd/system/"

    # systemdを再読み込み
    print_info "Reloading systemd..."
    sudo systemctl daemon-reload

    # サービスを有効化
    print_info "Enabling service..."
    sudo systemctl enable "$SERVICE_NAME"

    print_info "Installation completed!"
    print_warn "Please ensure .env file is properly configured before starting the service."
    print_info "Start the service with: sudo systemctl start $SERVICE_NAME"
}

# サービスをアンインストール
uninstall_service() {
    print_info "Uninstalling $SERVICE_NAME service..."

    # サービスを停止・無効化
    sudo systemctl stop "$SERVICE_NAME" 2>/dev/null || true
    sudo systemctl disable "$SERVICE_NAME" 2>/dev/null || true

    # ユニットファイルを削除
    sudo rm -f "/etc/systemd/system/$SERVICE_NAME.service"

    # systemdを再読み込み
    sudo systemctl daemon-reload

    # インストールディレクトリを削除
    sudo rm -rf "$INSTALL_DIR"

    # ユーザーを削除（オプション）
    read -p "Do you want to remove the user '$SERVICE_USER' and its home directory? [y/N]: " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        sudo userdel -r "$SERVICE_USER" 2>/dev/null || true
        print_info "User $SERVICE_USER and home directory removed"
    fi

    print_info "Uninstallation completed!"
}

# サービスを再起動
restart_service() {
    print_info "Restarting $SERVICE_NAME service..."
    sudo systemctl restart "$SERVICE_NAME"
    print_info "Service restarted!"
}

# サービスの状態を表示
show_status() {
    sudo systemctl status "$SERVICE_NAME"
}

# サービスのログを表示
show_logs() {
    sudo journalctl -u "$SERVICE_NAME" -f
}

# メイン処理
case "${1:-}" in
    install)
        if [ "$EUID" -ne 0 ]; then
            print_error "Please run with sudo for installation"
            exit 1
        fi
        install_service
        ;;
    uninstall)
        if [ "$EUID" -ne 0 ]; then
            print_error "Please run with sudo for uninstallation"
            exit 1
        fi
        uninstall_service
        ;;
    restart)
        restart_service
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs
        ;;
    *)
        show_usage
        ;;
esac
