# OnlineShopAuth


### Кеширование публичного ключа

- Ключ хранится в оперативной памяти микросервиса.

- При первом HTTP запросе к auth-сервису микросервис загружает публичный ключ и сохраняет его в памяти.

- Если ключ изменится,Auth-сервис публикует событие в Kafka: auth.public_key_updated

- Другие сервисы обращаются к auth GET /auth/public_key

### Проверка прав пользователя

- Из хедера извлекается access token

- Токен декодируется публичным ключом

- Из payload извлекаются permissions и сравниваются с доступами ресурса