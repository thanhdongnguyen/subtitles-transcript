# Sử dụng Python base image
FROM paketobuildpacks/builder:full as builder

# Cài đặt các gói cơ bản
RUN apt-get update && apt-get install -y \
    ffmpeg

# Cài đặt pip và poetry
RUN pip install --no-cache-dir poetry

RUN apt install software-properties-common -y

RUN apt install python3.11 -y

# Thiết lập thư mục làm việc
WORKDIR /app

# Copy tệp cấu hình poetry (pyproject.toml, poetry.lock) trước để sử dụng cơ chế caching
COPY pyproject.toml poetry.lock* /app/

# Cài đặt dependencies từ poetry
RUN poetry config virtualenvs.create false && poetry install --no-interaction --no-ansi

# Copy toàn bộ mã nguồn vào container
COPY . /app

# Cấu hình biến môi trường
ENV PORT=4001
EXPOSE 4001

# Cấu hình lệnh chạy ứng dụng
CMD ["uwsgi", "uwsgi.ini"]