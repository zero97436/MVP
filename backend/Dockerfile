FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1

# iputils-ping (check ping), snmp (check SNMP), build deps psycopg2/bcrypt,
# git (installation du paquet Enterprise depuis le dépôt privé).
RUN apt-get update && apt-get install -y --no-install-recommends \
    iputils-ping snmp gcc libpq-dev git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# --- Édition : "community" (défaut, public) ou "enterprise" (modules payants) ---
# En Enterprise, installe le paquet privé orbisys-enterprise. Le PAT GitHub est
# fourni en secret de build (BuildKit) : il n'apparaît dans AUCUNE couche d'image.
ARG EDITION=community
RUN --mount=type=secret,id=github_pat \
    if [ "$EDITION" = "enterprise" ]; then \
      pip install --no-cache-dir \
        "orbisys-enterprise @ git+https://$(cat /run/secrets/github_pat)@github.com/zero97436/orbisys-enterprise.git" ; \
    fi

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8000
ENTRYPOINT ["/entrypoint.sh"]
CMD ["api"]
