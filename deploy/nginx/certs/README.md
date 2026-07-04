# Certificats TLS

Générer un certificat auto-signé (évaluation) :

```bash
openssl req -x509 -nodes -newkey rsa:2048 -days 825   -keyout server.key -out server.crt   -subj "/CN=supervision-house"
```

En production, remplacer `server.crt` / `server.key` par un vrai certificat,
puis `docker compose restart nginx`.
