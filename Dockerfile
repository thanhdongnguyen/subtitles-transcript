# Sử dụng base image Python 3.10 với Debian (hoặc Alpine nếu bạn thích)
FROM python:3.11-slim

# Cài đặt các phụ thuộc hệ thống (bao gồm FFmpeg và các công cụ cần thiết cho uWSGI)
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    ffmpeg \
    uwsgi \
    uwsgi-plugin-python3 \
    && rm -rf /var/lib/apt/lists/*

# Thiết lập thư mục làm việc
WORKDIR /app

# Sao chép các tệp cần thiết
COPY pyproject.toml poetry.lock ./

# Cài đặt Poetry
RUN pip install poetry

# Cài đặt các phụ thuộc Python
RUN poetry config virtualenvs.create false && poetry install --no-root --no-interaction --no-ansi

# Sao chép mã nguồn ứng dụng
COPY . .

# Thiết lập biến môi trường (nếu cần)
ENV PYTHONUNBUFFERED=1

# Chạy ứng dụng với uWSGI
CMD ["uwsgi", "--ini", "uwsgi.ini"]