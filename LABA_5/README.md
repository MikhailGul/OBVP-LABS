events {
    # Пустой блок, но обязателен для работы Nginx
}

http {
    server {
        listen 80;
        server_name localhost;

        # Для статики (если нужно)
        location /static {
            root /usr/share/nginx/html;
            index index.html;
        }

        # Проксирование на FastAPI
        location / {
            proxy_pass http://fastapi:8000;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        }
    }
}

<!-- Инструкции для алины (я пишу сама для себя, если что) -->

<!-- 
    запуск кластера: docker-compose up -d --scale fastapi=3 

    проверка кластера: curl http://localhost
-->


<!-- 
    Проверка карбы: docker-compose up -d --scale fastapi=3
 -->