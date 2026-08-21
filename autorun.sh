#!/bin/bash
set -e

# Определение команды Docker Compose
if docker compose version &> /dev/null; then
    DOCKER_CMD="docker compose"
else
    DOCKER_CMD="docker-compose"
fi

# Функция автоматического определения sudo для Docker
run_docker() {
    if docker ps &> /dev/null; then
        $DOCKER_CMD "$@"
    else
        sudo $DOCKER_CMD "$@"
    fi
}

# Функция полной очистки системы
stop_and_clean() {
    echo "🧹 Начинаем полную очистку проекта..."

    # 1. Останавливаем контейнеры и удаляем сети/тома
    if [ -f docker-compose.yml ]; then
        run_docker down --volumes --remove-orphans || true
    fi

    # 2. Удаляем конфликтующие контейнеры по именам на всякий случай
    if ! docker ps &> /dev/null; then
        sudo docker rm -f wishlist-postgres-db wihslist-app &> /dev/null || true
        sudo docker rm -f  wihslist-app &> /dev/null || true
        sudo docker volume  rm -f wishlist_api-main_postgres_data || true

    else
        docker rm -f wishlist-postgres-db wihslist-app &> /dev/null || true
        docker rm -f wihslist-app &> /dev/null || true
        docker volume  rm -f wishlist_api-main_postgres_data || true
    fi

    # 3. Удаляем временную папку, если скрипт запущен извне
    USER_HOME=$(eval echo "~$USER")
    TARGET_DIR="$USER_HOME/Desktop/wishlist_api_app"
    rm -rf "$TARGET_DIR"
    #cd $HOME/Desktop
    #rm -rf "wishlist_api_app"
    echo "✨ Проект полностью удален, контейнеры остановлены, память очищена!"
}

# Функция запуска проекта
start_project() {
    echo "🚀 Начинаем установку и запуск Wishlist API..."

    # Создаем изолированную папку в системной директории /tmp (чтобы не мусорить на Рабочем столе)
    TARGET_DIR="$HOME/Desktop/wishlist_api_app"

    # Если скрипт запущен локально внутри репозитория, используем текущую папку
    if [ -f docker-compose.yml ] && [ -f main.py ]; then
        echo "📂 Запуск из локальной папки репозитория..."
    else
        echo "📦 Запуск из облака. Скачиваем файлы проекта..."
        mkdir -p "$TARGET_DIR"
        cd "$TARGET_DIR"
        curl -sSL https://github.com/MSvirski/wishlist_API/archive/refs/heads/main.zip -o wishlist_API_app.zip
        unzip -q wishlist_API_app.zip
        cd wishlist_API-main
    fi

    # Настройка .env
    if [ ! -f .env ]; then
        echo "📄 Создаем конфигурационный файл .env..."
        if [ -f .env.example ]; then
            cp .env.example .env
        else
            echo "При удаленном запуске файл .env не скачался..."# На случай, если при удаленном запуске файл еще не скачался
        fi
    fi

    # Очистка старых зависших контейнеров перед стартом
    echo "🧹 Проверяем порты и старые контейнеры..."
    run_docker down --remove-orphans || true

    # Сборка и запуск
    echo "🐳 Собираем и запускаем Docker-контейнеры..."
    run_docker up --build -d

    echo "🎉 Проект успешно запущен!"
    echo "👉 Документация Swagger: http://localhost:8000/docs"
    echo "ℹ️ Для полного удаления проекта выполните этот же скрипт с параметром 'remove'"
}

stop(){
  USER_HOME=$(eval echo "~$USER")
  TARGET_DIR="$USER_HOME/Desktop/wishlist_api_app/wishlist_API-main"
  # Переходим в эту папку
  cd "$TARGET_DIR"

  echo "=== Останавливаем контейнеры в $TARGET_DIR ==="

    # Проверяем, запущен ли Docker
  if ! docker ps > /dev/null; then
      echo "Ошибка: Демон Docker не запущен. Запустите Docker и повторите попытку."
      exit 1
  fi

  if [ ! -f docker-compose.yml ]; then
        echo "Файл docker-compose.yml не найден."
        exit 1
  fi

  # Останавливаем контейнеры, а также очищаем созданные сети
  run_docker down

  if [ $? -eq 0 ]; then
      echo "=== Все контейнеры успешно остановлены! ==="
  else
      echo "Произошла ошибка при остановке контейнеров."
  fi
}


# Логика обработки аргументов скрипта (up / down)
ACTION="${1:-up}" # Если аргумент не передан, по умолчанию запускаем (up)

case "$ACTION" in
    up)
        start_project
        ;;
    remove)
        stop_and_clean
        ;;
    down)
        stop
        ;;
    *)
        echo "❌ Ошибка: Неверный параметр. Используйте 'up' для запуска, 'down' для остановки или 'remove' для удаления."
        echo "Пример: ./run.sh up или ./run.sh down"
        exit 1
        ;;
esac
